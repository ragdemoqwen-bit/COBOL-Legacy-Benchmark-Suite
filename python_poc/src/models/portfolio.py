"""
Portfolio Master Record Model — converted from COBOL copybook PORTFLIO.cpy.

Source: src/copybook/common/PORTFLIO.cpy

COBOL COMP-3 (packed decimal) precision mapping:
  PIC S9(13)V99 COMP-3 → Decimal with max 13 integer digits + 2 fractional digits
  Sign is preserved via the Decimal type (supports negative values).
  Total precision: 15 digits, scale: 2.

COBOL PIC 9(8) (unsigned display numeric) → str constrained to 8 digits,
  stored as string to preserve leading zeros (e.g. date fields "20240320").
"""

from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import Annotated, Optional

from pydantic import BaseModel, Field, field_validator


# ----------------------------------------------------------------
# Level-88 condition equivalents
# ----------------------------------------------------------------

class ClientType(str, Enum):
    """
    COBOL level-88 conditions on PORT-CLIENT-TYPE:
      88 PORT-INDIVIDUAL  VALUE 'I'.
      88 PORT-CORPORATE   VALUE 'C'.
      88 PORT-TRUST       VALUE 'T'.
    """
    INDIVIDUAL = "I"
    CORPORATE = "C"
    TRUST = "T"


class PortfolioStatus(str, Enum):
    """
    COBOL level-88 conditions on PORT-STATUS:
      88 PORT-ACTIVE     VALUE 'A'.
      88 PORT-CLOSED     VALUE 'C'.
      88 PORT-SUSPENDED  VALUE 'S'.
    """
    ACTIVE = "A"
    CLOSED = "C"
    SUSPENDED = "S"


# ----------------------------------------------------------------
# COMP-3 packed decimal constraints
# ----------------------------------------------------------------
# PIC S9(13)V99 COMP-3:
#   - Signed: yes (S prefix)
#   - Integer digits: 13
#   - Fractional digits: 2 (V99)
#   - Total storage: 8 bytes in COBOL (ceil((15+1)/2))
#   - Range: -9_999_999_999_999.99 to +9_999_999_999_999.99
#
# We enforce this via Pydantic validators that check:
#   1. Scale never exceeds 2 decimal places
#   2. Magnitude stays within the 13-integer-digit limit

COMP3_S9_13_V99_MAX = Decimal("9999999999999.99")
COMP3_S9_13_V99_MIN = Decimal("-9999999999999.99")


def _validate_comp3_s9_13_v99(value: Decimal, field_name: str) -> Decimal:
    """
    Validate a Decimal value against COBOL PIC S9(13)V99 COMP-3 constraints.

    Enforces:
      - Exact type (no floats sneak through)
      - Scale ≤ 2 (no more than 2 fractional digits)
      - Magnitude within ±9,999,999,999,999.99
    """
    if not isinstance(value, Decimal):
        raise TypeError(f"{field_name}: expected Decimal, got {type(value).__name__}")

    # Check scale — COBOL V99 means at most 2 fractional digits
    sign, digits, exponent = value.as_tuple()
    # exponent is negative for fractional digits, 0 or positive for integers
    scale = -exponent if exponent < 0 else 0
    if scale > 2:
        raise ValueError(
            f"{field_name}: COMP-3 PIC S9(13)V99 allows max 2 decimal places, "
            f"got {scale} ({value})"
        )

    # Check magnitude — 13 integer digits + 2 fractional
    if value < COMP3_S9_13_V99_MIN or value > COMP3_S9_13_V99_MAX:
        raise ValueError(
            f"{field_name}: COMP-3 PIC S9(13)V99 range is "
            f"{COMP3_S9_13_V99_MIN} to {COMP3_S9_13_V99_MAX}, got {value}"
        )

    return value


# Type alias for documentation
Comp3Signed13v2 = Annotated[
    Decimal,
    Field(
        ge=COMP3_S9_13_V99_MIN,
        le=COMP3_S9_13_V99_MAX,
        description="COBOL PIC S9(13)V99 COMP-3 packed decimal",
    ),
]


# ----------------------------------------------------------------
# Nested record structures (matching COBOL 05/10 levels)
# ----------------------------------------------------------------

