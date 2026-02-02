# Writing Test Modules

Complete guide for writing test modules in socialseed-e2e.

## Overview

Test modules in socialseed-e2e are Python files that define individual test flows. Each module contains a `run()` function that executes a specific test scenario using a ServicePage object for API interactions.

## Test Module Structure

A test module follows a standard structure:

```
services/<service_name>/
├── __init__.py
├── <service_name>_page.py      # ServicePage class
├── data_schema.py               # Data models and constants
└── modules/                     # Test modules directory
    ├── 01_setup.py              # Setup/initialization tests
    ├── 02_authentication.py     # Auth flows
    ├── 03_core_feature.py       # Core functionality
    └── __init__.py
```

### File Naming Convention

- Use numeric prefixes for execution order: `01_`, `02_`, `03_`
- Use descriptive names: `01_login.py`, `02_create_user.py`, `03_update_profile.py`
- Tests execute in alphabetical order, so numeric prefixes ensure proper sequencing

## The run() Function

Every test module must define a `run()` function. This is the entry point that the test orchestrator calls.

### Basic Structure

```python
"""Test module for user login flow.

This module tests the user authentication flow.
"""

from playwright.sync_api import APIResponse
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..users_page import UsersPage


def run(users: 'UsersPage') -> APIResponse:
    """Execute user login test.

    This test validates that users can successfully log in
    with valid credentials.

    Args:
        users: Instance of UsersPage for API interactions

    Returns:
        APIResponse: HTTP response from the login endpoint

    Raises:
        AssertionError: If login fails or response is invalid
    """
    # Test implementation here
    pass
```

### Function Signature

The `run()` function must follow these conventions:

1. **Parameter**: Receives a ServicePage instance (type-hinted with forward reference)
2. **Return Type**: Returns `APIResponse` from Playwright
3. **Type Checking**: Use `TYPE_CHECKING` to avoid circular imports
4. **Documentation**: Include comprehensive docstring

### Example: Simple Test

```python
"""Test module for health check endpoint."""

from playwright.sync_api import APIResponse
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..myapi_page import MyapiPage


def run(myapi: 'MyapiPage') -> APIResponse:
    """Test health endpoint returns 200 OK."""
    response = myapi.get("/health")

    # Assert response is successful
    assert response.ok, f"Health check failed: {response.status}"

    # Verify response body
    data = response.json()
    assert data.get("status") == "healthy", "Service not healthy"

    return response
```

## ServicePage Usage

The ServicePage (inheriting from BasePage) provides HTTP methods and utilities for API testing.

### HTTP Methods

#### GET Request

```python
# Simple GET
response = users.get("/users")

# GET with query parameters
response = users.get("/users", params={"page": 1, "limit": 10})

# GET with custom headers
response = users.get("/users", headers={"X-Custom-Header": "value"})
```

#### POST Request

```python
# POST with JSON body
response = users.post("/users", json={
    "name": "John Doe",
    "email": "john@example.com"
})

# POST with form data
response = users.post("/users", data={
    "name": "John Doe",
    "email": "john@example.com"
})
```

#### PUT Request

```python
# PUT with JSON body
response = users.put("/users/123", json={
    "name": "Jane Doe",
    "email": "jane@example.com"
})
```

#### DELETE Request

```python
# DELETE request
response = users.delete("/users/123")
```

#### PATCH Request

```python
# PATCH with partial update
response = users.patch("/users/123", json={
    "name": "Updated Name"
})
```

### Helper Methods

#### Status Assertions

```python
# Assert specific status code
users.assert_status(response, 200)

# Assert multiple acceptable status codes
users.assert_status(response, [200, 201])

# Assert 2xx success
users.assert_ok(response)
```

#### JSON Parsing

```python
# Parse entire response as JSON
data = users.assert_json(response)

# Extract specific key from JSON
user_id = users.assert_json(response, key="data.id")

# Access nested fields
email = users.assert_json(response, key="data.user.email")
```

#### Header Assertions

```python
# Check header exists
content_type = users.assert_header(response, "content-type")

# Check header with expected value
users.assert_header(response, "content-type", "application/json")
```

### Complete Example

