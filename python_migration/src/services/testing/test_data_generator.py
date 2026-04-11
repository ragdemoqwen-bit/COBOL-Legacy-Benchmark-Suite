"""
Test Data Generator — converted from TSTGEN00.cbl (217 LOC).

Replaces: COBOL TSTGEN00 program — generates test data for system testing:
          portfolio test data, transaction scenarios, error conditions,
          performance test volumes.
Target:   Python service with configurable test data generation.

COBOL flow:
  1000-INITIALIZE       → open files, init random seed, init counters
  2000-PROCESS          → read config, dispatch to generator
  2100-GENERATE-TEST-DATA → EVALUATE CFG-TEST-TYPE
  2200-GEN-PORTFOLIO    → generate portfolio test records
  2300-GEN-TRANSACTION  → generate transaction test records
  2400-GEN-ERROR-DATA   → generate error condition data
  2500-GEN-VOLUME-DATA  → generate large volumes for perf testing
  3000-CLEANUP          → close files
"""

import logging
import random
import string
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from enum import StrEnum

logger = logging.getLogger(__name__)


class TestType(StrEnum):
    """Test data types — from TSTGEN00.cbl WS-TEST-TYPES."""

    PORTFOLIO = "PORTFOLIO"
    TRANSACTION = "TRANSACTN"
    ERROR = "ERROR"
    VOLUME = "VOLUME"


@dataclass
class GenerationConfig:
    """Generation config — replaces TSTGEN00.cbl CONFIG-RECORD."""

    test_type: str
    volume: int
    parameters: str = ""


@dataclass
class GenerationResult:
    """Generation result — replaces TSTGEN00.cbl WS-COUNTERS."""

    records_written: int = 0
    error_count: int = 0
    portfolios: list[dict] = field(default_factory=list)
    transactions: list[dict] = field(default_factory=list)


class TestDataGeneratorService:
    """
    Test data generator — replaces TSTGEN00.cbl.

    Generates synthetic test data: portfolios, transactions, error conditions,
    and volume data for performance testing.
    """

    MAX_ERRORS = 100  # From TSTGEN00.cbl: IF WS-ERROR-COUNT > 100

    PORTFOLIO_TYPES = ["GR", "IN", "BL", "AG"]
    TRANSACTION_TYPES = ["BU", "SL", "TR", "FE"]
    STATUSES = ["A", "C", "S"]
    CURRENCIES = ["USD", "EUR", "GBP", "JPY", "CAD"]

    def __init__(self, seed: int | None = None) -> None:
        """Initialize with optional random seed — replaces 1200-INIT-RANDOM."""
        self._rng = random.Random(seed)

    def generate(self, configs: list[GenerationConfig]) -> GenerationResult:
        """
        Generate test data from configs.

        Replaces: 2000-PROCESS loop reading TEST-CONFIG.
        """
        result = GenerationResult()

        for cfg in configs:
            if result.error_count > self.MAX_ERRORS:
                logger.error("Error threshold exceeded, aborting generation")
                break

            try:
                self._dispatch(cfg, result)
            except ValueError as exc:
                result.error_count += 1
                logger.error("Generation error: %s", exc)

        logger.info(
            "Generation complete: written=%d, errors=%d",
            result.records_written,
            result.error_count,
        )
        return result

    def _dispatch(self, cfg: GenerationConfig, result: GenerationResult) -> None:
        """Dispatch to generator — replaces 2100-GENERATE-TEST-DATA EVALUATE."""
        test_type = cfg.test_type.strip().upper()
        if test_type == TestType.PORTFOLIO:
            self._gen_portfolios(cfg.volume, result)
        elif test_type == TestType.TRANSACTION:
            self._gen_transactions(cfg.volume, result)
        elif test_type == TestType.ERROR:
            self._gen_error_data(cfg.volume, result)
        elif test_type == TestType.VOLUME:
            self._gen_volume_data(cfg.volume, result)
        else:
            raise ValueError(f"Invalid test type: {cfg.test_type!r}")

    def _gen_portfolios(self, volume: int, result: GenerationResult) -> None:
        """
        Generate portfolio test records.

        Replaces: 2200-GEN-PORTFOLIO loop.
        """
        for _ in range(volume):
            portfolio = {
                "portfolio_id": self._random_id(8),
                "account_type": self._rng.choice(self.PORTFOLIO_TYPES),
                "branch_id": f"{self._rng.randint(1, 99):02d}",
                "client_id": self._random_id(10),
                "portfolio_name": f"Portfolio {self._random_id(6)}",
                "currency_code": self._rng.choice(self.CURRENCIES),
                "risk_level": str(self._rng.randint(1, 5)),
                "status": self._rng.choice(self.STATUSES),
                "open_date": self._random_date(),
                "balance": self._random_amount(),
            }
            result.portfolios.append(portfolio)
            result.records_written += 1

    def _gen_transactions(self, volume: int, result: GenerationResult) -> None:
        """
        Generate transaction test records.

        Replaces: 2300-GEN-TRANSACTION loop.
        """
        for _ in range(volume):
            transaction = {
                "transaction_id": self._random_id(12),
                "transaction_type": self._rng.choice(self.TRANSACTION_TYPES),
                "amount": self._random_amount(),
                "transaction_date": self._random_date(),
                "status": self._rng.choice(["P", "D", "F", "R"]),
                "portfolio_id": self._random_id(8),
                "investment_id": self._random_id(10),
                "quantity": Decimal(str(self._rng.randint(1, 10000))),
                "price": self._random_amount(max_val=1000),
            }
            result.transactions.append(transaction)
            result.records_written += 1

    def _gen_error_data(self, volume: int, result: GenerationResult) -> None:
        """
        Generate error condition data.

        Replaces: 2400-GEN-ERROR-DATA → data errors + process errors.
        """
        # Data errors (invalid formats)
        for _ in range(volume // 2):
            result.portfolios.append({
                "portfolio_id": "",  # Invalid: empty ID
                "account_type": "XX",  # Invalid: bad type
                "status": "Z",  # Invalid: bad status
                "balance": Decimal("-999999999999.99"),  # Edge: negative
            })
            result.records_written += 1

        # Process errors (boundary values)
        for _ in range(volume - volume // 2):
            result.transactions.append({
                "transaction_id": self._random_id(12),
                "transaction_type": "ZZ",  # Invalid type
                "amount": Decimal("0.00"),  # Zero amount
                "status": "X",  # Invalid status
            })
            result.records_written += 1

    def _gen_volume_data(self, volume: int, result: GenerationResult) -> None:
        """
        Generate large volume data for performance testing.

        Replaces: 2500-GEN-VOLUME-DATA → large portfolio + transaction sets.
        """
        self._gen_portfolios(volume, result)
        self._gen_transactions(volume * 5, result)

    def _random_id(self, length: int) -> str:
        """Generate random alphanumeric ID."""
        return "".join(self._rng.choices(string.ascii_uppercase + string.digits, k=length))

    def _random_date(self, start_year: int = 2020, end_year: int = 2026) -> date:
        """Generate random date in range."""
        start = date(start_year, 1, 1)
        end = date(end_year, 12, 31)
        delta = (end - start).days
        return start + timedelta(days=self._rng.randint(0, delta))

    def _random_amount(self, max_val: int = 9999999) -> Decimal:
        """Generate random decimal amount with 2 decimal places."""
        whole = self._rng.randint(0, max_val)
        cents = self._rng.randint(0, 99)
        return Decimal(f"{whole}.{cents:02d}")
