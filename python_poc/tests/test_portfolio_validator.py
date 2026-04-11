"""
Tests for the PortfolioValidator module (converted from PORTVALD.cbl).

Covers all four validation types from the COBOL program:
  1000-VALIDATE-ID      — Portfolio ID format
  2000-VALIDATE-ACCOUNT — Account number format
  3000-VALIDATE-TYPE    — Investment type
  4000-VALIDATE-AMOUNT  — Amount range (PIC S9(13)V99 bounds)

Each section includes:
  - Valid inputs
  - Invalid inputs
  - Boundary values
  - Edge cases (empty strings, whitespace, special characters)
  - Sign flips for amounts
"""

import pytest

from python_poc.src.validators.portfolio_validator import (
    InvestmentType,
    PortfolioValidator,
    ValidationResult,
    ValidationReturnCode,
    ValidationType,
    VAL_ERR_ACCT,
    VAL_ERR_AMT,
    VAL_ERR_ID,
    VAL_ERR_TYPE,
    VAL_MAX_AMOUNT,
    VAL_MIN_AMOUNT,
)


@pytest.fixture
def validator() -> PortfolioValidator:
    return PortfolioValidator()


# ================================================================
# 1000-VALIDATE-ID — Portfolio ID
# ================================================================

class TestValidatePortfolioId:
    """
    COBOL rules:
      - Must start with 'PORT' (VAL-ID-PREFIX)
      - Positions 5-8 must be numeric (4 digits)
    """

    # --- Valid IDs ---

    def test_valid_port0001(self, validator):
        result = validator.validate_portfolio_id("PORT0001")
        assert result.is_valid
        assert result.return_code == ValidationReturnCode.SUCCESS
        assert result.error_msg == ""

    def test_valid_port9999(self, validator):
        """Upper boundary of the numeric suffix."""
        result = validator.validate_portfolio_id("PORT9999")
        assert result.is_valid

    def test_valid_port0000(self, validator):
        """Lower boundary — 0000 is valid (just digits, not account-style zero check)."""
        result = validator.validate_portfolio_id("PORT0000")
        assert result.is_valid

    def test_valid_port5432(self, validator):
        result = validator.validate_portfolio_id("PORT5432")
        assert result.is_valid

    # --- Invalid IDs ---

    def test_wrong_prefix(self, validator):
        result = validator.validate_portfolio_id("ACCT0001")
        assert not result.is_valid
        assert result.return_code == ValidationReturnCode.INVALID_ID
        assert result.error_msg == VAL_ERR_ID

    def test_lowercase_prefix(self, validator):
        """COBOL comparison is case-sensitive — 'port' != 'PORT'."""
        result = validator.validate_portfolio_id("port0001")
        assert not result.is_valid

    def test_non_numeric_suffix(self, validator):
        result = validator.validate_portfolio_id("PORTABCD")
        assert not result.is_valid
        assert result.return_code == ValidationReturnCode.INVALID_ID

    def test_partial_numeric_suffix(self, validator):
        result = validator.validate_portfolio_id("PORT12AB")
        assert not result.is_valid

    def test_too_short(self, validator):
        result = validator.validate_portfolio_id("PORT001")
        assert not result.is_valid

    def test_empty_string(self, validator):
        result = validator.validate_portfolio_id("")
        assert not result.is_valid

    def test_spaces_only(self, validator):
        result = validator.validate_portfolio_id("        ")
        assert not result.is_valid

    def test_special_characters_in_suffix(self, validator):
        result = validator.validate_portfolio_id("PORT@#$%")
        assert not result.is_valid

    def test_suffix_with_spaces(self, validator):
        result = validator.validate_portfolio_id("PORT 001")
        assert not result.is_valid

    # --- Dispatch via validate() ---

    def test_dispatch_portfolio_id(self, validator):
        """Test the EVALUATE TRUE dispatcher for type 'I'."""
        result = validator.validate(ValidationType.PORTFOLIO_ID, "PORT0001")
        assert result.is_valid


# ================================================================
# 2000-VALIDATE-ACCOUNT — Account Number
# ================================================================

