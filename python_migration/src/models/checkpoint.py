"""
Pydantic models derived from CKPRST.cpy — Checkpoint/Restart Control Structure.

COBOL source: src/copybook/batch/CKPRST.cpy (77 LOC)
"""

from pydantic import BaseModel, Field

from .enums import CheckpointPhase, CheckpointRestartMode, CheckpointStatus


class CheckpointFileStatus(BaseModel):
    """CK-FILE-STATUS OCCURS 5 TIMES — single file tracking entry."""

    file_name: str = Field(default="", max_length=8, description="PIC X(8)")
    file_pos: str = Field(default="", max_length=50, description="PIC X(50)")
    file_status: str = Field(default="", max_length=2, description="PIC X(2)")


class CheckpointControl(BaseModel):
    """
    Complete CHECKPOINT-CONTROL from CKPRST.cpy.

    Groups: CK-HEADER, CK-COUNTERS, CK-POSITION, CK-RESOURCES, CK-CONTROL-INFO
    """

    # CK-HEADER
    program_id: str = Field(max_length=8, description="PIC X(8)")
    run_date: str = Field(max_length=8, description="PIC X(8) — YYYYMMDD")
    run_time: str = Field(max_length=6, description="PIC X(6) — HHMMSS")
    status: CheckpointStatus = Field(default=CheckpointStatus.INITIAL)
    # CK-COUNTERS
    records_read: int = Field(default=0, ge=0, description="PIC 9(9) COMP")
    records_proc: int = Field(default=0, ge=0, description="PIC 9(9) COMP")
    records_error: int = Field(default=0, ge=0, description="PIC 9(9) COMP")
    restart_count: int = Field(default=0, ge=0, le=99, description="PIC 9(2) COMP")
    # CK-POSITION
    last_key: str = Field(default="", max_length=50, description="PIC X(50)")
    last_time: str = Field(default="", max_length=26, description="PIC X(26)")
    phase: CheckpointPhase = Field(default=CheckpointPhase.INIT)
    # CK-RESOURCES
    file_statuses: list[CheckpointFileStatus] = Field(
        default_factory=lambda: [CheckpointFileStatus() for _ in range(5)],
        max_length=5,
        description="OCCURS 5 TIMES",
    )
    # CK-CONTROL-INFO
    commit_freq: int = Field(default=1000, ge=0, le=99999, description="PIC 9(5) COMP")
    max_errors: int = Field(default=100, ge=0, le=999, description="PIC 9(3) COMP")
    max_restarts: int = Field(default=3, ge=0, le=99, description="PIC 9(2) COMP")
    restart_mode: CheckpointRestartMode = Field(default=CheckpointRestartMode.NORMAL)


class CheckpointRecord(BaseModel):
    """CHECKPOINT-RECORD from CKPRST.cpy — persisted to VSAM checkpoint file."""

    program_id: str = Field(max_length=8, description="PIC X(8)")
    run_date: str = Field(max_length=8, description="PIC X(8)")
    data: str = Field(default="", max_length=400, description="PIC X(400)")
