# Mock API for Integration Testing

Flask-based mock REST API for testing the socialseed-e2e framework without requiring external services.

## 🚀 Quick Start

### Start the Mock API Server

**Option 1: Run directly**
```bash
python tests/fixtures/mock_api.py
```

**Option 2: Use as pytest fixture**
```python
def test_with_mock_api(mock_api_url):
    response = requests.get(f"{mock_api_url}/health")
    assert response.status_code == 200
```

## 📡 Endpoints

### Health Check
```http
GET /health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-31T20:00:00",
  "service": "mock-api",
  "version": "1.0.0"
}
```

### Users API

#### List Users
```http
GET /api/users
GET /api/users?page=1&limit=10&search=john
```

Response:
```json
{
  "items": [
    {
      "id": "uuid",
      "email": "user@example.com",
      "name": "Test User",
      "role": "user",
      "created_at": "2025-01-31T20:00:00",
      "updated_at": "2025-01-31T20:00:00"
    }
  ],
  "total": 2,
  "page": 1,
  "limit": 10,
  "total_pages": 1
}
```

#### Create User
```http
POST /api/users
Content-Type: application/json

{
  "email": "new@example.com",
  "password": "password123",
  "name": "New User",
  "role": "user"
}
```

Response: `201 Created`
```json
{
  "id": "uuid",
  "email": "new@example.com",
  "name": "New User",
  "role": "user",
  "created_at": "2025-01-31T20:00:00",
  "updated_at": "2025-01-31T20:00:00"
}
```

#### Get User
```http
GET /api/users/{id}
```

Response: `200 OK` or `404 Not Found`

#### Update User
```http
PUT /api/users/{id}
Content-Type: application/json

{
  "name": "Updated Name",
  "email": "newemail@example.com"
}
```

Response: `200 OK`

#### Delete User
```http
DELETE /api/users/{id}
```

Response: `204 No Content` or `404 Not Found`

### Authentication API

#### Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "admin@example.com",
  "password": "admin123"
}
```

Response: `200 OK`
```json
{
  "token": "auth-token-uuid",
  "user": {
    "id": "uuid",
    "email": "admin@example.com",
    "name": "Admin User",
    "role": "admin"
  }
}
```

#### Register
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "newuser@example.com",
  "password": "securepass",
  "name": "New User"
}
```

Response: `201 Created`

## 🧪 Usage in Tests

### Using Fixtures

```python
import requests

def test_health_check(mock_api_url):
    """Test health endpoint."""
    response = requests.get(f"{mock_api_url}/health")
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'healthy'


def test_create_user(mock_api_url, mock_api_reset, sample_user_data):
    """Test creating a user with fresh data."""
    # mock_api_reset ensures clean state
    response = requests.post(
        f"{mock_api_url}/api/users",
        json=sample_user_data
    )
    assert response.status_code == 201
    data = response.json()
    assert data['email'] == sample_user_data['email']


def test_login(mock_api_url, admin_credentials):
    """Test login with admin credentials."""
    response = requests.post(
        f"{mock_api_url}/api/auth/login",
        json=admin_credentials
    )
    assert response.status_code == 200
    data = response.json()
    assert 'token' in data
    assert data['user']['role'] == 'admin'
```

### Using with socialseed-e2e

Create an e2e service for the mock API:

```bash
e2e new-service mock-api --base-url http://localhost:8765
```

Update `e2e.conf`:
```yaml
services:
  mock-api:
    name: mock-api
    base_url: http://localhost:8765
    health_endpoint: /health
    timeout: 5000
    required: true
```

Create a test module:
```python
# services/mock-api/modules/01_test_health.py
def run(mock_api):
    response = mock_api.get("/health")
    mock_api.assert_ok(response)
    data = mock_api.assert_json(response)
    assert data['status'] == 'healthy'
```

## 🔧 Available Fixtures

### `mock_api_server`
Session-scoped fixture providing the `MockAPIServer` instance.

```python
def test_something(mock_api_server):
    # Server is already running
    url = mock_api_server.get_base_url()
    # ... perform tests
```

### `mock_api_url`
Session-scoped fixture providing the base URL string.

```python
def test_something(mock_api_url):
    # mock_api_url = "http://localhost:8765"
    response = requests.get(f"{mock_api_url}/health")
```

### `mock_api_reset`
Function-scoped fixture that resets data before each test.

```python
def test_with_clean_data(mock_api_url, mock_api_reset):
    # Data is reset to initial seeded state
    response = requests.get(f"{mock_api_url}/api/users")
    data = response.json()
    assert data['total'] == 2  # Initial seeded users
```

### `sample_user_data`
Provides sample user data for testing.

```python
def test_create(mock_api_url, sample_user_data):
    response = requests.post(
        f"{mock_api_url}/api/users",
        json=sample_user_data
    )
```

### `admin_credentials` / `user_credentials`
Pre-configured credentials for seeded users.

```python
def test_admin_login(mock_api_url, admin_credentials):
    response = requests.post(
        f"{mock_api_url}/api/auth/login",
        json=admin_credentials
    )
    assert response.status_code == 200
```

## 📊 Seeded Data

The mock API comes with 2 pre-configured users:

**Admin User:**
- Email: `admin@example.com`
- Password: `admin123`
- Role: `admin`

**Regular User:**
- Email: `user@example.com`
- Password: `user123`
- Role: `user`

## 🔌 Server Management

### Start Server Manually

```python
from tests.fixtures.mock_api import MockAPIServer

server = MockAPIServer(port=8765)
server.run(debug=True)
```

### Reset Data

```python
# Reset to initial seeded state
server.reset()
```

### Custom Usage

```python
from tests.fixtures.mock_api import get_mock_api_server

# Get or create global instance
server = get_mock_api_server(port=8765)

# Access data directly
print(f"Users: {len(server.users)}")
print(f"Active tokens: {len(server.auth_tokens)}")
```

## 🧩 Integration with CI/CD

Use the mock API in GitHub Actions:

```yaml
jobs:
  test:
    steps:
      - name: Start Mock API
        run: |
          python tests/fixtures/mock_api.py &
          sleep 2

      - name: Run Tests
        run: pytest tests/integration/
```

## 📚 Examples

See `tests/integration/` for complete examples of integration tests using the mock API.
