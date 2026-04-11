"""
Pydantic models derived from TRNREC.cpy — Transaction Record Structure.

COBOL source: src/copybook/common/TRNREC.cpy (41 LOC)
Key mappings:
  TRN-QUANTITY PIC S9(11)V9(4) COMP-3 → Decimal (max_digits=15, decimal_places=4)
  TRN-PRICE    PIC S9(11)V9(4) COMP-3 → Decimal (max_digits=15, decimal_places=4)
  TRN-AMOUNT   PIC S9(13)V9(2) COMP-3 → Decimal (max_digits=15, decimal_places=2)
"""

from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from .enums import TransactionStatus, TransactionType

_COMP3_11V4_MAX = Decimal("99999999999.9999")
_COMP3_11V4_MIN = Decimal("-99999999999.9999")
_COMP3_13V2_MAX = Decimal("9999999999999.99")
_COMP3_13V2_MIN = Decimal("-9999999999999.99")


class TransactionRecord(BaseModel):
    """
    Complete TRANSACTION-RECORD from TRNREC.cpy.

    Groups: TRN-KEY, TRN-DATA, TRN-AUDIT
    """

    # TRN-KEY
    transaction_date: str = Field(max_length=8, description="PIC X(08) — YYYYMMDD")
    transaction_time: str = Field(max_length=6, description="PIC X(06) — HHMMSS")
    portfolio_id: str = Field(max_length=8, description="PIC X(08)")
    sequence_no: str = Field(max_length=6, description="PIC X(06)")
    # TRN-DATA
    investment_id: str = Field(max_length=10, description="PIC X(10)")
    transaction_type: TransactionType = Field(description="PIC X(02) — BU/SL/TR/FE")
    quantity: Decimal = Field(default=Decimal("0.0000"), max_digits=15, decimal_places=4)
    price: Decimal = Field(default=Decimal("0.0000"), max_digits=15, decimal_places=4)
    amount: Decimal = Field(default=Decimal("0.00"), max_digits=15, decimal_places=2)
    currency: str = Field(default="USD", max_length=3, description="PIC X(03)")
    status: TransactionStatus = Field(default=TransactionStatus.PENDING)
    # TRN-AUDIT
    process_date: str = Field(default="", max_length=26, description="PIC X(26)")
    process_user: str = Field(default="", max_length=8, description="PIC X(08)")

    @field_validator("quantity", "price", mode="before")
    @classmethod
    def validate_quantity_price(cls, v: object) -> Decimal:
        d = Decimal(str(v))
        if d.is_nan() or d.is_infinite():
            raise ValueError("COMP-3 fields cannot be NaN or Infinity")
        if not (_COMP3_11V4_MIN <= d <= _COMP3_11V4_MAX):
            raise ValueError(f"Value {d} outside COMP-3 S9(11)V9(4) range")
        return d.quantize(Decimal("0.0001"))

    @field_validator("amount", mode="before")
    @classmethod
    def validate_amount(cls, v: object) -> Decimal:
        d = Decimal(str(v))
        if d.is_nan() or d.is_infinite():
            raise ValueError("COMP-3 fields cannot be NaN or Infinity")
        if not (_COMP3_13V2_MIN <= d <= _COMP3_13V2_MAX):
            raise ValueError(f"Value {d} outside COMP-3 S9(13)V9(2) range")
        return d.quantize(Decimal("0.01"))
