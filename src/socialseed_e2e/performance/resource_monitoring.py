"""Resource Monitoring for Performance Testing.

This module provides resource monitoring capabilities:
- CPU and Memory profiling
- Database query analysis
- Network performance monitoring
- System resource tracking

Example:
    >>> from socialseed_e2e.performance import ResourceMonitor
    >>> monitor = ResourceMonitor()
    >>> async with monitor.track():
    ...     await run_performance_test()
    >>> report = monitor.get_report()
"""

import asyncio
import logging
import os
import time
import tracemalloc
from collections import defaultdict
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


@dataclass
class CPUStats:
    """CPU usage statistics."""

    user_time: float = 0.0
    system_time: float = 0.0
    total_time: float = 0.0
    percent_usage: float = 0.0
    core_count: int = 0

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            "user_time": self.user_time,
            "system_time": self.system_time,
            "total_time": self.total_time,
            "percent_usage": self.percent_usage,
            "core_count": self.core_count,
        }


@dataclass
class MemoryStats:
    """Memory usage statistics."""

    rss_mb: float = 0.0
    vms_mb: float = 0.0
    peak_mb: float = 0.0
    percent_usage: float = 0.0
    available_mb: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            "rss_mb": self.rss_mb,
            "vms_mb": self.vms_mb,
            "peak_mb": self.peak_mb,
            "percent_usage": self.percent_usage,
            "available_mb": self.available_mb,
        }


@dataclass
class DatabaseQuery:
    """Database query information."""

    query_text: str
    execution_time_ms: float
    rows_affected: int = 0
    rows_returned: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Performance metrics
    planning_time_ms: float = 0.0
    execution_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query": self.query_text[:200] + "..."
            if len(self.query_text) > 200
            else self.query_text,
            "execution_time_ms": self.execution_time_ms,
            "rows_affected": self.rows_affected,
            "rows_returned": self.rows_returned,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class DatabaseStats:
    """Database performance statistics."""

    total_queries: int = 0
    total_execution_time_ms: float = 0.0
    avg_execution_time_ms: float = 0.0
    slow_queries: List[DatabaseQuery] = field(default_factory=list)
    queries_by_table: Dict[str, int] = field(default_factory=dict)

    def record_query(self, query: DatabaseQuery) -> None:
        """Record a database query."""
        self.total_queries += 1
        self.total_execution_time_ms += query.execution_time_ms
        self.avg_execution_time_ms = self.total_execution_time_ms / self.total_queries

        # Track slow queries (>100ms)
        if query.execution_time_ms > 100:
            self.slow_queries.append(query)

        # Extract table name (simple heuristic)
        query_upper = query.query_text.upper()
        if "FROM" in query_upper:
            parts = query_upper.split("FROM")
            if len(parts) > 1:
                table = parts[1].split()[0].strip(";,")
                self.queries_by_table[table] = self.queries_by_table.get(table, 0) + 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_queries": self.total_queries,
            "avg_execution_time_ms": round(self.avg_execution_time_ms, 2),
            "slow_query_count": len(self.slow_queries),
            "slowest_queries": [
                q.to_dict()
                for q in sorted(
                    self.slow_queries, key=lambda x: x.execution_time_ms, reverse=True
                )[:5]
            ],
            "queries_by_table": self.queries_by_table,
        }


@dataclass
class NetworkStats:
    """Network performance statistics."""

    bytes_sent: int = 0
    bytes_received: int = 0
    packets_sent: int = 0
    packets_received: int = 0
    connections_opened: int = 0
    connections_closed: int = 0
    errors: int = 0

    @property
    def total_bytes(self) -> int:
        """Get total bytes transferred."""
        return self.bytes_sent + self.bytes_received

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "bytes_sent": self.bytes_sent,
            "bytes_received": self.bytes_received,
            "total_mb": round(self.total_bytes / (1024 * 1024), 2),
            "packets_sent": self.packets_sent,
            "packets_received": self.packets_received,
            "connections": {
                "opened": self.connections_opened,
                "closed": self.connections_closed,
                "active": self.connections_opened - self.connections_closed,
            },
            "errors": self.errors,
        }