```python
"""Test user CRUD operations."""

from playwright.sync_api import APIResponse
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..users_page import UsersPage


def run(users: 'UsersPage') -> APIResponse:
    """Test complete user lifecycle."""
    # Create user
    create_response = users.post("/users", json={
        "name": "Test User",
        "email": "test@example.com"
    })
    users.assert_status(create_response, 201)

    user_id = users.assert_json(create_response, key="data.id")

    # Read user
    get_response = users.get(f"/users/{user_id}")
    users.assert_ok(get_response)

    user_data = users.assert_json(get_response)
    assert user_data["name"] == "Test User"

    # Update user
    update_response = users.put(f"/users/{user_id}", json={
        "name": "Updated Name"
    })
    users.assert_ok(update_response)

    # Delete user
    delete_response = users.delete(f"/users/{user_id}")
    users.assert_status(delete_response, 204)

    return create_response
```

## Assertions and Error Handling

### Standard Assertions

Use Python's built-in `assert` statement for validations:

```python
# Assert response status
assert response.ok, f"Request failed: {response.status}"
assert response.status == 200, "Expected 200 OK"

# Assert response data
data = response.json()
assert "id" in data, "Response missing 'id' field"
assert data["active"] is True, "User should be active"
assert len(data["items"]) > 0, "Should have at least one item"
```

### Using ServicePage Assertions

The ServicePage provides enhanced assertions with better error messages:

```python
# Status assertions
users.assert_status(response, 200)
users.assert_ok(response)

# JSON assertions
data = users.assert_json(response)
user = users.assert_json(response, key="data.user")

# Header assertions
users.assert_header(response, "content-type", "application/json")
```

### Error Handling Patterns

#### Try-Except with Cleanup

```python
def run(users: 'UsersPage') -> APIResponse:
    """Test with cleanup on failure."""
    created_id = None

    try:
        # Create resource
        response = users.post("/users", json={"name": "Test"})
        users.assert_status(response, 201)

        created_id = users.assert_json(response, key="data.id")

        # Test operations...

        return response

    except AssertionError as e:
        # Log failure details
        print(f"Test failed: {e}")
        raise

    finally:
        # Cleanup: delete created resource
        if created_id:
            users.delete(f"/users/{created_id}")
```

#### Handling Expected Errors

```python
def run(users: 'UsersPage') -> APIResponse:
    """Test invalid input returns proper error."""
    response = users.post("/users", json={
        "email": "invalid-email"  # Missing required 'name' field
    })

    # Should return 400 Bad Request
    users.assert_status(response, 400)

    error_data = users.assert_json(response)
    assert "error" in error_data, "Should have error message"
    assert error_data["code"] == "VALIDATION_ERROR"

    return response
```

#### Timeout and Retry Handling

```python
def run(users: 'UsersPage') -> APIResponse:
    """Test with automatic retry configuration."""
    # Configure retry for this test
    from socialseed_e2e.core.base_page import RetryConfig

    users.retry_config = RetryConfig(
        max_retries=3,
        backoff_factor=1.0,
        retry_on=[502, 503, 504, 429]
    )

    try:
        response = users.get("/slow-endpoint")
        users.assert_ok(response)
        return response
    finally:
        # Reset retry config
        users.retry_config = RetryConfig(max_retries=0)
```

## Sharing State Between Tests

### Using ServicePage Attributes

Store data in the ServicePage instance to share between tests:

```python
# In 01_login.py
def run(users: 'UsersPage') -> APIResponse:
    """Login and store token for subsequent tests."""
    response = users.post("/auth/login", json={
        "email": "test@example.com",
        "password": "password123"
    })
    users.assert_ok(response)

    # Store token in service page
    data = response.json()
    users.auth_token = data["token"]
    users.current_user = data["user"]

    return response
```

```python
# In 02_get_profile.py
def run(users: 'UsersPage') -> APIResponse:
    """Get profile using token from login."""
    # Use token stored in previous test
    headers = {"Authorization": f"Bearer {users.auth_token}"}

    user_id = users.current_user["id"]
    response = users.get(f"/users/{user_id}/profile", headers=headers)

    users.assert_ok(response)
    return response
```

### State Management Best Practices

```python
"""Test module with proper state management."""

from playwright.sync_api import APIResponse
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..api_page import ApiPage


def run(api: 'ApiPage') -> APIResponse:
    """Test with state initialization and cleanup."""
    # Initialize state if not exists
    if not hasattr(api, 'test_data'):
        api.test_data = {}

    if not hasattr(api, 'created_resources'):
        api.created_resources = []

    try:
        # Create test resource
        response = api.post("/items", json={"name": "Test Item"})
        users.assert_status(response, 201)

        item_id = response.json()["id"]
        api.test_data["item_id"] = item_id
        api.created_resources.append(item_id)

        # Test operations...

        return response

    except Exception:
        # Mark test as failed for cleanup
        api.test_failed = True
        raise
```