class PortfolioKey(BaseModel):
    """
    COBOL group: 05 PORT-KEY
      10 PORT-ID          PIC X(8).
      10 PORT-ACCOUNT-NO  PIC X(10).
    """
    port_id: str = Field(
        max_length=8,
        description="Portfolio identifier — PIC X(8)",
    )
    account_no: str = Field(
        max_length=10,
        description="Account number — PIC X(10)",
    )


class ClientInfo(BaseModel):
    """
    COBOL group: 05 PORT-CLIENT-INFO
      10 PORT-CLIENT-NAME  PIC X(30).
      10 PORT-CLIENT-TYPE  PIC X(1).  (level-88: I/C/T)
    """
    client_name: str = Field(
        max_length=30,
        description="Client name — PIC X(30)",
    )
    client_type: ClientType = Field(
        description="Client type — PIC X(1) with level-88 values I/C/T",
    )


class PortfolioInfo(BaseModel):
    """
    COBOL group: 05 PORT-PORTFOLIO-INFO
      10 PORT-CREATE-DATE  PIC 9(8).
      10 PORT-LAST-MAINT   PIC 9(8).
      10 PORT-STATUS        PIC X(1).  (level-88: A/C/S)
    """
    create_date: str = Field(
        min_length=8,
        max_length=8,
        pattern=r"^\d{8}$",
        description="Creation date YYYYMMDD — PIC 9(8)",
    )
    last_maint: str = Field(
        min_length=8,
        max_length=8,
        pattern=r"^\d{8}$",
        description="Last maintenance date YYYYMMDD — PIC 9(8)",
    )
    status: PortfolioStatus = Field(
        description="Portfolio status — PIC X(1) with level-88 values A/C/S",
    )


class FinancialInfo(BaseModel):
    """
    COBOL group: 05 PORT-FINANCIAL-INFO
      10 PORT-TOTAL-VALUE   PIC S9(13)V99 COMP-3.
      10 PORT-CASH-BALANCE  PIC S9(13)V99 COMP-3.

    Both fields use COMP-3 packed decimal with sign.
    Precision: 13 integer digits + 2 fractional digits.
    """
    total_value: Comp3Signed13v2 = Field(
        description="Total portfolio value — PIC S9(13)V99 COMP-3",
    )
    cash_balance: Comp3Signed13v2 = Field(
        description="Cash balance — PIC S9(13)V99 COMP-3",
    )

    @field_validator("total_value")
    @classmethod
    def validate_total_value(cls, v: Decimal) -> Decimal:
        return _validate_comp3_s9_13_v99(v, "total_value")

    @field_validator("cash_balance")
    @classmethod
    def validate_cash_balance(cls, v: Decimal) -> Decimal:
        return _validate_comp3_s9_13_v99(v, "cash_balance")


class AuditInfo(BaseModel):
    """
    COBOL group: 05 PORT-AUDIT-INFO
      10 PORT-LAST-USER   PIC X(8).
      10 PORT-LAST-TRANS  PIC 9(8).
    """
    last_user: str = Field(
        max_length=8,
        description="Last user who modified record — PIC X(8)",
    )
    last_trans: str = Field(
        min_length=8,
        max_length=8,
        pattern=r"^\d{8}$",
        description="Last transaction date YYYYMMDD — PIC 9(8)",
    )


# ----------------------------------------------------------------
# Top-level record: 01 PORT-RECORD
# ----------------------------------------------------------------

class PortfolioRecord(BaseModel):
    """
    Complete Portfolio Master Record — from COBOL copybook PORTFLIO.cpy.

    Maps to: 01 PORT-RECORD
    VSAM file: Portfolio Master (KSDS, key = PORT-KEY)

    The 05 PORT-FILLER PIC X(50) is intentionally omitted — it is
    reserved space in the COBOL fixed-length record layout and carries
    no business data.
    """
    key: PortfolioKey
    client_info: ClientInfo
    portfolio_info: PortfolioInfo
    financial_info: FinancialInfo
    audit_info: AuditInfo
    filler: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Reserved space — PIC X(50). Omitted in normal usage.",
    )
