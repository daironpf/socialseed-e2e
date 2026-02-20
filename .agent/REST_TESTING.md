# REST API Testing Guide

This guide covers testing REST APIs with socialseed-e2e.

---

## Basic REST Testing

### Creating a REST Service

```bash
e2e new-service my-api
```

### Configuration

Edit `e2e.conf`:

```yaml
services:
  my-api:
    base_url: http://localhost:8080
    timeout: 30
    headers:
      Content-Type: application/json

    endpoints:
      - /api/users
      - /api/users/{id}
      - /api/auth/login
```

---

## Test Examples

### GET Request

```python
# services/my-api/modules/01_get_users.py
from socialseed_e2e.core.base_page import BasePage


def run(page: BasePage) -> dict:
    response = page.get("/api/users")
    
    assert response.status == 200
    assert len(response.json()) > 0
    
    return response
```

### POST Request

```python
# services/my-api/modules/02_create_user.py
from socialseed_e2e.core.base_page import BasePage


def run(page: BasePage) -> dict:
    payload = {
        "name": "Test User",
        "email": "test@example.com"
    }
    
    response = page.post("/api/users", json=payload)
    
    assert response.status == 201
    assert response.json()["email"] == "test@example.com"
    
    # Store user ID for next test
    page.created_user_id = response.json()["id"]
    
    return response
```

### PUT Request

```python
# services/my-api/modules/03_update_user.py
from socialseed_e2e.core.base_page import BasePage


def run(page: BasePage) -> dict:
    user_id = getattr(page, "created_user_id", None)
    
    if not user_id:
        return {"skipped": "No user created"}
    
    payload = {"name": "Updated Name"}
    
    response = page.put(f"/api/users/{user_id}", json=payload)
    
    assert response.status == 200
    assert response.json()["name"] == "Updated Name"
    
    return response
```

### DELETE Request

```python
# services/my-api/modules/04_delete_user.py
from socialseed_e2e.core.base_page import BasePage


def run(page: BasePage) -> dict:
    user_id = getattr(page, "created_user_id", None)
    
    if not user_id:
        return {"skipped": "No user created"}
    
    response = page.delete(f"/api/users/{user_id}")
    
    assert response.status == 204
    
    return response
```

---

## Authentication

### Bearer Token

```python
def run(page: BasePage) -> dict:
    # Login
    login_response = page.post("/api/auth/login", json={
        "username": "testuser",
        "password": "testpass"
    })
    
    token = login_response.json()["token"]
    
    # Set auth header
    page.headers["Authorization"] = f"Bearer {token}"
    
    # Make authenticated request
    response = page.get("/api/protected")
    
    assert response.status == 200
    
    return response
```

### API Key

```python
def run(page: BasePage) -> dict:
    page.headers["X-API-Key"] = "your-api-key"
    
    response = page.get("/api/data")
    
    return response
```

---

## Assertions

### Status Codes

```python
assert response.status == 200
assert response.status in [200, 201, 204]
```

### JSON Body

```python
data = response.json()
assert data["id"] == 1
assert "name" in data
assert data["tags"][0] == "important"
```

### Headers

```python
assert response.headers["content-type"].startswith("application/json")
```

---

## Error Handling

```python
def run(page: BasePage) -> dict:
    response = page.get("/api/nonexistent")
    
    if response.status >= 400:
        error = response.json()
        assert "message" in error
        return {"error": error}
    
    return response
```

---

## Running Tests

```bash
# Run all tests
e2e run

# Run specific service
e2e run --service my-api

# Run with report
e2e run --report html

# Run verbose
e2e run --verbose
```
