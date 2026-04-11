"""
Constants and structures derived from DBPROC.cpy and SQLCA.cpy — DB2 Procedures.

COBOL sources:
  src/copybook/db2/DBPROC.cpy (64 LOC) — Standard DB2 procedures
  src/copybook/db2/SQLCA.cpy  (16 LOC) — SQL Communication Area status codes
"""

from pydantic import BaseModel, Field

from .enums import SqlStatusCode


class DB2ErrorHandling(BaseModel):
    """DB2-ERROR-HANDLING from DBPROC.cpy — SQL error handling state."""

    sqlcode_txt: str = Field(default="", max_length=6, description="PIC X(6)")
    state: str = Field(default="", max_length=5, description="PIC X(5)")
    error_text: str = Field(default="", max_length=70, description="PIC X(70)")
    save_status: str = Field(default="", max_length=5, description="PIC X(5)")
    retry_count: int = Field(default=0, description="PIC S9(4) COMP")
    max_retries: int = Field(default=3, description="PIC S9(4) COMP")
    retry_wait: int = Field(default=100, description="PIC S9(4) COMP — milliseconds")


# Target database name from DBPROC.cpy CONNECT statement
DB2_DATABASE_NAME = "POSMVP"


class SqlStatusCodes:
    """
    Named SQL status code constants from SQLCA.cpy.

    Maps COBOL SQL-STATUS-CODES 05-level names to SQLSTATE strings.
    """

    SUCCESS = SqlStatusCode.SUCCESS
    NOT_FOUND = SqlStatusCode.NOT_FOUND
    DUPLICATE_KEY = SqlStatusCode.DUPLICATE_KEY
    DEADLOCK = SqlStatusCode.DEADLOCK
    TIMEOUT = SqlStatusCode.TIMEOUT
    CONNECTION_ERROR = SqlStatusCode.CONNECTION_ERROR
    DB_ERROR = SqlStatusCode.DB_ERROR
