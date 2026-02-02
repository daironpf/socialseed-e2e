"""Auth API Service Page.

This module provides the AuthApiPage class for JWT authentication testing.
"""

from typing import Any, Dict, Optional

from playwright.sync_api import APIResponse

from socialseed_e2e.core.base_page import BasePage


class AuthApiPage(BasePage):
    """Service page for Auth API with JWT authentication.

    Provides methods for:
    - User registration
    - User login (with JWT tokens)
    - Token refresh
    - Accessing protected endpoints with authentication

    Attributes:
        base_url: The base URL for the auth service
        access_token: Current JWT access token
        refresh_token: Current JWT refresh token
        current_user: Information about the logged-in user
    """

    def __init__(self, base_url: str = "http://localhost:5001") -> None:
        """Initialize the AuthApiPage.

        Args:
            base_url: Base URL for the Auth API
        """
        super().__init__(base_url)
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.current_user: Optional[Dict[str, Any]] = None
        # Test data storage for sharing between tests
        self.test_user_id: Optional[int] = None
        self.test_username: Optional[str] = None
        self.test_password: Optional[str] = None

    def register(self, username: str, email: str, password: str) -> APIResponse:
        """Register a new user.

        Args:
            username: Username for the new account
            email: Email address
            password: Password (minimum 6 characters)

        Returns:
            APIResponse: Response with user data
        """
        data = {"username": username, "email": email, "password": password}
        return self.post("/api/auth/register", json=data)

    def login(self, username: str, password: str) -> APIResponse:
        """Login and store JWT tokens.

        Args:
            username: Username
            password: Password

        Returns:
            APIResponse: Response with tokens and user data
        """
        data = {"username": username, "password": password}
        return self.post("/api/auth/login", json=data)

    def store_tokens(self, response_data: Dict[str, Any]) -> None:
        """Store tokens from login/refresh response.

        Args:
            response_data: Response JSON containing tokens
        """
        if "tokens" in response_data:
            tokens = response_data["tokens"]
            self.access_token = tokens.get("access_token")
            self.refresh_token = tokens.get("refresh_token")

        if "user" in response_data:
            self.current_user = response_data["user"]

    def refresh_token_request(self) -> APIResponse:
        """Refresh access token using refresh token.

        Returns:
            APIResponse: Response with new tokens
        """
        if not self.refresh_token:
            raise ValueError("No refresh token available. Login first.")

        data = {"refresh_token": self.refresh_token}
        return self.post("/api/auth/refresh", json=data)

    def get_auth_headers(self) -> Dict[str, str]:
        """Get headers with authorization token.

        Returns:
            Dict with Authorization header
        """
        if not self.access_token:
            raise ValueError("No access token available. Login first.")

        return {"Authorization": f"Bearer {self.access_token}"}

    def get_protected(self) -> APIResponse:
        """Access protected endpoint with authentication.

        Returns:
            APIResponse: Response from protected endpoint
        """
        headers = self.get_auth_headers()
        return self.get("/api/protected", headers=headers)

    def get_profile(self) -> APIResponse:
        """Get current user profile (requires auth).

        Returns:
            APIResponse: Response with user profile
        """
        headers = self.get_auth_headers()
        return self.get("/api/profile", headers=headers)

    def health_check(self) -> APIResponse:
        """Check API health status.

        Returns:
            APIResponse: Health check response
        """
        return self.get("/health")

    def logout(self) -> None:
        """Clear stored tokens (client-side logout)."""
        self.access_token = None
        self.refresh_token = None
        self.current_user = None
