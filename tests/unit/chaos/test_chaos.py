"""
Unit tests for chaos engineering module.
"""

import pytest
import time
from datetime import datetime

from socialseed_e2e.chaos import (
    NetworkChaosInjector,
    ServiceChaosInjector,
    ResourceChaosInjector,
    GameDayOrchestrator,
    RecoveryValidator,
    NetworkChaosConfig,
    ServiceChaosConfig,
    ResourceChaosConfig,
    ChaosExperiment,
    ChaosResult,
    ChaosType,
    ExperimentStatus,
    GameDayScenario,
)


class TestNetworkChaosInjector:
    """Test network chaos injector."""

    def test_injector_initialization(self):
        injector = NetworkChaosInjector()
        assert injector is not None
        assert injector.active_experiments == {}

    def test_run_experiment(self):
        injector = NetworkChaosInjector()
        config = NetworkChaosConfig(latency_ms=50, jitter_ms=5)

        result = injector.run_experiment(
            experiment_id="net-test-001",
            config=config,
            target_service="test-service",
            duration_seconds=2,
        )

        assert result.experiment_id == "net-test-001"
        assert result.status in [ExperimentStatus.COMPLETED, ExperimentStatus.FAILED]

    def test_inject_latency_decorator(self):
        injector = NetworkChaosInjector()

        @injector.inject_latency(latency_ms=100, jitter_ms=10)
        def test_function():
            return "success"

        start = time.time()
        result = test_function()
        elapsed = time.time() - start

        assert result == "success"
        assert elapsed >= 0.09  # Should have at least 90ms delay

    def test_inject_packet_loss(self):
        injector = NetworkChaosInjector()

        @injector.inject_packet_loss(loss_percent=100.0)
        def test_function():
            return "success"

        with pytest.raises(ConnectionError):
            test_function()

    def test_inject_dns_failure(self):
        injector = NetworkChaosInjector()

        @injector.inject_dns_failure(failure_rate=100.0)
        def test_function():
            return "success"

        with pytest.raises(ConnectionError):
            test_function()

    def test_stop_experiment(self):
        injector = NetworkChaosInjector()
        config = NetworkChaosConfig()

        injector.run_experiment(
            experiment_id="stop-test",
            config=config,
            target_service="test",
            duration_seconds=10,
        )

        assert injector.stop_experiment("stop-test") is True
        assert injector.stop_experiment("nonexistent") is False


class TestServiceChaosInjector:
    """Test service chaos injector."""

    def test_injector_initialization(self):
        injector = ServiceChaosInjector()
        assert injector is not None

    def test_simulate_downtime(self):
        injector = ServiceChaosInjector()
        config = ServiceChaosConfig(
            service_name="test-service",
            downtime_seconds=1,
        )

        result = injector.simulate_downtime(
            experiment_id="svc-test-001",
            config=config,
            duration_seconds=3,
        )

        assert result.experiment_id == "svc-test-001"
        assert result.status in [ExperimentStatus.COMPLETED, ExperimentStatus.FAILED]

    def test_inject_error_rate(self):
        injector = ServiceChaosInjector()

        @injector.inject_error_rate(error_rate_percent=100.0)
        def test_function():
            return "success"

        with pytest.raises(Exception):
            test_function()

    def test_inject_latency_degradation(self):
        injector = ServiceChaosInjector()

        @injector.inject_latency_degradation(latency_increase_ms=100)
        def test_function():
            return "success"

        start = time.time()
        result = test_function()
        elapsed = time.time() - start

        assert result == "success"
        assert elapsed >= 0.09

    def test_simulate_cascading_failure(self):
        injector = ServiceChaosInjector()

        result = injector.simulate_cascading_failure(
            experiment_id="cascade-test",
            primary_service="service-a",
            downstream_services=["service-b", "service-c"],
            failure_delay_seconds=1,
        )

        assert result.experiment_id == "cascade-test"
        assert len(result.observations) >= 3  # Primary + 2 downstream

    def test_inject_resource_pressure(self):
        injector = ServiceChaosInjector()

        @injector.inject_resource_pressure(cpu_load_percent=50)
        def test_function():
            return "success"

        result = test_function()
        assert result == "success"


