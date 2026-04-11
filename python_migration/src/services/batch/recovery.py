"""
Process Recovery Handler — converted from RCVPRC00.cbl (303 LOC).

Replaces: COBOL RCVPRC00 program — handles process recovery with
          restart/bypass/terminate actions, sequence recovery.
Target:   Python recovery orchestration.

COBOL interface (LINKAGE SECTION):
  LS-RCV-FUNCTION    PIC X(4) — 'INIT'/'ANLZ'/'EXEC'/'STAT'
  LS-RCV-PROCESS-ID  PIC X(8)
  LS-RCV-ACTION      PIC X(1) — 'R'(restart)/'B'(bypass)/'T'(terminate)
"""

import logging
from dataclasses import dataclass
from datetime import datetime

from models.enums import BatchProcessStatus, ReturnCode

logger = logging.getLogger(__name__)


@dataclass
class RecoveryAction:
    """A recovery action record — replaces RCVPRC00.cbl WS-RECOVERY-RECORD."""

    process_id: str
    action: str  # R=restart, B=bypass, T=terminate
    reason: str
    timestamp: datetime
    original_status: BatchProcessStatus
    result: str = ""


class RecoveryHandler:
    """
    Handles process recovery — replaces RCVPRC00.cbl.

    COBOL EVALUATE TRUE dispatch:
      'INIT' → initialize()
      'ANLZ' → analyze_failure()
      'EXEC' → execute_recovery()
      'STAT' → get_recovery_status()
    """

    def __init__(self) -> None:
        self.recovery_log: list[RecoveryAction] = []

    def initialize(self) -> ReturnCode:
        """Initialize recovery processing — replaces 1000-INIT-RECOVERY."""
        self.recovery_log.clear()
        logger.info("Recovery handler initialized")
        return ReturnCode.SUCCESS

    def analyze_failure(
        self,
        process_id: str,
        error_code: int,
        error_message: str,
    ) -> tuple[str, ReturnCode]:
        """
        Analyze a failure and recommend recovery action.

        Replaces: 2000-ANALYZE-FAILURE paragraph.
        Returns recommended action: 'R'(restart), 'B'(bypass), 'T'(terminate).
        """
        # Decision logic (replaces EVALUATE error-code ranges)
        if error_code <= 4:
            action = "R"  # Restart — transient/warning error
            reason = f"Warning-level error ({error_code}): recommend restart"
        elif error_code <= 8:
            action = "B"  # Bypass — known recoverable error
            reason = f"Recoverable error ({error_code}): recommend bypass"
        else:
            action = "T"  # Terminate — severe error
            reason = f"Severe error ({error_code}): recommend terminate"

        logger.info("Failure analysis for %s: action=%s, reason=%s", process_id, action, reason)
        return action, ReturnCode.SUCCESS

    def execute_recovery(
        self,
        process_id: str,
        action: str,
        original_status: BatchProcessStatus,
        reason: str = "",
    ) -> ReturnCode:
        """
        Execute a recovery action.

        Replaces: 3000-EXECUTE-RECOVERY paragraph with EVALUATE WS-RCV-ACTION.
        """
        recovery = RecoveryAction(
            process_id=process_id,
            action=action,
            reason=reason,
            timestamp=datetime.now(),
            original_status=original_status,
        )

        if action == "R":
            recovery.result = "RESTARTED"
            logger.info("Process %s restarted", process_id)
        elif action == "B":
            recovery.result = "BYPASSED"
            logger.info("Process %s bypassed", process_id)
        elif action == "T":
            recovery.result = "TERMINATED"
            logger.info("Process %s terminated", process_id)
        else:
            logger.error("Invalid recovery action: %s", action)
            return ReturnCode.ERROR

        self.recovery_log.append(recovery)
        return ReturnCode.SUCCESS

    def get_recovery_status(self) -> tuple[dict, ReturnCode]:
        """
        Get recovery status report.

        Replaces: 4000-GET-STATUS paragraph.
        """
        action_counts: dict[str, int] = {"R": 0, "B": 0, "T": 0}
        for entry in self.recovery_log:
            action_counts[entry.action] = action_counts.get(entry.action, 0) + 1

        return {
            "total_recoveries": len(self.recovery_log),
            "restarts": action_counts["R"],
            "bypasses": action_counts["B"],
            "terminations": action_counts["T"],
            "log": [
                {
                    "process_id": r.process_id,
                    "action": r.action,
                    "result": r.result,
                    "reason": r.reason,
                    "timestamp": r.timestamp.isoformat(),
                }
                for r in self.recovery_log
            ],
        }, ReturnCode.SUCCESS