## Best Practices

### 1. Keep Tests Independent When Possible

```python
# Good: Test is self-contained
def run(users: 'UsersPage') -> APIResponse:
    """Create and verify user can be retrieved."""
    # Create user
    create_resp = users.post("/users", json={"name": "Test"})
    users.assert_status(create_resp, 201)
    user_id = create_resp.json()["id"]

    # Verify user exists
    get_resp = users.get(f"/users/{user_id}")
    users.assert_ok(get_resp)

    # Cleanup
    users.delete(f"/users/{user_id}")

    return create_resp
```

### 2. Use Descriptive Test Names and Documentation

```python
"""Test user authentication with valid credentials.

This module validates:
- User can login with valid email/password
- Token is returned on successful login
- Token can be used for authenticated requests
"""

def run(auth: 'AuthPage') -> APIResponse:
    """Execute login flow with valid credentials.

    Steps:
        1. Send login request with valid credentials
        2. Verify 200 OK response
        3. Verify token is present in response
        4. Verify token works for authenticated endpoint
    """
    # Implementation...
    pass
```

### 3. Clean Up Resources

```python
def run(api: 'ApiPage') -> APIResponse:
    """Test with resource cleanup."""
    resource_id = None

    try:
        # Create resource
        response = api.post("/resources", json={"name": "Test"})
        resource_id = response.json()["id"]

        # Test operations...

        return response

    finally:
        # Always cleanup
        if resource_id:
            api.delete(f"/resources/{resource_id}")
```

### 4. Use Type Hints for Better IDE Support

```python
from typing import TYPE_CHECKING, Dict, Any
from playwright.sync_api import APIResponse

if TYPE_CHECKING:
    from ..users_page import UsersPage


def run(users: 'UsersPage') -> APIResponse:
    """Create user with proper type hints."""
    user_data: Dict[str, Any] = {
        "name": "Test User",
        "email": "test@example.com"
    }

    response: APIResponse = users.post("/users", json=user_data)
    return response
```

### 5. Document Expected Behavior

```python
def run(users: 'UsersPage') -> APIResponse:
    """Test rate limiting behavior.

    Expected Behavior:
    - First 10 requests should succeed (within burst limit)
    - 11th request should return 429 Too Many Requests
    - After 1 second, requests should succeed again
    """
    # Implementation...
    pass
```

### 6. Handle Test Data Properly

```python
import uuid
from datetime import datetime

def run(users: 'UsersPage') -> APIResponse:
    """Test with unique test data."""
    # Use UUID for unique identifiers
    unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"

    # Use timestamp for time-based data
    timestamp = datetime.now().isoformat()

    response = users.post("/users", json={
        "name": f"Test User {timestamp}",
        "email": unique_email
    })

    return response
```

## Complete Examples

### Example 1: Authentication Flow

```python
"""Complete authentication flow test.

Tests: Login → Get Profile → Logout
"""

from playwright.sync_api import APIResponse
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..auth_page import AuthPage


def run(auth: 'AuthPage') -> APIResponse:
    """Execute complete authentication flow."""
    print("Step 1: Login with valid credentials")
    login_response = auth.post("/auth/login", json={
        "email": "user@example.com",
        "password": "password123"
    })
    auth.assert_ok(login_response)

    # Extract and store auth token
    login_data = auth.assert_json(login_response)
    auth_token = login_data["token"]
    user_id = login_data["user"]["id"]

    # Store for potential use in other tests
    auth.auth_token = auth_token
    auth.current_user_id = user_id

    print("Step 2: Access protected endpoint")
    headers = {"Authorization": f"Bearer {auth_token}"}
    profile_response = auth.get("/auth/profile", headers=headers)
    auth.assert_ok(profile_response)

    profile_data = auth.assert_json(profile_response)
    assert profile_data["email"] == "user@example.com"

    print("Step 3: Logout")
    logout_response = auth.post("/auth/logout", headers=headers)
    auth.assert_ok(logout_response)

    print("Step 4: Verify token is invalidated")
    invalid_response = auth.get("/auth/profile", headers=headers)
    auth.assert_status(invalid_response, 401)

    print("✓ Authentication flow completed successfully")
    return login_response
```

