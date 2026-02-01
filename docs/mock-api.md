# Mock API for Integration Testing

The **Mock Flask API** provides a lightweight, self-contained REST API for integration testing. It's perfect for testing the socialseed-e2e framework itself or as a reference implementation when building your own tests.

## Overview

The mock API simulates a real-world REST API with:
- Health check endpoint
- Complete user CRUD operations
- Authentication system (login/register)
- In-memory data storage with seed data
- Pagination and search capabilities
- Proper HTTP status codes and error handling

## Quick Start

### Running the Mock API

#### Option 1: Direct Execution (for manual testing)

```bash
# From project root
python tests/fixtures/mock_api.py
```

Output:
```
🚀 Starting Mock API Server...
📍 URL: http://localhost:8765
📖 Endpoints:
   GET    /health
   GET    /api/users
   POST   /api/users
   GET    /api/users/{id}
   PUT    /api/users/{id}
   DELETE /api/users/{id}
   POST   /api/auth/login
   POST   /api/auth/register

Press Ctrl+C to stop
```

#### Option 2: As Pytest Fixture (for automated tests)

```python
import requests

def test_api(mock_api_url):
    """Test using the mock API fixture."""
    response = requests.get(f"{mock_api_url}/health")
    assert response.status_code == 200
```

## Available Endpoints

### Health Check

```
GET /health
```

Returns server status and timestamp.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-31T12:00:00",
  "service": "mock-api",
  "version": "1.0.0"
}
```

### Users CRUD

#### List Users
```
GET /api/users?page=1&limit=10&search=keyword
```

Query parameters:
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 10)
- `search`: Search in name or email (optional)

**Response:**
```json
{
  "items": [...],
  "total": 2,
  "page": 1,
  "limit": 10,
  "total_pages": 1
}
```

#### Create User
```
POST /api/users
```

**Request body:**
```json
{
  "email": "user@example.com",
  "password": "secret123",
  "name": "John Doe",
  "role": "user"
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid-here",
  "email": "user@example.com",
  "name": "John Doe",
  "role": "user",
  "created_at": "...",
  "updated_at": "..."
}
```

#### Get User
```
GET /api/users/{id}
```

**Response:** `200 OK` or `404 Not Found`

#### Update User
```
PUT /api/users/{id}
```

**Request body:**
```json
{
  "name": "Updated Name",
  "email": "new@example.com",
  "role": "admin"
}
```

**Response:** `200 OK`

#### Delete User
```
DELETE /api/users/{id}
```

**Response:** `204 No Content`

### Authentication

#### Login
```
POST /api/auth/login
```

**Request body:**
```json
{
  "email": "admin@example.com",
  "password": "admin123"
}
```

**Response:**
```json
{
  "token": "auth-token-here",
  "user": {...}
}
```

#### Register
```
POST /api/auth/register
```

**Request body:**
```json
{
  "email": "new@example.com",
  "password": "secret123",
  "name": "New User"
}
```

**Response:** `201 Created`
```json
{
  "token": "auth-token-here",
  "user": {...}
}
```

## Seeded Data

The mock API comes with 2 pre-configured users:

| Email | Password | Role | Purpose |
|-------|----------|------|---------|
| admin@example.com | admin123 | admin | Admin testing |
| user@example.com | user123 | user | Regular user testing |

## Pytest Fixtures

### Available Fixtures

#### `mock_api_server`
Session-scoped fixture that starts the mock API in a background thread.

```python
def test_with_server(mock_api_server):
    url = mock_api_server.get_base_url()
    # Server is already running
```

#### `mock_api_url`
Convenience fixture providing the base URL string.

```python
def test_with_url(mock_api_url):
    response = requests.get(f"{mock_api_url}/health")
```

#### `mock_api_reset`
Function-scoped fixture that resets data before each test.

```python
def test_with_clean_data(mock_api_url, mock_api_reset):
    # API is reset to initial state with 2 seeded users
    response = requests.get(f"{mock_api_url}/api/users")
    assert response.json()['total'] == 2
```

#### `sample_user_data`
Provides sample user data for testing.

```python
def test_create(mock_api_url, sample_user_data):
    response = requests.post(
        f"{mock_api_url}/api/users",
        json=sample_user_data
    )
    assert response.status_code == 201
```

#### `admin_credentials` / `user_credentials`
Pre-configured credentials for seeded users.

```python
def test_login(mock_api_url, admin_credentials):
    response = requests.post(
        f"{mock_api_url}/api/auth/login",
        json=admin_credentials
    )
    assert response.status_code == 200
```

### Fixture Scopes

| Fixture | Scope | Description |
|---------|-------|-------------|
| `mock_api_server` | session | Server runs once for all tests |
| `mock_api_url` | session | URL string from server |
| `mock_api_reset` | function | Resets data before each test |
| `sample_user_data` | function | Fresh sample data each test |
| `admin_credentials` | function | Admin credentials |
| `user_credentials` | function | User credentials |

## For AI Agents

### Understanding the Architecture

```
tests/
├── fixtures/
│   └── mock_api.py          # MockAPIServer class
├── conftest.py              # Pytest fixtures
└── integration/
    └── test_mock_api_integration.py  # Example tests
