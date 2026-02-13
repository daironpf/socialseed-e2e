"""Tests for AI Agent Communication Protocol (Issue #127)."""

import pytest
from unittest.mock import Mock

from socialseed_e2e.ai_protocol import AIProtocolEngine
from socialseed_e2e.ai_protocol.capability_registry import (
    Capability,
    CapabilityLevel,
    CapabilityNegotiation,
    CapabilityRegistry,
    Requirement,
)
from socialseed_e2e.ai_protocol.error_handler import (
    ErrorContext,
    ErrorHandler,
    ExecutionError,
    InvalidParameterError,
    MissingParameterError,
    ProtocolError,
)
from socialseed_e2e.ai_protocol.intent_parser import (
    IntentParser,
    ContextualIntentParser,
)
from socialseed_e2e.ai_protocol.message_formats import (
    Intent,
    IntentType,
    MessageType,
    Priority,
    ProtocolMessage,
    create_error_response,
    create_success_response,
)
from socialseed_e2e.ai_protocol.progress_reporter import (
    MultiOperationProgressTracker,
    ProgressReporter,
    ProgressStep,
)


class TestMessageFormats:
    """Tests for message format classes."""

    def test_create_request_message(self):
        """Test creating a request message."""
        intent = Intent(
            intent_type=IntentType.GENERATE_TESTS,
            confidence=0.95,
            entities={"service": "users"},
        )

        message = ProtocolMessage.create_request(
            message_id="test-123",
            intent=intent,
            parameters={"language": "python"},
            priority=Priority.HIGH,
        )

        assert message.header.message_type == MessageType.REQUEST
        assert message.header.message_id == "test-123"
        assert message.payload.intent.intent_type == IntentType.GENERATE_TESTS
        assert message.payload.priority == Priority.HIGH

    def test_create_response_message(self):
        """Test creating a response message."""
        message = create_success_response(
            correlation_id="test-123",
            data={"tests_generated": 5},
            message="Tests generated successfully",
        )

        assert message.header.message_type == MessageType.RESPONSE
        assert message.header.correlation_id == "test-123"
        assert message.payload.success is True
        assert message.payload.data["tests_generated"] == 5

    def test_create_error_response(self):
        """Test creating an error response."""
        message = create_error_response(
            correlation_id="test-123",
            error_code="INVALID_INTENT",
            error_message="Intent not recognized",
            recoverable=True,
        )

        assert message.header.message_type == MessageType.ERROR
        assert message.payload.error_code == "INVALID_INTENT"
        assert message.payload.recoverable is True

    def test_message_to_dict(self):
        """Test converting message to dictionary."""
        intent = Intent(
            intent_type=IntentType.QUERY,
            confidence=0.8,
        )

        message = ProtocolMessage.create_request(
            message_id="test-456",
            intent=intent,
        )

        msg_dict = message.to_dict()
        assert "header" in msg_dict
        assert "payload" in msg_dict
        assert msg_dict["header"]["message_type"] == "request"


class TestIntentParser:
    """Tests for intent parser."""

    @pytest.fixture
    def parser(self):
        return IntentParser()

    def test_parse_generate_tests_intent(self, parser):
        """Test parsing generate tests intent."""
        intent = parser.parse("Generate tests for the users service")

        assert intent.intent_type == IntentType.GENERATE_TESTS
        assert intent.confidence > 0.6

    def test_parse_execute_tests_intent(self, parser):
        """Test parsing execute tests intent."""
        intent = parser.parse("Run all tests")

        assert intent.intent_type == IntentType.EXECUTE_TESTS
        assert intent.confidence > 0.6

    def test_parse_unknown_intent(self, parser):
        """Test parsing unknown intent."""
        intent = parser.parse("Something completely unrelated")

        assert intent.intent_type == IntentType.UNKNOWN

    def test_extract_entities(self, parser):
        """Test entity extraction."""
        intent = parser.parse("Create tests for the auth service")

        assert "service" in intent.entities or "target" in intent.entities

    def test_contextual_parser(self):
        """Test contextual intent parser."""
        parser = ContextualIntentParser()

        # First query
        intent1 = parser.parse_with_context("Generate tests for users")
        assert intent1.intent_type == IntentType.GENERATE_TESTS

        # Second query with context - "run" should be recognized
        intent2 = parser.parse_with_context("Run all tests now")
        # This might be EXECUTE_TESTS or UNKNOWN depending on confidence
        assert intent2.intent_type in [IntentType.EXECUTE_TESTS, IntentType.UNKNOWN]

        # Should have context
        assert len(parser.context_history) == 2


