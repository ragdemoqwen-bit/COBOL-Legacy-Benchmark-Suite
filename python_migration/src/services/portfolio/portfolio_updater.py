"""
Portfolio Update — converted from PORTUPDT.cbl (161 LOC).

Replaces: COBOL PORTUPDT program — reads update file, applies updates
          to portfolio records (status, name, value).
Target:   SQLAlchemy batch update with validation.

COBOL flow:
  1000-OPEN-FILES      → open PORTFOLIO-FILE and UPDATE-FILE
  2000-PROCESS-UPDATES → read update record, find portfolio, apply changes
  3000-APPLY-UPDATE    → REWRITE PORTFOLIO-RECORD with updated fields
  4000-CLOSE-FILES     → close files, report counts
"""

import logging
from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from db.repositories import portfolio_repo
from models.enums import AuditAction, ReturnCode
from services.common.audit_processor import AuditProcessor, AuditRequest

logger = logging.getLogger(__name__)


class UpdateResult:
    """Tracks batch update results — replaces PORTUPDT.cbl WS-COUNTERS."""

    def __init__(self) -> None:
        self.total_read: int = 0
        self.updated: int = 0
        self.not_found: int = 0
        self.errors: int = 0


class PortfolioUpdaterService:
    """
    Applies updates to portfolio records — replaces PORTUPDT.cbl.

    Processes a list of update requests, each containing a portfolio_id
    and the fields to update (status, name, value).
    """

    def __init__(self) -> None:
        self.auditor = AuditProcessor()

    def apply_update(
        self,
        db: Session,
        portfolio_id: str,
        updates: dict,
        user_id: str = "SYSTEM",
    ) -> ReturnCode:
        """
        Apply a single update to a portfolio record.

        Replaces: 3000-APPLY-UPDATE paragraph.
        """
        try:
            record = portfolio_repo.get(db, portfolio_id=portfolio_id)
            if record is None:
                logger.warning("Portfolio %s not found for update", portfolio_id)
                return ReturnCode.WARNING

            # Capture before image for audit
            before = f"status={record.status},name={record.portfolio_name}"

            updates["last_maint_date"] = datetime.now()
            updates["last_maint_user"] = user_id
            portfolio_repo.update(db, db_obj=record, obj_in=updates)

            after = ",".join(f"{k}={v}" for k, v in updates.items() if k not in ("last_maint_date", "last_maint_user"))

            self.auditor.write_audit(
                AuditRequest(
                    system_id="PORTUPDT",
                    user_id=user_id,
                    program="PORTUPDT",
                    action=AuditAction.UPDATE,
                    portfolio_id=portfolio_id,
                    before_image=before,
                    after_image=after,
                    message=f"Updated portfolio {portfolio_id}",
                )
            )

            logger.info("Portfolio %s updated", portfolio_id)
            return ReturnCode.SUCCESS
        except SQLAlchemyError as exc:
            db.rollback()
            logger.error("Error updating portfolio %s: %s", portfolio_id, exc)
            return ReturnCode.ERROR

    def process_batch_updates(
        self,
        db: Session,
        update_records: list[dict],
    ) -> tuple[UpdateResult, ReturnCode]:
        """
        Process a batch of portfolio updates.

        Replaces: 2000-PROCESS-UPDATES paragraph loop.
        """
        result = UpdateResult()

        for record in update_records:
            result.total_read += 1
            portfolio_id = record.get("portfolio_id", "")
            updates = {k: v for k, v in record.items() if k != "portfolio_id"}

            rc = self.apply_update(db, portfolio_id, updates, user_id=record.get("user_id", "SYSTEM"))

            if rc == ReturnCode.SUCCESS:
                result.updated += 1
            elif rc == ReturnCode.WARNING:
                result.not_found += 1
            else:
                result.errors += 1

        logger.info(
            "Batch update: %d read, %d updated, %d not found, %d errors",
            result.total_read,
            result.updated,
            result.not_found,
            result.errors,
        )
        return result, ReturnCode.SUCCESS
