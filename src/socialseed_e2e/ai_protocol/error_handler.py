"""Error Handler for AI Agent Communication Protocol.

This module provides standardized error handling for the protocol.
"""

import traceback
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Union

from socialseed_e2e.ai_protocol.message_formats import (
    ErrorPayload,
    MessageHeader,
    MessageType,
    ProtocolMessage,
)


class ProtocolError(Exception):
    """Base exception for protocol errors."""

    def __init__(
        self,
        error_code: str,
        message: str,
        recoverable: bool = False,
        details: Dict[str, Any] = None,
    ):
        super().__init__(message)
        self.error_code = error_code
        self.error_message = message
        self.recoverable = recoverable
        self.details = details or {}


class IntentRecognitionError(ProtocolError):
    """Error when intent cannot be recognized."""

    def __init__(
        self,
        message: str = "Intent could not be recognized",
        details: Dict[str, Any] = None,
    ):
        super().__init__("INVALID_INTENT", message, recoverable=True, details=details)


class CapabilityNotSupportedError(ProtocolError):
    """Error when a capability is not supported."""

    def __init__(self, capability: str, details: Dict[str, Any] = None):
        super().__init__(
            "CAPABILITY_NOT_SUPPORTED",
            f"Capability '{capability}' is not supported",
            recoverable=False,
            details=details,
        )


class MissingParameterError(ProtocolError):
    """Error when a required parameter is missing."""

    def __init__(self, parameter: str, details: Dict[str, Any] = None):
        super().__init__(
            "MISSING_PARAMETER",
            f"Required parameter '{parameter}' is missing",
            recoverable=True,
            details=details,
        )


class InvalidParameterError(ProtocolError):
    """Error when a parameter value is invalid."""

    def __init__(self, parameter: str, value: Any, details: Dict[str, Any] = None):
        super().__init__(
            "INVALID_PARAMETER",
            f"Invalid value for parameter '{parameter}': {value}",
            recoverable=True,
            details=details,
        )


class TimeoutError(ProtocolError):
    """Error when operation times out."""

    def __init__(self, operation: str, timeout: int, details: Dict[str, Any] = None):
        super().__init__(
            "TIMEOUT",
            f"Operation '{operation}' timed out after {timeout} seconds",
            recoverable=True,
            details=details,
        )


class ExecutionError(ProtocolError):
    """Error during execution."""

    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__("EXECUTION_ERROR", message, recoverable=False, details=details)


class ResourceNotFoundError(ProtocolError):
    """Error when a resource is not found."""

    def __init__(
        self, resource_type: str, resource_id: str, details: Dict[str, Any] = None
    ):
        super().__init__(
            "RESOURCE_NOT_FOUND",
            f"{resource_type} '{resource_id}' not found",
            recoverable=False,
            details=details,
        )


class PermissionDeniedError(ProtocolError):
    """Error when permission is denied."""

    def __init__(self, operation: str, details: Dict[str, Any] = None):
        super().__init__(
            "PERMISSION_DENIED",
            f"Permission denied for operation '{operation}'",
            recoverable=False,
            details=details,
        )


class ProtocolVersionError(ProtocolError):
    """Error when protocol version is incompatible."""

    def __init__(self, expected: str, actual: str, details: Dict[str, Any] = None):
        super().__init__(
            "PROTOCOL_VERSION_ERROR",
            f"Protocol version mismatch: expected {expected}, got {actual}",
            recoverable=False,
            details=details,
        )


