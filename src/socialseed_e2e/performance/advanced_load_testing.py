"""Advanced Load Testing for Enterprise Performance Testing.

This module provides comprehensive load testing capabilities including:
- Spike testing: Sudden traffic surges
- Stress testing: Finding breaking points
- Endurance testing: Long-duration stability
- Volume testing: Large data handling
- Ramp testing: Gradual load increase

Example:
    >>> from socialseed_e2e.performance import AdvancedLoadTester, LoadPattern
    >>> tester = AdvancedLoadTester()
    >>> result = tester.spike_test(target_func, base_users=10, spike_users=1000)
"""

import asyncio
import logging
import random
import statistics
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class LoadTestType(Enum):
    """Types of load tests."""

    CONSTANT = "constant"  # Steady load
    SPIKE = "spike"  # Sudden traffic surge
    STRESS = "stress"  # Gradual increase to breaking point
    ENDURANCE = "endurance"  # Long-duration test
    VOLUME = "volume"  # Large data volume
    RAMP = "ramp"  # Gradual ramp up/down
    SOAK = "soak"  # Extended duration test


@dataclass
class LoadTestConfig:
    """Configuration for load tests."""

    test_type: LoadTestType
    duration_seconds: int = 60
    target_rps: Optional[int] = None
    max_concurrent_users: int = 100
    ramp_up_seconds: int = 10
    ramp_down_seconds: int = 10
    think_time_ms: Tuple[int, int] = (100, 500)  # Min, max think time
    enable_think_time: bool = True
    data_volume_mb: Optional[int] = None  # For volume tests
    spike_multiplier: float = 10.0  # For spike tests

    # Thresholds
    max_latency_ms: float = 1000.0
    max_error_rate: float = 5.0
    min_success_rate: float = 95.0


@dataclass
class RequestMetrics:
    """Metrics for a single request."""

    timestamp: float
    latency_ms: float
    success: bool
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    bytes_transferred: int = 0
    user_id: int = 0


@dataclass
class LoadTestResult:
    """Complete results from a load test."""

    test_type: LoadTestType
    config: LoadTestConfig
    start_time: datetime
    end_time: Optional[datetime] = None
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    requests_per_second: float = 0.0

    # Latency metrics
    latencies_ms: List[float] = field(default_factory=list)
    min_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    avg_latency_ms: float = 0.0
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0

    # Error metrics
    error_count: int = 0
    error_rate: float = 0.0
    errors_by_type: Dict[str, int] = field(default_factory=dict)

    # Throughput metrics
    total_bytes_transferred: int = 0
    throughput_mbps: float = 0.0

    # Time-series data
    timeseries_data: List[Dict[str, Any]] = field(default_factory=list)

    # Test-specific metrics
    breaking_point_reached: bool = False
    breaking_point_users: Optional[int] = None
    stability_issues: List[str] = field(default_factory=list)

    def calculate_statistics(self) -> None:
        """Calculate all statistical metrics."""
        if not self.latencies_ms:
            return

        sorted_latencies = sorted(self.latencies_ms)
        n = len(sorted_latencies)

        self.min_latency_ms = sorted_latencies[0]
        self.max_latency_ms = sorted_latencies[-1]
        self.avg_latency_ms = statistics.mean(sorted_latencies)
        self.p50_latency_ms = sorted_latencies[int(n * 0.5)]
        self.p95_latency_ms = sorted_latencies[int(n * 0.95)]
        self.p99_latency_ms = sorted_latencies[int(n * 0.99)]

        # Calculate throughput
        if self.end_time:
            duration_seconds = (self.end_time - self.start_time).total_seconds()
            if duration_seconds > 0:
                self.requests_per_second = self.total_requests / duration_seconds
                self.throughput_mbps = (
                    self.total_bytes_transferred / duration_seconds
                ) / (1024 * 1024)

        # Calculate error rate
        if self.total_requests > 0:
            self.error_rate = (self.failed_requests / self.total_requests) * 100

    def passed_thresholds(self) -> bool:
        """Check if test passed all thresholds."""
        return (
            self.avg_latency_ms <= self.config.max_latency_ms
            and self.error_rate <= self.config.max_error_rate
            and (self.successful_requests / max(self.total_requests, 1) * 100)
            >= self.config.min_success_rate
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "test_type": self.test_type.value,
            "duration_seconds": (self.end_time - self.start_time).total_seconds(),
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "requests_per_second": round(self.requests_per_second, 2),
            "latency": {
                "min_ms": round(self.min_latency_ms, 2),
                "avg_ms": round(self.avg_latency_ms, 2),
                "max_ms": round(self.max_latency_ms, 2),
                "p50_ms": round(self.p50_latency_ms, 2),
                "p95_ms": round(self.p95_latency_ms, 2),
                "p99_ms": round(self.p99_latency_ms, 2),
            },
            "errors": {
                "count": self.error_count,
                "rate_pct": round(self.error_rate, 2),
                "by_type": self.errors_by_type,
            },
            "throughput": {
                "total_bytes": self.total_bytes_transferred,
                "mbps": round(self.throughput_mbps, 2),
            },
            "passed_thresholds": self.passed_thresholds(),
            "breaking_point": {
                "reached": self.breaking_point_reached,
                "users": self.breaking_point_users,
            }
            if self.breaking_point_reached
            else None,
        }


