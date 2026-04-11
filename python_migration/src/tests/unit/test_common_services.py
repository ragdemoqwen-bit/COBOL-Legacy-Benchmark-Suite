"""
Tests for Wave 1 Common/DB Layer services + Wave 3 cursor_manager, db_recovery.
"""

from unittest.mock import MagicMock

from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session

from models.enums import (
    AuditAction,
    AuditStatus,
    AuditType,
    ErrorCategory,
    ErrorLogSeverity,
    ReturnCode,
)
from services.common.audit_processor import AuditProcessor, AuditRequest
from services.common.cursor_manager import CursorManager
from services.common.db_commit import DB2CommitController
from services.common.db_connection import DB2ConnectionManager
from services.common.db_error import DB2ErrorHandler
from services.common.db_recovery import DBRecoveryService, RecoveryStatus
from services.common.db_statistics import DB2StatisticsCollector
from services.common.error_processor import ErrorProcessor, ErrorRequest


class TestDB2ConnectionManager:
    def test_connect_returns_session_and_rc(self) -> None:
        mgr = DB2ConnectionManager()
        session, rc = mgr.connect()
        assert rc == ReturnCode.SUCCESS
        assert session is not None
        session.close()

    def test_disconnect_success(self) -> None:
        mgr = DB2ConnectionManager()
        session, _ = mgr.connect()
        rc = mgr.disconnect(session)
        assert rc == ReturnCode.SUCCESS
        assert mgr.stats.disconnect_count == 1

    def test_get_status(self) -> None:
        mgr = DB2ConnectionManager()
        status, rc = mgr.get_status()
        assert rc == ReturnCode.SUCCESS
        assert status["connected"] is True


class TestDB2CommitController:
    def test_commit_success(self) -> None:
        mock_db = MagicMock(spec=Session)
        ctrl = DB2CommitController()
        rc = ctrl.commit(mock_db)
        mock_db.commit.assert_called_once()
        assert rc == ReturnCode.SUCCESS

    def test_commit_failure(self) -> None:
        mock_db = MagicMock(spec=Session)
        mock_db.commit.side_effect = SQLAlchemyError("fail")
        ctrl = DB2CommitController()
        rc = ctrl.commit(mock_db)
        assert rc == ReturnCode.ERROR

    def test_rollback_success(self) -> None:
        mock_db = MagicMock(spec=Session)
        ctrl = DB2CommitController()
        rc = ctrl.rollback(mock_db)
        assert rc == ReturnCode.SUCCESS

    def test_initialize_resets_stats(self) -> None:
        ctrl = DB2CommitController()
        mock_db = MagicMock(spec=Session)
        ctrl.commit(mock_db)
        ctrl.initialize(mock_db)
        assert ctrl.stats.commit_count == 0

    def test_restore_missing_savepoint(self) -> None:
        ctrl = DB2CommitController()
        mock_db = MagicMock(spec=Session)
        rc = ctrl.restore(mock_db, "nonexistent")
        assert rc == ReturnCode.WARNING


class TestDB2ErrorHandler:
    def test_log_error(self) -> None:
        handler = DB2ErrorHandler()
        exc = OperationalError("test", {}, Exception("conn lost"))
        rc = handler.log_error(exc, program_id="TESTPROG")
        assert rc == ReturnCode.SUCCESS
        assert handler.stats.total_errors == 1

    def test_categorize_integrity_error(self) -> None:
        handler = DB2ErrorHandler()
        exc = IntegrityError("dup", {}, Exception("duplicate key"))
        handler.log_error(exc, program_id="TESTPROG")
        assert handler.stats.validation_errors == 1

    def test_diagnose_error(self) -> None:
        handler = DB2ErrorHandler()
        exc = OperationalError("test", {}, Exception("deadlock"))
        diagnosis, rc = handler.diagnose_error(exc)
        assert rc == ReturnCode.SUCCESS
        assert diagnosis["recoverable"] is True

    def test_retrieve_errors_filtered(self) -> None:
        handler = DB2ErrorHandler()
        exc1 = OperationalError("test", {}, Exception("err1"))
        exc2 = IntegrityError("test", {}, Exception("err2"))
        handler.log_error(exc1, program_id="PROG1")
        handler.log_error(exc2, program_id="PROG2")
        results, rc = handler.retrieve_errors(program_id="PROG1")
        assert len(results) == 1


