"""Base gRPC page for testing gRPC APIs.

This module provides a BaseGrpcPage class for testing gRPC services,
offering a similar interface to BasePage but adapted for gRPC protocol.
"""

import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Type, TypeVar

try:
    import grpc
    from grpc import (
        Channel,
        ChannelCredentials,
        insecure_channel,
        secure_channel,
        ssl_channel_credentials,
    )
    HAS_GRPC = True
except ImportError:
    HAS_GRPC = False
    # Define placeholder types for type hinting to avoid errors
    Channel = Any
    ChannelCredentials = Any
    insecure_channel = Any
    secure_channel = Any
    ssl_channel_credentials = Any

from socialseed_e2e.utils.state_management import DynamicStateMixin

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class GrpcRetryConfig:
    """Configuration for gRPC retry mechanism.

    Attributes:
        max_retries: Maximum number of retry attempts (default: 3)
        backoff_factor: Exponential backoff multiplier (default: 1.0)
        max_backoff: Maximum backoff time in seconds (default: 60)
        retry_codes: List of gRPC status codes to retry on
    """

    max_retries: int = 3
    backoff_factor: float = 1.0
    max_backoff: float = 60.0
    retry_codes: Optional[List[int]] = None

    def __post_init__(self):
        """Initialize default retry configuration values."""
        if self.retry_codes is None:
            # Retry on UNAVAILABLE, DEADLINE_EXCEEDED, RESOURCE_EXHAUSTED
            self.retry_codes = [14, 4, 8]


@dataclass
class GrpcCallLog:
    """Log entry for a single gRPC call.

    Attributes:
        service: Service name
        method: Method name
        request: Request data
        timestamp: When the call was made
        duration_ms: Call duration in milliseconds
        status_code: gRPC status code
        response: Response data (if successful)
        error: Error message if call failed
    """

    service: str
    method: str
    request: Any
    timestamp: float
    duration_ms: float = 0.0
    status_code: Optional[int] = None
    response: Optional[Any] = None
    error: Optional[str] = None


