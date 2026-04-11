"""
Pydantic models derived from DBTBLS.cpy — DB2 Table Host Variable Definitions.

COBOL source: src/copybook/db2/DBTBLS.cpy (51 LOC)
Key mappings:
  PH-QUANTITY      PIC S9(12)V9(3) COMP-3 → Decimal (max_digits=15, decimal_places=3)
  PH-PRICE         PIC S9(12)V9(3) COMP-3 → Decimal (max_digits=15, decimal_places=3)
  PH-AMOUNT etc.   PIC S9(13)V9(2) COMP-3 → Decimal (max_digits=15, decimal_places=2)
"""

from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from .enums import ErrorLogSeverity, ErrorLogType

_COMP3_12V3_MAX = Decimal("999999999999.999")
_COMP3_12V3_MIN = Decimal("-999999999999.999")
_COMP3_13V2_MAX = Decimal("9999999999999.99")
_COMP3_13V2_MIN = Decimal("-9999999999999.99")


class PoshistRecord(BaseModel):
    """
    POSHIST-RECORD from DBTBLS.cpy — DB2 host variable layout for position history.
    """

    account_no: str = Field(max_length=8, description="PIC X(8)")
    portfolio_id: str = Field(max_length=10, description="PIC X(10)")
    trans_date: str = Field(max_length=10, description="PIC X(10)")
    trans_time: str = Field(max_length=8, description="PIC X(8)")
    trans_type: str = Field(max_length=2, description="PIC X(2)")
    security_id: str = Field(max_length=12, description="PIC X(12)")
    # COMP-3 fields
    quantity: Decimal = Field(default=Decimal("0.000"), max_digits=15, decimal_places=3)
    price: Decimal = Field(default=Decimal("0.000"), max_digits=15, decimal_places=3)
    amount: Decimal = Field(default=Decimal("0.00"), max_digits=15, decimal_places=2)
    fees: Decimal = Field(default=Decimal("0.00"), max_digits=15, decimal_places=2)
    total_amount: Decimal = Field(default=Decimal("0.00"), max_digits=15, decimal_places=2)
    cost_basis: Decimal = Field(default=Decimal("0.00"), max_digits=15, decimal_places=2)
    gain_loss: Decimal = Field(default=Decimal("0.00"), max_digits=15, decimal_places=2)
    # Audit
    process_date: str = Field(default="", max_length=10, description="PIC X(10)")
    process_time: str = Field(default="", max_length=8, description="PIC X(8)")
    program_id: str = Field(default="", max_length=8, description="PIC X(8)")
    user_id: str = Field(default="", max_length=8, description="PIC X(8)")
    audit_timestamp: str = Field(default="", max_length=26, description="PIC X(26)")

    @field_validator("quantity", "price", mode="before")
    @classmethod
    def validate_12v3(cls, v: object) -> Decimal:
        d = Decimal(str(v))
        if d.is_nan() or d.is_infinite():
            raise ValueError("COMP-3 fields cannot be NaN or Infinity")
        if not (_COMP3_12V3_MIN <= d <= _COMP3_12V3_MAX):
            raise ValueError(f"Value {d} outside COMP-3 S9(12)V9(3) range")
        return d.quantize(Decimal("0.001"))

    @field_validator("amount", "fees", "total_amount", "cost_basis", "gain_loss", mode="before")
    @classmethod
    def validate_13v2(cls, v: object) -> Decimal:
        d = Decimal(str(v))
        if d.is_nan() or d.is_infinite():
            raise ValueError("COMP-3 fields cannot be NaN or Infinity")
        if not (_COMP3_13V2_MIN <= d <= _COMP3_13V2_MAX):
            raise ValueError(f"Value {d} outside COMP-3 S9(13)V9(2) range")
        return d.quantize(Decimal("0.01"))


class ErrlogRecord(BaseModel):
    """
    ERRLOG-RECORD from DBTBLS.cpy — DB2 host variable layout for error log.
    """

    error_timestamp: str = Field(max_length=26, description="PIC X(26)")
    program_id: str = Field(max_length=8, description="PIC X(8)")
    error_type: ErrorLogType = Field(description="PIC X(1) — S/A/D")
    error_severity: ErrorLogSeverity = Field(description="1=Info, 2=Warn, 3=Error, 4=Severe")
    error_code: str = Field(max_length=8, description="PIC X(8)")
    error_message: str = Field(max_length=200, description="PIC X(200)")
    process_date: str = Field(max_length=10, description="PIC X(10)")
    process_time: str = Field(max_length=8, description="PIC X(8)")
    user_id: str = Field(max_length=8, description="PIC X(8)")
    additional_info: str = Field(default="", max_length=500, description="PIC X(500)")
