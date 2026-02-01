"""Users API Service Page for Microservices Example.

This module provides the UsersApiPage class for testing the Users Service.
"""

from typing import Any, Dict, Optional
from playwright.sync_api import APIResponse

from socialseed_e2e.core.base_page import BasePage


class UsersApiPage(BasePage):
    """Service page for Users API (Port 5002).

    Manages user accounts and balances.

    Attributes:
        base_url: http://localhost:5002
    """

    def __init__(self, base_url: str = "http://localhost:5002") -> None:
        """Initialize the UsersApiPage.

        Args:
            base_url: Base URL for the Users Service
        """
        super().__init__(base_url)
        self.test_user_id: Optional[int] = None

    def list_users(self) -> APIResponse:
        """List all users."""
        return self.get("/api/users")

    def get_user(self, user_id: int) -> APIResponse:
        """Get user by ID."""
        return self.get(f"/api/users/{user_id}")

    def get_balance(self, user_id: int) -> APIResponse:
        """Get user balance."""
        return self.get(f"/api/users/{user_id}/balance")

    def update_balance(self, user_id: int, amount: float) -> APIResponse:
        """Update user balance (used by Payment Service).

        Args:
            user_id: User ID
            amount: Amount to add (positive) or deduct (negative)
        """
        return self.post(f"/api/users/{user_id}/balance", json={"amount": amount})

    def create_user(
        self, username: str, email: str, balance: float = 100.0
    ) -> APIResponse:
        """Create a new user."""
        return self.post(
            "/api/users",
            json={"username": username, "email": email, "balance": balance},
        )

    def health_check(self) -> APIResponse:
        """Check service health."""
        return self.get("/health")
