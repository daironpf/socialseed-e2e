"""Tests for sequence diagram generator."""

from datetime import datetime

import pytest

from socialseed_e2e.core.traceability.models import (
    Component,
    Interaction,
    InteractionType,
    TestTrace,
)
from socialseed_e2e.core.traceability.sequence_diagram import SequenceDiagramGenerator


class TestSequenceDiagramGenerator:
    """Tests for SequenceDiagramGenerator class."""

    @pytest.fixture
    def generator(self):
        """Create a generator instance."""
        return SequenceDiagramGenerator()

    @pytest.fixture
    def sample_trace(self):
        """Create a sample test trace."""
        trace = TestTrace(
            test_id="test-001",
            test_name="test_login_flow",
            service_name="auth-service",
            start_time=datetime.now(),
            end_time=datetime.now(),
            status="passed",
        )

        # Add components
        trace.components.append(Component(name="Client", type="client"))
        trace.components.append(Component(name="Auth-Service", type="service"))
        trace.components.append(Component(name="Database", type="database"))

        # Add interactions
        trace.interactions.append(
            Interaction(
                id="int_0001",
                type=InteractionType.HTTP_REQUEST,
                from_component="Client",
                to_component="Auth-Service",
                action="POST /login",
                timestamp=datetime.now(),
                duration_ms=150.0,
                status="success",
                request_data={"username": "test", "password": "secret"},
                response_data={"token": "abc123"},
            )
        )

        trace.interactions.append(
            Interaction(
                id="int_0002",
                type=InteractionType.DATABASE_QUERY,
                from_component="Auth-Service",
                to_component="Database",
                action="SELECT user",
                timestamp=datetime.now(),
                duration_ms=50.0,
                status="success",
            )
        )

        return trace

    def test_generate_mermaid(self, generator, sample_trace):
        """Test Mermaid diagram generation."""
        diagram = generator.generate_mermaid(sample_trace, title="Login Flow")

        assert diagram.title == "Login Flow"
        assert diagram.format == "mermaid"
        assert "sequenceDiagram" in diagram.content
        assert "Client" in diagram.content
        assert "Auth-Service" in diagram.content
        assert "Database" in diagram.content
        assert "POST /login" in diagram.content
        assert len(diagram.components) == 3

    def test_generate_mermaid_with_participants(self, generator, sample_trace):
        """Test Mermaid diagram includes participant declarations."""
        diagram = generator.generate_mermaid(sample_trace)

        content = diagram.content
        # Should have participant declarations
        assert "participant Client" in content or "actor Client" in content
        assert "participant Auth-Service" in content
        assert "database Database" in content

    def test_generate_mermaid_with_interactions(self, generator, sample_trace):
        """Test Mermaid diagram includes interaction arrows."""
        diagram = generator.generate_mermaid(sample_trace)

        content = diagram.content
        # Should have arrows
        assert "->>" in content  # Solid arrow for success
        assert "POST /login" in content
        assert "SELECT user" in content

    def test_generate_mermaid_with_timestamps(self, generator, sample_trace):
        """Test Mermaid diagram with timestamps."""
        diagram = generator.generate_mermaid(sample_trace, include_timestamps=True)

        # Should have time notes
        assert "Note" in diagram.content

    def test_generate_mermaid_without_timestamps(self, generator, sample_trace):
        """Test Mermaid diagram without timestamps."""
        diagram = generator.generate_mermaid(sample_trace, include_timestamps=False)

        # Should not have time-related notes for interactions
        # (still has start/end notes)
        pass

    def test_generate_mermaid_with_duration(self, generator, sample_trace):
        """Test Mermaid diagram includes duration."""
        diagram = generator.generate_mermaid(sample_trace, include_duration=True)

        # Should show duration in ms
        assert "150ms" in diagram.content or "150.0ms" in diagram.content

    def test_generate_mermaid_with_status(self, generator, sample_trace):
        """Test Mermaid diagram shows test status."""
        diagram = generator.generate_mermaid(sample_trace)

        # Should show passed status
        assert "PASSED" in diagram.content.upper() or "passed" in diagram.content

    def test_generate_mermaid_with_error(self, generator):
        """Test Mermaid diagram with error interaction."""
        trace = TestTrace(
            test_id="test-002",
            test_name="test_error",
            service_name="test-service",
            start_time=datetime.now(),
            end_time=datetime.now(),
            status="failed",
        )

        trace.components.append(Component(name="Client", type="client"))
        trace.components.append(Component(name="API", type="service"))

        trace.interactions.append(
            Interaction(
                id="int_0001",
                type=InteractionType.HTTP_REQUEST,
                from_component="Client",
                to_component="API",
                action="POST /invalid",
                timestamp=datetime.now(),
                status="error",
                error_message="Invalid request",
            )
        )

        diagram = generator.generate_mermaid(trace)

        # Should show error indicator
        assert "--x" in diagram.content  # X arrow for error
        assert "FAILED" in diagram.content.upper() or "failed" in diagram.content

    def test_generate_plantuml(self, generator, sample_trace):
        """Test PlantUML diagram generation."""
        diagram = generator.generate_plantuml(sample_trace, title="Login Flow")

        assert diagram.title == "Login Flow"
        assert diagram.format == "plantuml"
        assert "@startuml" in diagram.content
        assert "@enduml" in diagram.content
        assert "title Login Flow" in diagram.content

    def test_generate_plantuml_with_participants(self, generator, sample_trace):
        """Test PlantUML diagram includes participants."""
        diagram = generator.generate_plantuml(sample_trace)

        content = diagram.content
        # Should have participant declarations
        assert 'participant "Client"' in content or 'actor "Client"' in content
        assert 'participant "Auth-Service"' in content
        assert 'database "Database"' in content

    def test_generate_plantuml_with_messages(self, generator, sample_trace):
        """Test PlantUML diagram includes messages."""
        diagram = generator.generate_plantuml(sample_trace)

        content = diagram.content
        # Should have messages
        assert "->" in content  # Arrow
        assert "POST /login" in content

    def test_generate_plantuml_with_activation(self, generator, sample_trace):
        """Test PlantUML diagram includes activation bars."""
        diagram = generator.generate_plantuml(sample_trace)

        content = diagram.content
        # Should have activate/deactivate
        assert "activate" in content.lower()
        assert "deactivate" in content.lower()

    def test_generate_both(self, generator, sample_trace):
        """Test generating both Mermaid and PlantUML."""
        diagrams = generator.generate_both(sample_trace)

        assert len(diagrams) == 2
        assert diagrams[0].format == "mermaid"
        assert diagrams[1].format == "plantuml"

    def test_empty_trace(self, generator):
        """Test diagram generation with empty trace."""
        trace = TestTrace(
            test_id="test-003",
            test_name="empty_test",
            service_name="test-service",
            start_time=datetime.now(),
            end_time=datetime.now(),
            status="passed",
        )

        diagram = generator.generate_mermaid(trace)

        assert diagram.format == "mermaid"
        assert "sequenceDiagram" in diagram.content
        # Should still have start and end
        assert "Test started" in diagram.content
        assert "PASSED" in diagram.content.upper()

    def test_group_by_service(self, generator, sample_trace):
        """Test Mermaid diagram with service grouping."""
        diagram = generator.generate_mermaid(sample_trace, group_by_service=True)

        # Should have grouping rectangles
        assert "rect" in diagram.content.lower()

    def test_safe_alias_creation(self, generator):
        """Test that component names are converted to safe aliases."""
        trace = TestTrace(
            test_id="test-004",
            test_name="alias_test",
            service_name="test-service",
            start_time=datetime.now(),
        )

        # Component with spaces and special characters
        trace.components.append(Component(name="My Service-API", type="service"))
        trace.components.append(Component(name="Client", type="client"))

        trace.interactions.append(
            Interaction(
                id="int_0001",
                type=InteractionType.HTTP_REQUEST,
                from_component="Client",
                to_component="My Service-API",
                action="GET /test",
                timestamp=datetime.now(),
            )
        )

        diagram = generator.generate_mermaid(trace)

        # Should use safe aliases
        assert "My_Service_API" in diagram.content or "MyServiceAPI" in diagram.content
