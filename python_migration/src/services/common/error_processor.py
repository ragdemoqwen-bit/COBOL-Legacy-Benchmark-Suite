"""
Standard Error Processing — converted from ERRPROC.cbl (108 LOC).

Replaces: COBOL ERRPROC subroutine with file I/O error logging.
Target:   Python structured logging with database persistence.

COBOL interface (LINKAGE SECTION):
  LS-ERROR-REQUEST containing ERR-MESSAGE fields from ERRHAND.cpy
"""

import logging
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from db.models import ErrorLog
from models.enums import ErrorCategory, ErrorLogSeverity, ErrorLogType, ReturnCode

logger = logging.getLogger(__name__)


@dataclass
class ErrorRequest:
    """Structured error request — replaces ERRHAND.cpy LS-ERROR-REQUEST."""

    program_id: str
    category: ErrorCategory
    error_code: str
    severity: ErrorLogSeverity
    error_text: str
    error_details: str = ""


class ErrorProcessor:
    """
    Processes and logs errors — replaces ERRPROC.cbl.

    COBOL flow:
      1000-OPEN-ERROR-FILE       → DB session (already open)
      2000-FORMAT-ERROR-MESSAGE  → format_error()
      3000-WRITE-ERROR-RECORD    → log_to_db()
      4000-CLOSE-ERROR-FILE      → session managed externally
    """

    def process_error(
        self,
        error_request: ErrorRequest,
        db: Session | None = None,
    ) -> ReturnCode:
        """
        Main error processing entry point.

        Replaces: ERRPROC.cbl PROCEDURE DIVISION.
        """
        # Format the error message (replaces 2000-FORMAT-ERROR-MESSAGE)
        formatted = self._format_error(error_request)

        # Log to Python logger
        log_method = self._get_log_method(error_request.severity)
        log_method(formatted)

        # Write to database if session available (replaces 3000-WRITE-ERROR-RECORD)
        if db is not None:
            return self._log_to_db(error_request, db)

        return ReturnCode.SUCCESS

    def _format_error(self, req: ErrorRequest) -> str:
        """
        Format error message for logging.

        Replaces: 2000-FORMAT-ERROR-MESSAGE paragraph.
        """
        return (
            f"[{req.category.value}] {req.program_id} - "
            f"Code: {req.error_code} Sev: {req.severity.name} - "
            f"{req.error_text}"
            + (f" | {req.error_details}" if req.error_details else "")
        )

    def _log_to_db(self, req: ErrorRequest, db: Session) -> ReturnCode:
        """
        Persist error record to database.

        Replaces: 3000-WRITE-ERROR-RECORD paragraph with WRITE ERROR-RECORD.
        """
        try:
            now = datetime.now()
            error_log = ErrorLog(
                error_timestamp=now,
                program_id=req.program_id,
                error_type=self._map_category_to_type(req.category).value,
                error_severity=req.severity.value,
                error_code=req.error_code,
                error_message=req.error_text[:200],
                process_date=now.date(),
                process_time=now.time(),
                user_id="SYSTEM",
                additional_info=req.error_details[:500] if req.error_details else None,
            )
            db.add(error_log)
            db.commit()
            return ReturnCode.SUCCESS
        except SQLAlchemyError as exc:
            logger.error("Failed to persist error log: %s", exc)
            db.rollback()
            return ReturnCode.ERROR

    def _get_log_method(self, severity: ErrorLogSeverity):
        """Map severity to Python logging method."""
        severity_map = {
            ErrorLogSeverity.INFO: logger.info,
            ErrorLogSeverity.WARNING: logger.warning,
            ErrorLogSeverity.ERROR: logger.error,
            ErrorLogSeverity.SEVERE: logger.critical,
        }
        return severity_map.get(severity, logger.error)

    def _map_category_to_type(self, category: ErrorCategory) -> ErrorLogType:
        """Map error category to error log type."""
        category_map = {
            ErrorCategory.VSAM: ErrorLogType.DATA,
            ErrorCategory.VALIDATION: ErrorLogType.DATA,
            ErrorCategory.PROCESSING: ErrorLogType.APPLICATION,
            ErrorCategory.SYSTEM: ErrorLogType.SYSTEM,
        }
        return category_map.get(category, ErrorLogType.APPLICATION)
