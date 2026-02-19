"""Advanced Real-Time Protocol Testing Module.

This module provides comprehensive WebSocket and Server-Sent Events (SSE) testing:
- WebSocket connection lifecycle management
- Message sequencing and ordering validation
- SSE event stream parsing and testing
- Connection stability and reconnection testing
- Latency measurement for real-time APIs

Usage:
    from socialseed_e2e.realtime import (
        WebSocketTester,
        SSETester,
        RealtimeAssertions,
    )
"""

import json
import queue
import ssl
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set
from enum import Enum
from urllib.parse import urlparse

import websocket


class ConnectionState(str, Enum):
    """WebSocket connection states."""

    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class MessageType(str, Enum):
    """WebSocket message types."""

    TEXT = "text"
    BINARY = "binary"
    PING = "ping"
    PONG = "pong"
    CLOSE = "close"


@dataclass
class WebSocketMessage:
    """Represents a WebSocket message."""

    type: MessageType
    data: Any
    timestamp: datetime = field(default_factory=datetime.now)
    sequence_number: int = 0

    @property
    def is_text(self) -> bool:
        """Check if message is text."""
        return self.type == MessageType.TEXT

    @property
    def is_binary(self) -> bool:
        """Check if message is binary."""
        return self.type == MessageType.BINARY


@dataclass
class ConnectionMetrics:
    """WebSocket connection metrics."""

    connect_time_ms: float = 0.0
    total_messages: int = 0
    text_messages: int = 0
    binary_messages: int = 0
    pings_sent: int = 0
    pongs_received: int = 0
    total_bytes: int = 0
    reconnect_count: int = 0


