"""
Portfolio Validation — converted from PORTVALD.cbl (121 LOC).

Replaces: COBOL PORTVALD subroutine — validates portfolio ID, account number,
          investment type, and amount with EVALUATE TRUE dispatch.
Target:   Python validation functions with ValidationReturnCode.

This is the production version of the POC validation done in python_poc/.

COBOL interface (LINKAGE SECTION):
  LS-VALIDATE-REQUEST:
    LS-VAL-FUNCTION  PIC X(4)  — 'ID  '/'ACCT'/'TYPE'/'AMT '
    LS-VAL-DATA      PIC X(50)
    LS-VAL-RETURN-CODE PIC S9(4) COMP
"""

import logging
from decimal import Decimal, InvalidOperation

from models.enums import InvestmentType, ValidationReturnCode

logger = logging.getLogger(__name__)

# COMP-3 PIC S9(13)V99 boundaries (from PORTVAL.cpy)
_COMP3_MAX = Decimal("9999999999999.99")
_COMP3_MIN = Decimal("-9999999999999.99")


class PortfolioValidatorService:
    """
    Validates portfolio fields — replaces PORTVALD.cbl.

    COBOL EVALUATE TRUE dispatch on LS-VAL-FUNCTION:
      'ID  ' → validate_portfolio_id()
      'ACCT' → validate_account_number()
      'TYPE' → validate_investment_type()
      'AMT ' → validate_amount()
    """

    def validate_portfolio_id(self, portfolio_id: str) -> ValidationReturnCode:
        """
        Validate portfolio ID format.

        Replaces: 2000-VALIDATE-ID paragraph.
        Rules: Must be non-empty, max 8 chars, alphanumeric.
        """
        if not portfolio_id or not portfolio_id.strip():
            return ValidationReturnCode.INVALID_ID
        if len(portfolio_id) > 8:
            return ValidationReturnCode.INVALID_ID
        if not portfolio_id.strip().isalnum():
            return ValidationReturnCode.INVALID_ID
        return ValidationReturnCode.SUCCESS

    def validate_account_number(self, account_no: str) -> ValidationReturnCode:
        """
        Validate account number format.

        Replaces: 3000-VALIDATE-ACCOUNT paragraph.
        Rules: Must be non-empty, max 10 chars, first char must be digit.
        """
        if not account_no or not account_no.strip():
            return ValidationReturnCode.INVALID_ACCT
        cleaned = account_no.strip()
        if len(cleaned) > 10:
            return ValidationReturnCode.INVALID_ACCT
        if not cleaned[0].isdigit():
            return ValidationReturnCode.INVALID_ACCT
        return ValidationReturnCode.SUCCESS

    def validate_investment_type(self, inv_type: str) -> ValidationReturnCode:
        """
        Validate investment type against allowed values.

        Replaces: 4000-VALIDATE-TYPE paragraph.
        Valid types: STK, BND, MMF, ETF (from PORTVAL.cpy).
        """
        try:
            InvestmentType(inv_type)
            return ValidationReturnCode.SUCCESS
        except ValueError:
            return ValidationReturnCode.INVALID_TYPE

    def validate_amount(self, amount: Decimal | str | int | float) -> ValidationReturnCode:
        """
        Validate amount is within COMP-3 S9(13)V99 range.

        Replaces: 5000-VALIDATE-AMOUNT paragraph.
        """
        try:
            d = Decimal(str(amount))
        except (InvalidOperation, ValueError):
            return ValidationReturnCode.INVALID_AMT

        if d.is_nan() or d.is_infinite():
            return ValidationReturnCode.INVALID_AMT
        if not (_COMP3_MIN <= d <= _COMP3_MAX):
            return ValidationReturnCode.INVALID_AMT
        return ValidationReturnCode.SUCCESS

    def dispatch(self, function_code: str, data: str) -> ValidationReturnCode:
        """
        Main dispatch — replaces PORTVALD.cbl EVALUATE TRUE.
        """
        func = function_code.strip().upper()
        if func == "ID":
            return self.validate_portfolio_id(data)
        if func == "ACCT":
            return self.validate_account_number(data)
        if func == "TYPE":
            return self.validate_investment_type(data)
        if func == "AMT":
            return self.validate_amount(data)
        logger.error("Invalid validation function: '%s'", function_code)
        return ValidationReturnCode.INVALID_ID
