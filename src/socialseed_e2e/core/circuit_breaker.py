"""Circuit Breaker pattern for API testing.

This module provides a CircuitBreaker class to prevent making requests
to a service that is known to be failing, improving test suite stability.
"""

import logging
import time
from enum import Enum
from threading import Lock
from typing import Optional, List, Type

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    """Possible states of a circuit breaker."""
    CLOSED = "CLOSED"  # Normal operation, requests allowed
    OPEN = "OPEN"      # Failing, requests blocked
    HALF_OPEN = "HALF_OPEN"  # Testing if service is back up

class CircuitBreaker:
    """Circuit Breaker to prevent cascading failures.
    
    Attributes:
        failure_threshold: Number of failures before opening the circuit
        recovery_timeout: Seconds to wait before transitioning to HALF_OPEN
        expected_exceptions: Exceptions that count towards failure
        expected_status_codes: Status codes that count towards failure
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        expected_exceptions: Optional[List[Type[Exception]]] = None,
        expected_status_codes: Optional[List[int]] = None,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exceptions = expected_exceptions or [Exception]
        self.expected_status_codes = expected_status_codes or [500, 502, 503, 504]
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self._lock = Lock()

    def can_execute(self) -> bool:
        """Check if a request can be executed."""
        with self._lock:
            if self.state == CircuitState.CLOSED:
                return True
            
            if self.state == CircuitState.OPEN:
                now = time.time()
                if self.last_failure_time and (now - self.last_failure_time) > self.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                    logger.info("Circuit Breaker transitioned to HALF_OPEN")
                    return True
                return False
            
            if self.state == CircuitState.HALF_OPEN:
                # In half-open, we allow one request to test recovery
                return True
                
            return False

    def record_success(self):
        """Record a successful request."""
        with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                logger.info("Circuit Breaker transitioned to CLOSED (Recovered)")
            
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.last_failure_time = None

    def record_failure(self, exception: Optional[Exception] = None, status_code: Optional[int] = None):
        """Record a failed request."""
        should_count = False
        
        if exception:
            if any(isinstance(exception, exc_type) for exc_type in self.expected_exceptions):
                should_count = True
        
        if status_code:
            if status_code in self.expected_status_codes:
                should_count = True
                
        if not should_count:
            return

        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                if self.state != CircuitState.OPEN:
                    logger.error(f"Circuit Breaker transitioned to OPEN (threshold {self.failure_threshold} reached)")
                self.state = CircuitState.OPEN
    
    def reset(self):
        """Manually reset the circuit breaker."""
        with self._lock:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.last_failure_time = None