class WebSocketTester:
    """Comprehensive WebSocket testing.

    Example:
        tester = WebSocketTester("ws://localhost:8080/ws")

        # Connect with authentication
        tester.connect(headers={"Authorization": "Bearer token"})

        # Send and receive messages
        tester.send({"type": "subscribe", "channel": "updates"})
        response = tester.receive(timeout=5)

        # Test message ordering
        tester.assert_ordered(messages)

        tester.disconnect()
    """

    def __init__(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        subprotocols: Optional[List[str]] = None,
    ):
        """Initialize WebSocket tester.

        Args:
            url: WebSocket URL
            headers: Optional headers for connection
            subprotocols: Optional list of subprotocols
        """
        self.url = url
        self.headers = headers or {}
        self.subprotocols = subprotocols or []
        self.ws: Optional[websocket.WebSocket] = None
        self.state = ConnectionState.DISCONNECTED
        self.message_queue: queue.Queue = queue.Queue()
        self.metrics = ConnectionMetrics()
        self._sequence = 0
        self._lock = threading.Lock()
        self._listeners: Dict[str, Callable] = {}

    def connect(self, timeout: float = 10.0) -> bool:
        """Connect to WebSocket server.

        Args:
            timeout: Connection timeout in seconds

        Returns:
            True if connected successfully
        """
        start_time = time.perf_counter()

        try:
            self.ws = websocket.WebSocket(
                header=self.headers,
                subprotocols=self.subprotocols,
            )

            # Parse URL for SSL context
            parsed = urlparse(self.url)
            sslopt = {}
            if parsed.scheme == "wss":
                sslopt = {"cert_reqs": ssl.CERT_NONE}

            self.ws.settimeout(timeout)
            self.ws.connect(self.url, sslopt=sslopt)

            self.state = ConnectionState.CONNECTED
            self.metrics.connect_time_ms = (time.perf_counter() - start_time) * 1000

            # Start message listener
            self._start_listener()

            return True

        except Exception as e:
            self.state = ConnectionState.ERROR
            print(f"Connection failed: {e}")
            return False

    def disconnect(self) -> None:
        """Disconnect from WebSocket server."""
        if self.ws:
            self.state = ConnectionState.DISCONNECTING
            try:
                self.ws.close()
            except Exception:
                pass
            self.state = ConnectionState.DISCONNECTED

    def send(
        self,
        data: Any,
        binary: bool = False,
    ) -> bool:
        """Send message to WebSocket server.

        Args:
            data: Message data (will be JSON encoded if dict)
            binary: Send as binary instead of text

        Returns:
            True if sent successfully
        """
        if self.state != ConnectionState.CONNECTED:
            return False

        try:
            if isinstance(data, dict):
                message = json.dumps(data)
            else:
                message = str(data)

            self.ws.send(message, binary=binary)
            self.metrics.total_messages += 1

            if binary:
                self.metrics.binary_messages += 1
                self.metrics.total_bytes += len(message)
            else:
                self.metrics.text_messages += 1
                self.metrics.total_bytes += len(message.encode())

            return True

        except Exception as e:
            print(f"Send failed: {e}")
            return False

    def receive(self, timeout: Optional[float] = None) -> Optional[WebSocketMessage]:
        """Receive message from WebSocket server.

        Args:
            timeout: Optional timeout in seconds

        Returns:
            WebSocketMessage or None
        """
        try:
            if timeout:
                message = self.message_queue.get(timeout=timeout)
            else:
                message = self.message_queue.get_nowait()
            return message
        except queue.Empty:
            return None

    def receive_all(self, timeout: float = 1.0) -> List[WebSocketMessage]:
        """Receive all available messages.

        Args:
            timeout: Timeout in seconds

        Returns:
            List of messages
        """
        messages = []
        end_time = time.time() + timeout

        while time.time() < end_time:
            remaining = end_time - time.time()
            if remaining <= 0:
                break

            msg = self.receive(timeout=min(remaining, 0.1))
            if msg:
                messages.append(msg)
            else:
                break

        return messages

    def ping(self) -> bool:
        """Send ping to server.

        Returns:
            True if ping sent
        """
        if self.state != ConnectionState.CONNECTED:
            return False

        try:
            self.ws.ping()
            self.metrics.pings_sent += 1
            return True
        except Exception:
            return False

    def assert_ordered(
        self,
        messages: List[WebSocketMessage],
    ) -> bool:
        """Assert messages are in order.

        Args:
            messages: List of messages to check

        Returns:
            True if messages are ordered
        """
        for i in range(len(messages) - 1):
            if messages[i].sequence_number >= messages[i + 1].sequence_number:
                return False
        return True

    def assert_no_duplicates(
        self,
        messages: List[WebSocketMessage],
    ) -> bool:
        """Assert no duplicate messages.

        Args:
            messages: List of messages to check

        Returns:
            True if no duplicates
        """
        seen = set()
        for msg in messages:
            if msg.data in seen:
                return False
            seen.add(msg.data)
        return True

    def on(self, event: str, callback: Callable) -> None:
        """Register event listener.

        Args:
            event: Event name
            callback: Callback function
        """
        self._listeners[event] = callback

    def _start_listener(self) -> None:
        """Start message listener thread."""

        def listen():
            while self.state == ConnectionState.CONNECTED:
                try:
                    if self.ws:
                        data = self.ws.recv()
                        if data:
                            self._handle_message(data)
                except websocket.WebSocketTimeoutException:
                    pass
                except Exception:
                    break

        thread = threading.Thread(target=listen, daemon=True)
        thread.start()

    def _handle_message(self, data: Any) -> None:
        """Handle incoming message."""
        with self._lock:
            self._sequence += 1

        msg_type = MessageType.TEXT
        if isinstance(data, bytes):
            msg_type = MessageType.BINARY

        message = WebSocketMessage(
            type=msg_type,
            data=data,
            sequence_number=self._sequence,
        )

        self.message_queue.put(message)

        # Trigger listeners
        if "message" in self._listeners:
            self._listeners["message"](message)

    def get_metrics(self) -> ConnectionMetrics:
        """Get connection metrics.

        Returns:
            ConnectionMetrics object
        """
        return self.metrics

    def get_queue_size(self) -> int:
        """Get number of queued messages.

        Returns:
            Queue size
        """
        return self.message_queue.qsize()


