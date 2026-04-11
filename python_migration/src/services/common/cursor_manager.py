"""
Cursor Management — converted from CURSMGR.cbl (92 LOC).

Replaces: COBOL CURSMGR program — manages DB2 cursor lifecycle:
          declare, open, fetch (with array fetch optimization), close.
Target:   SQLAlchemy query pagination / streaming pattern.

COBOL flow (EVALUATE TRUE on CURS-REQUEST-TYPE):
  P100-DECLARE-CURSOR → declare cursor with optional array fetch
  P200-OPEN-CURSOR    → open cursor, reset fetch stats
  P300-FETCH-DATA     → fetch rows (single or array)
  P400-CLOSE-CURSOR   → close cursor

In Python/SQLAlchemy, cursors become query objects with pagination.
"""

import logging
from collections.abc import Generator, Sequence
from typing import Any, TypeVar

from sqlalchemy import Select
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Default array fetch size — from CURSMGR.cbl WS-MAX-ROWS
DEFAULT_FETCH_SIZE = 20


class CursorStats:
    """Cursor statistics — replaces CURSMGR.cbl WS-CURSOR-STATS."""

    def __init__(self) -> None:
        self.fetch_count: int = 0
        self.rows_fetched: int = 0


class CursorManager:
    """
    Cursor management service — replaces CURSMGR.cbl.

    In Python/SQLAlchemy, DB2 cursors map to:
      DECLARE CURSOR → build a Select statement
      OPEN CURSOR    → execute the query
      FETCH          → iterate results (with optional batch size)
      CLOSE CURSOR   → session cleanup (automatic in SQLAlchemy)

    This service provides a streaming/pagination interface over SQLAlchemy queries.
    """

    def __init__(self, fetch_size: int = DEFAULT_FETCH_SIZE) -> None:
        self._fetch_size = fetch_size
        self._stats = CursorStats()

    @property
    def stats(self) -> CursorStats:
        """Get current cursor statistics."""
        return self._stats

    def fetch_all(self, db: Session, stmt: Select) -> Sequence[Any]:
        """
        Execute query and fetch all results.

        Replaces: OPEN + FETCH loop + CLOSE with single-row fetch.
        """
        self._stats = CursorStats()
        results = db.execute(stmt).scalars().all()
        self._stats.fetch_count = 1
        self._stats.rows_fetched = len(results)
        logger.debug("Fetched %d rows in %d fetches", self._stats.rows_fetched, self._stats.fetch_count)
        return results

    def fetch_paginated(
        self,
        db: Session,
        stmt: Select,
        *,
        offset: int = 0,
        limit: int | None = None,
    ) -> Sequence[Any]:
        """
        Execute query with pagination.

        Replaces: OPEN CURSOR + FETCH with array fetch optimization.
        Uses OFFSET/LIMIT instead of DB2 cursor positioning.
        """
        self._stats = CursorStats()
        page_size = limit or self._fetch_size
        paginated = stmt.offset(offset).limit(page_size)
        results = db.execute(paginated).scalars().all()
        self._stats.fetch_count = 1
        self._stats.rows_fetched = len(results)
        return results

    def fetch_streaming(
        self,
        db: Session,
        stmt: Select,
    ) -> Generator[Any, None, None]:
        """
        Stream results in batches.

        Replaces: OPEN CURSOR + repeated FETCH (array fetch) + CLOSE.
        Yields individual rows, fetching in batches of fetch_size.
        """
        self._stats = CursorStats()
        offset = 0

        while True:
            paginated = stmt.offset(offset).limit(self._fetch_size)
            batch = db.execute(paginated).scalars().all()
            self._stats.fetch_count += 1

            if not batch:
                break

            for row in batch:
                self._stats.rows_fetched += 1
                yield row

            if len(batch) < self._fetch_size:
                break

            offset += self._fetch_size

        logger.debug(
            "Streaming complete: %d rows in %d fetches",
            self._stats.rows_fetched,
            self._stats.fetch_count,
        )
