"""Tests for Real-Time Protocol Testing Module.

This module tests the WebSocket and SSE testing features.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch

from socialseed_e2e.realtime import (
    ConnectionMetrics,
    ConnectionState,
    MessageType,
    RealtimeAssertions,
    RealtimeSuite,
    SSETester,
    WebSocketMessage,
    WebSocketTester,
)


class TestWebSocketMessage:
    """Tests for WebSocketMessage."""

    def test_text_message(self):
        """Test text message type."""
        msg = WebSocketMessage(type=MessageType.TEXT, data="hello")
        assert msg.is_text is True
        assert msg.is_binary is False

    def test_binary_message(self):
        """Test binary message type."""
        msg = WebSocketMessage(type=MessageType.BINARY, data=b"hello")
        assert msg.is_binary is True
        assert msg.is_text is False


class TestConnectionMetrics:
    """Tests for ConnectionMetrics."""

    def test_initialization(self):
        """Test metrics initialization."""
        metrics = ConnectionMetrics()
        assert metrics.connect_time_ms == 0.0
        assert metrics.total_messages == 0
        assert metrics.reconnect_count == 0


class TestWebSocketTester:
    """Tests for WebSocketTester."""

    def test_initialization(self):
        """Test WebSocket tester initialization."""
        tester = WebSocketTester("ws://localhost:8080/ws")
        assert tester.url == "ws://localhost:8080/ws"
        assert tester.state == ConnectionState.DISCONNECTED

    def test_initialization_with_headers(self):
        """Test initialization with headers."""
        headers = {"Authorization": "Bearer token"}
        tester = WebSocketTester("ws://localhost:8080/ws", headers=headers)
        assert tester.headers == headers


class TestSSETester:
    """Tests for SSETester."""

    def test_initialization(self):
        """Test SSE tester initialization."""
        tester = SSETester("http://localhost:8080/events")
        assert tester.url == "http://localhost:8080/events"
        assert tester.last_event_id is None
        assert tester.retry_count == 0


class TestRealtimeAssertions:
    """Tests for RealtimeAssertions."""

    def test_latency_acceptable(self):
        """Test latency assertion."""
        assertions = RealtimeAssertions()
        assert assertions.assert_latency_acceptable(50, max_ms=100) is True
        assert assertions.assert_latency_acceptable(150, max_ms=100) is False

    def test_ordered_messages(self):
        """Test message ordering assertion."""
        from datetime import datetime

        assertions = RealtimeAssertions()
        messages = [
            WebSocketMessage(
                type=MessageType.TEXT,
                data="a",
                timestamp=datetime(2024, 1, 1, 10, 0, 0),
            ),
            WebSocketMessage(
                type=MessageType.TEXT,
                data="b",
                timestamp=datetime(2024, 1, 1, 10, 0, 1),
            ),
            WebSocketMessage(
                type=MessageType.TEXT,
                data="c",
                timestamp=datetime(2024, 1, 1, 10, 0, 2),
            ),
        ]
        assert assertions.assert_ordered(messages) is True

    def test_stable_connection(self):
        """Test connection stability assertion."""
        assertions = RealtimeAssertions()
        metrics = ConnectionMetrics(reconnect_count=2)
        assert assertions.assert_stable_connection(metrics, max_reconnects=3) is True
        assert assertions.assert_stable_connection(metrics, max_reconnects=1) is False

    def test_message_count(self):
        """Test message count assertion."""
        assertions = RealtimeAssertions()
        messages = [
            WebSocketMessage(type=MessageType.TEXT, data="a"),
            WebSocketMessage(type=MessageType.TEXT, data="b"),
        ]
        assert assertions.assert_message_count(messages, 2) is True
        assert assertions.assert_message_count(messages, 3) is False

    def test_binary_ratio(self):
        """Test binary message ratio assertion."""
        assertions = RealtimeAssertions()
        metrics = ConnectionMetrics(total_messages=10, binary_messages=5)
        assert assertions.assert_binary_ratio(metrics, min_ratio=0.4) is True
        assert assertions.assert_binary_ratio(metrics, min_ratio=0.7) is False


class TestRealtimeSuite:
    """Tests for RealtimeSuite."""

    def test_initialization(self):
        """Test suite initialization."""
        suite = RealtimeSuite()
        assert suite.ws_tester is None
        assert suite.sse_tester is None
        assert suite.results == []

    def test_get_report_empty(self):
        """Test report with no results."""
        suite = RealtimeSuite()
        report = suite.get_report()
        assert report["total_tests"] == 0
        assert report["passed"] == 0
        assert report["failed"] == 0

    def test_get_report_with_results(self):
        """Test report with results."""
        suite = RealtimeSuite()
        suite.results = [
            {"success": True},
            {"success": True},
            {"success": False},
        ]
        report = suite.get_report()
        assert report["total_tests"] == 3
        assert report["passed"] == 2
        assert report["failed"] == 1
        assert report["success_rate"] == pytest.approx(66.67, rel=0.1)


class TestSSETesterMethods:
    """Tests for SSETester methods."""

    def test_assert_event_type(self):
        """Test event type assertion."""
        tester = SSETester("http://localhost:8080/events")
        events = [
            {"type": "message", "data": "hello"},
            {"type": "message", "data": "world"},
        ]
        assert tester.assert_event_type(events, "message") is True
        assert tester.assert_event_type(events, "error") is False

    def test_assert_event_id(self):
        """Test event ID assertion."""
        tester = SSETester("http://localhost:8080/events")
        events = [
            {"id": "1", "data": "a"},
            {"id": "1", "data": "b"},
        ]
        assert tester.assert_event_id(events, "1") is True
        assert tester.assert_event_id(events, "2") is False

    def test_assert_no_dropped_events(self):
        """Test no dropped events assertion."""
        tester = SSETester("http://localhost:8080/events")
        events = [
            {"id": "1"},
            {"id": "2"},
            {"id": "3"},
        ]
        assert tester.assert_no_dropped_events(events) is True


class TestWebSocketTesterMethods:
    """Tests for WebSocketTester methods."""

    def test_get_metrics(self):
        """Test getting metrics."""
        tester = WebSocketTester("ws://localhost:8080/ws")
        metrics = tester.get_metrics()
        assert isinstance(metrics, ConnectionMetrics)

    def test_get_queue_size(self):
        """Test getting queue size."""
        tester = WebSocketTester("ws://localhost:8080/ws")
        assert tester.get_queue_size() == 0

    def test_on_listener(self):
        """Test event listener registration."""
        tester = WebSocketTester("ws://localhost:8080/ws")

        def callback(msg):
            pass

        tester.on("message", callback)
        assert "message" in tester._listeners