class BaseGrpcPage(DynamicStateMixin):
    """Base page for testing gRPC APIs.

    This class provides a foundation for creating gRPC service pages,
    similar to BasePage for REST APIs. It handles channel management,
    retry logic, and logging.

    Example:
        >>> page = BaseGrpcPage("localhost:50051")
        >>> page.setup()
        >>> # Use in tests
        >>> page.teardown()

    Attributes:
        host: gRPC server host:port
        channel: gRPC channel instance
        use_tls: Whether to use TLS/SSL
        credentials: Channel credentials for secure connections
        timeout: Default timeout for calls in seconds
        retry_config: Retry configuration
        call_logs: List of all gRPC call logs
    """

    def __init__(
        self,
        host: str,
        use_tls: bool = False,
        credentials: Optional[ChannelCredentials] = None,
        timeout: float = 30.0,
        retry_config: Optional[GrpcRetryConfig] = None,
        **kwargs,
    ):
        """Initialize the gRPC page.

        Args:
            host: gRPC server address (e.g., "localhost:50051")
            use_tls: Whether to use TLS/SSL connection
            credentials: Channel credentials (auto-generated if use_tls=True)
            timeout: Default timeout for gRPC calls in seconds
            retry_config: Configuration for retry logic
            **kwargs: Additional arguments passed to parent classes
        """
        self.host = host
        self.use_tls = use_tls
        self.credentials = credentials
        self.timeout = timeout
        self.retry_config = retry_config or GrpcRetryConfig()
        self.call_logs: List[GrpcCallLog] = []
        self._channel: Optional[Channel] = None
        self._stubs: Dict[str, Any] = {}

        # Initialize state management
        self.init_dynamic_state()

        # Check and lazily suggest/install gRPC if missing
        if not HAS_GRPC:
            from socialseed_e2e.cli import check_and_install_extra
            if not check_and_install_extra("grpc", auto_install=True):
                raise ImportError("gRPC is not installed. Run 'e2e install-extras grpc' to install it.")

    def setup(self) -> "BaseGrpcPage":
        """Set up the gRPC channel.

        Returns:
            Self for method chaining
        """
        if self.use_tls:
            if self.credentials is None:
                self.credentials = ssl_channel_credentials()
            self._channel = secure_channel(self.host, self.credentials)
        else:
            self._channel = insecure_channel(self.host)

        logger.info(f"gRPC channel established to {self.host} (TLS={self.use_tls})")
        return self

    def teardown(self) -> None:
        """Close the gRPC channel."""
        if self._channel:
            self._channel.close()
            self._channel = None
            logger.info("gRPC channel closed")

    @property
    def channel(self) -> Channel:
        """Get the gRPC channel.

        Returns:
            The gRPC channel instance

        Raises:
            RuntimeError: If setup() hasn't been called
        """
        if self._channel is None:
            raise RuntimeError("Channel not initialized. Call setup() first.")
        return self._channel

    def register_stub(self, name: str, stub_class: Type[T]) -> T:
        """Register a gRPC stub.

        Args:
            name: Name to identify the stub
            stub_class: The stub class from generated protobuf code

        Returns:
            Instance of the stub class
        """
        stub = stub_class(self._channel)
        self._stubs[name] = stub
        return stub

    def get_stub(self, name: str) -> Any:
        """Get a registered stub.

        Args:
            name: Name of the registered stub

        Returns:
            The stub instance

        Raises:
            KeyError: If stub not found
        """
        if name not in self._stubs:
            raise KeyError(f"Stub '{name}' not registered. Use register_stub() first.")
        return self._stubs[name]

    def call(
        self,
        stub_name: str,
        method_name: str,
        request: Any,
        timeout: Optional[float] = None,
        metadata: Optional[Dict[str, str]] = None,
        retry: bool = True,
    ) -> Any:
        """Make a gRPC call with retry logic and logging.

        Args:
            stub_name: Name of the registered stub
            method_name: Method name to call on the stub
            request: Request message
            timeout: Call timeout (uses default if None)
            metadata: Call metadata (headers)
            retry: Whether to retry on failure

        Returns:
            Response from the gRPC call

        Raises:
            grpc.RpcError: If the call fails after all retries
        """
        stub = self.get_stub(stub_name)
        method = getattr(stub, method_name, None)
        if method is None:
            raise AttributeError(
                f"Method '{method_name}' not found on stub '{stub_name}'"
            )

        call_timeout = timeout or self.timeout
        call_metadata = [(k, v) for k, v in (metadata or {}).items()]

        # Initialize log entry
        log_entry = GrpcCallLog(
            service=stub_name,
            method=method_name,
            request=request,
            timestamp=time.time(),
        )

        last_error = None
        retries = 0
        max_retries = self.retry_config.max_retries if retry else 0

        while retries <= max_retries:
            try:
                start_time = time.time()

                # Make the call
                if call_metadata:
                    response = method(
                        request, timeout=call_timeout, metadata=call_metadata
                    )
                else:
                    response = method(request, timeout=call_timeout)

                # Update log entry
                log_entry.duration_ms = (time.time() - start_time) * 1000
                log_entry.status_code = grpc.StatusCode.OK.value[0]
                log_entry.response = response

                self.call_logs.append(log_entry)
                logger.debug(f"gRPC call succeeded: {stub_name}.{method_name}")

                return response

            except grpc.RpcError as e:
                last_error = e
                code = e.code()
                log_entry.status_code = code.value[0]
                log_entry.error = str(e)

                # Check if we should retry
                retry_codes = self.retry_config.retry_codes or []
                code_value = code.value[0] if code.value else None
                if (
                    retry
                    and code_value is not None
                    and code_value in retry_codes
                    and retries < max_retries
                ):
                    retries += 1
                    backoff = min(
                        self.retry_config.backoff_factor * (2 ** (retries - 1)),
                        self.retry_config.max_backoff,
                    )
                    logger.warning(
                        f"gRPC call failed with {code}, retrying {retries}/{max_retries} "
                        f"after {backoff:.1f}s"
                    )
                    time.sleep(backoff)
                else:
                    break

        # All retries exhausted or non-retryable error
        self.call_logs.append(log_entry)
        if last_error is not None:
            logger.error(f"gRPC call failed: {stub_name}.{method_name} - {last_error}")
            raise last_error
        else:
            raise RuntimeError(f"gRPC call failed: {stub_name}.{method_name}")

    def assert_ok(self, response: Any, context: str = "") -> None:
        """Assert that a gRPC call was successful.

        Args:
            response: The gRPC response
            context: Optional context message for assertion errors
        """
        if response is None:
            message = "gRPC response is None"
            if context:
                message = f"{context}: {message}"
            raise AssertionError(message)
        logger.debug(f"Assertion passed: {context or 'gRPC call'}")

    def get_call_logs(self) -> List[GrpcCallLog]:
        """Get all gRPC call logs.

        Returns:
            List of call log entries
        """
        return self.call_logs.copy()

    def clear_logs(self) -> None:
        """Clear all call logs."""
        self.call_logs.clear()

    def __enter__(self) -> "BaseGrpcPage":
        """Context manager entry."""
        self.setup()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.teardown()
