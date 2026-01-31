# Writing Tests

## Test Module Structure

A test module is a Python file with a `run` function:

```python
from playwright.sync_api import APIResponse
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..myapi_page import MyapiPage

def run(myapi: 'MyapiPage') -> APIResponse:
    """Test description here."""
    print("Running test...")
    
    response = myapi.get("/endpoint")
    
    if response.ok:
        print("✓ Test passed")
    else:
        print(f"✗ Failed: {response.status}")
        raise AssertionError("Test failed")
    
    return response
```

## Using ServicePage

The service page provides HTTP methods:

```python
# GET request
response = myapi.get("/users")

# POST request
response = myapi.post("/users", json={"name": "John"})

# PUT request
response = myapi.put("/users/1", json={"name": "Jane"})

# DELETE request
response = myapi.delete("/users/1")
```

## Assertions

Use standard Python assertions:

```python
assert response.ok, f"Request failed: {response.status}"
assert response.status == 200, "Expected 200 OK"
data = response.json()
assert "id" in data, "Response missing id field"
```

## Sharing State

Store data in the service page for use across tests:

```python
# In first test
myapi.current_user = response.json()

# In subsequent test
user_id = myapi.current_user["id"]
```

## Best Practices

1. Keep tests independent when possible
2. Use descriptive test names
3. Clean up resources in finally blocks
4. Use type hints for better IDE support
5. Document expected behavior in docstrings
