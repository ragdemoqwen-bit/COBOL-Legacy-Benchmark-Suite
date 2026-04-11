"""
Health Check and DB2 Online Status endpoints.

Replaces:
  DB2ONLN.cbl  (121 LOC) — Online DB2 Connection Manager (status check)
  ERRHNDL.cbl  (119 LOC) — Centralized Error Handler (error info endpoint)

Target: FastAPI health/status endpoints.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from db.base import get_db
from services.common.db_connection import DB2ConnectionManager

router = APIRouter(tags=["health"])

_conn_mgr = DB2ConnectionManager()


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint.

    Replaces: DB2ONLN.cbl P300-CHECK-STATUS (check if DB2 is reachable).
    """
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as exc:
        return {"status": "degraded", "database": "disconnected", "error": str(exc)}


@router.get("/status")
def system_status(db: Session = Depends(get_db)):
    """
    System status endpoint — provides connection pool and error stats.

    Replaces: DB2ONLN.cbl DB2-STATUS function + ERRHNDL.cbl error summary.
    """
    status_data, rc = _conn_mgr.get_status()
    return {
        "system": "Portfolio Management System",
        "version": "1.0.0",
        "migrated_from": "COBOL/DB2/CICS",
        "database": status_data,
    }
