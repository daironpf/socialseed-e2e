"""Test module for creating items.

Tests POST /api/items endpoint for creating new items.
"""

from typing import TYPE_CHECKING

from playwright.sync_api import APIResponse

if TYPE_CHECKING:
    from ..items_api_page import ItemsApiPage


def run(items_api: "ItemsApiPage") -> APIResponse:
    """Test creating items via POST /api/items.

    This test verifies:
    - Creating an item with all fields returns 201
    - Response contains the created item data
    - Item ID is assigned automatically

    Args:
        items_api: Instance of ItemsApiPage for API interactions

    Returns:
        APIResponse: Response from the create operation
    """
    print("Test 1: Create item with all fields")
    response = items_api.create_item(
        name="Test Laptop",
        price=999.99,
        description="A high-performance laptop for testing",
        quantity=10,
    )

    items_api.assert_status(response, 201)

    data = items_api.assert_json(response)
    assert "id" in data, "Response should contain item ID"
    assert data["name"] == "Test Laptop"
    assert data["price"] == 999.99

    # Store for cleanup and other tests
    item_id = data["id"]
    items_api.created_items.append(item_id)
    items_api.last_created_item_id = item_id

    print(f"  ✓ Created item with ID: {item_id}")

    print("Test 2: Create item with minimal fields")
    response = items_api.create_item(name="Simple Item", price=10.00)

    items_api.assert_status(response, 201)
    data = items_api.assert_json(response)
    assert data["description"] == ""
    assert data["quantity"] == 0

    items_api.created_items.append(data["id"])
    print(f"  ✓ Created minimal item with ID: {data['id']}")

    print("Test 3: Verify validation - missing required fields")
    response = items_api.post("/api/items", json={"description": "Missing name and price"})

    items_api.assert_status(response, 400)
    error_data = items_api.assert_json(response)
    assert "error" in error_data

    print("  ✓ Validation works correctly")

    print("\n✅ All create item tests passed!")
    return response
