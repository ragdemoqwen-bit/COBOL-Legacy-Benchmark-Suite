"""
DB2 Commit Controller — converted from DB2CMT.cbl (171 LOC).

Replaces: COBOL DB2CMT program with INIT/COMMIT/ROLLBACK/SAVEPOINT/RESTORE/STAT functions.
Target:   SQLAlchemy transaction management.

COBOL interface (LINKAGE SECTION):
  LS-CMT-FUNCTION    PIC X(4)  — 'INIT'/'CMIT'/'ROLL'/'SAVE'/'REST'/'STAT'
  LS-CMT-RETURN-CODE PIC S9(4) COMP
"""

import logging
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from models.enums import ReturnCode

logger = logging.getLogger(__name__)


@dataclass
class CommitStats:
    """Tracks commit/rollback statistics — replaces DB2CMT.cbl WS-CMT-STATS."""

    commit_count: int = 0
    rollback_count: int = 0
    savepoint_count: int = 0
    error_count: int = 0
    last_commit_time: datetime | None = None
    last_rollback_time: datetime | None = None


class DB2CommitController:
    """
    Manages transaction commit/rollback — replaces DB2CMT.cbl.

    COBOL EVALUATE TRUE dispatch:
      'INIT' → initialize
      'CMIT' → commit
      'ROLL' → rollback
      'SAVE' → savepoint
      'REST' → restore (rollback to savepoint)
      'STAT' → statistics
    """

    def __init__(self) -> None:
        self.stats = CommitStats()
        self._savepoints: dict[str, str] = {}

    def initialize(self, session: Session) -> ReturnCode:
        """
        Initialize commit processing.

        Replaces: 1000-INIT-COMMIT paragraph.
        """
        self.stats = CommitStats()
        logger.info("Commit controller initialized")
        return ReturnCode.SUCCESS

    def commit(self, session: Session) -> ReturnCode:
        """
        Commit current transaction.

        Replaces: 2000-COMMIT-WORK paragraph.
        """
        try:
            session.commit()
            self.stats.commit_count += 1
            self.stats.last_commit_time = datetime.now()
            logger.debug("Transaction committed (#%d)", self.stats.commit_count)
            return ReturnCode.SUCCESS
        except SQLAlchemyError as exc:
            self.stats.error_count += 1
            logger.error("Commit failed: %s", exc)
            return ReturnCode.ERROR

    def rollback(self, session: Session) -> ReturnCode:
        """
        Rollback current transaction.

        Replaces: 3000-ROLLBACK-WORK paragraph.
        """
        try:
            session.rollback()
            self.stats.rollback_count += 1
            self.stats.last_rollback_time = datetime.now()
            logger.info("Transaction rolled back (#%d)", self.stats.rollback_count)
            return ReturnCode.SUCCESS
        except SQLAlchemyError as exc:
            self.stats.error_count += 1
            logger.error("Rollback failed: %s", exc)
            return ReturnCode.ERROR

    def savepoint(self, session: Session, name: str) -> ReturnCode:
        """
        Create a savepoint.

        Replaces: 4000-SAVEPOINT paragraph.
        """
        try:
            session.begin_nested()
            self._savepoints[name] = name
            self.stats.savepoint_count += 1
            logger.debug("Savepoint '%s' created", name)
            return ReturnCode.SUCCESS
        except SQLAlchemyError as exc:
            self.stats.error_count += 1
            logger.error("Savepoint creation failed: %s", exc)
            return ReturnCode.ERROR

    def restore(self, session: Session, name: str) -> ReturnCode:
        """
        Rollback to a named savepoint.

        Replaces: 5000-RESTORE-SAVEPOINT paragraph.
        """
        if name not in self._savepoints:
            logger.warning("Savepoint '%s' not found", name)
            return ReturnCode.WARNING
        try:
            session.rollback()
            del self._savepoints[name]
            logger.info("Restored to savepoint '%s'", name)
            return ReturnCode.SUCCESS
        except SQLAlchemyError as exc:
            self.stats.error_count += 1
            logger.error("Restore failed: %s", exc)
            return ReturnCode.ERROR

    def get_statistics(self) -> tuple[dict, ReturnCode]:
        """
        Return commit statistics.

        Replaces: 6000-GET-STATS paragraph.
        """
        return {
            "commit_count": self.stats.commit_count,
            "rollback_count": self.stats.rollback_count,
            "savepoint_count": self.stats.savepoint_count,
            "error_count": self.stats.error_count,
            "last_commit_time": self.stats.last_commit_time,
            "last_rollback_time": self.stats.last_rollback_time,
        }, ReturnCode.SUCCESS
