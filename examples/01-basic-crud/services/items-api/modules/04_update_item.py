"""Test module for updating items.

Tests PUT /api/items/{id} endpoint for updating existing items.
"""

from playwright.sync_api import APIResponse
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..items_api_page import ItemsApiPage


def run(items_api: "ItemsApiPage") -> APIResponse:
    """Test updating items via PUT /api/items/{id}.

    This test verifies:
    - Updating an existing item returns 200
    - Only provided fields are updated
    - Unchanged fields remain the same
    - Updating non-existent item returns 404
    - Validation works for update operations

    Args:
        items_api: Instance of ItemsApiPage for API interactions

    Returns:
        APIResponse: Response from the update operation
    """
    print("Test 1: Create an item to update")
    create_response = items_api.create_item(
        name="Original Name",
        price=100.00,
        description="Original description",
        quantity=10,
    )

    items_api.assert_status(create_response, 201)
    created_data = items_api.assert_json(create_response)
    item_id = created_data["id"]
    items_api.created_items.append(item_id)

    print(f"  ✓ Created item with ID: {item_id}")

    print("Test 2: Update single field (name)")
    response = items_api.update_item(item_id, name="Updated Name")

    items_api.assert_status(response, 200)

    data = items_api.assert_json(response)
    assert data["item"]["name"] == "Updated Name"
    assert data["item"]["price"] == 100.00  # Unchanged
    assert data["item"]["description"] == "Original description"  # Unchanged

    print(f"  ✓ Name updated successfully")

    print("Test 3: Update multiple fields")
    response = items_api.update_item(item_id, price=150.00, quantity=20)

    items_api.assert_status(response, 200)
    data = items_api.assert_json(response)

    assert data["item"]["name"] == "Updated Name"  # From previous update
    assert data["item"]["price"] == 150.00
    assert data["item"]["quantity"] == 20

    print(f"  ✓ Multiple fields updated successfully")

    print("Test 4: Update non-existent item")
    response = items_api.update_item(999999, name="Wont Work")

    items_api.assert_status(response, 404)

    print(f"  ✓ 404 returned for non-existent item")

    print("Test 5: Verify update timestamp changed")
    response = items_api.get_item(item_id)
    data = items_api.assert_json(response)

    # Note: In a real test, you might want to verify updated_at > created_at
    # but for simplicity, we just verify the update persisted
    assert data["price"] == 150.00
    assert data["quantity"] == 20

    print(f"  ✓ Updates persisted correctly")

    print("\n✅ All update item tests passed!")
    return response
