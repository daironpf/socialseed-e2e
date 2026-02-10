# WebSocket Testing

This document describes WebSocket testing support in socialseed-e2e, including setup, configuration, and best practices.

## Overview

socialseed-e2e provides comprehensive support for testing WebSocket APIs. The framework includes:

- **BaseWebSocketPage**: Foundation class for WebSocket testing
- **Connection Management**: Automatic connection handling with reconnection support
- **Message Handling**: Send/receive messages with automatic JSON parsing
- **Async Support**: Full async/await support for WebSocket operations
- **Message History**: Track all sent and received messages
- **Event Handlers**: Register callbacks for specific message types

## Installation

WebSocket support requires the `websockets` package:

```bash
pip install websockets
```

Or add to your project:

```bash
echo "websockets>=12.0" >> requirements.txt
pip install -r requirements.txt
```

## Quick Start

### Basic Connection

```python
import asyncio
from socialseed_e2e import BaseWebSocketPage

async def test_websocket():
    # Create page
    page = BaseWebSocketPage("wss://api.example.com/ws")
    page.setup()

    try:
        # Connect
        await page.connect()
        print("Connected!")

        # Send message
        await page.send('{"action": "ping"}')

        # Receive response
        message = await page.receive()
        print(f"Received: {message.data}")

    finally:
        # Cleanup
        await page.disconnect()
        page.teardown()

# Run
asyncio.run(test_websocket())
```

## Core Classes

### BaseWebSocketPage

Main class for WebSocket testing:

```python
from socialseed_e2e import BaseWebSocketPage, WebSocketConfig

# With default configuration
page = BaseWebSocketPage("wss://api.example.com/ws")

# With custom configuration
config = WebSocketConfig(
    connect_timeout=10.0,
    auto_reconnect=True,
    max_reconnect_attempts=3,
)
page = BaseWebSocketPage("wss://api.example.com/ws", config=config)
```

### WebSocketConfig

Configuration options:

```python
from socialseed_e2e import WebSocketConfig

config = WebSocketConfig(
    # Connection timeouts
    connect_timeout=10.0,           # Connection timeout (seconds)
    receive_timeout=30.0,           # Message receive timeout (seconds)

    # Reconnection
    auto_reconnect=True,            # Auto-reconnect on disconnect
    max_reconnect_attempts=3,       # Max reconnection attempts
    reconnect_delay=1.0,            # Initial delay between attempts

    # Keep-alive
    ping_interval=20.0,             # Ping interval (seconds)
    ping_timeout=10.0,              # Pong response timeout (seconds)

    # Protocol options
    subprotocols=["chat", "json"],  # Subprotocols to negotiate
    headers={"X-Custom": "value"},  # Custom headers for handshake
)
```

### WebSocketMessage

Represents a WebSocket message:

```python
message = await page.receive()

# Properties
print(message.data)           # Raw message data
print(message.message_type)   # "text" or "binary"
print(message.direction)      # "incoming" or "outgoing"
print(message.timestamp)      # Unix timestamp

# Methods
if message.is_text:
    data = message.json()     # Parse as JSON

if message.is_binary:
    binary_data = message.data  # Bytes
```

## Connection Management

### Connecting

```python
# Simple connection
await page.connect()

# Check connection status
if page.is_connected:
    print("WebSocket is connected")

# Connection with error handling
from socialseed_e2e import WebSocketError

try:
    await page.connect()
except WebSocketError as e:
    print(f"Failed to connect: {e}")
    print(f"URL: {e.url}")
```

### Disconnecting

```python
# Graceful disconnect
await page.disconnect()

# Forced disconnect (if needed)
page._connected = False
if page.websocket:
    await page.websocket.close()
```

### Reconnection

Enable automatic reconnection:

```python
config = WebSocketConfig(
    auto_reconnect=True,
    max_reconnect_attempts=3,
    reconnect_delay=1.0,  # Initial delay (doubles with each attempt)
)

page = BaseWebSocketPage(url, config=config)
await page.connect()

# If connection drops, it will auto-reconnect
```

## Message Handling

### Sending Messages

