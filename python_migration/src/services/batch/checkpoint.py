"""
Checkpoint/Restart — converted from CKPRST.cbl (58 LOC).

Replaces: COBOL CKPRST program — handles checkpoint initialization,
          taking checkpoints, committing, and restart processing.
Target:   Python checkpoint management for batch resumability.

COBOL interface (LINKAGE SECTION):
  LS-CK-FUNCTION  PIC X(4)  — 'INIT'/'TAKE'/'CMIT'/'REST'
  LS-CK-DATA      PIC X(100)
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from models.enums import CheckpointPhase, CheckpointRestartMode, CheckpointStatus, ReturnCode

logger = logging.getLogger(__name__)

# Checkpoint file location
CHECKPOINT_DIR = Path("/tmp/checkpoints")


@dataclass
class CheckpointData:
    """Checkpoint state — replaces CKPRST.cbl WS-CHECKPOINT-RECORD."""

    job_name: str
    phase: CheckpointPhase
    status: CheckpointStatus
    restart_mode: CheckpointRestartMode
    records_processed: int
    last_key: str
    timestamp: str
    custom_data: dict


class CheckpointManager:
    """
    Manages checkpoint/restart processing — replaces CKPRST.cbl.

    COBOL EVALUATE TRUE dispatch:
      'INIT' → initialize()
      'TAKE' → take_checkpoint()
      'CMIT' → commit_checkpoint()
      'REST' → restart_from_checkpoint()
    """

    def __init__(self, job_name: str) -> None:
        self.job_name = job_name
        self.current_checkpoint: CheckpointData | None = None
        CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

    def _checkpoint_path(self) -> Path:
        return CHECKPOINT_DIR / f"{self.job_name}.ckpt.json"

    def initialize(self) -> ReturnCode:
        """
        Initialize checkpoint processing.

        Replaces: 1000-INIT-CHECKPOINT paragraph.
        """
        self.current_checkpoint = CheckpointData(
            job_name=self.job_name,
            phase=CheckpointPhase.INIT,
            status=CheckpointStatus.INITIAL,
            restart_mode=CheckpointRestartMode.NORMAL,
            records_processed=0,
            last_key="",
            timestamp=datetime.now().isoformat(),
            custom_data={},
        )
        logger.info("Checkpoint initialized for job %s", self.job_name)
        return ReturnCode.SUCCESS

    def take_checkpoint(
        self,
        phase: CheckpointPhase,
        records_processed: int,
        last_key: str,
        custom_data: dict | None = None,
    ) -> ReturnCode:
        """
        Take a checkpoint (save current state).

        Replaces: 2000-TAKE-CHECKPOINT paragraph.
        """
        if self.current_checkpoint is None:
            logger.error("Checkpoint not initialized for job %s", self.job_name)
            return ReturnCode.ERROR

        self.current_checkpoint.phase = phase
        self.current_checkpoint.status = CheckpointStatus.ACTIVE
        self.current_checkpoint.records_processed = records_processed
        self.current_checkpoint.last_key = last_key
        self.current_checkpoint.timestamp = datetime.now().isoformat()
        if custom_data:
            self.current_checkpoint.custom_data.update(custom_data)

        logger.debug(
            "Checkpoint taken: phase=%s, records=%d, key=%s",
            phase.value, records_processed, last_key,
        )
        return ReturnCode.SUCCESS

    def commit_checkpoint(self) -> ReturnCode:
        """
        Commit (persist) the checkpoint to disk.

        Replaces: 3000-COMMIT-CHECKPOINT paragraph.
        """
        if self.current_checkpoint is None:
            return ReturnCode.ERROR

        try:
            data = {
                "job_name": self.current_checkpoint.job_name,
                "phase": self.current_checkpoint.phase.value,
                "status": self.current_checkpoint.status.value,
                "restart_mode": self.current_checkpoint.restart_mode.value,
                "records_processed": self.current_checkpoint.records_processed,
                "last_key": self.current_checkpoint.last_key,
                "timestamp": self.current_checkpoint.timestamp,
                "custom_data": self.current_checkpoint.custom_data,
            }
            self._checkpoint_path().write_text(json.dumps(data, indent=2))
            logger.info("Checkpoint committed for job %s", self.job_name)
            return ReturnCode.SUCCESS
        except OSError as exc:
            logger.error("Failed to commit checkpoint: %s", exc)
            return ReturnCode.ERROR

    def restart_from_checkpoint(self) -> tuple[CheckpointData | None, ReturnCode]:
        """
        Restart from last committed checkpoint.

        Replaces: 4000-RESTART-PROCESSING paragraph.
        """
        path = self._checkpoint_path()
        if not path.exists():
            logger.info("No checkpoint found for job %s, starting fresh", self.job_name)
            return None, ReturnCode.WARNING

        try:
            data = json.loads(path.read_text())
            self.current_checkpoint = CheckpointData(
                job_name=data["job_name"],
                phase=CheckpointPhase(data["phase"]),
                status=CheckpointStatus.RESTARTED,
                restart_mode=CheckpointRestartMode.RESTART,
                records_processed=data["records_processed"],
                last_key=data["last_key"],
                timestamp=data["timestamp"],
                custom_data=data.get("custom_data", {}),
            )
            logger.info(
                "Restarting job %s from phase=%s, records=%d, key=%s",
                self.job_name,
                self.current_checkpoint.phase.value,
                self.current_checkpoint.records_processed,
                self.current_checkpoint.last_key,
            )
            return self.current_checkpoint, ReturnCode.SUCCESS
        except (OSError, json.JSONDecodeError, KeyError) as exc:
            logger.error("Failed to read checkpoint: %s", exc)
            return None, ReturnCode.ERROR

    def clear_checkpoint(self) -> ReturnCode:
        """Remove checkpoint file after successful completion."""
        path = self._checkpoint_path()
        if path.exists():
            path.unlink()
            logger.info("Checkpoint cleared for job %s", self.job_name)
        return ReturnCode.SUCCESS