class TestResourceChaosInjector:
    """Test resource chaos injector."""

    def test_injector_initialization(self):
        injector = ResourceChaosInjector()
        assert injector is not None

    def test_exhaust_cpu_short_duration(self):
        injector = ResourceChaosInjector()
        config = ResourceChaosConfig(
            cpu_cores=1,
            cpu_load_percent=50.0,
        )

        result = injector.exhaust_cpu(
            experiment_id="cpu-test",
            config=config,
            duration_seconds=1,
        )

        assert result.experiment_id == "cpu-test"
        assert result.status in [ExperimentStatus.COMPLETED, ExperimentStatus.FAILED]

    def test_consume_memory_short_duration(self):
        injector = ResourceChaosInjector()
        config = ResourceChaosConfig(memory_mb=10)

        result = injector.consume_memory(
            experiment_id="mem-test",
            config=config,
            duration_seconds=1,
        )

        assert result.experiment_id == "mem-test"
        assert result.status in [ExperimentStatus.COMPLETED, ExperimentStatus.FAILED]

    def test_saturate_disk_io_short_duration(self):
        injector = ResourceChaosInjector()
        config = ResourceChaosConfig(disk_io_mbps=1)

        result = injector.saturate_disk_io(
            experiment_id="disk-test",
            config=config,
            duration_seconds=1,
        )

        assert result.experiment_id == "disk-test"
        assert result.status in [ExperimentStatus.COMPLETED, ExperimentStatus.FAILED]


class TestGameDayOrchestrator:
    """Test GameDay orchestrator."""

    def test_orchestrator_initialization(self):
        orchestrator = GameDayOrchestrator()
        assert orchestrator is not None

    def test_create_scenario(self):
        orchestrator = GameDayOrchestrator()

        experiments = [
            ChaosExperiment(
                id="exp1",
                name="Test 1",
                chaos_type=ChaosType.NETWORK_LATENCY,
                target_service="test",
            )
        ]

        scenario = orchestrator.create_scenario(
            name="Test GameDay",
            description="Test scenario",
            objectives=["Test objective"],
            experiments=experiments,
            parallel=False,
            stop_on_failure=True,
        )

        assert scenario.name == "Test GameDay"
        assert len(scenario.experiments) == 1
        assert scenario.parallel_execution is False

    def test_run_gameday_simple(self):
        orchestrator = GameDayOrchestrator()

        experiments = [
            ChaosExperiment(
                id="latency-test",
                name="Latency Test",
                chaos_type=ChaosType.NETWORK_LATENCY,
                network_config=NetworkChaosConfig(latency_ms=10),
                target_service="test",
                duration_seconds=1,
            )
        ]

        scenario = orchestrator.create_scenario(
            name="Simple GameDay",
            description="Test",
            objectives=["Test resilience"],
            experiments=experiments,
        )

        result = orchestrator.run_gameday(scenario)

        assert result.scenario_id == scenario.id
        assert len(result.experiment_results) >= 0

    def test_generate_report(self):
        orchestrator = GameDayOrchestrator()

        experiments = [
            ChaosExperiment(
                id="test",
                name="Test",
                chaos_type=ChaosType.NETWORK_LATENCY,
                target_service="test",
            )
        ]

        scenario = orchestrator.create_scenario(
            name="Report Test",
            description="Test",
            objectives=["Test"],
            experiments=experiments,
        )

        orchestrator.run_gameday(scenario)
        report = orchestrator.generate_report(scenario.id)

        assert "scenario" in report
        assert "execution" in report
        assert "results" in report


class TestRecoveryValidator:
    """Test recovery validator."""

    def test_validator_initialization(self):
        validator = RecoveryValidator()
        assert validator is not None
        assert validator.health_history == []

    def test_create_health_check(self):
        validator = RecoveryValidator()
        config = validator.create_health_check(
            endpoint="https://example.com/health",
            interval_seconds=5,
            success_rate_threshold=95.0,
        )

        assert config.endpoint == "https://example.com/health"
        assert config.interval_seconds == 5
        assert config.success_rate_threshold == 95.0

    def test_validate_experiment_result_success(self):
        validator = RecoveryValidator()
        result = ChaosResult(
            experiment_id="test",
            error_rate_percent=10.0,
            health_check_success_rate=98.0,
        )

        is_valid = validator.validate_experiment_result(result, max_error_rate=50.0)
        assert is_valid is True

    def test_validate_experiment_result_failure(self):
        validator = RecoveryValidator()
        result = ChaosResult(
            experiment_id="test",
            error_rate_percent=60.0,
            health_check_success_rate=98.0,
        )

        is_valid = validator.validate_experiment_result(result, max_error_rate=50.0)
        assert is_valid is False
        assert len(result.failed_assertions) > 0

    def test_clear_history(self):
        validator = RecoveryValidator()
        validator.health_history.append({"test": "data"})

        validator.clear_history()
        assert validator.health_history == []