```python
# Send text
await page.send("Hello, WebSocket!")

# Send JSON (dict automatically serialized)
await page.send({
    "action": "subscribe",
    "channel": "updates"
})

# Send binary
await page.send(b"\x00\x01\x02\x03")
```

### Receiving Messages

```python
# Receive any message
message = await page.receive()

# Receive with timeout
message = await page.receive(timeout=5.0)

# Receive specific message type
message = await page.receive(message_type="text")

# Receive and parse JSON
data = await page.receive_json()
print(data["action"])
```

### Message Handlers

Register callbacks for specific message types:

```python
# Decorator style
@page.on_message("text")
def handle_text(message):
    print(f"Text message: {message.data}")

@page.on_message("binary")
async def handle_binary(message):
    await process_binary(message.data)

# Function style
def handler(message):
    print(f"Received: {message.data}")

page.on_message("text", handler)

# Handlers are called automatically when messages arrive
# Run in background receive loop
```

### Waiting for Specific Messages

```python
# Wait for message matching predicate
message = await page.wait_for_message(
    lambda m: "success" in m.data,
    timeout=10.0
)

# Wait for JSON with specific field
message = await page.wait_for_message(
    lambda m: m.json().get("type") == "notification"
)

# Wait for broadcast
message = await page.wait_for_message(
    lambda m: m.json().get("broadcast") == True
)
```

## Message History

### Tracking Messages

All messages are automatically tracked:

```python
# Get all messages
history = page.get_message_history()

# Filter by direction
incoming = page.get_message_history(direction="incoming")
outgoing = page.get_message_history(direction="outgoing")

# Filter by type
text_messages = page.get_message_history(message_type="text")

# Get recent messages only
recent = page.get_message_history(limit=10)

# Combined filters
recent_incoming = page.get_message_history(
    direction="incoming",
    message_type="text",
    limit=5
)
```

### Clearing History

```python
# Clear message history
page.clear_history()

# Also clears connection logs
page.connection_logs.clear()
```

## Assertions

### Connection Assertions

```python
# Assert connected
page.assert_connected()

# Assert disconnected
await page.disconnect()
page.assert_disconnected()
```

### Message Count Assertions

```python
# Total messages
page.assert_message_count(10)

# By direction
page.assert_message_count(5, direction="incoming")
page.assert_message_count(5, direction="outgoing")

# By type
page.assert_message_count(8, message_type="text")
page.assert_message_count(2, message_type="binary")

# Combined
page.assert_message_count(
    3,
    direction="incoming",
    message_type="text"
)
```

## Creating Service-Specific Pages

Extend `BaseWebSocketPage` for your service:

```python
from socialseed_e2e import BaseWebSocketPage, WebSocketConfig

class ChatServicePage(BaseWebSocketPage):
    """Page for chat WebSocket service."""

    def __init__(self, url="wss://chat.example.com/ws"):
        config = WebSocketConfig(
            ping_interval=20,
            auto_reconnect=True,
        )
        super().__init__(url, config=config)
        self.channels = []

    async def subscribe(self, channel):
        """Subscribe to a channel."""
        await self.send({
            "action": "subscribe",
            "channel": channel
        })
        response = await self.receive_json()
        if response.get("success"):
            self.channels.append(channel)
        return response

    async def send_message(self, channel, message):
        """Send a message to a channel."""
        await self.send({
            "action": "message",
            "channel": channel,
            "message": message
        })
        return await self.receive_json()

    def assert_subscribed(self, channel):
        """Assert subscription to channel."""
        if channel not in self.channels:
            raise AssertionError(
                f"Not subscribed to '{channel}'"
            )
```

## Testing Patterns

### Basic Test Pattern

```python
import asyncio
import pytest
from socialseed_e2e import BaseWebSocketPage

@pytest.mark.asyncio
async def test_websocket_connection():
    page = BaseWebSocketPage("wss://api.example.com/ws")
    page.setup()

    try:
        # Connect
        await page.connect()
        page.assert_connected()

        # Test ping/pong
        await page.send('{"action": "ping"}')
        response = await page.receive_json(timeout=5.0)
        assert response["action"] == "pong"

    finally:
        await page.disconnect()
        page.teardown()
```