class AdvancedLoadTester:
    """Advanced load testing with multiple test types.

    Supports:
    - Constant load: Steady traffic
    - Spike testing: Sudden surges
    - Stress testing: Finding breaking points
    - Endurance testing: Long-duration stability
    - Volume testing: Large data handling
    - Ramp testing: Gradual changes

    Example:
        >>> tester = AdvancedLoadTester()
        >>>
        >>> # Spike test
        >>> result = tester.spike_test(
        ...     target_func=my_api_call,
        ...     base_users=10,
        ...     spike_users=1000,
        ...     spike_duration=30
        ... )
        >>>
        >>> # Stress test
        >>> result = tester.stress_test(
        ...     target_func=my_api_call,
        ...     start_users=10,
        ...     max_users=1000,
        ...     step_users=50,
        ...     step_duration=60
        ... )
    """

    def __init__(self):
        """Initialize the advanced load tester."""
        self.results: List[LoadTestResult] = []

    async def _execute_request(
        self, target_func: Callable, user_id: int, result: LoadTestResult
    ) -> None:
        """Execute a single request and record metrics."""
        start_time = time.perf_counter()

        try:
            if asyncio.iscoroutinefunction(target_func):
                response = await target_func()
            else:
                response = target_func()

            latency_ms = (time.perf_counter() - start_time) * 1000

            # Determine success
            success = True
            status_code = None
            bytes_transferred = 0

            if isinstance(response, dict):
                status_code = response.get("status_code", 200)
                success = 200 <= status_code < 300
                bytes_transferred = len(str(response).encode())

            metric = RequestMetrics(
                timestamp=start_time,
                latency_ms=latency_ms,
                success=success,
                status_code=status_code,
                bytes_transferred=bytes_transferred,
                user_id=user_id,
            )

            result.latencies_ms.append(latency_ms)
            result.total_bytes_transferred += bytes_transferred

            if success:
                result.successful_requests += 1
            else:
                result.failed_requests += 1
                result.error_count += 1
                error_type = f"HTTP_{status_code}"
                result.errors_by_type[error_type] = (
                    result.errors_by_type.get(error_type, 0) + 1
                )

        except Exception as e:
            result.failed_requests += 1
            result.error_count += 1
            error_msg = str(e)
            result.errors_by_type[error_msg] = (
                result.errors_by_type.get(error_msg, 0) + 1
            )

        finally:
            result.total_requests += 1

    async def _user_worker(
        self,
        user_id: int,
        target_func: Callable,
        stop_event: asyncio.Event,
        result: LoadTestResult,
        think_time: Tuple[int, int],
    ) -> None:
        """Worker simulating a single user."""
        while not stop_event.is_set():
            await self._execute_request(target_func, user_id, result)

            # Add think time
            if result.config.enable_think_time:
                think_ms = random.randint(think_time[0], think_time[1])
                await asyncio.sleep(think_ms / 1000)

    async def constant_load_test(
        self,
        target_func: Callable,
        users: int,
        duration_seconds: int,
        config: Optional[LoadTestConfig] = None,
    ) -> LoadTestResult:
        """Run constant load test.

        Args:
            target_func: Function to call
            users: Number of concurrent users
            duration_seconds: Test duration
            config: Optional configuration

        Returns:
            LoadTestResult with metrics
        """
        logger.info(
            f"Starting constant load test: {users} users for {duration_seconds}s"
        )

        config = config or LoadTestConfig(
            test_type=LoadTestType.CONSTANT,
            duration_seconds=duration_seconds,
            max_concurrent_users=users,
        )

        result = LoadTestResult(
            test_type=LoadTestType.CONSTANT, config=config, start_time=datetime.utcnow()
        )

        stop_event = asyncio.Event()
        tasks = [
            asyncio.create_task(
                self._user_worker(
                    i, target_func, stop_event, result, config.think_time_ms
                )
            )
            for i in range(users)
        ]

        # Run for specified duration
        await asyncio.sleep(duration_seconds)
        stop_event.set()

        await asyncio.gather(*tasks, return_exceptions=True)

        result.end_time = datetime.utcnow()
        result.calculate_statistics()
        self.results.append(result)

        logger.info(
            f"Constant load test complete: {result.requests_per_second:.2f} RPS"
        )
        return result

    async def spike_test(
        self,
        target_func: Callable,
        base_users: int,
        spike_users: int,
        base_duration: int = 60,
        spike_duration: int = 30,
        recovery_duration: int = 60,
        config: Optional[LoadTestConfig] = None,
    ) -> LoadTestResult:
        """Run spike test with sudden traffic surge.

        Args:
            target_func: Function to call
            base_users: Normal load users
            spike_users: Peak load users
            base_duration: Duration of base load phase
            spike_duration: Duration of spike phase
            recovery_duration: Duration of recovery phase
            config: Optional configuration

        Returns:
            LoadTestResult with metrics
        """
        logger.info(
            f"Starting spike test: {base_users} -> {spike_users} users "
            f"for {spike_duration}s"
        )

        config = config or LoadTestConfig(
            test_type=LoadTestType.SPIKE,
            duration_seconds=base_duration + spike_duration + recovery_duration,
        )

        result = LoadTestResult(
            test_type=LoadTestType.SPIKE, config=config, start_time=datetime.utcnow()
        )

        stop_event = asyncio.Event()
        current_users = base_users
        all_tasks = []

        async def update_users(target_users: int, duration: int, phase: str):
            """Update number of active users."""
            nonlocal current_users, all_tasks

            # Cancel excess tasks
            while len(all_tasks) > target_users:
                task = all_tasks.pop()
                task.cancel()

            # Add new tasks
            while len(all_tasks) < target_users:
                user_id = len(all_tasks)
                task = asyncio.create_task(
                    self._user_worker(
                        user_id, target_func, stop_event, result, config.think_time_ms
                    )
                )
                all_tasks.append(task)

            current_users = target_users
            logger.info(f"{phase}: {current_users} users active")

            # Record timeseries data
            result.timeseries_data.append(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "phase": phase,
                    "users": current_users,
                    "rps": result.requests_per_second,
                    "avg_latency": result.avg_latency_ms,
                }
            )

            await asyncio.sleep(duration)

        # Base load phase
        await update_users(base_users, base_duration, "BASE")

        # Spike phase
        await update_users(spike_users, spike_duration, "SPIKE")

        # Recovery phase
        await update_users(base_users, recovery_duration, "RECOVERY")

        stop_event.set()
        await asyncio.gather(*all_tasks, return_exceptions=True)

        result.end_time = datetime.utcnow()
        result.calculate_statistics()
        self.results.append(result)

        logger.info(f"Spike test complete: peak={spike_users} users")
        return result

    async def stress_test(
        self,
        target_func: Callable,
        start_users: int = 10,
        max_users: int = 1000,
        step_users: int = 50,
        step_duration: int = 60,
        config: Optional[LoadTestConfig] = None,
    ) -> LoadTestResult:
        """Run stress test to find breaking point.

        Gradually increases load until errors exceed threshold
        or max users reached.

        Args:
            target_func: Function to call
            start_users: Starting user count
            max_users: Maximum user count
            step_users: Users to add per step
            step_duration: Duration of each step
            config: Optional configuration

        Returns:
            LoadTestResult with metrics
        """
        logger.info(
            f"Starting stress test: {start_users} -> {max_users} users "
            f"in steps of {step_users}"
        )

        config = config or LoadTestConfig(
            test_type=LoadTestType.STRESS, max_concurrent_users=max_users
        )

        result = LoadTestResult(
            test_type=LoadTestType.STRESS, config=config, start_time=datetime.utcnow()
        )

        stop_event = asyncio.Event()
        all_tasks = []
        current_users = 0
        breaking_point_found = False

        for users in range(start_users, max_users + 1, step_users):
            if breaking_point_found:
                break

            # Add tasks for this step
            while len(all_tasks) < users:
                user_id = len(all_tasks)
                task = asyncio.create_task(
                    self._user_worker(
                        user_id, target_func, stop_event, result, config.think_time_ms
                    )
                )
                all_tasks.append(task)

            current_users = users
            logger.info(f"Stress step: {current_users} users")

            # Wait for step duration
            await asyncio.sleep(step_duration)

            # Check if we've reached breaking point
            result.calculate_statistics()
            if result.error_rate > config.max_error_rate:
                logger.warning(f"Breaking point found at {current_users} users")
                result.breaking_point_reached = True
                result.breaking_point_users = current_users
                breaking_point_found = True

                # Add stability issues
                result.stability_issues.append(
                    f"Error rate {result.error_rate:.1f}% exceeds threshold "
                    f"{config.max_error_rate}% at {current_users} users"
                )

            # Record timeseries
            result.timeseries_data.append(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "users": current_users,
                    "error_rate": result.error_rate,
                    "avg_latency": result.avg_latency_ms,
                }
            )

        stop_event.set()
        await asyncio.gather(*all_tasks, return_exceptions=True)

        result.end_time = datetime.utcnow()
        result.calculate_statistics()
        self.results.append(result)

        logger.info(
            f"Stress test complete: breaking_point={result.breaking_point_users}"
        )
        return result

    async def endurance_test(
        self,
        target_func: Callable,
        users: int,
        duration_hours: int,
        checkpoint_interval_minutes: int = 30,
        config: Optional[LoadTestConfig] = None,
    ) -> LoadTestResult:
        """Run endurance test for extended duration.

        Tests system stability over long periods.

        Args:
            target_func: Function to call
            users: Concurrent users
            duration_hours: Test duration in hours
            checkpoint_interval_minutes: Interval for metrics checkpoints
            config: Optional configuration

        Returns:
            LoadTestResult with metrics
        """
        total_seconds = duration_hours * 3600
        logger.info(f"Starting endurance test: {users} users for {duration_hours}h")

        config = config or LoadTestConfig(
            test_type=LoadTestType.ENDURANCE,
            duration_seconds=total_seconds,
            max_concurrent_users=users,
        )

        result = LoadTestResult(
            test_type=LoadTestType.ENDURANCE,
            config=config,
            start_time=datetime.utcnow(),
        )

        stop_event = asyncio.Event()
        checkpoint_interval = checkpoint_interval_minutes * 60

        # Start all workers
        tasks = [
            asyncio.create_task(
                self._user_worker(
                    i, target_func, stop_event, result, config.think_time_ms
                )
            )
            for i in range(users)
        ]

        # Monitor checkpoints
        start_time = time.perf_counter()
        last_checkpoint = start_time

        while (time.perf_counter() - start_time) < total_seconds:
            await asyncio.sleep(1)

            # Record checkpoint
            if (time.perf_counter() - last_checkpoint) >= checkpoint_interval:
                result.calculate_statistics()
                result.timeseries_data.append(
                    {
                        "timestamp": datetime.utcnow().isoformat(),
                        "elapsed_minutes": (time.perf_counter() - start_time) / 60,
                        "users": users,
                        "error_rate": result.error_rate,
                        "avg_latency": result.avg_latency_ms,
                        "memory_stable": True,  # Placeholder
                    }
                )

                # Check for stability issues
                if result.error_rate > config.max_error_rate:
                    result.stability_issues.append(
                        f"High error rate at {(time.perf_counter() - start_time) / 60:.0f}min: "
                        f"{result.error_rate:.1f}%"
                    )

                last_checkpoint = time.perf_counter()
                logger.info(
                    f"Endurance checkpoint: {result.requests_per_second:.2f} RPS, "
                    f"{result.error_rate:.2f}% errors"
                )

        stop_event.set()
        await asyncio.gather(*tasks, return_exceptions=True)

        result.end_time = datetime.utcnow()
        result.calculate_statistics()
        self.results.append(result)

        logger.info(
            f"Endurance test complete: {len(result.stability_issues)} issues found"
        )
        return result

    async def volume_test(
        self,
        target_func: Callable,
        target_data_mb: int,
        users: int = 10,
        config: Optional[LoadTestConfig] = None,
    ) -> LoadTestResult:
        """Run volume test with large data transfer.

        Args:
            target_func: Function returning large data
            target_data_mb: Target data to transfer in MB
            users: Concurrent users
            config: Optional configuration

        Returns:
            LoadTestResult with metrics
        """
        logger.info(f"Starting volume test: {target_data_mb}MB with {users} users")

        config = config or LoadTestConfig(
            test_type=LoadTestType.VOLUME,
            max_concurrent_users=users,
            data_volume_mb=target_data_mb,
        )

        result = LoadTestResult(
            test_type=LoadTestType.VOLUME, config=config, start_time=datetime.utcnow()
        )

        stop_event = asyncio.Event()
        target_bytes = target_data_mb * 1024 * 1024

        tasks = [
            asyncio.create_task(
                self._user_worker(
                    i,
                    target_func,
                    stop_event,
                    result,
                    (0, 0),  # No think time
                )
            )
            for i in range(users)
        ]

        # Run until target data transferred
        while result.total_bytes_transferred < target_bytes and not stop_event.is_set():
            await asyncio.sleep(1)

            # Check for timeout (safety)
            elapsed = (datetime.utcnow() - result.start_time).total_seconds()
            if elapsed > 3600:  # 1 hour max
                logger.warning("Volume test timeout reached")
                break

        stop_event.set()
        await asyncio.gather(*tasks, return_exceptions=True)

        result.end_time = datetime.utcnow()
        result.calculate_statistics()
        self.results.append(result)

        logger.info(
            f"Volume test complete: {result.total_bytes_transferred / (1024 * 1024):.2f}MB "
            f"at {result.throughput_mbps:.2f} Mbps"
        )
        return result

    async def ramp_test(
        self,
        target_func: Callable,
        start_users: int,
        end_users: int,
        ramp_up_duration: int,
        steady_duration: int,
        ramp_down_duration: int,
        config: Optional[LoadTestConfig] = None,
    ) -> LoadTestResult:
        """Run ramp test with gradual load changes.

        Tests system response to gradual increases and decreases.

        Args:
            target_func: Function to call
            start_users: Starting users
            end_users: Peak users
            ramp_up_duration: Ramp up duration in seconds
            steady_duration: Steady state duration
            ramp_down_duration: Ramp down duration in seconds
            config: Optional configuration

        Returns:
            LoadTestResult with metrics
        """
        total_duration = ramp_up_duration + steady_duration + ramp_down_duration
        logger.info(
            f"Starting ramp test: {start_users} -> {end_users} -> {start_users} "
            f"over {total_duration}s"
        )

        config = config or LoadTestConfig(
            test_type=LoadTestType.RAMP, duration_seconds=total_duration
        )

        result = LoadTestResult(
            test_type=LoadTestType.RAMP, config=config, start_time=datetime.utcnow()
        )

        stop_event = asyncio.Event()
        all_tasks = []

        async def ramp_users(start: int, end: int, duration: int, phase: str):
            """Ramp users from start to end over duration."""
            steps = max(1, duration)
            users_per_step = (end - start) / steps

            for step in range(steps):
                target_users = int(start + (users_per_step * step))

                # Adjust tasks
                while len(all_tasks) < target_users:
                    user_id = len(all_tasks)
                    task = asyncio.create_task(
                        self._user_worker(
                            user_id,
                            target_func,
                            stop_event,
                            result,
                            config.think_time_ms,
                        )
                    )
                    all_tasks.append(task)

                while len(all_tasks) > target_users:
                    task = all_tasks.pop()
                    task.cancel()

                # Record timeseries
                result.timeseries_data.append(
                    {
                        "timestamp": datetime.utcnow().isoformat(),
                        "phase": phase,
                        "users": len(all_tasks),
                        "rps": result.requests_per_second,
                    }
                )

                await asyncio.sleep(1)

        # Ramp up
        await ramp_users(start_users, end_users, ramp_up_duration, "RAMP_UP")

        # Steady state
        await asyncio.sleep(steady_duration)

        # Ramp down
        await ramp_users(end_users, start_users, ramp_down_duration, "RAMP_DOWN")

        stop_event.set()
        await asyncio.gather(*all_tasks, return_exceptions=True)

        result.end_time = datetime.utcnow()
        result.calculate_statistics()
        self.results.append(result)

        logger.info(f"Ramp test complete: peak={end_users} users")
        return result

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all test results."""
        return {
            "total_tests": len(self.results),
            "tests_by_type": {
                test_type.value: len(
                    [r for r in self.results if r.test_type == test_type]
                )
                for test_type in LoadTestType
            },
            "passed_thresholds": len(
                [r for r in self.results if r.passed_thresholds()]
            ),
            "failed_thresholds": len(
                [r for r in self.results if not r.passed_thresholds()]
            ),
            "breaking_points_found": len(
                [r for r in self.results if r.breaking_point_reached]
            ),
        }
