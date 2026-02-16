"""Parameterized Tests Examples.

This module demonstrates how to run tests with multiple data sets
in SocialSeed E2E.

Run this example:
    python examples/advanced_usage/parameterized_tests_example.py
"""

import json
import uuid
from pathlib import Path
from typing import Any, Dict, List
from playwright.sync_api import APIResponse, sync_playwright

from socialseed_e2e.core.base_page import BasePage


class ParameterizedPage(BasePage):
    """Service page for parameterized testing."""

    def __init__(self, base_url: str = "http://localhost:8765", **kwargs):
        super().__init__(base_url=base_url, **kwargs)


def example_multiple_test_files():
    """Example: Using multiple test files for different data.

    The simplest approach: create separate test files for each scenario.
    """
    print("\n=== Multiple Test Files Example ===\n")

    print("""
# Approach: Create separate test modules
services/my-api/modules/
    01_create_user.py        # Test basic user creation
    02_create_admin.py       # Test admin user creation
    03_create_guest.py       # Test guest user creation
    04_create_with_special_chars.py  # Test edge cases

# Each file tests a different scenario
# Run specific tests:
e2e run --module 01_create_user
""")


def example_test_data_file():
    """Example: Loading test data from external files.

    Store test data in JSON/YAML files and load dynamically.
    """
    print("\n=== Test Data File Example ===\n")

    # Create sample test data file
    test_data = {
        "users": [
            {"email": "admin@test.com", "name": "Admin User", "role": "admin"},
            {"email": "user@test.com", "name": "Regular User", "role": "user"},
            {"email": "guest@test.com", "name": "Guest User", "role": "guest"},
        ],
        "items": [
            {"name": "Item 1", "price": 10.00},
            {"name": "Item 2", "price": 20.00},
            {"name": "Item 3", "price": 30.00},
        ],
    }

    # Save to file
    data_file = Path("test_data.json")
    with open(data_file, "w") as f:
        json.dump(test_data, f, indent=2)

    print(f"Created test data file: {data_file}")

    # Load in test
    with open(data_file) as f:
        loaded_data = json.load(f)

    print(f"Loaded {len(loaded_data['users'])} users:")
    for user in loaded_data["users"]:
        print(f"  - {user['name']} ({user['role']})")

    # Clean up
    data_file.unlink()


def example_iterate_over_data():
    """Example: Iterating over data in a single test.

    Run the same test logic with different data sets.
    """
    print("\n=== Iterate Over Data Example ===\n")

    test_cases = [
        {"email": f"user1_{uuid.uuid4().hex[:6]}@test.com", "name": "User 1"},
        {"email": f"user2_{uuid.uuid4().hex[:6]}@test.com", "name": "User 2"},
        {"email": f"user3_{uuid.uuid4().hex[:6]}@test.com", "name": "User 3"},
    ]

    with sync_playwright() as p:
        page = ParameterizedPage(base_url="http://localhost:8765", playwright=p)
        page.setup()

        results = []
        for i, test_data in enumerate(test_cases, 1):
            print(f"\nTest case {i}: {test_data['name']}")

            response = page.post("/api/users", json=test_data)

            result = {
                "case": i,
                "input": test_data,
                "status": response.status,
                "success": response.ok,
            }
            results.append(result)

            print(f"  Status: {response.status}")

        # Summary
        print(f"\n--- Summary ---")
        print(f"Total: {len(results)}")
        print(f"Passed: {sum(1 for r in results if r['success'])}")
        print(f"Failed: {sum(1 for r in results if not r['success'])}")

        page.teardown()


def example_pytest_parametrize():
    """Example: Using pytest parametrize decorator.

    For integration with pytest, use pytest.mark.parametrize.
    """
    print("\n=== Pytest Parametrize Example ===\n")

    print("""
# Install pytest: pip install pytest

# Example test with pytest parametrize:
# File: test_users.py

import pytest
from playwright.sync_api import APIResponse

# Parametrized test
@pytest.mark.parametrize("user_data", [
    {"email": "admin@test.com", "role": "admin"},
    {"email": "user@test.com", "role": "user"},
    {"email": "guest@test.com", "role": "guest"},
])
def test_create_user(page, user_data):
    \"\"\"Test creating users with different roles.\"\"\"
    response = page.post("/api/users", json=user_data)
    assert response.ok
    data = response.json()
    assert data["email"] == user_data["email"]


# Run with pytest:
# pytest test_users.py -v
# pytest test_users.py -v -k "admin"  # Run only admin tests


# Alternative: Custom parametrize decorator
def parametrize(*args, **kwargs):
    def decorator(func):
        return pytest.mark.parametrize(*args, **kwargs)(func)
    return decorator


# Or create custom test generator:
def generate_parametrized_tests(base_page_class):
    test_cases = [
        {"name": "test_admin", "email": "admin@test.com"},
        {"name": "test_user", "email": "user@test.com"},
    ]
    
    for case in test_cases:
        def test_fn(page, data=case):
            response = page.post("/api/users", json=data)
            assert response.ok
        
        test_fn.__name__ = case["name"]
        globals()[case["name"]] = test_fn
""")


