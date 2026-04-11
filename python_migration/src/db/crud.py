"""
Generic CRUD operations — base repository pattern.

Replaces: Direct VSAM READ/WRITE/REWRITE/DELETE and DB2 SQL operations
          scattered across COBOL programs.
Pattern:  Follows the CRUDBase pattern from the reference health-care-management-system repo.
"""

from collections.abc import Sequence
from typing import Any, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from .base import Base

ModelType = TypeVar("ModelType", bound=Base)


class CRUDBase:
    """
    Generic CRUD operations for any SQLAlchemy model.

    Provides the standard operations that replace COBOL VSAM verbs:
      COBOL READ    → get / get_multi
      COBOL WRITE   → create
      COBOL REWRITE → update
      COBOL DELETE   → delete
    """

    def __init__(self, model: type[ModelType]) -> None:
        self.model = model

    def get(self, db: Session, **pk_values: Any) -> ModelType | None:
        """Read a single record by primary key(s). Replaces COBOL READ with KEY IS."""
        return db.get(self.model, pk_values if len(pk_values) > 1 else next(iter(pk_values.values())))

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: dict[str, Any] | None = None,
    ) -> Sequence[ModelType]:
        """Read multiple records with optional filters. Replaces COBOL READ NEXT."""
        stmt = select(self.model)
        if filters:
            for col_name, value in filters.items():
                stmt = stmt.where(getattr(self.model, col_name) == value)
        stmt = stmt.offset(skip).limit(limit)
        return db.execute(stmt).scalars().all()

    def create(self, db: Session, *, obj_in: dict[str, Any]) -> ModelType:
        """Create a new record. Replaces COBOL WRITE."""
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, *, db_obj: ModelType, obj_in: dict[str, Any]) -> ModelType:
        """Update an existing record. Replaces COBOL REWRITE."""
        for field, value in obj_in.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, *, db_obj: ModelType) -> ModelType:
        """Delete a record. Replaces COBOL DELETE."""
        db.delete(db_obj)
        db.commit()
        return db_obj
