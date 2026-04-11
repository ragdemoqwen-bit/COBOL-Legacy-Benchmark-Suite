"""
Tests for the portfolio validation subroutine (converted from PORTVALD.cbl).

Covers every COBOL paragraph with valid, invalid, and edge-case inputs:
  1000-VALIDATE-ID      → Portfolio ID format
  2000-VALIDATE-ACCOUNT → Account number format
  3000-VALIDATE-TYPE    → Investment type codes
  4000-VALIDATE-AMOUNT  → Amount range check (PIC S9(13)V99)
  0000-MAIN EVALUATE    → Dispatch and invalid-type handling
"""

from decimal import Decimal

import pytest

from python_poc.validation.constants import (
    VAL_ERR_ACCT,
    VAL_ERR_AMT,
    VAL_ERR_ID,
    VAL_ERR_TYPE,
    VAL_MAX_AMOUNT,
    VAL_MIN_AMOUNT,
    ValReturnCode,
)
from python_poc.validation.portfolio_validator import (
    ValidationResult,
    ValidationType,
    validate,
    validate_account_number,
    validate_amount,
    validate_investment_type,
    validate_portfolio_id,
)


# ===================================================================
# 1000-VALIDATE-ID tests
# ===================================================================
class TestValidatePortfolioId:
    """Portfolio ID: must start with 'PORT' + 4 numeric digits."""

    # --- Valid IDs ---
    @pytest.mark.parametrize(
        "port_id",
        [
            "PORT0001",
            "PORT9999",
            "PORT0000",
            "PORT1234",
            "PORT5678",
        ],
    )
    def test_valid_ids(self, port_id: str):
        result = validate_portfolio_id(port_id)
        assert result.is_success
        assert result.return_code == ValReturnCode.SUCCESS
        assert result.error_msg == ""

    # --- Invalid prefix ---
    @pytest.mark.parametrize(
        "port_id",
        [
            "XORT0001",  # wrong first letter
            "port0001",  # lowercase
            "POST0001",  # close but wrong
            "PRT00001",  # missing one char in prefix
            "    0001",  # spaces instead of PORT
        ],
    )
    def test_invalid_prefix(self, port_id: str):
        result = validate_portfolio_id(port_id)
        assert result.return_code == ValReturnCode.INVALID_ID
        assert result.error_msg == VAL_ERR_ID

    # --- Invalid numeric part ---
    @pytest.mark.parametrize(
        "port_id",
        [
            "PORT000A",  # letter in numeric part
            "PORTABCD",  # all letters
            "PORT12.4",  # decimal point
            "PORT 001",  # space in numeric part
            "PORT-001",  # hyphen
        ],
    )
    def test_invalid_numeric_suffix(self, port_id: str):
        result = validate_portfolio_id(port_id)
        assert result.return_code == ValReturnCode.INVALID_ID
        assert result.error_msg == VAL_ERR_ID

    # --- Too short ---
    @pytest.mark.parametrize(
        "port_id",
        [
            "",
            "PORT",
            "PORT001",
            "POR",
        ],
    )
    def test_too_short(self, port_id: str):
        result = validate_portfolio_id(port_id)
        assert result.return_code == ValReturnCode.INVALID_ID

    # --- Edge: extra characters after 8 are ignored (COBOL PIC X(50)) ---
    def test_extra_chars_ignored(self):
        """COBOL only checks positions 1:4 and 5:4; extra chars are fine."""
        result = validate_portfolio_id("PORT0001EXTRASTUFF")
        assert result.is_success

    # --- Boundary: PORT0000 is valid (all zeros is valid for ID) ---
    def test_all_zeros_valid(self):
        result = validate_portfolio_id("PORT0000")
        assert result.is_success


