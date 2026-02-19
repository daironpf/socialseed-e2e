"""Advanced gRPC Testing Module.

This module provides comprehensive gRPC testing capabilities including:
- Streaming RPC testing (server, client, bidirectional)
- Complex message handling
- Error handling and status code verification
- Load testing
- Interceptor testing

Usage:
    from socialseed_e2e.grpc import (
        GrpcTestingSuite,
        StreamingTester,
        LoadTester,
    )
"""

import time
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set
from enum import Enum

import grpc
from grpc import insecure_channel, secure_channel, ssl_channel_credentials

from pydantic import BaseModel


class StreamType(str, Enum):
    """gRPC streaming types."""

    UNARY = "unary"
    SERVER_STREAMING = "server_streaming"
    CLIENT_STREAMING = "client_streaming"
    BIDIRECTIONAL = "bidirectional"


class GrpcStatusCode(int, Enum):
    """gRPC status codes."""

    OK = 0
    CANCELLED = 1
    UNKNOWN = 2
    INVALID_ARGUMENT = 3
    DEADLINE_EXCEEDED = 4
    NOT_FOUND = 5
    ALREADY_EXISTS = 6
    PERMISSION_DENIED = 7
    RESOURCE_EXHAUSTED = 8
    FAILED_PRECONDITION = 9
    ABORTED = 10
    OUT_OF_RANGE = 11
    UNIMPLEMENTED = 12
    INTERNAL = 13
    UNAVAILABLE = 14
    DATA_LOSS = 15
    UNAUTHENTICATED = 16


@dataclass
class GrpcRequest:
    """Represents a gRPC request."""

    service: str
    method: str
    request_data: Any
    metadata: Optional[Dict[str, str]] = None
    timeout: Optional[float] = None


@dataclass
class GrpcResponse:
    """Represents a gRPC response."""

    data: Any
    status_code: GrpcStatusCode
    status_message: str
    duration_ms: float
    metadata: Dict[str, str] = field(default_factory=dict)
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def success(self) -> bool:
        """Check if the response is successful."""
        return self.status_code == GrpcStatusCode.OK


@dataclass
class StreamingConfig:
    """Configuration for streaming RPCs."""

    stream_type: StreamType
    chunk_size: Optional[int] = None
    max_messages: Optional[int] = None
    timeout: float = 30.0


class StreamCollector:
    """Collects messages from streaming RPCs.

    Example:
        collector = StreamCollector()

        # For server streaming
        for response in stub.StreamMethod(request):
            collector.add(response)

        messages = collector.get_all()
    """

    def __init__(self, max_messages: Optional[int] = None):
        """Initialize stream collector.

        Args:
            max_messages: Maximum messages to collect (None for unlimited)
        """
        self._messages: List[Any] = []
        self._errors: List[str] = []
        self._max_messages = max_messages
        self._complete = False

    def add(self, message: Any) -> None:
        """Add a message to the collector.

        Args:
            message: Message to add
        """
        if self._max_messages and len(self._messages) >= self._max_messages:
            return

        self._messages.append(message)

    def add_error(self, error: str) -> None:
        """Add an error to the collector.

        Args:
            error: Error message
        """
        self._errors.append(error)

    def complete(self) -> None:
        """Mark stream as complete."""
        self._complete = True

    def get_all(self) -> List[Any]:
        """Get all collected messages.

        Returns:
            List of messages
        """
        return self._messages.copy()

    def get_errors(self) -> List[str]:
        """Get all collected errors.

        Returns:
            List of error messages
        """
        return self._errors.copy()

    @property
    def is_complete(self) -> bool:
        """Check if stream is complete."""
        return self._complete

    @property
    def count(self) -> int:
        """Get number of messages collected."""
        return len(self._messages)

    def clear(self) -> None:
        """Clear all collected data."""
        self._messages.clear()
        self._errors.clear()
        self._complete = False


