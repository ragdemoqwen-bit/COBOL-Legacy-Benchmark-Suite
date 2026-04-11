"""
SQLAlchemy base configuration and session management.

Replaces: DB2 connection management from DBPROC.cpy (CONNECT-TO-DB2, DISCONNECT-FROM-DB2)
Target: PostgreSQL (replacing DB2/VSAM)
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# Default to SQLite for development; PostgreSQL for production
DATABASE_URL = "sqlite:///./portfolio_mgmt.db"


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all ORM models."""

    pass


engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency — yields a DB session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables. Call once at startup."""
    Base.metadata.create_all(bind=engine)
