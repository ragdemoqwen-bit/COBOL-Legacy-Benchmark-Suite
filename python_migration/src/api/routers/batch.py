"""
Batch Operations API Router — exposes batch job management as REST endpoints.

Replaces:
  BCHCTL00.cbl (128 LOC) — Batch Control Processor
  PRCSEQ00.cbl (346 LOC) — Process Sequence Manager
  RCVPRC00.cbl (303 LOC) — Process Recovery Handler

Target: FastAPI REST endpoints for batch job orchestration.

In COBOL, batch jobs were triggered via JCL and controlled through
working-storage area function dispatching. In Python, they become
API endpoints for job management.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from models.enums import BatchProcessStatus, ReturnCode
from services.batch.batch_control import BatchControlProcessor
from services.batch.process_sequence import ProcessSequenceManager
from services.batch.recovery import RecoveryHandler

router = APIRouter(prefix="/batch", tags=["batch"])

_batch_ctl = BatchControlProcessor()
_sequence_mgr = ProcessSequenceManager()
_recovery = RecoveryHandler()


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------
class JobInitRequest(BaseModel):
    """Request to initialize a batch job."""

    job_name: str = Field(max_length=8)
    prerequisites: list[str] = Field(default_factory=list)


class JobStatusUpdate(BaseModel):
    """Request to update job status."""

    status: BatchProcessStatus
    records_processed: int = 0
    records_errored: int = 0


class SequenceInitRequest(BaseModel):
    """Request to initialize a process sequence."""

    processes: list[dict]


class RecoveryRequest(BaseModel):
    """Request to execute a recovery action."""

    process_id: str
    action: str = Field(pattern="^[RBT]$")
    reason: str = ""


# ---------------------------------------------------------------------------
# Batch Job Control Endpoints (replaces BCHCTL00.cbl)
# ---------------------------------------------------------------------------
@router.post("/jobs/{job_name}/init")
def init_job(job_name: str, body: JobInitRequest):
    """Initialize a batch job — replaces BCHCTL00 'INIT' function."""
    rc = _batch_ctl.initialize_job(job_name, body.prerequisites)
    return {"job_name": job_name, "status": "initialized", "return_code": rc.value}


@router.get("/jobs/{job_name}/check")
def check_prerequisites(job_name: str):
    """Check job prerequisites — replaces BCHCTL00 'CHEK' function."""
    rc = _batch_ctl.check_prerequisites(job_name)
    return {"job_name": job_name, "prerequisites_met": rc == ReturnCode.SUCCESS, "return_code": rc.value}


@router.put("/jobs/{job_name}/status")
def update_job_status(job_name: str, body: JobStatusUpdate):
    """Update job status — replaces BCHCTL00 'UPDT' function."""
    rc = _batch_ctl.update_status(
        job_name, body.status, body.records_processed, body.records_errored
    )
    if rc != ReturnCode.SUCCESS:
        raise HTTPException(status_code=404, detail=f"Job {job_name} not found")
    return {"job_name": job_name, "status": body.status.value, "return_code": rc.value}


@router.post("/jobs/{job_name}/terminate")
def terminate_job(job_name: str):
    """Terminate a batch job — replaces BCHCTL00 'TERM' function."""
    rc = _batch_ctl.terminate_job(job_name)
    if rc != ReturnCode.SUCCESS:
        raise HTTPException(status_code=404, detail=f"Job {job_name} not found")
    job = _batch_ctl.get_job_status(job_name)
    return {
        "job_name": job_name,
        "status": job.status.value if job else "UNKNOWN",
        "return_code": rc.value,
    }


@router.get("/jobs")
def list_jobs():
    """List all batch jobs."""
    jobs = _batch_ctl.get_all_jobs()
    return {
        name: {
            "status": job.status.value,
            "records_processed": job.records_processed,
            "records_errored": job.records_errored,
            "return_code": job.return_code.value,
        }
        for name, job in jobs.items()
    }


# ---------------------------------------------------------------------------
# Process Sequence Endpoints (replaces PRCSEQ00.cbl)
# ---------------------------------------------------------------------------
@router.post("/sequence/init")
def init_sequence(body: SequenceInitRequest):
    """Initialize process sequence — replaces PRCSEQ00 'INIT' function."""
    rc = _sequence_mgr.initialize(body.processes)
    return {"status": "initialized", "return_code": rc.value}


@router.get("/sequence/ready")
def get_ready_processes():
    """Get processes ready to execute — replaces PRCSEQ00 'CHEK' function."""
    ready = _sequence_mgr.get_ready_processes()
    return {"ready_processes": ready}


@router.get("/sequence/status")
def get_sequence_status():
    """Get sequence status — replaces PRCSEQ00 'STAT' function."""
    return _sequence_mgr.get_sequence_status()


# ---------------------------------------------------------------------------
# Recovery Endpoints (replaces RCVPRC00.cbl)
# ---------------------------------------------------------------------------
@router.post("/recovery/analyze")
def analyze_failure(process_id: str, error_code: int, error_message: str = ""):
    """Analyze a failure — replaces RCVPRC00 'ANLZ' function."""
    action, rc = _recovery.analyze_failure(process_id, error_code, error_message)
    return {"process_id": process_id, "recommended_action": action, "return_code": rc.value}


@router.post("/recovery/execute")
def execute_recovery(body: RecoveryRequest):
    """Execute a recovery action — replaces RCVPRC00 'EXEC' function."""
    rc = _recovery.execute_recovery(
        body.process_id,
        body.action,
        BatchProcessStatus.ERROR,
        body.reason,
    )
    if rc != ReturnCode.SUCCESS:
        raise HTTPException(status_code=400, detail="Recovery execution failed")
    return {"process_id": body.process_id, "action": body.action, "return_code": rc.value}


@router.get("/recovery/status")
def get_recovery_status():
    """Get recovery status — replaces RCVPRC00 'STAT' function."""
    status, rc = _recovery.get_recovery_status()
    return status
