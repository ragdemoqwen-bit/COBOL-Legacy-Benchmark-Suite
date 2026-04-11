"""
Pydantic models and constants derived from PORTVAL.cpy — Portfolio Validation Rules.

COBOL source: src/copybook/common/PORTVAL.cpy (47 LOC)
"""

from decimal import Decimal

from .enums import ValidationReturnCode

# ---------------------------------------------------------------------------
# Validation Constants (VAL-CONSTANTS from PORTVAL.cpy)
# ---------------------------------------------------------------------------
VAL_MIN_AMOUNT = Decimal("-9999999999999.99")
VAL_MAX_AMOUNT = Decimal("9999999999999.99")
VAL_ID_PREFIX = "PORT"

# ---------------------------------------------------------------------------
# Validation Error Messages (VAL-ERROR-MESSAGES from PORTVAL.cpy)
# ---------------------------------------------------------------------------
VAL_ERROR_MESSAGES: dict[ValidationReturnCode, str] = {
    ValidationReturnCode.SUCCESS: "",
    ValidationReturnCode.INVALID_ID: "Invalid Portfolio ID format",
    ValidationReturnCode.INVALID_ACCT: "Invalid Account Number format",
    ValidationReturnCode.INVALID_TYPE: "Invalid Investment Type",
    ValidationReturnCode.INVALID_AMT: "Amount outside valid range",
}

# Valid investment types (from PORTVALD.cbl validation logic)
VALID_INVESTMENT_TYPES = frozenset({"STK", "BND", "MMF", "ETF"})
