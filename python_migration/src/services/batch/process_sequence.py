"""
Process Sequence Manager — converted from PRCSEQ00.cbl (346 LOC).

Replaces: COBOL PRCSEQ00 program — manages process sequencing, dependency
          checking, status updates, completion checking.
Target:   Python DAG-based process orchestration.

COBOL interface (LINKAGE SECTION):
  LS-PSR-FUNCTION   PIC X(4) — 'INIT'/'CHEK'/'UPDT'/'COMP'/'STAT'
  LS-PSR-PROCESS-ID PIC X(8)
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime

from models.enums import (
    BatchProcessStatus,
    ProcessDependencyType,
    ProcessFrequency,
    ProcessSequenceType,
    ReturnCode,
)

logger = logging.getLogger(__name__)


@dataclass
class ProcessStep:
    """A single process step — replaces PRCSEQ00.cbl WS-PROCESS-ENTRY."""

    process_id: str
    process_type: ProcessSequenceType
    frequency: ProcessFrequency = ProcessFrequency.DAILY
    status: BatchProcessStatus = BatchProcessStatus.READY
    sequence_number: int = 0
    dependencies: list[str] = field(default_factory=list)
    dependency_type: ProcessDependencyType = ProcessDependencyType.HARD
    start_time: datetime | None = None
    end_time: datetime | None = None
    return_code: int = 0


class ProcessSequenceManager:
    """
    Manages process execution sequencing — replaces PRCSEQ00.cbl.

    Implements a simple DAG-based process orchestrator that:
    1. Registers processes with dependencies
    2. Checks if dependencies are satisfied before allowing execution
    3. Tracks status of each process
    4. Determines overall sequence completion
    """

    def __init__(self) -> None:
        self.processes: dict[str, ProcessStep] = {}
        self._sequence_counter: int = 0

    def initialize(self, process_definitions: list[dict]) -> ReturnCode:
        """
        Initialize the process sequence from definitions.

        Replaces: 1000-INIT-SEQUENCE paragraph.
        """
        self.processes.clear()
        self._sequence_counter = 0

        for defn in process_definitions:
            self._sequence_counter += 1
            step = ProcessStep(
                process_id=defn["process_id"],
                process_type=ProcessSequenceType(defn.get("process_type", "PRC")),
                frequency=ProcessFrequency(defn.get("frequency", "D")),
                sequence_number=self._sequence_counter,
                dependencies=defn.get("dependencies", []),
                dependency_type=ProcessDependencyType(defn.get("dependency_type", "H")),
            )
            self.processes[step.process_id] = step

        logger.info("Process sequence initialized with %d steps", len(self.processes))
        return ReturnCode.SUCCESS

    def check_dependencies(self, process_id: str) -> ReturnCode:
        """
        Check if all dependencies for a process are satisfied.

        Replaces: 2000-CHECK-DEPENDENCIES paragraph.
        """
        step = self.processes.get(process_id)
        if step is None:
            logger.error("Process %s not found", process_id)
            return ReturnCode.ERROR

        for dep_id in step.dependencies:
            dep = self.processes.get(dep_id)
            if dep is None:
                if step.dependency_type == ProcessDependencyType.HARD:
                    logger.error("Hard dependency %s not found for %s", dep_id, process_id)
                    return ReturnCode.ERROR
                continue

            if dep.status != BatchProcessStatus.DONE:
                if step.dependency_type == ProcessDependencyType.HARD:
                    logger.info("Hard dependency %s not complete for %s", dep_id, process_id)
                    return ReturnCode.WARNING
                logger.info("Soft dependency %s not complete for %s (proceeding)", dep_id, process_id)

        return ReturnCode.SUCCESS

    def update_status(
        self,
        process_id: str,
        status: BatchProcessStatus,
        return_code: int = 0,
    ) -> ReturnCode:
        """
        Update process status.

        Replaces: 3000-UPDATE-STATUS paragraph.
        """
        step = self.processes.get(process_id)
        if step is None:
            return ReturnCode.ERROR

        step.status = status
        step.return_code = return_code

        if status == BatchProcessStatus.ACTIVE and step.start_time is None:
            step.start_time = datetime.now()
        elif status in (BatchProcessStatus.DONE, BatchProcessStatus.ERROR):
            step.end_time = datetime.now()

        logger.info("Process %s status → %s (rc=%d)", process_id, status.value, return_code)
        return ReturnCode.SUCCESS

    def check_completion(self) -> tuple[bool, ReturnCode]:
        """
        Check if all processes in the sequence have completed.

        Replaces: 4000-CHECK-COMPLETION paragraph.
        """
        all_done = all(
            step.status in (BatchProcessStatus.DONE, BatchProcessStatus.ERROR)
            for step in self.processes.values()
        )
        has_errors = any(
            step.status == BatchProcessStatus.ERROR
            for step in self.processes.values()
        )

        if all_done:
            rc = ReturnCode.WARNING if has_errors else ReturnCode.SUCCESS
            return True, rc
        return False, ReturnCode.SUCCESS

    def get_ready_processes(self) -> list[str]:
        """Get list of processes ready to execute (dependencies met)."""
        ready = []
        for process_id, step in self.processes.items():
            if step.status == BatchProcessStatus.READY:
                if self.check_dependencies(process_id) == ReturnCode.SUCCESS:
                    ready.append(process_id)
        return ready

    def get_sequence_status(self) -> dict:
        """Get overall sequence status report."""
        status_counts: dict[str, int] = {}
        for step in self.processes.values():
            key = step.status.value
            status_counts[key] = status_counts.get(key, 0) + 1

        return {
            "total_processes": len(self.processes),
            "status_counts": status_counts,
            "processes": {
                pid: {
                    "type": step.process_type.value,
                    "status": step.status.value,
                    "return_code": step.return_code,
                    "sequence": step.sequence_number,
                }
                for pid, step in self.processes.items()
            },
        }
