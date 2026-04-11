"""
Standard Return Code Handler — converted from RTNCDE00.cbl (142 LOC).

Replaces: COBOL RTNCDE00 program — manages return codes, logging,
          analysis with DB2 INSERT/SELECT.
Target:   Python return code management with DB persistence.

COBOL interface (LINKAGE SECTION):
  LS-RC-FUNCTION    PIC X(4) — 'INIT'/'SET '/'GET '/'LOG '/'ANLZ'
  LS-RC-PROGRAM-ID  PIC X(8)
  LS-RC-RETURN-CODE PIC S9(4) COMP
"""

import logging
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from db.repositories import return_codes_repo
from models.enums import ReturnCode, ReturnCodeStatus

logger = logging.getLogger(__name__)


@dataclass
class ReturnCodeState:
    """Current return code state for a program — replaces RTNCDE00.cbl WS-RC-AREA."""

    program_id: str
    current_code: ReturnCode = ReturnCode.SUCCESS
    highest_code: ReturnCode = ReturnCode.SUCCESS
    status: ReturnCodeStatus = ReturnCodeStatus.SUCCESS


class ReturnCodeHandler:
    """
    Manages return codes — replaces RTNCDE00.cbl.

    COBOL EVALUATE TRUE dispatch on LS-RC-FUNCTION:
      'INIT' → initialize()
      'SET'  → set_code()
      'GET'  → get_code()
      'LOG'  → log_code()
      'ANLZ' → analyze()
    """

    def __init__(self) -> None:
        self._states: dict[str, ReturnCodeState] = {}

    def initialize(self, program_id: str) -> ReturnCode:
        """
        Initialize return code tracking for a program.

        Replaces: 1000-INIT-RETURN-CODES paragraph.
        """
        self._states[program_id] = ReturnCodeState(program_id=program_id)
        logger.debug("Return codes initialized for %s", program_id)
        return ReturnCode.SUCCESS

    def set_code(self, program_id: str, code: ReturnCode) -> ReturnCode:
        """
        Set current return code, tracking highest.

        Replaces: 2000-SET-RETURN-CODE paragraph.
        """
        state = self._states.get(program_id)
        if state is None:
            self.initialize(program_id)
            state = self._states[program_id]

        state.current_code = code
        if code.value > state.highest_code.value:
            state.highest_code = code

        # Update status based on highest code (replaces EVALUATE)
        state.status = self._code_to_status(state.highest_code)
        return ReturnCode.SUCCESS

    def get_code(self, program_id: str) -> tuple[ReturnCodeState | None, ReturnCode]:
        """
        Get current return code state.

        Replaces: 3000-GET-RETURN-CODE paragraph.
        """
        state = self._states.get(program_id)
        if state is None:
            return None, ReturnCode.WARNING
        return state, ReturnCode.SUCCESS

    def log_code(self, program_id: str, db: Session, message: str = "") -> ReturnCode:
        """
        Log return code to database.

        Replaces: 4000-LOG-RETURN-CODE paragraph with INSERT INTO RTNCODES.
        """
        state = self._states.get(program_id)
        if state is None:
            return ReturnCode.WARNING

        try:
            now = datetime.now()
            return_codes_repo.create(
                db,
                obj_in={
                    "timestamp": now,
                    "program_id": program_id,
                    "return_code": state.current_code.value,
                    "highest_code": state.highest_code.value,
                    "status_code": state.status.value,
                    "message_text": message[:80] if message else None,
                },
            )
            logger.info("Return code logged: %s rc=%d", program_id, state.current_code.value)
            return ReturnCode.SUCCESS
        except SQLAlchemyError as exc:
            logger.error("Failed to log return code: %s", exc)
            return ReturnCode.ERROR

    def analyze(self, program_id: str) -> tuple[dict, ReturnCode]:
        """
        Analyze return code history.

        Replaces: 5000-ANALYZE-CODES paragraph.
        """
        state = self._states.get(program_id)
        if state is None:
            return {}, ReturnCode.WARNING

        return {
            "program_id": program_id,
            "current_code": state.current_code.value,
            "highest_code": state.highest_code.value,
            "status": state.status.value,
            "severity": "OK" if state.highest_code == ReturnCode.SUCCESS else
                        "WARNING" if state.highest_code == ReturnCode.WARNING else
                        "ERROR",
        }, ReturnCode.SUCCESS

    def _code_to_status(self, code: ReturnCode) -> ReturnCodeStatus:
        """Map return code to status (replaces EVALUATE in RTNCDE00)."""
        status_map = {
            ReturnCode.SUCCESS: ReturnCodeStatus.SUCCESS,
            ReturnCode.WARNING: ReturnCodeStatus.WARNING,
            ReturnCode.ERROR: ReturnCodeStatus.ERROR,
            ReturnCode.SEVERE: ReturnCodeStatus.SEVERE,
            ReturnCode.CRITICAL: ReturnCodeStatus.SEVERE,
        }
        return status_map.get(code, ReturnCodeStatus.ERROR)