@dataclass
class ResourceSnapshot:
    """Snapshot of system resources at a point in time."""

    timestamp: datetime
    cpu: CPUStats
    memory: MemoryStats
    database: DatabaseStats
    network: NetworkStats

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "cpu": self.cpu.to_dict(),
            "memory": self.memory.to_dict(),
            "database": self.database.to_dict(),
            "network": self.network.to_dict(),
        }


@dataclass
class ResourceReport:
    """Complete resource monitoring report."""

    start_time: datetime
    end_time: datetime
    snapshots: List[ResourceSnapshot] = field(default_factory=list)

    # Aggregate statistics
    avg_cpu_percent: float = 0.0
    peak_cpu_percent: float = 0.0
    avg_memory_mb: float = 0.0
    peak_memory_mb: float = 0.0
    total_queries: int = 0
    slow_query_count: int = 0
    total_data_transferred_mb: float = 0.0

    def calculate_statistics(self) -> None:
        """Calculate aggregate statistics from snapshots."""
        if not self.snapshots:
            return

        cpu_values = [s.cpu.percent_usage for s in self.snapshots]
        memory_values = [s.memory.rss_mb for s in self.snapshots]

        self.avg_cpu_percent = sum(cpu_values) / len(cpu_values)
        self.peak_cpu_percent = max(cpu_values)
        self.avg_memory_mb = sum(memory_values) / len(memory_values)
        self.peak_memory_mb = max(memory_values)

        # Aggregate database stats
        for snapshot in self.snapshots:
            self.total_queries += snapshot.database.total_queries
            self.slow_query_count += len(snapshot.database.slow_queries)

        # Network stats from last snapshot
        if self.snapshots:
            last_network = self.snapshots[-1].network
            self.total_data_transferred_mb = last_network.total_bytes / (1024 * 1024)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        self.calculate_statistics()

        return {
            "duration_seconds": (self.end_time - self.start_time).total_seconds(),
            "cpu": {
                "avg_percent": round(self.avg_cpu_percent, 2),
                "peak_percent": round(self.peak_cpu_percent, 2),
            },
            "memory": {
                "avg_mb": round(self.avg_memory_mb, 2),
                "peak_mb": round(self.peak_memory_mb, 2),
            },
            "database": {
                "total_queries": self.total_queries,
                "slow_query_count": self.slow_query_count,
            },
            "network": {
                "total_data_mb": round(self.total_data_transferred_mb, 2),
            },
            "snapshot_count": len(self.snapshots),
        }


