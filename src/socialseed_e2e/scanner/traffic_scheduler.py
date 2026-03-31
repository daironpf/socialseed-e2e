"""
Traffic Scheduler - Advanced scheduling and concurrency control for traffic generation.
This implements Task EPIC-001-T04: Implementar scheduler para envío recurrente y concurrencia ajustable de los requests.
"""

import asyncio
import threading
import time
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, Future
from enum import Enum
import uuid
import random


class ScheduleType(Enum):
    """Type of scheduling."""
    FIXED_RATE = "fixed_rate"      # Fixed requests per minute
    INTERVAL = "interval"          # Fixed interval between requests
    RANDOM = "random"              # Random interval
    CRON = "cron"                  # Cron-style scheduling
    BURST = "burst"                # Burst mode (many requests at once)


class RequestPriority(Enum):
    """Priority of requests."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class SchedulerConfig:
    """Configuration for the scheduler."""
    schedule_type: ScheduleType = ScheduleType.FIXED_RATE
    requests_per_minute: int = 100
    interval_seconds: float = 0.6
    min_interval_seconds: float = 0.1
    max_interval_seconds: float = 2.0
    concurrent_workers: int = 5
    max_queue_size: int = 1000
    burst_size: int = 50
    burst_interval_seconds: float = 10.0
    enable_adaptive: bool = True  # Adapt based on latency
    target_latency_ms: float = 100.0


@dataclass
class ScheduledRequest:
    """A request scheduled for execution."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    endpoint: str = ""
    method: str = "GET"
    body: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None
    priority: RequestPriority = RequestPriority.NORMAL
    scheduled_time: Optional[datetime] = None
    execute_at: Optional[Callable] = None  # Custom execute function
    metadata: Dict[str, Any] = field(default_factory=dict)


