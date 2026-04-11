"""
Entity-specific repositories built on CRUDBase.

Each repository corresponds to a DB2 table and provides the same operations
that were spread across multiple COBOL programs.
"""

from .crud import CRUDBase
from .models import (
    ErrorLog,
    InvestmentPosition,
    PortfolioMaster,
    PositionHistory,
    ReturnCodes,
    TransactionHistory,
)

# ---------------------------------------------------------------------------
# Repository instances — one per DB2 table
# ---------------------------------------------------------------------------

portfolio_repo = CRUDBase(PortfolioMaster)
"""Replaces VSAM PORTMSTR file operations from PORTMSTR.cbl, PORTADD.cbl, etc."""

position_repo = CRUDBase(InvestmentPosition)
"""Replaces INVESTMENT_POSITIONS operations from POSUPDT.cbl."""

transaction_repo = CRUDBase(TransactionHistory)
"""Replaces TRANSACTION_HISTORY operations from PORTTRAN.cbl."""

position_history_repo = CRUDBase(PositionHistory)
"""Replaces POSHIST DB2 table operations from HISTLD00.cbl."""

error_log_repo = CRUDBase(ErrorLog)
"""Replaces ERRLOG DB2 table operations from DB2ERR.cbl."""

return_codes_repo = CRUDBase(ReturnCodes)
"""Replaces RTNCODES DB2 table operations from RTNANA00.cbl."""
