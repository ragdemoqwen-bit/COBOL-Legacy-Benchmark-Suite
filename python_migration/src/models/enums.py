"""
Enumerations derived from COBOL copybook 88-level conditions and COMMON.cpy constants.

Source copybooks: COMMON.cpy, PORTFLIO.cpy, POSREC.cpy, TRNREC.cpy, HISTREC.cpy,
                  AUDITLOG.cpy, ERRHAND.cpy, RETHND.cpy, BCHCON.cpy, SQLCA.cpy
"""

from enum import IntEnum, StrEnum


# ---------------------------------------------------------------------------
# Return Codes (COMMON.cpy RETURN-CODES + ERRHAND.cpy ERR-RETURN-CODES)
# ---------------------------------------------------------------------------
class ReturnCode(IntEnum):
    """Standard mainframe return codes (multiples of 4)."""

    SUCCESS = 0
    WARNING = 4
    ERROR = 8
    SEVERE = 12
    CRITICAL = 16


# ---------------------------------------------------------------------------
# Portfolio Validation Return Codes (PORTVAL.cpy VAL-RETURN-CODES)
# ---------------------------------------------------------------------------
class ValidationReturnCode(IntEnum):
    """Portfolio validation specific return codes."""

    SUCCESS = 0
    INVALID_ID = 1
    INVALID_ACCT = 2
    INVALID_TYPE = 3
    INVALID_AMT = 4


# ---------------------------------------------------------------------------
# Status Codes (COMMON.cpy STATUS-CODES)
# ---------------------------------------------------------------------------
class StatusCode(StrEnum):
    """General status codes used across the system."""

    ACTIVE = "A"
    CLOSED = "C"
    PENDING = "P"
    SUSPENDED = "S"
    FAILED = "F"
    REVERSED = "R"


# ---------------------------------------------------------------------------
# Client Type (PORTFLIO.cpy PORT-CLIENT-TYPE 88-levels)
# ---------------------------------------------------------------------------
class ClientType(StrEnum):
    """Portfolio client type."""

    INDIVIDUAL = "I"
    CORPORATE = "C"
    TRUST = "T"


# ---------------------------------------------------------------------------
# Portfolio Status (PORTFLIO.cpy PORT-STATUS 88-levels)
# ---------------------------------------------------------------------------
class PortfolioStatus(StrEnum):
    """Portfolio lifecycle status."""

    ACTIVE = "A"
    CLOSED = "C"
    SUSPENDED = "S"


# ---------------------------------------------------------------------------
# Position Status (POSREC.cpy POS-STATUS 88-levels)
# ---------------------------------------------------------------------------
class PositionStatus(StrEnum):
    """Investment position status."""

    ACTIVE = "A"
    CLOSED = "C"
    PENDING = "P"


# ---------------------------------------------------------------------------
# Transaction Type (COMMON.cpy TRANSACTION-TYPES + TRNREC.cpy 88-levels)
# ---------------------------------------------------------------------------
class TransactionType(StrEnum):
    """Investment transaction types."""

    BUY = "BU"
    SELL = "SL"
    TRANSFER = "TR"
    FEE = "FE"


# ---------------------------------------------------------------------------
# Transaction Status (TRNREC.cpy TRN-STATUS 88-levels)
# ---------------------------------------------------------------------------
class TransactionStatus(StrEnum):
    """Transaction processing status."""

    PENDING = "P"
    DONE = "D"
    FAILED = "F"
    REVERSED = "R"


# ---------------------------------------------------------------------------
# History Record Type (HISTREC.cpy HIST-RECORD-TYPE 88-levels)
# ---------------------------------------------------------------------------
class HistoryRecordType(StrEnum):
    """Type of record in history trail."""

    PORTFOLIO = "PT"
    POSITION = "PS"
    TRANSACTION = "TR"


# ---------------------------------------------------------------------------
# History Action Code (HISTREC.cpy HIST-ACTION-CODE 88-levels)
# ---------------------------------------------------------------------------
class HistoryActionCode(StrEnum):
    """Action that caused the history record."""

    ADD = "A"
    CHANGE = "C"
    DELETE = "D"


# ---------------------------------------------------------------------------
# Audit Type (AUDITLOG.cpy AUD-TYPE 88-levels)
# ---------------------------------------------------------------------------
class AuditType(StrEnum):
    """Audit record classification."""

    TRANSACTION = "TRAN"
    USER_ACTION = "USER"
    SYSTEM_EVENT = "SYST"