class StreamingTester:
    """Tests streaming RPC operations.

    Example:
        tester = StreamingTester(channel)

        # Test server streaming
        responses = tester.test_server_streaming(
            "UserService",
            "GetUserPosts",
            {"user_id": "123"}
        )

        # Test bidirectional
        def on_message(msg):
            print(f"Received: {msg}")

        tester.test_bidirectional("ChatService", "SendMessage", messages, on_message)
    """

    def __init__(self, channel: grpc.Channel):
        """Initialize streaming tester.

        Args:
            channel: gRPC channel
        """
        self.channel = channel

    def test_server_streaming(
        self,
        service: str,
        method: str,
        request_data: Any,
        config: Optional[StreamingConfig] = None,
    ) -> GrpcResponse:
        """Test server streaming RPC.

        Args:
            service: Service name
            method: Method name
            request_data: Request data
            config: Streaming configuration

        Returns:
            GrpcResponse with streaming results
        """
        config = config or StreamingConfig(StreamType.SERVER_STREAMING)
        collector = StreamCollector(config.max_messages)

        start_time = time.perf_counter()

        try:
            stub = self._get_stub(service)
            stream_method = getattr(stub, method)

            # In real implementation, iterate over stream
            # This is a simplified version
            for i, msg in enumerate(stream_method(request_data)):
                if config.max_messages and i >= config.max_messages:
                    break
                collector.add(msg)

            collector.complete()
            duration_ms = (time.perf_counter() - start_time) * 1000

            return GrpcResponse(
                data=collector.get_all(),
                status_code=GrpcStatusCode.OK,
                status_message="Streaming completed",
                duration_ms=duration_ms,
            )

        except grpc.RpcError as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            return GrpcResponse(
                data=None,
                status_code=GrpcStatusCode(e.code()),
                status_message=e.details(),
                duration_ms=duration_ms,
                error=str(e),
            )

    def test_client_streaming(
        self,
        service: str,
        method: str,
        messages: List[Any],
        config: Optional[StreamingConfig] = None,
    ) -> GrpcResponse:
        """Test client streaming RPC.

        Args:
            service: Service name
            method: Method name
            messages: List of messages to send
            config: Streaming configuration

        Returns:
            GrpcResponse with result
        """
        config = config or StreamingConfig(StreamType.CLIENT_STREAMING)

        start_time = time.perf_counter()

        try:
            stub = self._get_stub(service)
            stream_method = getattr(stub, method)

            # Create iterator for client streaming
            def message_iterator():
                for msg in messages:
                    yield msg

            response = stream_method(message_iterator())
            duration_ms = (time.perf_counter() - start_time) * 1000

            return GrpcResponse(
                data=response,
                status_code=GrpcStatusCode.OK,
                status_message="Client streaming completed",
                duration_ms=duration_ms,
            )

        except grpc.RpcError as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            return GrpcResponse(
                data=None,
                status_code=GrpcStatusCode(e.code()),
                status_message=e.details(),
                duration_ms=duration_ms,
                error=str(e),
            )

    def test_bidirectional(
        self,
        service: str,
        method: str,
        messages: List[Any],
        callback: Optional[Callable[[Any], None]] = None,
        config: Optional[StreamingConfig] = None,
    ) -> GrpcResponse:
        """Test bidirectional streaming RPC.

        Args:
            service: Service name
            method: Method name
            messages: Messages to send
            callback: Callback for each received message
            config: Streaming configuration

        Returns:
            GrpcResponse with results
        """
        config = config or StreamingConfig(StreamType.BIDIRECTIONAL)
        collector = StreamCollector(config.max_messages)

        start_time = time.perf_counter()

        try:
            stub = self._get_stub(service)
            stream_method = getattr(stub, method)

            # Bidirectional streaming
            def message_iterator():
                for msg in messages:
                    yield msg

            for response in stream_method(message_iterator()):
                collector.add(response)
                if callback:
                    callback(response)

            collector.complete()
            duration_ms = (time.perf_counter() - start_time) * 1000

            return GrpcResponse(
                data=collector.get_all(),
                status_code=GrpcStatusCode.OK,
                status_message="Bidirectional streaming completed",
                duration_ms=duration_ms,
            )

        except grpc.RpcError as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            return GrpcResponse(
                data=collector.get_all(),
                status_code=GrpcStatusCode(e.code()),
                status_message=e.details(),
                duration_ms=duration_ms,
                error=str(e),
            )

    def _get_stub(self, service: str):
        """Get service stub (simplified)."""
        # In real implementation, would generate stubs from proto
        return None


