"""
Service chaos injector for chaos engineering.

Provides service-level chaos injection:
- Service downtime simulation
- Error rate injection
- Latency degradation
- Cascading failure simulation
- CPU and memory pressure
"""

import random
import time
from functools import wraps
from typing import Callable, Dict, List, Optional

from ..models import (
    ChaosExperiment,
    ChaosResult,
    ChaosType,
    ExperimentStatus,
    ServiceChaosConfig,
)


class ServiceChaosInjector:
    """Service-level chaos injector for resilience testing.

    Simulates various service failures:
    - Service downtime/crashes
    - Degraded performance
    - Cascading failures
    - Resource exhaustion

    Example:
        injector = ServiceChaosInjector()

        config = ServiceChaosConfig(
            service_name="payment-service",
            downtime_seconds=30,
            error_rate_percent=25.0,
            latency_increase_ms=500
        )

        result = injector.simulate_downtime(
            experiment_id="svc-001",
            config=config,
            duration_seconds=300
        )
    """

    def __init__(self):
        """Initialize service chaos injector."""
        self.active_experiments: Dict[str, ChaosExperiment] = {}
        self.results: Dict[str, ChaosResult] = {}
        self._injected_errors: Dict[str, float] = {}
        self._injected_latency: Dict[str, int] = {}

    def simulate_downtime(
        self,
        experiment_id: str,
        config: ServiceChaosConfig,
        duration_seconds: int = 300,
    ) -> ChaosResult:
        """Simulate service downtime/crashes.

        Args:
            experiment_id: Unique experiment ID
            config: Service chaos configuration
            duration_seconds: Duration of experiment

        Returns:
            ChaosResult with experiment results
        """
        experiment = ChaosExperiment(
            id=experiment_id,
            name=f"Service Downtime - {config.service_name}",
            description=f"Simulate {config.downtime_seconds}s downtime for {config.service_name}",
            chaos_type=ChaosType.SERVICE_DOWNTIME,
            service_config=config,
            target_service=config.service_name,
            duration_seconds=duration_seconds,
        )

        self.active_experiments[experiment_id] = experiment

        result = ChaosResult(
            experiment_id=experiment_id,
            status=ExperimentStatus.RUNNING,
        )

        try:
            start_time = time.time()
            result.started_at = __import__("datetime").datetime.utcnow()

            # Simulate downtime cycles
            elapsed = 0
            downtime_cycles = 0
            requests_total = 0
            requests_success = 0

            while elapsed < duration_seconds:
                cycle_start = time.time()

                # Service is up initially
                service_up = True
                cycle_elapsed = 0

                # Simulate periodic downtime
                while cycle_elapsed < 60:  # 1-minute cycles
                    if service_up and cycle_elapsed >= random.randint(10, 30):
                        # Bring service down
                        service_up = False
                        downtime_start = cycle_elapsed

                    if (
                        not service_up
                        and cycle_elapsed - downtime_start >= config.downtime_seconds
                    ):
                        # Bring service back up
                        service_up = True
                        downtime_cycles += 1

                    # Simulate requests
                    requests_total += 1
                    if service_up:
                        requests_success += 1

                    time.sleep(0.1)
                    cycle_elapsed = time.time() - cycle_start

                elapsed = time.time() - start_time

            result.completed_at = __import__("datetime").datetime.utcnow()
            result.duration_actual_seconds = elapsed
            result.requests_total = requests_total
            result.requests_success = requests_success
            result.requests_failed = requests_total - requests_success
            result.error_rate_percent = (
                ((requests_total - requests_success) / requests_total * 100)
                if requests_total > 0
                else 0.0
            )
            result.success = result.error_rate_percent < 50.0
            result.status = ExperimentStatus.COMPLETED

            result.observations.append(f"Simulated {downtime_cycles} downtime cycles")
            result.observations.append(
                f"Each downtime lasted {config.downtime_seconds} seconds"
            )

        except Exception as e:
            result.status = ExperimentStatus.FAILED
            result.errors.append(str(e))

        self.results[experiment_id] = result
        return result

    def inject_error_rate(
        self,
        error_rate_percent: float = 10.0,
    ) -> Callable:
        """Decorator to inject error rates into service calls.

        Args:
            error_rate_percent: Percentage of requests to fail

        Returns:
            Decorator function
        """

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                if random.random() < (error_rate_percent / 100.0):
                    error_types = [
                        Exception(f"Chaos: Simulated {error_rate_percent}% error rate"),
                        TimeoutError("Chaos: Simulated timeout"),
                        ConnectionError("Chaos: Simulated connection failure"),
                    ]
                    raise random.choice(error_types)
                return func(*args, **kwargs)

            return wrapper

        return decorator

    def inject_latency_degradation(
        self,
        latency_increase_ms: int = 500,
        jitter_ms: int = 100,
    ) -> Callable:
        """Decorator to inject latency degradation.

        Args:
            latency_increase_ms: Additional latency in milliseconds
            jitter_ms: Jitter variance

        Returns:
            Decorator function
        """

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                total_latency = latency_increase_ms + random.randint(
                    -jitter_ms, jitter_ms
                )
                total_latency = max(0, total_latency)
                time.sleep(total_latency / 1000.0)
                return func(*args, **kwargs)

            return wrapper

        return decorator

    def simulate_cascading_failure(
        self,
        experiment_id: str,
        primary_service: str,
        downstream_services: List[str],
        failure_delay_seconds: int = 5,
    ) -> ChaosResult:
        """Simulate cascading failure through service dependencies.

        Args:
            experiment_id: Unique experiment ID
            primary_service: Primary service to fail
            downstream_services: List of dependent services
            failure_delay_seconds: Delay between cascading failures

        Returns:
            ChaosResult with experiment results
        """
        config = ServiceChaosConfig(
            service_name=primary_service,
            downstream_services=downstream_services,
            error_rate_percent=100.0,
        )

        experiment = ChaosExperiment(
            id=experiment_id,
            name=f"Cascading Failure - {primary_service}",
            description=f"Simulate cascading failure from {primary_service} to {', '.join(downstream_services)}",
            chaos_type=ChaosType.SERVICE_CASCADING,
            service_config=config,
            target_service=primary_service,
            duration_seconds=len(downstream_services) * failure_delay_seconds + 60,
        )

        self.active_experiments[experiment_id] = experiment

        result = ChaosResult(
            experiment_id=experiment_id,
            status=ExperimentStatus.RUNNING,
        )

        try:
            result.started_at = __import__("datetime").datetime.utcnow()

            # Simulate primary service failure
            result.observations.append(f"Primary service {primary_service} failed")
            time.sleep(failure_delay_seconds)

            # Simulate cascading failures
            for i, service in enumerate(downstream_services):
                result.observations.append(
                    f"Downstream service {service} failed (cascade level {i + 1})"
                )
                time.sleep(failure_delay_seconds)

            result.completed_at = __import__("datetime").datetime.utcnow()
            result.success = True
            result.status = ExperimentStatus.COMPLETED

        except Exception as e:
            result.status = ExperimentStatus.FAILED
            result.errors.append(str(e))

        self.results[experiment_id] = result
        return result

    def inject_resource_pressure(
        self,
        cpu_load_percent: int = 80,
        memory_pressure_mb: int = 512,
    ) -> Callable:
        """Decorator to inject CPU and memory pressure.

        Args:
            cpu_load_percent: CPU load to inject
            memory_pressure_mb: Memory pressure in MB

        Returns:
            Decorator function
        """

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Simulate resource pressure by adding delay
                # In real implementation, this would use actual resource consumption
                cpu_delay = (cpu_load_percent / 100.0) * 0.1  # 100ms max delay
                time.sleep(cpu_delay)
                return func(*args, **kwargs)

            return wrapper

        return decorator

    def stop_experiment(self, experiment_id: str) -> bool:
        """Stop a running experiment.

        Args:
            experiment_id: Experiment ID to stop

        Returns:
            True if stopped successfully
        """
        if experiment_id in self.active_experiments:
            if experiment_id in self.results:
                self.results[experiment_id].status = ExperimentStatus.STOPPED
            return True
        return False

    def get_experiment_status(self, experiment_id: str) -> Optional[ChaosResult]:
        """Get status of an experiment.

        Args:
            experiment_id: Experiment ID

        Returns:
            ChaosResult or None
        """
        return self.results.get(experiment_id)