# ---------------------------------------------------------------------------
# Audit Action (AUDITLOG.cpy AUD-ACTION 88-levels)
# ---------------------------------------------------------------------------
class AuditAction(StrEnum):
    """Audit trail action codes."""

    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    INQUIRE = "INQUIRE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    STARTUP = "STARTUP"
    SHUTDOWN = "SHUTDOWN"


# ---------------------------------------------------------------------------
# Audit Status (AUDITLOG.cpy AUD-STATUS 88-levels)
# ---------------------------------------------------------------------------
class AuditStatus(StrEnum):
    """Audit record outcome status."""

    SUCCESS = "SUCC"
    FAILURE = "FAIL"
    WARNING = "WARN"


# ---------------------------------------------------------------------------
# Error Category (ERRHAND.cpy ERR-CATEGORIES)
# ---------------------------------------------------------------------------
class ErrorCategory(StrEnum):
    """Error classification category."""

    VSAM = "VS"
    VALIDATION = "VL"
    PROCESSING = "PR"
    SYSTEM = "SY"


# ---------------------------------------------------------------------------
# Error Type (RETHND.cpy ERROR-TYPE 88-levels)
# ---------------------------------------------------------------------------
class ErrorType(StrEnum):
    """Detailed error type classification."""

    VALIDATION = "V"
    PROCESSING = "P"
    DATABASE = "D"
    FILE = "F"
    SECURITY = "S"


# ---------------------------------------------------------------------------
# Error Action (RETHND.cpy ACTION-FLAG 88-levels)
# ---------------------------------------------------------------------------
class ErrorAction(StrEnum):
    """Action to take after an error."""

    CONTINUE = "C"
    ABORT = "A"
    RETRY = "R"


# ---------------------------------------------------------------------------
# Return Code Status (RTNCODE.cpy RC-STATUS 88-levels)
# ---------------------------------------------------------------------------
class ReturnCodeStatus(StrEnum):
    """Return code analysis status."""

    SUCCESS = "S"
    WARNING = "W"
    ERROR = "E"
    SEVERE = "F"


# ---------------------------------------------------------------------------
# Return Code Request Type (RTNCODE.cpy RC-REQUEST-TYPE 88-levels)
# ---------------------------------------------------------------------------
class ReturnCodeRequestType(StrEnum):
    """Return code management request type."""

    INITIALIZE = "I"
    SET_CODE = "S"
    GET_CODE = "G"
    LOG_CODE = "L"
    ANALYZE = "A"


# ---------------------------------------------------------------------------
# Batch Process Status (BCHCON.cpy BCT-STAT-VALUES)
# ---------------------------------------------------------------------------
class BatchProcessStatus(StrEnum):
    """Batch process execution status."""

    READY = "R"
    ACTIVE = "A"
    WAITING = "W"
    DONE = "D"
    ERROR = "E"


# ---------------------------------------------------------------------------
# Batch Process Type (BCHCON.cpy BCT-PROC-TYPES)
# ---------------------------------------------------------------------------
class BatchProcessType(StrEnum):
    """Batch process classification."""

    INITIAL = "INI"
    UPDATE = "UPD"
    REPORT = "RPT"
    CLEANUP = "CLN"


# ---------------------------------------------------------------------------
# Batch Dependency Type (BCHCON.cpy BCT-DEP-TYPES)
# ---------------------------------------------------------------------------
class BatchDependencyType(StrEnum):
    """Batch job dependency classification."""

    REQUIRED = "R"
    OPTIONAL = "O"
    EXCLUSIVE = "X"


# ---------------------------------------------------------------------------
# Batch Record Type (BCHCON.cpy BCT-REC-TYPES)
# ---------------------------------------------------------------------------
class BatchRecordType(StrEnum):
    """Batch control file record type."""

    CONTROL = "C"
    PROCESS = "P"
    DEPENDENCY = "D"
    HISTORY = "H"


# ---------------------------------------------------------------------------
# Checkpoint Status (CKPRST.cpy CK-STATUS 88-levels)
# ---------------------------------------------------------------------------
class CheckpointStatus(StrEnum):
    """Checkpoint/restart processing status."""

    INITIAL = "I"
    ACTIVE = "A"
    COMPLETE = "C"
    FAILED = "F"
    RESTARTED = "R"


# ---------------------------------------------------------------------------
# Checkpoint Phase (CKPRST.cpy CK-PHASE 88-levels)
# ---------------------------------------------------------------------------
class CheckpointPhase(StrEnum):
    """Checkpoint processing phase."""

    INIT = "00"
    READ = "10"
    PROCESS = "20"
    UPDATE = "30"
    TERMINATE = "40"


