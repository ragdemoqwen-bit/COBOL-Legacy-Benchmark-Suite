"""
Test Validation Suite — converted from TSTVAL00.cbl (226 LOC).

Replaces: COBOL TSTVAL00 program — validates test results and system behavior:
          functional tests, integration tests, performance benchmarks, error tests.
Target:   Python test runner/validator service.

COBOL flow:
  1000-INITIALIZE   → open files, write headers, init metrics
  2000-PROCESS      → read test cases, execute, validate, report
  2100-EXECUTE-TEST → EVALUATE TEST-TYPE
  2200-RUN-FUNCTIONAL-TEST  → functional validation
  2300-RUN-INTEGRATION-TEST → cross-module validation
  2400-RUN-PERFORMANCE-TEST → timing validation
  2500-RUN-ERROR-TEST       → error handling validation
  2600-VALIDATE-RESULTS     → compare actual vs expected
  2700-UPDATE-METRICS       → update test metrics
  2800-WRITE-TEST-DETAIL    → write detail line
  2900-WRITE-SUMMARY        → write summary with pass/fail rates
  3000-CLEANUP              → close files
"""

import logging
import time
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

logger = logging.getLogger(__name__)


class TestCaseType(StrEnum):
    """Test case types — from TSTVAL00.cbl WS-TEST-TYPES."""

    FUNCTIONAL = "FUNCTIONAL"
    INTEGRATION = "INTEGRATE"
    PERFORMANCE = "PERFORM"
    ERROR = "ERROR"


@dataclass
class TestCase:
    """A test case — replaces TSTVAL00.cbl TEST-CASE-RECORD."""

    test_id: str
    test_type: str
    description: str
    parameters: dict[str, Any] = field(default_factory=dict)
    expected_result: Any = None
    actual_result: Any = None


@dataclass
class TestResult:
    """Result of a single test — replaces TSTVAL00.cbl WS-TEST-DETAIL."""

    test_id: str
    test_type: str
    description: str
    passed: bool
    message: str = ""
    elapsed_ms: float = 0.0


@dataclass
class TestSuiteMetrics:
    """Test suite metrics — replaces TSTVAL00.cbl WS-TEST-METRICS."""

    total_tests: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    start_time: float = 0.0
    end_time: float = 0.0
    results: list[TestResult] = field(default_factory=list)

    @property
    def elapsed_time(self) -> float:
        """Total elapsed time in seconds."""
        return self.end_time - self.start_time if self.end_time > self.start_time else 0.0

    @property
    def success_rate(self) -> float:
        """Success rate as percentage."""
        if self.total_tests == 0:
            return 0.0
        return (self.tests_passed / self.total_tests) * 100.0


class TestValidatorService:
    """
    Test validation suite — replaces TSTVAL00.cbl.

    Executes test cases, compares actual vs expected results, reports metrics.
    """

    def __init__(self) -> None:
        self._validators: dict[str, Any] = {}

    def register_validator(self, test_type: str, validator_fn: Any) -> None:
        """Register a validator function for a test type."""
        self._validators[test_type.strip().upper()] = validator_fn

    def run_suite(self, test_cases: list[TestCase]) -> TestSuiteMetrics:
        """
        Run a suite of test cases.

        Replaces: 2000-PROCESS loop + 2100-EXECUTE-TEST dispatch.
        """
        metrics = TestSuiteMetrics()
        metrics.start_time = time.time()

        for tc in test_cases:
            metrics.total_tests += 1
            result = self._execute_test(tc)
            metrics.results.append(result)

            if result.passed:
                metrics.tests_passed += 1
            else:
                metrics.tests_failed += 1

        metrics.end_time = time.time()

        logger.info(
            "Test suite complete: total=%d, passed=%d, failed=%d, rate=%.1f%%",
            metrics.total_tests,
            metrics.tests_passed,
            metrics.tests_failed,
            metrics.success_rate,
        )
        return metrics

    def _execute_test(self, tc: TestCase) -> TestResult:
        """
        Execute a single test case.

        Replaces: 2100-EXECUTE-TEST EVALUATE + 2600-VALIDATE-RESULTS.
        """
        start = time.time()
        test_type = tc.test_type.strip().upper()

        try:
            # Look up registered validator
            validator = self._validators.get(test_type)
            if validator is None:
                return TestResult(
                    test_id=tc.test_id,
                    test_type=tc.test_type,
                    description=tc.description,
                    passed=False,
                    message=f"No validator registered for type: {tc.test_type!r}",
                    elapsed_ms=(time.time() - start) * 1000,
                )

            # Execute the validator
            actual = validator(tc)
            tc.actual_result = actual

            # Compare actual vs expected (replaces 2600-VALIDATE-RESULTS)
            passed = actual == tc.expected_result
            elapsed = (time.time() - start) * 1000

            return TestResult(
                test_id=tc.test_id,
                test_type=tc.test_type,
                description=tc.description,
                passed=passed,
                message="" if passed else f"Expected {tc.expected_result!r}, got {actual!r}",
                elapsed_ms=elapsed,
            )

        except Exception as exc:
            elapsed = (time.time() - start) * 1000
            return TestResult(
                test_id=tc.test_id,
                test_type=tc.test_type,
                description=tc.description,
                passed=False,
                message=f"Exception: {exc}",
                elapsed_ms=elapsed,
            )

    def format_report(self, metrics: TestSuiteMetrics) -> str:
        """
        Format test report.

        Replaces: 1200-WRITE-HEADERS + 2800-WRITE-TEST-DETAIL + 2900-WRITE-SUMMARY.
        """
        lines = [
            "*" * 70,
            "                    TEST VALIDATION REPORT",
            "*" * 70,
            "",
        ]

        # Detail lines (replaces 2800-WRITE-TEST-DETAIL)
        lines.append(f"{'TEST ID':<12}{'TYPE':<12}{'DESCRIPTION':<40}{'RESULT':<6}")
        lines.append("-" * 70)
        for r in metrics.results:
            status = "PASS" if r.passed else "FAIL"
            lines.append(f"{r.test_id:<12}{r.test_type:<12}{r.description:<40}{status:<6}")
            if not r.passed and r.message:
                lines.append(f"             -> {r.message}")

        # Summary line (replaces 2900-WRITE-SUMMARY)
        lines.append("")
        lines.append("-" * 70)
        lines.append(
            f"TOTAL TESTS: {metrics.total_tests:>6,}  "
            f"PASSED: {metrics.tests_passed:>6,}  "
            f"FAILED: {metrics.tests_failed:>6,}  "
            f"SUCCESS: {metrics.success_rate:>6.2f}%"
        )
        lines.append(f"ELAPSED TIME: {metrics.elapsed_time:.3f}s")
        lines.append("*" * 70)
        return "\n".join(lines)
