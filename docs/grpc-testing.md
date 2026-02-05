# gRPC Protocol Testing Guide

This guide explains how to test gRPC APIs using the socialseed-e2e framework.

## Overview

The framework provides comprehensive support for gRPC testing through:

- **BaseGrpcPage**: Core class for gRPC service interactions
- **ProtoSchemaHandler**: Utility for protobuf schema management
- **Retry Logic**: Automatic retry on transient failures
- **Call Logging**: Track all gRPC calls for debugging
- **Mock Server**: Built-in mock gRPC server for testing

## Installation

Install with gRPC support:

```bash
pip install socialseed-e2e[grpc]
```

Or manually install dependencies:
```bash
pip install grpcio grpcio-tools protobuf
```

## Quick Start

### 1. Define Your Proto File

Create a `.proto` file defining your service:

```protobuf
syntax = "proto3";

package user;

service UserService {
  rpc GetUser (GetUserRequest) returns (User);
  rpc CreateUser (CreateUserRequest) returns (User);
}

message User {
  string id = 1;
  string name = 2;
  string email = 3;
}

message GetUserRequest {
  string id = 1;
}

message CreateUserRequest {
  string name = 1;
  string email = 2;
}
```

### 2. Compile Proto Files

```bash
python -m grpc_tools.protoc \
  --proto_path=. \
  --python_out=./protos \
  --grpc_python_out=./protos \
  user.proto
```

### 3. Create Service Page

```python
from socialseed_e2e.core.base_grpc_page import BaseGrpcPage
from protos import user_pb2, user_pb2_grpc

class UserServicePage(BaseGrpcPage):
    def setup(self):
        super().setup()
        self.register_stub("user", user_pb2_grpc.UserServiceStub)
        return self

    def do_get_user(self, user_id: str):
        request = user_pb2.GetUserRequest(id=user_id)
        return self.call("user", "GetUser", request)

    def do_create_user(self, name: str, email: str):
        request = user_pb2.CreateUserRequest(name=name, email=email)
        return self.call("user", "CreateUser", request)
```

### 4. Write Tests

```python
def run(page: UserServicePage):
    # Create a user
    response = page.do_create_user("John Doe", "john@example.com")
    page.assert_ok(response)

    user_id = response.id

    # Get the user
    user = page.do_get_user(user_id)
    assert user.name == "John Doe"
    assert user.email == "john@example.com"
```

## BaseGrpcPage API

### Initialization

```python
from socialseed_e2e.core.base_grpc_page import BaseGrpcPage, GrpcRetryConfig

# Basic setup
page = BaseGrpcPage("localhost:50051")

# With TLS
page = BaseGrpcPage("localhost:50051", use_tls=True)

# With custom retry config
retry_config = GrpcRetryConfig(
    max_retries=5,
    backoff_factor=2.0,
    retry_codes=[14, 4, 8]  # UNAVAILABLE, DEADLINE_EXCEEDED, RESOURCE_EXHAUSTED
)
page = BaseGrpcPage("localhost:50051", retry_config=retry_config)
```

### Lifecycle

```python
# Method 1: Explicit setup/teardown
page = BaseGrpcPage("localhost:50051")
page.setup()
# ... use page ...
page.teardown()

# Method 2: Context manager (recommended)
with BaseGrpcPage("localhost:50051") as page:
    # ... use page ...
    pass  # Automatically calls teardown
```

### Registering Stubs

```python
from protos import user_pb2_grpc

# Register a stub
page.register_stub("user", user_pb2_grpc.UserServiceStub)

# Get registered stub
stub = page.get_stub("user")
```

### Making Calls

```python
from protos import user_pb2

# Create request
request = user_pb2.GetUserRequest(id="user-123")

# Make call
response = page.call(
    stub_name="user",
    method_name="GetUser",
    request=request,
    timeout=10.0,  # Optional: override default timeout
    metadata={"authorization": "Bearer token"},  # Optional: add metadata
    retry=True  # Optional: retry on failure
)

# Assert success
page.assert_ok(response)
```

### Call Logs

```python
# Get all call logs
logs = page.get_call_logs()

for log in logs:
    print(f"{log.service}.{log.method}: {log.status_code}")
    print(f"  Duration: {log.duration_ms}ms")
    print(f"  Error: {log.error}")

# Clear logs
page.clear_logs()
```

