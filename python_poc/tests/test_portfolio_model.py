"""
Tests for the PortfolioRecord Pydantic model (converted from PORTFLIO.cpy).

Covers:
  - Valid record construction with all field groups
  - COMP-3 packed-decimal precision (PIC S9(13)V99)
  - Boundary values at the exact COMP-3 limits
  - Sign handling (positive, negative, zero)
  - Overflow rejection beyond COMP-3 range
  - Decimal quantization to exactly 2 places
  - Enum validation for ClientType and PortfolioStatus
  - Field length constraints matching PIC X(n) widths
  - Cross-field business rules (closed portfolio + positive balance)
  - NaN / Infinity rejection
"""

from decimal import Decimal

import pytest

from python_poc.models.portfolio import (
    COMP3_MAX_VALUE,
    COMP3_MIN_VALUE,
    ClientType,
    PortfolioAuditInfo,
    PortfolioClientInfo,
    PortfolioFinancialInfo,
    PortfolioInfo,
    PortfolioKey,
    PortfolioRecord,
    PortfolioStatus,
)


# ===================================================================
# Helper: build a valid record with overridable fields
# ===================================================================
def _make_record(**overrides) -> PortfolioRecord:
    """Build a valid PortfolioRecord with sensible defaults."""
    defaults = dict(
        key=PortfolioKey(port_id="PORT0001", port_account_no="1234567890"),
        client_info=PortfolioClientInfo(
            port_client_name="ACME Corporation",
            port_client_type=ClientType.CORPORATE,
        ),
        portfolio_info=PortfolioInfo(
            port_create_date="20240320",
            port_last_maint="20240320",
            port_status=PortfolioStatus.ACTIVE,
        ),
        financial_info=PortfolioFinancialInfo(
            port_total_value=Decimal("100000.00"),
            port_cash_balance=Decimal("25000.00"),
        ),
        audit_info=PortfolioAuditInfo(
            port_last_user="JSMITH",
            port_last_trans="20240320",
        ),
    )
    defaults.update(overrides)
    return PortfolioRecord(**defaults)


# ===================================================================
# 1. Valid record construction
# ===================================================================
class TestValidRecordConstruction:
    def test_minimal_valid_record(self):
        rec = _make_record()
        assert rec.key.port_id == "PORT0001"
        assert rec.key.port_account_no == "1234567890"
        assert rec.client_info.port_client_type == ClientType.CORPORATE
        assert rec.portfolio_info.port_status == PortfolioStatus.ACTIVE
        assert rec.financial_info.port_total_value == Decimal("100000.00")
        assert rec.financial_info.port_cash_balance == Decimal("25000.00")

    def test_individual_client_type(self):
        rec = _make_record(
            client_info=PortfolioClientInfo(
                port_client_name="John Doe",
                port_client_type=ClientType.INDIVIDUAL,
            )
        )
        assert rec.client_info.port_client_type == ClientType.INDIVIDUAL

    def test_trust_client_type(self):
        rec = _make_record(
            client_info=PortfolioClientInfo(
                port_client_name="Family Trust",
                port_client_type=ClientType.TRUST,
            )
        )
        assert rec.client_info.port_client_type == ClientType.TRUST

    def test_all_portfolio_statuses(self):
        for status in PortfolioStatus:
            if status == PortfolioStatus.CLOSED:
                # Closed portfolio must have zero/negative cash
                fi = PortfolioFinancialInfo(
                    port_total_value=Decimal("0.00"),
                    port_cash_balance=Decimal("0.00"),
                )
            else:
                fi = PortfolioFinancialInfo(
                    port_total_value=Decimal("1000.00"),
                    port_cash_balance=Decimal("500.00"),
                )
            rec = _make_record(
                portfolio_info=PortfolioInfo(
                    port_create_date="20240101",
                    port_last_maint="20240101",
                    port_status=status,
                ),
                financial_info=fi,
            )
            assert rec.portfolio_info.port_status == status

    def test_filler_field_optional(self):
        rec = _make_record()
        assert rec.filler is None

    def test_filler_field_populated(self):
        rec = _make_record(filler="X" * 50)
        assert rec.filler == "X" * 50


