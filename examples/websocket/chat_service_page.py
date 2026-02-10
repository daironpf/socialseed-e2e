"""Test page for WebSocket chat service.

This module provides a page object for testing the WebSocket chat service,
extending BaseWebSocketPage with service-specific methods.
"""

import asyncio
from typing import Any, Dict, List, Optional

from socialseed_e2e.core.base_websocket_page import (
    BaseWebSocketPage,
    WebSocketConfig,
    WebSocketMessage,
)


class ChatServicePage(BaseWebSocketPage):
    """Page object for WebSocket chat service testing.

    This class provides methods for interacting with a WebSocket chat service,
    including sending messages, subscribing to channels, and handling broadcasts.

    Example:
        >>> page = ChatServicePage("ws://localhost:8765")
        >>> page.setup()
        >>> await page.connect()
        >>> await page.subscribe("general")
        >>> await page.send_message("Hello everyone!")
        >>> message = await page.wait_for_message()
        >>> print(f"Received: {message.data}")
        >>> await page.disconnect()
        >>> page.teardown()

    Attributes:
        subscribed_channels: List of subscribed channels
        received_messages: Queue of received messages
    """

    def __init__(
        self,
        url: str = "ws://localhost:8765",
        config: Optional[WebSocketConfig] = None,
    ):
        """Initialize the Chat service page.

        Args:
            url: WebSocket server URL
            config: WebSocket configuration
        """
        super().__init__(url=url, config=config)
        self.subscribed_channels: List[str] = []
        self.received_messages: List[Dict[str, Any]] = []

    def setup(self) -> "ChatServicePage":
        """Set up the page.

        Returns:
            Self for method chaining
        """
        super().setup()
        # Register message handler for incoming messages
        self.on_message("text", self._handle_incoming_message)
        return self

    async def _handle_incoming_message(self, message: WebSocketMessage) -> None:
        """Handle incoming messages.

        Args:
            message: Received WebSocket message
        """
        try:
            data = message.json()
            self.received_messages.append(data)
        except Exception as e:
            # Handle non-JSON messages
            self.received_messages.append({"raw": message.data, "error": str(e)})

    async def subscribe(self, channel: str) -> Dict[str, Any]:
        """Subscribe to a chat channel.

        Args:
            channel: Channel name to subscribe to

        Returns:
            Server response
        """
        await self.send(
            {
                "action": "subscribe",
                "channel": channel,
            }
        )

        response = await self.receive_json(timeout=5.0)

        if response.get("type") == "subscribed":
            self.subscribed_channels.append(channel)

        return response

    async def send_message(
        self, message: str, channel: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send a chat message.

        Args:
            message: Message content
            channel: Optional channel name (uses subscribed channel if not specified)

        Returns:
            Server response
        """
        data = {
            "action": "echo",
            "data": {
                "message": message,
                "channel": channel
                or (
                    self.subscribed_channels[0]
                    if self.subscribed_channels
                    else "general"
                ),
            },
        }

        await self.send(data)
        return await self.receive_json(timeout=5.0)

    async def broadcast(self, message: str) -> Dict[str, Any]:
        """Broadcast a message to all clients.

        Args:
            message: Message to broadcast

        Returns:
            Server response with recipient count
        """
        await self.send(
            {
                "action": "broadcast",
                "message": message,
            }
        )

        return await self.receive_json(timeout=5.0)

    async def wait_for_message(self, timeout: float = 10.0) -> Dict[str, Any]:
        """Wait for a message from the server.

        Args:
            timeout: Timeout in seconds

        Returns:
            Received message data
        """
        message = await self.receive_json(timeout=timeout)
        return message

    async def simulate_delay(self, delay_ms: int = 1000) -> Dict[str, Any]:
        """Simulate a delayed response.

        Args:
            delay_ms: Delay in milliseconds

        Returns:
            Server response
        """
        await self.send(
            {
                "action": "delay",
                "delay_ms": delay_ms,
            }
        )

        return await self.receive_json(timeout=(delay_ms / 1000) + 5.0)

    async def trigger_error(self, error_message: str = "Test error") -> Dict[str, Any]:
        """Trigger an error response.

        Args:
            error_message: Error message to send

        Returns:
            Error response
        """
        await self.send(
            {
                "action": "error",
                "error_message": error_message,
            }
        )

        return await self.receive_json(timeout=5.0)

    def get_subscribed_channels(self) -> List[str]:
        """Get list of subscribed channels.

        Returns:
            List of channel names
        """
        return self.subscribed_channels.copy()

    def get_received_messages(self) -> List[Dict[str, Any]]:
        """Get all received messages.

        Returns:
            List of received message data
        """
        return self.received_messages.copy()

    def clear_received_messages(self) -> None:
        """Clear received messages buffer."""
        self.received_messages.clear()

    def assert_subscribed_to(self, channel: str) -> None:
        """Assert that subscribed to a specific channel.

        Args:
            channel: Channel name to check

        Raises:
            AssertionError: If not subscribed to channel
        """
        if channel not in self.subscribed_channels:
            raise AssertionError(
                f"Expected to be subscribed to '{channel}', but subscribed to: {self.subscribed_channels}"
            )

    def assert_received_message_count(self, expected: int) -> None:
        """Assert number of received messages.

        Args:
            expected: Expected message count

        Raises:
            AssertionError: If count doesn't match
        """
        actual = len(self.received_messages)
        if actual != expected:
            raise AssertionError(
                f"Expected {expected} received messages, but got {actual}"
            )


async def example_usage():
    """Example usage of ChatServicePage."""
    # Create page
    page = ChatServicePage("ws://localhost:8765")
    page.setup()

    try:
        # Connect to server
        await page.connect()
        print("✓ Connected to WebSocket server")

        # Subscribe to channel
        response = await page.subscribe("general")
        print(f"✓ Subscribed: {response}")

        # Send a message
        response = await page.send_message("Hello, World!")
        print(f"✓ Message sent: {response}")

        # Check received messages
        messages = page.get_received_messages()
        print(f"✓ Received {len(messages)} messages")

        # Broadcast
        response = await page.broadcast("Important announcement!")
        print(f"✓ Broadcast sent to {response.get('recipients', 0)} recipients")

        # Assertions
        page.assert_connected()
        page.assert_subscribed_to("general")
        print("✓ All assertions passed")

    finally:
        # Cleanup
        await page.disconnect()
        page.teardown()
        print("✓ Disconnected")


if __name__ == "__main__":
    # Run example
    print("WebSocket Chat Service Page Example")
    print("Make sure the mock server is running: python mock_server.py")
    print()

    try:
        asyncio.run(example_usage())
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure the mock WebSocket server is running!")
