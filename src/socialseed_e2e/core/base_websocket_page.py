"""Base WebSocket page for testing WebSocket APIs.

This module provides a BaseWebSocketPage class for testing WebSocket services,
offering a similar interface to BasePage but adapted for WebSocket protocol.
"""

import asyncio
import json
import logging
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Type, Union

from socialseed_e2e.utils.state_management import DynamicStateMixin

logger = logging.getLogger(__name__)


try:
    import websockets

    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False
    logger.warning(
        "websockets package not installed. WebSocket testing will not be available."
    )


@dataclass
class WebSocketConfig:
    """Configuration for WebSocket connections.

    Attributes:
        connect_timeout: Connection timeout in seconds (default: 10)
        receive_timeout: Timeout for receiving messages in seconds (default: 30)
        auto_reconnect: Whether to auto-reconnect on disconnect (default: True)
        max_reconnect_attempts: Maximum reconnection attempts (default: 3)
        reconnect_delay: Initial delay between reconnection attempts in seconds (default: 1.0)
        ping_interval: Interval for sending ping frames in seconds (default: 20)
        ping_timeout: Timeout for pong response in seconds (default: 10)
        subprotocols: List of subprotocols to negotiate (default: None)
        headers: Additional headers for WebSocket handshake (default: None)
    """

    connect_timeout: float = 10.0
    receive_timeout: float = 30.0
    auto_reconnect: bool = True
    max_reconnect_attempts: int = 3
    reconnect_delay: float = 1.0
    ping_interval: float = 20.0
    ping_timeout: float = 10.0
    subprotocols: Optional[List[str]] = None
    headers: Optional[Dict[str, str]] = None


@dataclass
class WebSocketMessage:
    """Represents a WebSocket message.

    Attributes:
        data: Message data (string or bytes)
        message_type: Type of message (text, binary, ping, pong, close)
        timestamp: When the message was received/sent
        direction: "incoming" or "outgoing"
    """

    data: Union[str, bytes]
    message_type: str  # text, binary, ping, pong, close
    timestamp: float = field(default_factory=time.time)
    direction: str = "incoming"  # incoming or outgoing

    @property
    def is_text(self) -> bool:
        """Check if message is text type."""
        return self.message_type == "text"

    @property
    def is_binary(self) -> bool:
        """Check if message is binary type."""
        return self.message_type == "binary"

    def json(self) -> Any:
        """Parse message data as JSON.

        Returns:
            Parsed JSON data

        Raises:
            json.JSONDecodeError: If data is not valid JSON
        """
        if isinstance(self.data, bytes):
            return json.loads(self.data.decode("utf-8"))
        return json.loads(self.data)


@dataclass
class WebSocketLog:
    """Log entry for WebSocket operations.

    Attributes:
        operation: Operation type (connect, disconnect, send, receive, error)
        timestamp: When the operation occurred
        duration_ms: Operation duration in milliseconds
        message: Message data (if applicable)
        error: Error message if operation failed
    """

    operation: str
    timestamp: float = field(default_factory=time.time)
    duration_ms: float = 0.0
    message: Optional[WebSocketMessage] = None
    error: Optional[str] = None


class WebSocketError(Exception):
    """Exception raised for WebSocket errors."""

    def __init__(
        self,
        message: str,
        url: Optional[str] = None,
        code: Optional[int] = None,
        reason: Optional[str] = None,
    ):
        """Initialize WebSocket error.

        Args:
            message: Error message
            url: WebSocket URL
            code: Close code (if connection closed)
            reason: Close reason (if connection closed)
        """
        super().__init__(message)
        self.url = url
        self.code = code
        self.reason = reason


