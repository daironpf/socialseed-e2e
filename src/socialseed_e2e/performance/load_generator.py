"""Load generation utilities for socialseed-e2e.

Provides tools for distributed load testing and custom load patterns.
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List


@dataclass
class LoadTestResult:
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    latencies: List[float] = field(default_factory=list)
    errors: Dict[str, int] = field(default_factory=dict)
    start_time: float = 0.0
    end_time: float = 0.0

    @property
    def rps(self) -> float:
        duration = self.end_time - self.start_time
        return self.total_requests / duration if duration > 0 else 0.0

    @property
    def avg_latency(self) -> float:
        return sum(self.latencies) / len(self.latencies) if self.latencies else 0.0


class LoadGenerator:
    """Generates load using asynchronous tasks."""

    def __init__(self, target_func: Callable[[], Any]):
        self.target_func = target_func
        self.results = LoadTestResult()

    async def _worker(self, stop_event: asyncio.Event):
        """Single worker executing requests."""
        while not stop_event.is_set():
            start = time.perf_counter()
            try:
                if asyncio.iscoroutinefunction(self.target_func):
                    await self.target_func()
                else:
                    self.target_func()

                latency = (time.perf_counter() - start) * 1000
                self.results.latencies.append(latency)
                self.results.successful_requests += 1
            except Exception as e:
                err_msg = str(e)
                self.results.errors[err_msg] = self.results.errors.get(err_msg, 0) + 1
                self.results.failed_requests += 1
            finally:
                self.results.total_requests += 1

    async def run_constant_load(self, users: int, duration_seconds: int):
        """Run load with a constant number of concurrent users."""
        print(f"Starting load test: {users} users for {duration_seconds}s")
        self.results = LoadTestResult()
        self.results.start_time = time.perf_counter()

        stop_event = asyncio.Event()
        tasks = [asyncio.create_task(self._worker(stop_event)) for _ in range(users)]

        await asyncio.sleep(duration_seconds)
        stop_event.set()

        await asyncio.gather(*tasks)
        self.results.end_time = time.perf_counter()
        return self.results

    async def run_ramp_up(self, start_users: int, end_users: int, ramp_duration: int, steady_duration: int):
        """Ramp up users over time."""
        print(f"Ramping up: {start_users} -> {end_users} users over {ramp_duration}s")
        self.results = LoadTestResult()
        self.results.start_time = time.perf_counter()

        stop_event = asyncio.Event()
        workers = []

        # Initial workers
        for _ in range(start_users):
            workers.append(asyncio.create_task(self._worker(stop_event)))

        # Ramping
        if end_users > start_users:
            spawn_interval = ramp_duration / (end_users - start_users)
            for _ in range(end_users - start_users):
                await asyncio.sleep(spawn_interval)
                workers.append(asyncio.create_task(self._worker(stop_event)))

        await asyncio.sleep(steady_duration)
        stop_event.set()
        await asyncio.gather(*workers)

        self.results.end_time = time.perf_counter()
        return self.results
