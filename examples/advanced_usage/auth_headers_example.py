"""Authorization Headers Examples.

This module demonstrates different authentication methods in SocialSeed E2E.

Run this example:
    python examples/advanced_usage/auth_headers_example.py
"""

import base64
from typing import Dict, Optional
from playwright.sync_api import APIResponse, sync_playwright

from socialseed_e2e.core.base_page import BasePage


class AuthPage(BasePage):
    """Service page demonstrating various authentication methods."""

    def __init__(self, base_url: str = "http://localhost:8765", **kwargs):
        super().__init__(base_url=base_url, **kwargs)
        self.access_token: Optional[str] = None


def example_basic_auth():
    """Example: Basic Authentication.

    Basic Auth encodes credentials as base64 and sends them in the Authorization header.
    Format: "Basic <base64(username:password)>"
    """
    print("\n=== Basic Authentication Example ===\n")

    with sync_playwright() as p:
        page = BasePage(base_url="http://localhost:8765", playwright=p)
        page.setup()

        # Create Basic Auth header
        credentials = base64.b64encode(b"admin:admin123").decode("utf-8")
        headers = {"Authorization": f"Basic {credentials}"}

        # Make authenticated request
        response = page.get("/api/users", headers=headers)

        print(f"Status: {response.status}")
        print(f"Response: {response.text()[:200]}...")

        page.teardown()


def example_bearer_token():
    """Example: Bearer Token (JWT) Authentication.

    Bearer tokens are typically JWTs sent in the Authorization header.
    Format: "Bearer <token>"
    """
    print("\n=== Bearer Token Example ===\n")

    with sync_playwright() as p:
        page = AuthPage(base_url="http://localhost:8765", playwright=p)
        page.setup()

        # Step 1: Login to get token (simulated)
        login_response = page.post(
            "/api/auth/login",
            json={"email": "admin@example.com", "password": "admin123"},
        )

        if login_response.ok:
            data = login_response.json()
            # Extract token (mock server returns it directly)
            page.access_token = data.get("token", data.get("access_token"))

        if page.access_token:
            # Step 2: Use token for authenticated requests
            headers = {"Authorization": f"Bearer {page.access_token}"}
            response = page.get("/api/profile", headers=headers)

            print(f"Status: {response.status}")
            print(f"Authenticated request successful!")
        else:
            print("Token not available, using mock data")

        page.teardown()


def example_api_key():
    """Example: API Key Authentication.

    API keys are typically sent as custom headers or query parameters.
    Common headers: X-API-Key, Api-Key, X-Auth-Token
    """
    print("\n=== API Key Example ===\n")

    with sync_playwright() as p:
        page = BasePage(base_url="http://localhost:8765", playwright=p)
        page.setup()

        # API Key in header
        headers = {"X-API-Key": "your-api-key-here"}
        response = page.get("/api/protected", headers=headers)

        print(f"Status: {response.status}")
        print(f"Response: {response.text()[:200]}...")

        # Alternative: API Key as query parameter
        response2 = page.get("/api/protected?api_key=your-api-key-here")
        print(f"Status (query param): {response2.status}")

        page.teardown()


def example_custom_headers():
    """Example: Custom Headers for any purpose.

    SocialSeed E2E allows passing custom headers to any request.
    """
    print("\n=== Custom Headers Example ===\n")

    with sync_playwright() as p:
        page = BasePage(base_url="http://localhost:8765", playwright=p)
        page.setup()

        # Multiple custom headers
        headers = {
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Cache-Control": "no-cache",
            "X-Request-ID": "unique-request-123",
            "X-Custom-Header": "custom-value",
        }

        response = page.get("/api/users", headers=headers)

        print(f"Status: {response.status}")
        print(f"Custom headers sent successfully!")

        page.teardown()


def example_oauth2():
    """Example: OAuth 2.0 Flow (Conceptual).

    OAuth2 typically involves:
    1. Authorization Code flow
    2. Client Credentials flow
    3. Refresh Token flow
    """
    print("\n=== OAuth 2.0 Flow Example (Conceptual) ===\n")

    with sync_playwright() as p:
        page = AuthPage(base_url="http://localhost:8765", playwright=p)
        page.setup()

        # This is a simplified OAuth2 Client Credentials flow
        # In production, you'd use an OAuth library

        # Step 1: Get token from OAuth server
        token_url = "http://localhost:8765/oauth/token"
        token_data = {
            "grant_type": "client_credentials",
            "client_id": "your-client-id",
            "client_secret": "your-client-secret",
        }

        response = page.post(token_url, json=token_data)

        if response.ok:
            token_response = response.json()
            page.access_token = token_response.get("access_token")

            # Step 2: Use token
            if page.access_token:
                headers = {"Authorization": f"Bearer {page.access_token}"}
                protected_response = page.get("/api/protected", headers=headers)
                print(f"Protected resource: {protected_response.status}")
        else:
            print("OAuth not available on mock server, using fallback")

        page.teardown()


class HeadersPage(BasePage):
    """Service page with built-in header management."""

    def __init__(self, base_url: str = "http://localhost:8765", **kwargs):
        super().__init__(base_url=base_url, **kwargs)
        self._default_headers: Dict[str, str] = {}

    def set_default_headers(self, headers: Dict[str, str]) -> None:
        """Set default headers for all requests."""
        self._default_headers = headers

    def add_default_header(self, key: str, value: str) -> None:
        """Add a single default header."""
        self._default_headers[key] = value

    def get_with_defaults(self, path: str, **kwargs) -> APIResponse:
        """Make a GET request with default headers merged."""
        headers = {**self._default_headers, **kwargs.get("headers", {})}
        return self.get(path, headers=headers)


def example_default_headers():
    """Example: Default headers for all requests.

    Useful when all requests need the same authentication or headers.
    """
    print("\n=== Default Headers Example ===\n")

    with sync_playwright() as p:
        page = HeadersPage(base_url="http://localhost:8765", playwright=p)
        page.setup()

        # Set default headers
        page.set_default_headers(
            {"Accept": "application/json", "X-Client-Version": "1.0.0"}
        )

        # These requests will automatically include the default headers
        response1 = page.get_with_defaults("/api/users")
        response2 = page.get_with_defaults("/api/users/1")

        print(f"Request 1 status: {response1.status}")
        print(f"Request 2 status: {response2.status}")

        page.teardown()


if __name__ == "__main__":
    # Run all examples
    print("=" * 60)
    print("Authorization Headers Examples")
    print("=" * 60)

    try:
        example_basic_auth()
    except Exception as e:
        print(f"Basic Auth example error: {e}")

    try:
        example_bearer_token()
    except Exception as e:
        print(f"Bearer Token example error: {e}")

    try:
        example_api_key()
    except Exception as e:
        print(f"API Key example error: {e}")

    try:
        example_custom_headers()
    except Exception as e:
        print(f"Custom Headers example error: {e}")

    try:
        example_oauth2()
    except Exception as e:
        print(f"OAuth2 example error: {e}")

    try:
        example_default_headers()
    except Exception as e:
        print(f"Default Headers example error: {e}")

    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)