class TestValidateAccount:
    """
    COBOL rules:
      - Must be numeric (IS NUMERIC)
      - Must not be all zeros (NOT = ZEROS)
      - Account number is PIC X(10) per PORTFLIO.cpy
    """

    # --- Valid accounts ---

    def test_valid_account(self, validator):
        result = validator.validate_account("1234567890")
        assert result.is_valid

    def test_valid_account_leading_zeros(self, validator):
        """Leading zeros are valid — just not ALL zeros."""
        result = validator.validate_account("0000000001")
        assert result.is_valid

    def test_valid_account_max_value(self, validator):
        result = validator.validate_account("9999999999")
        assert result.is_valid

    def test_valid_account_min_nonzero(self, validator):
        result = validator.validate_account("0000000001")
        assert result.is_valid

    # --- Invalid accounts ---

    def test_all_zeros_rejected(self, validator):
        """COBOL: OR LS-INPUT-VALUE = ZEROS."""
        result = validator.validate_account("0000000000")
        assert not result.is_valid
        assert result.return_code == ValidationReturnCode.INVALID_ACCT
        assert result.error_msg == VAL_ERR_ACCT

    def test_non_numeric(self, validator):
        result = validator.validate_account("12345ABCDE")
        assert not result.is_valid

    def test_too_short(self, validator):
        result = validator.validate_account("123456789")
        assert not result.is_valid

    def test_too_long(self, validator):
        result = validator.validate_account("12345678901")
        assert not result.is_valid

    def test_empty_string(self, validator):
        result = validator.validate_account("")
        assert not result.is_valid

    def test_spaces(self, validator):
        result = validator.validate_account("          ")
        assert not result.is_valid

    def test_special_chars(self, validator):
        result = validator.validate_account("123-456-78")
        assert not result.is_valid

    def test_account_with_decimal(self, validator):
        result = validator.validate_account("123456.890")
        assert not result.is_valid

    # --- Dispatch ---

    def test_dispatch_account(self, validator):
        result = validator.validate(ValidationType.ACCOUNT, "1234567890")
        assert result.is_valid


# ================================================================
# 3000-VALIDATE-TYPE — Investment Type
# ================================================================

class TestValidateInvestmentType:
    """
    COBOL rules:
      - Must be one of: 'STK', 'BND', 'MMF', 'ETF'
    """

    # --- Valid types ---

    @pytest.mark.parametrize("inv_type", ["STK", "BND", "MMF", "ETF"])
    def test_valid_types(self, validator, inv_type):
        result = validator.validate_investment_type(inv_type)
        assert result.is_valid

    def test_stk_maps_to_stock_enum(self):
        assert InvestmentType.STOCK.value == "STK"

    def test_bnd_maps_to_bond_enum(self):
        assert InvestmentType.BOND.value == "BND"

    def test_mmf_maps_to_money_market_enum(self):
        assert InvestmentType.MONEY_MARKET.value == "MMF"

    def test_etf_maps_to_etf_enum(self):
        assert InvestmentType.ETF.value == "ETF"

    # --- Invalid types ---

    def test_invalid_type(self, validator):
        result = validator.validate_investment_type("MUT")
        assert not result.is_valid
        assert result.return_code == ValidationReturnCode.INVALID_TYPE
        assert result.error_msg == VAL_ERR_TYPE

    def test_lowercase_rejected(self, validator):
        """COBOL string comparison is case-sensitive."""
        result = validator.validate_investment_type("stk")
        assert not result.is_valid

    def test_empty_string(self, validator):
        result = validator.validate_investment_type("")
        assert not result.is_valid

    def test_partial_match(self, validator):
        result = validator.validate_investment_type("ST")
        assert not result.is_valid

    def test_extra_chars(self, validator):
        result = validator.validate_investment_type("STKA")
        assert not result.is_valid

    def test_spaces(self, validator):
        result = validator.validate_investment_type("   ")
        assert not result.is_valid

    # --- With trailing spaces (COBOL PIC X(50) padding) ---

    def test_type_with_trailing_spaces(self, validator):
        """COBOL PIC X(50) would pad with spaces — we strip them."""
        result = validator.validate_investment_type("STK                    ")
        assert result.is_valid

    # --- Dispatch ---

    def test_dispatch_type(self, validator):
        result = validator.validate(ValidationType.INVESTMENT_TYPE, "ETF")
        assert result.is_valid


# ================================================================
# 4000-VALIDATE-AMOUNT — Amount Range
# ================================================================

