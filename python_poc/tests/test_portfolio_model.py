"""
Tests for the PortfolioRecord Pydantic model (converted from PORTFLIO.cpy).

Covers:
  - Valid record construction with all field types
  - COMP-3 PIC S9(13)V99 precision enforcement
  - Level-88 enum validation (ClientType, PortfolioStatus)
  - Boundary values for packed decimal fields
  - Sign handling (positive, negative, zero)
  - PIC X field length constraints
  - PIC 9(8) date field format constraints
  - Edge cases: max precision, overflow, truncation
"""

from decimal import Decimal

import pytest

from python_poc.src.models.portfolio import (
    AuditInfo,
    ClientInfo,
    ClientType,
    COMP3_S9_13_V99_MAX,
    COMP3_S9_13_V99_MIN,
    FinancialInfo,
    PortfolioInfo,
    PortfolioKey,
    PortfolioRecord,
    PortfolioStatus,
)


# ================================================================
# Helpers
# ================================================================

def _make_financial(
    total: Decimal = Decimal("1000.00"),
    cash: Decimal = Decimal("500.00"),
) -> FinancialInfo:
    return FinancialInfo(total_value=total, cash_balance=cash)


def _make_record(**overrides) -> PortfolioRecord:
    """Build a valid PortfolioRecord with sensible defaults."""
    defaults = {
        "key": PortfolioKey(port_id="PORT0001", account_no="1234567890"),
        "client_info": ClientInfo(client_name="John Doe", client_type=ClientType.INDIVIDUAL),
        "portfolio_info": PortfolioInfo(
            create_date="20240320",
            last_maint="20240401",
            status=PortfolioStatus.ACTIVE,
        ),
        "financial_info": _make_financial(),
        "audit_info": AuditInfo(last_user="ADMIN01", last_trans="20240401"),
    }
    defaults.update(overrides)
    return PortfolioRecord(**defaults)


# ================================================================
# Valid record construction
# ================================================================

class TestValidRecords:
    """Happy-path tests — valid records that should construct without error."""

    def test_minimal_valid_record(self):
        record = _make_record()
        assert record.key.port_id == "PORT0001"
        assert record.key.account_no == "1234567890"
        assert record.client_info.client_type == ClientType.INDIVIDUAL
        assert record.portfolio_info.status == PortfolioStatus.ACTIVE

    def test_all_client_types(self):
        for ct in ClientType:
            record = _make_record(
                client_info=ClientInfo(client_name="Test", client_type=ct)
            )
            assert record.client_info.client_type == ct

    def test_all_portfolio_statuses(self):
        for ps in PortfolioStatus:
            record = _make_record(
                portfolio_info=PortfolioInfo(
                    create_date="20240101",
                    last_maint="20240101",
                    status=ps,
                )
            )
            assert record.portfolio_info.status == ps

    def test_filler_field_optional(self):
        record = _make_record()
        assert record.filler is None

    def test_filler_field_with_value(self):
        record = _make_record(filler="reserved data")
        assert record.filler == "reserved data"


# ================================================================
# COMP-3 PIC S9(13)V99 — precision and sign handling
# ================================================================

