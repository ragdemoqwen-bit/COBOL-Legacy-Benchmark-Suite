"""
Audit Report Generator — converted from RPTAUD00.cbl (148 LOC).

Replaces: COBOL RPTAUD00 program — reads audit and error files,
          generates comprehensive audit report.
Target:   Python report generation with SQLAlchemy queries.

COBOL flow:
  1000-INIT           → open files, init counters
  2000-READ-AUDIT     → read audit trail records
  3000-READ-ERRORS    → read error log records
  4000-FORMAT-REPORT  → format and write report lines
  5000-TERMINATE      → print summary, close files
"""

import logging
from dataclasses import dataclass, field
from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import ErrorLog
from models.enums import ReturnCode

logger = logging.getLogger(__name__)


@dataclass
class AuditReportSummary:
    """Audit report summary — replaces RPTAUD00.cbl report totals."""

    report_date: date
    generated_at: datetime
    total_errors: int = 0
    errors_by_type: dict[str, int] = field(default_factory=dict)
    errors_by_severity: dict[int, int] = field(default_factory=dict)
    errors_by_program: dict[str, int] = field(default_factory=dict)
    error_details: list[dict] = field(default_factory=list)


class AuditReportGenerator:
    """
    Generates audit report — replaces RPTAUD00.cbl.

    Reads error log data and generates a comprehensive audit report
    with breakdowns by type, severity, and program.
    """

    def generate(
        self,
        db: Session,
        report_date: date | None = None,
    ) -> tuple[AuditReportSummary, ReturnCode]:
        """
        Generate the audit report.

        Replaces: Main processing loop in RPTAUD00.cbl.
        """
        if report_date is None:
            report_date = date.today()

        summary = AuditReportSummary(
            report_date=report_date,
            generated_at=datetime.now(),
        )

        try:
            # Query error logs for the report date (replaces READ AUDIT-FILE / ERROR-FILE)
            stmt = (
                select(ErrorLog)
                .where(ErrorLog.process_date == report_date)
                .order_by(ErrorLog.error_timestamp)
            )
            errors = db.execute(stmt).scalars().all()

            for error in errors:
                summary.total_errors += 1

                # Count by type (replaces accumulation in 2000-READ-AUDIT)
                error_type = error.error_type
                summary.errors_by_type[error_type] = summary.errors_by_type.get(error_type, 0) + 1

                # Count by severity
                sev = error.error_severity
                summary.errors_by_severity[sev] = summary.errors_by_severity.get(sev, 0) + 1

                # Count by program
                pgm = error.program_id
                summary.errors_by_program[pgm] = summary.errors_by_program.get(pgm, 0) + 1

                # Capture detail
                summary.error_details.append({
                    "timestamp": str(error.error_timestamp),
                    "program": error.program_id,
                    "type": error.error_type,
                    "severity": error.error_severity,
                    "code": error.error_code,
                    "message": error.error_message,
                })

            logger.info("Audit report generated: %d errors for %s", summary.total_errors, report_date)
            return summary, ReturnCode.SUCCESS

        except Exception as exc:
            logger.error("Error generating audit report: %s", exc)
            return summary, ReturnCode.ERROR

    def format_report(self, summary: AuditReportSummary) -> str:
        """Format the audit report as text (replaces COBOL WRITE REPORT-LINE)."""
        lines = [
            f"{'='*70}",
            f"AUDIT REPORT — {summary.report_date}",
            f"Generated: {summary.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"{'='*70}",
            f"Total Errors: {summary.total_errors}",
            "",
            "Errors by Type:",
        ]
        for etype, count in sorted(summary.errors_by_type.items()):
            lines.append(f"  {etype}: {count}")

        lines.append("\nErrors by Severity:")
        for sev, count in sorted(summary.errors_by_severity.items()):
            lines.append(f"  Level {sev}: {count}")

        lines.append("\nErrors by Program:")
        for pgm, count in sorted(summary.errors_by_program.items()):
            lines.append(f"  {pgm}: {count}")

        lines.append(f"\n{'='*70}")
        return "\n".join(lines)