class BaseWebSocketPage(DynamicStateMixin):
    """Base page for testing WebSocket APIs.

    This class provides a foundation for creating WebSocket service pages,
    similar to BasePage for REST APIs. It handles connection management,
    message handling, and logging.

    Example:
        >>> page = BaseWebSocketPage("wss://api.example.com/ws")
        >>> page.setup()
        >>> await page.connect()
        >>> await page.send({"action": "subscribe", "channel": "updates"})
        >>> message = await page.receive()
        >>> print(message.data)
        >>> await page.disconnect()
        >>> page.teardown()

    Attributes:
        url: WebSocket URL
        config: WebSocket configuration
        websocket: Active WebSocket connection
        message_history: Queue of recent messages
        connection_logs: List of connection events
    """

    def __init__(
        self,
        url: str,
        config: Optional[WebSocketConfig] = None,
        max_message_history: int = 100,
    ) -> None:
        """Initialize the BaseWebSocketPage.

        Args:
            url: WebSocket URL (e.g., "wss://api.example.com/ws")
            config: WebSocket configuration (uses defaults if not provided)
            max_message_history: Maximum number of messages to keep in history

        Raises:
            ImportError: If websockets package is not installed
        """
        if not WEBSOCKET_AVAILABLE:
            raise ImportError(
                "websockets package is required for WebSocket testing. "
                "Install with: pip install websockets"
            )

        super().__init__()

        self.url: str = url
        self.config: WebSocketConfig = config or WebSocketConfig()
        self.max_message_history: int = max_message_history

        # Connection state
        self.websocket: Optional[Any] = None
        self._connected: bool = False
        self._connection_time: Optional[float] = None

        # Message handling
        self.message_history: deque = deque(maxlen=max_message_history)
        self._pending_messages: asyncio.Queue = asyncio.Queue()
        self._message_handlers: Dict[str, List[Callable]] = {}

        # Logging
        self.connection_logs: List[WebSocketLog] = []
        self._receive_task: Optional[asyncio.Task] = None

        # Reconnection state
        self._reconnect_attempts: int = 0
        self._should_reconnect: bool = False

    def setup(self) -> None:
        """Setup the WebSocket page."""
        logger.info(f"Setting up WebSocket page for {self.url}")

    def teardown(self) -> None:
        """Teardown the WebSocket page and close connection."""
        logger.info(f"Tearing down WebSocket page for {self.url}")
        if self._connected:
            asyncio.get_event_loop().run_until_complete(self.disconnect())

    @property
    def is_connected(self) -> bool:
        """Check if WebSocket is connected."""
        return self._connected and self.websocket is not None

    async def connect(self) -> None:
        """Connect to WebSocket server.

        Raises:
            WebSocketError: If connection fails
        """
        if self.is_connected:
            logger.warning("Already connected to WebSocket")
            return

        start_time = time.time()
        try:
            extra_headers = self.config.headers or {}

            self.websocket = await websockets.connect(
                self.url,
                subprotocols=self.config.subprotocols,
                extra_headers=extra_headers,
                ping_interval=self.config.ping_interval,
                ping_timeout=self.config.ping_timeout,
                close_timeout=self.config.connect_timeout,
            )

            self._connected = True
            self._connection_time = time.time()
            self._reconnect_attempts = 0

            duration_ms = (time.time() - start_time) * 1000
            log = WebSocketLog(
                operation="connect",
                duration_ms=duration_ms,
            )
            self.connection_logs.append(log)

            # Start message receiver
            self._receive_task = asyncio.create_task(self._receive_loop())

            logger.info(f"Connected to WebSocket at {self.url}")

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            log = WebSocketLog(
                operation="connect",
                duration_ms=duration_ms,
                error=str(e),
            )
            self.connection_logs.append(log)
            raise WebSocketError(f"Failed to connect to {self.url}: {e}", url=self.url)

    async def disconnect(self) -> None:
        """Disconnect from WebSocket server."""
        if not self.is_connected:
            return

        self._should_reconnect = False

        # Stop receive loop
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
            self._receive_task = None

        start_time = time.time()
        try:
            if self.websocket:
                await self.websocket.close()
                self.websocket = None

            self._connected = False

            duration_ms = (time.time() - start_time) * 1000
            log = WebSocketLog(
                operation="disconnect",
                duration_ms=duration_ms,
            )
            self.connection_logs.append(log)

            logger.info(f"Disconnected from WebSocket at {self.url}")

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            log = WebSocketLog(
                operation="disconnect",
                duration_ms=duration_ms,
                error=str(e),
            )
            self.connection_logs.append(log)

    async def send(self, data: Union[str, bytes, dict]) -> None:
        """Send a message through WebSocket.

        Args:
            data: Message data (string, bytes, or dict that will be JSON-encoded)

        Raises:
            WebSocketError: If not connected or send fails
        """
        if not self.is_connected:
            raise WebSocketError("Not connected to WebSocket", url=self.url)

        start_time = time.time()
        try:
            # Convert dict to JSON string
            if isinstance(data, dict):
                data = json.dumps(data)

            if isinstance(data, str):
                await self.websocket.send(data)
                message = WebSocketMessage(
                    data=data, message_type="text", direction="outgoing"
                )
            else:
                await self.websocket.send(data)
                message = WebSocketMessage(
                    data=data, message_type="binary", direction="outgoing"
                )

            duration_ms = (time.time() - start_time) * 1000
            log = WebSocketLog(
                operation="send",
                duration_ms=duration_ms,
                message=message,
            )
            self.connection_logs.append(log)
            self.message_history.append(message)

            logger.debug(
                f"Sent message: {data[:100] if isinstance(data, str) else 'binary'}"
            )

        except Exception as e:
            raise WebSocketError(f"Failed to send message: {e}", url=self.url)

    async def receive(
        self,
        timeout: Optional[float] = None,
        message_type: Optional[str] = None,
    ) -> WebSocketMessage:
        """Receive a message from WebSocket.

        Args:
            timeout: Timeout in seconds (uses config.receive_timeout if not specified)
            message_type: Filter by message type (text, binary, etc.)

        Returns:
            WebSocketMessage: Received message

        Raises:
            WebSocketError: If receive fails or times out
        """
        if not self.is_connected:
            raise WebSocketError("Not connected to WebSocket", url=self.url)

        timeout = timeout or self.config.receive_timeout

        try:
            # Wait for message with timeout
            message = await asyncio.wait_for(
                self._pending_messages.get(),
                timeout=timeout,
            )

            # Filter by message type if specified
            if message_type and message.message_type != message_type:
                # Put message back and wait for next
                await self._pending_messages.put(message)
                return await self.receive(timeout, message_type)

            return message

        except asyncio.TimeoutError:
            raise WebSocketError(
                f"Timeout waiting for message after {timeout}s",
                url=self.url,
            )

    async def receive_json(self, timeout: Optional[float] = None) -> Any:
        """Receive a message and parse as JSON.

        Args:
            timeout: Timeout in seconds

        Returns:
            Parsed JSON data
        """
        message = await self.receive(timeout=timeout, message_type="text")
        return message.json()

    async def _receive_loop(self) -> None:
        """Background task to continuously receive messages."""
        try:
            while self.is_connected:
                try:
                    message_data = await self.websocket.recv()

                    if isinstance(message_data, str):
                        message = WebSocketMessage(
                            data=message_data,
                            message_type="text",
                            direction="incoming",
                        )
                    else:
                        message = WebSocketMessage(
                            data=message_data,
                            message_type="binary",
                            direction="incoming",
                        )

                    # Add to history
                    self.message_history.append(message)

                    # Log
                    log = WebSocketLog(
                        operation="receive",
                        message=message,
                    )
                    self.connection_logs.append(log)

                    # Add to pending queue for receive() calls
                    await self._pending_messages.put(message)

                    # Trigger handlers
                    await self._trigger_handlers(message)

                except websockets.exceptions.ConnectionClosed as e:
                    logger.info(f"WebSocket connection closed: {e}")
                    self._connected = False

                    # Attempt reconnection if configured
                    if self.config.auto_reconnect and self._should_reconnect:
                        await self._attempt_reconnect()
                    break

        except asyncio.CancelledError:
            logger.debug("Receive loop cancelled")
            raise

    async def _attempt_reconnect(self) -> None:
        """Attempt to reconnect to WebSocket server."""
        while (
            self._reconnect_attempts < self.config.max_reconnect_attempts
            and self._should_reconnect
        ):
            self._reconnect_attempts += 1
            delay = self.config.reconnect_delay * (2 ** (self._reconnect_attempts - 1))

            logger.info(
                f"Attempting reconnect {self._reconnect_attempts}/{self.config.max_reconnect_attempts} in {delay}s"
            )
            await asyncio.sleep(delay)

            try:
                await self.connect()
                logger.info("Reconnected successfully")
                return
            except Exception as e:
                logger.warning(f"Reconnection attempt failed: {e}")

        logger.error("Max reconnection attempts reached")

    async def _trigger_handlers(self, message: WebSocketMessage) -> None:
        """Trigger registered message handlers."""
        handlers = self._message_handlers.get(message.message_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(message)
                else:
                    handler(message)
            except Exception as e:
                logger.error(f"Error in message handler: {e}")

    def on_message(self, message_type: str, handler: Callable) -> Callable:
        """Register a message handler.

        Args:
            message_type: Type of message to handle (text, binary, etc.)
            handler: Callback function to handle messages

        Returns:
            The handler function (for use as decorator)
        """
        if message_type not in self._message_handlers:
            self._message_handlers[message_type] = []
        self._message_handlers[message_type].append(handler)
        return handler

    def get_message_history(
        self,
        direction: Optional[str] = None,
        message_type: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[WebSocketMessage]:
        """Get filtered message history.

        Args:
            direction: Filter by direction ("incoming" or "outgoing")
            message_type: Filter by message type
            limit: Maximum number of messages to return

        Returns:
            List of WebSocketMessage objects
        """
        messages = list(self.message_history)

        if direction:
            messages = [m for m in messages if m.direction == direction]

        if message_type:
            messages = [m for m in messages if m.message_type == message_type]

        if limit:
            messages = messages[-limit:]

        return messages

    async def wait_for_message(
        self,
        predicate: Callable[[WebSocketMessage], bool],
        timeout: Optional[float] = None,
    ) -> WebSocketMessage:
        """Wait for a message matching a predicate.

        Args:
            predicate: Function that returns True when desired message is found
            timeout: Timeout in seconds

        Returns:
            WebSocketMessage that matched the predicate

        Raises:
            WebSocketError: If timeout reached without match
        """
        timeout = timeout or self.config.receive_timeout
        start_time = time.time()

        while time.time() - start_time < timeout:
            # Check existing messages
            for message in self.message_history:
                if predicate(message):
                    return message

            # Wait for new message
            try:
                message = await asyncio.wait_for(
                    self._pending_messages.get(),
                    timeout=1.0,
                )
                if predicate(message):
                    return message
            except asyncio.TimeoutError:
                continue

        raise WebSocketError(
            f"Timeout waiting for matching message after {timeout}s",
            url=self.url,
        )

    def assert_connected(self) -> None:
        """Assert that WebSocket is connected.

        Raises:
            AssertionError: If not connected
        """
        if not self.is_connected:
            raise AssertionError(
                f"Expected WebSocket to be connected to {self.url}, but it's not"
            )

    def assert_disconnected(self) -> None:
        """Assert that WebSocket is disconnected.

        Raises:
            AssertionError: If connected
        """
        if self.is_connected:
            raise AssertionError(
                f"Expected WebSocket to be disconnected, but it's connected to {self.url}"
            )

    def assert_message_count(
        self,
        expected: int,
        direction: Optional[str] = None,
        message_type: Optional[str] = None,
    ) -> None:
        """Assert message count in history.

        Args:
            expected: Expected number of messages
            direction: Filter by direction
            message_type: Filter by message type

        Raises:
            AssertionError: If count doesn't match
        """
        messages = self.get_message_history(
            direction=direction, message_type=message_type
        )
        actual = len(messages)
        if actual != expected:
            raise AssertionError(
                f"Expected {expected} messages, but got {actual}. "
                f"Filters: direction={direction}, type={message_type}"
            )

    def clear_history(self) -> None:
        """Clear message history."""
        self.message_history.clear()
