"""
Pydantic models derived from BCHCTL.cpy and BCHCON.cpy — Batch Control Definitions.

COBOL sources:
  src/copybook/batch/BCHCTL.cpy (50 LOC) — Batch control record
  src/copybook/batch/BCHCON.cpy (66 LOC) — Batch control constants
"""

from pydantic import BaseModel, Field

from .enums import BatchProcessStatus


class PrerequisiteJob(BaseModel):
    """BCT-PREREQ-JOBS OCCURS 10 TIMES — single prerequisite entry."""

    prereq_name: str = Field(default="", max_length=8, description="PIC X(8)")
    prereq_seq: int = Field(default=0, ge=0, le=9999, description="PIC 9(4)")
    prereq_rc: int = Field(default=0, description="PIC S9(4) COMP")


class BatchControlRecord(BaseModel):
    """
    Complete BATCH-CONTROL-RECORD from BCHCTL.cpy.

    Groups: BCT-KEY, BCT-DATA, BCT-STATISTICS
    """

    # BCT-KEY
    job_name: str = Field(max_length=8, description="PIC X(8)")
    process_date: str = Field(max_length=8, description="PIC X(8) — YYYYMMDD")
    sequence_no: int = Field(ge=0, le=9999, description="PIC 9(4)")
    # BCT-DATA
    status: BatchProcessStatus = Field(default=BatchProcessStatus.READY)
    # BCT-PROCESS-CONTROL
    step_name: str = Field(default="", max_length=8, description="PIC X(8)")
    program_name: str = Field(default="", max_length=8, description="PIC X(8)")
    start_time: str = Field(default="", max_length=8, description="PIC X(8)")
    end_time: str = Field(default="", max_length=8, description="PIC X(8)")
    # BCT-DEPENDENCIES
    prereq_count: int = Field(default=0, ge=0, le=99, description="PIC 9(2) COMP")
    prereq_jobs: list[PrerequisiteJob] = Field(
        default_factory=lambda: [PrerequisiteJob() for _ in range(10)],
        max_length=10,
        description="OCCURS 10 TIMES",
    )
    # BCT-RETURN-INFO
    return_code: int = Field(default=0, description="PIC S9(4) COMP")
    error_desc: str = Field(default="", max_length=80, description="PIC X(80)")
    # BCT-STATISTICS
    restart_count: int = Field(default=0, ge=0, le=99, description="PIC 9(2) COMP")
    attempt_ts: str = Field(default="", max_length=26, description="PIC X(26)")
    complete_ts: str = Field(default="", max_length=26, description="PIC X(26)")


class BatchControlConstants:
    """
    Named constants from BCHCON.cpy — BATCH-CONTROL-CONSTANTS.

    These are compile-time constants, not runtime data, so they are plain class attributes.
    """

    # Process Status Values
    STAT_READY = "R"
    STAT_ACTIVE = "A"
    STAT_WAITING = "W"
    STAT_DONE = "D"
    STAT_ERROR = "E"

    # Return Code Thresholds
    RC_SUCCESS = 0
    RC_WARNING = 4
    RC_ERROR = 8
    RC_SEVERE = 12
    RC_CRITICAL = 16

    # Process Control Values
    MAX_PREREQ = 10
    MAX_RESTARTS = 3
    WAIT_INTERVAL = 300  # seconds
    MAX_WAIT_TIME = 3600  # seconds

    # Process Types
    TYPE_INITIAL = "INI"
    TYPE_UPDATE = "UPD"
    TYPE_REPORT = "RPT"
    TYPE_CLEANUP = "CLN"

    # Dependency Types
    DEP_REQUIRED = "R"
    DEP_OPTIONAL = "O"
    DEP_EXCLUSIVE = "X"

    # Special Process Names
    START_OF_DAY = "STARTDAY"
    END_OF_DAY = "ENDDAY"
    EMERGENCY = "EMERGENCY"

    # Standard Messages
    MSG_STARTING = "Process starting..."
    MSG_COMPLETE = "Process completed successfully"
    MSG_FAILED = "Process failed - check errors"
    MSG_WAITING = "Waiting for prerequisites"