class TestComp3Precision:
    """
    COMP-3 packed decimal tests.
    PIC S9(13)V99 means:
      - Signed (S prefix)
      - 13 integer digits
      - 2 fractional digits (V99)
      - Range: -9,999,999,999,999.99 to +9,999,999,999,999.99
    """

    def test_positive_value(self):
        fi = _make_financial(total=Decimal("12345.67"), cash=Decimal("890.12"))
        assert fi.total_value == Decimal("12345.67")
        assert fi.cash_balance == Decimal("890.12")

    def test_negative_value(self):
        """COMP-3 signed field — negative values are valid."""
        fi = _make_financial(
            total=Decimal("-5000.50"),
            cash=Decimal("-100.01"),
        )
        assert fi.total_value == Decimal("-5000.50")
        assert fi.cash_balance == Decimal("-100.01")

    def test_zero_value(self):
        fi = _make_financial(
            total=Decimal("0.00"),
            cash=Decimal("0.00"),
        )
        assert fi.total_value == Decimal("0.00")
        assert fi.cash_balance == Decimal("0.00")

    def test_zero_no_decimal(self):
        fi = _make_financial(total=Decimal("0"), cash=Decimal("0"))
        assert fi.total_value == Decimal("0")

    def test_max_positive_boundary(self):
        """Exact maximum: +9,999,999,999,999.99"""
        fi = _make_financial(
            total=COMP3_S9_13_V99_MAX,
            cash=Decimal("0"),
        )
        assert fi.total_value == COMP3_S9_13_V99_MAX

    def test_max_negative_boundary(self):
        """Exact minimum: -9,999,999,999,999.99"""
        fi = _make_financial(
            total=COMP3_S9_13_V99_MIN,
            cash=Decimal("0"),
        )
        assert fi.total_value == COMP3_S9_13_V99_MIN

    def test_overflow_positive(self):
        """One cent over the max → should fail."""
        with pytest.raises(Exception):
            _make_financial(
                total=Decimal("10000000000000.00"),
                cash=Decimal("0"),
            )

    def test_overflow_negative(self):
        """One cent below the min → should fail."""
        with pytest.raises(Exception):
            _make_financial(
                total=Decimal("-10000000000000.00"),
                cash=Decimal("0"),
            )

    def test_three_decimal_places_rejected(self):
        """
        PIC S9(13)V99 allows max 2 fractional digits.
        3 decimal places should be rejected.
        """
        with pytest.raises(Exception):
            _make_financial(
                total=Decimal("100.123"),
                cash=Decimal("0"),
            )

    def test_four_decimal_places_rejected(self):
        with pytest.raises(Exception):
            _make_financial(
                total=Decimal("100.1234"),
                cash=Decimal("0"),
            )

    def test_one_decimal_place_accepted(self):
        """V99 allows 0, 1, or 2 fractional digits."""
        fi = _make_financial(total=Decimal("100.1"), cash=Decimal("0"))
        assert fi.total_value == Decimal("100.1")

    def test_integer_only_accepted(self):
        """No decimal point at all — valid (0 fractional digits)."""
        fi = _make_financial(total=Decimal("999"), cash=Decimal("0"))
        assert fi.total_value == Decimal("999")

    def test_sign_flip_positive_to_negative(self):
        """Ensure sign is preserved through round-trip."""
        fi = _make_financial(total=Decimal("12345.67"), cash=Decimal("-12345.67"))
        assert fi.total_value > 0
        assert fi.cash_balance < 0
        assert fi.total_value + fi.cash_balance == Decimal("0.00")

    def test_very_small_positive(self):
        fi = _make_financial(total=Decimal("0.01"), cash=Decimal("0"))
        assert fi.total_value == Decimal("0.01")

    def test_very_small_negative(self):
        fi = _make_financial(total=Decimal("-0.01"), cash=Decimal("0"))
        assert fi.total_value == Decimal("-0.01")

    def test_large_13_digit_integer(self):
        """Max integer digits: 9999999999999 (13 nines) with .00"""
        fi = _make_financial(total=Decimal("9999999999999.00"), cash=Decimal("0"))
        assert fi.total_value == Decimal("9999999999999.00")

    def test_14_integer_digits_rejected(self):
        """14 integer digits exceed PIC S9(13)V99 capacity."""
        with pytest.raises(Exception):
            _make_financial(total=Decimal("99999999999999.00"), cash=Decimal("0"))


# ================================================================
# PIC X field length constraints
# ================================================================

