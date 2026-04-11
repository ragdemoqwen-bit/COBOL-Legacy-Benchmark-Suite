"""
Data Validation Utility — converted from UTLVAL00.cbl (191 LOC).

Replaces: COBOL UTLVAL00 program — performs comprehensive data validation:
          integrity checks, cross-reference validation, format verification,
          balance reconciliation.
Target:   Python service with dispatch pattern for validation types.

COBOL flow:
  1000-INITIALIZE      → open files, init totals
  2000-PROCESS         → read validation control, dispatch
  2100-PROCESS-VALIDATION → EVALUATE VAL-TYPE
  2200-CHECK-INTEGRITY → check position and transaction integrity
  2300-CHECK-XREF      → cross-reference positions vs transactions
  2400-CHECK-FORMAT    → verify data formats
  2500-CHECK-BALANCE   → accumulate positions, verify balance totals
  3000-CLEANUP         → close files
"""

import logging
from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from db.models import InvestmentPosition, PortfolioMaster, TransactionHistory

logger = logging.getLogger(__name__)


class ValidationType(StrEnum):
    """Validation types — from UTLVAL00.cbl WS-VALIDATION-TYPES."""

    INTEGRITY = "INTEGRITY"
    XREF = "XREF"
    FORMAT = "FORMAT"
    BALANCE = "BALANCE"


@dataclass
class ValidationError:
    """A single validation error — replaces UTLVAL00.cbl WS-ERROR-LINE."""

    error_type: str
    key: str
    description: str


@dataclass
class ValidationResult:
    """Validation result — replaces UTLVAL00.cbl WS-VALIDATION-TOTALS."""

    records_read: int = 0
    records_valid: int = 0
    records_error: int = 0
    total_amount: Decimal = Decimal("0.00")
    control_total: Decimal = Decimal("0.00")
    errors: list[ValidationError] = field(default_factory=list)

    @property
    def is_balanced(self) -> bool:
        """Check if totals reconcile."""
        return self.total_amount == self.control_total