# ---------------------------------------------------------------------------
# Checkpoint Restart Mode (CKPRST.cpy CK-RESTART-MODE 88-levels)
# ---------------------------------------------------------------------------
class CheckpointRestartMode(StrEnum):
    """Checkpoint restart mode."""

    NORMAL = "N"
    RESTART = "R"
    RECOVER = "C"


# ---------------------------------------------------------------------------
# Process Sequence Type (PRCSEQ.cpy PSR-TYPE 88-levels)
# ---------------------------------------------------------------------------
class ProcessSequenceType(StrEnum):
    """Process sequence classification."""

    INIT = "INI"
    PROCESS = "PRC"
    REPORT = "RPT"
    TERMINATE = "TRM"


# ---------------------------------------------------------------------------
# Process Frequency (PRCSEQ.cpy PSR-FREQ 88-levels)
# ---------------------------------------------------------------------------
class ProcessFrequency(StrEnum):
    """Process scheduling frequency."""

    DAILY = "D"
    WEEKLY = "W"
    MONTHLY = "M"


# ---------------------------------------------------------------------------
# Process Dependency Type (PRCSEQ.cpy PSR-DEP-TYPE 88-levels)
# ---------------------------------------------------------------------------
class ProcessDependencyType(StrEnum):
    """Process dependency classification."""

    HARD = "H"
    SOFT = "S"


# ---------------------------------------------------------------------------
# SQL Status Codes (SQLCA.cpy SQL-STATUS-CODES)
# ---------------------------------------------------------------------------
class SqlStatusCode(StrEnum):
    """DB2 SQLSTATE codes."""

    SUCCESS = "00000"
    NOT_FOUND = "02000"
    DUPLICATE_KEY = "23505"
    DEADLOCK = "40001"
    TIMEOUT = "40003"
    CONNECTION_ERROR = "08001"
    DB_ERROR = "58004"


# ---------------------------------------------------------------------------
# DB2 Request Type (DB2REQ.cpy DB2-REQUEST-TYPE 88-levels)
# ---------------------------------------------------------------------------
class DB2RequestType(StrEnum):
    """DB2 connection request type."""

    CONNECT = "C"
    DISCONNECT = "D"
    STATUS = "S"


# ---------------------------------------------------------------------------
# Online Inquiry Function (INQCOM.cpy INQCOM-FUNCTION 88-levels)
# ---------------------------------------------------------------------------
class InquiryFunction(StrEnum):
    """Online inquiry function codes."""

    MENU = "MENU"
    PORTFOLIO = "INQP"
    HISTORY = "INQH"
    EXIT = "EXIT"


# ---------------------------------------------------------------------------
# Online Error Severity (ERRHND.cpy ERR-SEVERITY 88-levels)
# ---------------------------------------------------------------------------
class OnlineErrorSeverity(StrEnum):
    """Online error severity level."""

    FATAL = "F"
    WARNING = "W"
    INFO = "I"


# ---------------------------------------------------------------------------
# Online Error Action (ERRHND.cpy ERR-ACTION 88-levels)
# ---------------------------------------------------------------------------
class OnlineErrorAction(StrEnum):
    """Online error handling action."""

    RETURN = "R"
    CONTINUE = "C"
    ABEND = "A"


# ---------------------------------------------------------------------------
# Error Log Type (DBTBLS.cpy EL-ERROR-TYPE 88-levels)
# ---------------------------------------------------------------------------
class ErrorLogType(StrEnum):
    """Error log entry type."""

    SYSTEM = "S"
    APPLICATION = "A"
    DATA = "D"


# ---------------------------------------------------------------------------
# Error Log Severity (DBTBLS.cpy EL-ERROR-SEVERITY 88-levels)
# ---------------------------------------------------------------------------
class ErrorLogSeverity(IntEnum):
    """Error log severity level."""

    INFO = 1
    WARNING = 2
    ERROR = 3
    SEVERE = 4


# ---------------------------------------------------------------------------
# Currency Codes (COMMON.cpy CURRENCY-CODES)
# ---------------------------------------------------------------------------
class CurrencyCode(StrEnum):
    """Supported currency codes."""

    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    CAD = "CAD"


# ---------------------------------------------------------------------------
# Investment Type (PORTVAL.cpy validation — valid investment types)
# ---------------------------------------------------------------------------
class InvestmentType(StrEnum):
    """Valid investment types for portfolio positions."""

    STOCK = "STK"
    BOND = "BND"
    MONEY_MARKET = "MMF"
    ETF = "ETF"
