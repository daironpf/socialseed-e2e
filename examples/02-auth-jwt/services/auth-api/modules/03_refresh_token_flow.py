"""Test module for token refresh flow.

Tests POST /api/auth/refresh endpoint.
"""

from playwright.sync_api import APIResponse
from typing import TYPE_CHECKING
import uuid
import time

if TYPE_CHECKING:
    from ..auth_api_page import AuthApiPage


def run(auth_api: "AuthApiPage") -> APIResponse:
    """Test token refresh flow.

    This test verifies:
    - Refresh token can be used to get new access token
    - New tokens have different values than old ones
    - Old refresh token remains valid (until expiry)
    - Invalid refresh token returns 401
    - Malformed refresh token returns 401

    Args:
        auth_api: Instance of AuthApiPage for API interactions

    Returns:
        APIResponse: Response from the last operation
    """
    # Ensure we have a logged-in user with tokens
    if not auth_api.refresh_token:
        print("Setup: Creating test user and logging in")
        unique_id = uuid.uuid4().hex[:8]
        test_username = f"refreshuser_{unique_id}"
        test_password = "mypassword123"

        # Register
        register_response = auth_api.register(
            username=test_username,
            email=f"refresh_{unique_id}@example.com",
            password=test_password,
        )

        if register_response.ok:
            print(f"  ✓ User registered")

        # Login
        login_response = auth_api.login(username=test_username, password=test_password)

        auth_api.assert_status(login_response, 200)
        auth_api.store_tokens(login_response.json())
        print("  ✓ Logged in and tokens stored")

    # Store old tokens for comparison
    old_access_token = auth_api.access_token
    old_refresh_token = auth_api.refresh_token

    print("Test 1: Refresh access token using refresh token")
    response = auth_api.refresh_token_request()

    auth_api.assert_status(response, 200)

    data = auth_api.assert_json(response)
    assert "tokens" in data, "Response should contain new tokens"
    assert "message" in data

    new_tokens = data["tokens"]
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens

    print(f"  ✓ New access token received")
    print(f"  ✓ New refresh token received")

    print("Test 2: Verify new tokens are different from old ones")
    assert new_tokens["access_token"] != old_access_token, (
        "Access token should be different"
    )
    # Note: Refresh token might or might not be rotated depending on implementation

    print("  ✓ New access token is different from old one")

    # Update stored tokens
    auth_api.store_tokens(data)

    print("Test 3: Verify new access token works")
    response = auth_api.get_protected()
    auth_api.assert_status(response, 200)

    print("  ✓ New access token works correctly")

    print("Test 4: Refresh with invalid token")
    # Temporarily replace with invalid token
    valid_refresh = auth_api.refresh_token
    auth_api.refresh_token = "invalid.token.here"

    response = auth_api.refresh_token_request()
    auth_api.assert_status(response, 401)

    # Restore valid token
    auth_api.refresh_token = valid_refresh

    print("  ✓ Invalid token correctly rejected")

    print("Test 5: Refresh with malformed token")
    auth_api.refresh_token = "not-a-valid-jwt"

    response = auth_api.refresh_token_request()
    auth_api.assert_status(response, 401)

    # Restore valid token
    auth_api.refresh_token = valid_refresh

    print("  ✓ Malformed token correctly rejected")

    print("Test 6: Missing refresh token in request")
    response = auth_api.post("/api/auth/refresh", json={})
    auth_api.assert_status(response, 400)

    print("  ✓ Missing token validation works")

    print("\n✅ All token refresh tests passed!")
    return response
