"""
Validation constants — converted from PORTVAL.cpy

Maps every COBOL working-storage item from the PORTVAL copybook to a Python
constant, preserving exact names, values, and semantics.

COBOL source reference:
  01  VAL-RETURN-CODES.
      05  VAL-SUCCESS          PIC S9(4) VALUE +0.
      05  VAL-INVALID-ID       PIC S9(4) VALUE +1.
      05  VAL-INVALID-ACCT     PIC S9(4) VALUE +2.
      05  VAL-INVALID-TYPE     PIC S9(4) VALUE +3.
      05  VAL-INVALID-AMT      PIC S9(4) VALUE +4.

  01  VAL-ERROR-MESSAGES.
      05  VAL-ERR-ID           PIC X(50) VALUE 'Invalid Portfolio ID format'.
      05  VAL-ERR-ACCT         PIC X(50) VALUE 'Invalid Account Number format'.
      05  VAL-ERR-TYPE         PIC X(50) VALUE 'Invalid Investment Type'.
      05  VAL-ERR-AMT          PIC X(50) VALUE 'Amount outside valid range'.

  01  VAL-CONSTANTS.
      05  VAL-MIN-AMOUNT       PIC S9(13)V99 VALUE -9999999999999.99.
      05  VAL-MAX-AMOUNT       PIC S9(13)V99 VALUE +9999999999999.99.
      05  VAL-ID-PREFIX        PIC X(4)      VALUE 'PORT'.
"""

from decimal import Decimal
from enum import IntEnum


# ---------------------------------------------------------------------------
# Return codes  (VAL-RETURN-CODES)
# ---------------------------------------------------------------------------
class ValReturnCode(IntEnum):
    """Maps COBOL VAL-RETURN-CODES PIC S9(4) values."""

    SUCCESS = 0
    INVALID_ID = 1
    INVALID_ACCT = 2
    INVALID_TYPE = 3
    INVALID_AMT = 4


# ---------------------------------------------------------------------------
# Error messages  (VAL-ERROR-MESSAGES, PIC X(50) each)
# ---------------------------------------------------------------------------
VAL_ERR_ID: str = "Invalid Portfolio ID format"
VAL_ERR_ACCT: str = "Invalid Account Number format"
VAL_ERR_TYPE: str = "Invalid Investment Type"
VAL_ERR_AMT: str = "Amount outside valid range"

# Map return code → error message for convenience
ERROR_MESSAGES: dict[ValReturnCode, str] = {
    ValReturnCode.INVALID_ID: VAL_ERR_ID,
    ValReturnCode.INVALID_ACCT: VAL_ERR_ACCT,
    ValReturnCode.INVALID_TYPE: VAL_ERR_TYPE,
    ValReturnCode.INVALID_AMT: VAL_ERR_AMT,
}


# ---------------------------------------------------------------------------
# Validation constants  (VAL-CONSTANTS)
# ---------------------------------------------------------------------------
# PIC S9(13)V99 — 13 integer digits, 2 decimal digits, signed
VAL_MIN_AMOUNT: Decimal = Decimal("-9999999999999.99")
VAL_MAX_AMOUNT: Decimal = Decimal("9999999999999.99")

# PIC X(4) VALUE 'PORT'
VAL_ID_PREFIX: str = "PORT"

# Valid investment types checked by 3000-VALIDATE-TYPE
VALID_INVESTMENT_TYPES: frozenset[str] = frozenset({"STK", "BND", "MMF", "ETF"})