@dataclass
class ErrorContext:
    """Context information for an error."""

    operation_id: Optional[str] = None
    step: Optional[str] = None
    user_input: Optional[str] = None
    intent: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ErrorHandler:
    """Handler for protocol errors."""

    # Map error codes to exception types
    ERROR_MAP = {
        "INVALID_INTENT": IntentRecognitionError,
        "CAPABILITY_NOT_SUPPORTED": CapabilityNotSupportedError,
        "MISSING_PARAMETER": MissingParameterError,
        "INVALID_PARAMETER": InvalidParameterError,
        "TIMEOUT": TimeoutError,
        "EXECUTION_ERROR": ExecutionError,
        "RESOURCE_NOT_FOUND": ResourceNotFoundError,
        "PERMISSION_DENIED": PermissionDeniedError,
        "PROTOCOL_VERSION_ERROR": ProtocolVersionError,
    }

    def __init__(self):
        """Initialize the error handler."""
        self.error_callbacks: List[Callable[[ProtocolError, ErrorContext], None]] = []
        self.recovery_strategies: Dict[str, Callable[[ProtocolError], Any]] = {}

    def register_error_callback(
        self, callback: Callable[[ProtocolError, ErrorContext], None]
    ) -> None:
        """Register a callback for error handling.

        Args:
            callback: Function to call when an error occurs
        """
        self.error_callbacks.append(callback)

    def register_recovery_strategy(
        self, error_code: str, strategy: Callable[[ProtocolError], Any]
    ) -> None:
        """Register a recovery strategy for an error code.

        Args:
            error_code: Error code to handle
            strategy: Recovery function
        """
        self.recovery_strategies[error_code] = strategy

    def handle_error(
        self,
        error: Union[ProtocolError, Exception],
        context: ErrorContext = None,
        correlation_id: str = None,
    ) -> ProtocolMessage:
        """Handle an error and create an error response.

        Args:
            error: The error to handle
            context: Error context
            correlation_id: Correlation ID for the message

        Returns:
            Error protocol message
        """
        context = context or ErrorContext()

        # Convert exception to ProtocolError if needed
        if not isinstance(error, ProtocolError):
            protocol_error = self._wrap_exception(error)
        else:
            protocol_error = error

        # Notify callbacks
        for callback in self.error_callbacks:
            try:
                callback(protocol_error, context)
            except Exception:
                pass

        # Try recovery if recoverable
        if (
            protocol_error.recoverable
            and protocol_error.error_code in self.recovery_strategies
        ):
            try:
                self.recovery_strategies[protocol_error.error_code](protocol_error)
            except Exception:
                pass

        # Create error message
        return self._create_error_message(protocol_error, correlation_id)

    def _wrap_exception(self, exception: Exception) -> ProtocolError:
        """Wrap a standard exception in a ProtocolError.

        Args:
            exception: Exception to wrap

        Returns:
            ProtocolError
        """
        return ExecutionError(
            message=str(exception),
            details={
                "exception_type": type(exception).__name__,
                "stack_trace": traceback.format_exc(),
            },
        )

    def _create_error_message(
        self, error: ProtocolError, correlation_id: str = None
    ) -> ProtocolMessage:
        """Create an error protocol message.

        Args:
            error: Protocol error
            correlation_id: Correlation ID

        Returns:
            Error message
        """
        import uuid

        header = MessageHeader(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.ERROR,
            correlation_id=correlation_id,
        )

        payload = ErrorPayload(
            error_code=error.error_code,
            error_message=error.error_message,
            recoverable=error.recoverable,
            details=error.details,
            stack_trace=traceback.format_exc() if not error.recoverable else None,
            suggestions=self._get_suggestions(error),
        )

        return ProtocolMessage(header=header, payload=payload)

    def _get_suggestions(self, error: ProtocolError) -> List[str]:
        """Get suggestions for fixing the error.

        Args:
            error: The error

        Returns:
            List of suggestions
        """
        suggestions = {
            "INVALID_INTENT": [
                "Try rephrasing your request with clearer action words",
                "Check the list of supported intents",
                "Provide more context about what you want to do",
            ],
            "MISSING_PARAMETER": [
                "Check the required parameters for this operation",
                "Provide all required information in your request",
            ],
            "INVALID_PARAMETER": [
                "Check the parameter format and type requirements",
                "Review the valid values for this parameter",
            ],
            "CAPABILITY_NOT_SUPPORTED": [
                "Check the framework capabilities documentation",
                "Update to a newer version of the framework",
                "Use an alternative approach",
            ],
            "TIMEOUT": [
                "Try the operation again",
                "Break the operation into smaller steps",
                "Check system resources and try again",
            ],
            "RESOURCE_NOT_FOUND": [
                "Verify the resource identifier is correct",
                "Check if the resource exists",
                "Create the resource if needed",
            ],
        }

        return suggestions.get(
            error.error_code, ["Contact support if the issue persists"]
        )

    def create_error_from_code(
        self,
        error_code: str,
        message: str = None,
        details: Dict[str, Any] = None,
        recoverable: bool = False,
    ) -> ProtocolError:
        """Create a protocol error from an error code.

        Args:
            error_code: Error code
            message: Error message
            details: Error details
            recoverable: Whether the error is recoverable

        Returns:
            ProtocolError
        """
        error_class = self.ERROR_MAP.get(error_code, ProtocolError)

        if error_class == ProtocolError:
            return ProtocolError(
                error_code=error_code,
                message=message or f"Error occurred: {error_code}",
                recoverable=recoverable,
                details=details,
            )

        # Create specific error type
        return error_class(message or "", details)

    def validate_message(self, message: ProtocolMessage) -> Optional[ProtocolError]:
        """Validate a protocol message.

        Args:
            message: Message to validate

        Returns:
            ProtocolError if invalid, None if valid
        """
        # Check header
        if not message.header:
            return ProtocolError(
                error_code="PROTOCOL_ERROR",
                message="Message header is missing",
                recoverable=False,
            )

        if not message.header.message_id:
            return ProtocolError(
                error_code="PROTOCOL_ERROR",
                message="Message ID is missing",
                recoverable=False,
            )

        if not message.header.message_type:
            return ProtocolError(
                error_code="PROTOCOL_ERROR",
                message="Message type is missing",
                recoverable=False,
            )

        # Check payload based on type
        if message.header.message_type == MessageType.REQUEST:
            if not hasattr(message.payload, "intent") or not message.payload.intent:
                return ProtocolError(
                    error_code="PROTOCOL_ERROR",
                    message="Request payload missing intent",
                    recoverable=False,
                )

        return None


