"""
Pydantic models derived from PORTFLIO.cpy — Portfolio Master Record Layout.

COBOL source: src/copybook/common/PORTFLIO.cpy (35 LOC)
Key mappings:
  PORT-TOTAL-VALUE  PIC S9(13)V99 COMP-3 → Decimal (max_digits=15, decimal_places=2)
  PORT-CASH-BALANCE PIC S9(13)V99 COMP-3 → Decimal (max_digits=15, decimal_places=2)
"""

from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from .enums import ClientType, PortfolioStatus

# COMP-3 PIC S9(13)V99 boundaries
_COMP3_13V2_MAX = Decimal("9999999999999.99")
_COMP3_13V2_MIN = Decimal("-9999999999999.99")


class PortfolioKey(BaseModel):
    """PORT-KEY group: primary key fields."""

    port_id: str = Field(max_length=8, description="PIC X(8) — Portfolio identifier")
    account_no: str = Field(max_length=10, description="PIC X(10) — Account number")


class PortfolioClientInfo(BaseModel):
    """PORT-CLIENT-INFO group."""

    client_name: str = Field(max_length=30, description="PIC X(30)")
    client_type: ClientType = Field(description="PIC X(1) — I/C/T")


class PortfolioInfo(BaseModel):
    """PORT-PORTFOLIO-INFO group."""

    create_date: str = Field(max_length=8, description="PIC 9(8) — YYYYMMDD")
    last_maint: str = Field(max_length=8, description="PIC 9(8) — YYYYMMDD")
    status: PortfolioStatus = Field(description="PIC X(1) — A/C/S")


class PortfolioFinancialInfo(BaseModel):
    """PORT-FINANCIAL-INFO group — COMP-3 packed decimal fields."""

    total_value: Decimal = Field(
        default=Decimal("0.00"),
        max_digits=15,
        decimal_places=2,
        description="PIC S9(13)V99 COMP-3",
    )
    cash_balance: Decimal = Field(
        default=Decimal("0.00"),
        max_digits=15,
        decimal_places=2,
        description="PIC S9(13)V99 COMP-3",
    )

    @field_validator("total_value", "cash_balance", mode="before")
    @classmethod
    def coerce_and_validate_comp3(cls, v: object) -> Decimal:
        d = Decimal(str(v))
        if d.is_nan() or d.is_infinite():
            raise ValueError("COMP-3 fields cannot be NaN or Infinity")
        if not (_COMP3_13V2_MIN <= d <= _COMP3_13V2_MAX):
            raise ValueError(f"Value {d} outside COMP-3 S9(13)V99 range")
        return d.quantize(Decimal("0.01"))


class PortfolioAuditInfo(BaseModel):
    """PORT-AUDIT-INFO group."""

    last_user: str = Field(default="", max_length=8, description="PIC X(8)")
    last_trans: str = Field(default="", max_length=8, description="PIC 9(8)")


class PortfolioRecord(BaseModel):
    """
    Complete PORT-RECORD — the full 01-level copybook record.

    Flattened for convenience; nested groups available via sub-models above.
    """

    # PORT-KEY
    port_id: str = Field(max_length=8)
    account_no: str = Field(max_length=10)
    # PORT-CLIENT-INFO
    client_name: str = Field(max_length=30)
    client_type: ClientType
    # PORT-PORTFOLIO-INFO
    create_date: str = Field(max_length=8)
    last_maint: str = Field(max_length=8)
    status: PortfolioStatus
    # PORT-FINANCIAL-INFO (COMP-3)
    total_value: Decimal = Field(default=Decimal("0.00"), max_digits=15, decimal_places=2)
    cash_balance: Decimal = Field(default=Decimal("0.00"), max_digits=15, decimal_places=2)
    # PORT-AUDIT-INFO
    last_user: str = Field(default="", max_length=8)
    last_trans: str = Field(default="", max_length=8)

    @field_validator("total_value", "cash_balance", mode="before")
    @classmethod
    def coerce_and_validate_comp3(cls, v: object) -> Decimal:
        d = Decimal(str(v))
        if d.is_nan() or d.is_infinite():
            raise ValueError("COMP-3 fields cannot be NaN or Infinity")
        if not (_COMP3_13V2_MIN <= d <= _COMP3_13V2_MAX):
            raise ValueError(f"Value {d} outside COMP-3 S9(13)V99 range")
        return d.quantize(Decimal("0.01"))
