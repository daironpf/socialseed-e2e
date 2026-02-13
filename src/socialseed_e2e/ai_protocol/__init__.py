"""AI Protocol Engine - Main entry point for AI Agent Communication Protocol.

This module provides the main protocol engine that integrates all components
for standardized communication between AI agents and the framework.
"""

import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union

from socialseed_e2e.ai_protocol.capability_registry import (
    Capability,
    CapabilityNegotiation,
    CapabilityRegistry,
    Requirement,
)
from socialseed_e2e.ai_protocol.error_handler import (
    ErrorContext,
    ErrorHandler,
    ProtocolError,
)
from socialseed_e2e.ai_protocol.intent_parser import ContextualIntentParser, Intent
from socialseed_e2e.ai_protocol.message_formats import (
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


@dataclass
class ProtocolContext:
    """Context for protocol operations."""

    session_id: str
    agent_capabilities: List[str] = field(default_factory=list)
    negotiated_capabilities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class AIProtocolEngine:
    """Main engine for AI Agent Communication Protocol.

    This engine provides a standardized interface for communication
    between AI agents and the framework, handling:
    - Intent recognition
    - Capability negotiation
    - Progress reporting
    - Error handling
    - Message routing
    """

    def __init__(self):
        """Initialize the protocol engine."""
        self.intent_parser = ContextualIntentParser()
        self.capability_registry = CapabilityRegistry()
        self.error_handler = ErrorHandler()
        self.progress_tracker = MultiOperationProgressTracker()
        self.contexts: Dict[str, ProtocolContext] = {}
        self.message_handlers: Dict[
            MessageType, Callable[[ProtocolMessage], ProtocolMessage]
        ] = {}
        self.intent_handlers: Dict[
            IntentType, Callable[[Intent, ProtocolContext], Any]
        ] = {}

        # Register default message handlers
        self._register_default_handlers()

    def _register_default_handlers(self) -> None:
        """Register default message handlers."""
        self.message_handlers[MessageType.REQUEST] = self._handle_request
        self.message_handlers[MessageType.CAPABILITY] = self._handle_capability_message

    def initialize_session(
        self,
        agent_capabilities: List[str] = None,
        agent_requirements: List[Requirement] = None,
    ) -> str:
        """Initialize a new communication session.

        Args:
            agent_capabilities: Capabilities the agent supports
            agent_requirements: Requirements the agent has

        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())

        # Negotiate capabilities
        negotiation = self.capability_registry.negotiate_capabilities(
            agent_offered=agent_capabilities or [],
            agent_requirements=agent_requirements or [],
        )

        # Create context
        context = ProtocolContext(
            session_id=session_id,
            agent_capabilities=agent_capabilities or [],
            negotiated_capabilities=negotiation.agreed_capabilities,
        )
        self.contexts[session_id] = context

        return session_id

    def process_message(self, message: ProtocolMessage) -> ProtocolMessage:
        """Process an incoming protocol message.

        Args:
            message: Incoming message

        Returns:
            Response message
        """
        # Validate message
        validation_error = self.error_handler.validate_message(message)
        if validation_error:
            return self.error_handler.handle_error(
                validation_error,
                correlation_id=message.header.message_id if message.header else None,
            )

        # Get handler for message type
        handler = self.message_handlers.get(message.header.message_type)
        if not handler:
            return create_error_response(
                correlation_id=message.header.message_id,
                error_code="PROTOCOL_ERROR",
                error_message=f"Unsupported message type: {message.header.message_type.value}",
            )

        # Handle message
        try:
            return handler(message)
        except Exception as e:
            return self.error_handler.handle_error(
                e,
                correlation_id=message.header.message_id,
            )

    def _handle_request(self, message: ProtocolMessage) -> ProtocolMessage:
        """Handle a request message.

        Args:
            message: Request message

        Returns:
            Response message
        """
        from socialseed_e2e.ai_protocol.message_formats import RequestPayload

        payload = message.payload
        if not isinstance(payload, RequestPayload):
            return create_error_response(
                correlation_id=message.header.message_id,
                error_code="PROTOCOL_ERROR",
                error_message="Invalid request payload",
            )

        intent = payload.intent

        # Get context
        context = self.contexts.get(message.header.correlation_id)
        if not context:
            return create_error_response(
                correlation_id=message.header.message_id,
                error_code="PROTOCOL_ERROR",
                error_message="Invalid or expired session",
            )

        # Check capability
        if not self._check_capability(intent.intent_type, context):
            return create_error_response(
                correlation_id=message.header.message_id,
                error_code="CAPABILITY_NOT_SUPPORTED",
                error_message=f"Intent '{intent.intent_type.value}' is not supported",
            )

        # Get intent handler
        handler = self.intent_handlers.get(intent.intent_type)
        if not handler:
            return create_error_response(
                correlation_id=message.header.message_id,
                error_code="INVALID_INTENT",
                error_message=f"No handler for intent: {intent.intent_type.value}",
            )

        # Execute handler with progress tracking
        operation_id = f"{context.session_id}_{intent.intent_type.value}"
        reporter = self.progress_tracker.register_operation(operation_id, total_steps=3)

        try:
            # Start operation
            reporter.start_step("initialization")

            # Execute
            reporter.start_step("execution")
            result = handler(intent, context)
            reporter.update_progress(100.0)

            # Complete
            reporter.complete_step()
            reporter.complete_operation()

            return create_success_response(
                correlation_id=message.header.message_id,
                data=result,
                message=f"Successfully processed {intent.intent_type.value}",
            )

        except Exception as e:
            reporter.fail_operation(str(e))
            return self.error_handler.handle_error(
                e,
                context=ErrorContext(
                    operation_id=operation_id,
                    intent=intent.intent_type.value,
                ),
                correlation_id=message.header.message_id,
            )

    def _handle_capability_message(self, message: ProtocolMessage) -> ProtocolMessage:
        """Handle a capability message.

        Args:
            message: Capability message

        Returns:
            Response message
        """
        from socialseed_e2e.ai_protocol.message_formats import CapabilityPayload

        payload = message.payload
        if not isinstance(payload, CapabilityPayload):
            return create_error_response(
                correlation_id=message.header.message_id,
                error_code="PROTOCOL_ERROR",
                error_message="Invalid capability payload",
            )

        # Return framework capabilities
        capabilities = self.capability_registry.list_framework_capabilities()

        return create_success_response(
            correlation_id=message.header.message_id,
            data={
                "capabilities": [cap.to_dict() for cap in capabilities],
                "version": "1.0.0",
            },
            message="Capabilities retrieved successfully",
        )

    def _check_capability(
        self, intent_type: IntentType, context: ProtocolContext
    ) -> bool:
        """Check if an intent is supported by negotiated capabilities.

        Args:
            intent_type: Intent to check
            context: Protocol context

        Returns:
            True if supported
        """
        capability_map = {
            IntentType.GENERATE_TESTS: "test_generation",
            IntentType.EXECUTE_TESTS: "test_execution",
            IntentType.ANALYZE_CODE: "manifest_generation",
            IntentType.FIX_TEST: "code_fixing",
            IntentType.CREATE_SERVICE: "test_generation",
            IntentType.CONFIGURE: "test_generation",
            IntentType.QUERY: "manifest_generation",
            IntentType.VALIDATE: "test_execution",
            IntentType.REFACTOR: "code_fixing",
            IntentType.DOCUMENT: "manifest_generation",
        }

        required_capability = capability_map.get(intent_type)
        if not required_capability:
            return True

        return required_capability in context.negotiated_capabilities

    def register_intent_handler(
        self, intent_type: IntentType, handler: Callable[[Intent, ProtocolContext], Any]
    ) -> None:
        """Register a handler for an intent type.

        Args:
            intent_type: Type of intent
            handler: Handler function
        """
        self.intent_handlers[intent_type] = handler

    def parse_user_input(self, user_input: str, session_id: str = None) -> Intent:
        """Parse user input and recognize intent.

        Args:
            user_input: User input string
            session_id: Optional session ID for context

        Returns:
            Recognized intent
        """
        context = None
        if session_id and session_id in self.contexts:
            context = self.contexts[session_id].metadata

        return self.intent_parser.parse_with_context(user_input, context)

    def get_session_context(self, session_id: str) -> Optional[ProtocolContext]:
        """Get session context.

        Args:
            session_id: Session ID

        Returns:
            Protocol context or None
        """
        return self.contexts.get(session_id)

    def close_session(self, session_id: str) -> None:
        """Close a session.

        Args:
            session_id: Session ID to close
        """
        if session_id in self.contexts:
            del self.contexts[session_id]

    def get_progress(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """Get progress for an operation.

        Args:
            operation_id: Operation ID

        Returns:
            Progress summary or None
        """
        reporter = self.progress_tracker.get_operation(operation_id)
        if reporter:
            return reporter.get_progress_summary()
        return None

    def get_all_progress(self) -> Dict[str, Dict[str, Any]]:
        """Get progress for all operations.

        Returns:
            Dictionary of progress summaries
        """
        return self.progress_tracker.get_all_progress()

    def create_request_message(
        self,
        user_input: str,
        session_id: str,
        parameters: Dict[str, Any] = None,
        priority: Priority = Priority.NORMAL,
    ) -> ProtocolMessage:
        """Create a request message from user input.

        Args:
            user_input: User input string
            session_id: Session ID
            parameters: Additional parameters
            priority: Request priority

        Returns:
            Request message
        """
        # Parse intent
        intent = self.parse_user_input(user_input, session_id)

        # Create message
        message_id = str(uuid.uuid4())

        return ProtocolMessage.create_request(
            message_id=message_id,
            intent=intent,
            parameters=parameters or {},
            priority=priority,
        )

    def get_capabilities(self) -> Dict[str, Any]:
        """Get all framework capabilities.

        Returns:
            Capabilities dictionary
        """
        return self.capability_registry.get_capability_matrix()

    def negotiate_capabilities(
        self,
        agent_capabilities: List[str],
        agent_requirements: List[Requirement] = None,
    ) -> CapabilityNegotiation:
        """Negotiate capabilities with an agent.

        Args:
            agent_capabilities: Capabilities the agent offers
            agent_requirements: Requirements the agent has

        Returns:
            Negotiation result
        """
        return self.capability_registry.negotiate_capabilities(
            agent_offered=agent_capabilities,
            agent_requirements=agent_requirements or [],
        )
