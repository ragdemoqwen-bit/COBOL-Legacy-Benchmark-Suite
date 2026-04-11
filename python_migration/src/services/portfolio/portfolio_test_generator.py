"""
Portfolio Test Data Generator — converted from PORTTEST.cbl (120 LOC).

Replaces: COBOL PORTTEST program — generates synthetic test data with
          random values for testing purposes.
Target:   Python faker/random-based test data generation.

COBOL flow:
  1000-INIT         → seed random, init counters
  2000-GENERATE     → loop N times generating random portfolio records
  3000-WRITE-RECORD → write each generated record
  4000-TERMINATE    → close files, display counts
"""

import logging
import random
import string
from datetime import date, datetime, timedelta
from decimal import Decimal

from models.enums import CurrencyCode, PortfolioStatus

logger = logging.getLogger(__name__)


class PortfolioTestGenerator:
    """
    Generates synthetic portfolio test data — replaces PORTTEST.cbl.

    Uses Python random module to generate realistic portfolio records,
    similar to COBOL FUNCTION RANDOM for generating test data.
    """

    def __init__(self, seed: int | None = None) -> None:
        if seed is not None:
            random.seed(seed)

    def generate_portfolio_id(self) -> str:
        """Generate a random 8-char portfolio ID (replaces PORTTEST random key generation)."""
        return "P" + "".join(random.choices(string.digits, k=7))

    def generate_account_no(self) -> str:
        """Generate a random 10-char account number."""
        return "".join(random.choices(string.digits, k=10))

    def generate_client_id(self) -> str:
        """Generate a random 10-char client ID."""
        return "C" + "".join(random.choices(string.digits, k=9))

    def generate_portfolio_record(self) -> dict:
        """
        Generate a single portfolio record with random data.

        Replaces: 2000-GENERATE-RECORD paragraph.
        """
        open_date = date.today() - timedelta(days=random.randint(30, 3650))
        status = random.choice(list(PortfolioStatus))
        close_date = None
        if status == PortfolioStatus.CLOSED:
            close_date = open_date + timedelta(days=random.randint(1, 365))

        return {
            "portfolio_id": self.generate_portfolio_id(),
            "account_type": random.choice(["IN", "CO", "TR"]),
            "branch_id": random.choice(["01", "02", "03", "04", "05"]),
            "client_id": self.generate_client_id(),
            "portfolio_name": f"Portfolio {random.randint(1000, 9999)}",
            "currency_code": random.choice(list(CurrencyCode)).value,
            "risk_level": random.choice(["1", "2", "3", "4", "5"]),
            "status": status.value,
            "open_date": open_date,
            "close_date": close_date,
            "last_maint_date": datetime.now(),
            "last_maint_user": "TESTGEN",
        }

    def generate_batch(self, count: int = 100) -> list[dict]:
        """
        Generate a batch of portfolio test records.

        Replaces: Main loop — PERFORM 2000-GENERATE-RECORD N TIMES.
        """
        records = []
        for _ in range(count):
            records.append(self.generate_portfolio_record())
        logger.info("Generated %d test portfolio records", count)
        return records

    def generate_transaction_data(self, portfolio_id: str, count: int = 10) -> list[dict]:
        """Generate test transaction data for a given portfolio."""
        transactions = []
        for i in range(count):
            trans_type = random.choice(["BU", "SL", "TR", "FE"])
            qty = Decimal(str(random.randint(1, 1000)))
            price = Decimal(str(round(random.uniform(1.0, 500.0), 4)))
            transactions.append({
                "transaction_id": f"T{portfolio_id}{i:04d}",
                "portfolio_id": portfolio_id,
                "investment_id": f"INV{random.randint(10000, 99999):05d}",
                "transaction_type": trans_type,
                "quantity": qty,
                "price": price,
                "currency_code": "USD",
                "user_id": "TESTGEN",
            })
        return transactions
