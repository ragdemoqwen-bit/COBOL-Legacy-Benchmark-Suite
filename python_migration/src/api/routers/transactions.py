"""
Transaction API Router — converted from CICS online programs.

Replaces:
  PORTTRAN.cbl (318 LOC) — Portfolio Transaction Processing
  INQHIST.cbl  (194 LOC) — Transaction History Inquiry Handler

Target: FastAPI REST endpoints for transaction processing and history inquiry.

CICS → FastAPI mapping:
  EXEC CICS LINK PROGRAM('PORTTRAN') → POST /transactions/
  EXEC CICS LINK PROGRAM('INQHIST')  → GET  /transactions/history/{account}
  DB2 cursor HISTORY_CURSOR           → SQLAlchemy query with pagination
"""

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.base import get_db
from db.models import PositionHistory
from models.enums import ReturnCode, TransactionType
from services.portfolio.portfolio_transaction import PortfolioTransactionService

router = APIRouter(prefix="/transactions", tags=["transactions"])

_txn_svc = PortfolioTransactionService()


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------
class TransactionCreate(BaseModel):
    """Request body for creating a transaction."""

    transaction_id: str = Field(max_length=20)
    portfolio_id: str = Field(max_length=8)
    investment_id: str = Field(max_length=10)
    transaction_type: TransactionType
    quantity: Decimal = Field(gt=0)
    price: Decimal = Field(gt=0)
    currency_code: str = Field(default="USD", max_length=3)


class TransactionResponse(BaseModel):
    """Response body for a transaction."""

    transaction_id: str
    portfolio_id: str
    investment_id: str
    transaction_type: str
    quantity: str
    price: str
    amount: str
    status: str
    transaction_date: str


class HistoryEntry(BaseModel):
    """A single history entry — replaces INQHIST.cbl WS-HISTORY-ENTRY."""

    trans_date: str
    trans_type: str
    quantity: str
    price: str
    amount: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.post("/", response_model=TransactionResponse, status_code=201)
def create_transaction(body: TransactionCreate, db: Session = Depends(get_db)):
    """
    Process a new transaction.

    Replaces: PORTTRAN.cbl 2000-PROCESS-TRANSACTION.
    """
    record, rc = _txn_svc.process_transaction(
        db,
        transaction_id=body.transaction_id,
        portfolio_id=body.portfolio_id,
        investment_id=body.investment_id,
        transaction_type=body.transaction_type,
        quantity=body.quantity,
        price=body.price,
        currency_code=body.currency_code,
    )
    if rc == ReturnCode.WARNING:
        raise HTTPException(
            status_code=404,
            detail=f"Portfolio {body.portfolio_id} not found or not active",
        )
    if rc != ReturnCode.SUCCESS or record is None:
        raise HTTPException(status_code=500, detail="Transaction processing failed")

    return TransactionResponse(
        transaction_id=record.transaction_id,
        portfolio_id=record.portfolio_id,
        investment_id=record.investment_id,
        transaction_type=record.transaction_type,
        quantity=str(record.quantity),
        price=str(record.price),
        amount=str(record.amount),
        status=record.status,
        transaction_date=str(record.transaction_date),
    )


@router.get("/history/{account_no}", response_model=list[HistoryEntry])
def get_transaction_history(
    account_no: str,
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Get transaction history for an account.

    Replaces: INQHIST.cbl P200-GET-HISTORY with HISTORY_CURSOR.
    The COBOL program used a DB2 cursor to fetch up to 10 rows at a time;
    this endpoint uses a simple LIMIT query.
    """
    stmt = (
        select(PositionHistory)
        .where(PositionHistory.account_no == account_no)
        .order_by(PositionHistory.trans_date.desc())
        .limit(limit)
    )
    records = db.execute(stmt).scalars().all()

    return [
        HistoryEntry(
            trans_date=str(r.trans_date),
            trans_type=r.trans_type,
            quantity=str(r.quantity),
            price=str(r.price),
            amount=str(r.amount),
        )
        for r in records
    ]
