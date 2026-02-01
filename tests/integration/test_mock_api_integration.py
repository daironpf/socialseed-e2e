"""Example integration tests using the mock API.

These tests demonstrate how to use the mock Flask API for integration testing.
They serve as both tests and documentation for using the mock API fixtures.
"""

import requests


class TestMockAPIHealth:
    """Tests for the health check endpoint."""

    def test_health_endpoint_returns_200(self, mock_api_url):
        """Test that health endpoint returns HTTP 200."""
        response = requests.get(f"{mock_api_url}/health")
        assert response.status_code == 200

    def test_health_endpoint_returns_json(self, mock_api_url):
        """Test that health endpoint returns JSON."""
        response = requests.get(f"{mock_api_url}/health")
        data = response.json()
        assert 'status' in data
        assert data['status'] == 'healthy'

    def test_health_endpoint_has_timestamp(self, mock_api_url):
        """Test that health response includes timestamp."""
        response = requests.get(f"{mock_api_url}/health")
        data = response.json()
        assert 'timestamp' in data
        assert 'service' in data
        assert data['service'] == 'mock-api'


class TestMockAPIUsersCRUD:
    """Tests for user CRUD operations."""

    def test_list_users_returns_200(self, mock_api_url):
        """Test listing users returns HTTP 200."""
        response = requests.get(f"{mock_api_url}/api/users")
        assert response.status_code == 200

    def test_list_users_returns_paginated_data(self, mock_api_url):
        """Test that users are returned with pagination."""
        response = requests.get(f"{mock_api_url}/api/users")
        data = response.json()
        
        assert 'items' in data
        assert 'total' in data
        assert 'page' in data
        assert 'limit' in data
        assert 'total_pages' in data

    def test_list_users_has_seeded_data(self, mock_api_url):
        """Test that seeded users are present."""
        response = requests.get(f"{mock_api_url}/api/users")
        data = response.json()
        
        # Should have 2 seeded users (admin and user)
        assert data['total'] == 2
        emails = [u['email'] for u in data['items']]
        assert 'admin@example.com' in emails
        assert 'user@example.com' in emails

    def test_create_user_returns_201(self, mock_api_url, sample_user_data):
        """Test creating a user returns HTTP 201."""
        response = requests.post(
            f"{mock_api_url}/api/users",
            json=sample_user_data
        )
        assert response.status_code == 201

    def test_create_user_returns_user_data(self, mock_api_url, mock_api_reset, sample_user_data):
        """Test creating a user returns the created user."""
        response = requests.post(
            f"{mock_api_url}/api/users",
            json=sample_user_data
        )
        data = response.json()
        
        assert 'id' in data
        assert data['email'] == sample_user_data['email']
        assert data['name'] == sample_user_data['name']
        assert 'password' not in data  # Password should not be in response

    def test_get_user_by_id(self, mock_api_url):
        """Test getting a specific user by ID."""
        # First, get list of users to find an ID
        list_response = requests.get(f"{mock_api_url}/api/users")
        users = list_response.json()['items']
        user_id = users[0]['id']
        
        # Get specific user
        response = requests.get(f"{mock_api_url}/api/users/{user_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data['id'] == user_id

    def test_get_nonexistent_user_returns_404(self, mock_api_url):
        """Test that getting a non-existent user returns 404."""
        response = requests.get(f"{mock_api_url}/api/users/nonexistent-id")
        assert response.status_code == 404

    def test_update_user(self, mock_api_url):
        """Test updating a user."""
        # Get a user to update
        list_response = requests.get(f"{mock_api_url}/api/users")
        users = list_response.json()['items']
        user_id = users[0]['id']
        
        # Update the user
        update_data = {"name": "Updated Name"}
        response = requests.put(
            f"{mock_api_url}/api/users/{user_id}",
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['name'] == "Updated Name"

    def test_delete_user(self, mock_api_url, mock_api_reset):
        """Test deleting a user."""
        # Create a user to delete
        new_user = {
            "email": "delete.me@example.com",
            "password": "password123",
            "name": "To Delete"
        }
        create_response = requests.post(
            f"{mock_api_url}/api/users",
            json=new_user
        )
        user_id = create_response.json()['id']
        
        # Delete the user
        delete_response = requests.delete(f"{mock_api_url}/api/users/{user_id}")
        assert delete_response.status_code == 204
        
        # Verify user is gone
        get_response = requests.get(f"{mock_api_url}/api/users/{user_id}")
        assert get_response.status_code == 404

    def test_user_pagination(self, mock_api_url, mock_api_reset):
        """Test pagination of users."""
        # Create several users
        for i in range(5):
            requests.post(
                f"{mock_api_url}/api/users",
                json={
                    "email": f"user{i}@test.com",
                    "password": "pass123",
                    "name": f"User {i}"
                }
            )
        
        # Test with limit=2
        response = requests.get(f"{mock_api_url}/api/users?limit=2")
        data = response.json()
        
        assert len(data['items']) == 2
        assert data['total'] == 7  # 2 seeded + 5 created
        assert data['total_pages'] == 4

    def test_user_search(self, mock_api_url):
        """Test searching users."""
        response = requests.get(f"{mock_api_url}/api/users?search=admin")
        data = response.json()
        
        assert data['total'] >= 1
        assert all('admin' in u['email'] or 'admin' in u['name'].lower() 
                   for u in data['items'])


class TestMockAPIAuthentication:
    """Tests for authentication endpoints."""

    def test_login_with_valid_credentials(self, mock_api_url, admin_credentials):
        """Test login with valid admin credentials."""
        response = requests.post(
            f"{mock_api_url}/api/auth/login",
            json=admin_credentials
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'token' in data
        assert 'user' in data
        assert data['user']['email'] == admin_credentials['email']

    def test_login_with_invalid_credentials(self, mock_api_url):
        """Test login with invalid credentials."""
        response = requests.post(
            f"{mock_api_url}/api/auth/login",
            json={"email": "wrong@example.com", "password": "wrongpass"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert 'error' in data

    def test_login_requires_email_and_password(self, mock_api_url):
        """Test that login requires both email and password."""
        response = requests.post(
            f"{mock_api_url}/api/auth/login",
            json={"email": "test@example.com"}  # Missing password
        )
        
        assert response.status_code == 400

    def test_register_new_user(self, mock_api_url, mock_api_reset):
        """Test registering a new user."""
        new_user = {
            "email": "new.registered@example.com",
            "password": "newpass123",
            "name": "New Registered User"
        }
        
        response = requests.post(
            f"{mock_api_url}/api/auth/register",
            json=new_user
        )
        
        assert response.status_code == 201
        data = response.json()
        assert 'token' in data
        assert 'user' in data
        assert data['user']['email'] == new_user['email']

    def test_register_duplicate_email_fails(self, mock_api_url):
        """Test that registering with duplicate email fails."""
        # Try to register with existing admin email
        response = requests.post(
            f"{mock_api_url}/api/auth/register",
            json={
                "email": "admin@example.com",  # Already exists
                "password": "password",
                "name": "Duplicate"
            }
        )
        
        assert response.status_code == 409
        data = response.json()
        assert 'error' in data


class TestMockAPIErrorHandling:
    """Tests for API error handling."""

    def test_create_user_missing_required_fields(self, mock_api_url):
        """Test creating user without required fields."""
        response = requests.post(
            f"{mock_api_url}/api/users",
            json={"email": "test@example.com"}  # Missing password and name
        )
        
        assert response.status_code == 400

    def test_create_user_duplicate_email(self, mock_api_url):
        """Test creating user with duplicate email."""
        response = requests.post(
            f"{mock_api_url}/api/users",
            json={
                "email": "admin@example.com",  # Already exists
                "password": "pass",
                "name": "Duplicate"
            }
        )
        
        assert response.status_code == 409

    def test_update_nonexistent_user(self, mock_api_url):
        """Test updating a non-existent user."""
        response = requests.put(
            f"{mock_api_url}/api/users/nonexistent",
            json={"name": "New Name"}
        )
        
        assert response.status_code == 404

    def test_invalid_json_body(self, mock_api_url):
        """Test endpoints with invalid JSON."""
        response = requests.post(
            f"{mock_api_url}/api/users",
            data="not valid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code in [400, 500]  # Should fail