class ResourceMonitor:
    """Monitor system resources during performance testing.

    Tracks CPU, memory, database queries, and network performance
    throughout test execution.

    Example:
        >>> monitor = ResourceMonitor(sampling_interval=5.0)
        >>>
        >>> async with monitor.track():
        ...     await run_load_test()
        >>>
        >>> report = monitor.get_report()
        >>> print(f"Peak CPU: {report.peak_cpu_percent}%")
        >>> print(f"Peak Memory: {report.peak_memory_mb}MB")
    """

    def __init__(self, sampling_interval: float = 5.0):
        """Initialize resource monitor.

        Args:
            sampling_interval: Seconds between resource snapshots
        """
        self.sampling_interval = sampling_interval
        self.snapshots: List[ResourceSnapshot] = []
        self.is_monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()

        # Trackers
        self.database_tracker = DatabaseTracker()
        self.network_tracker = NetworkTracker()

    def _get_cpu_stats(self) -> CPUStats:
        """Get current CPU statistics."""
        try:
            import psutil

            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_times = psutil.cpu_times()

            return CPUStats(
                user_time=cpu_times.user,
                system_time=cpu_times.system,
                total_time=cpu_times.user + cpu_times.system,
                percent_usage=cpu_percent,
                core_count=psutil.cpu_count(),
            )
        except ImportError:
            # Fallback if psutil not available
            return CPUStats(percent_usage=0.0)

    def _get_memory_stats(self) -> MemoryStats:
        """Get current memory statistics."""
        try:
            import psutil

            memory = psutil.virtual_memory()
            process = psutil.Process()
            process_memory = process.memory_info()

            return MemoryStats(
                rss_mb=process_memory.rss / (1024 * 1024),
                vms_mb=process_memory.vms / (1024 * 1024),
                percent_usage=memory.percent,
                available_mb=memory.available / (1024 * 1024),
            )
        except ImportError:
            return MemoryStats(percent_usage=0.0)

    async def _take_snapshot(self) -> ResourceSnapshot:
        """Take a resource snapshot."""
        return ResourceSnapshot(
            timestamp=datetime.utcnow(),
            cpu=self._get_cpu_stats(),
            memory=self._get_memory_stats(),
            database=self.database_tracker.get_stats(),
            network=self.network_tracker.get_stats(),
        )

    async def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while not self._stop_event.is_set():
            try:
                snapshot = await self._take_snapshot()
                self.snapshots.append(snapshot)

                # Wait for next interval
                await asyncio.wait_for(
                    self._stop_event.wait(), timeout=self.sampling_interval
                )
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")

    @asynccontextmanager
    async def track(self):
        """Context manager for tracking resources.

        Usage:
            async with monitor.track():
                await run_test()
            report = monitor.get_report()
        """
        self.start()
        try:
            yield self
        finally:
            await self.stop()

    def start(self) -> None:
        """Start resource monitoring."""
        if self.is_monitoring:
            return

        self.is_monitoring = True
        self.snapshots = []
        self._stop_event.clear()
        self._monitor_task = asyncio.create_task(self._monitor_loop())

        # Start tracemalloc for memory tracking
        tracemalloc.start()

        logger.info(
            f"Resource monitoring started (interval: {self.sampling_interval}s)"
        )

    async def stop(self) -> None:
        """Stop resource monitoring."""
        if not self.is_monitoring:
            return

        self.is_monitoring = False
        self._stop_event.set()

        if self._monitor_task:
            try:
                await asyncio.wait_for(self._monitor_task, timeout=5.0)
            except asyncio.TimeoutError:
                self._monitor_task.cancel()

        tracemalloc.stop()
        logger.info(f"Resource monitoring stopped ({len(self.snapshots)} snapshots)")

    def get_report(self) -> ResourceReport:
        """Get resource monitoring report.

        Returns:
            ResourceReport with all statistics
        """
        if not self.snapshots:
            return ResourceReport(
                start_time=datetime.utcnow(), end_time=datetime.utcnow()
            )

        report = ResourceReport(
            start_time=self.snapshots[0].timestamp,
            end_time=self.snapshots[-1].timestamp,
            snapshots=self.snapshots,
        )

        report.calculate_statistics()
        return report

    def record_database_query(self, query: DatabaseQuery) -> None:
        """Record a database query.

        Args:
            query: DatabaseQuery to record
        """
        self.database_tracker.record_query(query)

    def record_network_activity(
        self, bytes_sent: int = 0, bytes_received: int = 0
    ) -> None:
        """Record network activity.

        Args:
            bytes_sent: Bytes sent
            bytes_received: Bytes received
        """
        self.network_tracker.record_activity(bytes_sent, bytes_received)


class DatabaseTracker:
    """Track database query performance."""

    def __init__(self):
        """Initialize database tracker."""
        self.stats = DatabaseStats()

    def record_query(self, query: DatabaseQuery) -> None:
        """Record a database query."""
        self.stats.record_query(query)

    def get_stats(self) -> DatabaseStats:
        """Get current statistics."""
        return self.stats


class NetworkTracker:
    """Track network performance."""

    def __init__(self):
        """Initialize network tracker."""
        self.stats = NetworkStats()

    def record_activity(self, bytes_sent: int = 0, bytes_received: int = 0) -> None:
        """Record network activity."""
        self.stats.bytes_sent += bytes_sent
        self.stats.bytes_received += bytes_received

    def record_connection_opened(self) -> None:
        """Record a new connection."""
        self.stats.connections_opened += 1

    def record_connection_closed(self) -> None:
        """Record a closed connection."""
        self.stats.connections_closed += 1

    def record_error(self) -> None:
        """Record a network error."""
        self.stats.errors += 1

    def get_stats(self) -> NetworkStats:
        """Get current statistics."""
        return self.stats


