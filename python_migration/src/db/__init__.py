"""
Database layer — SQLAlchemy ORM models, session management, and CRUD repositories.

Replaces:
  - DB2 connection management (DBPROC.cpy, DB2CONN.cbl)
  - VSAM file I/O (all READ/WRITE/REWRITE/DELETE operations)
  - DB2 SQL operations (INSERT/SELECT/UPDATE/DELETE)
"""

from .base import Base, SessionLocal, engine, get_db, init_db
from .crud import CRUDBase
from .models import (
    ErrorLog,
    InvestmentPosition,
    PortfolioMaster,
    PositionHistory,
    ReturnCodes,
    TransactionHistory,
)
from .repositories import (
    error_log_repo,
    portfolio_repo,
    position_history_repo,
    position_repo,
    return_codes_repo,
    transaction_repo,
)

__all__ = [
    # Base
    "Base",
    "engine",
    "SessionLocal",
    "get_db",
    "init_db",
    "CRUDBase",
    # ORM models
    "PortfolioMaster",
    "InvestmentPosition",
    "TransactionHistory",
    "PositionHistory",
    "ErrorLog",
    "ReturnCodes",
    # Repositories
    "portfolio_repo",
    "position_repo",
    "transaction_repo",
    "position_history_repo",
    "error_log_repo",
    "return_codes_repo",
]