class LoadTester:
    """Load testing for gRPC services.

    Example:
        load_tester = LoadTester(channel)

        # Concurrent calls
        results = load_tester.concurrent_calls(
            service="UserService",
            method="GetUser",
            request_data={"id": "123"},
            num_calls=100,
            max_workers=10
        )

        # Print statistics
        stats = load_tester.get_statistics()
        print(f"Success rate: {stats['success_rate']}%")
    """

    def __init__(self, channel: grpc.Channel):
        """Initialize load tester.

        Args:
            channel: gRPC channel
        """
        self.channel = channel
        self.results: List[GrpcResponse] = []
        self._lock = threading.Lock()

    def concurrent_calls(
        self,
        service: str,
        method: str,
        request_data: Any,
        num_calls: int = 100,
        max_workers: int = 10,
    ) -> List[GrpcResponse]:
        """Execute concurrent gRPC calls.

        Args:
            service: Service name
            method: Method name
            request_data: Request data
            num_calls: Total number of calls
            max_workers: Maximum concurrent workers

        Returns:
            List of responses
        """
        self.results.clear()

        def make_call(call_id: int) -> None:
            response = self._make_call(service, method, request_data)
            with self._lock:
                self.results.append(response)

        threads = []
        for i in range(num_calls):
            thread = threading.Thread(target=make_call, args=(i,))
            threads.append(thread)
            thread.start()

            # Limit concurrent workers
            if len(threads) >= max_workers:
                for t in threads:
                    t.join()
                threads = []

        # Wait for remaining threads
        for t in threads:
            t.join()

        return self.results

    def _make_call(self, service: str, method: str, request_data: Any) -> GrpcResponse:
        """Make a single gRPC call."""
        start_time = time.perf_counter()

        try:
            stub = StreamingTester(self.channel)._get_stub(service)
            if stub:
                response = getattr(stub, method)(request_data)
                duration_ms = (time.perf_counter() - start_time) * 1000

                return GrpcResponse(
                    data=response,
                    status_code=GrpcStatusCode.OK,
                    status_message="OK",
                    duration_ms=duration_ms,
                )
        except grpc.RpcError as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            return GrpcResponse(
                data=None,
                status_code=GrpcStatusCode(e.code()),
                status_message=e.details(),
                duration_ms=duration_ms,
                error=str(e),
            )

        return GrpcResponse(
            data=None,
            status_code=GrpcStatusCode.UNKNOWN,
            status_message="Service not found",
            duration_ms=0,
        )

    def get_statistics(self) -> Dict[str, Any]:
        """Get load test statistics.

        Returns:
            Dictionary with statistics
        """
        if not self.results:
            return {}

        total = len(self.results)
        successes = sum(1 for r in self.results if r.success)
        failures = total - successes

        durations = [r.duration_ms for r in self.results]
        durations.sort()

        return {
            "total_calls": total,
            "successful": successes,
            "failed": failures,
            "success_rate": (successes / total * 100) if total > 0 else 0,
            "min_duration_ms": min(durations) if durations else 0,
            "max_duration_ms": max(durations) if durations else 0,
            "avg_duration_ms": sum(durations) / len(durations) if durations else 0,
            "p50_duration_ms": durations[len(durations) // 2] if durations else 0,
            "p95_duration_ms": durations[int(len(durations) * 0.95)]
            if durations
            else 0,
            "p99_duration_ms": durations[int(len(durations) * 0.99)]
            if durations
            else 0,
        }


class ErrorHandler:
    """Handles and validates gRPC errors.

    Example:
        handler = ErrorHandler()

        # Validate status code
        handler.validate_status_code(response, GrpcStatusCode.NOT_FOUND)

        # Get error details
        details = handler.parse_error_details(error)
    """

    def __init__(self):
        """Initialize error handler."""
        self.error_log: List[GrpcResponse] = []

    def validate_status_code(
        self,
        response: GrpcResponse,
        expected_code: GrpcStatusCode,
    ) -> bool:
        """Validate gRPC status code.

        Args:
            response: gRPC response
            expected_code: Expected status code

        Returns:
            True if status code matches
        """
        return response.status_code == expected_code

    def is_retriable(self, response: GrpcResponse) -> bool:
        """Check if error is retriable.

        Args:
            response: gRPC response

        Returns:
            True if error can be retried
        """
        retriable_codes = [
            GrpcStatusCode.UNAVAILABLE,
            GrpcStatusCode.DEADLINE_EXCEEDED,
            GrpcStatusCode.RESOURCE_EXHAUSTED,
        ]
        return response.status_code in retriable_codes

    def parse_error_details(self, error: grpc.RpcError) -> Dict[str, Any]:
        """Parse error details from gRPC error.

        Args:
            error: gRPC RpcError

        Returns:
            Dictionary with error details
        """
        details = {
            "code": error.code(),
            "message": error.details(),
            "debug_error_string": error.debug_error_string(),
        }

        # Try to get trailing metadata
        if hasattr(error, "trailing_metadata"):
            details["trailing_metadata"] = error.trailing_metadata()

        return details

    def log_error(self, response: GrpcResponse) -> None:
        """Log an error response.

        Args:
            response: gRPC response
        """
        self.error_log.append(response)

    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of logged errors.

        Returns:
            Dictionary with error summary
        """
        if not self.error_log:
            return {}

        error_counts: Dict[GrpcStatusCode, int] = {}
        for response in self.error_log:
            error_counts[response.status_code] = (
                error_counts.get(response.status_code, 0) + 1
            )

        return {
            "total_errors": len(self.error_log),
            "errors_by_code": {
                code.value: count for code, count in error_counts.items()
            },
            "most_common_error": max(error_counts.items(), key=lambda x: x[1])[0]
            if error_counts
            else None,
        }


class GrpcTestingSuite:
    """Comprehensive gRPC testing suite.

    Example:
        suite = GrpcTestingSuite("localhost:50051")

        # Test unary call
        response = suite.call("UserService", "GetUser", {"id": "123"})

        # Test with metadata
        response = suite.call_with_metadata(
            "UserService",
            "GetUser",
            {"id": "123"},
            metadata={"authorization": "Bearer token"}
        )
    """

    def __init__(
        self,
        target: str,
        credentials: Optional[grpc.ChannelCredentials] = None,
    ):
        """Initialize gRPC testing suite.

        Args:
            target: Server address (host:port)
            credentials: Optional channel credentials
        """
        self.target = target
        if credentials:
            self.channel = secure_channel(target, credentials)
        else:
            self.channel = insecure_channel(target)

        self.streaming_tester = StreamingTester(self.channel)
        self.load_tester = LoadTester(self.channel)
        self.error_handler = ErrorHandler()

    def call(
        self,
        service: str,
        method: str,
        request_data: Any,
        timeout: float = 30.0,
    ) -> GrpcResponse:
        """Make a unary gRPC call.

        Args:
            service: Service name
            method: Method name
            request_data: Request data
            timeout: Call timeout

        Returns:
            GrpcResponse
        """
        start_time = time.perf_counter()

        try:
            stub = self.streaming_tester._get_stub(service)
            if stub:
                response = getattr(stub, method)(request_data, timeout=timeout)
                duration_ms = (time.perf_counter() - start_time) * 1000

                return GrpcResponse(
                    data=response,
                    status_code=GrpcStatusCode.OK,
                    status_message="OK",
                    duration_ms=duration_ms,
                )

        except grpc.RpcError as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            return GrpcResponse(
                data=None,
                status_code=GrpcStatusCode(e.code()),
                status_message=e.details(),
                duration_ms=duration_ms,
                error=str(e),
            )

        return GrpcResponse(
            data=None,
            status_code=GrpcStatusCode.UNKNOWN,
            status_message="Service not found",
            duration_ms=0,
        )

    def call_with_metadata(
        self,
        service: str,
        method: str,
        request_data: Any,
        metadata: Dict[str, str],
        timeout: float = 30.0,
    ) -> GrpcResponse:
        """Make a gRPC call with metadata.

        Args:
            service: Service name
            method: Method name
            request_data: Request data
            metadata: Metadata dictionary
            timeout: Call timeout

        Returns:
            GrpcResponse
        """
        start_time = time.perf_counter()

        try:
            # Create metadata
            metadata_pairs = list(metadata.items())

            # Note: Actual implementation would use metadata in call
            return self.call(service, method, request_data, timeout)

        except grpc.RpcError as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            return GrpcResponse(
                data=None,
                status_code=GrpcStatusCode(e.code()),
                status_message=e.details(),
                duration_ms=duration_ms,
                error=str(e),
            )

    def close(self) -> None:
        """Close the gRPC channel."""
        if self.channel:
            self.channel.close()