### Multi-Client Testing

```python
async def test_broadcast():
    """Test broadcasting to multiple clients."""
    # Create multiple clients
    client1 = BaseWebSocketPage("wss://api.example.com/ws")
    client2 = BaseWebSocketPage("wss://api.example.com/ws")

    client1.setup()
    client2.setup()

    try:
        # Connect both
        await asyncio.gather(
            client1.connect(),
            client2.connect()
        )

        # Client1 sends broadcast
        await client1.send({
            "action": "broadcast",
            "message": "Hello everyone!"
        })

        # Client2 receives broadcast
        msg = await client2.wait_for_message(
            lambda m: "broadcast" in m.data,
            timeout=5.0
        )
        assert "Hello everyone!" in msg.data

    finally:
        await client1.disconnect()
        await client2.disconnect()
        client1.teardown()
        client2.teardown()
```

### Error Testing

```python
async def test_error_handling():
    """Test error responses."""
    page = BaseWebSocketPage("wss://api.example.com/ws")
    page.setup()

    try:
        await page.connect()

        # Send invalid request
        await page.send({"action": "invalid"})

        # Wait for error
        response = await page.receive_json()
        assert response["type"] == "error"
        assert "error" in response

    finally:
        await page.disconnect()
        page.teardown()
```

### Reconnection Testing

```python
async def test_reconnection():
    """Test auto-reconnection."""
    config = WebSocketConfig(
        auto_reconnect=True,
        max_reconnect_attempts=3,
        reconnect_delay=0.5,
    )

    page = BaseWebSocketPage("wss://api.example.com/ws", config=config)
    page.setup()

    await page.connect()
    assert page.is_connected

    # Simulate disconnect (implementation depends on server)
    # Server closes connection...

    # Wait for reconnection
    await asyncio.sleep(2)
    assert page.is_connected  # Should reconnect

    await page.disconnect()
    page.teardown()
```

## Error Handling

### WebSocketError

```python
from socialseed_e2e import WebSocketError

try:
    await page.connect()
except WebSocketError as e:
    print(f"Error: {e}")
    print(f"URL: {e.url}")
    print(f"Code: {e.code}")          # Close code
    print(f"Reason: {e.reason}")      # Close reason

try:
    message = await page.receive(timeout=5.0)
except WebSocketError as e:
    if "timeout" in str(e).lower():
        print("Receive timeout")
    else:
        raise
```

### Connection Errors

```python
# Handle connection refused
page = BaseWebSocketPage("wss://invalid-server.com/ws")

try:
    await page.connect()
except WebSocketError as e:
    print(f"Connection failed: {e}")
    # Server might be down

# Handle SSL errors
page = BaseWebSocketPage("wss://expired-cert.com/ws")

try:
    await page.connect()
except WebSocketError as e:
    print(f"SSL error: {e}")
```

## Best Practices

### 1. Always Cleanup

```python
# Good: Always disconnect
page = BaseWebSocketPage(url)
page.setup()

try:
    await page.connect()
    # ... tests ...
finally:
    await page.disconnect()
    page.teardown()

# Better: Use context manager (if available)
async with WebSocketPage(url) as page:
    # ... tests ...
    pass  # Auto cleanup
```

### 2. Set Appropriate Timeouts

```python
# Good: Reasonable timeouts
config = WebSocketConfig(
    connect_timeout=10.0,   # 10 seconds for connection
    receive_timeout=30.0,   # 30 seconds for messages
)

# Bad: Too short
config = WebSocketConfig(
    connect_timeout=0.5,    # Too short!
    receive_timeout=1.0,    # Too short!
)
```

### 3. Handle Reconnections Carefully

```python
# Good: Test both with and without reconnection
async def test_with_reconnect():
    config = WebSocketConfig(auto_reconnect=True)
    page = BaseWebSocketPage(url, config=config)
    # ... test reconnection ...

async def test_without_reconnect():
    config = WebSocketConfig(auto_reconnect=False)
    page = BaseWebSocketPage(url, config=config)
    # ... test normal behavior ...
```

### 4. Clean State Between Tests

