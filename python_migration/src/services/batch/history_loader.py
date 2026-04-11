"""
Position History DB2 Load — converted from HISTLD00.cbl (234 LOC).

Replaces: COBOL HISTLD00 program — reads transaction history file,
          loads to DB2 with commit thresholds, checkpoint updates.
Target:   SQLAlchemy batch insert with commit intervals.

COBOL flow:
  1000-INIT        → open files, init counters, set commit threshold
  2000-READ-TRANS  → read next transaction history record
  3000-INSERT-DB2  → INSERT INTO POSHIST
  4000-CHECK-COMMIT → commit if threshold reached
  5000-TERMINATE   → final commit, close files, display counts
"""

import logging
from datetime import datetime
from decimal import Decimal

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from db.repositories import position_history_repo
from models.enums import CheckpointPhase, ReturnCode
from services.batch.checkpoint import CheckpointManager

logger = logging.getLogger(__name__)

# Commit threshold (from HISTLD00.cbl WS-COMMIT-THRESHOLD)
DEFAULT_COMMIT_THRESHOLD = 100


class LoadResult:
    """Load statistics — replaces HISTLD00.cbl WS-COUNTERS."""

    def __init__(self) -> None:
        self.records_read: int = 0
        self.records_inserted: int = 0
        self.records_rejected: int = 0
        self.commits: int = 0


class HistoryLoaderService:
    """
    Loads position history into database — replaces HISTLD00.cbl.

    Processes transaction history records in batches with commit
    thresholds, checkpoint/restart support, and error handling.
    """

    def __init__(self, commit_threshold: int = DEFAULT_COMMIT_THRESHOLD) -> None:
        self.commit_threshold = commit_threshold

    def load_history(
        self,
        db: Session,
        records: list[dict],
        job_name: str = "HISTLD00",
    ) -> tuple[LoadResult, ReturnCode]:
        """
        Load a batch of position history records.

        Replaces: Main processing loop in HISTLD00.cbl.
        """
        result = LoadResult()
        ckpt = CheckpointManager(job_name)
        ckpt.initialize()
        highest_rc = ReturnCode.SUCCESS

        for record in records:
            result.records_read += 1

            rc = self._insert_record(db, record)
            if rc == ReturnCode.SUCCESS:
                result.records_inserted += 1
            else:
                result.records_rejected += 1
                if rc.value > highest_rc.value:
                    highest_rc = rc

            # Check commit threshold (replaces 4000-CHECK-COMMIT)
            if result.records_inserted % self.commit_threshold == 0 and result.records_inserted > 0:
                try:
                    db.commit()
                    result.commits += 1
                    ckpt.take_checkpoint(
                        phase=CheckpointPhase.PROCESS,
                        records_processed=result.records_inserted,
                        last_key=record.get("account_no", ""),
                    )
                except SQLAlchemyError:
                    pass

        # Final commit (replaces 5000-TERMINATE)
        try:
            db.commit()
            result.commits += 1
        except SQLAlchemyError as exc:
            logger.error("Final commit failed: %s", exc)
            highest_rc = ReturnCode.ERROR

        logger.info(
            "History load complete: read=%d, inserted=%d, rejected=%d, commits=%d",
            result.records_read, result.records_inserted, result.records_rejected, result.commits,
        )
        return result, highest_rc

    def _insert_record(self, db: Session, record: dict) -> ReturnCode:
        """
        Insert a single position history record.

        Replaces: 3000-INSERT-DB2 paragraph.
        """
        try:
            now = datetime.now()
            history_data = {
                "account_no": record["account_no"],
                "portfolio_id": record["portfolio_id"],
                "trans_date": record.get("trans_date", now.date()),
                "trans_time": record.get("trans_time", now.time()),
                "trans_type": record["trans_type"],
                "security_id": record["security_id"],
                "quantity": Decimal(str(record["quantity"])),
                "price": Decimal(str(record["price"])),
                "amount": Decimal(str(record["amount"])),
                "fees": Decimal(str(record.get("fees", "0.00"))),
                "total_amount": Decimal(str(record.get("total_amount", record["amount"]))),
                "cost_basis": Decimal(str(record.get("cost_basis", "0.00"))),
                "gain_loss": Decimal(str(record.get("gain_loss", "0.00"))),
                "process_date": now.date(),
                "process_time": now.time(),
                "program_id": "HISTLD00",
                "user_id": record.get("user_id", "SYSTEM"),
                "audit_timestamp": now,
            }
            position_history_repo.create(db, obj_in=history_data)
            return ReturnCode.SUCCESS
        except IntegrityError:
            db.rollback()
            logger.warning("Duplicate history record: %s/%s", record.get("account_no"), record.get("trans_date"))
            return ReturnCode.WARNING
        except (SQLAlchemyError, KeyError, ValueError) as exc:
            db.rollback()
            logger.error("Error inserting history: %s", exc)
            return ReturnCode.ERROR
