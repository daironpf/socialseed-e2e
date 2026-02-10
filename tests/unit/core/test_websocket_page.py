"""Tests for WebSocket page implementation."""

import json
import sys
from pathlib import Path

import pytest

from socialseed_e2e.core.base_websocket_page import (
    WEBSOCKET_AVAILABLE,
    WebSocketConfig,
    WebSocketError,
    WebSocketLog,
    WebSocketMessage,
)

# Skip all tests if websockets not available
pytestmark = pytest.mark.skipif(
    not WEBSOCKET_AVAILABLE,
    reason="websockets package not installed",
)


class TestWebSocketConfig:
    """Test WebSocketConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = WebSocketConfig()

        assert config.connect_timeout == 10.0
        assert config.receive_timeout == 30.0
        assert config.auto_reconnect is True
        assert config.max_reconnect_attempts == 3
        assert config.reconnect_delay == 1.0
        assert config.ping_interval == 20.0
        assert config.ping_timeout == 10.0
        assert config.subprotocols is None
        assert config.headers is None

    def test_custom_values(self):
        """Test custom configuration values."""
        config = WebSocketConfig(
            connect_timeout=5.0,
            receive_timeout=15.0,
            auto_reconnect=False,
            max_reconnect_attempts=5,
            reconnect_delay=2.0,
            ping_interval=10.0,
            ping_timeout=5.0,
            subprotocols=["chat", "json"],
            headers={"Authorization": "Bearer token"},
        )

        assert config.connect_timeout == 5.0
        assert config.receive_timeout == 15.0
        assert config.auto_reconnect is False
        assert config.max_reconnect_attempts == 5
        assert config.reconnect_delay == 2.0
        assert config.ping_interval == 10.0
        assert config.ping_timeout == 5.0
        assert config.subprotocols == ["chat", "json"]
        assert config.headers == {"Authorization": "Bearer token"}


class TestWebSocketMessage:
    """Test WebSocketMessage dataclass."""

    def test_text_message(self):
        """Test text message creation."""
        msg = WebSocketMessage(
            data='{"action": "ping"}',
            message_type="text",
            direction="outgoing",
        )

        assert msg.data == '{"action": "ping"}'
        assert msg.message_type == "text"
        assert msg.direction == "outgoing"
        assert msg.is_text is True
        assert msg.is_binary is False

    def test_binary_message(self):
        """Test binary message creation."""
        msg = WebSocketMessage(
            data=b"\x00\x01\x02",
            message_type="binary",
            direction="incoming",
        )

        assert msg.data == b"\x00\x01\x02"
        assert msg.message_type == "binary"
        assert msg.direction == "incoming"
        assert msg.is_text is False
        assert msg.is_binary is True

    def test_json_parsing(self):
        """Test JSON parsing from text message."""
        msg = WebSocketMessage(
            data='{"action": "test", "value": 123}',
            message_type="text",
        )

        data = msg.json()
        assert data["action"] == "test"
        assert data["value"] == 123

    def test_json_parsing_binary(self):
        """Test JSON parsing from binary message."""
        msg = WebSocketMessage(
            data=b'{"action": "test"}',
            message_type="binary",
        )

        data = msg.json()
        assert data["action"] == "test"


class TestWebSocketLog:
    """Test WebSocketLog dataclass."""

    def test_log_creation(self):
        """Test log entry creation."""
        msg = WebSocketMessage(data="test", message_type="text")
        log = WebSocketLog(
            operation="send",
            duration_ms=100.0,
            message=msg,
        )

        assert log.operation == "send"
        assert log.duration_ms == 100.0
        assert log.message == msg
        assert log.error is None

    def test_error_log(self):
        """Test error log entry."""
        log = WebSocketLog(
            operation="connect",
            duration_ms=5000.0,
            error="Connection refused",
        )

        assert log.operation == "connect"
        assert log.error == "Connection refused"
        assert log.message is None


class TestWebSocketError:
    """Test WebSocketError exception."""

    def test_basic_error(self):
        """Test basic error creation."""
        error = WebSocketError("Connection failed")

        assert str(error) == "Connection failed"
        assert error.url is None
        assert error.code is None
        assert error.reason is None

    def test_error_with_context(self):
        """Test error with full context."""
        error = WebSocketError(
            message="Connection closed",
            url="ws://example.com/ws",
            code=1006,
            reason="Abnormal closure",
        )

        assert "Connection closed" in str(error)
        assert error.url == "ws://example.com/ws"
        assert error.code == 1006
        assert error.reason == "Abnormal closure"


@pytest.mark.asyncio
class TestBaseWebSocketPageUnit:
    """Unit tests for BaseWebSocketPage (no connection)."""

    def test_initialization(self):
        """Test page initialization."""
        from socialseed_e2e.core.base_websocket_page import BaseWebSocketPage

        page = BaseWebSocketPage("ws://localhost:8765")

        assert page.url == "ws://localhost:8765"
        assert page.config is not None
        assert page.is_connected is False
        assert len(page.message_history) == 0
        assert len(page.connection_logs) == 0

    def test_initialization_with_config(self):
        """Test page initialization with custom config."""
        from socialseed_e2e.core.base_websocket_page import BaseWebSocketPage

        config = WebSocketConfig(connect_timeout=5.0)
        page = BaseWebSocketPage("ws://localhost:8765", config=config)

        assert page.config.connect_timeout == 5.0

    def test_setup_teardown(self):
        """Test setup and teardown."""
        from socialseed_e2e.core.base_websocket_page import BaseWebSocketPage

        page = BaseWebSocketPage("ws://localhost:8765")

        page.setup()
        assert page is not None

        page.teardown()
        # Should not raise even if not connected

    def test_not_connected_assertions(self):
        """Test assertions when not connected."""
        from socialseed_e2e.core.base_websocket_page import BaseWebSocketPage

        page = BaseWebSocketPage("ws://localhost:8765")
        page.setup()

        # assert_disconnected should pass when not connected
        page.assert_disconnected()

        # assert_connected should fail when not connected
        with pytest.raises(AssertionError):
            page.assert_connected()

    def test_message_history_operations(self):
        """Test message history operations."""
        from socialseed_e2e.core.base_websocket_page import BaseWebSocketPage

        page = BaseWebSocketPage("ws://localhost:8765")

        # Add some messages manually
        page.message_history.append(
            WebSocketMessage(data="msg1", message_type="text", direction="incoming")
        )
        page.message_history.append(
            WebSocketMessage(data="msg2", message_type="text", direction="outgoing")
        )
        page.message_history.append(
            WebSocketMessage(data=b"bin", message_type="binary", direction="incoming")
        )

        # Get all messages
        all_msgs = page.get_message_history()
        assert len(all_msgs) == 3

        # Filter by direction
        incoming = page.get_message_history(direction="incoming")
        assert len(incoming) == 2

        outgoing = page.get_message_history(direction="outgoing")
        assert len(outgoing) == 1

        # Filter by type
        text_msgs = page.get_message_history(message_type="text")
        assert len(text_msgs) == 2

        binary_msgs = page.get_message_history(message_type="binary")
        assert len(binary_msgs) == 1

        # Get recent with limit
        recent = page.get_message_history(limit=2)
        assert len(recent) == 2

        # Clear history
        page.clear_history()
        assert len(page.get_message_history()) == 0

    def test_message_count_assertions(self):
        """Test message count assertions."""
        from socialseed_e2e.core.base_websocket_page import BaseWebSocketPage

        page = BaseWebSocketPage("ws://localhost:8765")

        # Add messages
        page.message_history.append(
            WebSocketMessage(data="msg1", message_type="text", direction="incoming")
        )
        page.message_history.append(
            WebSocketMessage(data="msg2", message_type="text", direction="outgoing")
        )

        # Total count
        page.assert_message_count(2)

        # By direction
        page.assert_message_count(1, direction="incoming")
        page.assert_message_count(1, direction="outgoing")

        # Wrong count should raise
        with pytest.raises(AssertionError):
            page.assert_message_count(5)

    def test_on_message_handler_registration(self):
        """Test message handler registration."""
        from socialseed_e2e.core.base_websocket_page import BaseWebSocketPage

        page = BaseWebSocketPage("ws://localhost:8765")

        # Register handler
        def handler(msg):
            pass

        result = page.on_message("text", handler)

        # Should return the handler
        assert result == handler

        # Handler should be registered
        assert "text" in page._message_handlers
        assert handler in page._message_handlers["text"]

    def test_import_availability(self):
        """Test that WebSocket classes can be imported."""
        from socialseed_e2e import (
            WEBSOCKET_AVAILABLE,
            WebSocketConfig,
            WebSocketMessage,
            WebSocketLog,
            WebSocketError,
        )

        # Classes should be importable
        assert WebSocketConfig is not None
        assert WebSocketMessage is not None
        assert WebSocketLog is not None
        assert WebSocketError is not None

        # WEBSOCKET_AVAILABLE should be a boolean
        assert isinstance(WEBSOCKET_AVAILABLE, bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