### Example 2: CRUD Operations

```python
"""Test complete CRUD lifecycle for resources."""

from playwright.sync_api import APIResponse
from typing import TYPE_CHECKING, Dict, Any

if TYPE_CHECKING:
    from ..resources_page import ResourcesPage


def run(resources: 'ResourcesPage') -> APIResponse:
    """Test Create, Read, Update, Delete operations."""
    created_ids = []

    try:
        print("Step 1: Create resource")
        create_data: Dict[str, Any] = {
            "name": "Test Resource",
            "description": "A test resource",
            "tags": ["test", "example"]
        }

        create_resp = resources.post("/resources", json=create_data)
        resources.assert_status(create_resp, 201)

        created_data = resources.assert_json(create_resp)
        resource_id = created_data["id"]
        created_ids.append(resource_id)

        print(f"  Created resource with ID: {resource_id}")

        print("Step 2: Read resource")
        get_resp = resources.get(f"/resources/{resource_id}")
        resources.assert_ok(get_resp)

        retrieved_data = resources.assert_json(get_resp)
        assert retrieved_data["name"] == create_data["name"]
        assert retrieved_data["description"] == create_data["description"]

        print("Step 3: Update resource")
        update_data = {"name": "Updated Resource Name"}
        update_resp = resources.put(f"/resources/{resource_id}", json=update_data)
        resources.assert_ok(update_resp)

        # Verify update
        verify_resp = resources.get(f"/resources/{resource_id}")
        verify_data = resources.assert_json(verify_resp)
        assert verify_data["name"] == update_data["name"]
        assert verify_data["description"] == create_data["description"]  # Unchanged

        print("Step 4: List resources")
        list_resp = resources.get("/resources")
        resources.assert_ok(list_resp)

        list_data = resources.assert_json(list_resp)
        assert any(r["id"] == resource_id for r in list_data["items"])

        print("Step 5: Delete resource")
        delete_resp = resources.delete(f"/resources/{resource_id}")
        resources.assert_status(delete_resp, 204)

        print("Step 6: Verify deletion")
        not_found_resp = resources.get(f"/resources/{resource_id}")
        resources.assert_status(not_found_resp, 404)

        created_ids.remove(resource_id)  # Mark as cleaned up

        print("✓ CRUD operations completed successfully")
        return create_resp

    finally:
        # Cleanup any remaining resources
        for resource_id in created_ids:
            try:
                resources.delete(f"/resources/{resource_id}")
            except Exception:
                pass  # Ignore cleanup errors
```

### Example 3: Error Handling and Validation

```python
"""Test input validation and error responses."""

from playwright.sync_api import APIResponse
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..users_page import UsersPage


def run(users: 'UsersPage') -> APIResponse:
    """Test various error scenarios."""
    print("Test 1: Missing required field")
    response = users.post("/users", json={
        "email": "test@example.com"
        # Missing 'name' field
    })
    users.assert_status(response, 400)

    error_data = users.assert_json(response)
    assert error_data["code"] == "VALIDATION_ERROR"
    assert "name" in error_data["details"]["missing_fields"]

    print("Test 2: Invalid email format")
    response = users.post("/users", json={
        "name": "Test User",
        "email": "not-an-email"
    })
    users.assert_status(response, 400)

    print("Test 3: Duplicate email")
    # Create first user
    users.post("/users", json={
        "name": "First User",
        "email": "duplicate@example.com"
    })

    # Try to create second user with same email
    response = users.post("/users", json={
        "name": "Second User",
        "email": "duplicate@example.com"
    })
    users.assert_status(response, 409)  # Conflict

    print("Test 4: Invalid field types")
    response = users.post("/users", json={
        "name": "Test",
        "email": "test@example.com",
        "age": "not-a-number"  # Should be integer
    })
    users.assert_status(response, 400)

    print("Test 5: Request too large")
    large_data = {"name": "x" * 10000}  # Exceeds limit
    response = users.post("/users", json=large_data)
    users.assert_status(response, 413)  # Payload Too Large

    print("Test 6: Not found")
    response = users.get("/users/999999")
    users.assert_status(response, 404)

    print("✓ All error scenarios handled correctly")
    return response
```

## Common Patterns

### Pattern 1: Setup and Teardown

