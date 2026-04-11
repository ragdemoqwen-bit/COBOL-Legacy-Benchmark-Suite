"""
Foundation tests — validate all Pydantic models from copybook conversions.

Tests COMP-3 precision, enum validation, field constraints, and model construction.
"""

from decimal import Decimal

import pytest

from models.enums import (
    AuditAction,
    AuditStatus,
    AuditType,
    BatchProcessStatus,
    CheckpointPhase,
    CheckpointStatus,
    ClientType,
    CurrencyCode,
    ErrorAction,
    ErrorType,
    HistoryActionCode,
    HistoryRecordType,
    InquiryFunction,
    InvestmentType,
    OnlineErrorSeverity,
    PortfolioStatus,
    PositionStatus,
    ProcessSequenceType,
    ReturnCode,
    TransactionStatus,
    TransactionType,
    ValidationReturnCode,
)
from models.audit import AuditRecord
from models.batch_control import BatchControlConstants, BatchControlRecord
from models.checkpoint import CheckpointControl
from models.db_procedures import DB2ErrorHandling, SqlStatusCodes
from models.db_tables import ErrlogRecord, PoshistRecord
from models.error_handling import ErrorMessage, ReturnHandling, StandardErrorCode, VsamStatus
from models.history import HistoryRecord
from models.online import DB2RequestArea, InquiryCommunicationArea, OnlineErrorHandling
from models.portfolio import PortfolioRecord
from models.position import PositionRecord
from models.process_sequence import ProcessSequenceRecord, StandardSequences
from models.return_code import ReturnCodeArea
from models.transaction import TransactionRecord
from models.validation import VAL_ID_PREFIX, VAL_MAX_AMOUNT, VAL_MIN_AMOUNT, VALID_INVESTMENT_TYPES


# ===== ENUM TESTS =====


class TestEnums:
    """Verify all enums map correctly to COBOL copybook values."""

    def test_return_codes(self) -> None:
        assert ReturnCode.SUCCESS == 0
        assert ReturnCode.WARNING == 4
        assert ReturnCode.ERROR == 8
        assert ReturnCode.SEVERE == 12
        assert ReturnCode.CRITICAL == 16

    def test_validation_return_codes(self) -> None:
        assert ValidationReturnCode.SUCCESS == 0
        assert ValidationReturnCode.INVALID_ID == 1
        assert ValidationReturnCode.INVALID_AMT == 4

    def test_portfolio_status(self) -> None:
        assert PortfolioStatus.ACTIVE == "A"
        assert PortfolioStatus.CLOSED == "C"
        assert PortfolioStatus.SUSPENDED == "S"

    def test_client_type(self) -> None:
        assert ClientType.INDIVIDUAL == "I"
        assert ClientType.CORPORATE == "C"
        assert ClientType.TRUST == "T"

    def test_transaction_types(self) -> None:
        assert TransactionType.BUY == "BU"
        assert TransactionType.SELL == "SL"
        assert TransactionType.TRANSFER == "TR"
        assert TransactionType.FEE == "FE"

    def test_transaction_status(self) -> None:
        assert TransactionStatus.PENDING == "P"
        assert TransactionStatus.DONE == "D"
        assert TransactionStatus.FAILED == "F"
        assert TransactionStatus.REVERSED == "R"

    def test_history_types(self) -> None:
        assert HistoryRecordType.PORTFOLIO == "PT"
        assert HistoryRecordType.POSITION == "PS"
        assert HistoryRecordType.TRANSACTION == "TR"

    def test_history_actions(self) -> None:
        assert HistoryActionCode.ADD == "A"
        assert HistoryActionCode.CHANGE == "C"
        assert HistoryActionCode.DELETE == "D"

    def test_audit_enums(self) -> None:
        assert AuditType.TRANSACTION == "TRAN"
        assert AuditAction.CREATE == "CREATE"
        assert AuditStatus.SUCCESS == "SUCC"

    def test_batch_status(self) -> None:
        assert BatchProcessStatus.READY == "R"
        assert BatchProcessStatus.DONE == "D"
        assert BatchProcessStatus.ERROR == "E"

    def test_checkpoint_phases(self) -> None:
        assert CheckpointPhase.INIT == "00"
        assert CheckpointPhase.READ == "10"
        assert CheckpointPhase.TERMINATE == "40"

    def test_position_status(self) -> None:
        assert PositionStatus.ACTIVE == "A"
        assert PositionStatus.CLOSED == "C"
        assert PositionStatus.PENDING == "P"

    def test_inquiry_functions(self) -> None:
        assert InquiryFunction.MENU == "MENU"
        assert InquiryFunction.PORTFOLIO == "INQP"
        assert InquiryFunction.HISTORY == "INQH"
        assert InquiryFunction.EXIT == "EXIT"

    def test_investment_types(self) -> None:
        assert InvestmentType.STOCK == "STK"
        assert InvestmentType.BOND == "BND"
        assert InvestmentType.MONEY_MARKET == "MMF"
        assert InvestmentType.ETF == "ETF"

    def test_currency_codes(self) -> None:
        assert CurrencyCode.USD == "USD"
        assert CurrencyCode.EUR == "EUR"
        assert CurrencyCode.GBP == "GBP"
        assert CurrencyCode.JPY == "JPY"
        assert CurrencyCode.CAD == "CAD"

    def test_error_types(self) -> None:
        assert ErrorType.VALIDATION == "V"
        assert ErrorType.DATABASE == "D"
        assert ErrorType.SECURITY == "S"

    def test_error_actions(self) -> None:
        assert ErrorAction.CONTINUE == "C"
        assert ErrorAction.ABORT == "A"
        assert ErrorAction.RETRY == "R"