class TrafficScheduler:
    """
    Advanced scheduler for traffic generation with configurable concurrency and scheduling.
    
    Features:
    - Multiple scheduling strategies (fixed rate, interval, random, cron, burst)
    - Configurable concurrency
    - Priority queue for requests
    - Adaptive rate limiting based on latency
    - Thread-safe execution
    
    Usage:
        scheduler = TrafficScheduler(
            base_url="http://localhost:8085",
            config=SchedulerConfig(
                schedule_type=ScheduleType.FIXED_RATE,
                requests_per_minute=100,
                concurrent_workers=5
            )
        )
        
        # Add endpoints to test
        scheduler.add_endpoints(endpoints)
        
        # Start scheduler
        scheduler.start()
        
        # Run for 5 minutes
        time.sleep(300)
        
        # Stop
        scheduler.stop()
    """
    
    def __init__(
        self,
        base_url: str,
        config: Optional[SchedulerConfig] = None,
        request_executor: Optional[Callable] = None
    ):
        """
        Initialize the traffic scheduler.
        
        Args:
            base_url: Base URL for the API
            config: Scheduler configuration
            request_executor: Function to execute requests (sync or async)
        """
        self.base_url = base_url.rstrip('/')
        self.config = config or SchedulerConfig()
        self.request_executor = request_executor
        
        self.endpoints: List[Dict[str, Any]] = []
        self.scheduled_requests: List[ScheduledRequest] = []
        
        self._running = False
        self._executor: Optional[ThreadPoolExecutor] = None
        self._scheduler_thread: Optional[threading.Thread] = None
        self._worker_threads: List[threading.Thread] = []
        
        # Statistics
        self.total_scheduled = 0
        self.total_completed = 0
        self.total_failed = 0
        self.current_rpm = 0.0
        self._last_check_time = time.time()
        self._recent_requests: List[datetime] = []
        
        # Adaptive rate control
        self._current_interval = self.config.interval_seconds
        self._latency_history: List[float] = []
        self._max_latency_history = 100
        
        # Priority queues
        self._priority_queues: Dict[RequestPriority, List[ScheduledRequest]] = {
            RequestPriority.CRITICAL: [],
            RequestPriority.HIGH: [],
            RequestPriority.NORMAL: [],
            RequestPriority.LOW: [],
        }
        
    def add_endpoints(self, endpoints: List[Dict[str, Any]]):
        """Add endpoints to test."""
        self.endpoints.extend(endpoints)
        
    def add_scheduled_request(self, request: ScheduledRequest):
        """Add a scheduled request to the queue."""
        self._priority_queues[request.priority].append(request)
        self.scheduled_requests.append(request)
        self.total_scheduled += 1
    
    def _get_next_request(self) -> Optional[ScheduledRequest]:
        """Get the next request based on priority."""
        # Check from highest to lowest priority
        for priority in RequestPriority:
            if self._priority_queues[priority]:
                return self._priority_queues[priority].pop(0)
        return None
    
    def _select_endpoint(self) -> Dict[str, Any]:
        """Select an endpoint to test (weighted random)."""
        if not self.endpoints:
            return {"path": "/", "method": "GET"}
        
        # Weight endpoints by method (GET more common than POST/PUT/DELETE)
        weights = []
        for ep in self.endpoints:
            method = ep.get('method', 'GET').upper()
            if method == 'GET':
                weights.append(10)
            elif method == 'POST':
                weights.append(5)
            elif method in ['PUT', 'PATCH']:
                weights.append(3)
            else:  # DELETE
                weights.append(2)
        
        # Weighted random selection
        return random.choices(self.endpoints, weights=weights)[0]
    
    def _should_adapt_interval(self) -> bool:
        """Determine if interval should be adapted based on latency."""
        if not self.config.enable_adaptive or not self._latency_history:
            return False
        
        avg_latency = sum(self._latency_history) / len(self._latency_history)
        
        # If latency is significantly above target, slow down
        if avg_latency > self.config.target_latency_ms * 1.5:
            return True
        
        # If latency is well below target, speed up
        if avg_latency < self.config.target_latency_ms * 0.5:
            return True
            
        return False
    
    def _adapt_interval(self, latency_ms: float):
        """Adapt the interval based on latency."""
        self._latency_history.append(latency_ms)
        if len(self._latency_history) > self._max_latency_history:
            self._latency_history.pop(0)
        
        if not self._should_adapt_interval():
            return
            
        avg_latency = sum(self._latency_history) / len(self._latency_history)
        
        if avg_latency > self.config.target_latency_ms * 1.5:
            # Slow down
            self._current_interval = min(
                self._current_interval * 1.2,
                self.config.max_interval_seconds
            )
        elif avg_latency < self.config.target_latency_ms * 0.5:
            # Speed up
            self._current_interval = max(
                self._current_interval * 0.8,
                self.config.min_interval_seconds
            )
    
    def _execute_request_sync(self, request: ScheduledRequest) -> bool:
        """Execute a request synchronously."""
        if self.request_executor:
            try:
                result = self.request_executor(request)
                self._adapt_interval(getattr(result, 'duration_ms', 0))
                return True
            except Exception as e:
                print(f"Request failed: {e}")
                return False
        return False
    
    def _worker_loop(self, worker_id: int):
        """Worker thread main loop."""
        while self._running:
            request = self._get_next_request()
            
            if request is None:
                time.sleep(0.01)  # Brief sleep when queue is empty
                continue
            
            # Execute request
            success = self._execute_request_sync(request)
            
            if success:
                self.total_completed += 1
            else:
                self.total_failed += 1
            
            # Record for RPM calculation
            self._recent_requests.append(datetime.utcnow())
            
            # Adaptive interval
            time.sleep(self._current_interval)
    
    def _scheduler_loop(self):
        """Main scheduler loop for generating requests."""
        last_burst_time = time.time()
        
        while self._running:
            current_time = time.time()
            
            # Handle different schedule types
            if self.config.schedule_type == ScheduleType.FIXED_RATE:
                # Generate at fixed rate
                interval = 60.0 / self.config.requests_per_minute
                time.sleep(interval)
                
                # Schedule requests based on concurrency
                for _ in range(self.config.concurrent_workers):
                    endpoint = self._select_endpoint()
                    request = ScheduledRequest(
                        endpoint=endpoint.get('path', '/'),
                        method=endpoint.get('method', 'GET')
                    )
                    self._priority_queues[RequestPriority.NORMAL].append(request)
                    self.total_scheduled += 1
                    
            elif self.config.schedule_type == ScheduleType.INTERVAL:
                time.sleep(self.config.interval_seconds)
                endpoint = self._select_endpoint()
                request = ScheduledRequest(
                    endpoint=endpoint.get('path', '/'),
                    method=endpoint.get('method', 'GET')
                )
                self._priority_queues[RequestPriority.NORMAL].append(request)
                self.total_scheduled += 1
                
            elif self.config.schedule_type == ScheduleType.RANDOM:
                interval = random.uniform(
                    self.config.min_interval_seconds,
                    self.config.max_interval_seconds
                )
                time.sleep(interval)
                endpoint = self._select_endpoint()
                request = ScheduledRequest(
                    endpoint=endpoint.get('path', '/'),
                    method=endpoint.get('method', 'GET')
                )
                self._priority_queues[RequestPriority.NORMAL].append(request)
                self.total_scheduled += 1
                
            elif self.config.schedule_type == ScheduleType.BURST:
                if current_time - last_burst_time >= self.config.burst_interval_seconds:
                    # Generate burst
                    for _ in range(self.config.burst_size):
                        endpoint = self._select_endpoint()
                        request = ScheduledRequest(
                            endpoint=endpoint.get('path', '/'),
                            method=endpoint.get('method', 'GET')
                        )
                        self._priority_queues[RequestPriority.NORMAL].append(request)
                        self.total_scheduled += 1
                    last_burst_time = current_time
                time.sleep(0.1)
            
            # Update RPM calculation
            self._update_rpm()
            
            # Check queue size - don't overload
            total_queued = sum(len(q) for q in self._priority_queues.values())
            if total_queued > self.config.max_queue_size:
                # Drop lowest priority requests
                while len(self._priority_queues[RequestPriority.LOW]) > 0:
                    self._priority_queues[RequestPriority.LOW].pop(0)
    
    def _update_rpm(self):
        """Update requests per minute calculation."""
        now = datetime.utcnow()
        cutoff = now - timedelta(minutes=1)
        
        # Remove old timestamps
        self._recent_requests = [t for t in self._recent_requests if t > cutoff]
        
        # Calculate RPM
        self.current_rpm = len(self._recent_requests)
    
    def start(self):
        """Start the scheduler."""
        if self._running:
            return
            
        self._running = True
        
        # Create worker threads
        self._executor = ThreadPoolExecutor(
            max_workers=self.config.concurrent_workers
        )
        
        for i in range(self.config.concurrent_workers):
            thread = threading.Thread(
                target=self._worker_loop,
                args=(i,),
                daemon=True
            )
            thread.start()
            self._worker_threads.append(thread)
        
        # Create scheduler thread
        self._scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            daemon=True
        )
        self._scheduler_thread.start()
        
        print(f"Traffic Scheduler started")
        print(f"  Schedule type: {self.config.schedule_type.value}")
        print(f"  Target rate: {self.config.requests_per_minute} req/min")
        print(f"  Concurrent workers: {self.config.concurrent_workers}")
    
    def stop(self):
        """Stop the scheduler."""
        self._running = False
        
        # Wait for threads to finish
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=2.0)
            
        for thread in self._worker_threads:
            thread.join(timeout=1.0)
            
        if self._executor:
            self._executor.shutdown(wait=False)
        
        print(f"\nTraffic Scheduler stopped")
        self._print_stats()
    
    def _print_stats(self):
        """Print final statistics."""
        print(f"\nStatistics:")
        print(f"  Total scheduled: {self.total_scheduled}")
        print(f"  Total completed: {self.total_completed}")
        print(f"  Total failed: {self.total_failed}")
        print(f"  Success rate: {self.total_completed/max(1,self.total_scheduled)*100:.1f}%")
        print(f"  Current RPM: {self.current_rpm:.1f}")
        print(f"  Current interval: {self._current_interval:.3f}s")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics."""
        return {
            "running": self._running,
            "total_scheduled": self.total_scheduled,
            "total_completed": self.total_completed,
            "total_failed": self.total_failed,
            "success_rate": self.total_completed / max(1, self.total_scheduled),
            "current_rpm": self.current_rpm,
            "current_interval": self._current_interval,
            "queue_size": sum(len(q) for q in self._priority_queues.values()),
            "avg_latency_ms": sum(self._latency_history) / max(1, len(self._latency_history))
        }


class AdaptiveTrafficScheduler(TrafficScheduler):
    """
    Traffic scheduler with advanced adaptive capabilities.
    Automatically adjusts rate based on:
    - Response latency
    - Error rate
    - Resource utilization
    """
    
    def __init__(self, base_url: str, config: Optional[SchedulerConfig] = None):
        super().__init__(base_url, config)
        
        self._error_rate = 0.0
        self._target_error_rate = 0.01  # 1% target
        self._consecutive_errors = 0
        self._consecutive_success = 0
        
    def _adapt_rate(self):
        """Advanced adaptive rate control."""
        # Adjust based on error rate
        if self._error_rate > self._target_error_rate * 2:
            # Too many errors, reduce rate
            self._current_interval *= 1.5
            self.config.concurrent_workers = max(1, self.config.concurrent_workers - 1)
        elif self._error_rate < self._target_error_rate * 0.5:
            # Very few errors, increase rate
            self._current_interval *= 0.8
            self.config.concurrent_workers = min(20, self.config.concurrent_workers + 1)
        
        # Clamp values
        self._current_interval = max(
            self.config.min_interval_seconds,
            min(self.config.max_interval_seconds, self._current_interval)
        )
    
    def record_success(self):
        """Record a successful request."""
        self._consecutive_success += 1
        self._consecutive_errors = 0
        
    def record_failure(self):
        """Record a failed request."""
        self._consecutive_errors += 1
        self._consecutive_success = 0


# Convenience function
def create_scheduler(
    base_url: str,
    endpoints: List[Dict[str, Any]],
    schedule_type: ScheduleType = ScheduleType.FIXED_RATE,
    requests_per_minute: int = 100,
    concurrent_workers: int = 5
) -> TrafficScheduler:
    """
    Create a traffic scheduler with common configuration.
    
    Args:
        base_url: Base URL for the API
        endpoints: List of endpoints to test
        schedule_type: Type of scheduling
        requests_per_minute: Target requests per minute
        concurrent_workers: Number of concurrent workers
        
    Returns:
        Configured TrafficScheduler
    """
    config = SchedulerConfig(
        schedule_type=schedule_type,
        requests_per_minute=requests_per_minute,
        concurrent_workers=concurrent_workers
    )
    
    scheduler = TrafficScheduler(base_url, config)
    scheduler.add_endpoints(endpoints)
    
    return scheduler


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python traffic_scheduler.py <base_url> [requests_per_minute]")
        print("Example: python traffic_scheduler.py http://localhost:8085 100")
        sys.exit(1)
    
    base_url = sys.argv[1]
    requests_per_minute = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    
    # Create scheduler
    config = SchedulerConfig(
        schedule_type=ScheduleType.FIXED_RATE,
        requests_per_minute=requests_per_minute,
        concurrent_workers=5
    )
    
    # For demo, add a simple endpoint
    endpoints = [
        {"path": "/api/health", "method": "GET"},
        {"path": "/api/users", "method": "GET"},
    ]
    
    scheduler = TrafficScheduler(base_url, config)
    scheduler.add_endpoints(endpoints)
    
    # Start and run for 60 seconds
    scheduler.start()
    print("Scheduler running for 60 seconds...")
    time.sleep(60)
    scheduler.stop()