"""
SQLAlchemy ORM models derived from DB2 table definitions.

Sources:
  src/database/db2/db2-definitions.sql — PORTFOLIO_MASTER, INVESTMENT_POSITIONS, TRANSACTION_HISTORY
  src/database/db2/POSHIST.sql         — POSHIST (position history)
  src/database/db2/ERRLOG.sql          — ERRLOG (error logging)
  src/database/db2/RTNCODES.sql        — RTNCODES (return code logging)
"""

from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import (
    CHAR,
    DATE,
    DECIMAL,
    INTEGER,
    TIME,
    TIMESTAMP,
    VARCHAR,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


# ============================================================================
# PORTFOLIO_MASTER — from db2-definitions.sql lines 10-24
# ============================================================================
class PortfolioMaster(Base):
    """
    DB2 PORTFOLIO_MASTER table.

    Primary key: PORTFOLIO_ID CHAR(8)
    """

    __tablename__ = "portfolio_master"

    portfolio_id: Mapped[str] = mapped_column(CHAR(8), primary_key=True)
    account_type: Mapped[str] = mapped_column(CHAR(2), nullable=False)
    branch_id: Mapped[str] = mapped_column(CHAR(2), nullable=False)
    client_id: Mapped[str] = mapped_column(CHAR(10), nullable=False)
    portfolio_name: Mapped[str] = mapped_column(VARCHAR(50), nullable=False)
    currency_code: Mapped[str] = mapped_column(CHAR(3), nullable=False)
    risk_level: Mapped[str] = mapped_column(CHAR(1), nullable=False)
    status: Mapped[str] = mapped_column(CHAR(1), nullable=False)
    open_date: Mapped[date] = mapped_column(DATE, nullable=False)
    close_date: Mapped[date | None] = mapped_column(DATE, nullable=True)
    last_maint_date: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)
    last_maint_user: Mapped[str] = mapped_column(VARCHAR(8), nullable=False)

    # Relationships
    positions: Mapped[list["InvestmentPosition"]] = relationship(back_populates="portfolio")
    transactions: Mapped[list["TransactionHistory"]] = relationship(back_populates="portfolio")

    __table_args__ = (
        Index("idx_port_master_client", "client_id", "status"),
    )


# ============================================================================
# INVESTMENT_POSITIONS — from db2-definitions.sql lines 29-41
# ============================================================================
class InvestmentPosition(Base):
    """
    DB2 INVESTMENT_POSITIONS table.

    Composite PK: (PORTFOLIO_ID, INVESTMENT_ID, POSITION_DATE)
    FK: PORTFOLIO_ID → PORTFOLIO_MASTER
    """

    __tablename__ = "investment_positions"

    portfolio_id: Mapped[str] = mapped_column(
        CHAR(8), ForeignKey("portfolio_master.portfolio_id"), primary_key=True
    )
    investment_id: Mapped[str] = mapped_column(CHAR(10), primary_key=True)
    position_date: Mapped[date] = mapped_column(DATE, primary_key=True)
    quantity: Mapped[Decimal] = mapped_column(DECIMAL(18, 4), nullable=False)
    cost_basis: Mapped[Decimal] = mapped_column(DECIMAL(18, 2), nullable=False)
    market_value: Mapped[Decimal] = mapped_column(DECIMAL(18, 2), nullable=False)
    currency_code: Mapped[str] = mapped_column(CHAR(3), nullable=False)
    last_maint_date: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)
    last_maint_user: Mapped[str] = mapped_column(VARCHAR(8), nullable=False)

    # Relationship
    portfolio: Mapped["PortfolioMaster"] = relationship(back_populates="positions")

    __table_args__ = (
        Index("idx_positions_date", "position_date", "portfolio_id"),
    )


# ============================================================================
# TRANSACTION_HISTORY — from db2-definitions.sql lines 46-62
# ============================================================================
class TransactionHistory(Base):
    """
    DB2 TRANSACTION_HISTORY table.

    Primary key: TRANSACTION_ID CHAR(20)
    FK: PORTFOLIO_ID → PORTFOLIO_MASTER
    """

    __tablename__ = "transaction_history"

    transaction_id: Mapped[str] = mapped_column(CHAR(20), primary_key=True)
    portfolio_id: Mapped[str] = mapped_column(
        CHAR(8), ForeignKey("portfolio_master.portfolio_id"), nullable=False
    )
    transaction_date: Mapped[date] = mapped_column(DATE, nullable=False)
    transaction_time: Mapped[time] = mapped_column(TIME, nullable=False)
    investment_id: Mapped[str] = mapped_column(CHAR(10), nullable=False)
    transaction_type: Mapped[str] = mapped_column(CHAR(2), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(DECIMAL(18, 4), nullable=False)
    price: Mapped[Decimal] = mapped_column(DECIMAL(18, 4), nullable=False)
    amount: Mapped[Decimal] = mapped_column(DECIMAL(18, 2), nullable=False)
    currency_code: Mapped[str] = mapped_column(CHAR(3), nullable=False)
    status: Mapped[str] = mapped_column(CHAR(1), nullable=False)
    process_date: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)
    process_user: Mapped[str] = mapped_column(VARCHAR(8), nullable=False)

    # Relationship
    portfolio: Mapped["PortfolioMaster"] = relationship(back_populates="transactions")

    __table_args__ = (
        Index("idx_trans_hist_port", "portfolio_id", "transaction_date"),
        Index("idx_trans_hist_date", "transaction_date", "portfolio_id"),
    )