class TestDB2StatisticsCollector:
    def test_initialize(self) -> None:
        collector = DB2StatisticsCollector()
        rc = collector.initialize()
        assert rc == ReturnCode.SUCCESS

    def test_update_stats(self) -> None:
        collector = DB2StatisticsCollector()
        rc = collector.update_stats("SELECT", 50.0)
        assert rc == ReturnCode.SUCCESS
        assert collector.stats.total_operations == 1

    def test_display_stats(self) -> None:
        collector = DB2StatisticsCollector()
        collector.initialize()
        collector.update_stats("SELECT", 25.0)
        collector.update_stats("SELECT", 75.0)
        collector.terminate()
        report, rc = collector.display_stats()
        assert rc == ReturnCode.SUCCESS
        assert report["total_operations"] == 2


class TestErrorProcessor:
    def test_process_error_no_db(self) -> None:
        proc = ErrorProcessor()
        req = ErrorRequest(
            program_id="PORTMSTR",
            category=ErrorCategory.VALIDATION,
            error_code="E001",
            severity=ErrorLogSeverity.ERROR,
            error_text="Invalid data",
        )
        rc = proc.process_error(req)
        assert rc == ReturnCode.SUCCESS


class TestAuditProcessor:
    def test_write_audit(self) -> None:
        proc = AuditProcessor()
        req = AuditRequest(
            system_id="SYS01",
            user_id="ADMIN01",
            program="PORTMSTR",
            audit_type=AuditType.TRANSACTION,
            action=AuditAction.CREATE,
            status=AuditStatus.SUCCESS,
            portfolio_id="PORT0001",
        )
        rc = proc.write_audit(req)
        assert rc == ReturnCode.SUCCESS
        assert proc.audit_count == 1

    def test_get_stats(self) -> None:
        proc = AuditProcessor()
        stats = proc.get_stats()
        assert stats["audit_records_written"] == 0


class TestCursorManager:
    def test_init_default_fetch_size(self) -> None:
        mgr = CursorManager()
        assert mgr._fetch_size == 20

    def test_custom_fetch_size(self) -> None:
        mgr = CursorManager(fetch_size=50)
        assert mgr._fetch_size == 50

    def test_stats_initialized(self) -> None:
        mgr = CursorManager()
        assert mgr.stats.fetch_count == 0
        assert mgr.stats.rows_fetched == 0


class TestDBRecoveryService:
    def test_recover_transaction_success(self) -> None:
        svc = DBRecoveryService()
        mock_db = MagicMock(spec=Session)
        result = svc.recover_transaction(mock_db)
        assert result.status == RecoveryStatus.SUCCESS
        mock_db.rollback.assert_called_once()

    def test_recover_transaction_failure(self) -> None:
        svc = DBRecoveryService()
        mock_db = MagicMock(spec=Session)
        mock_db.rollback.side_effect = SQLAlchemyError("rollback failed")
        result = svc.recover_transaction(mock_db)
        assert result.status == RecoveryStatus.FAILED

    def test_recover_cursor_non_fatal(self) -> None:
        svc = DBRecoveryService()
        result = svc.recover_cursor("TESTPROG", "CURSOR1", 100)
        assert result.status == RecoveryStatus.RETRY

    def test_recover_cursor_fatal(self) -> None:
        svc = DBRecoveryService()
        result = svc.recover_cursor("TESTPROG", "CURSOR1", -911)
        assert result.status == RecoveryStatus.FAILED

    def test_dispatch_transaction(self) -> None:
        svc = DBRecoveryService()
        mock_db = MagicMock(spec=Session)
        result = svc.dispatch("T", db=mock_db)
        assert result.status == RecoveryStatus.SUCCESS

    def test_dispatch_unknown_type(self) -> None:
        svc = DBRecoveryService()
        result = svc.dispatch("X")
        assert result.status == RecoveryStatus.FAILED