# ===== PORTFOLIO MODEL TESTS =====


class TestPortfolioRecord:
    """Tests for PORTFLIO.cpy → PortfolioRecord."""

    def test_valid_portfolio(self) -> None:
        p = PortfolioRecord(
            port_id="PORT0001",
            account_no="1234567890",
            client_name="Test Client",
            client_type=ClientType.INDIVIDUAL,
            create_date="20240320",
            last_maint="20240320",
            status=PortfolioStatus.ACTIVE,
            total_value=Decimal("1000000.50"),
            cash_balance=Decimal("50000.25"),
        )
        assert p.port_id == "PORT0001"
        assert p.total_value == Decimal("1000000.50")
        assert p.cash_balance == Decimal("50000.25")

    def test_comp3_max_boundary(self) -> None:
        """PIC S9(13)V99 max = 9999999999999.99"""
        p = PortfolioRecord(
            port_id="PORT0001",
            account_no="1234567890",
            client_name="Max Value",
            client_type=ClientType.CORPORATE,
            create_date="20240320",
            last_maint="20240320",
            status=PortfolioStatus.ACTIVE,
            total_value=Decimal("9999999999999.99"),
        )
        assert p.total_value == Decimal("9999999999999.99")

    def test_comp3_overflow_rejected(self) -> None:
        """One cent over max should fail."""
        with pytest.raises(ValueError):
            PortfolioRecord(
                port_id="PORT0001",
                account_no="1234567890",
                client_name="Overflow",
                client_type=ClientType.TRUST,
                create_date="20240320",
                last_maint="20240320",
                status=PortfolioStatus.ACTIVE,
                total_value=Decimal("10000000000000.00"),
            )

    def test_comp3_negative(self) -> None:
        """Negative values valid for S9(13)V99."""
        p = PortfolioRecord(
            port_id="PORT0002",
            account_no="9876543210",
            client_name="Negative",
            client_type=ClientType.INDIVIDUAL,
            create_date="20240320",
            last_maint="20240320",
            status=PortfolioStatus.CLOSED,
            total_value=Decimal("-500.00"),
            cash_balance=Decimal("-100.50"),
        )
        assert p.total_value == Decimal("-500.00")

    def test_comp3_quantization(self) -> None:
        """3+ decimal places quantized to 2."""
        p = PortfolioRecord(
            port_id="PORT0003",
            account_no="1111111111",
            client_name="Quantize",
            client_type=ClientType.INDIVIDUAL,
            create_date="20240320",
            last_maint="20240320",
            status=PortfolioStatus.ACTIVE,
            total_value=Decimal("100.999"),
        )
        assert p.total_value == Decimal("101.00")  # banker's rounding

    def test_nan_rejected(self) -> None:
        with pytest.raises(ValueError):
            PortfolioRecord(
                port_id="PORT0004",
                account_no="2222222222",
                client_name="NaN",
                client_type=ClientType.INDIVIDUAL,
                create_date="20240320",
                last_maint="20240320",
                status=PortfolioStatus.ACTIVE,
                total_value=Decimal("NaN"),
            )


# ===== POSITION MODEL TESTS =====


class TestPositionRecord:
    """Tests for POSREC.cpy → PositionRecord."""

    def test_valid_position(self) -> None:
        p = PositionRecord(
            portfolio_id="PORT0001",
            position_date="20240320",
            investment_id="AAPL000001",
            quantity=Decimal("100.5000"),
            cost_basis=Decimal("15075.00"),
            market_value=Decimal("17250.50"),
        )
        assert p.quantity == Decimal("100.5000")
        assert p.cost_basis == Decimal("15075.00")

    def test_quantity_4_decimal_precision(self) -> None:
        """PIC S9(11)V9(4) — 4 decimal places."""
        p = PositionRecord(
            portfolio_id="PORT0001",
            position_date="20240320",
            investment_id="BOND00001",
            quantity=Decimal("0.0001"),
        )
        assert p.quantity == Decimal("0.0001")


