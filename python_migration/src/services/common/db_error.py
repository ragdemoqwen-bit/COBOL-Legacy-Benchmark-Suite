"""
DB2 SQL Error Handler — converted from DB2ERR.cbl (201 LOC).

Replaces: COBOL DB2ERR program with LOG/DIAGNOSE/RETRIEVE functions,
          error categorization, and DB2 SQLCA analysis.
Target:   Python exception handling with structured error logging.

COBOL interface (LINKAGE SECTION):
  LS-ERR-FUNCTION     PIC X(4)  — 'LOG '/'DIAG'/'RETR'
  LS-ERR-SQLCODE      PIC S9(9) COMP
  LS-ERR-CATEGORY     PIC X(2)
  LS-ERR-RETURN-CODE  PIC S9(4) COMP
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy.exc import (
    IntegrityError,
    OperationalError,
    ProgrammingError,
    SQLAlchemyError,
)

from models.enums import ErrorCategory, ReturnCode

logger = logging.getLogger(__name__)


@dataclass
class SqlError:
    """Structured SQL error record — replaces DB2ERR.cbl WS-ERROR-RECORD."""

    timestamp: datetime
    sqlcode: int
    category: ErrorCategory
    program_id: str
    message: str
    details: str = ""


@dataclass
class ErrorStats:
    """Error statistics — replaces DB2ERR.cbl WS-ERR-STATS."""

    total_errors: int = 0
    vsam_errors: int = 0
    validation_errors: int = 0
    processing_errors: int = 0
    system_errors: int = 0
    error_log: list[SqlError] = field(default_factory=list)


class DB2ErrorHandler:
    """
    Handles SQL/database errors — replaces DB2ERR.cbl.

    COBOL EVALUATE TRUE dispatch:
      'LOG '  → log_error()
      'DIAG'  → diagnose_error()
      'RETR'  → retrieve_errors()
    """

    def __init__(self) -> None:
        self.stats = ErrorStats()

    def log_error(
        self,
        exc: Exception,
        program_id: str = "UNKNOWN",
        details: str = "",
    ) -> ReturnCode:
        """
        Log a database error.

        Replaces: 2000-LOG-ERROR paragraph.
        Categorizes error by exception type (replaces SQLCODE analysis).
        """
        category = self._categorize_error(exc)
        sqlcode = self._extract_sqlcode(exc)

        error_record = SqlError(
            timestamp=datetime.now(),
            sqlcode=sqlcode,
            category=category,
            program_id=program_id,
            message=str(exc),
            details=details,
        )
        self.stats.error_log.append(error_record)
        self.stats.total_errors += 1
        self._increment_category_count(category)

        logger.error(
            "[%s] %s error in %s: SQLCODE=%d %s",
            error_record.timestamp.isoformat(),
            category.value,
            program_id,
            sqlcode,
            exc,
        )
        return ReturnCode.SUCCESS

    def diagnose_error(self, exc: Exception) -> tuple[dict, ReturnCode]:
        """
        Diagnose a database error and return structured analysis.

        Replaces: 3000-DIAGNOSE-ERROR paragraph with EVALUATE SQLCODE.
        """
        category = self._categorize_error(exc)
        sqlcode = self._extract_sqlcode(exc)

        diagnosis = {
            "sqlcode": sqlcode,
            "category": category.value,
            "exception_type": type(exc).__name__,
            "message": str(exc),
            "recoverable": self._is_recoverable(exc),
            "suggested_action": self._suggest_action(exc),
        }
        return diagnosis, ReturnCode.SUCCESS

    def retrieve_errors(
        self,
        program_id: str | None = None,
        category: ErrorCategory | None = None,
        limit: int = 100,
    ) -> tuple[list[SqlError], ReturnCode]:
        """
        Retrieve logged errors with optional filters.

        Replaces: 4000-RETRIEVE-ERRORS paragraph.
        """
        results = self.stats.error_log
        if program_id:
            results = [e for e in results if e.program_id == program_id]
        if category:
            results = [e for e in results if e.category == category]
        return results[:limit], ReturnCode.SUCCESS

    def _categorize_error(self, exc: Exception) -> ErrorCategory:
        """
        Map exception type to ErrorCategory.

        Replaces: DB2ERR.cbl EVALUATE SQLCODE error categorization.
        """
        if isinstance(exc, IntegrityError):
            return ErrorCategory.VALIDATION
        if isinstance(exc, OperationalError):
            return ErrorCategory.SYSTEM
        if isinstance(exc, ProgrammingError):
            return ErrorCategory.PROCESSING
        return ErrorCategory.PROCESSING

    def _extract_sqlcode(self, exc: Exception) -> int:
        """Extract a numeric error code from the exception."""
        if isinstance(exc, SQLAlchemyError) and exc.orig:
            args = getattr(exc.orig, "args", ())
            if args and isinstance(args[0], int):
                return args[0]
        return -1

    def _increment_category_count(self, category: ErrorCategory) -> None:
        if category == ErrorCategory.VSAM:
            self.stats.vsam_errors += 1
        elif category == ErrorCategory.VALIDATION:
            self.stats.validation_errors += 1
        elif category == ErrorCategory.PROCESSING:
            self.stats.processing_errors += 1
        elif category == ErrorCategory.SYSTEM:
            self.stats.system_errors += 1

    def _is_recoverable(self, exc: Exception) -> bool:
        """Determine if error is recoverable (deadlock/timeout = yes)."""
        return isinstance(exc, OperationalError)

    def _suggest_action(self, exc: Exception) -> str:
        """Suggest recovery action based on error type."""
        if isinstance(exc, OperationalError):
            return "RETRY — transient error, retry the operation"
        if isinstance(exc, IntegrityError):
            return "ABORT — data integrity violation, fix input data"
        if isinstance(exc, ProgrammingError):
            return "ABORT — SQL programming error, fix the query"
        return "ABORT — unknown error"
