"""Items API Service Page.

This module provides the ItemsApiPage class for testing the Items API.
"""

from typing import Any, Dict, Optional

from playwright.sync_api import APIResponse

from socialseed_e2e.core.base_page import BasePage


class ItemsApiPage(BasePage):
    """Service page for Items API.

    Provides methods for CRUD operations on items:
    - Create: POST /api/items
    - List: GET /api/items
    - Get: GET /api/items/{id}
    - Update: PUT /api/items/{id}
    - Delete: DELETE /api/items/{id}

    Attributes:
        base_url: The base URL for the API
        created_items: List of item IDs created during tests (for cleanup)
    """

    def __init__(self, base_url: str = "http://localhost:5000") -> None:
        """Initialize the ItemsApiPage.

        Args:
            base_url: Base URL for the Items API
        """
        super().__init__(base_url)
        self.created_items: list = []
        self.last_created_item_id: Optional[int] = None

    def create_item(
        self, name: str, price: float, description: str = "", quantity: int = 0
    ) -> APIResponse:
        """Create a new item.

        Args:
            name: Item name
            price: Item price
            description: Item description
            quantity: Item quantity in stock

        Returns:
            APIResponse: Response with created item data
        """
        data = {
            "name": name,
            "price": price,
            "description": description,
            "quantity": quantity,
        }
        return self.post("/api/items", json=data)

    def list_items(self, page: int = 1, limit: int = 10, search: str = "") -> APIResponse:
        """List all items with pagination.

        Args:
            page: Page number (1-based)
            limit: Items per page
            search: Optional search term

        Returns:
            APIResponse: Response with items list and pagination info
        """
        params: Dict[str, Any] = {"page": page, "limit": limit}
        if search:
            params["search"] = search
        return self.get("/api/items", params=params)

    def get_item(self, item_id: int) -> APIResponse:
        """Get a single item by ID.

        Args:
            item_id: ID of the item to retrieve

        Returns:
            APIResponse: Response with item data
        """
        return self.get(f"/api/items/{item_id}")

    def update_item(
        self,
        item_id: int,
        name: Optional[str] = None,
        price: Optional[float] = None,
        description: Optional[str] = None,
        quantity: Optional[int] = None,
    ) -> APIResponse:
        """Update an existing item.

        Args:
            item_id: ID of the item to update
            name: New name (optional)
            price: New price (optional)
            description: New description (optional)
            quantity: New quantity (optional)

        Returns:
            APIResponse: Response with updated item data
        """
        data: Dict[str, Any] = {}
        if name is not None:
            data["name"] = name
        if price is not None:
            data["price"] = price
        if description is not None:
            data["description"] = description
        if quantity is not None:
            data["quantity"] = quantity

        return self.put(f"/api/items/{item_id}", json=data)

    def delete_item(self, item_id: int) -> APIResponse:
        """Delete an item.

        Args:
            item_id: ID of the item to delete

        Returns:
            APIResponse: Response confirming deletion
        """
        return self.delete(f"/api/items/{item_id}")

    def health_check(self) -> APIResponse:
        """Check API health status.

        Returns:
            APIResponse: Health check response
        """
        return self.get("/health")

    def cleanup_created_items(self) -> None:
        """Delete all items created during tests.

        Call this in test cleanup to ensure test isolation.
        """
        for item_id in self.created_items:
            try:
                self.delete_item(item_id)
            except Exception:
                pass  # Ignore cleanup errors
        self.created_items.clear()
