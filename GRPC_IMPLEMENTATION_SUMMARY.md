# Issue #49: Add Support for gRPC Protocol Testing - Implementation Summary

## Overview
This document summarizes the implementation of gRPC protocol testing support for the socialseed-e2e framework.

## Changes Made

### 1. Dependencies (`pyproject.toml`)
- **Added**: Optional dependencies group `[project.optional-dependencies.grpc]`
  - `grpcio>=1.59.0` - Core gRPC library
  - `grpcio-tools>=1.59.0` - Protocol compiler
  - `protobuf>=4.24.0` - Protocol Buffers runtime
- **Updated**: Keywords to include "grpc"
- **Updated**: pytest markers to include "grpc" marker

### 2. Core gRPC Module (`src/socialseed_e2e/core/base_grpc_page.py`)
Created a new base page class for gRPC testing with features:
- **BaseGrpcPage**: Main class for gRPC service interactions
  - Channel management (secure/insecure)
  - Stub registration and retrieval
  - Automatic retry logic with configurable backoff
  - Call logging for debugging
  - Context manager support
- **GrpcRetryConfig**: Configuration for retry behavior
  - Customizable max retries, backoff factor, max backoff
  - Configurable retry status codes
- **GrpcCallLog**: Data class for logging gRPC calls
  - Tracks service, method, request, response, duration, errors

### 3. Protobuf Schema Handler (`src/socialseed_e2e/utils/proto_schema.py`)
Created utilities for protobuf schema management:
- **ProtoSchemaHandler**: Main handler class
  - Find proto files
  - Compile proto files to Python modules
  - Load message classes dynamically
  - Load service stubs
  - Create message instances
  - Parse JSON to protobuf
  - Convert protobuf to JSON/dict
  - List message types and services
  - Validate proto syntax
- **ProtoRegistry**: Registry for multiple proto handlers
  - Manage multiple proto directories
  - Compile all protos at once

### 4. Template (`src/socialseed_e2e/templates/grpc_service_page.py.template`)
Created template for generating gRPC service pages:
- Pre-configured structure
- Proto handler setup
- CRUD method templates
- Custom metadata support

### 5. Examples (`examples/grpc/`)
Created complete working example:
- **user.proto**: Protocol Buffer service definition
- **mock_server.py**: Mock gRPC server for testing
  - Implements UserService with CRUD operations
  - Includes test data seeding
  - Context manager support
- **user_grpc_page.py**: Service-specific page class
  - CRUD operations for User service
  - Assertion helpers
- **README.md**: Comprehensive usage guide

### 6. Documentation (`docs/grpc-testing.md`)
Created comprehensive documentation:
- Installation instructions
- Quick start guide
- BaseGrpcPage API reference
- ProtoSchemaHandler usage
- Mock server example
- Best practices
- Troubleshooting

### 7. Exports (`src/socialseed_e2e/__init__.py`)
Updated main exports to include:
- `BaseGrpcPage`
- `GrpcRetryConfig`
- `GrpcCallLog`
- `ProtoSchemaHandler`
- `ProtoRegistry`
- `GRPC_AVAILABLE` flag

### 8. Tests (`tests/unit/core/test_base_grpc_page.py`)
Created unit tests:
- GrpcRetryConfig tests
- GrpcCallLog tests
- BaseGrpcPage initialization tests
- Channel management tests
- Stub registration tests
- Call validation tests
- Context manager tests

## Usage Example

### Basic Usage
```python
from socialseed_e2e import BaseGrpcPage
from protos import user_pb2, user_pb2_grpc

# Create page and setup
page = BaseGrpcPage("localhost:50051")
page.setup()

# Register stub
page.register_stub("user", user_pb2_grpc.UserServiceStub)

# Make call
request = user_pb2.GetUserRequest(id="user-123")
response = page.call("user", "GetUser", request)

# Assert and cleanup
page.assert_ok(response)
page.teardown()
```

### With Context Manager
```python
with BaseGrpcPage("localhost:50051") as page:
    page.register_stub("user", user_pb2_grpc.UserServiceStub)
    request = user_pb2.GetUserRequest(id="user-123")
    response = page.call("user", "GetUser", request)
    page.assert_ok(response)
```

### Custom Service Page
```python
from socialseed_e2e import BaseGrpcPage
from protos import user_pb2, user_pb2_grpc

class UserServicePage(BaseGrpcPage):
    def setup(self):
        super().setup()
        self.register_stub("user", user_pb2_grpc.UserServiceStub)
        return self

    def do_get_user(self, user_id: str):
        request = user_pb2.GetUserRequest(id=user_id)
        return self.call("user", "GetUser", request)

# Usage
with UserServicePage("localhost:50051") as page:
    user = page.do_get_user("user-123")
    print(f"User: {user.name}")
```

## Running Tests

### Unit Tests
```bash
pytest tests/unit/core/test_base_grpc_page.py -v
```

### Integration Tests (with gRPC)
```bash
pytest -m grpc -v
```

### All Tests
```bash
pytest -v
```

## Directory Structure

```
socialseed-e2e/
├── pyproject.toml                          # Updated with gRPC dependencies
├── src/socialseed_e2e/
│   ├── __init__.py                        # Updated exports
│   ├── core/
│   │   └── base_grpc_page.py             # NEW: Core gRPC functionality
│   └── utils/
│       └── proto_schema.py               # NEW: Protobuf utilities
├── templates/
│   └── grpc_service_page.py.template     # NEW: gRPC service template
├── examples/grpc/                         # NEW: Complete example
│   ├── __init__.py
│   ├── user.proto
│   ├── mock_server.py
│   ├── user_grpc_page.py
│   ├── protos/
│   │   └── __init__.py
│   └── README.md
├── docs/
│   └── grpc-testing.md                    # NEW: Documentation
└── tests/unit/core/
    └── test_base_grpc_page.py            # NEW: Unit tests
```

## Key Features

1. **Protocol Agnostic**: Works with any gRPC service
2. **Retry Logic**: Automatic retry on transient failures
3. **Call Logging**: Complete request/response tracking
4. **Stub Management**: Easy stub registration and retrieval
5. **TLS Support**: Secure channel support
6. **Protobuf Utilities**: Schema compilation and message creation
7. **Mock Server**: Built-in test server
8. **Context Manager**: Clean resource management
9. **State Sharing**: Between test modules via DynamicStateMixin
10. **Type Safety**: Full type hints throughout

## Migration Notes

For existing users:
- No breaking changes to existing REST API functionality
- gRPC support is optional (requires `[grpc]` extra)
- All existing tests continue to work

## Next Steps

Future enhancements could include:
- CLI command: `e2e new-grpc-service`
- gRPC streaming support
- gRPC reflection support
- Automatic proto compilation on test run
- IDE integration for proto files
- Performance benchmarks

## References

- [gRPC Python Documentation](https://grpc.io/docs/languages/python/)
- [Protocol Buffers Documentation](https://developers.google.com/protocol-buffers)
- Example: `examples/grpc/`
- Documentation: `docs/grpc-testing.md`
