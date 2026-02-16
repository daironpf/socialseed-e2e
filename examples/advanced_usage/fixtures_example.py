"""Test Fixtures Examples.

This module demonstrates setup/teardown patterns and fixture management
in SocialSeed E2E.

Run this example:
    python examples/advanced_usage/fixtures_example.py
"""

import uuid
from typing import Any, Dict, List, Optional
from playwright.sync_api import APIResponse, sync_playwright

from socialseed_e2e.core.base_page import BasePage


class FixturePage(BasePage):
    """Service page with built-in fixture support."""

    def __init__(self, base_url: str = "http://localhost:8765", **kwargs):
        super().__init__(base_url=base_url, **kwargs)
        # State that persists across tests
        self.created_resources: List[str] = []
        self.test_data: Dict[str, Any] = {}
        self.auth_token: Optional[str] = None


def example_page_attributes():
    """Example: Using page attributes as fixtures.

    Page attributes persist across test modules, making them ideal
    for sharing state between tests.
    """
    print("\n=== Page Attributes as Fixtures ===\n")

    with sync_playwright() as p:
        page = FixturePage(base_url="http://localhost:8765", playwright=p)
        page.setup()

        # Simulate test 1: Create a user
        unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        create_response = page.post(
            "/api/users",
            json={
                "email": unique_email,
                "name": "Test User",
                "password": "testpass123",
            },
        )

        if create_response.ok:
            user_data = create_response.json()
            user_id = user_data.get("id")

            # Store in page attribute (available to next test)
            page.test_data["last_created_user"] = user_data
            page.created_resources.append(f"user:{user_id}")

            print(f"Test 1: Created user {user_id}")
            print(
                f"  Stored in page.test_data: {bool(page.test_data.get('last_created_user'))}"
            )

        # Simulate test 2: Use the user from previous test
        if page.test_data.get("last_created_user"):
            user = page.test_data["last_created_user"]
            print(f"\nTest 2: Using user from previous test: {user.get('email')}")

        page.teardown()


def example_setup_method():
    """Example: Using setup() for test initialization.

    The BasePage.setup() method runs before each test,
    making it perfect for initialization.
    """
    print("\n=== Setup Method Example ===\n")

    class SetupPage(BasePage):
        """Page with custom setup logic."""

        def setup(self):
            """Override setup to add custom initialization."""
            super().setup()

            # Custom setup: authenticate
            login_response = self.post(
                "/api/auth/login",
                json={"email": "admin@example.com", "password": "admin123"},
            )

            if login_response.ok:
                data = login_response.json()
                self.auth_token = data.get("token", data.get("access_token"))
                print(f"  ✓ Authenticated, token: {self.auth_token[:20]}...")

    with sync_playwright() as p:
        page = SetupPage(base_url="http://localhost:8765", playwright=p)

        # setup() is called automatically when running via e2e run
        page.setup()

        # Now we can use authenticated requests
        if page.auth_token:
            headers = {"Authorization": f"Bearer {page.auth_token}"}
            response = page.get("/api/protected", headers=headers)
            print(f"  Authenticated request status: {response.status}")

        page.teardown()


def example_teardown_cleanup():
    """Example: Using teardown() for cleanup.

    The BasePage.teardown() method runs after each test,
    making it perfect for cleanup.
    """
    print("\n=== Teardown Cleanup Example ===\n")

    created_items = []

    with sync_playwright() as p:
        page = FixturePage(base_url="http://localhost:8765", playwright=p)
        page.setup()

        # Create some test data
        for i in range(3):
            unique_id = uuid.uuid4().hex[:8]
            response = page.post(
                "/api/users",
                json={
                    "email": f"user_{unique_id}@example.com",
                    "name": f"User {i}",
                    "password": "test123",
                },
            )

            if response.ok:
                item_id = response.json().get("id")
                created_items.append(item_id)
                print(f"  Created item: {item_id}")

        print(f"\n  Total created: {len(created_items)}")

        # In a real scenario, teardown() would clean these up
        # Here we just demonstrate the pattern
        print("  Teardown would clean up: " + ", ".join(created_items[:2]) + "...")

        page.teardown()