class TestFieldLengths:
    """Ensure PIC X(n) max_length constraints are enforced."""

    def test_port_id_max_length(self):
        """PIC X(8) — exactly 8 chars is fine."""
        key = PortfolioKey(port_id="PORT0001", account_no="1234567890")
        assert len(key.port_id) == 8

    def test_port_id_too_long(self):
        """PIC X(8) — 9 chars should fail."""
        with pytest.raises(Exception):
            PortfolioKey(port_id="PORT00019", account_no="1234567890")

    def test_account_no_max_length(self):
        """PIC X(10) — exactly 10 chars."""
        key = PortfolioKey(port_id="PORT0001", account_no="1234567890")
        assert len(key.account_no) == 10

    def test_account_no_too_long(self):
        """PIC X(10) — 11 chars should fail."""
        with pytest.raises(Exception):
            PortfolioKey(port_id="PORT0001", account_no="12345678901")

    def test_client_name_max_length(self):
        """PIC X(30) — 30 chars is fine."""
        info = ClientInfo(
            client_name="A" * 30,
            client_type=ClientType.INDIVIDUAL,
        )
        assert len(info.client_name) == 30

    def test_client_name_too_long(self):
        """PIC X(30) — 31 chars should fail."""
        with pytest.raises(Exception):
            ClientInfo(
                client_name="A" * 31,
                client_type=ClientType.INDIVIDUAL,
            )

    def test_last_user_max_length(self):
        """PIC X(8)."""
        audit = AuditInfo(last_user="ADMIN001", last_trans="20240101")
        assert len(audit.last_user) == 8

    def test_last_user_too_long(self):
        with pytest.raises(Exception):
            AuditInfo(last_user="ADMIN0019", last_trans="20240101")

    def test_filler_max_length(self):
        """PIC X(50)."""
        record = _make_record(filler="X" * 50)
        assert len(record.filler) == 50

    def test_filler_too_long(self):
        with pytest.raises(Exception):
            _make_record(filler="X" * 51)


# ================================================================
# PIC 9(8) date field format constraints
# ================================================================

class TestDateFields:
    """PIC 9(8) fields must be exactly 8 digits (YYYYMMDD format)."""

    def test_valid_date(self):
        info = PortfolioInfo(
            create_date="20240320",
            last_maint="20240401",
            status=PortfolioStatus.ACTIVE,
        )
        assert info.create_date == "20240320"

    def test_date_with_letters_rejected(self):
        with pytest.raises(Exception):
            PortfolioInfo(
                create_date="2024032A",
                last_maint="20240401",
                status=PortfolioStatus.ACTIVE,
            )

    def test_date_too_short(self):
        with pytest.raises(Exception):
            PortfolioInfo(
                create_date="2024032",
                last_maint="20240401",
                status=PortfolioStatus.ACTIVE,
            )

    def test_date_too_long(self):
        with pytest.raises(Exception):
            PortfolioInfo(
                create_date="202403200",
                last_maint="20240401",
                status=PortfolioStatus.ACTIVE,
            )


# ================================================================
# Level-88 enum validation (invalid values)
# ================================================================

class TestEnumValidation:
    def test_invalid_client_type(self):
        with pytest.raises(Exception):
            ClientInfo(client_name="Test", client_type="X")

    def test_invalid_portfolio_status(self):
        with pytest.raises(Exception):
            PortfolioInfo(
                create_date="20240101",
                last_maint="20240101",
                status="X",
            )


# ================================================================
# Round-trip serialization
# ================================================================

class TestSerialization:
    """Ensure Pydantic models round-trip through dict/JSON without precision loss."""

    def test_round_trip_dict(self):
        original = _make_record(
            financial_info=_make_financial(
                total=Decimal("9999999999999.99"),
                cash=Decimal("-123456.78"),
            ),
        )
        data = original.model_dump()
        restored = PortfolioRecord.model_validate(data)
        assert restored.financial_info.total_value == Decimal("9999999999999.99")
        assert restored.financial_info.cash_balance == Decimal("-123456.78")

    def test_round_trip_json(self):
        original = _make_record()
        json_str = original.model_dump_json()
        restored = PortfolioRecord.model_validate_json(json_str)
        assert restored.financial_info.total_value == original.financial_info.total_value
