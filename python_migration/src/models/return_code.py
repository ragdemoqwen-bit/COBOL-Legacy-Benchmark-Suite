"""
Pydantic models derived from RTNCODE.cpy — Return Code Management.

COBOL source: src/copybook/common/RTNCODE.cpy (33 LOC)
"""

from pydantic import BaseModel, Field

from .enums import ReturnCodeRequestType, ReturnCodeStatus


class ReturnCodeArea(BaseModel):
    """
    Complete RETURN-CODE-AREA from RTNCODE.cpy.

    Used by the return code management service (RTNCDE00.cbl).
    """

    request_type: ReturnCodeRequestType = Field(
        default=ReturnCodeRequestType.INITIALIZE,
        description="PIC X — I/S/G/L/A",
    )
    program_id: str = Field(default="", max_length=8, description="PIC X(8)")
    # RC-CODES-AREA
    current_code: int = Field(default=0, description="PIC S9(4) COMP")
    highest_code: int = Field(default=0, description="PIC S9(4) COMP")
    new_code: int = Field(default=0, description="PIC S9(4) COMP")
    status: ReturnCodeStatus = Field(default=ReturnCodeStatus.SUCCESS, description="PIC X")
    message: str = Field(default="", max_length=80, description="PIC X(80)")
    response_code: int = Field(default=0, description="PIC S9(8) COMP")
    # RC-ANALYSIS-DATA
    start_time: str = Field(default="", max_length=26, description="PIC X(26)")
    end_time: str = Field(default="", max_length=26, description="PIC X(26)")
    total_codes: int = Field(default=0, description="PIC S9(8) COMP")
    max_code: int = Field(default=0, description="PIC S9(4) COMP")
    min_code: int = Field(default=0, description="PIC S9(4) COMP")
    # RC-RETURN-DATA
    return_value: int = Field(default=0, description="PIC S9(4) COMP")
    highest_return: int = Field(default=0, description="PIC S9(4) COMP")
    return_status: str = Field(default="", max_length=1, description="PIC X")