def example_pytest_fixtures():
    """Example: Using pytest fixtures with SocialSeed E2E.

    This shows how to integrate pytest fixtures with the framework.
    """
    print("\n=== Pytest Fixtures Example ===\n")

    # These would be in conftest.py
    print("""
# Example conftest.py configuration:

import pytest
from socialseed_e2e.core.base_page import BasePage

@pytest.fixture(scope="session")
def base_url():
    \"\"\"Provide base URL for all tests.\"\"\"
    return "http://localhost:8765"

@pytest.fixture(scope="function")
def authenticated_page(base_url, playwright):
    \"\"\"Provide an authenticated page for tests.\"\"\"
    page = BasePage(base_url=base_url, playwright=playwright)
    page.setup()
    
    # Authenticate
    page.post("/api/auth/login", json={
        "email": "admin@example.com",
        "password": "admin123"
    })
    
    yield page
    
    page.teardown()

@pytest.fixture
def test_user():
    \"\"\"Generate a unique test user.\"\"\"
    import uuid
    return {
        "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
        "name": "Test User",
        "password": "testpass123"
    }
""")


def example_state_sharing():
    """Example: Sharing state between test modules.

    Tests run in order (alphabetically), so you can use
    page attributes to share state.
    """
    print("\n=== State Sharing Between Tests ===\n")

    # Module 01_login.py
    print("Module 01_login.py:")

    with sync_playwright() as p:
        page = FixturePage(base_url="http://localhost:8765", playwright=p)
        page.setup()

        # Login and store token
        login_response = page.post(
            "/api/auth/login",
            json={"email": "admin@example.com", "password": "admin123"},
        )

        if login_response.ok:
            data = login_response.json()
            page.auth_token = data.get("token", data.get("access_token"))
            print(f"  ✓ Logged in, token stored in page.auth_token")

        page.teardown()

    # Module 02_create_item.py (runs after 01_login.py)
    print("\nModule 02_create_item.py:")
    print("  ✓ Can access page.auth_token from previous module")

    # Module 03_get_item.py
    print("\nModule 03_get_item.py:")
    print("  ✓ Can access item created in 02_create_item.py")


def example_test_isolation():
    """Example: Ensuring test isolation.

    Best practices for keeping tests independent.
    """
    print("\n=== Test Isolation Example ===\n")

    print("""
# BAD: Tests depend on each other
def test_01_create():
    page.user_id = create_user()
    
def test_02_get():
    # Relies on test_01 running first!
    user = get_user(page.user_id)

# GOOD: Each test is independent
def test_01_create_and_get():
    user_id = create_user()
    user = get_user(user_id)
    assert user is not None

# GOOD: Use fixtures for setup
@pytest.fixture
def authenticated_page():
    page = setup_authenticated_page()
    yield page
    cleanup(page)

def test_protected_endpoint(authenticated_page):
    response = authenticated_page.get("/api/protected")
    assert response.ok
""")


def example_cleanup_strategy():
    """Example: Different cleanup strategies.

    When to clean up and how.
    """
    print("\n=== Cleanup Strategy Example ===\n")

    print("""
# Strategy 1: Cleanup in teardown (always runs)
class MyPage(BasePage):
    def teardown(self):
        # Clean up created resources
        for resource_id in self.created_resources:
            try:
                self.delete(f"/api/{resource_id}")
            except:
                pass
        super().teardown()

# Strategy 2: Explicit cleanup function
def cleanup_test_data(page, resource_ids):
    for resource_id in resource_ids:
        page.delete(f"/api/{resource_id}")

def test_create_and_cleanup():
    resource_ids = []
    try:
        response = page.post("/api/items", json={...})
        resource_ids.append(response.json()["id"])
    finally:
        cleanup_test_data(page, resource_ids)

# Strategy 3: Use a cleanup test module
# Create 99_cleanup.py that runs last and cleans up
""")


if __name__ == "__main__":
    print("=" * 60)
    print("Test Fixtures Examples")
    print("=" * 60)

    try:
        example_page_attributes()
    except Exception as e:
        print(f"Error: {e}")

    try:
        example_setup_method()
    except Exception as e:
        print(f"Error: {e}")

    try:
        example_teardown_cleanup()
    except Exception as e:
        print(f"Error: {e}")

    try:
        example_pytest_fixtures()
    except Exception as e:
        print(f"Error: {e}")

    try:
        example_state_sharing()
    except Exception as e:
        print(f"Error: {e}")

    try:
        example_test_isolation()
    except Exception as e:
        print(f"Error: {e}")

    try:
        example_cleanup_strategy()
    except Exception as e:
        print(f"Error: {e}")

    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)
