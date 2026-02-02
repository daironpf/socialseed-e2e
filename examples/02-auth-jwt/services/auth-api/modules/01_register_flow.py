"""Test module for user registration flow.

Tests POST /api/auth/register endpoint.
"""

import uuid
from typing import TYPE_CHECKING

from playwright.sync_api import APIResponse

if TYPE_CHECKING:
    from ..auth_api_page import AuthApiPage


def run(auth_api: "AuthApiPage") -> APIResponse:
    """Test user registration flow.

    This test verifies:
    - Registration with valid data returns 201
    - User data is returned correctly
    - Duplicate username returns 409
    - Duplicate email returns 409
    - Validation errors return 400

    Args:
        auth_api: Instance of AuthApiPage for API interactions

    Returns:
        APIResponse: Response from the last operation
    """
    # Generate unique test data to avoid conflicts
    unique_id = uuid.uuid4().hex[:8]
    test_username = f"testuser_{unique_id}"
    test_email = f"test_{unique_id}@example.com"

    print(f"Test 1: Register new user: {test_username}")
    response = auth_api.register(username=test_username, email=test_email, password="securepass123")

    auth_api.assert_status(response, 201)

    data = auth_api.assert_json(response)
    assert "user" in data, "Response should contain user data"
    assert data["user"]["username"] == test_username
    assert data["user"]["email"] == test_email
    assert "id" in data["user"]

    # Store for potential use in other tests
    auth_api.test_user_id = data["user"]["id"]
    auth_api.test_username = test_username
    auth_api.test_password = "securepass123"

    print(f"  ✓ User registered with ID: {data['user']['id']}")

    print("Test 2: Attempt duplicate username registration")
    response = auth_api.register(
        username=test_username,  # Same username
        email=f"different_{unique_id}@example.com",
        password="securepass123",
    )

    auth_api.assert_status(response, 409)
    error_data = auth_api.assert_json(response)
    assert "error" in error_data
    assert "username" in error_data["message"].lower() or "exists" in error_data["message"].lower()

    print("  ✓ Duplicate username correctly rejected")

    print("Test 3: Attempt duplicate email registration")
    response = auth_api.register(
        username=f"different_{unique_id}",
        email=test_email,  # Same email
        password="securepass123",
    )

    auth_api.assert_status(response, 409)
    error_data = auth_api.assert_json(response)
    assert "error" in error_data

    print("  ✓ Duplicate email correctly rejected")

    print("Test 4: Validation - short username")
    response = auth_api.register(
        username="ab",  # Too short
        email=f"valid_{unique_id}@example.com",
        password="securepass123",
    )

    auth_api.assert_status(response, 400)
    error_data = auth_api.assert_json(response)
    assert "error" in error_data

    print("  ✓ Short username validation works")

    print("Test 5: Validation - short password")
    response = auth_api.register(
        username=f"validuser_{unique_id}",
        email=f"valid2_{unique_id}@example.com",
        password="123",  # Too short
    )

    auth_api.assert_status(response, 400)
    error_data = auth_api.assert_json(response)
    assert "error" in error_data

    print("  ✓ Short password validation works")

    print("Test 6: Validation - invalid email")
    response = auth_api.register(
        username=f"validuser2_{unique_id}",
        email="not-an-email",
        password="securepass123",
    )

    auth_api.assert_status(response, 400)

    print("  ✓ Invalid email validation works")

    print("\n✅ All registration tests passed!")
    return response
