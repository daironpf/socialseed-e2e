"""Payment API Service Page for Microservices Example.

This module provides the PaymentApiPage class for testing the Payment Service.
"""

from typing import Any, Dict, Optional
from playwright.sync_api import APIResponse

from socialseed_e2e.core.base_page import BasePage


class PaymentApiPage(BasePage):
    """Service page for Payment API (Port 5004).

    Processes payments. Depends on Users and Orders Services.

    Attributes:
        base_url: http://localhost:5004
    """

    def __init__(self, base_url: str = "http://localhost:5004") -> None:
        """Initialize the PaymentApiPage.

        Args:
            base_url: Base URL for the Payment Service
        """
        super().__init__(base_url)
        self.test_payment_id: Optional[int] = None

    def process_payment(self, order_id: int, user_id: int) -> APIResponse:
        """Process a payment (multi-service transaction).

        This operation:
        1. Gets order from Orders Service
        2. Checks user balance from Users Service
        3. Deducts balance via Users Service
        4. Updates order status via Orders Service

        Args:
            order_id: Order ID
            user_id: User ID
        """
        return self.post(
            "/api/payments", json={"order_id": order_id, "user_id": user_id}
        )

    def list_payments(self, user_id: Optional[int] = None) -> APIResponse:
        """List all payments or filter by user."""
        params = {}
        if user_id:
            params["user_id"] = user_id
        return self.get("/api/payments", params=params)

    def get_payment(self, payment_id: int) -> APIResponse:
        """Get payment by ID."""
        return self.get(f"/api/payments/{payment_id}")

    def get_user_payments(self, user_id: int) -> APIResponse:
        """Get all payments for a user."""
        return self.get(f"/api/users/{user_id}/payments")

    def refund_payment(self, payment_id: int) -> APIResponse:
        """Refund a payment."""
        return self.post("/api/refund", json={"payment_id": payment_id})

    def health_check(self) -> APIResponse:
        """Check service health."""
        return self.get("/health")
