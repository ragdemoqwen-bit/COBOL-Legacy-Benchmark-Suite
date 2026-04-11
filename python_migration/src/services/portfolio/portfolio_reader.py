"""
Portfolio Record Reading — converted from PORTREAD.cbl (112 LOC).

Replaces: COBOL PORTREAD program — sequential read of portfolio file,
          displays records.
Target:   SQLAlchemy query with formatted output.

COBOL flow:
  1000-OPEN-FILE   → DB session
  2000-READ-FILE   → sequential read loop
  3000-DISPLAY     → format and display each record
  4000-CLOSE-FILE  → session close
"""

import logging
from collections.abc import Generator

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import PortfolioMaster
from models.enums import ReturnCode

logger = logging.getLogger(__name__)


class PortfolioReaderService:
    """
    Sequential portfolio file reader — replaces PORTREAD.cbl.

    Reads all portfolio records sequentially and yields formatted output,
    just as PORTREAD.cbl reads PORTFOLIO-FILE until EOF and DISPLAYs.
    """

    def read_all(self, db: Session) -> tuple[list[dict], ReturnCode]:
        """
        Read all portfolio records and return formatted list.

        Replaces: Main loop — PERFORM 2000-READ-FILE UNTIL END-OF-FILE.
        """
        try:
            stmt = select(PortfolioMaster).order_by(PortfolioMaster.portfolio_id)
            records = db.execute(stmt).scalars().all()

            results = []
            for record in records:
                results.append(self._format_record(record))

            logger.info("Read %d portfolio records", len(results))
            return results, ReturnCode.SUCCESS
        except Exception as exc:
            logger.error("Error reading portfolios: %s", exc)
            return [], ReturnCode.ERROR

    def read_sequential(self, db: Session) -> Generator[dict, None, None]:
        """
        Yield portfolio records one at a time (streaming).

        Replaces: Sequential READ NEXT loop with EOF check.
        """
        stmt = select(PortfolioMaster).order_by(PortfolioMaster.portfolio_id)
        for record in db.execute(stmt).scalars():
            yield self._format_record(record)

    def _format_record(self, record: PortfolioMaster) -> dict:
        """
        Format a portfolio record for display.

        Replaces: 3000-DISPLAY-RECORD paragraph with DISPLAY statements.
        """
        return {
            "portfolio_id": record.portfolio_id,
            "portfolio_name": record.portfolio_name,
            "account_type": record.account_type,
            "branch_id": record.branch_id,
            "client_id": record.client_id,
            "currency_code": record.currency_code,
            "risk_level": record.risk_level,
            "status": record.status,
            "open_date": str(record.open_date) if record.open_date else None,
            "close_date": str(record.close_date) if record.close_date else None,
            "last_maint_date": str(record.last_maint_date) if record.last_maint_date else None,
            "last_maint_user": record.last_maint_user,
        }
