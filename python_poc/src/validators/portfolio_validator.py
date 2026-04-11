"""
Portfolio Validation Module — converted from COBOL program PORTVALD.cbl.

Source: src/programs/portfolio/PORTVALD.cbl
Copybook: src/copybook/common/PORTVAL.cpy

This module replicates the exact validation logic from the COBOL subroutine:
  - Portfolio ID validation (prefix + numeric suffix)
  - Account number validation (10 numeric digits, non-zero)
  - Investment type validation (STK/BND/MMF/ETF)
  - Amount range validation (PIC S9(13)V99 bounds)

The COBOL program is a callable subroutine (CALL 'PORTVALD' USING LS-VALIDATION-REQUEST)
that dispatches on LS-VALIDATE-TYPE. In Python this becomes a class with methods.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum, IntEnum


# ----------------------------------------------------------------
# COBOL PORTVAL.cpy → Validation constants
# ----------------------------------------------------------------

class ValidationType(str, Enum):
    """
    COBOL level-88 conditions on LS-VALIDATE-TYPE:
      88 LS-VAL-ID    VALUE 'I'.
      88 LS-VAL-ACCT  VALUE 'A'.
      88 LS-VAL-TYPE  VALUE 'T'.
      88 LS-VAL-AMT   VALUE 'M'.
    """
    PORTFOLIO_ID = "I"
    ACCOUNT = "A"
    INVESTMENT_TYPE = "T"
    AMOUNT = "M"


class ValidationReturnCode(IntEnum):
    """
    COBOL VAL-RETURN-CODES from PORTVAL.cpy:
      05 VAL-SUCCESS       PIC S9(4) VALUE +0.
      05 VAL-INVALID-ID    PIC S9(4) VALUE +1.
      05 VAL-INVALID-ACCT  PIC S9(4) VALUE +2.
      05 VAL-INVALID-TYPE  PIC S9(4) VALUE +3.
      05 VAL-INVALID-AMT   PIC S9(4) VALUE +4.
    """
    SUCCESS = 0
    INVALID_ID = 1
    INVALID_ACCT = 2
    INVALID_TYPE = 3
    INVALID_AMT = 4


class InvestmentType(str, Enum):
    """
    Valid investment types from PORTVALD.cbl 3000-VALIDATE-TYPE:
      'STK' = Stock
      'BND' = Bond
      'MMF' = Money Market Fund
      'ETF' = Exchange-Traded Fund
    """
    STOCK = "STK"
    BOND = "BND"
    MONEY_MARKET = "MMF"
    ETF = "ETF"


# ----------------------------------------------------------------
# Validation constants from PORTVAL.cpy
# ----------------------------------------------------------------

# VAL-ID-PREFIX  PIC X(4) VALUE 'PORT'.
VAL_ID_PREFIX = "PORT"

# VAL-MIN-AMOUNT  PIC S9(13)V99 VALUE -9999999999999.99.
# VAL-MAX-AMOUNT  PIC S9(13)V99 VALUE +9999999999999.99.
VAL_MIN_AMOUNT = Decimal("-9999999999999.99")
VAL_MAX_AMOUNT = Decimal("9999999999999.99")

# Error messages from PORTVAL.cpy
VAL_ERR_ID = "Invalid Portfolio ID format"
VAL_ERR_ACCT = "Invalid Account Number format"
VAL_ERR_TYPE = "Invalid Investment Type"
VAL_ERR_AMT = "Amount outside valid range"


# ----------------------------------------------------------------
# Validation result (replaces COBOL LS-VALIDATION-REQUEST output)
# ----------------------------------------------------------------

@dataclass(frozen=True)
class ValidationResult:
    """
    Maps to the output portion of COBOL LINKAGE SECTION:
      05 LS-RETURN-CODE  PIC S9(4) COMP.
      05 LS-ERROR-MSG    PIC X(50).
    """
    return_code: ValidationReturnCode
    error_msg: str

    @property
    def is_valid(self) -> bool:
        return self.return_code == ValidationReturnCode.SUCCESS


# ----------------------------------------------------------------
# Portfolio Validator (replaces COBOL program PORTVALD)
# ----------------------------------------------------------------

class PortfolioValidator:
    """
    Python equivalent of the COBOL PORTVALD subroutine.

    The COBOL program dispatches on LS-VALIDATE-TYPE via EVALUATE TRUE.
    In Python, callers either use validate() with a type code (preserving
    the COBOL interface) or call individual methods directly.

    Each validation method returns a ValidationResult matching the COBOL
    return codes and error messages exactly.
    """

    # Pre-compiled regex for the numeric suffix of portfolio ID
    _NUMERIC_PATTERN = re.compile(r"^\d{4}$")
    # Account must be exactly 10 digits, non-zero
    _ACCOUNT_PATTERN = re.compile(r"^\d{10}$")

    # Valid investment types as a set for O(1) lookup
    _VALID_INVESTMENT_TYPES = frozenset(t.value for t in InvestmentType)

    def validate(
        self,
        validation_type: ValidationType,
        input_value: str,
    ) -> ValidationResult:
        """
        Dispatcher matching COBOL EVALUATE TRUE in 0000-MAIN.

        Args:
            validation_type: Which validation to perform (maps to LS-VALIDATE-TYPE)
            input_value: The value to validate (maps to LS-INPUT-VALUE PIC X(50))

        Returns:
            ValidationResult with return_code and error_msg
        """
        if validation_type == ValidationType.PORTFOLIO_ID:
            return self.validate_portfolio_id(input_value)
        elif validation_type == ValidationType.ACCOUNT:
            return self.validate_account(input_value)
        elif validation_type == ValidationType.INVESTMENT_TYPE:
            return self.validate_investment_type(input_value)
        elif validation_type == ValidationType.AMOUNT:
            return self.validate_amount(input_value)
        else:
            # WHEN OTHER branch in COBOL
            return ValidationResult(
                return_code=ValidationReturnCode.INVALID_ID,
                error_msg="Invalid validation type",
            )

    def validate_portfolio_id(self, value: str) -> ValidationResult:
        """
        1000-VALIDATE-ID from PORTVALD.cbl.

        Portfolio ID must:
          1. Start with 'PORT' (VAL-ID-PREFIX)
          2. Be followed by exactly 4 numeric digits

        COBOL logic:
          IF LS-INPUT-VALUE(1:4) NOT = VAL-ID-PREFIX → reject
          MOVE LS-INPUT-VALUE(5:4) TO VAL-NUMERIC-CHECK
          IF VAL-NUMERIC-CHECK IS NOT NUMERIC → reject
        """
        # Check prefix — COBOL substring (1:4) is 1-based, length 4
        if len(value) < 8 or value[:4] != VAL_ID_PREFIX:
            return ValidationResult(
                return_code=ValidationReturnCode.INVALID_ID,
                error_msg=VAL_ERR_ID,
            )

        # Check numeric suffix — COBOL substring (5:4) is positions 5-8
        suffix = value[4:8]
        if not self._NUMERIC_PATTERN.match(suffix):
            return ValidationResult(
                return_code=ValidationReturnCode.INVALID_ID,
                error_msg=VAL_ERR_ID,
            )

        return ValidationResult(
            return_code=ValidationReturnCode.SUCCESS,
            error_msg="",
        )

    def validate_account(self, value: str) -> ValidationResult:
        """
        2000-VALIDATE-ACCOUNT from PORTVALD.cbl.

        Account number must:
          1. Be numeric (IS NUMERIC test)
          2. Not be all zeros (NOT = ZEROS)

        COBOL logic:
          IF LS-INPUT-VALUE IS NOT NUMERIC
          OR LS-INPUT-VALUE = ZEROS
              → reject

        Note: The COBOL IS NUMERIC test on PIC X checks that all characters
        are digits 0-9. The ZEROS test checks if the value equals all '0' chars.
        The input is PIC X(50) but account numbers are PIC X(10) per PORTFLIO.cpy,
        so we check for 10 digits.
        """
        # Strip trailing spaces (COBOL PIC X(50) would be space-padded)
        stripped = value.strip()

        if not self._ACCOUNT_PATTERN.match(stripped):
            return ValidationResult(
                return_code=ValidationReturnCode.INVALID_ACCT,
                error_msg=VAL_ERR_ACCT,
            )

        # COBOL: OR LS-INPUT-VALUE = ZEROS
        if stripped == "0" * 10:
            return ValidationResult(
                return_code=ValidationReturnCode.INVALID_ACCT,
                error_msg=VAL_ERR_ACCT,
            )

        return ValidationResult(
            return_code=ValidationReturnCode.SUCCESS,
            error_msg="",
        )

    def validate_investment_type(self, value: str) -> ValidationResult:
        """
        3000-VALIDATE-TYPE from PORTVALD.cbl.

        Investment type must be one of: STK, BND, MMF, ETF.

        COBOL logic:
          IF LS-INPUT-VALUE NOT = 'STK'
             AND NOT = 'BND'
             AND NOT = 'MMF'
             AND NOT = 'ETF'
              → reject
        """
        # Strip trailing spaces from PIC X(50) input
        stripped = value.strip()

        if stripped not in self._VALID_INVESTMENT_TYPES:
            return ValidationResult(
                return_code=ValidationReturnCode.INVALID_TYPE,
                error_msg=VAL_ERR_TYPE,
            )

        return ValidationResult(
            return_code=ValidationReturnCode.SUCCESS,
            error_msg="",
        )

    def validate_amount(self, value: str) -> ValidationResult:
        """
        4000-VALIDATE-AMOUNT from PORTVALD.cbl.

        Amount must be within valid range:
          VAL-MIN-AMOUNT = -9999999999999.99  (PIC S9(13)V99)
          VAL-MAX-AMOUNT = +9999999999999.99  (PIC S9(13)V99)

        COBOL logic:
          MOVE LS-INPUT-VALUE TO VAL-TEMP-NUM
          IF VAL-TEMP-NUM < VAL-MIN-AMOUNT
          OR VAL-TEMP-NUM > VAL-MAX-AMOUNT
              → reject

        The COBOL MOVE from PIC X to PIC S9(13)V99 performs an implicit
        numeric conversion. We use Decimal for exact representation.
        """
        try:
            amount = Decimal(value.strip())
        except Exception:
            return ValidationResult(
                return_code=ValidationReturnCode.INVALID_AMT,
                error_msg=VAL_ERR_AMT,
            )

        if amount < VAL_MIN_AMOUNT or amount > VAL_MAX_AMOUNT:
            return ValidationResult(
                return_code=ValidationReturnCode.INVALID_AMT,
                error_msg=VAL_ERR_AMT,
            )

        return ValidationResult(
            return_code=ValidationReturnCode.SUCCESS,
            error_msg="",
        )