class TestChaosModels:
    """Test chaos data models."""

    def test_network_chaos_config(self):
        config = NetworkChaosConfig(
            latency_ms=100,
            jitter_ms=10,
            packet_loss_percent=5.0,
        )

        assert config.latency_ms == 100
        assert config.jitter_ms == 10
        assert config.packet_loss_percent == 5.0

    def test_service_chaos_config(self):
        config = ServiceChaosConfig(
            service_name="test-service",
            downtime_seconds=30,
            error_rate_percent=25.0,
        )

        assert config.service_name == "test-service"
        assert config.downtime_seconds == 30
        assert config.error_rate_percent == 25.0

    def test_resource_chaos_config(self):
        config = ResourceChaosConfig(
            cpu_cores=2,
            cpu_load_percent=90.0,
            memory_mb=1024,
        )

        assert config.cpu_cores == 2
        assert config.cpu_load_percent == 90.0
        assert config.memory_mb == 1024

    def test_chaos_experiment_creation(self):
        experiment = ChaosExperiment(
            id="exp-001",
            name="Test Experiment",
            chaos_type=ChaosType.NETWORK_LATENCY,
            network_config=NetworkChaosConfig(latency_ms=100),
            target_service="test-service",
        )

        assert experiment.id == "exp-001"
        assert experiment.name == "Test Experiment"
        assert experiment.chaos_type == ChaosType.NETWORK_LATENCY

    def test_chaos_result_creation(self):
        result = ChaosResult(
            experiment_id="exp-001",
            status=ExperimentStatus.COMPLETED,
            requests_total=100,
            requests_success=95,
        )

        assert result.experiment_id == "exp-001"
        assert result.status == ExperimentStatus.COMPLETED
        assert result.requests_total == 100
        assert result.requests_success == 95

    def test_gameday_scenario_creation(self):
        scenario = GameDayScenario(
            id="gd-001",
            name="Test GameDay",
            description="Test scenario",
            objectives=["Test objective 1", "Test objective 2"],
        )

        assert scenario.id == "gd-001"
        assert scenario.name == "Test GameDay"
        assert len(scenario.objectives) == 2


class TestChaosIntegration:
    """Integration tests for chaos module."""

    def test_full_chaos_workflow(self):
        """Test complete chaos engineering workflow."""
        # Network chaos
        network_injector = NetworkChaosInjector()
        network_result = network_injector.run_experiment(
            experiment_id="net-int-test",
            config=NetworkChaosConfig(latency_ms=10),
            target_service="test",
            duration_seconds=1,
        )

        # Validate result structure
        assert network_result.experiment_id is not None
        assert network_result.status is not None

        # Service chaos
        service_injector = ServiceChaosInjector()
        service_result = service_injector.simulate_downtime(
            experiment_id="svc-int-test",
            config=ServiceChaosConfig(service_name="test", downtime_seconds=1),
            duration_seconds=2,
        )

        assert service_result.experiment_id is not None

    def test_gameday_with_recovery(self):
        """Test GameDay with recovery validation."""
        orchestrator = GameDayOrchestrator()
        validator = RecoveryValidator()

        # Create simple scenario
        experiments = [
            ChaosExperiment(
                id="latency",
                name="Latency",
                chaos_type=ChaosType.NETWORK_LATENCY,
                network_config=NetworkChaosConfig(latency_ms=10),
                target_service="test",
                duration_seconds=1,
            )
        ]

        scenario = orchestrator.create_scenario(
            name="Integration GameDay",
            description="Test",
            objectives=["Test recovery"],
            experiments=experiments,
        )

        # Run GameDay
        result = orchestrator.run_gameday(scenario)

        # Verify results
        assert result.scenario_id == scenario.id
        assert result.started_at is not None
