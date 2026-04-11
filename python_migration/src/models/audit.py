"""
Pydantic models derived from AUDITLOG.cpy — Audit Trail Record Definitions.

COBOL source: src/copybook/common/AUDITLOG.cpy (37 LOC)
All fields are alphanumeric (no COMP-3).
"""

from pydantic import BaseModel, Field

from .enums import AuditAction, AuditStatus, AuditType


class AuditRecord(BaseModel):
    """
    Complete AUDIT-RECORD from AUDITLOG.cpy.

    Groups: AUD-HEADER, AUD-TYPE, AUD-ACTION, AUD-STATUS, AUD-KEY-INFO, images, message
    """

    # AUD-HEADER
    timestamp: str = Field(max_length=26, description="PIC X(26)")
    system_id: str = Field(default="", max_length=8, description="PIC X(8)")
    user_id: str = Field(default="", max_length=8, description="PIC X(8)")
    program: str = Field(default="", max_length=8, description="PIC X(8)")
    terminal: str = Field(default="", max_length=8, description="PIC X(8)")
    # Classification
    audit_type: AuditType = Field(description="PIC X(4) — TRAN/USER/SYST")
    action: AuditAction = Field(description="PIC X(8)")
    status: AuditStatus = Field(description="PIC X(4) — SUCC/FAIL/WARN")
    # AUD-KEY-INFO
    portfolio_id: str = Field(default="", max_length=8, description="PIC X(8)")
    account_no: str = Field(default="", max_length=10, description="PIC X(10)")
    # Images
    before_image: str = Field(default="", max_length=100, description="PIC X(100)")
    after_image: str = Field(default="", max_length=100, description="PIC X(100)")
    message: str = Field(default="", max_length=100, description="PIC X(100)")
