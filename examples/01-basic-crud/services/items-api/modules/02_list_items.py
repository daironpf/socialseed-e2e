"""Test module for listing items.

Tests GET /api/items endpoint for listing all items.
"""

from playwright.sync_api import APIResponse
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..items_api_page import ItemsApiPage


def run(items_api: "ItemsApiPage") -> APIResponse:
    """Test listing items via GET /api/items.

    This test verifies:
    - Listing items returns 200
    - Response contains items array and pagination info
    - Pagination parameters work correctly
    - Search functionality works

    Args:
        items_api: Instance of ItemsApiPage for API interactions

    Returns:
        APIResponse: Response from the list operation
    """
    print("Test 1: List all items with default pagination")
    response = items_api.list_items()

    items_api.assert_status(response, 200)

    data = items_api.assert_json(response)
    assert "items" in data, "Response should contain items array"
    assert "pagination" in data, "Response should contain pagination info"

    pagination = data["pagination"]
    assert pagination["page"] == 1
    assert pagination["limit"] == 10

    print(f"  ✓ Listed {len(data['items'])} items")

    print("Test 2: List items with custom pagination")
    response = items_api.list_items(page=1, limit=5)

    items_api.assert_status(response, 200)
    data = items_api.assert_json(response)

    assert len(data["items"]) <= 5, "Should respect limit parameter"
    assert data["pagination"]["limit"] == 5

    print(f"  ✓ Custom pagination works (limit=5)")

    print("Test 3: Search functionality")
    # First create an item with a unique name
    unique_name = "UniqueSearchTestItem12345"
    create_response = items_api.create_item(
        name=unique_name,
        price=100.00,
        description="This is a unique test item for search",
    )

    if create_response.ok:
        created_data = create_response.json()
        items_api.created_items.append(created_data["id"])

        # Now search for it
        search_response = items_api.list_items(search="UniqueSearchTest")
        items_api.assert_status(search_response, 200)

        search_data = search_response.json()
        found = any(item["name"] == unique_name for item in search_data["items"])
        assert found, "Should find the item by search term"

        print(f"  ✓ Search functionality works")

    print("\n✅ All list items tests passed!")
    return response
