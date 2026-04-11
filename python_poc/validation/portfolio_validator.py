"""
Portfolio Validation Subroutine — converted from PORTVALD.cbl

Mirrors the COBOL program logic 1:1:

  PORTVALD accepts a validation request via its LINKAGE SECTION:
    01  LS-VALIDATION-REQUEST.
        05  LS-VALIDATE-TYPE    PIC X(1).
            88  LS-VAL-ID       VALUE 'I'.
            88  LS-VAL-ACCT     VALUE 'A'.
            88  LS-VAL-TYPE     VALUE 'T'.
            88  LS-VAL-AMT      VALUE 'M'.
        05  LS-INPUT-VALUE      PIC X(50).
        05  LS-RETURN-CODE      PIC S9(4) COMP.
        05  LS-ERROR-MSG        PIC X(50).

  The EVALUATE dispatches to:
    1000-VALIDATE-ID     → Portfolio ID must start with 'PORT' + 4 numeric digits
    2000-VALIDATE-ACCOUNT → Account number must be 10 numeric digits, not all zeros
    3000-VALIDATE-TYPE   → Must be STK / BND / MMF / ETF
    4000-VALIDATE-AMOUNT → Must be within [-9999999999999.99, +9999999999999.99]

  This Python module exposes both individual validators and a single
  ``validate()`` dispatcher that matches the COBOL EVALUATE TRUE logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import Enum

from python_poc.validation.constants import (
    ERROR_MESSAGES,
    VALID_INVESTMENT_TYPES,
    VAL_ERR_ACCT,
    VAL_ERR_AMT,
    VAL_ERR_ID,
    VAL_ERR_TYPE,
    VAL_ID_PREFIX,
    VAL_MAX_AMOUNT,
    VAL_MIN_AMOUNT,
    ValReturnCode,
)


# ---------------------------------------------------------------------------
# Validation type enum  (mirrors LS-VALIDATE-TYPE level-88 conditions)
# ---------------------------------------------------------------------------
class ValidationType(str, Enum):
    """LS-VALIDATE-TYPE PIC X(1) level-88 values."""

    ID = "I"
    ACCOUNT = "A"
    TYPE = "T"
    AMOUNT = "M"


# ---------------------------------------------------------------------------
# Result dataclass  (mirrors LS-RETURN-CODE + LS-ERROR-MSG)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class ValidationResult:
    """Matches the COBOL LINKAGE SECTION return fields.

    Attributes:
        return_code: PIC S9(4) COMP  — 0 = success, 1-4 = specific error
        error_msg:   PIC X(50)       — blank on success, descriptive on error
    """

    return_code: ValReturnCode
    error_msg: str

    @property
    def is_success(self) -> bool:
        return self.return_code == ValReturnCode.SUCCESS


def _success() -> ValidationResult:
    """MOVE VAL-SUCCESS TO LS-RETURN-CODE / MOVE SPACES TO LS-ERROR-MSG."""
    return ValidationResult(return_code=ValReturnCode.SUCCESS, error_msg="")


# ---------------------------------------------------------------------------
# 1000-VALIDATE-ID
# ---------------------------------------------------------------------------
def validate_portfolio_id(input_value: str) -> ValidationResult:
    """Portfolio ID must start with 'PORT' and have 4 numeric digits.

    COBOL logic:
        IF LS-INPUT-VALUE(1:4) NOT = VAL-ID-PREFIX  → error
        MOVE LS-INPUT-VALUE(5:4) TO VAL-NUMERIC-CHECK
        IF VAL-NUMERIC-CHECK IS NOT NUMERIC          → error
    """
    # LS-INPUT-VALUE(1:4) — COBOL substring is 1-based, length-based
    if len(input_value) < 8 or input_value[:4] != VAL_ID_PREFIX:
        return ValidationResult(
            return_code=ValReturnCode.INVALID_ID, error_msg=VAL_ERR_ID
        )

    # LS-INPUT-VALUE(5:4) — positions 5-8 (0-indexed: 4-8)
    numeric_part = input_value[4:8]
    if not numeric_part.isdigit():
        return ValidationResult(
            return_code=ValReturnCode.INVALID_ID, error_msg=VAL_ERR_ID
        )

    return _success()


# ---------------------------------------------------------------------------
# 2000-VALIDATE-ACCOUNT
# ---------------------------------------------------------------------------
def validate_account_number(input_value: str) -> ValidationResult:
    """Account number must be 10 numeric digits and not all zeros.

    COBOL logic:
        IF LS-INPUT-VALUE IS NOT NUMERIC
        OR LS-INPUT-VALUE = ZEROS  → error
    """
    # COBOL IS NUMERIC checks every character is 0-9
    # We check exactly the first 10 characters to match PIC X(10)
    account = input_value[:10]
    if not account.isdigit() or account == "0" * len(account):
        return ValidationResult(
            return_code=ValReturnCode.INVALID_ACCT, error_msg=VAL_ERR_ACCT
        )

    return _success()


# ---------------------------------------------------------------------------
# 3000-VALIDATE-TYPE
# ---------------------------------------------------------------------------
def validate_investment_type(input_value: str) -> ValidationResult:
    """Investment type must be STK, BND, MMF, or ETF.

    COBOL logic:
        IF LS-INPUT-VALUE NOT = 'STK'
           AND NOT = 'BND'
           AND NOT = 'MMF'
           AND NOT = 'ETF'  → error
    """
    # COBOL comparison uses the value as-is; strip trailing spaces to match
    # PIC X(50) which would be space-padded
    type_code = input_value.strip()
    if type_code not in VALID_INVESTMENT_TYPES:
        return ValidationResult(
            return_code=ValReturnCode.INVALID_TYPE, error_msg=VAL_ERR_TYPE
        )

    return _success()


# ---------------------------------------------------------------------------
# 4000-VALIDATE-AMOUNT
# ---------------------------------------------------------------------------
def validate_amount(input_value: str) -> ValidationResult:
    """Amount must be within [-9999999999999.99, +9999999999999.99].

    COBOL logic:
        MOVE LS-INPUT-VALUE TO VAL-TEMP-NUM       (PIC S9(13)V99)
        IF VAL-TEMP-NUM < VAL-MIN-AMOUNT
        OR VAL-TEMP-NUM > VAL-MAX-AMOUNT  → error

    The MOVE to PIC S9(13)V99 truncates to 2 decimal places. We replicate
    that by quantizing to .01 before comparing.
    """
    try:
        amount = Decimal(input_value.strip()).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        return ValidationResult(
            return_code=ValReturnCode.INVALID_AMT, error_msg=VAL_ERR_AMT
        )

    if amount < VAL_MIN_AMOUNT or amount > VAL_MAX_AMOUNT:
        return ValidationResult(
            return_code=ValReturnCode.INVALID_AMT, error_msg=VAL_ERR_AMT
        )

    return _success()


# ---------------------------------------------------------------------------
# Main dispatcher  (mirrors 0000-MAIN EVALUATE TRUE)
# ---------------------------------------------------------------------------
def validate(validate_type: str, input_value: str) -> ValidationResult:
    """Top-level dispatcher matching PORTVALD's EVALUATE TRUE.

    Args:
        validate_type: Single character — 'I', 'A', 'T', or 'M'.
        input_value:   The value to validate (PIC X(50) equivalent).

    Returns:
        ValidationResult with return_code and error_msg.
    """
    try:
        vtype = ValidationType(validate_type)
    except ValueError:
        # WHEN OTHER → MOVE VAL-INVALID-ID TO LS-RETURN-CODE
        return ValidationResult(
            return_code=ValReturnCode.INVALID_ID,
            error_msg="Invalid validation type",
        )

    dispatch = {
        ValidationType.ID: validate_portfolio_id,
        ValidationType.ACCOUNT: validate_account_number,
        ValidationType.TYPE: validate_investment_type,
        ValidationType.AMOUNT: validate_amount,
    }

    return dispatch[vtype](input_value)
