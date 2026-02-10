"""Mock WebSocket server for testing examples.

This module provides a simple WebSocket echo server for testing purposes.
"""

import asyncio
import json
import logging
from typing import Optional

try:
    import websockets
    from websockets.server import WebSocketServerProtocol

    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False
    print("websockets package not installed. Install with: pip install websockets")

logger = logging.getLogger(__name__)


class MockWebSocketServer:
    """Mock WebSocket server for testing.

    Provides a simple echo server that can also simulate different scenarios
    like delays, errors, and broadcasts.

    Example:
        >>> server = MockWebSocketServer("localhost", 8765)
        >>> await server.start()
        >>> # Run tests
        >>> await server.stop()
    """

    def __init__(self, host: str = "localhost", port: int = 8765):
        """Initialize mock server.

        Args:
            host: Host to bind to
            port: Port to listen on
        """
        self.host = host
        self.port = port
        self.server = None
        self.clients: set = set()
        self.message_history: list = []
        self.running = False

    async def start(self) -> None:
        """Start the WebSocket server."""
        if not WEBSOCKET_AVAILABLE:
            raise RuntimeError("websockets package required")

        self.server = await websockets.serve(
            self._handle_client,
            self.host,
            self.port,
        )
        self.running = True
        logger.info(f"WebSocket server started at ws://{self.host}:{self.port}")

    async def stop(self) -> None:
        """Stop the WebSocket server."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            self.running = False
            logger.info("WebSocket server stopped")

    async def _handle_client(
        self, websocket: WebSocketServerProtocol, path: str
    ) -> None:
        """Handle client connection.

        Args:
            websocket: WebSocket connection
            path: Connection path
        """
        self.clients.add(websocket)
        client_id = id(websocket)
        logger.info(f"Client {client_id} connected")

        try:
            async for message in websocket:
                # Log received message
                self.message_history.append(
                    {
                        "type": "received",
                        "client_id": client_id,
                        "message": message,
                        "timestamp": asyncio.get_event_loop().time(),
                    }
                )

                # Parse and process message
                try:
                    data = json.loads(message)
                    response = await self._process_message(data, client_id)
                except json.JSONDecodeError:
                    response = {"error": "Invalid JSON", "received": message}

                # Send response
                response_str = json.dumps(response)
                await websocket.send(response_str)

                # Log sent message
                self.message_history.append(
                    {
                        "type": "sent",
                        "client_id": client_id,
                        "message": response_str,
                        "timestamp": asyncio.get_event_loop().time(),
                    }
                )

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client {client_id} disconnected")
        finally:
            self.clients.discard(websocket)

    async def _process_message(self, data: dict, client_id: int) -> dict:
        """Process incoming message and generate response.

        Args:
            data: Parsed JSON message
            client_id: Client identifier

        Returns:
            Response dictionary
        """
        action = data.get("action", "echo")

        if action == "echo":
            return {
                "type": "echo",
                "data": data.get("data"),
                "client_id": client_id,
            }

        elif action == "subscribe":
            channel = data.get("channel", "default")
            return {
                "type": "subscribed",
                "channel": channel,
                "client_id": client_id,
            }

        elif action == "broadcast":
            # Broadcast to all clients
            message = data.get("message", "")
            await self._broadcast(message, exclude=client_id)
            return {
                "type": "broadcast_sent",
                "message": message,
                "recipients": len(self.clients) - 1,
            }

        elif action == "delay":
            # Simulate processing delay
            delay_ms = data.get("delay_ms", 1000)
            await asyncio.sleep(delay_ms / 1000)
            return {
                "type": "delayed_response",
                "delay_ms": delay_ms,
            }

        elif action == "error":
            # Simulate error response
            return {
                "type": "error",
                "error": data.get("error_message", "Simulated error"),
                "code": data.get("error_code", 500),
            }

        else:
            return {
                "type": "unknown_action",
                "action": action,
                "supported_actions": [
                    "echo",
                    "subscribe",
                    "broadcast",
                    "delay",
                    "error",
                ],
            }

    async def _broadcast(self, message: str, exclude: Optional[int] = None) -> None:
        """Broadcast message to all clients.

        Args:
            message: Message to broadcast
            exclude: Client ID to exclude from broadcast
        """
        if not self.clients:
            return

        data = json.dumps({"type": "broadcast", "message": message})

        for client in self.clients:
            if exclude and id(client) == exclude:
                continue
            try:
                await client.send(data)
            except Exception as e:
                logger.error(f"Failed to broadcast to client: {e}")

    def get_message_history(self) -> list:
        """Get message history."""
        return self.message_history.copy()

    def clear_history(self) -> None:
        """Clear message history."""
        self.message_history.clear()


async def main():
    """Run server for testing."""
    logging.basicConfig(level=logging.INFO)

    server = MockWebSocketServer("localhost", 8765)
    await server.start()

    print(f"WebSocket server running at ws://localhost:8765")
    print("Press Ctrl+C to stop")

    try:
        await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        print("\nStopping server...")
    finally:
        await server.stop()


if __name__ == "__main__":
    asyncio.run(main())