```python
"""Test with comprehensive setup and teardown."""

def run(api: 'ApiPage') -> APIResponse:
    """Test with proper lifecycle management."""
    # Setup
    test_resources = []

    try:
        # Create test data
        for i in range(3):
            resp = api.post("/items", json={"name": f"Item {i}"})
            test_resources.append(resp.json()["id"])

        # Run test
        response = api.get("/items")
        data = response.json()
        assert len(data["items"]) >= 3

        return response

    finally:
        # Teardown
        for resource_id in test_resources:
            api.delete(f"/items/{resource_id}")
```

### Pattern 2: Chained Requests

```python
"""Test with dependent operations."""

def run(api: 'ApiPage') -> APIResponse:
    """Test workflow requiring multiple steps."""
    # Step 1: Create order
    order_resp = api.post("/orders", json={
        "items": [{"product_id": "123", "quantity": 2}]
    })
    order_id = order_resp.json()["id"]

    # Step 2: Process payment
    payment_resp = api.post(f"/orders/{order_id}/payment", json={
        "method": "credit_card",
        "amount": 100.00
    })

    # Step 3: Verify order status
    order = api.get(f"/orders/{order_id}").json()
    assert order["status"] == "paid"

    # Step 4: Trigger fulfillment
    api.post(f"/orders/{order_id}/fulfill")

    # Step 5: Verify fulfillment
    order = api.get(f"/orders/{order_id}").json()
    assert order["status"] == "fulfilled"

    return order_resp
```

### Pattern 3: Batch Operations

```python
"""Test batch/bulk operations."""

def run(api: 'ApiPage') -> APIResponse:
    """Test batch processing."""
    # Create multiple items
    items = [
        {"name": f"Item {i}"}
        for i in range(100)
    ]

    response = api.post("/items/batch", json={"items": items})
    api.assert_status(response, 201)

    result = response.json()
    assert result["created"] == 100
    assert result["failed"] == 0

    return response
```

### Pattern 4: Pagination Testing

```python
"""Test pagination behavior."""

def run(api: 'ApiPage') -> APIResponse:
    """Test list pagination."""
    # Get first page
    page1 = api.get("/items", params={"page": 1, "limit": 10})
    data1 = page1.json()

    assert len(data1["items"]) == 10
    assert data1["page"] == 1
    assert data1["has_next"] is True

    # Get second page
    page2 = api.get("/items", params={"page": 2, "limit": 10})
    data2 = page2.json()

    assert len(data2["items"]) == 10
    assert data2["page"] == 2

    # Verify no overlap
    page1_ids = {item["id"] for item in data1["items"]}
    page2_ids = {item["id"] for item in data2["items"]}
    assert not page1_ids.intersection(page2_ids)

    return page1
```

### Pattern 5: Async/Polling Operations

```python
"""Test asynchronous operations with polling."""

import time

def run(api: 'ApiPage') -> APIResponse:
    """Test async job with polling."""
    # Start async job
    job_resp = api.post("/jobs", json={"type": "data_export"})
    job_id = job_resp.json()["id"]

    # Poll until complete
    max_attempts = 30
    for attempt in range(max_attempts):
        status_resp = api.get(f"/jobs/{job_id}")
        status_data = status_resp.json()

        if status_data["status"] == "completed":
            break
        elif status_data["status"] == "failed":
            raise AssertionError(f"Job failed: {status_data['error']}")

        time.sleep(1)  # Wait before next poll
    else:
        raise AssertionError("Job did not complete in time")

    # Verify result
    result = api.get(f"/jobs/{job_id}/result")
    api.assert_ok(result)

    return job_resp
```

## Testing with Mock API

When writing tests, you can use the built-in Mock API for integration testing:

```python
"""Example using mock API for testing."""

from playwright.sync_api import APIResponse
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..users_page import UsersPage


def run(users: 'UsersPage') -> APIResponse:
    """Test with mock API data."""
    # The mock API has pre-configured test users:
    # - admin/admin123 (role: admin)
    # - user/user123 (role: user)

    # Test login with mock credentials
    response = users.post("/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })

    users.assert_ok(response)

    data = users.assert_json(response)
    assert data["role"] == "admin"
    assert "token" in data

    return response
```

## See Also

- [Configuration Reference](configuration.md) - Service configuration options
- [Mock API Guide](mock-api.md) - Using the mock API for testing
- [Testing Guide](testing-guide.md) - Pytest configuration and best practices
- [Quick Start](quickstart.md) - Get started with your first test
