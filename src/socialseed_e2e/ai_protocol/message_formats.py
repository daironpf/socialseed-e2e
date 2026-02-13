"""Standardized message formats for AI Agent Communication Protocol.

This module defines the standardized input/output formats for communication
between AI agents and the framework.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class MessageType(str, Enum):
    """Types of messages in the protocol."""

    REQUEST = "request"
    RESPONSE = "response"
    EVENT = "event"
    ERROR = "error"
    PROGRESS = "progress"
    CAPABILITY = "capability"
    HANDSHAKE = "handshake"


class IntentType(str, Enum):
    """Types of intents that can be recognized."""

    GENERATE_TESTS = "generate_tests"
    EXECUTE_TESTS = "execute_tests"
    ANALYZE_CODE = "analyze_code"
    FIX_TEST = "fix_test"
    CREATE_SERVICE = "create_service"
    CONFIGURE = "configure"
    QUERY = "query"
    VALIDATE = "validate"
    REFACTOR = "refactor"
    DOCUMENT = "document"
    UNKNOWN = "unknown"


class Priority(str, Enum):
    """Priority levels for requests."""

    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


@dataclass
class MessageHeader:
    """Header for all protocol messages."""

    message_id: str
    message_type: MessageType
    timestamp: datetime = field(default_factory=datetime.utcnow)
    version: str = "1.0.0"
    correlation_id: Optional[str] = None
    source: str = "ai_agent"
    target: str = "e2e_framework"

    def to_dict(self) -> Dict[str, Any]:
        """Convert header to dictionary."""
        return {
            "message_id": self.message_id,
            "message_type": self.message_type.value,
            "timestamp": self.timestamp.isoformat(),
            "version": self.version,
            "correlation_id": self.correlation_id,
            "source": self.source,
            "target": self.target,
        }


@dataclass
class Intent:
    """Recognized intent from user input."""

    intent_type: IntentType
    confidence: float
    entities: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    raw_input: str = ""
    alternative_intents: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert intent to dictionary."""
        return {
            "intent_type": self.intent_type.value,
            "confidence": self.confidence,
            "entities": self.entities,
            "context": self.context,
            "raw_input": self.raw_input,
            "alternative_intents": self.alternative_intents,
        }


@dataclass
class RequestPayload:
    """Payload for request messages."""

    intent: Intent
    parameters: Dict[str, Any] = field(default_factory=dict)
    options: Dict[str, Any] = field(default_factory=dict)
    priority: Priority = Priority.NORMAL
    timeout_seconds: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert payload to dictionary."""
        return {
            "intent": self.intent.to_dict(),
            "parameters": self.parameters,
            "options": self.options,
            "priority": self.priority.value,
            "timeout_seconds": self.timeout_seconds,
            "metadata": self.metadata,
        }


@dataclass
class ResponsePayload:
    """Payload for response messages."""

    success: bool
    data: Any = None
    message: str = ""
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    execution_time_ms: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert payload to dictionary."""
        return {
            "success": self.success,
            "data": self.data,
            "message": self.message,
            "warnings": self.warnings,
            "suggestions": self.suggestions,
            "execution_time_ms": self.execution_time_ms,
            "metadata": self.metadata,
        }


@dataclass
class ErrorPayload:
    """Payload for error messages."""

    error_code: str
    error_message: str
    error_type: str = "general"
    recoverable: bool = False
    suggestions: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert payload to dictionary."""
        return {
            "error_code": self.error_code,
            "error_message": self.error_message,
            "error_type": self.error_type,
            "recoverable": self.recoverable,
            "suggestions": self.suggestions,
            "details": self.details,
            "stack_trace": self.stack_trace,
        }


@dataclass
class ProgressPayload:
    """Payload for progress messages."""

    progress_percent: float
    status: str
    current_step: str
    total_steps: Optional[int] = None
    current_step_number: Optional[int] = None
    estimated_remaining_seconds: Optional[int] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert payload to dictionary."""
        return {
            "progress_percent": self.progress_percent,
            "status": self.status,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "current_step_number": self.current_step_number,
            "estimated_remaining_seconds": self.estimated_remaining_seconds,
            "details": self.details,
        }


