# gRPC API Testing Guide

This guide covers testing gRPC APIs with socialseed-e2e.

---

## Installation

gRPC support requires extra dependencies:

```bash
pip install socialseed-e2e[grpc]
```

---

## Configuration

Edit `e2e.conf`:

```yaml
services:
  my-grpc:
    type: grpc
    host: localhost
    port: 50051
    proto_file: ./protos/user.proto
    package: user
    service: UserService
```

---

## Test Examples

### Unary Call

```python
# services/my-grpc/modules/01_get_user.py
from socialseed_e2e.core.base_page import BasePage


def run(page: BasePage) -> dict:
    response = page.grpc_call(
        "GetUser",
        {"id": "123"}
    )
    
    assert response.code == 0  # OK
    assert response.data["name"] == "John"
    
    return response
```

### Server Streaming

```python
# services/my-grpc/modules/02_list_users.py
from socialseed_e2e.core.base_page import BasePage


def run(page: BasePage) -> dict:
    responses = page.grpc_stream(
        "ListUsers",
        {"limit": 10}
    )
    
    # responses is an iterator
    user_list = list(responses)
    
    assert len(user_list) > 0
    assert user_list[0].data["id"]
    
    return {"count": len(user_list)}
```

### Client Streaming

```python
# services/my-grpc/modules/03_create_users.py
from socialseed_e2e.core.base_page import BasePage


def run(page: BasePage) -> dict:
    users = [
        {"name": "User1", "email": "user1@example.com"},
        {"name": "User2", "email": "user2@example.com"},
    ]
    
    response = page.grpc_client_stream(
        "CreateUsers",
        users
    )
    
    assert response.code == 0
    assert len(response.data["created"]) == 2
    
    return response
```

### Bidirectional Streaming

```python
# services/my-grpc/modules/04_chat.py
from socialseed_e2e.core.base_page import BasePage


def run(page: BasePage) -> dict:
    messages = [
        {"content": "Hello"},
        {"content": "World"},
    ]
    
    responses = page.grpc_bidi_stream(
        "Chat",
        messages
    )
    
    response_list = list(responses)
    
    assert len(response_list) == 2
    
    return {"exchanged": len(response_list)}
```

---

## Authentication

### Token Authentication

```python
def run(page: BasePage) -> dict:
    # Set metadata for authentication
    page.grpc_metadata = {
        "authorization": "Bearer your-token-here"
    }
    
    response = page.grpc_call("GetProfile", {"user_id": "123"})
    
    assert response.code == 0
    
    return response
```

---

## Error Handling

```python
def run(page: BasePage) -> dict:
    response = page.grpc_call(
        "GetUser",
        {"id": "nonexistent"}
    )
    
    if response.code != 0:
        # Handle error
        return {
            "error": response.error,
            "code": response.code
        }
    
    return response
```

---

## Assertions

### Status Codes

gRPC uses numeric codes:
- 0 = OK
- 1 = CANCELED
- 2 = UNKNOWN
- 3 = INVALID_ARGUMENT
- 5 = NOT_FOUND
- 13 = INTERNAL
- 16 = UNAUTHENTICATED

```python
assert response.code == 0  # Success
assert response.code == 5  # Not found
```

### Response Data

```python
data = response.data
assert data["id"] == "123"
assert "email" in data
assert data["status"] == "active"
```

---

## Running gRPC Tests

```bash
# Install gRPC dependencies first
pip install socialseed-e2e[grpc]

# Run tests
e2e run --service my-grpc
```

---

## Proto File Generation

If you don't have generated Python files:

```bash
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. your.proto
```

---

## Demo API

Use the included gRPC demo:

```bash
e2e install-demo grpc
cd demos/grpc
python server.py  # Start gRPC server on port 50051
```

Then configure and test:
```bash
e2e set url grpc_demo http://localhost:50051
e2e run --service grpc_demo
```
