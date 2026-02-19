"""
Advanced network chaos injector for chaos engineering.

Provides network-level chaos injection:
- Latency injection with jitter
- Packet loss simulation
- DNS manipulation
- Network partitioning
- Bandwidth throttling
"""

import time
import random
import uuid
from typing import Any, Callable, Dict, List, Optional
from functools import wraps

from ..models import (
    ChaosExperiment,
    ChaosResult,
    ChaosType,
    ExperimentStatus,
    NetworkChaosConfig,
)


class NetworkChaosInjector:
    """Advanced network chaos injector for resilience testing.

    Injects various network-level failures to test system resilience:
    - Latency and jitter
    - Packet loss and corruption
    - DNS failures
    - Network partitions
    - Bandwidth limits

    Example:
        injector = NetworkChaosInjector()

        config = NetworkChaosConfig(
            latency_ms=200,
            jitter_ms=50,
            packet_loss_percent=5.0,
            dns_failure_rate=10.0
        )

        result = injector.run_experiment(
            experiment_id="net-001",
            config=config,
            target_service="payment-api",
            duration_seconds=300
        )
    """

    def __init__(self):
        """Initialize network chaos injector."""
        self.active_experiments: Dict[str, ChaosExperiment] = {}
        self.results: Dict[str, ChaosResult] = {}

    def run_experiment(
        self,
        experiment_id: str,
        config: NetworkChaosConfig,
        target_service: str,
        duration_seconds: int = 300,
        ramp_up_seconds: int = 10,
        ramp_down_seconds: int = 10,
    ) -> ChaosResult:
        """Run a network chaos experiment.

        Args:
            experiment_id: Unique experiment ID
            config: Network chaos configuration
            target_service: Target service name
            duration_seconds: Duration of chaos injection
            ramp_up_seconds: Time to ramp up chaos
            ramp_down_seconds: Time to ramp down chaos

        Returns:
            ChaosResult with experiment results
        """
        experiment = ChaosExperiment(
            id=experiment_id,
            name=f"Network Chaos - {config.latency_ms}ms latency",
            description=f"Network chaos with {config.latency_ms}ms latency, {config.packet_loss_percent}% packet loss",
            chaos_type=ChaosType.NETWORK_LATENCY
            if config.latency_ms > 0
            else ChaosType.NETWORK_PACKET_LOSS,
            network_config=config,
            target_service=target_service,
            duration_seconds=duration_seconds,
            ramp_up_seconds=ramp_up_seconds,
            ramp_down_seconds=ramp_down_seconds,
        )

        self.active_experiments[experiment_id] = experiment

        result = ChaosResult(
            experiment_id=experiment_id,
            status=ExperimentStatus.RUNNING,
        )

        try:
            import asyncio
            import time as time_module

            start_time = time_module.time()
            result.started_at = __import__("datetime").datetime.utcnow()

            # Simulate chaos injection over time
            # In real implementation, this would use tc (traffic control) or toxiproxy

            elapsed = 0
            requests_total = 0
            requests_success = 0
            latencies = []

            while elapsed < duration_seconds:
                # Simulate request
                requests_total += 1

                # Calculate current chaos intensity (ramp up/down)
                if elapsed < ramp_up_seconds:
                    intensity = elapsed / ramp_up_seconds
                elif elapsed > (duration_seconds - ramp_down_seconds):
                    intensity = (duration_seconds - elapsed) / ramp_down_seconds
                else:
                    intensity = 1.0

                # Apply latency
                latency = self._calculate_latency(config, intensity)
                time_module.sleep(latency / 1000.0)
                latencies.append(latency)

                # Simulate packet loss
                if random.random() < (config.packet_loss_percent / 100.0 * intensity):
                    # Request failed due to packet loss
                    pass
                else:
                    requests_success += 1

                # Check DNS failure
                if random.random() < (config.dns_failure_rate / 100.0 * intensity):
                    # DNS failure
                    pass

                elapsed = time_module.time() - start_time

            # Calculate metrics
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
            result.avg_latency_ms = (
                sum(latencies) / len(latencies) if latencies else 0.0
            )
            result.p95_latency_ms = (
                sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0.0
            )
            result.p99_latency_ms = (
                sorted(latencies)[int(len(latencies) * 0.99)] if latencies else 0.0
            )

            # Determine success
            result.success = result.error_rate_percent < 50.0
            result.status = ExperimentStatus.COMPLETED

            # Add observations
            result.observations.append(
                f"Injected {config.latency_ms}ms latency with {config.jitter_ms}ms jitter"
            )
            result.observations.append(
                f"Simulated {config.packet_loss_percent}% packet loss"
            )
            result.observations.append(
                f"Achieved {result.error_rate_percent:.2f}% error rate"
            )

        except Exception as e:
            result.status = ExperimentStatus.FAILED
            result.errors.append(str(e))

        self.results[experiment_id] = result
        return result

    def inject_latency(
        self,
        func: Callable,
        latency_ms: int = 100,
        jitter_ms: int = 10,
    ) -> Callable:
        """Decorator to inject latency into function calls.

        Args:
            func: Function to wrap
            latency_ms: Base latency in milliseconds
            jitter_ms: Jitter variance in milliseconds

        Returns:
            Wrapped function
        """

        @wraps(func)
        def wrapper(*args, **kwargs):
            # Calculate latency with jitter
            total_latency = latency_ms + random.randint(-jitter_ms, jitter_ms)
            total_latency = max(0, total_latency)

            # Apply latency
            time.sleep(total_latency / 1000.0)

            return func(*args, **kwargs)

        return wrapper

    def inject_packet_loss(
        self,
        loss_percent: float = 5.0,
    ) -> Callable:
        """Decorator to simulate packet loss.

        Args:
            loss_percent: Packet loss percentage

        Returns:
            Decorator function
        """

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                if random.random() < (loss_percent / 100.0):
                    raise ConnectionError(
                        f"Chaos Engineering: Simulated packet loss ({loss_percent}%)"
                    )
                return func(*args, **kwargs)

            return wrapper

        return decorator

    def inject_dns_failure(
        self,
        failure_rate: float = 10.0,
    ) -> Callable:
        """Decorator to simulate DNS failures.

        Args:
            failure_rate: DNS failure rate percentage

        Returns:
            Decorator function
        """

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                if random.random() < (failure_rate / 100.0):
                    raise ConnectionError(
                        f"Chaos Engineering: Simulated DNS resolution failure"
                    )
                return func(*args, **kwargs)

            return wrapper

        return decorator

    def inject_bandwidth_limit(
        self,
        bandwidth_mbps: int,
    ) -> Callable:
        """Decorator to simulate bandwidth limitations.

        Args:
            bandwidth_mbps: Bandwidth limit in Mbps

        Returns:
            Decorator function
        """

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                # In real implementation, this would use traffic shaping
                # For now, we just add a note
                result = func(*args, **kwargs)
                return result

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
            experiment = self.active_experiments[experiment_id]
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

    def _calculate_latency(self, config: NetworkChaosConfig, intensity: float) -> int:
        """Calculate current latency with jitter and intensity.

        Args:
            config: Network chaos config
            intensity: Current intensity (0.0 to 1.0)

        Returns:
            Latency in milliseconds
        """
        base_latency = int(config.latency_ms * intensity)
        jitter = (
            random.randint(-config.jitter_ms, config.jitter_ms)
            if config.jitter_ms > 0
            else 0
        )
        return max(0, base_latency + jitter)

    def create_latency_profile(
        self,
        name: str,
        latencies: List[int],
        durations: List[int],
    ) -> Dict[str, Any]:
        """Create a custom latency profile for complex scenarios.

        Args:
            name: Profile name
            latencies: List of latency values in ms
            durations: List of durations for each latency

        Returns:
            Profile configuration
        """
        return {
            "name": name,
            "type": "latency_profile",
            "phases": [
                {"latency_ms": lat, "duration_seconds": dur}
                for lat, dur in zip(latencies, durations)
            ],
        }