# ===== TRANSACTION MODEL TESTS =====


class TestTransactionRecord:
    """Tests for TRNREC.cpy → TransactionRecord."""

    def test_buy_transaction(self) -> None:
        t = TransactionRecord(
            transaction_date="20240320",
            transaction_time="143025",
            portfolio_id="PORT0001",
            sequence_no="000001",
            investment_id="AAPL000001",
            transaction_type=TransactionType.BUY,
            quantity=Decimal("50.0000"),
            price=Decimal("175.5000"),
            amount=Decimal("8775.00"),
        )
        assert t.transaction_type == TransactionType.BUY
        assert t.status == TransactionStatus.PENDING  # default

    def test_all_transaction_types_valid(self) -> None:
        for tt in TransactionType:
            t = TransactionRecord(
                transaction_date="20240320",
                transaction_time="143025",
                portfolio_id="PORT0001",
                sequence_no="000001",
                investment_id="AAPL000001",
                transaction_type=tt,
            )
            assert t.transaction_type == tt


# ===== HISTORY MODEL TESTS =====


class TestHistoryRecord:
    """Tests for HISTREC.cpy → HistoryRecord."""

    def test_valid_history(self) -> None:
        h = HistoryRecord(
            portfolio_id="PORT0001",
            history_date="20240320",
            history_time="143025",
            seq_no="0001",
            record_type=HistoryRecordType.PORTFOLIO,
            action_code=HistoryActionCode.ADD,
            before_image="",
            after_image="new portfolio created",
        )
        assert h.record_type == HistoryRecordType.PORTFOLIO


# ===== AUDIT MODEL TESTS =====


class TestAuditRecord:
    """Tests for AUDITLOG.cpy → AuditRecord."""

    def test_valid_audit(self) -> None:
        a = AuditRecord(
            timestamp="2024-03-20T14:30:25.123456",
            system_id="MAINFRM1",
            user_id="ADMIN01",
            program="PORTMSTR",
            audit_type=AuditType.TRANSACTION,
            action=AuditAction.CREATE,
            status=AuditStatus.SUCCESS,
            portfolio_id="PORT0001",
        )
        assert a.action == AuditAction.CREATE
        assert a.status == AuditStatus.SUCCESS


# ===== ERROR HANDLING MODEL TESTS =====


class TestErrorHandling:
    """Tests for ERRHAND.cpy + RETHND.cpy → ErrorMessage, ReturnHandling."""

    def test_error_message(self) -> None:
        e = ErrorMessage(
            program="PORTMSTR",
            category="VS",
            code="E004",
            severity=8,
            text="VSAM file error",
        )
        assert e.severity == 8

    def test_return_handling_defaults(self) -> None:
        rh = ReturnHandling()
        assert rh.return_code == ReturnCode.SUCCESS
        assert rh.actions.max_retries == 3

    def test_standard_error_codes(self) -> None:
        assert StandardErrorCode.INVALID_DATA == "E001"
        assert StandardErrorCode.NOT_FOUND == "E002"
        assert StandardErrorCode.TIMEOUT == "E010"

    def test_vsam_statuses(self) -> None:
        assert VsamStatus.SUCCESS == "00"
        assert VsamStatus.DUPLICATE_KEY == "22"
        assert VsamStatus.NOT_FOUND == "23"
        assert VsamStatus.END_OF_FILE == "10"


# ===== BATCH CONTROL TESTS =====


class TestBatchControl:
    """Tests for BCHCTL.cpy + BCHCON.cpy → BatchControlRecord."""

    def test_valid_batch_record(self) -> None:
        b = BatchControlRecord(
            job_name="TRNVAL00",
            process_date="20240320",
            sequence_no=1,
        )
        assert b.status == BatchProcessStatus.READY
        assert len(b.prereq_jobs) == 10

    def test_constants(self) -> None:
        assert BatchControlConstants.MAX_PREREQ == 10
        assert BatchControlConstants.MAX_RESTARTS == 3
        assert BatchControlConstants.WAIT_INTERVAL == 300
        assert BatchControlConstants.START_OF_DAY == "STARTDAY"


# ===== CHECKPOINT TESTS =====


class TestCheckpoint:
    """Tests for CKPRST.cpy → CheckpointControl."""

    def test_valid_checkpoint(self) -> None:
        c = CheckpointControl(
            program_id="HISTLD00",
            run_date="20240320",
            run_time="143025",
        )
        assert c.status == CheckpointStatus.INITIAL
        assert c.commit_freq == 1000
        assert c.max_errors == 100
        assert len(c.file_statuses) == 5