```

### Key Classes

#### `MockAPIServer`

The main server class that wraps Flask:

```python
from tests.fixtures.mock_api import MockAPIServer

# Create instance
server = MockAPIServer(port=8765)

# Access data
print(server.users)           # Dict of users
print(server.auth_tokens)     # Dict of active tokens

# Control server
server.run(debug=True)        # Blocking
server.reset()                # Reset to initial state
url = server.get_base_url()   # Get "http://localhost:8765"
```

### Writing Tests with Mock API

#### Pattern 1: Simple API Test

```python
import requests

def test_health_check(mock_api_url):
    """Basic health check test."""
    response = requests.get(f"{mock_api_url}/health")
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'healthy'
```

#### Pattern 2: CRUD Operations Test

```python
def test_user_lifecycle(mock_api_url, mock_api_reset):
    """Test complete user CRUD with clean state."""
    # Create
    create_resp = requests.post(
        f"{mock_api_url}/api/users",
        json={"email": "test@test.com", "password": "pass", "name": "Test"}
    )
    assert create_resp.status_code == 201
    user_id = create_resp.json()['id']
    
    # Read
    get_resp = requests.get(f"{mock_api_url}/api/users/{user_id}")
    assert get_resp.status_code == 200
    
    # Update
    update_resp = requests.put(
        f"{mock_api_url}/api/users/{user_id}",
        json={"name": "Updated"}
    )
    assert update_resp.json()['name'] == "Updated"
    
    # Delete
    delete_resp = requests.delete(f"{mock_api_url}/api/users/{user_id}")
    assert delete_resp.status_code == 204
```

#### Pattern 3: Authentication Flow

```python
def test_auth_flow(mock_api_url, mock_api_reset):
    """Test registration and login flow."""
    # Register new user
    register_resp = requests.post(
        f"{mock_api_url}/api/auth/register",
        json={"email": "new@test.com", "password": "pass", "name": "New"}
    )
    assert register_resp.status_code == 201
    token = register_resp.json()['token']
    
    # Login with same credentials
    login_resp = requests.post(
        f"{mock_api_url}/api/auth/login",
        json={"email": "new@test.com", "password": "pass"}
    )
    assert login_resp.status_code == 200
    assert 'token' in login_resp.json()
```

### Best Practices for AI Agents

1. **Always use `mock_api_reset`** for tests that modify data
   - Ensures tests don't interfere with each other
   - Provides predictable initial state

2. **Use seeded credentials** for authentication tests
   - `admin_credentials` and `user_credentials` fixtures
   - Avoid creating users just to test login

3. **Test error cases**
   - 404 for missing resources
   - 400 for invalid input
   - 409 for duplicates
   - 401 for invalid auth

4. **Verify response structure**
   - Check status codes
   - Verify JSON structure
   - Ensure passwords are NOT returned

### Example: Complete Test Suite

```python
import requests
import pytest

class TestUserAPI:
    """Comprehensive tests for user endpoints."""
    
    def test_list_users_pagination(self, mock_api_url):
        """Test pagination works correctly."""
        resp = requests.get(f"{mock_api_url}/api/users?limit=1")
        data = resp.json()
        assert len(data['items']) == 1
        assert data['total_pages'] >= 2
    
    def test_search_users(self, mock_api_url):
        """Test search functionality."""
        resp = requests.get(f"{mock_api_url}/api/users?search=admin")
        data = resp.json()
        assert all('admin' in u['email'] for u in data['items'])
    
    def test_create_duplicate_fails(self, mock_api_url):
        """Test duplicate email returns 409."""
        resp = requests.post(
            f"{mock_api_url}/api/users",
            json={"email": "admin@example.com", "password": "x", "name": "X"}
        )
        assert resp.status_code == 409
```

## Troubleshooting

### Port Already in Use

If port 8765 is occupied:

```python
# Use different port
server = MockAPIServer(port=9999)
```

### Server Not Starting in Tests

The fixture has built-in retry logic (30 retries, 0.1s delay). If it fails:

```python
# Check if something else is using port 8765
lsof -i :8765

# Or modify the port in conftest.py
server = MockAPIServer(port=9999)  # Change port
```

### Data Persistence Between Tests

By default, data persists between tests for performance. Use `mock_api_reset` to clean:

```python
def test_with_reset(mock_api_url, mock_api_reset):
    # Data is fresh for this test
    pass

def test_without_reset(mock_api_url):
    # Data persists from previous tests
    pass
```

## Advanced Usage

### Customizing Seed Data

Edit `tests/fixtures/mock_api.py`:

```python
def _seed_data(self) -> None:
    """Override with your own seed data."""
    self.users = {
        "custom-id": {
            "id": "custom-id",
            "email": "custom@example.com",
            "password": "custompass",
            "name": "Custom User",
            "role": "user",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
    }
```

### Adding Custom Endpoints

Extend the MockAPIServer class:

```python
class CustomMockAPI(MockAPIServer):
    def _register_routes(self):
        super()._register_routes()
        
        @self.app.route('/api/custom', methods=['GET'])
        def custom_endpoint():
            return jsonify({"custom": "data"})
```

## See Also

- [Writing Tests](writing-tests.md) - General test writing guide
- [API Reference](api-reference.md) - Framework API documentation
- `tests/integration/test_mock_api_integration.py` - Example tests
