"""Environment Variables Examples.

This module demonstrates how to use environment variables in SocialSeed E2E.

Requirements:
    pip install python-dotenv

Run this example:
    python examples/advanced_usage/env_variables_example.py
"""

import os
from pathlib import Path
from typing import Dict, Optional
from playwright.sync_api import APIResponse, sync_playwright

from socialseed_e2e.core.base_page import BasePage


def load_env_file(env_path: str = ".env") -> Dict[str, str]:
    """Load environment variables from a .env file.

    Args:
        env_path: Path to the .env file

    Returns:
        Dictionary of environment variables
    """
    env_vars = {}
    path = Path(env_path)

    if path.exists():
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, value = line.split("=", 1)
                        env_vars[key.strip()] = value.strip()

    return env_vars


def example_env_file_loading():
    """Example: Loading environment variables from .env file.

    This shows how to read a .env file manually without python-dotenv.
    """
    print("\n=== Environment File Loading Example ===\n")

    # Create a sample .env file
    sample_env = """
# API Configuration
API_BASE_URL=http://localhost:8765
API_USERNAME=admin
API_PASSWORD=admin123

# Feature Flags  
ENABLE_LOGGING=true
MAX_RETRIES=3

# Environment
ENVIRONMENT=development
"""

    # Write sample .env
    with open(".env.example", "w") as f:
        f.write(sample_env)

    # Load it
    env_vars = load_env_file(".env.example")

    print("Loaded environment variables:")
    for key, value in env_vars.items():
        print(f"  {key} = {value}")

    # Use in your tests
    base_url = env_vars.get("API_BASE_URL", "http://localhost:8080")
    print(f"\nUsing base URL: {base_url}")

    # Clean up
    os.remove(".env.example")


def example_env_with_dotenv():
    """Example: Using python-dotenv for environment variables.

    This is the recommended approach using the python-dotenv library.

    Requirements:
        pip install python-dotenv
    """
    print("\n=== python-dotenv Example ===\n")

    try:
        from dotenv import load_dotenv, dotenv_values

        # Create a sample .env file
        sample_env = """API_BASE_URL=http://localhost:8765
API_KEY=secret-key-12345
DATABASE_URL=postgresql://localhost:5432/testdb
SECRET_KEY=my-secret-key
DEBUG=true
"""
        with open(".env.test", "w") as f:
            f.write(sample_env)

        # Load environment variables from .env file
        load_dotenv(".env.test")

        # Access variables
        api_base_url = os.getenv("API_BASE_URL")
        api_key = os.getenv("API_KEY")
        debug = os.getenv("DEBUG", "false")

        print(f"API_BASE_URL: {api_base_url}")
        print(f"API_KEY: {api_key}")
        print(f"DEBUG: {debug}")

        # Alternative: Get all values as dict
        config = dotenv_values(".env.test")
        print(f"\nAll config: {dict(config)}")

        # Clean up
        os.remove(".env.test")

        print("\n✓ python-dotenv loaded successfully!")

    except ImportError:
        print("python-dotenv not installed. Install with: pip install python-dotenv")


def example_environment_specific_config():
    """Example: Different configuration per environment.

    Common pattern: dev, staging, production have different configs.
    """
    print("\n=== Environment-Specific Configuration Example ===\n")

    # Simulate different environments
    environments = {
        "development": {
            "base_url": "http://localhost:8765",
            "debug": True,
            "timeout": 30000,
        },
        "staging": {
            "base_url": "https://staging-api.example.com",
            "debug": True,
            "timeout": 15000,
        },
        "production": {
            "base_url": "https://api.example.com",
            "debug": False,
            "timeout": 10000,
        },
    }

    # Get current environment (default to development)
    env = os.getenv("APP_ENV", "development")
    config = environments.get(env, environments["development"])

    print(f"Current environment: {env}")
    print(f"Configuration: {config}")

    # Use in page initialization
    base_url = config["base_url"]
    print(f"\nInitializing page with: {base_url}")


