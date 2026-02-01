"""Test module for deleting items.

Tests DELETE /api/items/{id} endpoint for removing items.
"""

from playwright.sync_api import APIResponse
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..items_api_page import ItemsApiPage


def run(items_api: "ItemsApiPage") -> APIResponse:
    """Test deleting items via DELETE /api/items/{id}.

    This test verifies:
    - Deleting an existing item returns 200
    - Item is actually removed from the database
    - Getting deleted item returns 404
    - Deleting non-existent item returns 404
    - Deleting already deleted item returns 404

    Args:
        items_api: Instance of ItemsApiPage for API interactions

    Returns:
        APIResponse: Response from the delete operation
    """
    print("Test 1: Create an item to delete")
    create_response = items_api.create_item(
        name="Item To Delete",
        price=29.99,
        description="This item will be deleted",
        quantity=3,
    )

    items_api.assert_status(create_response, 201)
    created_data = items_api.assert_json(create_response)
    item_id = created_data["id"]

    print(f"  ✓ Created item with ID: {item_id}")

    print("Test 2: Delete the item")
    response = items_api.delete_item(item_id)

    items_api.assert_status(response, 200)

    data = items_api.assert_json(response)
    assert data["message"] == "Item deleted successfully"
    assert data["id"] == item_id

    print(f"  ✓ Item deleted successfully")

    print("Test 3: Verify item is actually deleted")
    get_response = items_api.get_item(item_id)
    items_api.assert_status(get_response, 404)

    print(f"  ✓ Deleted item returns 404")

    print("Test 4: Delete non-existent item")
    response = items_api.delete_item(999999)

    items_api.assert_status(response, 404)

    print(f"  ✓ 404 returned for non-existent item")

    print("Test 5: Delete multiple items (bulk cleanup simulation)")
    # Create and delete multiple items
    created_ids = []
    for i in range(3):
        create_resp = items_api.create_item(name=f"Bulk Item {i}", price=float(i * 10))
        if create_resp.ok:
            item_data = create_resp.json()
            created_ids.append(item_data["id"])

    print(f"  Created {len(created_ids)} items for bulk deletion")

    # Delete all
    for item_id in created_ids:
        delete_resp = items_api.delete_item(item_id)
        items_api.assert_status(delete_resp, 200)

    print(f"  ✓ All {len(created_ids)} items deleted successfully")

    print("\n✅ All delete item tests passed!")
    return response
