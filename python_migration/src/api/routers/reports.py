"""
Reports API Router — converted from COBOL batch report programs.

Replaces:
  RPTPOS00.cbl (161 LOC) — Daily Position Report Generator
  RPTAUD00.cbl (148 LOC) — Audit Report Generator
  RPTSTA00.cbl (186 LOC) — System Statistics Report Generator
  RTNANA00.cbl (211 LOC) — Return Code Analysis Utility

Target: FastAPI REST endpoints for on-demand report generation.

In COBOL, these were batch JCL jobs producing spool output.
In Python, they become API endpoints returning JSON or formatted text.
"""

from datetime import date

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from db.base import get_db
from services.batch.report_audit import AuditReportGenerator
from services.batch.report_position import PositionReportGenerator
from services.batch.report_statistics import SystemStatisticsReportGenerator
from services.batch.return_code_analyzer import ReturnCodeAnalyzer

router = APIRouter(prefix="/reports", tags=["reports"])

_position_rpt = PositionReportGenerator()
_audit_rpt = AuditReportGenerator()
_stats_rpt = SystemStatisticsReportGenerator()
_rc_analyzer = ReturnCodeAnalyzer()


@router.get("/positions")
def position_report(
    report_date: date | None = Query(None),
    format: str = Query("json", regex="^(json|text)$"),
    db: Session = Depends(get_db),
):
    """
    Generate daily position report.

    Replaces: JCL job running RPTPOS00.
    """
    report, rc = _position_rpt.generate(db, report_date)
    if format == "text":
        return Response(
            content=_position_rpt.format_report(report),
            media_type="text/plain",
        )
    return {
        "report_date": str(report.report_date),
        "generated_at": report.generated_at.isoformat(),
        "record_count": report.record_count,
        "total_cost_basis": str(report.total_cost_basis),
        "total_market_value": str(report.total_market_value),
        "total_gain_loss": str(report.total_gain_loss),
        "positions": [
            {
                "portfolio_id": line.portfolio_id,
                "portfolio_name": line.portfolio_name,
                "investment_id": line.investment_id,
                "quantity": str(line.quantity),
                "cost_basis": str(line.cost_basis),
                "market_value": str(line.market_value),
                "gain_loss": str(line.gain_loss),
                "gain_loss_pct": str(line.gain_loss_pct),
            }
            for line in report.lines
        ],
    }


@router.get("/audit")
def audit_report(
    report_date: date | None = Query(None),
    format: str = Query("json", regex="^(json|text)$"),
    db: Session = Depends(get_db),
):
    """
    Generate audit report.

    Replaces: JCL job running RPTAUD00.
    """
    summary, rc = _audit_rpt.generate(db, report_date)
    if format == "text":
        return Response(
            content=_audit_rpt.format_report(summary),
            media_type="text/plain",
        )
    return {
        "report_date": str(summary.report_date),
        "generated_at": summary.generated_at.isoformat(),
        "total_errors": summary.total_errors,
        "errors_by_type": summary.errors_by_type,
        "errors_by_severity": summary.errors_by_severity,
        "errors_by_program": summary.errors_by_program,
    }


@router.get("/statistics")
def statistics_report(
    report_date: date | None = Query(None),
    format: str = Query("json", regex="^(json|text)$"),
    db: Session = Depends(get_db),
):
    """
    Generate system statistics report.

    Replaces: JCL job running RPTSTA00.
    """
    report, rc = _stats_rpt.generate(db, report_date)
    if format == "text":
        return Response(
            content=_stats_rpt.format_report(report),
            media_type="text/plain",
        )
    return {
        "report_date": str(report.report_date),
        "generated_at": report.generated_at.isoformat(),
        "error_stats": report.error_stats,
        "return_code_stats": report.return_code_stats,
    }


@router.get("/return-codes")
def return_code_analysis(
    analysis_date: date | None = Query(None),
    format: str = Query("json", regex="^(json|text)$"),
    db: Session = Depends(get_db),
):
    """
    Generate return code analysis report.

    Replaces: JCL job running RTNANA00.
    """
    analysis, rc = _rc_analyzer.analyze(db, analysis_date)
    if format == "text":
        return Response(
            content=_rc_analyzer.format_report(analysis),
            media_type="text/plain",
        )
    return {
        "analysis_date": str(analysis.analysis_date),
        "generated_at": analysis.generated_at.isoformat(),
        "total_records": analysis.total_records,
        "by_program": analysis.by_program,
        "by_status": analysis.by_status,
        "highest_code_seen": analysis.highest_code_seen,
        "programs_with_errors": analysis.programs_with_errors,
    }