# ===================================================================
# 2000-VALIDATE-ACCOUNT tests
# ===================================================================
class TestValidateAccountNumber:
    """Account number: must be 10 numeric digits, not all zeros."""

    # --- Valid account numbers ---
    @pytest.mark.parametrize(
        "account",
        [
            "1234567890",
            "0000000001",  # leading zeros OK as long as not ALL zeros
            "9999999999",
            "1000000000",
            "0123456789",
        ],
    )
    def test_valid_accounts(self, account: str):
        result = validate_account_number(account)
        assert result.is_success
        assert result.return_code == ValReturnCode.SUCCESS

    # --- All zeros rejected (COBOL: LS-INPUT-VALUE = ZEROS) ---
    def test_all_zeros_rejected(self):
        result = validate_account_number("0000000000")
        assert result.return_code == ValReturnCode.INVALID_ACCT
        assert result.error_msg == VAL_ERR_ACCT

    # --- Non-numeric rejected ---
    @pytest.mark.parametrize(
        "account",
        [
            "123456789A",
            "ABCDEFGHIJ",
            "12345 6789",
            "12-3456789",
            "12345.6789",
            "",
            "          ",  # all spaces
        ],
    )
    def test_non_numeric_rejected(self, account: str):
        result = validate_account_number(account)
        assert result.return_code == ValReturnCode.INVALID_ACCT
        assert result.error_msg == VAL_ERR_ACCT

    # --- Edge: short input ---
    def test_short_all_zeros(self):
        """Input shorter than 10 chars but all zeros."""
        result = validate_account_number("00000")
        assert result.return_code == ValReturnCode.INVALID_ACCT

    def test_single_digit_nonzero(self):
        """Single non-zero digit — IS NUMERIC succeeds but only 1 char."""
        result = validate_account_number("5")
        assert result.is_success  # COBOL checks the value, not length


# ===================================================================
# 3000-VALIDATE-TYPE tests
# ===================================================================
class TestValidateInvestmentType:
    """Investment type: must be STK, BND, MMF, or ETF."""

    # --- All valid types ---
    @pytest.mark.parametrize("inv_type", ["STK", "BND", "MMF", "ETF"])
    def test_valid_types(self, inv_type: str):
        result = validate_investment_type(inv_type)
        assert result.is_success
        assert result.return_code == ValReturnCode.SUCCESS

    # --- Invalid types ---
    @pytest.mark.parametrize(
        "inv_type",
        [
            "XXX",
            "stk",  # lowercase
            "STOCK",  # full word
            "BD",  # too short
            "",
            "   ",  # blank
            "MUT",  # close but wrong
            "CD ",
        ],
    )
    def test_invalid_types(self, inv_type: str):
        result = validate_investment_type(inv_type)
        assert result.return_code == ValReturnCode.INVALID_TYPE
        assert result.error_msg == VAL_ERR_TYPE

    # --- Edge: trailing spaces (COBOL PIC X(50) pads with spaces) ---
    def test_trailing_spaces_stripped(self):
        """COBOL comparison would match; we strip to replicate."""
        result = validate_investment_type("STK   ")
        assert result.is_success

    def test_leading_spaces_stripped(self):
        result = validate_investment_type("  ETF")
        assert result.is_success


# ===================================================================
# 4000-VALIDATE-AMOUNT tests
# ===================================================================
class TestValidateAmount:
    """Amount: must be within PIC S9(13)V99 range."""

    # --- Valid amounts ---
    @pytest.mark.parametrize(
        "amount_str",
        [
            "0",
            "0.00",
            "1.00",
            "-1.00",
            "12345.67",
            "-12345.67",
            "9999999999999.99",  # max
            "-9999999999999.99",  # min
            "100",
            "0.01",  # smallest positive
            "-0.01",  # smallest negative
        ],
    )
    def test_valid_amounts(self, amount_str: str):
        result = validate_amount(amount_str)
        assert result.is_success
        assert result.return_code == ValReturnCode.SUCCESS

    # --- Boundary: exactly at limits ---
    def test_exact_max(self):
        result = validate_amount(str(VAL_MAX_AMOUNT))
        assert result.is_success

    def test_exact_min(self):
        result = validate_amount(str(VAL_MIN_AMOUNT))
        assert result.is_success

    # --- Just over boundary ---
    def test_one_cent_over_max(self):
        result = validate_amount("10000000000000.00")
        assert result.return_code == ValReturnCode.INVALID_AMT
        assert result.error_msg == VAL_ERR_AMT

    def test_one_cent_under_min(self):
        result = validate_amount("-10000000000000.00")
        assert result.return_code == ValReturnCode.INVALID_AMT
        assert result.error_msg == VAL_ERR_AMT

    # --- Way over ---
    def test_huge_positive(self):
        result = validate_amount("99999999999999.99")
        assert result.return_code == ValReturnCode.INVALID_AMT

    def test_huge_negative(self):
        result = validate_amount("-99999999999999.99")
        assert result.return_code == ValReturnCode.INVALID_AMT

    # --- Non-numeric input ---
    @pytest.mark.parametrize(
        "bad_input",
        [
            "ABC",
            "",
            "twelve",
            "12.34.56",
            "$1000.00",
            "1,000.00",
        ],
    )
    def test_non_numeric_rejected(self, bad_input: str):
        result = validate_amount(bad_input)
        assert result.return_code == ValReturnCode.INVALID_AMT
        assert result.error_msg == VAL_ERR_AMT

    # --- Decimal quantization (COBOL MOVE to PIC S9(13)V99 truncates) ---
    def test_three_decimals_quantized(self):
        """0.999 quantizes to 1.00 which is in range → success."""
        result = validate_amount("0.999")
        assert result.is_success

    def test_many_decimals_quantized(self):
        """123.456789 quantizes to 123.46 → success."""
        result = validate_amount("123.456789")
        assert result.is_success

    # --- Sign handling ---
    def test_explicit_positive_sign(self):
        result = validate_amount("+500.00")
        assert result.is_success

    def test_negative_zero(self):
        result = validate_amount("-0.00")
        assert result.is_success

    # --- Whitespace handling ---
    def test_leading_trailing_spaces(self):
        result = validate_amount("  1000.00  ")
        assert result.is_success