class ErrorRecoveryManager:
    """Manager for error recovery strategies."""

    def __init__(self):
        """Initialize the recovery manager."""
        self.strategies: Dict[str, List[Callable[[ProtocolError], Any]]] = {}

    def register_strategy(
        self, error_code: str, strategy: Callable[[ProtocolError], Any]
    ) -> None:
        """Register a recovery strategy.

        Args:
            error_code: Error code to handle
            strategy: Recovery function
        """
        if error_code not in self.strategies:
            self.strategies[error_code] = []
        self.strategies[error_code].append(strategy)

    def attempt_recovery(self, error: ProtocolError) -> Any:
        """Attempt to recover from an error.

        Args:
            error: The error to recover from

        Returns:
            Recovery result or raises error if recovery fails
        """
        if error.error_code not in self.strategies:
            raise error

        for strategy in self.strategies[error.error_code]:
            try:
                result = strategy(error)
                return result
            except Exception:
                continue

        # If all strategies fail, re-raise the error
        raise error

    def has_recovery_strategy(self, error_code: str) -> bool:
        """Check if a recovery strategy exists.

        Args:
            error_code: Error code to check

        Returns:
            True if strategy exists
        """
        return error_code in self.strategies and len(self.strategies[error_code]) > 0


# Convenience functions


def handle_exception(
    exception: Exception,
    correlation_id: str = None,
    context: ErrorContext = None,
) -> ProtocolMessage:
    """Handle an exception and return an error message.

    Args:
        exception: Exception to handle
        correlation_id: Correlation ID
        context: Error context

    Returns:
        Error protocol message
    """
    handler = ErrorHandler()
    return handler.handle_error(exception, context, correlation_id)


def create_validation_error(
    field: str,
    message: str,
    correlation_id: str = None,
) -> ProtocolMessage:
    """Create a validation error message.

    Args:
        field: Field that failed validation
        message: Validation message
        correlation_id: Correlation ID

    Returns:
        Error protocol message
    """
    error = InvalidParameterError(field, None, {"field": field, "message": message})
    handler = ErrorHandler()
    return handler.handle_error(error, correlation_id=correlation_id)
