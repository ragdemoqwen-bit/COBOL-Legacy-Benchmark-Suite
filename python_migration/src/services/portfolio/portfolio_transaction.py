"""
Portfolio Transaction Processing — converted from PORTTRAN.cbl (318 LOC).

Replaces: COBOL PORTTRAN program — reads transaction file, validates against
          portfolio, updates positions, writes audit trail.
Target:   SQLAlchemy transaction processing with audit logging.

COBOL flow:
  1000-INIT        → open files, init counters
  2000-PROCESS     → read transaction, validate, update position
  3000-UPDATE-POS  → update investment positions
  4000-AUDIT       → write audit trail record
  5000-TERMINATE   → close files, report totals
"""

import logging
from datetime import datetime
from decimal import Decimal

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from db.models import TransactionHistory
from db.repositories import portfolio_repo, position_repo, transaction_repo
from models.enums import (
    AuditAction,
    ReturnCode,
    TransactionStatus,
    TransactionType,
)
from services.common.audit_processor import AuditProcessor, AuditRequest

logger = logging.getLogger(__name__)


class TransactionResult:
    """Result of processing a batch of transactions."""

    def __init__(self) -> None:
        self.processed: int = 0
        self.successful: int = 0
        self.failed: int = 0
        self.total_amount: Decimal = Decimal("0.00")


class PortfolioTransactionService:
    """
    Processes portfolio transactions — replaces PORTTRAN.cbl.

    COBOL 2000-PROCESS-TRANSACTION logic:
      1. Read transaction record
      2. Validate portfolio exists and is active
      3. Validate transaction fields
      4. Update investment position
      5. Write audit trail
    """

    def __init__(self) -> None:
        self.auditor = AuditProcessor()

    def process_transaction(
        self,
        db: Session,
        *,
        transaction_id: str,
        portfolio_id: str,
        investment_id: str,
        transaction_type: TransactionType,
        quantity: Decimal,
        price: Decimal,
        currency_code: str = "USD",
        user_id: str = "SYSTEM",
    ) -> tuple[TransactionHistory | None, ReturnCode]:
        """
        Process a single transaction.

        Replaces: 2000-PROCESS-TRANSACTION paragraph.
        """
        now = datetime.now()

        # Validate portfolio exists and is active (replaces 2100-VALIDATE-PORTFOLIO)
        portfolio = portfolio_repo.get(db, portfolio_id=portfolio_id)
        if portfolio is None:
            logger.warning("Transaction %s: portfolio %s not found", transaction_id, portfolio_id)
            return None, ReturnCode.WARNING
        if portfolio.status != "A":
            logger.warning("Transaction %s: portfolio %s not active", transaction_id, portfolio_id)
            return None, ReturnCode.WARNING

        # Calculate amount (replaces COMPUTE WS-TRANS-AMOUNT)
        amount = (quantity * price).quantize(Decimal("0.01"))

        try:
            # Create transaction record (replaces 2200-WRITE-TRANSACTION)
            trans_data = {
                "transaction_id": transaction_id,
                "portfolio_id": portfolio_id,
                "transaction_date": now.date(),
                "transaction_time": now.time(),
                "investment_id": investment_id,
                "transaction_type": transaction_type.value,
                "quantity": quantity,
                "price": price,
                "amount": amount,
                "currency_code": currency_code,
                "status": TransactionStatus.DONE.value,
                "process_date": now,
                "process_user": user_id,
            }
            trans_record = transaction_repo.create(db, obj_in=trans_data)

            # Update position (replaces 3000-UPDATE-POSITION)
            self._update_position(
                db,
                portfolio_id=portfolio_id,
                investment_id=investment_id,
                transaction_type=transaction_type,
                quantity=quantity,
                price=price,
                amount=amount,
                currency_code=currency_code,
                user_id=user_id,
            )

            # Write audit trail (replaces 4000-WRITE-AUDIT)
            self.auditor.write_audit(
                AuditRequest(
                    system_id="PORTTRAN",
                    user_id=user_id,
                    program="PORTTRAN",
                    action=AuditAction.CREATE,
                    portfolio_id=portfolio_id,
                    account_no=investment_id,
                    message=f"{transaction_type.value} {quantity} @ {price} = {amount}",
                )
            )

            logger.info("Transaction %s processed: %s", transaction_id, transaction_type.value)
            return trans_record, ReturnCode.SUCCESS

        except SQLAlchemyError as exc:
            db.rollback()
            logger.error("Transaction %s failed: %s", transaction_id, exc)
            return None, ReturnCode.ERROR

    def process_batch(
        self,
        db: Session,
        transactions: list[dict],
    ) -> tuple[TransactionResult, ReturnCode]:
        """
        Process a batch of transactions.

        Replaces: PORTTRAN.cbl main loop (PERFORM 2000-PROCESS-TRANSACTION
                  UNTIL END-OF-FILE).
        """
        result = TransactionResult()

        for txn in transactions:
            result.processed += 1
            try:
                trans_type = TransactionType(txn["transaction_type"])
            except (ValueError, KeyError):
                result.failed += 1
                continue

            record, rc = self.process_transaction(
                db,
                transaction_id=txn["transaction_id"],
                portfolio_id=txn["portfolio_id"],
                investment_id=txn["investment_id"],
                transaction_type=trans_type,
                quantity=Decimal(str(txn["quantity"])),
                price=Decimal(str(txn["price"])),
                currency_code=txn.get("currency_code", "USD"),
                user_id=txn.get("user_id", "SYSTEM"),
            )
            if rc == ReturnCode.SUCCESS:
                result.successful += 1
                result.total_amount += record.amount if record else Decimal("0.00")
            else:
                result.failed += 1

        logger.info(
            "Batch complete: %d processed, %d ok, %d failed",
            result.processed,
            result.successful,
            result.failed,
        )
        return result, ReturnCode.SUCCESS

    def _update_position(
        self,
        db: Session,
        *,
        portfolio_id: str,
        investment_id: str,
        transaction_type: TransactionType,
        quantity: Decimal,
        price: Decimal,
        amount: Decimal,
        currency_code: str,
        user_id: str,
    ) -> None:
        """
        Update investment position based on transaction.

        Replaces: 3000-UPDATE-POSITION paragraph.
        BUY  → add quantity, update cost basis
        SELL → subtract quantity, update market value
        """
        now = datetime.now()
        existing = position_repo.get(
            db,
            portfolio_id=portfolio_id,
            investment_id=investment_id,
            position_date=now.date(),
        )

        if existing is not None:
            new_qty = existing.quantity
            new_cost = existing.cost_basis
            new_market = existing.market_value

            if transaction_type == TransactionType.BUY:
                new_qty += quantity
                new_cost += amount
            elif transaction_type == TransactionType.SELL:
                new_qty -= quantity
                new_market -= amount

            position_repo.update(
                db,
                db_obj=existing,
                obj_in={
                    "quantity": new_qty,
                    "cost_basis": new_cost,
                    "market_value": new_market,
                    "last_maint_date": now,
                    "last_maint_user": user_id,
                },
            )
        else:
            # Create new position
            position_repo.create(
                db,
                obj_in={
                    "portfolio_id": portfolio_id,
                    "investment_id": investment_id,
                    "position_date": now.date(),
                    "quantity": quantity,
                    "cost_basis": amount if transaction_type == TransactionType.BUY else Decimal("0.00"),
                    "market_value": amount,
                    "currency_code": currency_code,
                    "last_maint_date": now,
                    "last_maint_user": user_id,
                },
            )
