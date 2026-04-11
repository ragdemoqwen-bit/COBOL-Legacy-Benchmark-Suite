"""
Batch Control Processor — converted from BCHCTL00.cbl (128 LOC).

Replaces: COBOL BCHCTL00 program — manages batch job control with
          INIT/CHEK/UPDT/TERM functions, prerequisite checking.
Target:   Python batch job orchestration.

COBOL interface (LINKAGE SECTION):
  LS-BCT-FUNCTION  PIC X(4) — 'INIT'/'CHEK'/'UPDT'/'TERM'
  LS-BCT-JOB-NAME  PIC X(8)
  LS-BCT-RETURN-CODE PIC S9(4) COMP
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime

from models.enums import BatchProcessStatus, ReturnCode

logger = logging.getLogger(__name__)


@dataclass
class BatchJob:
    """Represents a batch job — replaces BCHCTL00.cbl WS-JOB-RECORD."""

    job_name: str
    status: BatchProcessStatus = BatchProcessStatus.READY
    start_time: datetime | None = None
    end_time: datetime | None = None
    return_code: ReturnCode = ReturnCode.SUCCESS
    records_processed: int = 0
    records_errored: int = 0
    prerequisites: list[str] = field(default_factory=list)


class BatchControlProcessor:
    """
    Manages batch job lifecycle — replaces BCHCTL00.cbl.

    COBOL EVALUATE TRUE dispatch on LS-BCT-FUNCTION:
      'INIT' → initialize_job()
      'CHEK' → check_prerequisites()
      'UPDT' → update_status()
      'TERM' → terminate_job()
    """

    def __init__(self) -> None:
        self.jobs: dict[str, BatchJob] = {}

    def initialize_job(self, job_name: str, prerequisites: list[str] | None = None) -> ReturnCode:
        """
        Initialize a batch job.

        Replaces: 1000-INIT-JOB paragraph.
        """
        if job_name in self.jobs:
            logger.warning("Job %s already exists, reinitializing", job_name)

        self.jobs[job_name] = BatchJob(
            job_name=job_name,
            status=BatchProcessStatus.READY,
            start_time=datetime.now(),
            prerequisites=prerequisites or [],
        )
        logger.info("Job %s initialized", job_name)
        return ReturnCode.SUCCESS

    def check_prerequisites(self, job_name: str) -> ReturnCode:
        """
        Check if all prerequisite jobs have completed successfully.

        Replaces: 2000-CHECK-PREREQS paragraph.
        """
        job = self.jobs.get(job_name)
        if job is None:
            logger.error("Job %s not found", job_name)
            return ReturnCode.ERROR

        for prereq in job.prerequisites:
            prereq_job = self.jobs.get(prereq)
            if prereq_job is None:
                logger.warning("Prerequisite %s not found for job %s", prereq, job_name)
                return ReturnCode.WARNING
            if prereq_job.status != BatchProcessStatus.DONE:
                logger.info("Prerequisite %s not complete (status=%s)", prereq, prereq_job.status.value)
                return ReturnCode.WARNING

        logger.info("All prerequisites met for job %s", job_name)
        return ReturnCode.SUCCESS

    def update_status(
        self,
        job_name: str,
        status: BatchProcessStatus,
        records_processed: int = 0,
        records_errored: int = 0,
    ) -> ReturnCode:
        """
        Update batch job status.

        Replaces: 3000-UPDATE-STATUS paragraph.
        """
        job = self.jobs.get(job_name)
        if job is None:
            logger.error("Job %s not found", job_name)
            return ReturnCode.ERROR

        job.status = status
        job.records_processed += records_processed
        job.records_errored += records_errored
        logger.info("Job %s status → %s (processed=%d, errors=%d)",
                     job_name, status.value, job.records_processed, job.records_errored)
        return ReturnCode.SUCCESS

    def terminate_job(self, job_name: str, return_code: ReturnCode = ReturnCode.SUCCESS) -> ReturnCode:
        """
        Terminate a batch job.

        Replaces: 4000-TERMINATE-JOB paragraph.
        """
        job = self.jobs.get(job_name)
        if job is None:
            logger.error("Job %s not found", job_name)
            return ReturnCode.ERROR

        job.status = BatchProcessStatus.DONE if return_code == ReturnCode.SUCCESS else BatchProcessStatus.ERROR
        job.end_time = datetime.now()
        job.return_code = return_code

        elapsed = (job.end_time - job.start_time).total_seconds() if job.start_time else 0
        logger.info(
            "Job %s terminated: rc=%d, processed=%d, errors=%d, elapsed=%.1fs",
            job_name, return_code.value, job.records_processed, job.records_errored, elapsed,
        )
        return ReturnCode.SUCCESS

    def get_job_status(self, job_name: str) -> BatchJob | None:
        """Get current job status."""
        return self.jobs.get(job_name)

    def get_all_jobs(self) -> dict[str, BatchJob]:
        """Get all job statuses."""
        return self.jobs
