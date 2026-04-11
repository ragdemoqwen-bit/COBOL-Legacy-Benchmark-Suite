"""
Pydantic models derived from PRCSEQ.cpy — Process Sequence Definitions.

COBOL source: src/copybook/batch/PRCSEQ.cpy (76 LOC)
"""

from pydantic import BaseModel, Field

from .enums import ProcessDependencyType, ProcessFrequency, ProcessSequenceType


class ProcessDependencyEntry(BaseModel):
    """PSR-DEP-ENTRY OCCURS 10 TIMES — single dependency."""

    dep_id: str = Field(default="", max_length=8, description="PIC X(8)")
    dep_type: ProcessDependencyType = Field(default=ProcessDependencyType.HARD)
    dep_rc: int = Field(default=0, description="PIC S9(4) COMP")


class ProcessSequenceRecord(BaseModel):
    """
    Complete PROCESS-SEQUENCE-RECORD from PRCSEQ.cpy.

    Groups: PSR-KEY, PSR-DATA, PSR-SCHEDULE, PSR-RECOVERY, PSR-AUDIT
    """

    # PSR-KEY
    process_id: str = Field(max_length=8, description="PIC X(8)")
    version: int = Field(default=1, ge=0, le=99, description="PIC 9(2)")
    # PSR-DATA
    description: str = Field(default="", max_length=30, description="PIC X(30)")
    process_type: ProcessSequenceType = Field(description="PIC X(3) — INI/PRC/RPT/TRM")
    # PSR-TIMING
    frequency: ProcessFrequency = Field(default=ProcessFrequency.DAILY)
    start_time: int = Field(default=0, ge=0, le=9999, description="PIC 9(4) — HHMM")
    max_time: int = Field(default=0, ge=0, le=9999, description="PIC 9(4) — minutes")
    # PSR-DEPENDENCIES
    dep_count: int = Field(default=0, ge=0, le=99, description="PIC 9(2) COMP")
    dependencies: list[ProcessDependencyEntry] = Field(
        default_factory=lambda: [ProcessDependencyEntry() for _ in range(10)],
        max_length=10,
        description="OCCURS 10 TIMES",
    )
    # PSR-CONTROL
    program: str = Field(default="", max_length=8, description="PIC X(8)")
    parm: str = Field(default="", max_length=50, description="PIC X(50)")
    max_rc: int = Field(default=0, description="PIC S9(4) COMP")
    restartable: bool = Field(default=True, description="PIC X(1) — Y/N")
    # PSR-SCHEDULE
    active_days: str = Field(default="YYYYYYY", max_length=7, description="PIC X(7)")
    month_end: bool = Field(default=False, description="PIC X(1) — Y/N")
    holiday_run: bool = Field(default=False, description="PIC X(1) — Y/N")
    # PSR-RECOVERY
    recovery_pgm: str = Field(default="", max_length=8, description="PIC X(8)")
    recovery_parm: str = Field(default="", max_length=50, description="PIC X(50)")
    error_limit: int = Field(default=0, ge=0, le=9999, description="PIC 9(4) COMP")
    # PSR-AUDIT
    create_date: str = Field(default="", max_length=10, description="PIC X(10)")
    create_user: str = Field(default="", max_length=8, description="PIC X(8)")
    update_date: str = Field(default="", max_length=10, description="PIC X(10)")
    update_user: str = Field(default="", max_length=8, description="PIC X(8)")


class StandardSequences:
    """
    Named process sequences from STANDARD-SEQUENCES in PRCSEQ.cpy.

    These define the standard batch execution order.
    """

    START_OF_DAY = ["INITDAY", "CKPCLR", "DATEVAL"]
    MAIN_PROCESS = ["TRNVAL00", "POSUPD00", "HISTLD00"]
    END_OF_DAY = ["RPTGEN00", "BCKLOD00", "ENDDAY"]