# ===================================================================
# 2. COMP-3 packed-decimal precision tests
# ===================================================================
class TestComp3Precision:
    """PIC S9(13)V99 COMP-3 — signed, 13 integer digits, 2 decimal."""

    def test_exact_two_decimal_places_preserved(self):
        fi = PortfolioFinancialInfo(
            port_total_value=Decimal("12345.67"),
            port_cash_balance=Decimal("89.01"),
        )
        assert fi.port_total_value == Decimal("12345.67")
        assert fi.port_cash_balance == Decimal("89.01")

    def test_value_quantized_to_two_places(self):
        """COBOL MOVE to PIC S9(13)V99 truncates extra decimals."""
        fi = PortfolioFinancialInfo(
            port_total_value=Decimal("100.999"),  # will quantize to 101.00
        )
        assert fi.port_total_value == Decimal("101.00")

    def test_integer_value_gets_two_decimals(self):
        fi = PortfolioFinancialInfo(port_total_value=Decimal("5000"))
        assert fi.port_total_value == Decimal("5000.00")

    def test_single_decimal_gets_padded(self):
        fi = PortfolioFinancialInfo(port_total_value=Decimal("123.4"))
        assert fi.port_total_value == Decimal("123.40")

    def test_zero_value(self):
        fi = PortfolioFinancialInfo(
            port_total_value=Decimal("0"),
            port_cash_balance=Decimal("0.00"),
        )
        assert fi.port_total_value == Decimal("0.00")
        assert fi.port_cash_balance == Decimal("0.00")

    def test_negative_zero(self):
        """COBOL COMP-3 can represent -0; Decimal quantize normalizes it."""
        fi = PortfolioFinancialInfo(port_total_value=Decimal("-0.00"))
        # After quantize, -0.00 should still compare equal to 0.00
        assert fi.port_total_value == Decimal("0.00") or fi.port_total_value == Decimal("-0.00")


# ===================================================================
# 3. COMP-3 boundary values
# ===================================================================
class TestComp3Boundaries:
    """Test exact boundary of PIC S9(13)V99: ±9,999,999,999,999.99."""

    def test_max_positive_value(self):
        fi = PortfolioFinancialInfo(port_total_value=COMP3_MAX_VALUE)
        assert fi.port_total_value == Decimal("9999999999999.99")

    def test_min_negative_value(self):
        fi = PortfolioFinancialInfo(port_total_value=COMP3_MIN_VALUE)
        assert fi.port_total_value == Decimal("-9999999999999.99")

    def test_one_cent_below_max(self):
        fi = PortfolioFinancialInfo(
            port_total_value=Decimal("9999999999999.98")
        )
        assert fi.port_total_value == Decimal("9999999999999.98")

    def test_one_cent_above_min(self):
        fi = PortfolioFinancialInfo(
            port_total_value=Decimal("-9999999999999.98")
        )
        assert fi.port_total_value == Decimal("-9999999999999.98")

    def test_overflow_positive_rejected(self):
        with pytest.raises(ValueError, match="outside COMP-3 range"):
            PortfolioFinancialInfo(
                port_total_value=Decimal("10000000000000.00")
            )

    def test_overflow_negative_rejected(self):
        with pytest.raises(ValueError, match="outside COMP-3 range"):
            PortfolioFinancialInfo(
                port_total_value=Decimal("-10000000000000.00")
            )

    def test_just_over_max_by_one_cent(self):
        with pytest.raises(ValueError, match="outside COMP-3 range"):
            PortfolioFinancialInfo(
                port_total_value=Decimal("10000000000000.00")
            )

    def test_large_positive_overflow(self):
        with pytest.raises(ValueError, match="outside COMP-3 range"):
            PortfolioFinancialInfo(
                port_total_value=Decimal("99999999999999.99")
            )

    def test_large_negative_overflow(self):
        with pytest.raises(ValueError, match="outside COMP-3 range"):
            PortfolioFinancialInfo(
                port_total_value=Decimal("-99999999999999.99")
            )


# ===================================================================
# 4. Sign handling
# ===================================================================
class TestSignHandling:
    """COMP-3 is explicitly signed (PIC S9...)."""

    def test_positive_amount(self):
        fi = PortfolioFinancialInfo(port_total_value=Decimal("12345.67"))
        assert fi.port_total_value > Decimal("0")

    def test_negative_amount(self):
        fi = PortfolioFinancialInfo(port_total_value=Decimal("-12345.67"))
        assert fi.port_total_value < Decimal("0")

    def test_sign_flip_positive_to_negative(self):
        """Simulates COBOL sign reversal."""
        original = Decimal("5000.00")
        flipped = -original
        fi = PortfolioFinancialInfo(port_total_value=flipped)
        assert fi.port_total_value == Decimal("-5000.00")

    def test_sign_flip_negative_to_positive(self):
        original = Decimal("-5000.00")
        flipped = -original
        fi = PortfolioFinancialInfo(port_total_value=flipped)
        assert fi.port_total_value == Decimal("5000.00")

    def test_sign_preserved_through_arithmetic(self):
        """Verify sign is preserved after add/subtract like COBOL COMPUTE."""
        a = Decimal("1000.50")
        b = Decimal("2000.75")
        result = a - b  # should be -1000.25
        fi = PortfolioFinancialInfo(port_total_value=result)
        assert fi.port_total_value == Decimal("-1000.25")

    def test_negative_cash_balance_allowed(self):
        """COMP-3 signed field allows negative cash (margin account)."""
        fi = PortfolioFinancialInfo(
            port_total_value=Decimal("50000.00"),
            port_cash_balance=Decimal("-1000.00"),
        )
        assert fi.port_cash_balance == Decimal("-1000.00")