class SSETester:
    """Server-Sent Events testing.

    Example:
        tester = SSETester("http://localhost:8080/events")

        # Connect and listen
        tester.connect()
        events = tester.listen(duration=10)

        # Check event types
        tester.assert_event_type(events, "message")
        tester.assert_event_id(events, "last-id")

        tester.disconnect()
    """

    def __init__(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
    ):
        """Initialize SSE tester.

        Args:
            url: SSE endpoint URL
            headers: Optional headers
        """
        self.url = url
        self.headers = headers or {}
        self.event_queue: queue.Queue = queue.Queue()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self.last_event_id: Optional[str] = None
        self.retry_count: int = 0

    def connect(self) -> bool:
        """Connect to SSE endpoint.

        Returns:
            True if connected
        """
        self._running = True
        self._thread = threading.Thread(target=self._listen, daemon=True)
        self._thread.start()
        return True

    def disconnect(self) -> None:
        """Disconnect from SSE endpoint."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)

    def listen(self, duration: Optional[float] = None) -> List[Dict[str, Any]]:
        """Listen for events.

        Args:
            duration: Duration to listen in seconds

        Returns:
            List of events
        """
        events = []
        end_time = time.time() + duration if duration else None

        while True:
            if end_time and time.time() > end_time:
                break

            try:
                event = self.event_queue.get(timeout=0.5)
                events.append(event)
            except queue.Empty:
                if duration:
                    break
                continue

        return events

    def assert_event_type(
        self,
        events: List[Dict[str, Any]],
        event_type: str,
    ) -> bool:
        """Assert all events are of specific type.

        Args:
            events: List of events
            event_type: Expected event type

        Returns:
            True if all events match type
        """
        return all(e.get("type") == event_type for e in events)

    def assert_event_id(
        self,
        events: List[Dict[str, Any]],
        expected_id: str,
    ) -> bool:
        """Assert events have expected ID.

        Args:
            events: List of events
            expected_id: Expected event ID

        Returns:
            True if all events have expected ID
        """
        return all(e.get("id") == expected_id for e in events)

    def assert_no_dropped_events(
        self,
        events: List[Dict[str, Any]],
    ) -> bool:
        """Assert no events were dropped.

        Args:
            events: List of events

        Returns:
            True if no gaps in event IDs
        """
        ids = [e.get("id") for e in events if e.get("id")]
        if not ids:
            return True

        # Check for gaps (simple check)
        for i in range(len(ids) - 1):
            if ids[i + 1] != str(int(ids[i]) + 1):
                return False
        return True

    def _listen(self) -> None:
        """Listen for SSE events."""
        import urllib.request

        while self._running:
            try:
                request = urllib.request.Request(self.url, headers=self.headers)
                with urllib.request.urlopen(request) as response:
                    self._parse_sse(response)

            except Exception as e:
                print(f"SSE connection error: {e}")
                self.retry_count += 1
                time.sleep(1)

    def _parse_sse(self, response) -> None:
        """Parse SSE stream."""
        event_data = {}
        for line in response:
            if not self._running:
                break

            line = line.decode("utf-8").strip()

            if line.startswith(":"):
                continue

            if ":" in line:
                key, value = line.split(":", 1)
                value = value.strip()

                if key == "event":
                    event_data["type"] = value
                elif key == "data":
                    event_data["data"] = value
                elif key == "id":
                    event_data["id"] = value
                    self.last_event_id = value
                elif key == "retry":
                    event_data["retry"] = value

            elif line == "":
                if event_data:
                    self.event_queue.put(event_data.copy())
                    event_data.clear()


class RealtimeAssertions:
    """Assertions for real-time protocols.

    Example:
        assertions = RealtimeAssertions()

        # Latency assertions
        assertions.assert_latency_acceptable(50, max_ms=100)

        # Ordering assertions
        assertions.assert_ordered(messages)

        # Stability assertions
        assertions.assert_stable_connection(metrics)
    """

    def assert_latency_acceptable(
        self,
        latency_ms: float,
        max_ms: float = 100.0,
    ) -> bool:
        """Assert latency is within acceptable range.

        Args:
            latency_ms: Measured latency
            max_ms: Maximum acceptable latency

        Returns:
            True if acceptable
        """
        return latency_ms <= max_ms

    def assert_ordered(
        self,
        messages: List[WebSocketMessage],
    ) -> bool:
        """Assert messages are in order.

        Args:
            messages: List of messages

        Returns:
            True if ordered
        """
        for i in range(len(messages) - 1):
            if messages[i].timestamp > messages[i + 1].timestamp:
                return False
        return True

    def assert_stable_connection(
        self,
        metrics: ConnectionMetrics,
        max_reconnects: int = 3,
    ) -> bool:
        """Assert connection is stable.

        Args:
            metrics: Connection metrics
            max_reconnects: Maximum reconnect count

        Returns:
            True if stable
        """
        return metrics.reconnect_count <= max_reconnects

    def assert_message_count(
        self,
        messages: List[WebSocketMessage],
        expected: int,
    ) -> bool:
        """Assert expected message count.

        Args:
            messages: List of messages
            expected: Expected count

        Returns:
            True if matches
        """
        return len(messages) == expected

    def assert_binary_ratio(
        self,
        metrics: ConnectionMetrics,
        min_ratio: float = 0.0,
    ) -> bool:
        """Assert minimum binary message ratio.

        Args:
            metrics: Connection metrics
            min_ratio: Minimum ratio (0-1)

        Returns:
            True if acceptable
        """
        if metrics.total_messages == 0:
            return True

        ratio = metrics.binary_messages / metrics.total_messages
        return ratio >= min_ratio


class RealtimeSuite:
    """Comprehensive real-time protocol testing suite.

    Example:
        suite = RealtimeSuite()

        # Test WebSocket
        ws_response = suite.test_websocket("ws://localhost:8080/ws")

        # Test SSE
        sse_events = suite.test_sse("http://localhost:8080/events")

        # Generate report
        report = suite.get_report()
    """

    def __init__(self):
        """Initialize real-time testing suite."""
        self.ws_tester: Optional[WebSocketTester] = None
        self.sse_tester: Optional[SSETester] = None
        self.results: List[Dict[str, Any]] = []

    def test_websocket(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        test_messages: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Test WebSocket connection.

        Args:
            url: WebSocket URL
            headers: Optional headers
            test_messages: Optional test messages to send

        Returns:
            Test results
        """
        self.ws_tester = WebSocketTester(url, headers)
        result = {"type": "websocket", "url": url}

        # Connect
        connected = self.ws_tester.connect()
        result["connected"] = connected

        if not connected:
            result["success"] = False
            self.results.append(result)
            return result

        # Send test messages
        if test_messages:
            for msg in test_messages:
                self.ws_tester.send(msg)
                time.sleep(0.1)

        # Receive messages
        messages = self.ws_tester.receive_all(timeout=2)
        result["messages_received"] = len(messages)

        # Get metrics
        result["metrics"] = {
            "connect_time_ms": self.ws_tester.metrics.connect_time_ms,
            "total_messages": self.ws_tester.metrics.total_messages,
            "text_messages": self.ws_tester.metrics.text_messages,
            "binary_messages": self.ws_tester.metrics.binary_messages,
        }

        # Disconnect
        self.ws_tester.disconnect()

        result["success"] = True
        self.results.append(result)
        return result

    def test_sse(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        duration: float = 5.0,
    ) -> Dict[str, Any]:
        """Test SSE connection.

        Args:
            url: SSE URL
            headers: Optional headers
            duration: Listen duration in seconds

        Returns:
            Test results
        """
        self.sse_tester = SSETester(url, headers)
        result = {"type": "sse", "url": url}

        # Connect
        connected = self.sse_tester.connect()
        result["connected"] = connected

        if not connected:
            result["success"] = False
            self.results.append(result)
            return result

        # Listen for events
        events = self.sse_tester.listen(duration=duration)
        result["events_received"] = len(events)

        # Analyze events
        event_types = set(e.get("type") for e in events if e.get("type"))
        result["event_types"] = list(event_types)

        # Disconnect
        self.sse_tester.disconnect()

        result["success"] = True
        self.results.append(result)
        return result

    def get_report(self) -> Dict[str, Any]:
        """Get test report.

        Returns:
            Test report
        """
        total = len(self.results)
        successes = sum(1 for r in self.results if r.get("success"))

        return {
            "total_tests": total,
            "passed": successes,
            "failed": total - successes,
            "success_rate": (successes / total * 100) if total > 0 else 0,
            "results": self.results,
        }
