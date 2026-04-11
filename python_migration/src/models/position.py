"""
Pydantic models derived from POSREC.cpy — Position Record Structure.

COBOL source: src/copybook/common/POSREC.cpy (34 LOC)
Key mappings:
  POS-QUANTITY     PIC S9(11)V9(4) COMP-3 → Decimal (max_digits=15, decimal_places=4)
  POS-COST-BASIS   PIC S9(13)V9(2) COMP-3 → Decimal (max_digits=15, decimal_places=2)
  POS-MARKET-VALUE PIC S9(13)V9(2) COMP-3 → Decimal (max_digits=15, decimal_places=2)
"""

from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from .enums import PositionStatus

_COMP3_11V4_MAX = Decimal("99999999999.9999")
_COMP3_11V4_MIN = Decimal("-99999999999.9999")
_COMP3_13V2_MAX = Decimal("9999999999999.99")
_COMP3_13V2_MIN = Decimal("-9999999999999.99")


class PositionRecord(BaseModel):
    """
    Complete POSITION-RECORD from POSREC.cpy.

    Groups: POS-KEY, POS-DATA, POS-AUDIT
    """

    # POS-KEY
    portfolio_id: str = Field(max_length=8, description="PIC X(08)")
    position_date: str = Field(max_length=8, description="PIC X(08) — YYYYMMDD")
    investment_id: str = Field(max_length=10, description="PIC X(10)")
    # POS-DATA (COMP-3 fields)
    quantity: Decimal = Field(default=Decimal("0.0000"), max_digits=15, decimal_places=4)
    cost_basis: Decimal = Field(default=Decimal("0.00"), max_digits=15, decimal_places=2)
    market_value: Decimal = Field(default=Decimal("0.00"), max_digits=15, decimal_places=2)
    currency: str = Field(default="USD", max_length=3, description="PIC X(03)")
    status: PositionStatus = Field(default=PositionStatus.ACTIVE)
    # POS-AUDIT
    last_maint_date: str = Field(default="", max_length=26, description="PIC X(26) — ISO timestamp")
    last_maint_user: str = Field(default="", max_length=8, description="PIC X(08)")

    @field_validator("quantity", mode="before")
    @classmethod
    def validate_quantity(cls, v: object) -> Decimal:
        d = Decimal(str(v))
        if d.is_nan() or d.is_infinite():
            raise ValueError("COMP-3 fields cannot be NaN or Infinity")
        if not (_COMP3_11V4_MIN <= d <= _COMP3_11V4_MAX):
            raise ValueError(f"Value {d} outside COMP-3 S9(11)V9(4) range")
        return d.quantize(Decimal("0.0001"))

    @field_validator("cost_basis", "market_value", mode="before")
    @classmethod
    def validate_money(cls, v: object) -> Decimal:
        d = Decimal(str(v))
        if d.is_nan() or d.is_infinite():
            raise ValueError("COMP-3 fields cannot be NaN or Infinity")
        if not (_COMP3_13V2_MIN <= d <= _COMP3_13V2_MAX):
            raise ValueError(f"Value {d} outside COMP-3 S9(13)V9(2) range")
        return d.quantize(Decimal("0.01"))
