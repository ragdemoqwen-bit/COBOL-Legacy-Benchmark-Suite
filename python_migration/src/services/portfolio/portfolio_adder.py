"""
Portfolio Addition — converted from PORTADD.cbl (149 LOC).

Replaces: COBOL PORTADD program — creates new portfolio records from input file,
          handles duplicate detection.
Target:   SQLAlchemy INSERT with IntegrityError handling.

COBOL flow:
  1000-OPEN-FILES   → open PORTFOLIO-FILE and INPUT-FILE
  2000-READ-INPUT   → read next input record
  3000-ADD-RECORD   → WRITE PORTFOLIO-RECORD (check for duplicates via file status)
  4000-CLOSE-FILES  → close files, report counts
"""

import logging
from datetime import datetime

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from db.repositories import portfolio_repo
from models.enums import AuditAction, PortfolioStatus, ReturnCode
from services.common.audit_processor import AuditProcessor, AuditRequest

logger = logging.getLogger(__name__)


class AddResult:
    """Tracks batch addition results — replaces PORTADD.cbl WS-COUNTERS."""

    def __init__(self) -> None:
        self.total_read: int = 0
        self.added: int = 0
        self.duplicates: int = 0
        self.errors: int = 0


class PortfolioAdderService:
    """
    Creates new portfolio records — replaces PORTADD.cbl.

    Processes a list of new portfolio records, handling duplicates
    gracefully (just like COBOL FILE STATUS '22' for duplicate key).
    """

    def __init__(self) -> None:
        self.auditor = AuditProcessor()

    def add_portfolio(
        self,
        db: Session,
        data: dict,
        user_id: str = "SYSTEM",
    ) -> ReturnCode:
        """
        Add a single portfolio record.

        Replaces: 3000-ADD-RECORD paragraph.
        """
        try:
            now = datetime.now()
            data.setdefault("status", PortfolioStatus.ACTIVE.value)
            data.setdefault("open_date", now.date())
            data.setdefault("last_maint_date", now)
            data.setdefault("last_maint_user", user_id)

            portfolio_repo.create(db, obj_in=data)

            self.auditor.write_audit(
                AuditRequest(
                    system_id="PORTADD",
                    user_id=user_id,
                    program="PORTADD",
                    action=AuditAction.CREATE,
                    portfolio_id=data.get("portfolio_id", ""),
                    message=f"Added portfolio {data.get('portfolio_id', '')}",
                )
            )

            logger.info("Portfolio %s added", data.get("portfolio_id"))
            return ReturnCode.SUCCESS
        except IntegrityError:
            db.rollback()
            logger.warning("Duplicate portfolio: %s", data.get("portfolio_id"))
            return ReturnCode.WARNING
        except SQLAlchemyError as exc:
            db.rollback()
            logger.error("Error adding portfolio: %s", exc)
            return ReturnCode.ERROR

    def process_batch_additions(
        self,
        db: Session,
        records: list[dict],
    ) -> tuple[AddResult, ReturnCode]:
        """
        Process a batch of portfolio additions.

        Replaces: Main loop — PERFORM 2000-READ-INPUT / 3000-ADD-RECORD UNTIL EOF.
        """
        result = AddResult()

        for record in records:
            result.total_read += 1
            rc = self.add_portfolio(db, record, user_id=record.get("user_id", "SYSTEM"))

            if rc == ReturnCode.SUCCESS:
                result.added += 1
            elif rc == ReturnCode.WARNING:
                result.duplicates += 1
            else:
                result.errors += 1

        logger.info(
            "Batch add: %d read, %d added, %d dups, %d errors",
            result.total_read,
            result.added,
            result.duplicates,
            result.errors,
        )
        return result, ReturnCode.SUCCESS