@dataclass
class CapabilityPayload:
    """Payload for capability messages."""

    capabilities: List[Dict[str, Any]] = field(default_factory=list)
    requirements: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert payload to dictionary."""
        return {
            "capabilities": self.capabilities,
            "requirements": self.requirements,
            "constraints": self.constraints,
        }


@dataclass
class ProtocolMessage:
    """Standardized protocol message."""

    header: MessageHeader
    payload: Union[
        RequestPayload,
        ResponsePayload,
        ErrorPayload,
        ProgressPayload,
        CapabilityPayload,
        Dict[str, Any],
    ]

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return {
            "header": self.header.to_dict(),
            "payload": self.payload.to_dict()
            if hasattr(self.payload, "to_dict")
            else self.payload,
        }

    @classmethod
    def create_request(
        cls,
        message_id: str,
        intent: Intent,
        parameters: Dict[str, Any] = None,
        priority: Priority = Priority.NORMAL,
    ) -> "ProtocolMessage":
        """Create a request message."""
        header = MessageHeader(
            message_id=message_id,
            message_type=MessageType.REQUEST,
        )
        payload = RequestPayload(
            intent=intent,
            parameters=parameters or {},
            priority=priority,
        )
        return cls(header=header, payload=payload)

    @classmethod
    def create_response(
        cls,
        message_id: str,
        correlation_id: str,
        success: bool,
        data: Any = None,
        message: str = "",
    ) -> "ProtocolMessage":
        """Create a response message."""
        header = MessageHeader(
            message_id=message_id,
            message_type=MessageType.RESPONSE,
            correlation_id=correlation_id,
        )
        payload = ResponsePayload(
            success=success,
            data=data,
            message=message,
        )
        return cls(header=header, payload=payload)

    @classmethod
    def create_error(
        cls,
        message_id: str,
        correlation_id: str,
        error_code: str,
        error_message: str,
        recoverable: bool = False,
    ) -> "ProtocolMessage":
        """Create an error message."""
        header = MessageHeader(
            message_id=message_id,
            message_type=MessageType.ERROR,
            correlation_id=correlation_id,
        )
        payload = ErrorPayload(
            error_code=error_code,
            error_message=error_message,
            recoverable=recoverable,
        )
        return cls(header=header, payload=payload)

    @classmethod
    def create_progress(
        cls,
        message_id: str,
        correlation_id: str,
        progress_percent: float,
        status: str,
        current_step: str,
    ) -> "ProtocolMessage":
        """Create a progress message."""
        header = MessageHeader(
            message_id=message_id,
            message_type=MessageType.PROGRESS,
            correlation_id=correlation_id,
        )
        payload = ProgressPayload(
            progress_percent=progress_percent,
            status=status,
            current_step=current_step,
        )
        return cls(header=header, payload=payload)


# Predefined error codes
ERROR_CODES = {
    "INVALID_INTENT": "The intent could not be recognized or is not supported",
    "MISSING_PARAMETER": "Required parameter is missing",
    "INVALID_PARAMETER": "Parameter value is invalid",
    "CAPABILITY_NOT_SUPPORTED": "The requested capability is not supported",
    "TIMEOUT": "Request timed out",
    "EXECUTION_ERROR": "Error during execution",
    "RESOURCE_NOT_FOUND": "Requested resource not found",
    "PERMISSION_DENIED": "Permission denied for the requested operation",
    "FRAMEWORK_ERROR": "Internal framework error",
    "PROTOCOL_ERROR": "Protocol violation or invalid message format",
}


def create_success_response(
    correlation_id: str,
    data: Any = None,
    message: str = "Operation completed successfully",
) -> ProtocolMessage:
    """Helper to create a success response."""
    import uuid

    return ProtocolMessage.create_response(
        message_id=str(uuid.uuid4()),
        correlation_id=correlation_id,
        success=True,
        data=data,
        message=message,
    )


def create_error_response(
    correlation_id: str,
    error_code: str,
    error_message: str,
    recoverable: bool = False,
) -> ProtocolMessage:
    """Helper to create an error response."""
    import uuid

    return ProtocolMessage.create_error(
        message_id=str(uuid.uuid4()),
        correlation_id=correlation_id,
        error_code=error_code,
        error_message=error_message,
        recoverable=recoverable,
    )