class TestValidateAmount:
    """
    COBOL rules:
      - Amount must be >= VAL-MIN-AMOUNT (-9999999999999.99)
      - Amount must be <= VAL-MAX-AMOUNT (+9999999999999.99)
      - PIC S9(13)V99 — signed, 13 integer digits, 2 fractional
    """

    # --- Valid amounts ---

    def test_valid_positive(self, validator):
        result = validator.validate_amount("12345.67")
        assert result.is_valid

    def test_valid_negative(self, validator):
        result = validator.validate_amount("-12345.67")
        assert result.is_valid

    def test_valid_zero(self, validator):
        result = validator.validate_amount("0")
        assert result.is_valid

    def test_valid_zero_decimal(self, validator):
        result = validator.validate_amount("0.00")
        assert result.is_valid

    def test_valid_integer(self, validator):
        result = validator.validate_amount("1000")
        assert result.is_valid

    def test_valid_one_cent(self, validator):
        result = validator.validate_amount("0.01")
        assert result.is_valid

    def test_valid_negative_one_cent(self, validator):
        result = validator.validate_amount("-0.01")
        assert result.is_valid

    # --- Boundary values ---

    def test_max_amount_exact(self, validator):
        result = validator.validate_amount("9999999999999.99")
        assert result.is_valid

    def test_min_amount_exact(self, validator):
        result = validator.validate_amount("-9999999999999.99")
        assert result.is_valid

    def test_one_cent_over_max(self, validator):
        result = validator.validate_amount("10000000000000.00")
        assert not result.is_valid
        assert result.return_code == ValidationReturnCode.INVALID_AMT
        assert result.error_msg == VAL_ERR_AMT

    def test_one_cent_below_min(self, validator):
        result = validator.validate_amount("-10000000000000.00")
        assert not result.is_valid
        assert result.return_code == ValidationReturnCode.INVALID_AMT

    def test_just_below_max(self, validator):
        """9999999999999.98 — one cent below max."""
        result = validator.validate_amount("9999999999999.98")
        assert result.is_valid

    def test_just_above_min(self, validator):
        """-9999999999999.98 — one cent above min."""
        result = validator.validate_amount("-9999999999999.98")
        assert result.is_valid

    # --- Sign flips ---

    def test_sign_flip_positive_max(self, validator):
        """Positive max boundary."""
        result = validator.validate_amount(str(VAL_MAX_AMOUNT))
        assert result.is_valid

    def test_sign_flip_negative_max(self, validator):
        """Negative max boundary (most negative value)."""
        result = validator.validate_amount(str(VAL_MIN_AMOUNT))
        assert result.is_valid

    def test_sign_flip_cross_zero(self, validator):
        """Both +0.01 and -0.01 are valid."""
        assert validator.validate_amount("0.01").is_valid
        assert validator.validate_amount("-0.01").is_valid

    # --- Invalid amounts ---

    def test_non_numeric(self, validator):
        result = validator.validate_amount("abc")
        assert not result.is_valid
        assert result.return_code == ValidationReturnCode.INVALID_AMT

    def test_empty_string(self, validator):
        result = validator.validate_amount("")
        assert not result.is_valid

    def test_spaces_only(self, validator):
        result = validator.validate_amount("   ")
        assert not result.is_valid

    def test_special_characters(self, validator):
        result = validator.validate_amount("$1,000.00")
        assert not result.is_valid

    def test_multiple_decimal_points(self, validator):
        result = validator.validate_amount("100.00.00")
        assert not result.is_valid

    def test_huge_overflow(self, validator):
        result = validator.validate_amount("99999999999999999.99")
        assert not result.is_valid

    # --- With trailing spaces (COBOL PIC X(50) padding) ---

    def test_amount_with_trailing_spaces(self, validator):
        result = validator.validate_amount("12345.67                    ")
        assert result.is_valid

    # --- Dispatch ---

    def test_dispatch_amount(self, validator):
        result = validator.validate(ValidationType.AMOUNT, "500.00")
        assert result.is_valid


# ================================================================
# Dispatcher — invalid validation type
# ================================================================

class TestDispatcherEdgeCases:
    """Test the EVALUATE TRUE WHEN OTHER branch."""

    def test_all_validation_types_dispatch(self, validator):
        """Ensure every ValidationType enum value dispatches correctly."""
        test_cases = {
            ValidationType.PORTFOLIO_ID: "PORT0001",
            ValidationType.ACCOUNT: "1234567890",
            ValidationType.INVESTMENT_TYPE: "STK",
            ValidationType.AMOUNT: "100.00",
        }
        for vtype, value in test_cases.items():
            result = validator.validate(vtype, value)
            assert result.is_valid, f"Failed for {vtype} with value {value}"


# ================================================================
# ValidationResult dataclass
# ================================================================

