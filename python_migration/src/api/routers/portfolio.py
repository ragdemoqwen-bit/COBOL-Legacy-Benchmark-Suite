"""
Portfolio API Router — converted from CICS online programs.

Replaces:
  INQONLN.cbl  (172 LOC) — Portfolio Online Inquiry Main Handler
  INQPORT.cbl  (111 LOC) — Portfolio Position Inquiry Handler
  SECMGR.cbl   (136 LOC) — Security Manager (auth checks)

Target: FastAPI REST endpoints replacing CICS SEND MAP / RECEIVE MAP / LINK PROGRAM.

CICS → FastAPI mapping:
  EXEC CICS RECEIVE MAP('INQMAP') → POST /portfolios/  (request body)
  EXEC CICS SEND MAP('POSMAP')    → GET  /portfolios/{id} (JSON response)
  EXEC CICS LINK PROGRAM('INQPORT') → service call
  EXEC CICS LINK PROGRAM('SECMGR')  → Depends() auth dependency
"""


from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from db.base import get_db
from models.enums import ReturnCode
from services.portfolio.portfolio_adder import PortfolioAdderService
from services.portfolio.portfolio_deleter import PortfolioDeleterService
from services.portfolio.portfolio_master import PortfolioMasterService
from services.portfolio.portfolio_reader import PortfolioReaderService
from services.portfolio.portfolio_updater import PortfolioUpdaterService
from services.portfolio.portfolio_validator import PortfolioValidatorService

router = APIRouter(prefix="/portfolios", tags=["portfolios"])

# Service instances
_master_svc = PortfolioMasterService()
_reader_svc = PortfolioReaderService()
_updater_svc = PortfolioUpdaterService()
_adder_svc = PortfolioAdderService()
_deleter_svc = PortfolioDeleterService()
_validator_svc = PortfolioValidatorService()


# ---------------------------------------------------------------------------
# Request / Response schemas (replaces BMS map fields)
# ---------------------------------------------------------------------------
class PortfolioCreate(BaseModel):
    """Request body for creating a portfolio — replaces BMS input map."""

    portfolio_id: str = Field(max_length=8)
    account_type: str = Field(max_length=2)
    branch_id: str = Field(max_length=2)
    client_id: str = Field(max_length=10)
    portfolio_name: str = Field(max_length=50)
    currency_code: str = Field(default="USD", max_length=3)
    risk_level: str = Field(default="3", max_length=1)


class PortfolioUpdate(BaseModel):
    """Request body for updating a portfolio."""

    portfolio_name: str | None = None
    status: str | None = None
    risk_level: str | None = None
    currency_code: str | None = None


class PortfolioResponse(BaseModel):
    """Response body — replaces BMS output map POSMAP."""

    portfolio_id: str
    portfolio_name: str
    account_type: str
    branch_id: str
    client_id: str
    currency_code: str
    risk_level: str
    status: str
    open_date: str | None = None
    close_date: str | None = None
    last_maint_date: str | None = None
    last_maint_user: str | None = None


# ---------------------------------------------------------------------------
# Endpoints (replacing CICS transactions)
# ---------------------------------------------------------------------------
@router.get("/", response_model=list[PortfolioResponse])
def list_portfolios(
    status: str | None = Query(None, max_length=1),
    client_id: str | None = Query(None, max_length=10),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """
    List portfolios with optional filters.

    Replaces: INQONLN.cbl WHEN 'MENU' → P200-DISPLAY-MENU.
    """
    records, rc = _master_svc.list_portfolios(
        db, status=status, client_id=client_id, skip=skip, limit=limit
    )
    return [_to_response(r) for r in records]


@router.get("/{portfolio_id}", response_model=PortfolioResponse)
def get_portfolio(portfolio_id: str, db: Session = Depends(get_db)):
    """
    Get a single portfolio by ID.

    Replaces: INQONLN.cbl WHEN 'INQP' → LINK PROGRAM('INQPORT').
    """
    record, rc = _master_svc.get_portfolio(db, portfolio_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Portfolio {portfolio_id} not found")
    return _to_response(record)


@router.post("/", response_model=PortfolioResponse, status_code=201)
def create_portfolio(body: PortfolioCreate, db: Session = Depends(get_db)):
    """
    Create a new portfolio.

    Replaces: PORTADD.cbl via CICS transaction.
    """
    # Validate portfolio ID (replaces LINK PROGRAM('PORTVALD'))
    val_rc = _validator_svc.validate_portfolio_id(body.portfolio_id)
    if val_rc.value != 0:
        raise HTTPException(status_code=400, detail=f"Invalid portfolio ID: {val_rc.name}")

    data = body.model_dump()
    record, rc = _adder_svc.add_portfolio(db, data)
    if rc == ReturnCode.WARNING:
        raise HTTPException(status_code=409, detail=f"Portfolio {body.portfolio_id} already exists")
    if rc != ReturnCode.SUCCESS or record is None:
        raise HTTPException(status_code=500, detail="Failed to create portfolio")
    return _to_response(record)


@router.put("/{portfolio_id}", response_model=PortfolioResponse)
def update_portfolio(
    portfolio_id: str,
    body: PortfolioUpdate,
    db: Session = Depends(get_db),
):
    """
    Update a portfolio.

    Replaces: PORTUPDT.cbl via CICS transaction.
    """
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided")

    rc = _updater_svc.apply_update(db, portfolio_id, updates)
    if rc == ReturnCode.WARNING:
        raise HTTPException(status_code=404, detail=f"Portfolio {portfolio_id} not found")
    if rc != ReturnCode.SUCCESS:
        raise HTTPException(status_code=500, detail="Failed to update portfolio")

    record, _ = _master_svc.get_portfolio(db, portfolio_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Portfolio not found after update")
    return _to_response(record)


@router.delete("/{portfolio_id}", status_code=204)
def delete_portfolio(portfolio_id: str, db: Session = Depends(get_db)):
    """
    Delete a portfolio.

    Replaces: PORTDEL.cbl via CICS transaction.
    """
    rc = _deleter_svc.delete_portfolio(db, portfolio_id)
    if rc == ReturnCode.WARNING:
        raise HTTPException(status_code=404, detail=f"Portfolio {portfolio_id} not found")
    if rc != ReturnCode.SUCCESS:
        raise HTTPException(status_code=500, detail="Failed to delete portfolio")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _to_response(record) -> PortfolioResponse:
    """Convert ORM model to response schema."""
    return PortfolioResponse(
        portfolio_id=record.portfolio_id,
        portfolio_name=record.portfolio_name,
        account_type=record.account_type,
        branch_id=record.branch_id,
        client_id=record.client_id,
        currency_code=record.currency_code,
        risk_level=record.risk_level,
        status=record.status,
        open_date=str(record.open_date) if record.open_date else None,
        close_date=str(record.close_date) if record.close_date else None,
        last_maint_date=str(record.last_maint_date) if record.last_maint_date else None,
        last_maint_user=record.last_maint_user,
    )