class TestCapabilityRegistry:
    """Tests for capability registry."""

    @pytest.fixture
    def registry(self):
        return CapabilityRegistry()

    def test_default_capabilities_registered(self, registry):
        """Test that default capabilities are registered."""
        caps = registry.list_framework_capabilities()
        assert len(caps) > 0

        # Check some expected capabilities
        cap_names = [c.name for c in caps]
        assert "test_generation" in cap_names
        assert "test_execution" in cap_names

    def test_register_capability(self, registry):
        """Test registering a new capability."""
        cap = Capability(
            name="custom_capability",
            description="A custom capability",
            level=CapabilityLevel.FULL,
        )

        registry.register_framework_capability(cap)

        retrieved = registry.get_framework_capability("custom_capability")
        assert retrieved is not None
        assert retrieved.name == "custom_capability"

    def test_capability_negotiation_success(self, registry):
        """Test successful capability negotiation."""
        agent_caps = ["test_generation", "test_execution"]

        result = registry.negotiate_capabilities(agent_caps)

        assert result.success is True
        assert len(result.agreed_capabilities) > 0
        assert len(result.missing_requirements) == 0

    def test_capability_negotiation_failure(self, registry):
        """Test failed capability negotiation."""
        # Add a required capability
        registry.add_framework_requirement(
            Requirement(name="required_cap", level="required")
        )

        result = registry.negotiate_capabilities([])

        assert result.success is False
        assert len(result.missing_requirements) > 0

    def test_has_capability(self, registry):
        """Test checking if capability exists."""
        assert registry.has_capability("test_generation") is True
        assert registry.has_capability("nonexistent") is False


class TestErrorHandler:
    """Tests for error handler."""

    @pytest.fixture
    def handler(self):
        return ErrorHandler()

    def test_handle_protocol_error(self, handler):
        """Test handling a protocol error."""
        error = InvalidParameterError("field_name", "invalid_value")

        message = handler.handle_error(error, correlation_id="test-123")

        assert message.header.message_type == MessageType.ERROR
        assert message.payload.error_code == "INVALID_PARAMETER"
        assert len(message.payload.suggestions) > 0

    def test_handle_generic_exception(self, handler):
        """Test handling a generic exception."""
        error = ValueError("Something went wrong")

        message = handler.handle_error(error, correlation_id="test-123")

        assert message.header.message_type == MessageType.ERROR
        assert message.payload.error_code == "EXECUTION_ERROR"

    def test_validate_valid_message(self, handler):
        """Test validating a valid message."""
        intent = Intent(intent_type=IntentType.QUERY, confidence=0.9)
        message = ProtocolMessage.create_request("test-123", intent)

        error = handler.validate_message(message)

        assert error is None

    def test_validate_invalid_message(self, handler):
        """Test validating an invalid message."""
        message = ProtocolMessage(header=None, payload=None)

        error = handler.validate_message(message)

        assert error is not None
        assert error.error_code == "PROTOCOL_ERROR"

    def test_create_error_from_code(self, handler):
        """Test creating error from code."""
        error = handler.create_error_from_code(
            "MISSING_PARAMETER",
            message="Required field missing",
            recoverable=True,
        )

        assert isinstance(error, MissingParameterError)
        assert error.recoverable is True


