"""
DB2 Statistics Collector — converted from DB2STAT.cbl (229 LOC).

Replaces: COBOL DB2STAT program with INIT/UPDATE/TERMINATE/DISPLAY functions.
Target:   Python dataclass-based statistics tracking.

COBOL interface (LINKAGE SECTION):
  LS-STAT-FUNCTION    PIC X(4)  — 'INIT'/'UPDT'/'TERM'/'DISP'
  LS-STAT-RETURN-CODE PIC S9(4) COMP
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime

from models.enums import ReturnCode

logger = logging.getLogger(__name__)


@dataclass
class OperationMetric:
    """Single operation metric — replaces DB2STAT.cbl WS-STAT-RECORD."""

    operation: str
    count: int = 0
    total_elapsed_ms: float = 0.0
    min_elapsed_ms: float = float("inf")
    max_elapsed_ms: float = 0.0
    error_count: int = 0

    @property
    def avg_elapsed_ms(self) -> float:
        return self.total_elapsed_ms / self.count if self.count > 0 else 0.0


@dataclass
class DB2Statistics:
    """Full statistics collection — replaces DB2STAT.cbl WS-STAT-AREA."""

    start_time: datetime | None = None
    end_time: datetime | None = None
    total_operations: int = 0
    total_commits: int = 0
    total_rollbacks: int = 0
    total_errors: int = 0
    metrics: dict[str, OperationMetric] = field(default_factory=dict)


class DB2StatisticsCollector:
    """
    Collects and reports database operation statistics — replaces DB2STAT.cbl.

    COBOL EVALUATE TRUE dispatch:
      'INIT' → initialize()
      'UPDT' → update_stats()
      'TERM' → terminate()
      'DISP' → display_stats()
    """

    def __init__(self) -> None:
        self.stats = DB2Statistics()

    def initialize(self) -> ReturnCode:
        """
        Initialize statistics collection.

        Replaces: 1000-INIT-STATISTICS paragraph.
        """
        self.stats = DB2Statistics(start_time=datetime.now())
        logger.info("Statistics collection initialized")
        return ReturnCode.SUCCESS

    def update_stats(
        self,
        operation: str,
        elapsed_ms: float,
        is_error: bool = False,
    ) -> ReturnCode:
        """
        Update statistics for an operation.

        Replaces: 2000-UPDATE-STATISTICS paragraph.
        """
        if operation not in self.stats.metrics:
            self.stats.metrics[operation] = OperationMetric(operation=operation)

        metric = self.stats.metrics[operation]
        metric.count += 1
        metric.total_elapsed_ms += elapsed_ms
        metric.min_elapsed_ms = min(metric.min_elapsed_ms, elapsed_ms)
        metric.max_elapsed_ms = max(metric.max_elapsed_ms, elapsed_ms)

        self.stats.total_operations += 1
        if is_error:
            metric.error_count += 1
            self.stats.total_errors += 1

        return ReturnCode.SUCCESS

    def record_commit(self) -> None:
        """Track a commit operation."""
        self.stats.total_commits += 1

    def record_rollback(self) -> None:
        """Track a rollback operation."""
        self.stats.total_rollbacks += 1

    def terminate(self) -> ReturnCode:
        """
        Finalize statistics collection.

        Replaces: 3000-TERMINATE-STATISTICS paragraph.
        """
        self.stats.end_time = datetime.now()
        logger.info("Statistics collection terminated")
        return ReturnCode.SUCCESS

    def display_stats(self) -> tuple[dict, ReturnCode]:
        """
        Format and return statistics report.

        Replaces: 4000-DISPLAY-STATISTICS paragraph with DISPLAY statements.
        """
        elapsed = None
        if self.stats.start_time and self.stats.end_time:
            elapsed = (self.stats.end_time - self.stats.start_time).total_seconds()

        report = {
            "start_time": self.stats.start_time,
            "end_time": self.stats.end_time,
            "elapsed_seconds": elapsed,
            "total_operations": self.stats.total_operations,
            "total_commits": self.stats.total_commits,
            "total_rollbacks": self.stats.total_rollbacks,
            "total_errors": self.stats.total_errors,
            "operations": {},
        }

        for op_name, metric in self.stats.metrics.items():
            report["operations"][op_name] = {
                "count": metric.count,
                "avg_ms": round(metric.avg_elapsed_ms, 2),
                "min_ms": round(metric.min_elapsed_ms, 2) if metric.min_elapsed_ms != float("inf") else 0,
                "max_ms": round(metric.max_elapsed_ms, 2),
                "errors": metric.error_count,
            }

        return report, ReturnCode.SUCCESS
