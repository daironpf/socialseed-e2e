"""Pytest fixtures for integration testing with mock API.

This module provides pytest fixtures for integration testing with the mock Flask API.
Fixtures handle server lifecycle automatically - starting before tests and stopping after.

Usage:
    def test_something(mock_api_url, mock_api_server):
        # mock_api_url is the base URL (e.g., "http://localhost:8765")
        # mock_api_server is the MockAPIServer instance

        response = requests.get(f"{mock_api_url}/health")
        assert response.status_code == 200
"""

import threading
import time
from typing import Generator

import pytest
import requests

from tests.fixtures.mock_api import MockAPIServer


@pytest.fixture(scope="session")
def mock_api_server() -> Generator[MockAPIServer, None, None]:
    """Session-scoped fixture that provides a running mock API server.

    This fixture starts the mock API server in a background thread before
    any tests run, and stops it after all tests complete.

    Yields:
        MockAPIServer: The running mock API server instance

    Example:
        def test_health(mock_api_server):
            url = mock_api_server.get_base_url()
            response = requests.get(f"{url}/health")
            assert response.status_code == 200
    """
    server = MockAPIServer(port=8765)

    # Start server in background thread
    server_thread = threading.Thread(
        target=server.run, kwargs={"debug": False}, daemon=True
    )
    server_thread.start()

    # Wait for server to be ready
    max_retries = 30
    retry_delay = 0.1
    base_url = server.get_base_url()

    for i in range(max_retries):
        try:
            response = requests.get(f"{base_url}/health", timeout=1)
            if response.status_code == 200:
                break
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(retry_delay)
    else:
        raise RuntimeError(f"Mock API server failed to start at {base_url}")

    yield server

    # Cleanup: Stop the server gracefully
    try:
        server.stop()
    except Exception:
        pass  # Server may already be stopped


@pytest.fixture(scope="session")
def mock_api_url(mock_api_server) -> str:
    """Session-scoped fixture that provides the mock API base URL.

    This is a convenience fixture that returns the base URL string
    from the mock_api_server fixture.

    Args:
        mock_api_server: The mock API server fixture

    Returns:
        str: The base URL (e.g., "http://localhost:8765")

    Example:
        def test_users(mock_api_url):
            response = requests.get(f"{mock_api_url}/api/users")
            assert response.status_code == 200
    """
    return mock_api_server.get_base_url()


@pytest.fixture(scope="function")
def mock_api_reset(mock_api_server) -> None:
    """Function-scoped fixture that resets mock API data before each test.

    This fixture ensures each test starts with clean, seeded data.
    It resets the mock API to its initial state before each test function.

    Args:
        mock_api_server: The mock API server fixture

    Example:
        def test_create_user(mock_api_url, mock_api_reset):
            # API is reset to initial state with 2 seeded users
            response = requests.get(f"{mock_api_url}/api/users")
            data = response.json()
            assert data['total'] == 2  # Initial seeded users
    """
    mock_api_server.reset()
    yield


@pytest.fixture
def sample_user_data() -> dict:
    """Fixture providing sample user data for testing.

    Returns:
        dict: Sample user data with email, password, and name

    Example:
        def test_register(mock_api_url, sample_user_data):
            response = requests.post(
                f"{mock_api_url}/api/auth/register",
                json=sample_user_data
            )
            assert response.status_code == 201
    """
    return {
        "email": "newuser@example.com",
        "password": "securepassword123",
        "name": "New Test User",
    }


@pytest.fixture
def admin_credentials() -> dict:
    """Fixture providing admin user credentials for testing.

    These credentials match the seeded admin user in the mock API.

    Returns:
        dict: Admin credentials with email and password

    Example:
        def test_login(mock_api_url, admin_credentials):
            response = requests.post(
                f"{mock_api_url}/api/auth/login",
                json=admin_credentials
            )
            assert response.status_code == 200
            assert 'token' in response.json()
    """
    return {"email": "admin@example.com", "password": "admin123"}


@pytest.fixture
def user_credentials() -> dict:
    """Fixture providing regular user credentials for testing.

    These credentials match the seeded regular user in the mock API.

    Returns:
        dict: User credentials with email and password
    """
    return {"email": "user@example.com", "password": "user123"}