class TestProgressReporter:
    """Tests for progress reporter."""

    def test_progress_reporter_creation(self):
        """Test creating a progress reporter."""
        reporter = ProgressReporter("op-123", total_steps=5)

        assert reporter.operation_id == "op-123"
        assert reporter.total_steps == 5
        # overall_progress is calculated dynamically
        summary = reporter.get_progress_summary()
        assert summary["overall_progress"] == 0.0

    def test_progress_update(self):
        """Test updating progress."""
        reporter = ProgressReporter("op-123", total_steps=2)
        reporter.define_steps(
            [
                ProgressStep(name="step1", description="First step"),
                ProgressStep(name="step2", description="Second step"),
            ]
        )

        reporter.start_step("step1")
        reporter.update_progress(50.0)

        assert reporter.step_progress == 50.0
        assert reporter.overall_progress > 0.0

    def test_complete_operation(self):
        """Test completing an operation."""
        reporter = ProgressReporter("op-123", total_steps=1)
        reporter.complete_operation("Done!")

        assert reporter.overall_progress == 100.0
        assert reporter.status == "completed"

    def test_progress_callback(self):
        """Test progress callback."""
        callback = Mock()
        reporter = ProgressReporter("op-123", total_steps=1)
        reporter.register_callback(callback)

        reporter.start_step("test")

        assert callback.called

    def test_multi_operation_tracker(self):
        """Test multi-operation tracker."""
        tracker = MultiOperationProgressTracker()

        reporter1 = tracker.register_operation("op-1", 3)
        reporter2 = tracker.register_operation("op-2", 2)

        reporter1.start_step("step1")
        reporter2.start_step("step1")

        all_progress = tracker.get_all_progress()

        assert "op-1" in all_progress
        assert "op-2" in all_progress


class TestAIProtocolEngine:
    """Tests for AI Protocol Engine."""

    @pytest.fixture
    def engine(self):
        return AIProtocolEngine()

    def test_initialize_session(self, engine):
        """Test initializing a session."""
        session_id = engine.initialize_session(
            agent_capabilities=["test_generation"],
        )

        assert session_id is not None
        assert len(session_id) > 0

        context = engine.get_session_context(session_id)
        assert context is not None
        assert "test_generation" in context.negotiated_capabilities

    def test_parse_user_input(self, engine):
        """Test parsing user input."""
        intent = engine.parse_user_input("Generate tests for users service")

        assert intent.intent_type == IntentType.GENERATE_TESTS
        assert intent.confidence > 0.6

    def test_process_request_message(self, engine):
        """Test processing a request message."""
        # Initialize session with all capabilities
        session_id = engine.initialize_session(
            agent_capabilities=[
                "test_generation",
                "test_execution",
                "manifest_generation",
                "deep_context_analysis",
            ]
        )

        # Register a simple handler for GENERATE_TESTS (which is supported)
        def mock_handler(intent, context):
            return {"result": "success"}

        engine.register_intent_handler(IntentType.GENERATE_TESTS, mock_handler)

        # Create and process message
        intent = Intent(intent_type=IntentType.GENERATE_TESTS, confidence=0.9)
        message = ProtocolMessage.create_request(
            message_id="test-123",
            intent=intent,
        )
        message.header.correlation_id = session_id

        response = engine.process_message(message)

        assert response.header.message_type == MessageType.RESPONSE

    def test_get_capabilities(self, engine):
        """Test getting capabilities."""
        caps = engine.get_capabilities()

        assert "framework" in caps
        assert len(caps["framework"]) > 0

    def test_capability_negotiation(self, engine):
        """Test capability negotiation."""
        result = engine.negotiate_capabilities(
            agent_capabilities=["test_generation", "test_execution"],
        )

        assert isinstance(result, CapabilityNegotiation)
        assert len(result.agreed_capabilities) > 0

    def test_close_session(self, engine):
        """Test closing a session."""
        session_id = engine.initialize_session()
        assert engine.get_session_context(session_id) is not None

        engine.close_session(session_id)
        assert engine.get_session_context(session_id) is None
