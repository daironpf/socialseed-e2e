"""Tests for traceability models."""

from datetime import datetime

import pytest

from socialseed_e2e.core.traceability.models import (
    Component,
    Interaction,
    InteractionType,
    LogicBranch,
    LogicBranchType,
    SequenceDiagram,
    TestTrace,
    TraceConfig,
    TraceReport,
)


class TestComponent:
    """Tests for Component model."""

    def test_component_creation(self):
        """Test basic component creation."""
        component = Component(
            name="Auth-Service", type="service", description="Authentication service"
        )

        assert component.name == "Auth-Service"
        assert component.type == "service"
        assert component.description == "Authentication service"
        assert component.metadata == {}

    def test_component_with_metadata(self):
        """Test component with metadata."""
        component = Component(
            name="Database",
            type="database",
            metadata={"host": "localhost", "port": 5432},
        )

        assert component.metadata["host"] == "localhost"
        assert component.metadata["port"] == 5432


class TestInteraction:
    """Tests for Interaction model."""

    def test_interaction_creation(self):
        """Test basic interaction creation."""
        interaction = Interaction(
            id="int_0001",
            type=InteractionType.HTTP_REQUEST,
            from_component="Client",
            to_component="API",
            action="POST /login",
            timestamp=datetime.now(),
        )

        assert interaction.id == "int_0001"
        assert interaction.type == InteractionType.HTTP_REQUEST
        assert interaction.from_component == "Client"
        assert interaction.to_component == "API"
        assert interaction.action == "POST /login"
        assert interaction.status == "pending"

    def test_interaction_with_request_data(self):
        """Test interaction with request/response data."""
        interaction = Interaction(
            id="int_0002",
            type=InteractionType.HTTP_REQUEST,
            from_component="Client",
            to_component="API",
            action="POST /users",
            timestamp=datetime.now(),
            request_data={"name": "John", "email": "john@example.com"},
            response_data={"id": 1, "name": "John"},
            status="success",
            duration_ms=150.5,
        )

        assert interaction.request_data["name"] == "John"
        assert interaction.response_data["id"] == 1
        assert interaction.duration_ms == 150.5
        assert interaction.status == "success"


class TestLogicBranch:
    """Tests for LogicBranch model."""

    def test_logic_branch_creation(self):
        """Test basic logic branch creation."""
        branch = LogicBranch(
            id="branch_0001",
            type=LogicBranchType.CONDITIONAL,
            condition="response.status == 200",
            decision="true",
            timestamp=datetime.now(),
        )

        assert branch.id == "branch_0001"
        assert branch.type == LogicBranchType.CONDITIONAL
        assert branch.condition == "response.status == 200"
        assert branch.decision == "true"

    def test_logic_branch_with_reason(self):
        """Test logic branch with reason."""
        branch = LogicBranch(
            id="branch_0002",
            type=LogicBranchType.ASSERTION,
            condition="assert response.status == 200",
            decision="passed",
            timestamp=datetime.now(),
            reason="Response status matches expected",
        )

        assert branch.decision == "passed"
        assert branch.reason == "Response status matches expected"


class TestTestTrace:
    """Tests for TestTrace model."""

    def test_test_trace_creation(self):
        """Test basic test trace creation."""
        trace = TestTrace(
            test_id="test-123",
            test_name="test_login",
            service_name="auth-service",
            start_time=datetime.now(),
        )

        assert trace.test_id == "test-123"
        assert trace.test_name == "test_login"
        assert trace.service_name == "auth-service"
        assert trace.status == "running"
        assert trace.interactions == []
        assert trace.logic_branches == []

    def test_test_trace_duration(self):
        """Test duration calculation."""
        start = datetime.now()
        end = datetime.now()

        trace = TestTrace(
            test_id="test-456",
            test_name="test_duration",
            service_name="test-service",
            start_time=start,
            end_time=end,
        )

        # Duration should be 0 or very small
        duration = trace.get_duration_ms()
        assert duration >= 0

    def test_test_trace_with_interactions(self):
        """Test trace with interactions."""
        trace = TestTrace(
            test_id="test-789",
            test_name="test_with_interactions",
            service_name="test-service",
            start_time=datetime.now(),
        )

        # Add component
        trace.components.append(Component(name="Client", type="client"))
        trace.components.append(Component(name="API", type="service"))

        # Add interaction
        trace.interactions.append(
            Interaction(
                id="int_0001",
                type=InteractionType.HTTP_REQUEST,
                from_component="Client",
                to_component="API",
                action="GET /users",
                timestamp=datetime.now(),
            )
        )

        assert len(trace.components) == 2
        assert len(trace.interactions) == 1

        # Test filtering
        api_interactions = trace.get_interactions_by_component("API")
        assert len(api_interactions) == 1


class TestTraceConfig:
    """Tests for TraceConfig model."""

    def test_default_config(self):
        """Test default configuration."""
        config = TraceConfig()

        assert config.enabled is True
        assert config.capture_request_body is True
        assert config.capture_response_body is True
        assert config.track_logic_branches is True
        assert config.generate_sequence_diagrams is True
        assert config.output_format == "mermaid"
        assert config.max_body_size == 10000

    def test_custom_config(self):
        """Test custom configuration."""
        config = TraceConfig(
            enabled=False,
            capture_request_body=False,
            output_format="plantuml",
            max_body_size=5000,
        )

        assert config.enabled is False
        assert config.capture_request_body is False
        assert config.output_format == "plantuml"
        assert config.max_body_size == 5000


class TestSequenceDiagram:
    """Tests for SequenceDiagram model."""

    def test_sequence_diagram_creation(self):
        """Test sequence diagram creation."""
        diagram = SequenceDiagram(
            title="Test Login Flow",
            format="mermaid",
            content="sequenceDiagram\n    Client->>API: POST /login",
            components=["Client", "API"],
            interactions_count=1,
            generated_at=datetime.now(),
        )

        assert diagram.title == "Test Login Flow"
        assert diagram.format == "mermaid"
        assert "Client->>API" in diagram.content
        assert len(diagram.components) == 2


class TestTraceReport:
    """Tests for TraceReport model."""

    def test_empty_report(self):
        """Test empty report."""
        report = TraceReport(report_id="report-001", generated_at=datetime.now(), traces=[])

        assert report.report_id == "report-001"
        assert report.get_total_interactions() == 0
        assert report.get_total_components() == 0
        assert report.get_success_rate() == 0.0

    def test_report_with_traces(self):
        """Test report with traces."""
        trace1 = TestTrace(
            test_id="test-1",
            test_name="test_passed",
            service_name="service-1",
            start_time=datetime.now(),
            status="passed",
        )
        trace1.components.append(Component(name="Client", type="client"))
        trace1.interactions.append(
            Interaction(
                id="int_1",
                type=InteractionType.HTTP_REQUEST,
                from_component="Client",
                to_component="API",
                action="GET /test",
                timestamp=datetime.now(),
            )
        )

        trace2 = TestTrace(
            test_id="test-2",
            test_name="test_failed",
            service_name="service-1",
            start_time=datetime.now(),
            status="failed",
        )
        trace2.components.append(Component(name="API", type="service"))

        report = TraceReport(
            report_id="report-002", generated_at=datetime.now(), traces=[trace1, trace2]
        )

        assert report.get_total_interactions() == 1
        assert report.get_total_components() == 2  # Unique components
        assert report.get_success_rate() == 50.0