# ============================================================================
# POSHIST — from POSHIST.sql lines 25-44
# ============================================================================
class PositionHistory(Base):
    """
    DB2 POSHIST table — position history / transaction detail.

    Composite PK: (ACCOUNT_NO, PORTFOLIO_ID, TRANS_DATE, TRANS_TIME)
    """

    __tablename__ = "poshist"

    account_no: Mapped[str] = mapped_column(CHAR(8), primary_key=True)
    portfolio_id: Mapped[str] = mapped_column(CHAR(10), primary_key=True)
    trans_date: Mapped[date] = mapped_column(DATE, primary_key=True)
    trans_time: Mapped[time] = mapped_column(TIME, primary_key=True)
    trans_type: Mapped[str] = mapped_column(CHAR(2), nullable=False)
    security_id: Mapped[str] = mapped_column(CHAR(12), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(DECIMAL(15, 3), nullable=False)
    price: Mapped[Decimal] = mapped_column(DECIMAL(15, 3), nullable=False)
    amount: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), nullable=False)
    fees: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), nullable=False, default=Decimal("0.00"))
    total_amount: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), nullable=False)
    cost_basis: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), nullable=False)
    gain_loss: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), nullable=False)
    process_date: Mapped[date] = mapped_column(DATE, nullable=False)
    process_time: Mapped[time] = mapped_column(TIME, nullable=False)
    program_id: Mapped[str] = mapped_column(CHAR(8), nullable=False)
    user_id: Mapped[str] = mapped_column(CHAR(8), nullable=False)
    audit_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, default=datetime.now)

    __table_args__ = (
        Index("poshist_ix1", "security_id", "trans_date"),
        Index("poshist_ix2", "process_date", "program_id"),
    )


# ============================================================================
# ERRLOG — from ERRLOG.sql lines 15-26
# ============================================================================
class ErrorLog(Base):
    """
    DB2 ERRLOG table — error logging.

    Composite PK: (ERROR_TIMESTAMP, PROGRAM_ID)
    """

    __tablename__ = "errlog"

    error_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP, primary_key=True)
    program_id: Mapped[str] = mapped_column(CHAR(8), primary_key=True)
    error_type: Mapped[str] = mapped_column(CHAR(1), nullable=False)
    error_severity: Mapped[int] = mapped_column(INTEGER, nullable=False)
    error_code: Mapped[str] = mapped_column(CHAR(8), nullable=False)
    error_message: Mapped[str] = mapped_column(VARCHAR(200), nullable=False)
    process_date: Mapped[date] = mapped_column(DATE, nullable=False)
    process_time: Mapped[time] = mapped_column(TIME, nullable=False)
    user_id: Mapped[str] = mapped_column(CHAR(8), nullable=False)
    additional_info: Mapped[str | None] = mapped_column(VARCHAR(500), nullable=True)

    __table_args__ = (
        Index("errlog_ix1", "process_date", "error_severity"),
    )


# ============================================================================
# RTNCODES — from RTNCODES.sql lines 2-10
# ============================================================================
class ReturnCodes(Base):
    """
    DB2 RTNCODES table — return code logging for analysis.

    Composite PK: (TIMESTAMP, PROGRAM_ID)
    """

    __tablename__ = "rtncodes"

    timestamp: Mapped[datetime] = mapped_column(TIMESTAMP, primary_key=True)
    program_id: Mapped[str] = mapped_column(CHAR(8), primary_key=True)
    return_code: Mapped[int] = mapped_column(INTEGER, nullable=False)
    highest_code: Mapped[int] = mapped_column(INTEGER, nullable=False)
    status_code: Mapped[str] = mapped_column(CHAR(1), nullable=False)
    message_text: Mapped[str | None] = mapped_column(VARCHAR(80), nullable=True)

    __table_args__ = (
        Index("rtncodes_prg_idx", "program_id", "timestamp"),
        Index("rtncodes_sts_idx", "status_code", "timestamp"),
    )
