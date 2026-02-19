"""Tests for Observability Module.

This module tests the observability features.
"""

import pytest
from unittest.mock import Mock

from socialseed_e2e.observability import (
    Metric,
    MetricType,
    MetricsCollector,
    ObservabilityManager,
    ObservabilityProvider,
    ObservabilitySuite,
    StructuredLogger,
    TelemetryManager,
    TraceSpan,
    TracingProvider,
)


class TestMetric:
    """Tests for Metric."""

    def test_initialization(self):
        """Test metric initialization."""
        metric = Metric(name="test_metric", type=MetricType.COUNTER, value=1.0)
        assert metric.name == "test_metric"
        assert metric.type == MetricType.COUNTER
        assert metric.value == 1.0


class TestTraceSpan:
    """Tests for TraceSpan."""

    def test_initialization(self):
        """Test trace span initialization."""
        span = TraceSpan(name="test_span", trace_id="trace123", span_id="span456")
        assert span.name == "test_span"
        assert span.trace_id == "trace123"
        assert span.span_id == "span456"

    def test_end(self):
        """Test ending span."""
        span = TraceSpan(name="test", trace_id="t1", span_id="s1")
        span.end()
        assert span.end_time is not None

    def test_duration_ms(self):
        """Test span duration."""
        import time

        span = TraceSpan(name="test", trace_id="t1", span_id="s1")
        time.sleep(0.01)
        span.end()
        assert span.duration_ms >= 10


class TestMetricsCollector:
    """Tests for MetricsCollector."""

    def test_initialization(self):
        """Test collector initialization."""
        collector = MetricsCollector()
        assert len(collector.metrics) == 0

    def test_counter(self):
        """Test counter metric."""
        collector = MetricsCollector()
        collector.counter("requests_total", 1, {"method": "GET"})

        assert collector.get_counter("requests_total", {"method": "GET"}) == 1
        assert len(collector.metrics) == 1

    def test_gauge(self):
        """Test gauge metric."""
        collector = MetricsCollector()
        collector.gauge("active_connections", 10)

        assert collector.get_gauge("active_connections") == 10

    def test_histogram(self):
        """Test histogram metric."""
        collector = MetricsCollector()
        collector.histogram("request_duration", 150.0)

        assert len(collector.metrics) == 1
        assert collector.metrics[0].type == MetricType.HISTOGRAM

    def test_export_to_prometheus(self):
        """Test Prometheus export."""
        collector = MetricsCollector()
        collector.counter("requests_total", 5)

        output = collector.export_to_prometheus()
        assert "requests_total" in output
        assert "5" in output

    def test_clear(self):
        """Test clearing metrics."""
        collector = MetricsCollector()
        collector.counter("test", 1)
        collector.clear()

        assert len(collector.metrics) == 0
        assert len(collector.counters) == 0


class TestTelemetryManager:
    """Tests for TelemetryManager."""

    def test_initialization(self):
        """Test telemetry manager initialization."""
        telemetry = TelemetryManager()
        assert len(telemetry.spans) == 0

    def test_start_trace(self):
        """Test starting trace."""
        telemetry = TelemetryManager()
        trace_id = telemetry.start_trace()

        assert trace_id is not None
        assert telemetry.current_trace_id == trace_id

    def test_start_span(self):
        """Test starting span."""
        telemetry = TelemetryManager()
        span = telemetry.start_span("test_span")

        assert span.name == "test_span"
        assert len(telemetry.spans) == 1

    def test_get_spans(self):
        """Test getting spans."""
        telemetry = TelemetryManager()
        telemetry.start_span("span1")
        telemetry.start_span("span2")

        spans = telemetry.get_spans()
        assert len(spans) == 2

    def test_get_trace(self):
        """Test getting trace."""
        telemetry = TelemetryManager()
        trace_id = telemetry.start_trace()
        telemetry.start_span("span1")

        trace_spans = telemetry.get_trace(trace_id)
        assert len(trace_spans) == 1


class TestStructuredLogger:
    """Tests for StructuredLogger."""

    def test_initialization(self):
        """Test logger initialization."""
        logger = StructuredLogger("test_logger")
        assert logger.name == "test_logger"

    def test_set_context(self):
        """Test setting context."""
        logger = StructuredLogger()
        logger.set_context(request_id="abc123")

        assert logger.context["request_id"] == "abc123"

    def test_clear_context(self):
        """Test clearing context."""
        logger = StructuredLogger()
        logger.set_context(request_id="abc123")
        logger.clear_context()

        assert len(logger.context) == 0


class TestObservabilityManager:
    """Tests for ObservabilityManager."""

    def test_initialization(self):
        """Test manager initialization."""
        manager = ObservabilityManager()
        assert len(manager.providers) == 0

    def test_add_provider(self):
        """Test adding provider."""
        manager = ObservabilityManager()
        provider = Mock(spec=ObservabilityProvider)
        manager.add_provider(provider)

        assert len(manager.providers) == 1


class TestObservabilitySuite:
    """Tests for ObservabilitySuite."""

    def test_initialization(self):
        """Test suite initialization."""
        suite = ObservabilitySuite("my_service")
        assert suite.service_name == "my_service"

    def test_record_request_metrics(self):
        """Test recording request metrics."""
        suite = ObservabilitySuite()
        suite.record_request_metrics(duration_ms=150, status_code=200)

        assert suite.metrics.get_counter("requests_total") == 1

    def test_create_span(self):
        """Test creating span."""
        suite = ObservabilitySuite()
        span = suite.create_span("api_call")

        assert span.name == "api_call"

    def test_generate_report(self):
        """Test generating report."""
        suite = ObservabilitySuite()
        suite.record_request_metrics(duration_ms=100, status_code=200)
        span = suite.create_span("test")
        span.end()

        report = suite.generate_report()
        assert report["service_name"] == "socialseed-e2e"
        assert report["total_spans"] == 1


class TestMetricType:
    """Tests for MetricType enum."""

    def test_types(self):
        """Test metric types."""
        assert MetricType.COUNTER.value == "counter"
        assert MetricType.GAUGE.value == "gauge"
        assert MetricType.HISTOGRAM.value == "histogram"
        assert MetricType.SUMMARY.value == "summary"