## ProtoSchemaHandler

The `ProtoSchemaHandler` provides utilities for working with protobuf schemas:

### Compiling Proto Files

```python
from socialseed_e2e.utils.proto_schema import ProtoSchemaHandler

handler = ProtoSchemaHandler("./protos")
generated_files = handler.compile_protos()

# Force recompilation
handler.compile_protos(force=True)
```

### Loading Message Classes

```python
# Load a message class
UserClass = handler.load_message_class("user_pb2", "User")

# Create instance
user = UserClass(id="123", name="John", email="john@example.com")
```

### Creating Messages

```python
# Create with keyword arguments
request = handler.create_message(
    "user_pb2",
    "CreateUserRequest",
    name="John",
    email="john@example.com"
)
```

### Converting Formats

```python
# Parse from JSON
request = handler.parse_message(
    "user_pb2",
    "CreateUserRequest",
    '{"name": "John", "email": "john@example.com"}'
)

# Convert to dict
data = handler.message_to_dict(response)
# {'id': '123', 'name': 'John', 'email': 'john@example.com'}
```

### Loading Service Stubs

```python
# Load stub class
UserServiceStub = handler.load_service_stub(
    "user_pb2_grpc",
    "UserService",
    stub_type="stub"  # or "servicer" for server implementation
)

# Instantiate
stub = UserServiceStub(channel)
```

## Mock gRPC Server

For testing without a real gRPC server:

```python
from examples.grpc.mock_server import MockGrpcServer

# Start mock server
with MockGrpcServer(port=50051) as server:
    # Run your tests
    page = UserServicePage("localhost:50051")
    page.setup()
    # ... tests ...
    page.teardown()

# Server automatically stops on exit
```

## Best Practices

### 1. Use Service-Specific Pages

Create a dedicated page class for each gRPC service:

```python
class OrderServicePage(BaseGrpcPage):
    def setup(self):
        super().setup()
        self.register_stub("orders", order_pb2_grpc.OrderServiceStub)
        return self

    def do_create_order(self, customer_id: str, items: List[dict]):
        request = order_pb2.CreateOrderRequest(
            customer_id=customer_id,
            items=[order_pb2.OrderItem(**item) for item in items]
        )
        return self.call("orders", "CreateOrder", request)
```

### 2. Handle Timeouts

```python
# Set default timeout in constructor
page = BaseGrpcPage("localhost:50051", timeout=60.0)

# Or override per call
response = page.call("user", "SlowOperation", request, timeout=120.0)
```

### 3. Use Retry for Resilience

```python
retry_config = GrpcRetryConfig(
    max_retries=3,
    backoff_factor=1.5,
    retry_codes=[14, 4]  # UNAVAILABLE, DEADLINE_EXCEEDED
)

page = BaseGrpcPage("localhost:50051", retry_config=retry_config)
```

### 4. Share State Between Tests

Use the state management mixin to share data:

```python
# Test 1: Create user
response = page.do_create_user("John", "john@example.com")
page.set_state("created_user_id", response.id)

# Test 2: Use created user
user_id = page.get_state("created_user_id")
page.do_get_user(user_id)
```

### 5. Validate Proto Files

```python
errors = handler.validate_proto_syntax("service.proto")
if errors:
    print("Proto validation errors:", errors)
```

## Examples

See the `examples/grpc/` directory for a complete working example including:

- `user.proto` - Protocol Buffer definition
- `mock_server.py` - Mock gRPC server
- `user_grpc_page.py` - Service page implementation
- `test_modules/` - Test examples

## Troubleshooting

### Import Error

Error: `ImportError: No module named 'user_pb2'`

**Solution**: Compile proto files first:
```bash
python -m grpc_tools.protoc --proto_path=. --python_out=./protos --grpc_python_out=./protos user.proto
```

### Connection Error

Error: `grpc.RpcError: StatusCode.UNAVAILABLE`

**Solution**: Ensure the gRPC server is running and accessible.

### Proto Compilation Error

Error: `protoc: command not found`

**Solution**: Install grpcio-tools:
```bash
pip install grpcio-tools
```

## CLI Support

Create gRPC service scaffolding:

```bash
# Create a new gRPC service (when CLI support is added)
e2e new-grpc-service user-service --proto=user.proto
```

This will generate:
- Service page class
- Proto handler setup
- Test module templates
