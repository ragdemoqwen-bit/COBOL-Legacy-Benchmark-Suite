"""
Pydantic models derived from online copybooks.

COBOL sources:
  src/copybook/online/INQCOM.cpy (13 LOC) — Online Inquiry Communication Area
  src/copybook/online/DB2REQ.cpy (14 LOC) — DB2 Request Area
  src/copybook/online/ERRHND.cpy (22 LOC) — Online Error Handling
"""

from pydantic import BaseModel, Field

from .enums import DB2RequestType, InquiryFunction, OnlineErrorAction, OnlineErrorSeverity


# ---------------------------------------------------------------------------
# From INQCOM.cpy — INQCOM-AREA
# ---------------------------------------------------------------------------
class InquiryCommunicationArea(BaseModel):
    """INQCOM-AREA from INQCOM.cpy — communication between online inquiry programs."""

    function: InquiryFunction = Field(description="PIC X(4) — MENU/INQP/INQH/EXIT")
    account_no: str = Field(default="", max_length=10, description="PIC X(10)")
    response_code: int = Field(default=0, description="PIC S9(8) COMP")
    error_msg: str = Field(default="", max_length=80, description="PIC X(80)")


# ---------------------------------------------------------------------------
# From DB2REQ.cpy — DB2-REQUEST-AREA
# ---------------------------------------------------------------------------
class DB2RequestArea(BaseModel):
    """DB2-REQUEST-AREA from DB2REQ.cpy — DB2 connection management."""

    request_type: DB2RequestType = Field(description="PIC X — C/D/S")
    response_code: int = Field(default=0, description="PIC S9(8) COMP")
    connection_token: str = Field(default="", max_length=16, description="PIC X(16)")
    # DB2-ERROR-INFO
    sqlcode: int = Field(default=0, description="PIC S9(9) COMP")
    error_msg: str = Field(default="", max_length=80, description="PIC X(80)")


# ---------------------------------------------------------------------------
# From ERRHND.cpy — ERROR-HANDLING (online version)
# ---------------------------------------------------------------------------
class OnlineErrorHandling(BaseModel):
    """ERROR-HANDLING from online/ERRHND.cpy — CICS error handling structure."""

    program: str = Field(default="", max_length=8, description="PIC X(8)")
    paragraph: str = Field(default="", max_length=30, description="PIC X(30)")
    sqlcode: int = Field(default=0, description="PIC S9(9) COMP")
    cics_resp: int = Field(default=0, description="PIC S9(8) COMP")
    cics_resp2: int = Field(default=0, description="PIC S9(8) COMP")
    severity: OnlineErrorSeverity = Field(default=OnlineErrorSeverity.INFO)
    message: str = Field(default="", max_length=80, description="PIC X(80)")
    action: OnlineErrorAction = Field(default=OnlineErrorAction.RETURN)
    # ERR-TRACE
    trace_id: str = Field(default="", max_length=16, description="PIC X(16)")
    timestamp: str = Field(default="", max_length=26, description="PIC X(26)")