class QueryProfiler:
    """Profile database queries for performance analysis.

    Wraps database calls to capture execution time and query details.

    Example:
        >>> profiler = QueryProfiler()
        >>>
        >>> @profiler.profile
        >>> async def get_user(user_id):
        ...     return await db.query("SELECT * FROM users WHERE id = $1", user_id)
        >>>
        >>> stats = profiler.get_stats()
    """

    def __init__(self):
        """Initialize query profiler."""
        self.queries: List[DatabaseQuery] = []
        self.slow_query_threshold_ms: float = 100.0

    def profile(self, func: Callable) -> Callable:
        """Decorator to profile a database function.

        Args:
            func: Function to profile

        Returns:
            Wrapped function
        """

        async def wrapper(*args, **kwargs):
            start_time = time.perf_counter()

            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                execution_time_ms = (time.perf_counter() - start_time) * 1000

                # Create query record
                query_text = args[0] if args else str(func.__name__)
                query = DatabaseQuery(
                    query_text=query_text, execution_time_ms=execution_time_ms
                )

                self.queries.append(query)

                # Log slow queries
                if execution_time_ms > self.slow_query_threshold_ms:
                    logger.warning(
                        f"Slow query ({execution_time_ms:.2f}ms): {query_text[:100]}"
                    )

                return result

            except Exception as e:
                execution_time_ms = (time.perf_counter() - start_time) * 1000
                query = DatabaseQuery(
                    query_text=args[0] if args else str(func.__name__),
                    execution_time_ms=execution_time_ms,
                )
                self.queries.append(query)
                raise

        return wrapper

    def get_stats(self) -> DatabaseStats:
        """Get profiling statistics."""
        stats = DatabaseStats()
        for query in self.queries:
            stats.record_query(query)
        return stats

    def get_slow_queries(self, threshold_ms: float = None) -> List[DatabaseQuery]:
        """Get slow queries.

        Args:
            threshold_ms: Threshold in milliseconds

        Returns:
            List of slow queries
        """
        threshold = threshold_ms or self.slow_query_threshold_ms
        return [q for q in self.queries if q.execution_time_ms > threshold]

    def reset(self) -> None:
        """Reset profiler state."""
        self.queries = []


class MemoryProfiler:
    """Profile memory usage during performance tests.

    Uses tracemalloc to track memory allocations.

    Example:
        >>> profiler = MemoryProfiler()
        >>> profiler.start()
        >>> await run_test()
        >>> top_allocations = profiler.get_top_allocations(10)
    """

    def __init__(self):
        """Initialize memory profiler."""
        self.is_profiling = False
        self.start_snapshot = None

    def start(self) -> None:
        """Start memory profiling."""
        if not tracemalloc.is_tracing():
            tracemalloc.start()

        self.start_snapshot = tracemalloc.take_snapshot()
        self.is_profiling = True
        logger.info("Memory profiling started")

    def stop(self) -> Dict[str, Any]:
        """Stop memory profiling and return statistics."""
        if not self.is_profiling:
            return {}

        end_snapshot = tracemalloc.take_snapshot()
        self.is_profiling = False

        # Calculate differences
        stats = end_snapshot.compare_to(self.start_snapshot, "lineno")

        # Top memory consumers
        top_stats = [
            {
                "file": str(stat.traceback.format()[-1])
                if stat.traceback.format()
                else "unknown",
                "size_diff_mb": round(stat.size_diff / (1024 * 1024), 2),
                "count_diff": stat.count_diff,
            }
            for stat in stats[:10]
        ]

        current, peak = tracemalloc.get_traced_memory()

        return {
            "current_mb": round(current / (1024 * 1024), 2),
            "peak_mb": round(peak / (1024 * 1024), 2),
            "top_allocations": top_stats,
        }

    def get_top_allocations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top memory allocations.

        Args:
            limit: Number of top allocations to return

        Returns:
            List of allocation information
        """
        if not tracemalloc.is_tracing():
            return []

        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics("lineno")[:limit]

        return [
            {
                "file": str(stat.traceback.format()[-1])
                if stat.traceback.format()
                else "unknown",
                "size_mb": round(stat.size / (1024 * 1024), 2),
                "count": stat.count,
            }
            for stat in top_stats
        ]
