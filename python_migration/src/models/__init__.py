"""
Pydantic models converted from all 17 COBOL copybooks + DB2/VSAM definitions.

Copybook → Model mapping:
  PORTFLIO.cpy → portfolio.PortfolioRecord
  PORTVAL.cpy  → validation (constants)
  POSREC.cpy   → position.PositionRecord
  HISTREC.cpy  → history.HistoryRecord
  TRNREC.cpy   → transaction.TransactionRecord
  COMMON.cpy   → enums (ReturnCode, StatusCode, TransactionType, CurrencyCode, ...)
  RETHND.cpy   → error_handling.ReturnHandling
  AUDITLOG.cpy → audit.AuditRecord
  ERRHAND.cpy  → error_handling.ErrorMessage
  RTNCODE.cpy  → return_code.ReturnCodeArea
  BCHCON.cpy   → batch_control.BatchControlConstants
  BCHCTL.cpy   → batch_control.BatchControlRecord
  CKPRST.cpy   → checkpoint.CheckpointControl
  PRCSEQ.cpy   → process_sequence.ProcessSequenceRecord
  DBTBLS.cpy   → db_tables.PoshistRecord, ErrlogRecord
  DBPROC.cpy   → db_procedures.DB2ErrorHandling
  SQLCA.cpy    → db_procedures.SqlStatusCodes
  INQCOM.cpy   → online.InquiryCommunicationArea
  DB2REQ.cpy   → online.DB2RequestArea
  ERRHND.cpy   → online.OnlineErrorHandling
"""

from .audit import AuditRecord
from .batch_control import BatchControlConstants, BatchControlRecord, PrerequisiteJob
from .checkpoint import CheckpointControl, CheckpointFileStatus, CheckpointRecord
from .db_procedures import DB2ErrorHandling, SqlStatusCodes
from .db_tables import ErrlogRecord, PoshistRecord
from .enums import (
    AuditAction,
    AuditStatus,
    AuditType,
    BatchDependencyType,
    BatchProcessStatus,
    BatchProcessType,
    BatchRecordType,
    CheckpointPhase,
    CheckpointRestartMode,
    CheckpointStatus,
    ClientType,
    CurrencyCode,
    DB2RequestType,
    ErrorAction,
    ErrorCategory,
    ErrorLogSeverity,
    ErrorLogType,
    ErrorType,
    HistoryActionCode,
    HistoryRecordType,
    InquiryFunction,
    InvestmentType,
    OnlineErrorAction,
    OnlineErrorSeverity,
    PortfolioStatus,
    PositionStatus,
    ProcessDependencyType,
    ProcessFrequency,
    ProcessSequenceType,
    ReturnCode,
    ReturnCodeRequestType,
    ReturnCodeStatus,
    SqlStatusCode,
    StatusCode,
    TransactionStatus,
    TransactionType,
    ValidationReturnCode,
)
from .error_handling import (
    ErrorInfo,
    ErrorLocation,
    ErrorMessage,
    ReturnActions,
    ReturnHandling,
    StandardErrorCode,
    SystemInfo,
    VsamStatus,
)
from .history import HistoryRecord
from .online import DB2RequestArea, InquiryCommunicationArea, OnlineErrorHandling
from .portfolio import (
    PortfolioAuditInfo,
    PortfolioClientInfo,
    PortfolioFinancialInfo,
    PortfolioInfo,
    PortfolioKey,
    PortfolioRecord,
)
from .position import PositionRecord
from .process_sequence import ProcessDependencyEntry, ProcessSequenceRecord, StandardSequences
from .return_code import ReturnCodeArea
from .transaction import TransactionRecord
from .validation import (
    VAL_ERROR_MESSAGES,
    VAL_ID_PREFIX,
    VAL_MAX_AMOUNT,
    VAL_MIN_AMOUNT,
    VALID_INVESTMENT_TYPES,
)

__all__ = [
    # Portfolio
    "PortfolioRecord",
    "PortfolioKey",
    "PortfolioClientInfo",
    "PortfolioInfo",
    "PortfolioFinancialInfo",
    "PortfolioAuditInfo",
    # Position
    "PositionRecord",
    # Transaction
    "TransactionRecord",
    # History
    "HistoryRecord",
    # Audit
    "AuditRecord",
    # Error handling
    "ErrorMessage",
    "ReturnHandling",
    "ErrorLocation",
    "ErrorInfo",
    "SystemInfo",
    "ReturnActions",
    "StandardErrorCode",
    "VsamStatus",
    # Return codes
    "ReturnCodeArea",
    # Batch
    "BatchControlRecord",
    "BatchControlConstants",
    "PrerequisiteJob",
    # Checkpoint
    "CheckpointControl",
    "CheckpointRecord",
    "CheckpointFileStatus",
    # Process sequence
    "ProcessSequenceRecord",
    "ProcessDependencyEntry",
    "StandardSequences",
    # DB tables
    "PoshistRecord",
    "ErrlogRecord",
    # DB procedures
    "DB2ErrorHandling",
    "SqlStatusCodes",
    # Online
    "InquiryCommunicationArea",
    "DB2RequestArea",
    "OnlineErrorHandling",
    # Validation
    "VAL_MIN_AMOUNT",
    "VAL_MAX_AMOUNT",
    "VAL_ID_PREFIX",
    "VAL_ERROR_MESSAGES",
    "VALID_INVESTMENT_TYPES",
    # All enums
    "ReturnCode",
    "ValidationReturnCode",
    "StatusCode",
    "ClientType",
    "PortfolioStatus",
    "PositionStatus",
    "TransactionType",
    "TransactionStatus",
    "HistoryRecordType",
    "HistoryActionCode",
    "AuditType",
    "AuditAction",
    "AuditStatus",
    "ErrorCategory",
    "ErrorType",
    "ErrorAction",
    "ReturnCodeStatus",
    "ReturnCodeRequestType",
    "BatchProcessStatus",
    "BatchProcessType",
    "BatchDependencyType",
    "BatchRecordType",
    "CheckpointStatus",
    "CheckpointPhase",
    "CheckpointRestartMode",
    "ProcessSequenceType",
    "ProcessFrequency",
    "ProcessDependencyType",
    "SqlStatusCode",
    "DB2RequestType",
    "InquiryFunction",
    "OnlineErrorSeverity",
    "OnlineErrorAction",
    "ErrorLogType",
    "ErrorLogSeverity",
    "CurrencyCode",
    "InvestmentType",
]
