"""
Pydantic models derived from HISTREC.cpy — History Record Structure.

COBOL source: src/copybook/common/HISTREC.cpy (40 LOC)
All fields are alphanumeric (no COMP-3).
"""

from pydantic import BaseModel, Field

from .enums import HistoryActionCode, HistoryRecordType


class HistoryRecord(BaseModel):
    """
    Complete HISTORY-RECORD from HISTREC.cpy.

    Groups: HIST-KEY, HIST-DATA, HIST-AUDIT
    """

    # HIST-KEY
    portfolio_id: str = Field(max_length=8, description="PIC X(08)")
    history_date: str = Field(max_length=8, description="PIC X(08) — YYYYMMDD")
    history_time: str = Field(max_length=6, description="PIC X(06) — HHMMSS")
    seq_no: str = Field(max_length=4, description="PIC X(04)")
    # HIST-DATA
    record_type: HistoryRecordType = Field(description="PIC X(02) — PT/PS/TR")
    action_code: HistoryActionCode = Field(description="PIC X(01) — A/C/D")
    before_image: str = Field(default="", max_length=400, description="PIC X(400)")
    after_image: str = Field(default="", max_length=400, description="PIC X(400)")
    reason_code: str = Field(default="", max_length=4, description="PIC X(04)")
    # HIST-AUDIT
    process_date: str = Field(default="", max_length=26, description="PIC X(26)")
    process_user: str = Field(default="", max_length=8, description="PIC X(08)")
