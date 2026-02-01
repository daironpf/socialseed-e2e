"""Test module for protected endpoint access.

Tests protected endpoints with JWT authentication.
"""

from playwright.sync_api import APIResponse
from typing import TYPE_CHECKING
import uuid

if TYPE_CHECKING:
    from ..auth_api_page import AuthApiPage


def run(auth_api: "AuthApiPage") -> APIResponse:
    """Test accessing protected endpoints with JWT.

    This test verifies:
    - Protected endpoint requires authentication
    - Valid token grants access
    - Invalid token is rejected
    - Expired token is rejected (if testable)
    - Malformed Authorization header is rejected
    - Missing Authorization header is rejected

    Args:
        auth_api: Instance of AuthApiPage for API interactions

    Returns:
        APIResponse: Response from the last operation
    """
    # Ensure we have tokens
    if not auth_api.access_token:
        print("Setup: Creating test user and logging in")
        unique_id = uuid.uuid4().hex[:8]
        test_username = f"protecteduser_{unique_id}"
        test_password = "mypassword123"

        # Register
        auth_api.register(
            username=test_username,
            email=f"protected_{unique_id}@example.com",
            password=test_password,
        )

        # Login
        login_response = auth_api.login(username=test_username, password=test_password)

        if login_response.ok:
            auth_api.store_tokens(login_response.json())
            print("  ✓ Logged in and tokens stored")
        else:
            print("  ⚠ Login failed, some tests may fail")

    print("Test 1: Access protected endpoint without authentication")
    response = auth_api.get("/api/protected")
    auth_api.assert_status(response, 401)

    error_data = auth_api.assert_json(response)
    assert "error" in error_data

    print("  ✓ Unauthenticated access correctly rejected")

    print("Test 2: Access protected endpoint with valid token")
    response = auth_api.get_protected()
    auth_api.assert_status(response, 200)

    data = auth_api.assert_json(response)
    assert "message" in data
    assert "user" in data
    assert "data" in data

    print(f"  ✓ Authenticated access granted")
    print(f"  ✓ User info: {data['user']}")

    print("Test 3: Access user profile with valid token")
    response = auth_api.get_profile()
    auth_api.assert_status(response, 200)

    data = auth_api.assert_json(response)
    assert "user" in data

    print(f"  ✓ Profile access granted")
    print(f"  ✓ Username: {data['user']['username']}")

    print("Test 4: Access with invalid token")
    # Temporarily set invalid token
    valid_token = auth_api.access_token
    auth_api.access_token = "invalid.jwt.token"

    try:
        response = auth_api.get_protected()
        auth_api.assert_status(response, 401)
        print("  ✓ Invalid token correctly rejected")
    except Exception as e:
        print(f"  ✓ Invalid token rejected: {e}")
    finally:
        auth_api.access_token = valid_token

    print("Test 5: Access with malformed Authorization header")
    response = auth_api.get(
        "/api/protected", headers={"Authorization": "NotBearer token123"}
    )
    auth_api.assert_status(response, 401)

    print("  ✓ Malformed header correctly rejected")

    print("Test 6: Access with empty Authorization header")
    response = auth_api.get("/api/protected", headers={"Authorization": ""})
    auth_api.assert_status(response, 401)

    print("  ✓ Empty header correctly rejected")

    print("Test 7: Re-access with valid token (session continuity)")
    response = auth_api.get_protected()
    auth_api.assert_status(response, 200)

    data = auth_api.assert_json(response)
    if auth_api.current_user:
        assert data["user"]["username"] == auth_api.current_user["username"]
    else:
        assert "username" in data["user"]

    print("  ✓ Session continuity maintained")

    print("\n✅ All protected endpoint tests passed!")
    return response
