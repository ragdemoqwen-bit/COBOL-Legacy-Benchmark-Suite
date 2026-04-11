"""
Portfolio Deletion — converted from PORTDEL.cbl (195 LOC).

Replaces: COBOL PORTDEL program — processes deletion requests,
          writes audit trail, handles not-found cases.
Target:   SQLAlchemy DELETE with audit logging.

COBOL flow:
  1000-OPEN-FILES      → open PORTFOLIO-FILE, DELETE-FILE, AUDIT-FILE
  2000-READ-DELETE-REQ → read next deletion request
  3000-PROCESS-DELETE  → READ portfolio, validate, DELETE, write audit
  4000-CLOSE-FILES     → close files, report counts
"""

import logging

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from db.repositories import portfolio_repo
from models.enums import AuditAction, ReturnCode
from services.common.audit_processor import AuditProcessor, AuditRequest

logger = logging.getLogger(__name__)


class DeleteResult:
    """Tracks batch deletion results — replaces PORTDEL.cbl WS-COUNTERS."""

    def __init__(self) -> None:
        self.total_read: int = 0
        self.deleted: int = 0
        self.not_found: int = 0
        self.errors: int = 0


class PortfolioDeleterService:
    """
    Deletes portfolio records — replaces PORTDEL.cbl.

    Processes deletion requests, validates the portfolio exists,
    captures before-image for audit, then deletes.
    """

    def __init__(self) -> None:
        self.auditor = AuditProcessor()

    def delete_portfolio(
        self,
        db: Session,
        portfolio_id: str,
        user_id: str = "SYSTEM",
        reason: str = "",
    ) -> ReturnCode:
        """
        Delete a single portfolio record.

        Replaces: 3000-PROCESS-DELETE paragraph.
        """
        try:
            record = portfolio_repo.get(db, portfolio_id=portfolio_id)
            if record is None:
                logger.warning("Portfolio %s not found for deletion", portfolio_id)
                return ReturnCode.WARNING

            # Capture before-image for audit (replaces MOVE fields TO AUDIT-BEFORE)
            before_image = (
                f"id={record.portfolio_id},name={record.portfolio_name},"
                f"status={record.status},client={record.client_id}"
            )

            portfolio_repo.delete(db, db_obj=record)

            self.auditor.write_audit(
                AuditRequest(
                    system_id="PORTDEL",
                    user_id=user_id,
                    program="PORTDEL",
                    action=AuditAction.DELETE,
                    portfolio_id=portfolio_id,
                    before_image=before_image,
                    message=f"Deleted portfolio {portfolio_id}" + (f": {reason}" if reason else ""),
                )
            )

            logger.info("Portfolio %s deleted", portfolio_id)
            return ReturnCode.SUCCESS
        except SQLAlchemyError as exc:
            db.rollback()
            logger.error("Error deleting portfolio %s: %s", portfolio_id, exc)
            return ReturnCode.ERROR

    def process_batch_deletions(
        self,
        db: Session,
        deletion_requests: list[dict],
    ) -> tuple[DeleteResult, ReturnCode]:
        """
        Process a batch of deletion requests.

        Replaces: Main loop — PERFORM 2000-READ-DELETE-REQ / 3000-PROCESS-DELETE UNTIL EOF.
        """
        result = DeleteResult()

        for req in deletion_requests:
            result.total_read += 1
            rc = self.delete_portfolio(
                db,
                portfolio_id=req["portfolio_id"],
                user_id=req.get("user_id", "SYSTEM"),
                reason=req.get("reason", ""),
            )

            if rc == ReturnCode.SUCCESS:
                result.deleted += 1
            elif rc == ReturnCode.WARNING:
                result.not_found += 1
            else:
                result.errors += 1

        logger.info(
            "Batch delete: %d read, %d deleted, %d not found, %d errors",
            result.total_read,
            result.deleted,
            result.not_found,
            result.errors,
        )
        return result, ReturnCode.SUCCESS
