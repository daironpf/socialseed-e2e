"""Network disruption tools for Chaos Engineering."""

import time
import random
from typing import Optional, Callable, Any
from functools import wraps


class NetworkChaos:
    """Simulates network issues like latency and connectivity drops."""

    def __init__(self):
        self.latency_ms = 0
        self.jitter_ms = 0
        self.failure_rate = 0.0  # 0.0 to 1.0

    def configure(self, latency: int = 0, jitter: int = 0, failure_rate: float = 0.0):
        """Configure chaos parameters.
        
        Args:
            latency: Fixed latency in milliseconds.
            jitter: Random variance in latency in milliseconds.
            failure_rate: Probability of request failure (0.0 to 1.0).
        """
        self.latency_ms = latency
        self.jitter_ms = jitter
        self.failure_rate = failure_rate

    def inject(self, func: Callable) -> Callable:
        """Decorator to inject network chaos into an API call."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Simulate total network failure
            if self.failure_rate > 0 and random.random() < self.failure_rate:
                raise ConnectionError("Chaos Engineering: Simulated network failure")

            # Simulate latency
            total_latency = self.latency_ms
            if self.jitter_ms > 0:
                total_latency += random.randint(-self.jitter_ms, self.jitter_ms)
            
            if total_latency > 0:
                time.sleep(max(0, total_latency) / 1000.0)

            return func(*args, **kwargs)
        return wrapper

    def simulate_timeout(self, duration_ms: int):
        """Force a sleep to simulate a timeout."""
        time.sleep(duration_ms / 1000.0)
