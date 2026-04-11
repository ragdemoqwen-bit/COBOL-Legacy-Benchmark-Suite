"""
DB2 Recovery Manager — converted from DB2RECV.cbl (146 LOC).

Replaces: COBOL DB2RECV program — handles DB2 connection failures,
          retry logic, transaction rollback, recovery status tracking.
Target:   Python retry/recovery service for SQLAlchemy sessions.

COBOL flow (EVALUATE TRUE on RECV-REQUEST-TYPE):
  P100-RECOVER-CONNECTION  → retry connection up to MAX-RETRIES
  P200-RECOVER-TRANSACTION → ROLLBACK and report status
  P300-RECOVER-CURSOR      → log error, check if continue/fail

COBOL parameters:
  WS-MAX-RETRIES     = 3
  WS-RETRY-INTERVAL  = 2 seconds
"""

import logging
import time
from dataclasses import dataclass
from enum import StrEnum

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from db.base import SessionLocal

logger = logging.getLogger(__name__)

# From DB2RECV.cbl WS-RECOVERY-STATS
MAX_RETRIES = 3
RETRY_INTERVAL_SECONDS = 2


class RecoveryRequestType(StrEnum):
    """Recovery request types — from DB2RECV.cbl RECV-REQUEST-TYPE 88-levels."""

    CONNECTION = "C"
    TRANSACTION = "T"
    CURSOR = "R"


class RecoveryStatus(StrEnum):
    """Recovery outcome — from DB2RECV.cbl RECV-STATUS 88-levels."""

    SUCCESS = "S"
    FAILED = "F"
    RETRY = "R"


@dataclass
class RecoveryResult:
    """Recovery result — replaces DB2RECV.cbl RECOVERY-REQUEST-AREA output."""

    status: RecoveryStatus
    response_code: int = 0
    sqlcode: int = 0
    message: str = ""
    retry_count: int = 0


class DBRecoveryService:
    """
    DB2 recovery manager — replaces DB2RECV.cbl.

    Handles connection failures, transaction rollback, and cursor recovery
    with configurable retry logic.
    """

    def __init__(
        self,
        max_retries: int = MAX_RETRIES,
        retry_interval: float = RETRY_INTERVAL_SECONDS,
    ) -> None:
        self._max_retries = max_retries
        self._retry_interval = retry_interval

    def recover_connection(self) -> RecoveryResult:
        """
        Attempt to recover a database connection.

        Replaces: P100-RECOVER-CONNECTION retry loop.
        Tries to create a new session up to max_retries times.
        """
        retry_count = 0

        while retry_count < self._max_retries:
            try:
                db = SessionLocal()
                # Test the connection
                db.execute(db.get_bind().dialect.do_ping(db.get_bind()))
                db.close()
                logger.info("Connection recovered after %d retries", retry_count)
                return RecoveryResult(
                    status=RecoveryStatus.SUCCESS,
                    response_code=0,
                    retry_count=retry_count,
                )
            except Exception as exc:
                retry_count += 1
                logger.warning(
                    "Connection attempt %d/%d failed: %s",
                    retry_count,
                    self._max_retries,
                    exc,
                )
                if retry_count < self._max_retries:
                    time.sleep(self._retry_interval)

        return RecoveryResult(
            status=RecoveryStatus.FAILED,
            response_code=-1,
            message=f"Connection recovery failed after {self._max_retries} retries",
            retry_count=retry_count,
        )

    def recover_transaction(self, db: Session) -> RecoveryResult:
        """
        Recover from a failed transaction by rolling back.

        Replaces: P200-RECOVER-TRANSACTION → EXEC SQL ROLLBACK.
        """
        try:
            db.rollback()
            logger.info("Transaction rolled back successfully")
            return RecoveryResult(
                status=RecoveryStatus.SUCCESS,
                response_code=0,
            )
        except SQLAlchemyError as exc:
            logger.error("Transaction rollback failed: %s", exc)
            return RecoveryResult(
                status=RecoveryStatus.FAILED,
                response_code=-1,
                message=f"Rollback failed: {exc}",
            )

    def recover_cursor(
        self,
        program: str,
        cursor_name: str,
        error_code: int,
    ) -> RecoveryResult:
        """
        Recover from a cursor error.

        Replaces: P300-RECOVER-CURSOR → log error, determine action.
        Non-fatal errors allow retry; fatal errors signal failure.
        """
        # Non-fatal cursor errors (data not found, etc.) → retry
        non_fatal_codes = {100, -811}  # NOT FOUND, multiple rows

        if error_code in non_fatal_codes:
            logger.warning(
                "Non-fatal cursor error in %s/%s: sqlcode=%d — retrying",
                program,
                cursor_name,
                error_code,
            )
            return RecoveryResult(
                status=RecoveryStatus.RETRY,
                sqlcode=error_code,
                message=f"Non-fatal cursor error {error_code} in {program}/{cursor_name}",
            )

        logger.error(
            "Fatal cursor error in %s/%s: sqlcode=%d",
            program,
            cursor_name,
            error_code,
        )
        return RecoveryResult(
            status=RecoveryStatus.FAILED,
            sqlcode=error_code,
            message=f"Fatal cursor error {error_code} in {program}/{cursor_name}",
        )

    def dispatch(self, request_type: str, **kwargs: object) -> RecoveryResult:
        """
        Dispatch recovery request.

        Replaces: EVALUATE TRUE on RECV-REQUEST-TYPE.
        """
        req = request_type.strip().upper()
        if req == RecoveryRequestType.CONNECTION:
            return self.recover_connection()
        if req == RecoveryRequestType.TRANSACTION:
            db = kwargs.get("db")
            if not isinstance(db, Session):
                return RecoveryResult(
                    status=RecoveryStatus.FAILED,
                    response_code=-1,
                    message="Transaction recovery requires a db session",
                )
            return self.recover_transaction(db)
        if req == RecoveryRequestType.CURSOR:
            program = str(kwargs.get("program", ""))
            cursor_name = str(kwargs.get("cursor_name", ""))
            error_code = int(kwargs.get("error_code", 0))
            return self.recover_cursor(program, cursor_name, error_code)

        return RecoveryResult(
            status=RecoveryStatus.FAILED,
            response_code=-1,
            message=f"Unknown recovery request type: {request_type!r}",
        )
