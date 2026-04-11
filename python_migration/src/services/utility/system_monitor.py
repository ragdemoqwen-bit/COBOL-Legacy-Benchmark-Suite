"""
System Monitoring Utility — converted from UTLMON00.cbl (222 LOC).

Replaces: COBOL UTLMON00 program — monitors system health and performance:
          resource utilization, performance metrics, threshold monitoring, alerts.
Target:   Python service with threshold-based alerting.

COBOL flow:
  1000-INITIALIZE   → open files, read config, init
  2000-PROCESS      → collect metrics, check thresholds, log, alert
  2100-COLLECT-METRICS → gather CPU/memory/DASD/DB2 metrics
  2200-CHECK-THRESHOLDS → compare metrics vs configured thresholds
  2300-LOG-STATUS    → write to monitor log
  2400-GENERATE-ALERTS → write alerts if thresholds breached
  3000-CLEANUP       → close files
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

logger = logging.getLogger(__name__)


class ResourceType(StrEnum):
    """Resource types — from UTLMON00.cbl WS-RESOURCE-TYPES."""

    CPU = "CPU"
    MEMORY = "MEMORY"
    DASD = "DASD"
    DB2 = "DB2"


class ThresholdType(StrEnum):
    """Threshold types — from UTLMON00.cbl WS-THRESHOLD-TYPES."""

    UTILIZATION = "UTIL"
    RESPONSE = "RESPONSE"
    QUEUE = "QUEUE"
    ERROR = "ERROR"


class AlertLevel(StrEnum):
    """Alert levels — from UTLMON00.cbl WS-ALERT-LEVELS."""

    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


@dataclass
class ThresholdConfig:
    """Threshold configuration — replaces UTLMON00.cbl CONFIG-RECORD."""

    resource_type: str
    threshold_type: str
    threshold_value: Decimal
    alert_level: str
    alert_action: str = ""


@dataclass
class MetricReading:
    """A single metric reading — replaces UTLMON00.cbl LOG-RECORD."""

    timestamp: datetime
    resource_type: str
    metric_name: str
    metric_value: Decimal
    status: str = "OK"


@dataclass
class Alert:
    """An alert record — replaces UTLMON00.cbl ALERT-RECORD."""

    timestamp: datetime
    level: str
    resource: str
    message: str


@dataclass
class MonitoringResult:
    """Result of a monitoring cycle."""

    metrics: list[MetricReading] = field(default_factory=list)
    alerts: list[Alert] = field(default_factory=list)
    thresholds_breached: int = 0


class SystemMonitorService:
    """
    System monitoring utility — replaces UTLMON00.cbl.

    Collects metrics, checks thresholds, generates alerts.
    """

    def __init__(self, thresholds: list[ThresholdConfig] | None = None) -> None:
        self._thresholds = thresholds or []

    def configure(self, thresholds: list[ThresholdConfig]) -> None:
        """
        Load threshold configurations.

        Replaces: 1300-READ-CONFIG loop reading MONITOR-CONFIG.
        """
        self._thresholds = list(thresholds)
        logger.info("Loaded %d threshold configurations", len(self._thresholds))

    def check_metrics(self, metrics: dict[str, Decimal]) -> MonitoringResult:
        """
        Check current metrics against configured thresholds.

        Replaces: 2000-PROCESS → collect, check, log, alert.

        Args:
            metrics: dict mapping "RESOURCE.METRIC" → value
                     e.g. {"CPU.UTIL": Decimal("85.5"), "DB2.RESPONSE": Decimal("150")}
        """
        now = datetime.now()
        result = MonitoringResult()

        # Log all metrics (replaces 2300-LOG-STATUS)
        for key, value in metrics.items():
            parts = key.split(".", 1)
            resource = parts[0] if len(parts) > 0 else "UNKNOWN"
            metric_name = parts[1] if len(parts) > 1 else "VALUE"

            reading = MetricReading(
                timestamp=now,
                resource_type=resource,
                metric_name=metric_name,
                metric_value=value,
            )
            result.metrics.append(reading)

        # Check thresholds (replaces 2200-CHECK-THRESHOLDS)
        for threshold in self._thresholds:
            key = f"{threshold.resource_type}.{threshold.threshold_type}"
            if key in metrics:
                current = metrics[key]
                if current >= threshold.threshold_value:
                    result.thresholds_breached += 1
                    # Update metric status
                    for m in result.metrics:
                        if m.resource_type == threshold.resource_type and m.metric_name == threshold.threshold_type:
                            m.status = threshold.alert_level

                    # Generate alert (replaces 2400-GENERATE-ALERTS)
                    alert = Alert(
                        timestamp=now,
                        level=threshold.alert_level,
                        resource=threshold.resource_type,
                        message=(
                            f"{threshold.resource_type} {threshold.threshold_type} "
                            f"at {current} exceeds threshold {threshold.threshold_value}"
                        ),
                    )
                    result.alerts.append(alert)
                    logger.warning(
                        "Threshold breached: %s %s = %s (limit: %s)",
                        threshold.resource_type,
                        threshold.threshold_type,
                        current,
                        threshold.threshold_value,
                    )

        return result

    def format_status_report(self, result: MonitoringResult) -> str:
        """Format a status report from monitoring results."""
        lines = [
            "=" * 70,
            "SYSTEM MONITORING STATUS REPORT",
            "=" * 70,
            "",
            f"Metrics collected: {len(result.metrics)}",
            f"Thresholds breached: {result.thresholds_breached}",
            f"Alerts generated: {len(result.alerts)}",
            "",
        ]

        if result.metrics:
            lines.append("METRICS:")
            lines.append("-" * 50)
            for m in result.metrics:
                lines.append(
                    f"  {m.resource_type:<10} {m.metric_name:<12} "
                    f"{m.metric_value:>12} [{m.status}]"
                )

        if result.alerts:
            lines.append("")
            lines.append("ALERTS:")
            lines.append("-" * 50)
            for a in result.alerts:
                lines.append(f"  [{a.level}] {a.resource}: {a.message}")

        lines.append("")
        lines.append("=" * 70)
        return "\n".join(lines)
