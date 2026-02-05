# gRPC Testing Example

This example demonstrates how to test gRPC services using the socialseed-e2e framework.

## Files

- `user.proto` - Protocol Buffer definition for UserService
- `mock_server.py` - Mock gRPC server implementing UserService
- `test_user_grpc_page.py` - Test page for UserService
- `test_modules/` - Test modules demonstrating different test scenarios

## Setup

1. Install gRPC dependencies:
```bash
pip install socialseed-e2e[grpc]
```

2. Compile the proto file:
```bash
cd examples/grpc
python -m grpc_tools.protoc --proto_path=. --python_out=./protos --grpc_python_out=./protos user.proto
```

3. Run the tests:
```bash
e2e run
```

## Usage

### Basic Example

```python
from socialseed_e2e import BaseGrpcPage
from protos import user_pb2_grpc

# Create and setup the page
page = BaseGrpcPage("localhost:50051")
page.setup()

# Register the stub
page.register_stub("user", user_pb2_grpc.UserServiceStub)

# Create a request
from protos import user_pb2
request = user_pb2.CreateUserRequest(
    name="John Doe",
    email="john@example.com",
    age=30
)

# Make the call
response = page.call("user", "CreateUser", request)
page.assert_ok(response)

# Teardown
page.teardown()
```

### Using Context Manager

```python
from socialseed_e2e import BaseGrpcPage
from protos import user_pb2_grpc, user_pb2

with BaseGrpcPage("localhost:50051") as page:
    page.register_stub("user", user_pb2_grpc.UserServiceStub)

    request = user_pb2.GetUserRequest(id="user-123")
    response = page.call("user", "GetUser", request)

    print(f"User: {response.name}")
```

### With Custom Service Page

```python
from socialseed_e2e.core.base_grpc_page import BaseGrpcPage
from socialseed_e2e.utils.proto_schema import ProtoSchemaHandler
from protos import user_pb2_grpc

class UserServicePage(BaseGrpcPage):
    def __init__(self, host="localhost:50051"):
        super().__init__(host)
        self.proto_handler = ProtoSchemaHandler("./protos")
        self.proto_handler.compile_protos()

    def setup(self):
        super().setup()
        self.register_stub("user", user_pb2_grpc.UserServiceStub)
        return self

    def do_get_user(self, user_id: str):
        request = self.proto_handler.create_message(
            "user_pb2", "GetUserRequest", id=user_id
        )
        return self.call("user", "GetUser", request)

    def do_create_user(self, name: str, email: str, age: int = 0):
        request = self.proto_handler.create_message(
            "user_pb2", "CreateUserRequest",
            name=name, email=email, age=age
        )
        return self.call("user", "CreateUser", request)

# Usage
page = UserServicePage()
page.setup()

response = page.do_create_user("Jane Doe", "jane@example.com", 25)
page.assert_ok(response)

page.teardown()
```

## Features Demonstrated

1. **BaseGrpcPage** - Core gRPC testing functionality
2. **ProtoSchemaHandler** - Protobuf schema compilation and message creation
3. **Stub Registration** - Service stub management
4. **Retry Logic** - Automatic retry on failures
5. **Call Logging** - Track all gRPC calls
6. **Custom Service Pages** - Extending base functionality

## Running the Example

1. Start the mock server:
```bash
python examples/grpc/mock_server.py
```

2. In another terminal, run the tests:
```bash
cd examples/grpc
e2e run
```

## Protobuf Schema Handler

The `ProtoSchemaHandler` provides utilities for:

- Compiling .proto files
- Loading message classes
- Creating message instances
- Parsing JSON to protobuf
- Converting protobuf to JSON

Example:
```python
from socialseed_e2e.utils.proto_schema import ProtoSchemaHandler

handler = ProtoSchemaHandler("./protos")
handler.compile_protos()

# Create a message
request = handler.create_message(
    "user_pb2", "CreateUserRequest",
    name="John", email="john@example.com"
)

# Parse from JSON
request = handler.parse_message(
    "user_pb2", "CreateUserRequest",
    '{"name": "John", "email": "john@example.com"}'
)

# Convert to dict
data = handler.message_to_dict(response)
```
