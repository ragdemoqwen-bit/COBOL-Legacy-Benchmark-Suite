"""
Portfolio Master File Maintenance — converted from PORTMSTR.cbl (289 LOC).

Replaces: COBOL PORTMSTR program — CRUD operations for portfolio records,
          VSAM indexed file I/O, validation, error handling.
Target:   SQLAlchemy ORM operations via CRUDBase.

COBOL interface (FILE SECTION):
  PORTFOLIO-FILE — VSAM KSDS, key = PORT-ID
  Operations: OPEN, READ, WRITE, REWRITE, DELETE, CLOSE
"""

import logging
from datetime import datetime

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from db.models import PortfolioMaster as PortfolioMasterModel
from db.repositories import portfolio_repo
from models.enums import PortfolioStatus, ReturnCode

logger = logging.getLogger(__name__)


class PortfolioMasterService:
    """
    Portfolio master file maintenance — replaces PORTMSTR.cbl.

    COBOL EVALUATE TRUE dispatch on WS-FUNCTION:
      'ADD'  → add_portfolio()
      'UPD'  → update_portfolio()
      'DEL'  → delete_portfolio()
      'INQ'  → get_portfolio()
      'LST'  → list_portfolios()
    """

    def get_portfolio(self, db: Session, portfolio_id: str) -> tuple[PortfolioMasterModel | None, ReturnCode]:
        """
        Read a portfolio record by key.

        Replaces: 2000-READ-PORTFOLIO paragraph with READ PORTFOLIO-FILE.
        """
        try:
            record = portfolio_repo.get(db, portfolio_id=portfolio_id)
            if record is None:
                logger.info("Portfolio %s not found", portfolio_id)
                return None, ReturnCode.WARNING
            return record, ReturnCode.SUCCESS
        except SQLAlchemyError as exc:
            logger.error("Error reading portfolio %s: %s", portfolio_id, exc)
            return None, ReturnCode.ERROR

    def add_portfolio(self, db: Session, data: dict) -> tuple[PortfolioMasterModel | None, ReturnCode]:
        """
        Add a new portfolio record.

        Replaces: 3000-ADD-PORTFOLIO paragraph with WRITE PORTFOLIO-RECORD.
        """
        try:
            # Set maintenance fields (replaces MOVE FUNCTION CURRENT-DATE)
            now = datetime.now()
            data.setdefault("last_maint_date", now)
            data.setdefault("last_maint_user", "SYSTEM")
            data.setdefault("open_date", now.date())
            data.setdefault("status", PortfolioStatus.ACTIVE.value)

            record = portfolio_repo.create(db, obj_in=data)
            logger.info("Portfolio %s added successfully", data.get("portfolio_id"))
            return record, ReturnCode.SUCCESS
        except IntegrityError as exc:
            db.rollback()
            logger.warning("Duplicate portfolio: %s", exc)
            return None, ReturnCode.WARNING
        except SQLAlchemyError as exc:
            db.rollback()
            logger.error("Error adding portfolio: %s", exc)
            return None, ReturnCode.ERROR

    def update_portfolio(
        self,
        db: Session,
        portfolio_id: str,
        updates: dict,
    ) -> tuple[PortfolioMasterModel | None, ReturnCode]:
        """
        Update an existing portfolio record.

        Replaces: 4000-UPDATE-PORTFOLIO paragraph with REWRITE PORTFOLIO-RECORD.
        """
        try:
            existing = portfolio_repo.get(db, portfolio_id=portfolio_id)
            if existing is None:
                logger.warning("Portfolio %s not found for update", portfolio_id)
                return None, ReturnCode.WARNING

            updates["last_maint_date"] = datetime.now()
            record = portfolio_repo.update(db, db_obj=existing, obj_in=updates)
            logger.info("Portfolio %s updated", portfolio_id)
            return record, ReturnCode.SUCCESS
        except SQLAlchemyError as exc:
            db.rollback()
            logger.error("Error updating portfolio %s: %s", portfolio_id, exc)
            return None, ReturnCode.ERROR

    def delete_portfolio(self, db: Session, portfolio_id: str) -> ReturnCode:
        """
        Delete a portfolio record.

        Replaces: 5000-DELETE-PORTFOLIO paragraph with DELETE PORTFOLIO-FILE.
        """
        try:
            existing = portfolio_repo.get(db, portfolio_id=portfolio_id)
            if existing is None:
                logger.warning("Portfolio %s not found for deletion", portfolio_id)
                return ReturnCode.WARNING

            portfolio_repo.delete(db, db_obj=existing)
            logger.info("Portfolio %s deleted", portfolio_id)
            return ReturnCode.SUCCESS
        except SQLAlchemyError as exc:
            db.rollback()
            logger.error("Error deleting portfolio %s: %s", portfolio_id, exc)
            return ReturnCode.ERROR

    def list_portfolios(
        self,
        db: Session,
        *,
        status: str | None = None,
        client_id: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[PortfolioMasterModel], ReturnCode]:
        """
        List portfolio records with optional filters.

        Replaces: 6000-LIST-PORTFOLIOS paragraph with sequential READ NEXT.
        """
        try:
            filters: dict = {}
            if status:
                filters["status"] = status
            if client_id:
                filters["client_id"] = client_id
            records = portfolio_repo.get_multi(db, skip=skip, limit=limit, filters=filters or None)
            return list(records), ReturnCode.SUCCESS
        except SQLAlchemyError as exc:
            logger.error("Error listing portfolios: %s", exc)
            return [], ReturnCode.ERROR
