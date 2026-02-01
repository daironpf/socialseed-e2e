"""Test module for login flow.

Tests POST /api/auth/login endpoint and token handling.
"""

from playwright.sync_api import APIResponse
from typing import TYPE_CHECKING
import uuid

if TYPE_CHECKING:
    from ..auth_api_page import AuthApiPage


def run(auth_api: "AuthApiPage") -> APIResponse:
    """Test user login flow with JWT tokens.

    This test verifies:
    - Login with valid credentials returns 200
    - Access token and refresh token are provided
    - Token metadata is correct
    - Login with invalid credentials returns 401
    - Tokens are properly stored for subsequent requests

    Args:
        auth_api: Instance of AuthApiPage for API interactions

    Returns:
        APIResponse: Response from the last operation
    """
    # First, register a test user
    unique_id = uuid.uuid4().hex[:8]
    test_username = f"loginuser_{unique_id}"
    test_password = "mypassword123"

    print(f"Setup: Register test user: {test_username}")
    register_response = auth_api.register(
        username=test_username,
        email=f"login_{unique_id}@example.com",
        password=test_password,
    )

    if not register_response.ok:
        print(
            f"  ⚠ Registration failed, but continuing with test: {register_response.status}"
        )
    else:
        print(f"  ✓ Test user registered")

    print("Test 1: Login with valid credentials")
    response = auth_api.login(username=test_username, password=test_password)

    auth_api.assert_status(response, 200)

    data = auth_api.assert_json(response)
    assert "tokens" in data, "Response should contain tokens"
    assert "user" in data, "Response should contain user data"
    assert "message" in data

    # Verify token structure
    tokens = data["tokens"]
    assert "access_token" in tokens, "Should have access_token"
    assert "refresh_token" in tokens, "Should have refresh_token"
    assert "token_type" in tokens, "Should have token_type"
    assert "expires_in" in tokens, "Should have expires_in"
    assert tokens["token_type"] == "Bearer"

    # Store tokens for other tests
    auth_api.store_tokens(data)

    print(f"  ✓ Login successful")
    print(f"  ✓ Access token received (length: {len(tokens['access_token'])})")
    print(f"  ✓ Refresh token received (length: {len(tokens['refresh_token'])})")
    print(f"  ✓ Token expires in: {tokens['expires_in']} seconds")

    print("Test 2: Verify user data in response")
    user = data["user"]
    assert user["username"] == test_username
    assert "id" in user
    assert "email" in user

    print(f"  ✓ User data correct (ID: {user['id']})")

    print("Test 3: Login with invalid password")
    response = auth_api.login(username=test_username, password="wrongpassword")

    auth_api.assert_status(response, 401)
    error_data = auth_api.assert_json(response)
    assert "error" in error_data
    assert (
        "invalid" in error_data["message"].lower()
        or "unauthorized" in error_data["message"].lower()
    )

    print("  ✓ Invalid password correctly rejected")

    print("Test 4: Login with non-existent user")
    response = auth_api.login(
        username="nonexistent_user_12345", password="somepassword"
    )

    auth_api.assert_status(response, 401)

    print("  ✓ Non-existent user correctly rejected")

    print("Test 5: Login with missing fields")
    response = auth_api.post("/api/auth/login", json={})

    auth_api.assert_status(response, 400)

    print("  ✓ Missing fields validation works")

    # Re-login to ensure tokens are stored for subsequent tests
    print("Setup: Re-login to store tokens for next tests")
    login_response = auth_api.login(username=test_username, password=test_password)
    if login_response.ok:
        auth_api.store_tokens(login_response.json())
        print("  ✓ Tokens stored successfully")

    print("\n✅ All login tests passed!")
    return response