# ===== PROCESS SEQUENCE TESTS =====


class TestProcessSequence:
    """Tests for PRCSEQ.cpy → ProcessSequenceRecord."""

    def test_valid_sequence(self) -> None:
        ps = ProcessSequenceRecord(
            process_id="TRNVAL00",
            process_type=ProcessSequenceType.PROCESS,
        )
        assert ps.restartable is True
        assert ps.active_days == "YYYYYYY"

    def test_standard_sequences(self) -> None:
        assert StandardSequences.START_OF_DAY == ["INITDAY", "CKPCLR", "DATEVAL"]
        assert StandardSequences.MAIN_PROCESS == ["TRNVAL00", "POSUPD00", "HISTLD00"]
        assert StandardSequences.END_OF_DAY == ["RPTGEN00", "BCKLOD00", "ENDDAY"]


# ===== DB TABLE MODEL TESTS =====


class TestDBTableModels:
    """Tests for DBTBLS.cpy → PoshistRecord, ErrlogRecord."""

    def test_poshist_comp3_precision(self) -> None:
        """PH-QUANTITY S9(12)V9(3) → 3 decimal places."""
        ph = PoshistRecord(
            account_no="12345678",
            portfolio_id="PORT000001",
            trans_date="2024-03-20",
            trans_time="14:30:25",
            trans_type="BU",
            security_id="AAPL00000001",
            quantity=Decimal("100.500"),
            price=Decimal("175.250"),
            amount=Decimal("17575.00"),
            total_amount=Decimal("17575.00"),
            cost_basis=Decimal("17575.00"),
            gain_loss=Decimal("0.00"),
        )
        assert ph.quantity == Decimal("100.500")
        assert ph.price == Decimal("175.250")

    def test_errlog_record(self) -> None:
        from models.enums import ErrorLogSeverity, ErrorLogType

        el = ErrlogRecord(
            error_timestamp="2024-03-20T14:30:25.123456",
            program_id="PORTMSTR",
            error_type=ErrorLogType.APPLICATION,
            error_severity=ErrorLogSeverity.ERROR,
            error_code="E001",
            error_message="Invalid portfolio ID",
            process_date="2024-03-20",
            process_time="14:30:25",
            user_id="ADMIN01",
        )
        assert el.error_severity == ErrorLogSeverity.ERROR


# ===== ONLINE MODEL TESTS =====


class TestOnlineModels:
    """Tests for INQCOM.cpy, DB2REQ.cpy, ERRHND.cpy → online models."""

    def test_inquiry_communication(self) -> None:
        inq = InquiryCommunicationArea(
            function=InquiryFunction.PORTFOLIO,
            account_no="1234567890",
        )
        assert inq.function == InquiryFunction.PORTFOLIO

    def test_db2_request(self) -> None:
        from models.enums import DB2RequestType

        req = DB2RequestArea(request_type=DB2RequestType.CONNECT)
        assert req.response_code == 0

    def test_online_error(self) -> None:
        err = OnlineErrorHandling(
            program="INQONLN",
            severity=OnlineErrorSeverity.WARNING,
            message="Record not found",
        )
        assert err.severity == OnlineErrorSeverity.WARNING


# ===== DB PROCEDURES / SQL STATUS TESTS =====


class TestDBProcedures:
    """Tests for DBPROC.cpy + SQLCA.cpy → DB2ErrorHandling, SqlStatusCodes."""

    def test_db2_error_defaults(self) -> None:
        deh = DB2ErrorHandling()
        assert deh.max_retries == 3
        assert deh.retry_wait == 100

    def test_sql_status_codes(self) -> None:
        assert SqlStatusCodes.SUCCESS == "00000"
        assert SqlStatusCodes.NOT_FOUND == "02000"
        assert SqlStatusCodes.DUPLICATE_KEY == "23505"
        assert SqlStatusCodes.DEADLOCK == "40001"


# ===== VALIDATION CONSTANTS TESTS =====


class TestValidationConstants:
    """Tests for PORTVAL.cpy → validation constants."""

    def test_amount_range(self) -> None:
        assert VAL_MIN_AMOUNT == Decimal("-9999999999999.99")
        assert VAL_MAX_AMOUNT == Decimal("9999999999999.99")

    def test_id_prefix(self) -> None:
        assert VAL_ID_PREFIX == "PORT"

    def test_valid_investment_types(self) -> None:
        assert VALID_INVESTMENT_TYPES == frozenset({"STK", "BND", "MMF", "ETF"})
