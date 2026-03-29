"""Observability Metrics Module.

Provides metrics collection for the socialseed-e2e framework.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class MetricType(str, Enum):
    """Types of metrics."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class Metric:
    """Represents a single metric data point."""
    name: str
    type: MetricType
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    tags: Dict[str, str] = field(default_factory=dict)
    unit: Optional[str] = None


class MetricsCollector:
    """Collects and manages metrics."""
    
    def __init__(self, service_name: str = "socialseed-e2e"):
        self.service_name = service_name
        self._metrics: List[Metric] = []
    
    @property
    def metrics(self) -> List[Metric]:
        """Get all recorded metrics."""
        return self._metrics
    
    @property
    def counters(self) -> List[Metric]:
        """Get counter metrics."""
        return [m for m in self._metrics if m.type == MetricType.COUNTER]
    
    def counter(self, name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None) -> None:
        """Record a counter metric."""
        metric = Metric(
            name=name,
            type=MetricType.COUNTER,
            value=value,
            tags=tags or {},
        )
        self._metrics.append(metric)
    
    def gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None, unit: Optional[str] = None) -> None:
        """Record a gauge metric."""
        metric = Metric(
            name=name,
            type=MetricType.GAUGE,
            value=value,
            tags=tags or {},
            unit=unit,
        )
        self._metrics.append(metric)
    
    def histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None, unit: Optional[str] = "ms") -> None:
        """Record a histogram metric."""
        metric = Metric(
            name=name,
            type=MetricType.HISTOGRAM,
            value=value,
            tags=tags or {},
            unit=unit,
        )
        self._metrics.append(metric)
    
    def get_counter(self, name: str, tags: Optional[Dict[str, str]] = None) -> float:
        """Get counter value."""
        for m in self._metrics:
            if m.name == name and m.type == MetricType.COUNTER:
                if tags is None or m.tags == tags:
                    return m.value
        return 0.0
    
    def get_gauge(self, name: str, tags: Optional[Dict[str, str]] = None) -> Optional[float]:
        """Get gauge value."""
        for m in self._metrics:
            if m.name == name and m.type == MetricType.GAUGE:
                if tags is None or m.tags == tags:
                    return m.value
        return None
    
    def export_to_prometheus(self) -> str:
        """Export metrics in Prometheus format."""
        lines = []
        for m in self._metrics:
            tags_str = ",".join(f'{k}="{v}"' for k, v in m.tags.items())
            if tags_str:
                lines.append(f"{m.name}{{{tags_str}}} {m.value}")
            else:
                lines.append(f"{m.name} {m.value}")
        return "\n".join(lines)
    
    def clear(self) -> None:
        """Clear all recorded metrics."""
        self._metrics.clear()


class TraceSpan:
    """Represents a distributed tracing span."""
    
    def __init__(self, name: str, trace_id: str, span_id: str, parent_id: Optional[str] = None):
        self.name = name
        self.trace_id = trace_id
        self.span_id = span_id
        self.parent_id = parent_id
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
        self.tags: Dict[str, str] = {}
        self.status = "ok"
    
    def end(self) -> None:
        """End the span."""
        self.end_time = datetime.now()
    
    @property
    def duration_ms(self) -> float:
        """Get span duration in milliseconds."""
        if self.end_time is None:
            return 0.0
        return (self.end_time - self.start_time).total_seconds() * 1000