def example_secrets_management():
    """Example: Managing secrets in tests.

    IMPORTANT: Never commit secrets to version control!
    Use environment variables or secret management tools.
    """
    print("\n=== Secrets Management Example ===\n")

    # Set environment variables (in real tests, these come from CI/CD)
    os.environ["API_TOKEN"] = "test-token-12345"
    os.environ["ADMIN_PASSWORD"] = "secret-admin-pass"

    # Access secrets
    api_token = os.environ.get("API_TOKEN")
    admin_password = os.environ.get("ADMIN_PASSWORD")

    print(f"API Token loaded: {'Yes' if api_token else 'No'}")
    print(f"Admin Password loaded: {'Yes' if admin_password else 'No'}")

    # Use in requests
    with sync_playwright() as p:
        page = BasePage(base_url="http://localhost:8765", playwright=p)
        page.setup()

        headers = {"Authorization": f"Bearer {api_token}"}
        response = page.get("/api/protected", headers=headers)

        print(f"Request with token: {response.status}")

        page.teardown()

    # Clean up
    del os.environ["API_TOKEN"]
    del os.environ["ADMIN_PASSWORD"]


def example_env_in_service_page():
    """Example: Using environment variables in a service page.

    This pattern allows for flexible configuration without code changes.
    """
    print("\n=== Service Page with Environment Variables ===\n")

    # Set test environment variables
    os.environ["BASE_URL"] = "http://localhost:8765"
    os.environ["API_VERSION"] = "v1"

    class ConfiguredPage(BasePage):
        """Service page that reads configuration from environment."""

        def __init__(self, **kwargs):
            # Read from environment
            base_url = os.getenv("BASE_URL", "http://localhost:8080")
            api_version = os.getenv("API_VERSION", "v1")

            super().__init__(base_url=base_url, **kwargs)
            self.api_version = api_version

        def get_users_v1(self) -> APIResponse:
            """Get users using configured API version."""
            return self.get(f"/{self.api_version}/users")

        def get_users_default(self) -> APIResponse:
            """Get users using default endpoint."""
            return self.get("/api/users")

    with sync_playwright() as p:
        page = ConfiguredPage(playwright=p)
        page.setup()

        print(f"Base URL: {page.base_url}")
        print(f"API Version: {page.api_version}")

        # Test both endpoints
        response1 = page.get_users_v1()
        response2 = page.get_users_default()

        print(f"v1 endpoint: {response1.status}")
        print(f"Default endpoint: {response2.status}")

        page.teardown()

    # Clean up
    del os.environ["BASE_URL"]
    del os.environ["API_VERSION"]


def example_test_data_from_env():
    """Example: Loading test data from environment.

    Useful for parameterized tests with external data.
    """
    print("\n=== Test Data from Environment ===\n")

    # Simulate test data via environment
    os.environ["TEST_USER_EMAIL"] = "test@example.com"
    os.environ["TEST_USER_NAME"] = "Test User"
    os.environ["TEST_USER_COUNT"] = "5"

    # Load test data
    test_users = []
    for i in range(int(os.environ.get("TEST_USER_COUNT", "1"))):
        test_users.append(
            {
                "email": os.getenv("TEST_USER_EMAIL", f"test{i}@example.com"),
                "name": os.environ.get("TEST_USER_NAME", "Test User"),
            }
        )

    print(f"Loaded {len(test_users)} test users:")
    for i, user in enumerate(test_users):
        print(f"  {i + 1}. {user['email']} - {user['name']}")

    # Clean up
    del os.environ["TEST_USER_EMAIL"]
    del os.environ["TEST_USER_NAME"]
    del os.environ["TEST_USER_COUNT"]


if __name__ == "__main__":
    print("=" * 60)
    print("Environment Variables Examples")
    print("=" * 60)

    try:
        example_env_file_loading()
    except Exception as e:
        print(f"Error: {e}")

    try:
        example_env_with_dotenv()
    except Exception as e:
        print(f"Error: {e}")

    try:
        example_environment_specific_config()
    except Exception as e:
        print(f"Error: {e}")

    try:
        example_secrets_management()
    except Exception as e:
        print(f"Error: {e}")

    try:
        example_env_in_service_page()
    except Exception as e:
        print(f"Error: {e}")

    try:
        example_test_data_from_env()
    except Exception as e:
        print(f"Error: {e}")

    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)
