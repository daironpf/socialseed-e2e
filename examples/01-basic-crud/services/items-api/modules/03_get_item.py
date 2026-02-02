"""Test module for getting a single item.

Tests GET /api/items/{id} endpoint for retrieving specific items.
"""

from typing import TYPE_CHECKING

from playwright.sync_api import APIResponse

if TYPE_CHECKING:
    from ..items_api_page import ItemsApiPage


def run(items_api: "ItemsApiPage") -> APIResponse:
    """Test getting a single item via GET /api/items/{id}.

    This test verifies:
    - Getting an existing item returns 200
    - Response contains correct item data
    - Getting a non-existent item returns 404

    Args:
        items_api: Instance of ItemsApiPage for API interactions

    Returns:
        APIResponse: Response from the get operation
    """
    print("Test 1: Create an item first to retrieve")
    create_response = items_api.create_item(
        name="Retrievable Item",
        price=49.99,
        description="This item will be retrieved",
        quantity=5,
    )

    items_api.assert_status(create_response, 201)
    created_data = items_api.assert_json(create_response)
    item_id = created_data["id"]
    items_api.created_items.append(item_id)

    print(f"  ✓ Created test item with ID: {item_id}")

    print("Test 2: Get the created item")
    response = items_api.get_item(item_id)

    items_api.assert_status(response, 200)

    data = items_api.assert_json(response)
    assert data["id"] == item_id
    assert data["name"] == "Retrievable Item"
    assert data["price"] == 49.99
    assert data["description"] == "This item will be retrieved"
    assert data["quantity"] == 5

    print(f"  ✓ Retrieved item correctly")

    print("Test 3: Get non-existent item")
    response = items_api.get_item(999999)

    items_api.assert_status(response, 404)

    error_data = items_api.assert_json(response)
    assert "error" in error_data
    assert "not found" in error_data["message"].lower()

    print(f"  ✓ 404 returned for non-existent item")

    print("\n✅ All get item tests passed!")
    return response
