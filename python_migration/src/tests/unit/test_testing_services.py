"""Tests for Wave 3 Test Harness services."""

from decimal import Decimal

from services.testing.test_data_generator import (
    GenerationConfig,
    TestDataGeneratorService,
)
from services.testing.test_validator import (
    TestCase,
    TestValidatorService,
)


class TestTestDataGenerator:
    def test_generate_portfolios(self) -> None:
        gen = TestDataGeneratorService(seed=42)
        configs = [GenerationConfig(test_type="PORTFOLIO", volume=10)]
        result = gen.generate(configs)
        assert result.records_written == 10
        assert len(result.portfolios) == 10

    def test_generate_transactions(self) -> None:
        gen = TestDataGeneratorService(seed=42)
        configs = [GenerationConfig(test_type="TRANSACTN", volume=5)]
        result = gen.generate(configs)
        assert result.records_written == 5
        assert len(result.transactions) == 5

    def test_generate_error_data(self) -> None:
        gen = TestDataGeneratorService(seed=42)
        configs = [GenerationConfig(test_type="ERROR", volume=4)]
        result = gen.generate(configs)
        assert result.records_written == 4

    def test_generate_volume_data(self) -> None:
        gen = TestDataGeneratorService(seed=42)
        configs = [GenerationConfig(test_type="VOLUME", volume=3)]
        result = gen.generate(configs)
        assert result.records_written == 3 + 15

    def test_invalid_test_type(self) -> None:
        gen = TestDataGeneratorService(seed=42)
        configs = [GenerationConfig(test_type="INVALID", volume=1)]
        result = gen.generate(configs)
        assert result.error_count == 1

    def test_deterministic_with_seed(self) -> None:
        gen1 = TestDataGeneratorService(seed=123)
        gen2 = TestDataGeneratorService(seed=123)
        r1 = gen1.generate([GenerationConfig(test_type="PORTFOLIO", volume=5)])
        r2 = gen2.generate([GenerationConfig(test_type="PORTFOLIO", volume=5)])
        assert r1.portfolios == r2.portfolios

    def test_portfolio_fields(self) -> None:
        gen = TestDataGeneratorService(seed=42)
        configs = [GenerationConfig(test_type="PORTFOLIO", volume=1)]
        result = gen.generate(configs)
        port = result.portfolios[0]
        assert "portfolio_id" in port
        assert "currency_code" in port
        assert isinstance(port["balance"], Decimal)

    def test_multiple_configs(self) -> None:
        gen = TestDataGeneratorService(seed=42)
        configs = [
            GenerationConfig(test_type="PORTFOLIO", volume=3),
            GenerationConfig(test_type="TRANSACTN", volume=2),
        ]
        result = gen.generate(configs)
        assert result.records_written == 5


class TestTestValidator:
    def test_run_suite_all_pass(self) -> None:
        svc = TestValidatorService()
        svc.register_validator("FUNCTIONAL", lambda tc: tc.expected_result)
        cases = [
            TestCase(test_id="T001", test_type="FUNCTIONAL",
                     description="Basic check", expected_result="OK"),
            TestCase(test_id="T002", test_type="FUNCTIONAL",
                     description="Another check", expected_result="PASS"),
        ]
        metrics = svc.run_suite(cases)
        assert metrics.total_tests == 2
        assert metrics.tests_passed == 2
        assert metrics.success_rate == 100.0

    def test_run_suite_with_failure(self) -> None:
        svc = TestValidatorService()
        svc.register_validator("FUNCTIONAL", lambda tc: "WRONG")
        cases = [
            TestCase(test_id="T001", test_type="FUNCTIONAL",
                     description="Should fail", expected_result="RIGHT"),
        ]
        metrics = svc.run_suite(cases)
        assert metrics.tests_failed == 1

    def test_no_validator_registered(self) -> None:
        svc = TestValidatorService()
        cases = [
            TestCase(test_id="T001", test_type="UNKNOWN",
                     description="No validator", expected_result="X"),
        ]
        metrics = svc.run_suite(cases)
        assert metrics.tests_failed == 1
        assert "No validator" in metrics.results[0].message

    def test_format_report(self) -> None:
        svc = TestValidatorService()
        svc.register_validator("FUNCTIONAL", lambda tc: tc.expected_result)
        cases = [
            TestCase(test_id="T001", test_type="FUNCTIONAL",
                     description="Pass test", expected_result="OK"),
        ]
        metrics = svc.run_suite(cases)
        report = svc.format_report(metrics)
        assert "TEST VALIDATION REPORT" in report

    def test_empty_suite(self) -> None:
        svc = TestValidatorService()
        metrics = svc.run_suite([])
        assert metrics.total_tests == 0
        assert metrics.success_rate == 0.0