class TestValidationResult:
    def test_success_result(self):
        r = ValidationResult(return_code=ValidationReturnCode.SUCCESS, error_msg="")
        assert r.is_valid
        assert r.return_code == 0
        assert r.error_msg == ""

    def test_error_result(self):
        r = ValidationResult(
            return_code=ValidationReturnCode.INVALID_ID,
            error_msg=VAL_ERR_ID,
        )
        assert not r.is_valid
        assert r.return_code == 1
        assert r.error_msg == VAL_ERR_ID

    def test_result_is_frozen(self):
        """ValidationResult is a frozen dataclass — immutable."""
        r = ValidationResult(return_code=ValidationReturnCode.SUCCESS, error_msg="")
        with pytest.raises(AttributeError):
            r.return_code = ValidationReturnCode.INVALID_ID


# ================================================================
# Synthetic test data matrix
# ================================================================

class TestSyntheticDataMatrix:
    """
    Comprehensive synthetic data generated from COBOL copybook definitions.
    Tests valid + invalid + boundary + edge cases in a parametrized matrix.
    """

    # --- Portfolio ID matrix ---
    @pytest.mark.parametrize(
        "value,expected_valid",
        [
            # Valid
            ("PORT0001", True),
            ("PORT0000", True),
            ("PORT9999", True),
            ("PORT1234", True),
            # Invalid prefix
            ("ACCT0001", False),
            ("port0001", False),
            ("POR10001", False),
            ("XORT0001", False),
            ("    0001", False),
            # Invalid suffix
            ("PORTABCD", False),
            ("PORT    ", False),
            ("PORT-001", False),
            ("PORT001", False),   # too short
            ("PORT00001", True),   # 9 chars — COBOL checks (1:4)='PORT' and (5:4) numeric; extra chars ignored
            # Edge cases
            ("", False),
            ("PORT", False),
        ],
        ids=lambda v: f"id={v[0] if isinstance(v, tuple) else v!r}",
    )
    def test_portfolio_id_matrix(self, validator, value, expected_valid):
        result = validator.validate_portfolio_id(value)
        assert result.is_valid == expected_valid, (
            f"Portfolio ID '{value}': expected valid={expected_valid}, "
            f"got rc={result.return_code}, msg={result.error_msg!r}"
        )

    # --- Account number matrix ---
    @pytest.mark.parametrize(
        "value,expected_valid",
        [
            # Valid
            ("1234567890", True),
            ("0000000001", True),
            ("9999999999", True),
            ("0123456789", True),
            # Invalid — all zeros
            ("0000000000", False),
            # Invalid — non-numeric
            ("12345ABCDE", False),
            ("123456789 ", False),
            ("123-456789", False),
            # Invalid — wrong length
            ("123456789", False),
            ("12345678901", False),
            # Edge cases
            ("", False),
            ("          ", False),
        ],
    )
    def test_account_matrix(self, validator, value, expected_valid):
        result = validator.validate_account(value)
        assert result.is_valid == expected_valid

    # --- Investment type matrix ---
    @pytest.mark.parametrize(
        "value,expected_valid",
        [
            ("STK", True),
            ("BND", True),
            ("MMF", True),
            ("ETF", True),
            ("stk", False),
            ("MUT", False),
            ("ST", False),
            ("STKA", False),
            ("", False),
            ("   ", False),
            ("STK   ", True),  # trailing spaces stripped
        ],
    )
    def test_investment_type_matrix(self, validator, value, expected_valid):
        result = validator.validate_investment_type(value)
        assert result.is_valid == expected_valid

    # --- Amount matrix (boundary values + sign flips) ---
    @pytest.mark.parametrize(
        "value,expected_valid",
        [
            # Valid amounts
            ("0", True),
            ("0.00", True),
            ("0.01", True),
            ("-0.01", True),
            ("100.50", True),
            ("-100.50", True),
            ("9999999999999.99", True),    # max
            ("-9999999999999.99", True),   # min
            ("9999999999999.98", True),    # just below max
            ("-9999999999999.98", True),   # just above min
            ("1", True),
            ("-1", True),
            # Overflow
            ("10000000000000.00", False),
            ("-10000000000000.00", False),
            ("99999999999999.99", False),
            ("-99999999999999.99", False),
            # Invalid format
            ("abc", False),
            ("", False),
            ("   ", False),
            ("$100", False),
            ("1,000.00", False),
            ("100.00.00", False),
        ],
    )
    def test_amount_matrix(self, validator, value, expected_valid):
        result = validator.validate_amount(value)
        assert result.is_valid == expected_valid, (
            f"Amount '{value}': expected valid={expected_valid}, "
            f"got rc={result.return_code}, msg={result.error_msg!r}"
        )