def example_data_provider():
    """Example: Data provider pattern.

    Centralize test data in a provider class.
    """
    print("\n=== Data Provider Pattern Example ===\n")

    class TestDataProvider:
        """Centralized test data provider."""

        @staticmethod
        def get_valid_users():
            return [
                {"email": f"user{i}@test.com", "name": f"User {i}"} for i in range(1, 4)
            ]

        @staticmethod
        def get_invalid_users():
            return [
                {"email": "invalid", "name": "Bad Email"},  # Invalid email
                {"email": "", "name": "Empty Email"},  # Empty
            ]

        @staticmethod
        def get_edge_cases():
            return [
                {"email": "a@b.c", "name": "Short"},
                {
                    "email": "very_long_email@very_long_domain.very_long_tld",
                    "name": "Long Everything",
                },
                {"email": "user+tag@example.com", "name": "With Tag"},
                {"email": "user123@example.com", "name": "With Numbers"},
            ]

    # Use in tests
    provider = TestDataProvider()

    print("Valid users:")
    for user in provider.get_valid_users():
        print(f"  {user}")

    print("\nInvalid users:")
    for user in provider.get_invalid_users():
        print(f"  {user}")

    print("\nEdge cases:")
    for user in provider.get_edge_cases():
        print(f"  {user['name']}: {user['email']}")


def example_dynamic_test_generation():
    """Example: Dynamic test generation.

    Generate tests programmatically based on data.
    """
    print("\n=== Dynamic Test Generation Example ===\n")

    # Define test scenarios
    scenarios = [
        {
            "name": "happy_path",
            "data": {"email": "test@test.com", "name": "Test"},
            "expected_status": 200,
        },
        {
            "name": "missing_email",
            "data": {"name": "Test"},
            "expected_status": 400,
        },
        {
            "name": "invalid_email",
            "data": {"email": "not-an-email", "name": "Test"},
            "expected_status": 400,
        },
    ]

    # Generate test functions dynamically
    def create_test_function(scenario):
        def test_function():
            print(f"  Running: {scenario['name']}")
            # In real test, you'd make the API call here
            # response = page.post("/api/users", json=scenario["data"])
            # assert response.status == scenario["expected_status"]

        return test_function

    # Create test functions
    test_functions = {}
    for scenario in scenarios:
        fn = create_test_function(scenario)
        fn.__name__ = f"test_{scenario['name']}"
        test_functions[fn.__name__] = fn

    print("Generated tests:")
    for name, fn in test_functions.items():
        print(f"  - {name}()")

    # Run "tests"
    print("\nRunning tests:")
    for name, fn in test_functions.items():
        fn()


def example_csv_test_data():
    """Example: Loading test data from CSV.

    Useful for large data sets or data from other tools.
    """
    print("\n=== CSV Test Data Example ===\n")

    csv_content = """email,name,role,expected_status
admin@test.com,Admin User,admin,200
user@test.com,Regular User,user,200
guest@test.com,Guest User,guest,200
invalid,Bad Email,user,400
"""

    # Save CSV
    csv_file = Path("test_data.csv")
    with open(csv_file, "w") as f:
        f.write(csv_content)

    # Parse CSV
    import io

    data = []
    lines = csv_content.strip().split("\n")
    headers = lines[0].split(",")

    for line in lines[1:]:
        values = line.split(",")
        row = dict(zip(headers, values))
        data.append(row)

    print(f"Loaded {len(data)} test cases from CSV:")
    for row in data:
        print(f"  {row['email']} -> expected status: {row['expected_status']}")

    # Clean up
    csv_file.unlink()


if __name__ == "__main__":
    print("=" * 60)
    print("Parameterized Tests Examples")
    print("=" * 60)

    try:
        example_multiple_test_files()
    except Exception as e:
        print(f"Error: {e}")

    try:
        example_test_data_file()
    except Exception as e:
        print(f"Error: {e}")

    try:
        example_iterate_over_data()
    except Exception as e:
        print(f"Error: {e}")

    try:
        example_pytest_parametrize()
    except Exception as e:
        print(f"Error: {e}")

    try:
        example_data_provider()
    except Exception as e:
        print(f"Error: {e}")

    try:
        example_dynamic_test_generation()
    except Exception as e:
        print(f"Error: {e}")

    try:
        example_csv_test_data()
    except Exception as e:
        print(f"Error: {e}")

    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)
