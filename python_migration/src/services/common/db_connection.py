"""
DB2 Connection Manager — converted from DB2CONN.cbl (155 LOC).

Replaces: COBOL DB2CONN program with CONNECT/DISCONNECT/STATUS functions,
          retry logic, and connection status tracking.
Target:   SQLAlchemy session management with connection pooling.

COBOL interface (LINKAGE SECTION):
  LS-DB2-FUNCTION   PIC X(4)  — 'CONN' / 'DISC' / 'STAT'
  LS-DB2-RETURN-CODE PIC S9(4) COMP
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session

from db.base import SessionLocal, engine
from models.enums import DB2RequestType, ReturnCode

logger = logging.getLogger(__name__)

# Connection retry parameters (from DB2CONN.cbl WS-MAX-RETRIES / WS-RETRY-DELAY)
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5


@dataclass
class ConnectionStats:
    """Tracks connection statistics — replaces DB2CONN.cbl WS-CONN-STATS."""

    connect_count: int = 0
    disconnect_count: int = 0
    error_count: int = 0
    last_connect_time: datetime | None = None
    last_disconnect_time: datetime | None = None
    active_sessions: list[Session] = field(default_factory=list)


class DB2ConnectionManager:
    """
    Manages database connections — replaces DB2CONN.cbl.

    COBOL EVALUATE TRUE dispatch:
      WHEN DB2-CONNECT    → connect()
      WHEN DB2-DISCONNECT → disconnect()
      WHEN DB2-STATUS     → get_status()
    """

    def __init__(self) -> None:
        self.stats = ConnectionStats()

    def connect(self) -> tuple[Session, ReturnCode]:
        """
        Establish a database connection with retry logic.

        Replaces: 2000-CONNECT-DB2 paragraph with retry loop.
        Returns:  (session, return_code) tuple.
        """
        last_error: Exception | None = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                session = SessionLocal()
                # Verify connection is alive (replaces DB2 CONNECT statement)
                session.execute(text("SELECT 1"))
                self.stats.connect_count += 1
                self.stats.last_connect_time = datetime.now()
                self.stats.active_sessions.append(session)
                logger.info(
                    "DB connection established (attempt %d/%d)",
                    attempt,
                    MAX_RETRIES,
                )
                return session, ReturnCode.SUCCESS
            except OperationalError as exc:
                last_error = exc
                self.stats.error_count += 1
                logger.warning(
                    "DB connection attempt %d/%d failed: %s",
                    attempt,
                    MAX_RETRIES,
                    exc,
                )

        logger.error("DB connection failed after %d retries: %s", MAX_RETRIES, last_error)
        return SessionLocal(), ReturnCode.ERROR

    def disconnect(self, session: Session) -> ReturnCode:
        """
        Disconnect a database session.

        Replaces: 3000-DISCONNECT-DB2 paragraph.
        """
        try:
            session.close()
            self.stats.disconnect_count += 1
            self.stats.last_disconnect_time = datetime.now()
            if session in self.stats.active_sessions:
                self.stats.active_sessions.remove(session)
            logger.info("DB connection closed successfully")
            return ReturnCode.SUCCESS
        except SQLAlchemyError as exc:
            self.stats.error_count += 1
            logger.error("Error disconnecting: %s", exc)
            return ReturnCode.ERROR

    def get_status(self) -> tuple[dict, ReturnCode]:
        """
        Check connection status.

        Replaces: 4000-CHECK-STATUS paragraph.
        """
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            status = {
                "connected": True,
                "connect_count": self.stats.connect_count,
                "disconnect_count": self.stats.disconnect_count,
                "error_count": self.stats.error_count,
                "active_sessions": len(self.stats.active_sessions),
                "last_connect_time": self.stats.last_connect_time,
                "last_disconnect_time": self.stats.last_disconnect_time,
            }
            return status, ReturnCode.SUCCESS
        except SQLAlchemyError as exc:
            logger.error("Status check failed: %s", exc)
            return {"connected": False, "error": str(exc)}, ReturnCode.ERROR

    def dispatch(self, function_code: DB2RequestType) -> tuple[object, ReturnCode]:
        """
        Main dispatch — replaces DB2CONN.cbl 0000-MAIN EVALUATE TRUE.
        """
        if function_code == DB2RequestType.CONNECT:
            return self.connect()
        if function_code == DB2RequestType.DISCONNECT:
            # Disconnect last active session
            if self.stats.active_sessions:
                session = self.stats.active_sessions[-1]
                rc = self.disconnect(session)
                return None, rc
            return None, ReturnCode.WARNING
        if function_code == DB2RequestType.STATUS:
            return self.get_status()
        logger.error("Invalid function code: %s", function_code)
        return None, ReturnCode.ERROR