class DataValidatorService:
    """
    Data validation utility — replaces UTLVAL00.cbl.

    Dispatches validation types: integrity, cross-reference, format, balance.
    """

    def validate(
        self,
        db: Session,
        validation_types: list[str] | None = None,
    ) -> ValidationResult:
        """
        Run validation checks.

        Replaces: 2000-PROCESS loop reading VALIDATION-CONTROL.
        If validation_types is None, runs all checks.
        """
        result = ValidationResult()
        types_to_run = validation_types or [v.value for v in ValidationType]

        for val_type in types_to_run:
            val_type_upper = val_type.strip().upper()
            try:
                self._dispatch(db, val_type_upper, result)
            except ValueError as exc:
                result.records_error += 1
                result.errors.append(ValidationError(
                    error_type="DISPATCH",
                    key="",
                    description=str(exc),
                ))

        logger.info(
            "Validation complete: read=%d, valid=%d, errors=%d",
            result.records_read,
            result.records_valid,
            result.records_error,
        )
        return result

    def _dispatch(self, db: Session, val_type: str, result: ValidationResult) -> None:
        """
        Dispatch to correct validation function.

        Replaces: 2100-PROCESS-VALIDATION EVALUATE VAL-TYPE.
        """
        if val_type == ValidationType.INTEGRITY:
            self._check_integrity(db, result)
        elif val_type == ValidationType.XREF:
            self._check_xref(db, result)
        elif val_type == ValidationType.FORMAT:
            self._check_format(db, result)
        elif val_type == ValidationType.BALANCE:
            self._check_balance(db, result)
        else:
            raise ValueError(f"Invalid validation type: {val_type!r}")

    def _check_integrity(self, db: Session, result: ValidationResult) -> None:
        """
        Check data integrity.

        Replaces: 2200-CHECK-INTEGRITY → position and transaction integrity.
        Ensures all positions reference existing portfolios.
        """
        # Check positions reference valid portfolios
        orphan_positions = (
            db.execute(
                select(InvestmentPosition.portfolio_id, InvestmentPosition.investment_id)
                .outerjoin(PortfolioMaster, InvestmentPosition.portfolio_id == PortfolioMaster.portfolio_id)
                .where(PortfolioMaster.portfolio_id.is_(None))
            )
            .all()
        )

        for row in orphan_positions:
            result.records_read += 1
            result.records_error += 1
            result.errors.append(ValidationError(
                error_type="INTEGRITY",
                key=f"{row[0]}/{row[1]}",
                description="Orphan position — no matching portfolio",
            ))

        # Check transactions reference valid portfolios
        orphan_transactions = (
            db.execute(
                select(TransactionHistory.transaction_id, TransactionHistory.portfolio_id)
                .outerjoin(PortfolioMaster, TransactionHistory.portfolio_id == PortfolioMaster.portfolio_id)
                .where(PortfolioMaster.portfolio_id.is_(None))
            )
            .all()
        )

        for row in orphan_transactions:
            result.records_read += 1
            result.records_error += 1
            result.errors.append(ValidationError(
                error_type="INTEGRITY",
                key=f"{row[0]}",
                description=f"Orphan transaction — portfolio {row[1]} not found",
            ))

        if not orphan_positions and not orphan_transactions:
            result.records_valid += 1

    def _check_xref(self, db: Session, result: ValidationResult) -> None:
        """
        Cross-reference validation.

        Replaces: 2300-CHECK-XREF → position vs transaction cross-checks.
        """
        # Check every active position has at least one transaction
        positions = db.execute(
            select(InvestmentPosition.portfolio_id, InvestmentPosition.investment_id)
        ).all()

        for pos in positions:
            result.records_read += 1
            txn_count = db.execute(
                select(func.count())
                .select_from(TransactionHistory)
                .where(
                    TransactionHistory.portfolio_id == pos[0],
                    TransactionHistory.investment_id == pos[1],
                )
            ).scalar()

            if txn_count == 0:
                result.records_error += 1
                result.errors.append(ValidationError(
                    error_type="XREF",
                    key=f"{pos[0]}/{pos[1]}",
                    description="Position has no matching transactions",
                ))
            else:
                result.records_valid += 1

    def _check_format(self, db: Session, result: ValidationResult) -> None:
        """
        Format verification.

        Replaces: 2400-CHECK-FORMAT → position and transaction format checks.
        Validates field lengths and allowed values.
        """
        portfolios = db.execute(select(PortfolioMaster)).scalars().all()

        for port in portfolios:
            result.records_read += 1
            errors_found = False

            if not port.portfolio_id or len(port.portfolio_id.strip()) == 0:
                result.errors.append(ValidationError(
                    error_type="FORMAT",
                    key=port.portfolio_id,
                    description="Empty portfolio ID",
                ))
                errors_found = True

            if port.status not in ("A", "C", "S"):
                result.errors.append(ValidationError(
                    error_type="FORMAT",
                    key=port.portfolio_id,
                    description=f"Invalid status: {port.status!r}",
                ))
                errors_found = True

            if errors_found:
                result.records_error += 1
            else:
                result.records_valid += 1

    def _check_balance(self, db: Session, result: ValidationResult) -> None:
        """
        Balance reconciliation.

        Replaces: 2500-CHECK-BALANCE → accumulate positions, verify totals.
        Compares sum of position market values vs sum of transaction amounts.
        """
        # Sum of position market values
        position_total = db.execute(
            select(func.coalesce(func.sum(InvestmentPosition.market_value), 0))
        ).scalar()

        # Sum of transaction amounts
        transaction_total = db.execute(
            select(func.coalesce(func.sum(TransactionHistory.amount), 0))
        ).scalar()

        result.total_amount = Decimal(str(position_total))
        result.control_total = Decimal(str(transaction_total))
        result.records_read += 1

        if result.total_amount != result.control_total:
            diff = result.total_amount - result.control_total
            result.errors.append(ValidationError(
                error_type="BALANCE",
                key="SYSTEM",
                description=(
                    f"Balance mismatch: positions={result.total_amount}, "
                    f"transactions={result.control_total}, diff={diff}"
                ),
            ))
            result.records_error += 1
        else:
            result.records_valid += 1

    def format_report(self, result: ValidationResult) -> str:
        """Format validation result as a text report."""
        lines = [
            "=" * 70,
            "DATA VALIDATION REPORT",
            "=" * 70,
            "",
            f"Records read:    {result.records_read}",
            f"Records valid:   {result.records_valid}",
            f"Records in error:{result.records_error}",
            f"Position total:  {result.total_amount}",
            f"Control total:   {result.control_total}",
            f"Balanced:        {'YES' if result.is_balanced else 'NO'}",
            "",
        ]

        if result.errors:
            lines.append("ERRORS:")
            lines.append("-" * 50)
            for err in result.errors:
                lines.append(f"  [{err.error_type}] {err.key}: {err.description}")

        lines.append("")
        lines.append("=" * 70)
        return "\n".join(lines)
