"""Test module for Users Service.

Tests user management and balance operations.
"""

from typing import TYPE_CHECKING

from playwright.sync_api import APIResponse

if TYPE_CHECKING:
    from ..users_api_page import UsersApiPage


def run(users_api: "UsersApiPage") -> APIResponse:
    """Test Users Service operations.

    Tests:
    - List users (pre-loaded data)
    - Get user by ID
    - Check balance
    - Create new user

    Args:
        users_api: Instance of UsersApiPage

    Returns:
        APIResponse: Last response
    """
    print("Test 1: List pre-loaded users")
    response = users_api.list_users()
    users_api.assert_status(response, 200)

    data = users_api.assert_json(response)
    assert "users" in data
    assert len(data["users"]) >= 3  # alice, bob, charlie
    print(f"  ✓ Found {len(data['users'])} users")

    print("Test 2: Get user alice (ID: 1)")
    response = users_api.get_user(1)
    users_api.assert_status(response, 200)

    user = users_api.assert_json(response)
    assert user["username"] == "alice"
    assert user["balance"] == 500.0
    print(f"  ✓ Alice found with balance: ${user['balance']}")

    print("Test 3: Check balance endpoint")
    response = users_api.get_balance(1)
    users_api.assert_status(response, 200)

    balance_data = users_api.assert_json(response)
    assert balance_data["balance"] == 500.0
    print(f"  ✓ Balance endpoint works")

    print("Test 4: Create new user")
    import uuid

    unique_id = uuid.uuid4().hex[:6]
    response = users_api.create_user(
        username=f"testuser_{unique_id}",
        email=f"test_{unique_id}@example.com",
        balance=200.0,
    )
    users_api.assert_status(response, 201)

    new_user = users_api.assert_json(response)
    users_api.test_user_id = new_user["user"]["id"]
    print(f"  ✓ Created user with ID: {users_api.test_user_id}")

    print("\n✅ All Users Service tests passed!")
    return response
