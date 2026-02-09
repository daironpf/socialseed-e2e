"""Tests for TraceCollector."""

from datetime import datetime

import pytest

from socialseed_e2e.core.traceability.collector import (
    TraceCollector,
    create_collector,
    get_global_collector,
    set_global_collector,
)
from socialseed_e2e.core.traceability.models import InteractionType, LogicBranchType, TraceConfig


class TestTraceCollector:
    """Tests for TraceCollector class."""

    def test_collector_creation(self):
        """Test collector creation with default config."""
        collector = TraceCollector()

        assert collector.config.enabled is True
        assert collector._current_trace is None
        assert collector._completed_traces == []

    def test_collector_with_custom_config(self):
        """Test collector with custom configuration."""
        config = TraceConfig(enabled=False, max_body_size=5000)
        collector = TraceCollector(config)

        assert collector.config.enabled is False
        assert collector.config.max_body_size == 5000

    def test_start_trace(self):
        """Test starting a trace."""
        collector = TraceCollector()
        trace = collector.start_trace("test_login", "auth-service")

        assert trace is not None
        assert trace.test_name == "test_login"
        assert trace.service_name == "auth-service"
        assert trace.status == "running"
        assert collector._current_trace is trace

    def test_start_trace_when_disabled(self):
        """Test starting a trace when collector is disabled."""
        config = TraceConfig(enabled=False)
        collector = TraceCollector(config)
        trace = collector.start_trace("test_login", "auth-service")

        assert trace is None

    def test_end_trace(self):
        """Test ending a trace."""
        collector = TraceCollector()
        collector.start_trace("test_login", "auth-service")

        completed = collector.end_trace("passed")

        assert completed is not None
        assert completed.status == "passed"
        assert completed.end_time is not None
        assert len(collector._completed_traces) == 1
        assert collector._current_trace is None

    def test_end_trace_with_error(self):
        """Test ending a trace with error."""
        collector = TraceCollector()
        collector.start_trace("test_login", "auth-service")

        completed = collector.end_trace("failed", "Authentication failed")

        assert completed.status == "failed"
        assert completed.error_message == "Authentication failed"

    def test_register_component(self):
        """Test registering a component."""
        collector = TraceCollector()
        collector.start_trace("test", "service")

        component = collector.register_component("Auth-Service", "service")

        assert component.name == "Auth-Service"
        assert component.type == "service"
        assert "Auth-Service" in collector._component_registry
        assert len(collector._current_trace.components) == 1

    def test_record_interaction(self):
        """Test recording an interaction."""
        collector = TraceCollector()
        collector.start_trace("test", "service")

        interaction = collector.record_interaction(
            from_component="Client",
            to_component="API",
            action="POST /login",
            interaction_type=InteractionType.HTTP_REQUEST,
            request_data={"username": "test"},
            status="success",
        )

        assert interaction is not None
        assert interaction.from_component == "Client"
        assert interaction.to_component == "API"
        assert interaction.action == "POST /login"
        assert len(collector._current_trace.interactions) == 1

    def test_record_interaction_registers_components(self):
        """Test that recording interaction auto-registers components."""
        collector = TraceCollector()
        collector.start_trace("test", "service")

        collector.record_interaction(
            from_component="Client", to_component="API", action="GET /users"
        )

        assert "Client" in collector._component_registry
        assert "API" in collector._component_registry

    def test_record_logic_branch(self):
        """Test recording a logic branch."""
        collector = TraceCollector()
        collector.start_trace("test", "service")

        branch = collector.record_logic_branch(
            condition="response.status == 200", decision="true", reason="Valid response"
        )

        assert branch is not None
        assert branch.condition == "response.status == 200"
        assert branch.decision == "true"
        assert branch.reason == "Valid response"
        assert len(collector._current_trace.logic_branches) == 1

    def test_record_assertion(self):
        """Test recording an assertion."""
        collector = TraceCollector()
        collector.start_trace("test", "service")

        # Passed assertion
        branch = collector.record_assertion(assertion="status == 200", passed=True)

        assert branch.decision == "passed"
        assert branch.type == LogicBranchType.ASSERTION

        # Failed assertion
        branch = collector.record_assertion(
            assertion="body contains 'success'",
            passed=False,
            expected_value="'success'",
            actual_value="'error'",
        )

        assert branch.decision == "failed"
        assert "Expected: 'success'" in branch.reason
        assert "Got: 'error'" in branch.reason

    def test_get_current_trace(self):
        """Test getting current trace."""
        collector = TraceCollector()

        assert collector.get_current_trace() is None

        collector.start_trace("test", "service")
        assert collector.get_current_trace() is not None

        collector.end_trace()
        assert collector.get_current_trace() is None

    def test_get_completed_traces(self):
        """Test getting completed traces."""
        collector = TraceCollector()
        collector.start_trace("test1", "service")
        collector.end_trace("passed")

        collector.start_trace("test2", "service")
        collector.end_trace("failed")

        completed = collector.get_completed_traces()

        assert len(completed) == 2
        assert completed[0].status == "passed"
        assert completed[1].status == "failed"

    def test_get_all_traces(self):
        """Test getting all traces including current."""
        collector = TraceCollector()
        collector.start_trace("test1", "service")
        collector.end_trace("passed")

        collector.start_trace("test2", "service")
        # Don't end this one

        all_traces = collector.get_all_traces()

        assert len(all_traces) == 2
        assert all_traces[1].status == "running"  # Current trace

    def test_clear(self):
        """Test clearing collector."""
        collector = TraceCollector()
        collector.start_trace("test", "service")
        collector.register_component("API", "service")
        collector.record_interaction("Client", "API", "GET /test")
        collector.end_trace()

        collector.clear()

        assert collector._current_trace is None
        assert collector._completed_traces == []
        assert collector._component_registry == {}
        assert collector._interaction_counter == 0

    def test_truncate_data(self):
        """Test data truncation."""
        config = TraceConfig(max_body_size=50)
        collector = TraceCollector(config)

        # Small data should not be truncated
        small_data = {"key": "value"}
        result = collector._truncate_data(small_data)
        assert result == small_data

        # Large data should be truncated
        large_data = {"key": "x" * 1000}
        result = collector._truncate_data(large_data)
        assert result.get("_truncated") is True
        assert "_original_size" in result


class TestGlobalCollector:
    """Tests for global collector functions."""

    def test_get_set_global_collector(self):
        """Test getting and setting global collector."""
        # Initially None
        assert get_global_collector() is None

        # Set collector
        collector = TraceCollector()
        set_global_collector(collector)

        assert get_global_collector() is collector

        # Reset
        set_global_collector(None)
        assert get_global_collector() is None

    def test_create_collector(self):
        """Test create_collector helper."""
        config = TraceConfig(output_format="plantuml")
        collector = create_collector(config)

        assert isinstance(collector, TraceCollector)
        assert collector.config.output_format == "plantuml"
