"""
FastAPI Application — replaces CICS online transaction processing layer.

This is the main entry point for the migrated portfolio management system.
It replaces the entire CICS online layer (8 programs) with a REST API.

CICS → FastAPI mapping:
  CICS Region      → FastAPI application
  CICS Transactions → API endpoints
  BMS Maps          → Pydantic request/response models
  COMMAREA           → Request body / path params
  CICS LINK          → Service function calls
"""

from api.db.base import init_db
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import batch, health, portfolio, reports, transactions

app = FastAPI(
    title="Portfolio Management System",
    description="Migrated from COBOL/DB2/CICS to Python/PostgreSQL/FastAPI",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers (each replaces a set of CICS programs)
app.include_router(health.router)
app.include_router(portfolio.router)
app.include_router(transactions.router)
app.include_router(reports.router)
app.include_router(batch.router)


@app.on_event("startup")
def startup_event():
    """Initialize database tables on startup."""
    init_db()
