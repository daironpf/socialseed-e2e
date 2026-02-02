"""Orders API Service Page for Microservices Example.

This module provides the OrdersApiPage class for testing the Orders Service.
"""

from typing import Any, Dict, List, Optional

from playwright.sync_api import APIResponse

from socialseed_e2e.core.base_page import BasePage


class OrdersApiPage(BasePage):
    """Service page for Orders API (Port 5003).

    Manages orders. Depends on Users Service for validation.

    Attributes:
        base_url: http://localhost:5003
    """

    def __init__(self, base_url: str = "http://localhost:5003") -> None:
        """Initialize the OrdersApiPage.

        Args:
            base_url: Base URL for the Orders Service
        """
        super().__init__(base_url)
        self.test_order_id: Optional[int] = None

    def list_orders(self, user_id: Optional[int] = None) -> APIResponse:
        """List all orders or filter by user."""
        params = {}
        if user_id:
            params["user_id"] = user_id
        return self.get("/api/orders", params=params)

    def create_order(self, user_id: int, items: List[str], total_amount: float) -> APIResponse:
        """Create a new order (validates user via Users Service).

        Args:
            user_id: User ID (validated against Users Service)
            items: List of items
            total_amount: Total order amount
        """
        return self.post(
            "/api/orders",
            json={"user_id": user_id, "items": items, "total_amount": total_amount},
        )

    def get_order(self, order_id: int) -> APIResponse:
        """Get order by ID."""
        return self.get(f"/api/orders/{order_id}")

    def update_status(self, order_id: int, status: str) -> APIResponse:
        """Update order status."""
        return self.put(f"/api/orders/{order_id}/status", json={"status": status})

    def get_user_orders(self, user_id: int) -> APIResponse:
        """Get all orders for a user."""
        return self.get(f"/api/users/{user_id}/orders")

    def health_check(self) -> APIResponse:
        """Check service health."""
        return self.get("/health")
