"""Test module for Orders Service.

Tests order creation and service communication.
"""

from typing import TYPE_CHECKING

from playwright.sync_api import APIResponse

if TYPE_CHECKING:
    from ..orders_api_page import OrdersApiPage


def run(orders_api: "OrdersApiPage") -> APIResponse:
    """Test Orders Service with Users Service communication.

    Tests:
    - Create order for valid user (service-to-service call)
    - Create order for invalid user (should fail)
    - List orders
    - Get order details

    Args:
        orders_api: Instance of OrdersApiPage

    Returns:
        APIResponse: Last response
    """
    print("Test 1: Create order for valid user (ID: 1)")
    response = orders_api.create_order(user_id=1, items=["Laptop", "Mouse"], total_amount=299.99)
    orders_api.assert_status(response, 201)

    order_data = orders_api.assert_json(response)
    assert "order" in order_data
    orders_api.test_order_id = order_data["order"]["id"]
    print(f"  ✓ Order created with ID: {orders_api.test_order_id}")

    print("Test 2: Verify order enriched with user data")
    assert orders_api.test_order_id is not None
    response = orders_api.get_order(orders_api.test_order_id)
    orders_api.assert_status(response, 200)

    order = orders_api.assert_json(response)
    assert order["user"]["username"] == "alice"
    print(f"  ✓ Order has user data from Users Service")

    print("Test 3: Create order for invalid user (should fail)")
    response = orders_api.create_order(user_id=999, items=["Phone"], total_amount=199.99)
    orders_api.assert_status(response, 404)
    print(f"  ✓ Invalid user correctly rejected")

    print("Test 4: List all orders")
    response = orders_api.list_orders()
    orders_api.assert_status(response, 200)

    data = orders_api.assert_json(response)
    assert len(data["orders"]) > 0
    print(f"  ✓ Listed {len(data['orders'])} orders")

    print("Test 5: Get user's orders")
    response = orders_api.get_user_orders(1)
    orders_api.assert_status(response, 200)

    user_orders = orders_api.assert_json(response)
    assert user_orders["user_name"] == "alice"
    print(f"  ✓ User orders retrieved")

    print("\n✅ All Orders Service tests passed!")
    return response
