"""
Pydantic models derived from ERRHAND.cpy and RETHND.cpy — Error Handling Definitions.

COBOL sources:
  src/copybook/common/ERRHAND.cpy (57 LOC) — Error categories, return codes, VSAM statuses
  src/copybook/common/RETHND.cpy  (67 LOC) — Return code handling with nested structures
"""

from pydantic import BaseModel, Field

from .enums import ErrorAction, ErrorType, ReturnCode


# ---------------------------------------------------------------------------
# From ERRHAND.cpy — ERR-MESSAGE structure
# ---------------------------------------------------------------------------
class ErrorMessage(BaseModel):
    """ERR-MESSAGE from ERRHAND.cpy — structured error record."""

    err_date: str = Field(default="", max_length=10, description="PIC X(10)")
    err_time: str = Field(default="", max_length=8, description="PIC X(8)")
    program: str = Field(default="", max_length=8, description="PIC X(8)")
    category: str = Field(default="", max_length=2, description="PIC X(2) — VS/VL/PR/SY")
    code: str = Field(default="", max_length=4, description="PIC X(4)")
    severity: int = Field(default=0, description="PIC S9(4) COMP")
    text: str = Field(default="", max_length=80, description="PIC X(80)")
    details: str = Field(default="", max_length=256, description="PIC X(256)")


# ---------------------------------------------------------------------------
# VSAM status constants from ERRHAND.cpy
# ---------------------------------------------------------------------------
class VsamStatus:
    """VSAM file status code constants from ERR-VSAM-STATUSES."""

    SUCCESS = "00"
    DUPLICATE_KEY = "22"
    NOT_FOUND = "23"
    END_OF_FILE = "10"


# ---------------------------------------------------------------------------
# From RETHND.cpy — RETURN-HANDLING structure
# ---------------------------------------------------------------------------
class ErrorLocation(BaseModel):
    """ERROR-LOCATION from RETHND.cpy."""

    program_name: str = Field(default="", max_length=8, description="PIC X(8)")
    paragraph_name: str = Field(default="", max_length=8, description="PIC X(8)")
    error_routine: str = Field(default="", max_length=8, description="PIC X(8)")


class ErrorInfo(BaseModel):
    """ERROR-INFO from RETHND.cpy."""

    error_type: ErrorType = Field(default=ErrorType.PROCESSING)
    error_code: str = Field(default="", max_length=4, description="PIC X(4)")
    error_text: str = Field(default="", max_length=80, description="PIC X(80)")


class SystemInfo(BaseModel):
    """SYSTEM-INFO from RETHND.cpy."""

    system_code: str = Field(default="", max_length=4, description="PIC X(4)")
    system_msg: str = Field(default="", max_length=80, description="PIC X(80)")


class ReturnActions(BaseModel):
    """RETURN-ACTIONS from RETHND.cpy."""

    action_flag: ErrorAction = Field(default=ErrorAction.CONTINUE)
    retry_count: int = Field(default=0, ge=0, le=99, description="PIC 9(2) COMP")
    max_retries: int = Field(default=3, ge=0, le=99, description="PIC 9(2) COMP")


class ReturnHandling(BaseModel):
    """
    Complete RETURN-HANDLING from RETHND.cpy.

    Top-level structure with RETURN-STATUS, RETURN-DETAILS, RETURN-ACTIONS.
    """

    # RETURN-STATUS
    return_code: ReturnCode = Field(default=ReturnCode.SUCCESS)
    reason_code: int = Field(default=0, description="PIC S9(4) COMP")
    module_id: str = Field(default="", max_length=8, description="PIC X(8)")
    function_id: str = Field(default="", max_length=8, description="PIC X(8)")
    # RETURN-DETAILS
    location: ErrorLocation = Field(default_factory=ErrorLocation)
    error_info: ErrorInfo = Field(default_factory=ErrorInfo)
    system_info: SystemInfo = Field(default_factory=SystemInfo)
    # RETURN-ACTIONS
    actions: ReturnActions = Field(default_factory=ReturnActions)


# ---------------------------------------------------------------------------
# Standard Error Codes from RETHND.cpy STD-ERROR-CODES
# ---------------------------------------------------------------------------
class StandardErrorCode:
    """Named constants from STD-ERROR-CODES in RETHND.cpy."""

    INVALID_DATA = "E001"
    NOT_FOUND = "E002"
    DUPLICATE = "E003"
    FILE_ERROR = "E004"
    DB_ERROR = "E005"
    SECURITY = "E006"
    PROCESSING = "E007"
    VALIDATION = "E008"
    VERSION = "E009"
    TIMEOUT = "E010"