```python
# Good: Clean state
async def test1():
    page = BaseWebSocketPage(url)
    page.setup()
    # ... test ...
    await page.disconnect()
    page.teardown()

async def test2():
    page = BaseWebSocketPage(url)  # Fresh instance
    page.setup()
    # ... test ...
```

### 5. Use Message History Wisely

```python
# Good: Clear history when needed
async def test():
    page = BaseWebSocketPage(url)
    page.setup()

    # Setup phase
    await page.connect()
    await page.send({"action": "login"})

    # Clear before actual test
    page.clear_history()

    # Test phase
    await page.send({"action": "test"})
    page.assert_message_count(2)  # Only test messages
```

## Mock Server for Testing

Use a mock server for reliable tests:

```python
# mock_server.py
import asyncio
import websockets
import json

async def handler(websocket, path):
    async for message in websocket:
        data = json.loads(message)

        if data["action"] == "ping":
            await websocket.send(json.dumps({"action": "pong"}))

        elif data["action"] == "echo":
            await websocket.send(json.dumps(data))

        elif data["action"] == "error":
            await websocket.send(json.dumps({
                "type": "error",
                "error": "Test error"
            }))

async def main():
    server = await websockets.serve(handler, "localhost", 8765)
    await server.wait_closed()

asyncio.run(main())
```

## Examples

See the `examples/websocket/` directory for complete examples:

- `mock_server.py` - Mock WebSocket server
- `chat_service_page.py` - Service page example
- `test_websocket.py` - Complete test suite
- `README.md` - Example documentation

## Troubleshooting

### Import Error

```python
# If you get: ImportError: websockets package is required
# Install the package:
pip install websockets
```

### Connection Timeout

```python
# Increase timeout
config = WebSocketConfig(connect_timeout=30.0)
page = BaseWebSocketPage(url, config=config)
```

### SSL Certificate Errors

```python
# For testing only - disable SSL verification
import ssl
import websockets

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Note: This is insecure, only for testing!
```

### Message Not Received

```python
# Check message is being sent
await page.send(data)
page.assert_message_count(1, direction="outgoing")

# Increase receive timeout
message = await page.receive(timeout=10.0)
```

## API Reference

### BaseWebSocketPage

| Method | Description |
|--------|-------------|
| `setup()` | Initialize the page |
| `teardown()` | Cleanup resources |
| `connect()` | Connect to WebSocket server |
| `disconnect()` | Disconnect from server |
| `send(data)` | Send a message |
| `receive(timeout)` | Receive a message |
| `receive_json(timeout)` | Receive and parse JSON |
| `wait_for_message(predicate, timeout)` | Wait for specific message |
| `on_message(type, handler)` | Register message handler |
| `get_message_history(...)` | Get message history |
| `clear_history()` | Clear history |
| `assert_connected()` | Assert is connected |
| `assert_disconnected()` | Assert is disconnected |
| `assert_message_count(n, ...)` | Assert message count |

### WebSocketConfig

| Attribute | Default | Description |
|-----------|---------|-------------|
| `connect_timeout` | 10.0 | Connection timeout (seconds) |
| `receive_timeout` | 30.0 | Receive timeout (seconds) |
| `auto_reconnect` | True | Auto-reconnect on disconnect |
| `max_reconnect_attempts` | 3 | Max reconnection attempts |
| `reconnect_delay` | 1.0 | Initial reconnection delay |
| `ping_interval` | 20.0 | Ping interval (seconds) |
| `ping_timeout` | 10.0 | Pong timeout (seconds) |
| `subprotocols` | None | List of subprotocols |
| `headers` | None | Custom headers |

### WebSocketMessage

| Property | Description |
|----------|-------------|
| `data` | Raw message content |
| `message_type` | "text" or "binary" |
| `direction` | "incoming" or "outgoing" |
| `timestamp` | Unix timestamp |

| Method | Description |
|--------|-------------|
| `json()` | Parse as JSON |

## See Also

- [Examples](../examples/websocket/)
- [BasePage Documentation](base-page.md)
- [gRPC Testing](grpc-testing.md)
- [Testing Guide](testing-guide.md)