# ===================================================================
# 0000-MAIN EVALUATE dispatch tests
# ===================================================================
class TestValidateDispatch:
    """Tests for the top-level validate() dispatcher."""

    def test_dispatch_id_valid(self):
        result = validate("I", "PORT0001")
        assert result.is_success

    def test_dispatch_id_invalid(self):
        result = validate("I", "BADID001")
        assert result.return_code == ValReturnCode.INVALID_ID

    def test_dispatch_account_valid(self):
        result = validate("A", "1234567890")
        assert result.is_success

    def test_dispatch_account_invalid(self):
        result = validate("A", "0000000000")
        assert result.return_code == ValReturnCode.INVALID_ACCT

    def test_dispatch_type_valid(self):
        result = validate("T", "STK")
        assert result.is_success

    def test_dispatch_type_invalid(self):
        result = validate("T", "XXX")
        assert result.return_code == ValReturnCode.INVALID_TYPE

    def test_dispatch_amount_valid(self):
        result = validate("M", "12345.67")
        assert result.is_success

    def test_dispatch_amount_invalid(self):
        result = validate("M", "ABC")
        assert result.return_code == ValReturnCode.INVALID_AMT

    # --- WHEN OTHER: invalid validation type ---
    @pytest.mark.parametrize("bad_type", ["X", "Z", "1", " ", ""])
    def test_invalid_validation_type(self, bad_type: str):
        result = validate(bad_type, "anything")
        assert result.return_code == ValReturnCode.INVALID_ID
        assert result.error_msg == "Invalid validation type"


# ===================================================================
# Synthetic edge-case / stress tests
# ===================================================================
class TestSyntheticEdgeCases:
    """Additional edge cases based on COBOL field definitions."""

    def test_amount_at_one_penny(self):
        """Smallest non-zero amount."""
        result = validate_amount("0.01")
        assert result.is_success

    def test_amount_at_negative_one_penny(self):
        result = validate_amount("-0.01")
        assert result.is_success

    def test_portfolio_id_boundary_prefix_match(self):
        """'PORT' followed by exactly boundary numeric values."""
        assert validate_portfolio_id("PORT0000").is_success
        assert validate_portfolio_id("PORT9999").is_success

    def test_account_single_one(self):
        """Account '0000000001' — not all zeros, should pass."""
        assert validate_account_number("0000000001").is_success

    def test_account_all_nines(self):
        assert validate_account_number("9999999999").is_success

    def test_amount_sign_flip_boundary(self):
        """Flip the sign of the max value — should still be in range."""
        max_val = VAL_MAX_AMOUNT
        min_val = -max_val
        assert validate_amount(str(min_val)).is_success

    def test_amount_sign_flip_min(self):
        """Flip the sign of the min value — should become max → in range."""
        min_val = VAL_MIN_AMOUNT
        max_val = -min_val
        assert validate_amount(str(max_val)).is_success

    def test_all_validation_types_enumerated(self):
        """Ensure every ValidationType enum member has a dispatch entry."""
        for vtype in ValidationType:
            # Just verify it doesn't raise; use a generic valid input
            result = validate(vtype.value, "PORT0001")
            assert isinstance(result, ValidationResult)
