"""Tests for Wave 3 Utility services."""

from decimal import Decimal

from services.utility.file_maintenance import (
    FileMaintenanceService,
    MaintenanceCommand,
)
from services.utility.system_monitor import (
    SystemMonitorService,
    ThresholdConfig,
)


class TestFileMaintenanceService:
    def test_archive_command(self) -> None:
        svc = FileMaintenanceService()
        cmds = [MaintenanceCommand(function="ARCHIVE", file_name="PORTMSTR")]
        result = svc.process_commands(cmds)
        assert result.records_read == 1
        assert result.records_written == 1
        assert result.errors == 0

    def test_cleanup_command(self) -> None:
        svc = FileMaintenanceService()
        cmds = [MaintenanceCommand(function="CLEANUP", file_name="TRANHIST")]
        result = svc.process_commands(cmds)
        assert result.records_written == 1

    def test_reorg_command(self) -> None:
        svc = FileMaintenanceService()
        cmds = [MaintenanceCommand(function="REORG", file_name="POSHIST")]
        result = svc.process_commands(cmds)
        assert result.records_written == 1

    def test_analyze_command(self) -> None:
        svc = FileMaintenanceService()
        cmds = [MaintenanceCommand(function="ANALYZE", file_name="PORTMSTR")]
        result = svc.process_commands(cmds)
        assert result.records_written == 1

    def test_invalid_function(self) -> None:
        svc = FileMaintenanceService()
        cmds = [MaintenanceCommand(function="INVALID", file_name="TEST")]
        result = svc.process_commands(cmds)
        assert result.errors == 1

    def test_multiple_commands(self) -> None:
        svc = FileMaintenanceService()
        cmds = [
            MaintenanceCommand(function="ARCHIVE", file_name="F1"),
            MaintenanceCommand(function="CLEANUP", file_name="F2"),
            MaintenanceCommand(function="REORG", file_name="F3"),
            MaintenanceCommand(function="ANALYZE", file_name="F4"),
        ]
        result = svc.process_commands(cmds)
        assert result.records_read == 4
        assert result.records_written == 4


class TestSystemMonitorService:
    def test_no_thresholds(self) -> None:
        svc = SystemMonitorService()
        result = svc.check_metrics({"CPU.UTIL": Decimal("50")})
        assert len(result.metrics) == 1
        assert result.thresholds_breached == 0

    def test_threshold_breached(self) -> None:
        svc = SystemMonitorService(thresholds=[
            ThresholdConfig(
                resource_type="CPU",
                threshold_type="UTIL",
                threshold_value=Decimal("80"),
                alert_level="WARNING",
            ),
        ])
        result = svc.check_metrics({"CPU.UTIL": Decimal("90")})
        assert result.thresholds_breached == 1
        assert len(result.alerts) == 1

    def test_threshold_not_breached(self) -> None:
        svc = SystemMonitorService(thresholds=[
            ThresholdConfig(
                resource_type="CPU",
                threshold_type="UTIL",
                threshold_value=Decimal("80"),
                alert_level="WARNING",
            ),
        ])
        result = svc.check_metrics({"CPU.UTIL": Decimal("50")})
        assert result.thresholds_breached == 0

    def test_multiple_metrics(self) -> None:
        svc = SystemMonitorService()
        result = svc.check_metrics({
            "CPU.UTIL": Decimal("75"),
            "MEMORY.UTIL": Decimal("60"),
            "DB2.RESPONSE": Decimal("150"),
        })
        assert len(result.metrics) == 3

    def test_format_status_report(self) -> None:
        svc = SystemMonitorService()
        result = svc.check_metrics({"CPU.UTIL": Decimal("50")})
        report = svc.format_status_report(result)
        assert "SYSTEM MONITORING STATUS REPORT" in report