# ===================================================================
# 5. Invalid data rejection
# ===================================================================
class TestInvalidDataRejection:
    def test_nan_rejected(self):
        with pytest.raises(ValueError, match="NaN"):
            PortfolioFinancialInfo(port_total_value=Decimal("NaN"))

    def test_infinity_rejected(self):
        with pytest.raises(ValueError, match="finite number"):
            PortfolioFinancialInfo(port_total_value=Decimal("Infinity"))

    def test_negative_infinity_rejected(self):
        with pytest.raises(ValueError, match="finite number"):
            PortfolioFinancialInfo(port_total_value=Decimal("-Infinity"))

    def test_invalid_client_type_rejected(self):
        with pytest.raises(ValueError):
            PortfolioClientInfo(
                port_client_name="Bad Client",
                port_client_type="X",  # type: ignore[arg-type]
            )

    def test_invalid_portfolio_status_rejected(self):
        with pytest.raises(ValueError):
            PortfolioInfo(
                port_create_date="20240101",
                port_last_maint="20240101",
                port_status="X",  # type: ignore[arg-type]
            )

    def test_non_numeric_date_rejected(self):
        with pytest.raises(ValueError):
            PortfolioInfo(
                port_create_date="ABCDEFGH",
                port_last_maint="20240101",
                port_status=PortfolioStatus.ACTIVE,
            )

    def test_port_id_too_long(self):
        with pytest.raises(ValueError):
            PortfolioKey(port_id="TOOLONGID", port_account_no="1234567890")

    def test_account_no_too_long(self):
        with pytest.raises(ValueError):
            PortfolioKey(port_id="PORT0001", port_account_no="12345678901")

    def test_client_name_too_long(self):
        with pytest.raises(ValueError):
            PortfolioClientInfo(
                port_client_name="X" * 31,  # PIC X(30) max
                port_client_type=ClientType.INDIVIDUAL,
            )

    def test_filler_too_long(self):
        with pytest.raises(ValueError):
            _make_record(filler="X" * 51)  # PIC X(50) max


# ===================================================================
# 6. Cross-field business rules
# ===================================================================
class TestCrossFieldRules:
    def test_closed_portfolio_with_positive_cash_rejected(self):
        with pytest.raises(ValueError, match="Closed portfolio"):
            _make_record(
                portfolio_info=PortfolioInfo(
                    port_create_date="20240101",
                    port_last_maint="20240601",
                    port_status=PortfolioStatus.CLOSED,
                ),
                financial_info=PortfolioFinancialInfo(
                    port_total_value=Decimal("0.00"),
                    port_cash_balance=Decimal("0.01"),
                ),
            )

    def test_closed_portfolio_with_zero_cash_allowed(self):
        rec = _make_record(
            portfolio_info=PortfolioInfo(
                port_create_date="20240101",
                port_last_maint="20240601",
                port_status=PortfolioStatus.CLOSED,
            ),
            financial_info=PortfolioFinancialInfo(
                port_total_value=Decimal("0.00"),
                port_cash_balance=Decimal("0.00"),
            ),
        )
        assert rec.portfolio_info.port_status == PortfolioStatus.CLOSED

    def test_closed_portfolio_with_negative_cash_allowed(self):
        rec = _make_record(
            portfolio_info=PortfolioInfo(
                port_create_date="20240101",
                port_last_maint="20240601",
                port_status=PortfolioStatus.CLOSED,
            ),
            financial_info=PortfolioFinancialInfo(
                port_total_value=Decimal("0.00"),
                port_cash_balance=Decimal("-100.00"),
            ),
        )
        assert rec.financial_info.port_cash_balance == Decimal("-100.00")

    def test_suspended_portfolio_with_positive_cash_allowed(self):
        rec = _make_record(
            portfolio_info=PortfolioInfo(
                port_create_date="20240101",
                port_last_maint="20240601",
                port_status=PortfolioStatus.SUSPENDED,
            ),
            financial_info=PortfolioFinancialInfo(
                port_total_value=Decimal("50000.00"),
                port_cash_balance=Decimal("10000.00"),
            ),
        )
        assert rec.portfolio_info.port_status == PortfolioStatus.SUSPENDED
