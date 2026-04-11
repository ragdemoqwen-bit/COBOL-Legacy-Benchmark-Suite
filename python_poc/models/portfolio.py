"""
Portfolio Master Record Model — converted from PORTFLIO.cpy

Mirrors the COBOL copybook layout exactly:
  01  PORT-RECORD.
      05  PORT-KEY.
          10  PORT-ID             PIC X(8).
          10  PORT-ACCOUNT-NO     PIC X(10).
      05  PORT-CLIENT-INFO.
          10  PORT-CLIENT-NAME    PIC X(30).
          10  PORT-CLIENT-TYPE    PIC X(1).   88-levels: I/C/T
      05  PORT-PORTFOLIO-INFO.
          10  PORT-CREATE-DATE    PIC 9(8).
          10  PORT-LAST-MAINT     PIC 9(8).
          10  PORT-STATUS         PIC X(1).   88-levels: A/C/S
      05  PORT-FINANCIAL-INFO.
          10  PORT-TOTAL-VALUE    PIC S9(13)V99 COMP-3.
          10  PORT-CASH-BALANCE   PIC S9(13)V99 COMP-3.
      05  PORT-AUDIT-INFO.
          10  PORT-LAST-USER      PIC X(8).
          10  PORT-LAST-TRANS     PIC 9(8).
      05  PORT-FILLER            PIC X(50).

COMP-3 handling:
  PIC S9(13)V99 COMP-3 means a signed packed-decimal with 13 integer digits
  and 2 fractional digits.  The valid range is -9_999_999_999_999.99 ..
  +9_999_999_999_999.99.  We use Python ``decimal.Decimal`` with matching
  precision and enforce the exact limits via Pydantic validators.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Annotated, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# COMP-3 / packed-decimal constants
# ---------------------------------------------------------------------------
# PIC S9(13)V99 → 13 integer digits, 2 decimal places
COMP3_MAX_INTEGER_DIGITS = 13
COMP3_DECIMAL_PLACES = 2
COMP3_MAX_VALUE = Decimal("9999999999999.99")
COMP3_MIN_VALUE = Decimal("-9999999999999.99")


def _validate_comp3_field(value: Decimal, field_name: str) -> Decimal:
    """Validate a value conforms to PIC S9(13)V99 COMP-3 constraints.

    Enforces:
      - Exact 2-decimal-place precision (quantize to .01)
      - Signed range: -9_999_999_999_999.99 .. +9_999_999_999_999.99
      - No NaN / Infinity
    """
    if not isinstance(value, Decimal):
        try:
            value = Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise ValueError(
                f"{field_name}: cannot convert to Decimal: {value!r}"
            ) from exc

    if value.is_nan() or value.is_infinite():
        raise ValueError(f"{field_name}: NaN and Infinity are not allowed")

    # Quantize to 2 decimal places (match COBOL V99)
    quantized = value.quantize(Decimal("0.01"))

    if quantized < COMP3_MIN_VALUE or quantized > COMP3_MAX_VALUE:
        raise ValueError(
            f"{field_name}: value {quantized} outside COMP-3 range "
            f"[{COMP3_MIN_VALUE}, {COMP3_MAX_VALUE}]"
        )

    return quantized


# ---------------------------------------------------------------------------
# Enums  (COBOL level-88 condition names)
# ---------------------------------------------------------------------------
class ClientType(str, Enum):
    """PORT-CLIENT-TYPE level-88 values."""

    INDIVIDUAL = "I"
    CORPORATE = "C"
    TRUST = "T"


class PortfolioStatus(str, Enum):
    """PORT-STATUS level-88 values."""

    ACTIVE = "A"
    CLOSED = "C"
    SUSPENDED = "S"


# ---------------------------------------------------------------------------
# Sub-models  (mirror the COBOL group-level items)
# ---------------------------------------------------------------------------
class PortfolioKey(BaseModel):
    """PORT-KEY group."""

    port_id: Annotated[str, Field(min_length=1, max_length=8)]
    port_account_no: Annotated[str, Field(min_length=1, max_length=10)]


class PortfolioClientInfo(BaseModel):
    """PORT-CLIENT-INFO group."""

    port_client_name: Annotated[str, Field(max_length=30)]
    port_client_type: ClientType


class PortfolioInfo(BaseModel):
    """PORT-PORTFOLIO-INFO group."""

    port_create_date: Annotated[str, Field(pattern=r"^\d{8}$")]
    port_last_maint: Annotated[str, Field(pattern=r"^\d{8}$")]
    port_status: PortfolioStatus


class PortfolioFinancialInfo(BaseModel):
    """PORT-FINANCIAL-INFO group — contains the COMP-3 packed-decimal fields."""

    port_total_value: Decimal = Field(
        default=Decimal("0.00"),
        description="PIC S9(13)V99 COMP-3 — portfolio total market value",
    )
    port_cash_balance: Decimal = Field(
        default=Decimal("0.00"),
        description="PIC S9(13)V99 COMP-3 — available cash balance",
    )

    @field_validator("port_total_value")
    @classmethod
    def validate_total_value(cls, v: Decimal) -> Decimal:
        return _validate_comp3_field(v, "port_total_value")

    @field_validator("port_cash_balance")
    @classmethod
    def validate_cash_balance(cls, v: Decimal) -> Decimal:
        return _validate_comp3_field(v, "port_cash_balance")


class PortfolioAuditInfo(BaseModel):
    """PORT-AUDIT-INFO group."""

    port_last_user: Annotated[str, Field(max_length=8)]
    port_last_trans: Annotated[str, Field(pattern=r"^\d{8}$")]


# ---------------------------------------------------------------------------
# Top-level record  (PORT-RECORD)
# ---------------------------------------------------------------------------
class PortfolioRecord(BaseModel):
    """Complete portfolio master record — mirrors PORTFLIO.cpy 01 PORT-RECORD.

    All COMP-3 fields use ``decimal.Decimal`` to preserve exact mainframe
    precision.  The model rejects values that exceed the PIC S9(13)V99 range
    or that contain more than 2 decimal places.
    """

    key: PortfolioKey
    client_info: PortfolioClientInfo
    portfolio_info: PortfolioInfo
    financial_info: PortfolioFinancialInfo
    audit_info: PortfolioAuditInfo
    filler: Optional[str] = Field(default=None, max_length=50)

    @model_validator(mode="after")
    def validate_cross_field_rules(self) -> "PortfolioRecord":
        """Cross-field business rules that span multiple groups."""
        # A closed portfolio must not have a positive cash balance
        if (
            self.portfolio_info.port_status == PortfolioStatus.CLOSED
            and self.financial_info.port_cash_balance > Decimal("0.00")
        ):
            raise ValueError(
                "Closed portfolio cannot have a positive cash balance"
            )
        return self
