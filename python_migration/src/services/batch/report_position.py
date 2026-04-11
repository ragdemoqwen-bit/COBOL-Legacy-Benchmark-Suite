"""
Daily Position Report Generator — converted from RPTPOS00.cbl (161 LOC).

Replaces: COBOL RPTPOS00 program — reads position master and transaction
          history, generates position report with calculations.
Target:   Python report generation with SQLAlchemy queries.

COBOL flow:
  1000-INIT        → open files, print headers
  2000-READ-POS    → read position master records
  3000-CALC-VALUES → compute market value, gain/loss
  4000-PRINT-LINE  → write report line
  5000-TERMINATE   → print totals, close files
"""

import logging
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import InvestmentPosition, PortfolioMaster
from models.enums import ReturnCode

logger = logging.getLogger(__name__)


@dataclass
class PositionReportLine:
    """A single report line — replaces RPTPOS00.cbl REPORT-LINE."""

    portfolio_id: str
    portfolio_name: str
    investment_id: str
    quantity: Decimal
    cost_basis: Decimal
    market_value: Decimal
    gain_loss: Decimal
    gain_loss_pct: Decimal


@dataclass
class PositionReport:
    """Complete position report — replaces RPTPOS00.cbl full report output."""

    report_date: date
    generated_at: datetime
    lines: list[PositionReportLine]
    total_cost_basis: Decimal = Decimal("0.00")
    total_market_value: Decimal = Decimal("0.00")
    total_gain_loss: Decimal = Decimal("0.00")
    record_count: int = 0


class PositionReportGenerator:
    """
    Generates daily position report — replaces RPTPOS00.cbl.

    Reads all active positions, calculates gain/loss,
    generates formatted report with totals.
    """

    def generate(
        self,
        db: Session,
        report_date: date | None = None,
    ) -> tuple[PositionReport, ReturnCode]:
        """
        Generate the position report.

        Replaces: Main loop — 1000-INIT through 5000-TERMINATE.
        """
        if report_date is None:
            report_date = date.today()

        report = PositionReport(
            report_date=report_date,
            generated_at=datetime.now(),
            lines=[],
        )

        try:
            # Query positions with portfolio info (replaces READ POSITION-FILE)
            stmt = (
                select(InvestmentPosition, PortfolioMaster)
                .join(PortfolioMaster, InvestmentPosition.portfolio_id == PortfolioMaster.portfolio_id)
                .where(InvestmentPosition.position_date <= report_date)
                .order_by(InvestmentPosition.portfolio_id, InvestmentPosition.investment_id)
            )
            results = db.execute(stmt).all()

            for position, portfolio in results:
                # Calculate gain/loss (replaces 3000-CALC-VALUES)
                gain_loss = position.market_value - position.cost_basis
                gain_loss_pct = (
                    (gain_loss / position.cost_basis * 100).quantize(Decimal("0.01"))
                    if position.cost_basis != 0
                    else Decimal("0.00")
                )

                line = PositionReportLine(
                    portfolio_id=position.portfolio_id,
                    portfolio_name=portfolio.portfolio_name,
                    investment_id=position.investment_id,
                    quantity=position.quantity,
                    cost_basis=position.cost_basis,
                    market_value=position.market_value,
                    gain_loss=gain_loss,
                    gain_loss_pct=gain_loss_pct,
                )
                report.lines.append(line)
                report.total_cost_basis += position.cost_basis
                report.total_market_value += position.market_value
                report.total_gain_loss += gain_loss
                report.record_count += 1

            logger.info("Position report generated: %d records", report.record_count)
            return report, ReturnCode.SUCCESS

        except Exception as exc:
            logger.error("Error generating position report: %s", exc)
            return report, ReturnCode.ERROR

    def format_report(self, report: PositionReport) -> str:
        """Format the report as a text string (replaces COBOL WRITE REPORT-LINE)."""
        lines = [
            f"{'='*80}",
            f"DAILY POSITION REPORT — {report.report_date}",
            f"Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"{'='*80}",
            f"{'Portfolio':<10} {'Name':<20} {'Invest':<12} {'Qty':>10} "
            f"{'Cost':>14} {'Market':>14} {'G/L':>14} {'G/L%':>8}",
            f"{'-'*80}",
        ]

        for line in report.lines:
            lines.append(
                f"{line.portfolio_id:<10} {line.portfolio_name:<20} {line.investment_id:<12} "
                f"{line.quantity:>10} {line.cost_basis:>14.2f} {line.market_value:>14.2f} "
                f"{line.gain_loss:>14.2f} {line.gain_loss_pct:>7.2f}%"
            )

        lines.extend([
            f"{'-'*80}",
            f"{'TOTALS':<44} {report.total_cost_basis:>14.2f} "
            f"{report.total_market_value:>14.2f} {report.total_gain_loss:>14.2f}",
            f"Records: {report.record_count}",
            f"{'='*80}",
        ])

        return "\n".join(lines)
