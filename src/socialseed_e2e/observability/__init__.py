"""Observability Deep Integration Module.

This module provides comprehensive observability support:
- OpenTelemetry integration for distributed tracing
- Metrics export (Prometheus, custom metrics)
- Structured logging with correlation
- Log aggregation and analysis

Usage:
    from socialseed_e2e.observability import (
        TelemetryManager,
        MetricsCollector,
        StructuredLogger,
    )
"""

import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from enum import Enum

from abc import ABC, abstractmethod


class ObservabilityProvider(ABC):
    """Base class for all observability providers."""

    @abstractmethod
    def record_test_result(
        self,
        test_name: str,
        status: str,
        duration_ms: float,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Record the result of a test."""
        pass

    @abstractmethod
    def record_metric(
        self, name: str, value: float, tags: Optional[Dict[str, str]] = None
    ):
        """Record a custom metric."""
        pass


class TracingProvider(ABC):
    """Base class for distributed tracing providers."""

    @abstractmethod
    def start_span(self, name: str, tags: Optional[Dict[str, str]] = None) -> Any:
        """Start a new trace span."""
        pass

    @abstractmethod
    def end_span(self, span: Any):
        """End an active span."""
        pass


class MetricType(str, Enum):
    """Types of metrics."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class Metric:
    """Represents a metric."""

    name: str
    type: MetricType
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class TraceSpan:
    """Represents a trace span."""

    name: str
    trace_id: str
    span_id: str
    parent_id: Optional[str] = None
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    status: str = "unset"

    def end(self):
        """End the span."""
        self.end_time = datetime.now()

    @property
    def duration_ms(self) -> float:
        """Get span duration in milliseconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return 0.0


class MetricsCollector:
    """Collects and manages metrics.

    Example:
        collector = MetricsCollector()

        # Record metrics
        collector.counter("requests_total", 1, {"method": "GET"})
        collector.gauge("active_connections", 10)
        collector.histogram("request_duration", 150.0)

        # Get metrics
        metrics = collector.get_metrics()
    """

    def __init__(self):
        """Initialize metrics collector."""
        self.metrics: List[Metric] = []
        self.counters: Dict[str, float] = {}
        self.gauges: Dict[str, float] = {}

    def counter(
        self, name: str, value: float = 1, labels: Optional[Dict[str, str]] = None
    ):
        """Record a counter metric."""
        key = self._make_key(name, labels)
        self.counters[key] = self.counters.get(key, 0) + value

        self.metrics.append(
            Metric(
                name=name,
                type=MetricType.COUNTER,
                value=self.counters[key],
                labels=labels or {},
            )
        )

    def gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Record a gauge metric."""
        key = self._make_key(name, labels)
        self.gauges[key] = value

        self.metrics.append(
            Metric(name=name, type=MetricType.GAUGE, value=value, labels=labels or {})
        )

    def histogram(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ):
        """Record a histogram metric."""
        self.metrics.append(
            Metric(
                name=name, type=MetricType.HISTOGRAM, value=value, labels=labels or {}
            )
        )

    def get_metrics(self) -> List[Metric]:
        """Get all recorded metrics."""
        return self.metrics.copy()

    def get_counter(self, name: str, labels: Optional[Dict[str, str]] = None) -> float:
        """Get counter value."""
        key = self._make_key(name, labels)
        return self.counters.get(key, 0)

    def get_gauge(self, name: str, labels: Optional[Dict[str, str]] = None) -> float:
        """Get gauge value."""
        key = self._make_key(name, labels)
        return self.gauges.get(key, 0)

    def export_to_prometheus(self) -> str:
        """Export metrics in Prometheus format."""
        lines = []

        for name, value in self.counters.items():
            metric_name = name.split("{")[0]
            lines.append(f"# TYPE {metric_name} counter")
            lines.append(f"{name} {value}")

        for name, value in self.gauges.items():
            metric_name = name.split("{")[0]
            lines.append(f"# TYPE {metric_name} gauge")
            lines.append(f"{name} {value}")

        return "\n".join(lines)

    def _make_key(self, name: str, labels: Optional[Dict[str, str]]) -> str:
        """Create key from name and labels."""
        if not labels:
            return name
        label_str = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def clear(self):
        """Clear all metrics."""
        self.metrics.clear()
        self.counters.clear()
        self.gauges.clear()


class TelemetryManager:
    """Manages distributed tracing and telemetry.

    Example:
        telemetry = TelemetryManager()

        # Start a trace
        with telemetry.start_span("process_request") as span:
            span.set_attribute("user.id", "123")
            # ... do work ...

        # Get spans
        spans = telemetry.get_spans()
    """

    def __init__(self, service_name: str = "socialseed-e2e"):
        """Initialize telemetry manager."""
        self.service_name = service_name
        self.spans: List[TraceSpan] = []
        self.current_trace_id: Optional[str] = None

    def start_trace(self) -> str:
        """Start a new trace."""
        self.current_trace_id = str(uuid.uuid4())
        return self.current_trace_id

    def start_span(
        self,
        name: str,
        parent_id: Optional[str] = None,
    ) -> TraceSpan:
        """Start a new span."""
        trace_id = self.current_trace_id or str(uuid.uuid4())
        span = TraceSpan(
            name=name,
            trace_id=trace_id,
            span_id=str(uuid.uuid4())[:16],
            parent_id=parent_id,
        )
        self.spans.append(span)
        return span

    def end_span(self, span: TraceSpan):
        """End a span."""
        span.end()

    def get_spans(self) -> List[TraceSpan]:
        """Get all spans."""
        return self.spans.copy()

    def get_trace(self, trace_id: str) -> List[TraceSpan]:
        """Get spans for a specific trace."""
        return [s for s in self.spans if s.trace_id == trace_id]

    def clear(self):
        """Clear all spans."""
        self.spans.clear()
        self.current_trace_id = None


class StructuredLogger:
    """Structured logging with correlation IDs.

    Example:
        logger = StructuredLogger()

        # Log with context
        logger.info("Processing request", {
            "request_id": "abc123",
            "user_id": "user456"
        })
    """

    def __init__(self, name: str = "socialseed-e2e"):
        """Initialize structured logger."""
        self.name = name
        self.logger = logging.getLogger(name)
        self.context: Dict[str, Any] = {}

    def set_context(self, **kwargs):
        """Set context fields."""
        self.context.update(kwargs)

    def clear_context(self):
        """Clear context."""
        self.context.clear()

    def _log(self, level: str, message: str, extra: Optional[Dict[str, Any]] = None):
        """Internal log method."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "logger": self.name,
            "message": message,
        }
        log_entry.update(self.context)
        if extra:
            log_entry.update(extra)

        print(json.dumps(log_entry))

    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log debug message."""
        self._log("DEBUG", message, extra)

    def info(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log info message."""
        self._log("INFO", message, extra)

    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log warning message."""
        self._log("WARNING", message, extra)

    def error(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log error message."""
        self._log("ERROR", message, extra)


class ObservabilityManager:
    """Manages multiple observability providers."""

    def __init__(self):
        self.providers: List[ObservabilityProvider] = []
        self.tracing_provider: Optional[TracingProvider] = None

    def add_provider(self, provider: ObservabilityProvider):
        self.providers.append(provider)

    def set_tracing_provider(self, provider: TracingProvider):
        self.tracing_provider = provider

    def record_test(
        self,
        test_name: str,
        status: str,
        duration_ms: float,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        for provider in self.providers:
            provider.record_test_result(test_name, status, duration_ms, metadata)

    def record_metric(
        self, name: str, value: float, tags: Optional[Dict[str, str]] = None
    ):
        for provider in self.providers:
            provider.record_metric(name, value, tags)


class ObservabilitySuite:
    """Comprehensive observability testing suite.

    Example:
        suite = ObservabilitySuite()

        # Collect metrics
        suite.record_request_metrics(duration_ms=150, status_code=200)

        # Create trace
        with suite.create_span("api_call") as span:
            # ... make API call ...
            pass

        # Generate report
        report = suite.generate_report()
    """

    def __init__(self, service_name: str = "socialseed-e2e"):
        """Initialize observability suite."""
        self.service_name = service_name
        self.metrics = MetricsCollector()
        self.telemetry = TelemetryManager(service_name)
        self.logger = StructuredLogger(service_name)

    def record_request_metrics(
        self,
        duration_ms: float,
        status_code: int,
        endpoint: Optional[str] = None,
    ):
        """Record request metrics."""
        labels = {"endpoint": endpoint} if endpoint else {}

        self.metrics.counter("requests_total", 1, labels)
        self.metrics.histogram("request_duration_ms", duration_ms, labels)

        if status_code >= 400:
            self.metrics.counter("errors_total", 1, {"status_code": str(status_code)})

    def create_span(self, name: str) -> TraceSpan:
        """Create a new trace span."""
        return self.telemetry.start_span(name)

    def generate_report(self) -> Dict[str, Any]:
        """Generate observability report."""
        spans = self.telemetry.get_spans()
        total_duration = sum(s.duration_ms for s in spans if s.end_time)

        return {
            "service_name": self.service_name,
            "total_spans": len(spans),
            "total_duration_ms": total_duration,
            "metrics_count": len(self.metrics.get_metrics()),
            "counters": self.metrics.counters.copy(),
            "gauges": self.metrics.gauges.copy(),
        }
