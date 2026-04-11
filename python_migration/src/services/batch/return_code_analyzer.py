"""
Return Code Analysis Utility — converted from RTNANA00.cbl (211 LOC).

Replaces: COBOL RTNANA00 program — analyzes return codes across the system,
          generates trend analysis report with DB2 cursor.
Target:   SQLAlchemy aggregate queries for return code analysis.

COBOL flow:
  1000-INIT        → open cursor on RTNCODES
  2000-FETCH-CODES → fetch return code records via cursor
  3000-ANALYZE     → accumulate statistics, detect trends
  4000-REPORT      → format and display analysis report
  5000-TERMINATE   → close cursor
"""

import logging
from dataclasses import dataclass, field
from datetime import date, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from db.models import ReturnCodes
from models.enums import ReturnCode

logger = logging.getLogger(__name__)


@dataclass
class ReturnCodeAnalysis:
    """Return code analysis results — replaces RTNANA00.cbl WS-ANALYSIS-AREA."""

    analysis_date: date
    generated_at: datetime
    total_records: int = 0
    by_program: dict[str, dict] = field(default_factory=dict)
    by_status: dict[str, int] = field(default_factory=dict)
    highest_code_seen: int = 0
    programs_with_errors: list[str] = field(default_factory=list)


class ReturnCodeAnalyzer:
    """
    Analyzes return codes — replaces RTNANA00.cbl.

    Reads from RTNCODES table using aggregate queries (replacing
    DB2 cursor-based row-by-row processing) to produce trend analysis.
    """

    def analyze(
        self,
        db: Session,
        analysis_date: date | None = None,
    ) -> tuple[ReturnCodeAnalysis, ReturnCode]:
        """
        Run return code analysis.

        Replaces: Main processing loop in RTNANA00.cbl (OPEN CURSOR / FETCH / CLOSE).
        """
        if analysis_date is None:
            analysis_date = date.today()

        result = ReturnCodeAnalysis(
            analysis_date=analysis_date,
            generated_at=datetime.now(),
        )

        try:
            # Total count
            result.total_records = db.execute(
                select(func.count()).select_from(ReturnCodes)
            ).scalar() or 0

            # By program (replaces cursor fetch loop with GROUP BY)
            by_program = db.execute(
                select(
                    ReturnCodes.program_id,
                    func.count().label("count"),
                    func.max(ReturnCodes.return_code).label("max_rc"),
                    func.max(ReturnCodes.highest_code).label("max_highest"),
                )
                .group_by(ReturnCodes.program_id)
            ).all()

            for pgm_id, count, max_rc, max_highest in by_program:
                result.by_program[pgm_id] = {
                    "count": count,
                    "max_return_code": max_rc,
                    "max_highest_code": max_highest,
                }
                if max_highest > result.highest_code_seen:
                    result.highest_code_seen = max_highest
                if max_highest > 4:
                    result.programs_with_errors.append(pgm_id)

            # By status (replaces status accumulation in FETCH loop)
            by_status = db.execute(
                select(ReturnCodes.status_code, func.count())
                .group_by(ReturnCodes.status_code)
            ).all()

            for status, count in by_status:
                result.by_status[status] = count

            logger.info("Return code analysis: %d records, %d programs",
                        result.total_records, len(result.by_program))
            return result, ReturnCode.SUCCESS

        except Exception as exc:
            logger.error("Return code analysis failed: %s", exc)
            return result, ReturnCode.ERROR

    def format_report(self, analysis: ReturnCodeAnalysis) -> str:
        """Format the analysis report as text."""
        lines = [
            f"{'='*70}",
            f"RETURN CODE ANALYSIS — {analysis.analysis_date}",
            f"Generated: {analysis.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"{'='*70}",
            f"Total Records: {analysis.total_records}",
            f"Highest Code Seen: {analysis.highest_code_seen}",
            "",
            "By Program:",
        ]

        for pgm_id, stats in sorted(analysis.by_program.items()):
            lines.append(
                f"  {pgm_id:<10} count={stats['count']:<6} "
                f"max_rc={stats['max_return_code']:<4} "
                f"max_highest={stats['max_highest_code']}"
            )

        lines.append("\nBy Status:")
        for status, count in sorted(analysis.by_status.items()):
            lines.append(f"  {status}: {count}")

        if analysis.programs_with_errors:
            lines.append(f"\nPrograms with Errors: {', '.join(analysis.programs_with_errors)}")

        lines.append(f"\n{'='*70}")
        return "\n".join(lines)
