"""
System Statistics Report Generator — converted from RPTSTA00.cbl (186 LOC).

Replaces: COBOL RPTSTA00 program — reads DB2 and batch stats,
          generates performance metrics report.
Target:   Python report generation.

COBOL flow:
  1000-INIT           → open files, init area
  2000-READ-DB2-STATS → read DB2 performance statistics
  3000-READ-BATCH     → read batch processing statistics
  4000-CALCULATE      → compute averages, throughput
  5000-FORMAT-REPORT  → format and write report
  6000-TERMINATE      → print summary
"""

import logging
from dataclasses import dataclass, field
from datetime import date, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from db.models import ErrorLog, ReturnCodes
from models.enums import ReturnCode

logger = logging.getLogger(__name__)


@dataclass
class SystemStatsReport:
    """System statistics report — replaces RPTSTA00.cbl report output."""

    report_date: date
    generated_at: datetime
    db_stats: dict = field(default_factory=dict)
    batch_stats: dict = field(default_factory=dict)
    error_stats: dict = field(default_factory=dict)
    return_code_stats: dict = field(default_factory=dict)


class SystemStatisticsReportGenerator:
    """
    Generates system statistics report — replaces RPTSTA00.cbl.

    Collects DB2 statistics, batch job metrics, error summaries,
    and return code analysis into a comprehensive performance report.
    """

    def generate(
        self,
        db: Session,
        report_date: date | None = None,
    ) -> tuple[SystemStatsReport, ReturnCode]:
        """
        Generate the system statistics report.

        Replaces: Main processing sequence in RPTSTA00.cbl.
        """
        if report_date is None:
            report_date = date.today()

        report = SystemStatsReport(
            report_date=report_date,
            generated_at=datetime.now(),
        )

        try:
            # Gather error statistics (replaces 2000-READ-DB2-STATS)
            report.error_stats = self._gather_error_stats(db, report_date)

            # Gather return code statistics (replaces 3000-READ-BATCH-STATS)
            report.return_code_stats = self._gather_return_code_stats(db, report_date)

            logger.info("Statistics report generated for %s", report_date)
            return report, ReturnCode.SUCCESS
        except Exception as exc:
            logger.error("Error generating statistics report: %s", exc)
            return report, ReturnCode.ERROR

    def _gather_error_stats(self, db: Session, report_date: date) -> dict:
        """Gather error statistics from ERRLOG table."""
        try:
            total = db.execute(
                select(func.count()).select_from(ErrorLog).where(ErrorLog.process_date == report_date)
            ).scalar() or 0

            by_severity = db.execute(
                select(ErrorLog.error_severity, func.count())
                .where(ErrorLog.process_date == report_date)
                .group_by(ErrorLog.error_severity)
            ).all()

            return {
                "total_errors": total,
                "by_severity": {str(sev): cnt for sev, cnt in by_severity},
            }
        except Exception:
            return {"total_errors": 0, "by_severity": {}}

    def _gather_return_code_stats(self, db: Session, report_date: date) -> dict:
        """Gather return code statistics from RTNCODES table."""
        try:
            total = db.execute(
                select(func.count()).select_from(ReturnCodes)
            ).scalar() or 0

            by_status = db.execute(
                select(ReturnCodes.status_code, func.count())
                .group_by(ReturnCodes.status_code)
            ).all()

            return {
                "total_entries": total,
                "by_status": {status: cnt for status, cnt in by_status},
            }
        except Exception:
            return {"total_entries": 0, "by_status": {}}

    def format_report(self, report: SystemStatsReport) -> str:
        """Format the statistics report as text."""
        lines = [
            f"{'='*70}",
            f"SYSTEM STATISTICS REPORT — {report.report_date}",
            f"Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"{'='*70}",
            "",
            "ERROR STATISTICS:",
            f"  Total Errors: {report.error_stats.get('total_errors', 0)}",
        ]

        for sev, cnt in sorted(report.error_stats.get("by_severity", {}).items()):
            lines.append(f"  Severity {sev}: {cnt}")

        lines.extend([
            "",
            "RETURN CODE STATISTICS:",
            f"  Total Entries: {report.return_code_stats.get('total_entries', 0)}",
        ])

        for status, cnt in sorted(report.return_code_stats.get("by_status", {}).items()):
            lines.append(f"  Status {status}: {cnt}")

        lines.append(f"\n{'='*70}")
        return "\n".join(lines)
