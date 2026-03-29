"""Observability Module - Metrics, Tracing, and Logging.

This module provides observability features for the socialseed-e2e framework:
- Metrics collection and export
- Distributed tracing
- Structured logging
- Telemetry integration
"""

from typing import Any, List

from socialseed_e2e.observability.metrics import (
    Metric,
    MetricType,
    MetricsCollector,
    TraceSpan,
)


class ObservabilitySuite:
    """Observability suite for recording metrics and traces."""
    
    def __init__(self, service_name: str = "socialseed-e2e"):
        self.service_name = service_name
        self.metrics = MetricsCollector(service_name)
        self._spans: List[TraceSpan] = []
    
    def record_request_metrics(self, duration_ms: float, status_code: int) -> None:
        """Record request metrics."""
        self.metrics.counter("requests_total", 1, {"status": str(status_code)})
        self.metrics.histogram("request_duration", duration_ms, {"status": str(status_code)})
    
    def create_span(self, name: str) -> "TraceSpan":
        """Create a new span."""
        import uuid
        span = TraceSpan(
            name=name,
            trace_id=str(uuid.uuid4()),
            span_id=str(uuid.uuid4())
        )
        self._spans.append(span)
        return span
    
    def generate_report(self) -> dict:
        """Generate observability report."""
        return {
            "service_name": self.service_name,
            "total_spans": len(self._spans),
        }


class ObservabilityManager:
    """Manages observability providers."""
    
    def __init__(self):
        self.providers = []
    
    def add_provider(self, provider: "ObservabilityProvider") -> None:
        """Add an observability provider."""
        self.providers.append(provider)


class ObservabilityProvider:
    """Base class for observability providers."""
    
    def __init__(self, name: str):
        self.name = name
    
    def emit_metric(self, metric: "Metric") -> None:
        """Emit a metric."""
        pass


class StructuredLogger:
    """Structured logger with context support."""
    
    def __init__(self, name: str = "socialseed-e2e"):
        self.name = name
        self._context = {}
    
    @property
    def context(self) -> dict:
        """Get logger context."""
        return self._context
    
    def set_context(self, **kwargs) -> None:
        """Set context from kwargs."""
        self._context.update(kwargs)
    
    def clear_context(self) -> None:
        """Clear context."""
        self._context.clear()
    
    def log(self, level: str, message: str, **kwargs) -> None:
        """Log a message."""
        pass


class TelemetryManager:
    """Manages distributed tracing."""
    
    def __init__(self):
        self.spans: List[TraceSpan] = []
        self._current_trace: str = None
    
    @property
    def current_trace_id(self) -> str:
        """Get current trace ID."""
        return self._current_trace
    
    def start_trace(self) -> str:
        """Start a trace (no args version)."""
        import uuid
        self._current_trace = str(uuid.uuid4())
        return self._current_trace
    
    def start_span(self, name: str, trace_id: str = None) -> "TraceSpan":
        """Start a Span."""
        import uuid
        span = TraceSpan(
            name=name,
            trace_id=trace_id or self._current_trace or str(uuid.uuid4()),
            span_id=str(uuid.uuid4())
        )
        self.spans.append(span)
        return span
    
    def get_spans(self, trace_id: str = None) -> list:
        """Get spans."""
        if trace_id:
            return [s for s in self.spans if s.trace_id == trace_id]
        return self.spans
    
    def get_trace(self, trace_id: str) -> list:
        """Get trace - returns list of spans."""
        return self.get_spans(trace_id)


class TracingProvider:
    """Base class for tracing providers."""
    
    def __init__(self, name: str):
        self.name = name
    
    def start_span(self, name: str, trace_id: str = None) -> "TraceSpan":
        """Start a span."""
        import uuid
        from socialseed_e2e.observability.metrics import TraceSpan as ImportedTraceSpan
        return ImportedTraceSpan(name=name, trace_id=trace_id or str(uuid.uuid4()), span_id=str(uuid.uuid4()))


__all__ = [
    "Metric",
    "MetricType", 
    "MetricsCollector",
    "ObservabilitySuite",
    "ObservabilityManager",
    "ObservabilityProvider",
    "StructuredLogger",
    "TelemetryManager",
    "TraceSpan",
    "TracingProvider",
]
