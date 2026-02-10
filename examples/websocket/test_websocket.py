"""WebSocket test example.

This module demonstrates how to write WebSocket tests using the framework.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from chat_service_page import ChatServicePage


async def test_basic_connection():
    """Test basic WebSocket connection."""
    print("\n=== Test: Basic Connection ===")

    page = ChatServicePage("ws://localhost:8765")
    page.setup()

    try:
        # Connect
        await page.connect()
        page.assert_connected()
        print("✓ Connected successfully")

        # Disconnect
        await page.disconnect()
        page.assert_disconnected()
        print("✓ Disconnected successfully")

        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

    finally:
        page.teardown()


async def test_subscribe():
    """Test channel subscription."""
    print("\n=== Test: Channel Subscription ===")

    page = ChatServicePage("ws://localhost:8765")
    page.setup()

    try:
        await page.connect()

        # Subscribe to channel
        response = await page.subscribe("test-channel")

        assert response.get("type") == "subscribed", (
            f"Expected 'subscribed', got {response.get('type')}"
        )
        assert response.get("channel") == "test-channel"

        page.assert_subscribed_to("test-channel")
        print("✓ Subscribed to channel successfully")

        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

    finally:
        await page.disconnect()
        page.teardown()


async def test_send_message():
    """Test sending messages."""
    print("\n=== Test: Send Message ===")

    page = ChatServicePage("ws://localhost:8765")
    page.setup()

    try:
        await page.connect()
        await page.subscribe("general")

        # Send message
        response = await page.send_message("Hello, WebSocket!")

        assert response.get("type") == "echo", (
            f"Expected 'echo', got {response.get('type')}"
        )
        assert "data" in response
        print("✓ Message sent and echoed successfully")

        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

    finally:
        await page.disconnect()
        page.teardown()


async def test_broadcast():
    """Test broadcasting messages."""
    print("\n=== Test: Broadcast ===")

    # Create two client pages
    page1 = ChatServicePage("ws://localhost:8765")
    page2 = ChatServicePage("ws://localhost:8765")

    page1.setup()
    page2.setup()

    try:
        # Connect both clients
        await page1.connect()
        await page2.connect()

        # Subscribe both to same channel
        await page1.subscribe("general")
        await page2.subscribe("general")

        # Page1 broadcasts
        response = await page1.broadcast("Hello everyone!")

        assert response.get("type") == "broadcast_sent"
        print(f"✓ Broadcast sent to {response.get('recipients', 0)} recipients")

        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

    finally:
        await page1.disconnect()
        await page2.disconnect()
        page1.teardown()
        page2.teardown()


async def test_error_handling():
    """Test error handling."""
    print("\n=== Test: Error Handling ===")

    page = ChatServicePage("ws://localhost:8765")
    page.setup()

    try:
        await page.connect()

        # Trigger error response
        response = await page.trigger_error("Test error message")

        assert response.get("type") == "error"
        assert "error" in response
        print("✓ Error response handled correctly")

        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

    finally:
        await page.disconnect()
        page.teardown()


async def test_message_history():
    """Test message history tracking."""
    print("\n=== Test: Message History ===")

    page = ChatServicePage("ws://localhost:8765")
    page.setup()

    try:
        await page.connect()
        await page.subscribe("general")

        # Send multiple messages
        await page.send_message("Message 1")
        await page.send_message("Message 2")
        await page.send_message("Message 3")

        # Check message history
        history = page.get_message_history()
        print(f"✓ Message history contains {len(history)} messages")

        # Check received messages
        received = page.get_received_messages()
        assert len(received) >= 3, f"Expected at least 3 messages, got {len(received)}"
        print(f"✓ Received {len(received)} messages")

        # Clear and verify
        page.clear_received_messages()
        assert len(page.get_received_messages()) == 0
        print("✓ Message buffer cleared")

        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

    finally:
        await page.disconnect()
        page.teardown()


async def run_all_tests():
    """Run all WebSocket tests."""
    print("=" * 50)
    print("WebSocket Test Suite")
    print("=" * 50)
    print("\nMake sure the mock server is running:")
    print("  python examples/websocket/mock_server.py")
    print()

    tests = [
        test_basic_connection,
        test_subscribe,
        test_send_message,
        test_broadcast,
        test_error_handling,
        test_message_history,
    ]

    results = []
    for test in tests:
        try:
            result = await test()
            results.append((test.__name__, result))
        except Exception as e:
            print(f"✗ {test.__name__} crashed: {e}")
            results.append((test.__name__, False))

    # Summary
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)

    passed = sum(1 for _, result in results if result)
    failed = len(results) - passed

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")

    print(f"\nTotal: {len(results)} tests")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")

    return failed == 0


if __name__ == "__main__":
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nTest suite error: {e}")
        print("\nMake sure the mock WebSocket server is running!")
        print("  python examples/websocket/mock_server.py")
        sys.exit(1)
