# WebSocket Testing Example

This example demonstrates how to use the socialseed-e2e framework for testing WebSocket APIs.

## Files

- `mock_server.py` - Mock WebSocket server for testing
- `chat_service_page.py` - Example WebSocket page class
- `test_websocket.py` - Example tests

## Running the Example

### 1. Install dependencies

```bash
pip install websockets
```

### 2. Start the mock server

```bash
python examples/websocket/mock_server.py
```

The server will start on `ws://localhost:8765`

### 3. Run the tests

In another terminal:

```bash
python examples/websocket/test_websocket.py
```

## Features Demonstrated

### Connection Management

```python
from socialseed_e2e import BaseWebSocketPage

page = BaseWebSocketPage("ws://localhost:8765")
page.setup()

# Connect
await page.connect()
page.assert_connected()

# Disconnect
await page.disconnect()
page.assert_disconnected()

page.teardown()
```

### Sending and Receiving Messages

```python
# Send text message
await page.send("Hello, WebSocket!")

# Send JSON message
await page.send({"action": "subscribe", "channel": "general"})

# Receive message
message = await page.receive()
print(message.data)

# Receive and parse JSON
data = await page.receive_json()
```

### Message Handlers

```python
# Register handler for specific message type
@page.on_message("text")
def handle_text(message):
    print(f"Received: {message.data}")

# Handler can be async too
@page.on_message("binary")
async def handle_binary(message):
    await process_binary_data(message.data)
```

### Waiting for Specific Messages

```python
# Wait for message matching predicate
message = await page.wait_for_message(
    lambda m: "success" in m.data
)

# Wait for JSON message with specific field
data = await page.wait_for_message(
    lambda m: m.json().get("type") == "notification"
)
```

### Message History

```python
# Get all messages
history = page.get_message_history()

# Filter by direction (incoming/outgoing)
incoming = page.get_message_history(direction="incoming")

# Filter by type
json_messages = page.get_message_history(message_type="text")

# Get recent messages only
recent = page.get_message_history(limit=10)

# Clear history
page.clear_history()
```

### Assertions

```python
# Connection assertions
page.assert_connected()
page.assert_disconnected()

# Message count assertions
page.assert_message_count(5)
page.assert_message_count(3, direction="outgoing")
page.assert_message_count(2, message_type="text")
```

## Creating Custom WebSocket Pages

Extend `BaseWebSocketPage` for service-specific testing:

```python
from socialseed_e2e import BaseWebSocketPage, WebSocketConfig

class MyServicePage(BaseWebSocketPage):
    def __init__(self, url="ws://api.example.com/ws"):
        config = WebSocketConfig(
            ping_interval=20,
            auto_reconnect=True,
        )
        super().__init__(url, config=config)

    async def login(self, username, password):
        await self.send({
            "action": "login",
            "username": username,
            "password": password
        })
        response = await self.receive_json()
        self.access_token = response.get("token")
        return response

    async def subscribe(self, channel):
        await self.send({
            "action": "subscribe",
            "channel": channel
        })
        return await self.receive_json()
```

## Configuration Options

```python
from socialseed_e2e import WebSocketConfig

config = WebSocketConfig(
    # Connection
    connect_timeout=10.0,           # Connection timeout in seconds
    receive_timeout=30.0,           # Message receive timeout

    # Reconnection
    auto_reconnect=True,            # Auto-reconnect on disconnect
    max_reconnect_attempts=3,       # Max reconnection attempts
    reconnect_delay=1.0,            # Initial delay between attempts

    # Keep-alive
    ping_interval=20.0,             # Ping interval in seconds
    ping_timeout=10.0,              # Pong response timeout

    # Protocol
    subprotocols=["chat", "json"],  # Subprotocols to negotiate
    headers={"Authorization": ...}, # Custom headers
)

page = BaseWebSocketPage("ws://api.example.com/ws", config=config)
```

## Error Handling

```python
from socialseed_e2e import WebSocketError

try:
    await page.connect()
except WebSocketError as e:
    print(f"Connection failed: {e}")
    print(f"URL: {e.url}")
    print(f"Code: {e.code}")
    print(f"Reason: {e.reason}")

try:
    message = await page.receive(timeout=5.0)
except WebSocketError as e:
    print(f"Receive timeout: {e}")
```

## Testing Best Practices

1. **Always cleanup**: Use try/finally or context managers to ensure disconnection
2. **Set timeouts**: Always specify timeouts to prevent hanging tests
3. **Use assertions**: Leverage built-in assertion methods
4. **Handle reconnections**: Test both happy path and reconnection scenarios
5. **Clean state**: Clear message history between test cases
6. **Mock server**: Use mock server for reliable, repeatable tests

## Running in CI/CD

```yaml
# Example GitHub Actions workflow
- name: Start WebSocket Mock Server
  run: |
    python examples/websocket/mock_server.py &
    sleep 2  # Wait for server to start

- name: Run WebSocket Tests
  run: |
    python examples/websocket/test_websocket.py
```

## Next Steps

- See `chat_service_page.py` for a complete service page example
- Check `test_websocket.py` for comprehensive test patterns
- Review the main framework documentation for advanced features
