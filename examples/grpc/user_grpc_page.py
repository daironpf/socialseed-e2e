"""Test page for User gRPC Service.

This module provides a page object for testing the User gRPC service,
extending BaseGrpcPage with service-specific methods.
"""

from typing import Any, List, Optional

from socialseed_e2e.core.base_grpc_page import BaseGrpcPage, GrpcRetryConfig
from socialseed_e2e.utils.proto_schema import ProtoSchemaHandler

# Import generated protobuf modules (will be available after compiling)
try:
    from examples.grpc.protos import user_pb2
    from examples.grpc.protos import user_pb2_grpc

    HAS_PROTO = True
except ImportError:
    HAS_PROTO = False
    print(
        "Warning: Protobuf modules not found. Run: python -m grpc_tools.protoc --proto_path=. --python_out=./protos --grpc_python_out=./protos user.proto"
    )


class UserServicePage(BaseGrpcPage):
    """Page object for User gRPC service testing.

    This class provides methods for interacting with the User gRPC service,
    including CRUD operations and list operations.

    Example:
        >>> page = UserServicePage("localhost:50051")
        >>> page.setup()
        >>> response = page.do_create_user("John", "john@example.com", 30)
        >>> page.assert_ok(response)
        >>> print(f"Created user: {response.name}")
        >>> page.teardown()

    Attributes:
        proto_handler: Handler for protobuf operations
    """

    def __init__(
        self,
        host: str = "localhost:50051",
        use_tls: bool = False,
        timeout: float = 30.0,
        retry_config: Optional[GrpcRetryConfig] = None,
    ):
        """Initialize the User service page.

        Args:
            host: gRPC server host:port
            use_tls: Whether to use TLS/SSL
            timeout: Default timeout for calls
            retry_config: Retry configuration
        """
        super().__init__(
            host=host, use_tls=use_tls, timeout=timeout, retry_config=retry_config
        )

        # Initialize protobuf handler
        self.proto_handler = ProtoSchemaHandler("./protos")

        # Compile protos if available
        if HAS_PROTO:
            try:
                self.proto_handler.compile_protos()
            except Exception as e:
                print(f"Warning: Could not compile protos: {e}")

    def setup(self) -> "UserServicePage":
        """Set up the page and register stubs.

        Returns:
            Self for method chaining
        """
        super().setup()

        # Register the UserService stub
        if HAS_PROTO:
            self.register_stub("user", user_pb2_grpc.UserServiceStub)

        return self

    def do_get_user(self, user_id: str) -> Any:
        """Get a user by ID.

        Args:
            user_id: ID of the user to get

        Returns:
            User message or None if not found
        """
        if not HAS_PROTO:
            raise RuntimeError("Protobuf modules not available")

        request = user_pb2.GetUserRequest(id=user_id)
        return self.call("user", "GetUser", request)

    def do_create_user(self, name: str, email: str, age: int = 0) -> Any:
        """Create a new user.

        Args:
            name: User name
            email: User email
            age: User age

        Returns:
            Created user message
        """
        if not HAS_PROTO:
            raise RuntimeError("Protobuf modules not available")

        request = user_pb2.CreateUserRequest(name=name, email=email, age=age)
        return self.call("user", "CreateUser", request)

    def do_update_user(
        self,
        user_id: str,
        name: Optional[str] = None,
        email: Optional[str] = None,
        age: Optional[int] = None,
    ) -> Any:
        """Update an existing user.

        Args:
            user_id: ID of the user to update
            name: New name (optional)
            email: New email (optional)
            age: New age (optional)

        Returns:
            Updated user message
        """
        if not HAS_PROTO:
            raise RuntimeError("Protobuf modules not available")

        request = user_pb2.UpdateUserRequest(
            id=user_id, name=name or "", email=email or "", age=age or 0
        )
        return self.call("user", "UpdateUser", request)

    def do_delete_user(self, user_id: str) -> Any:
        """Delete a user.

        Args:
            user_id: ID of the user to delete

        Returns:
            Delete response message
        """
        if not HAS_PROTO:
            raise RuntimeError("Protobuf modules not available")

        request = user_pb2.DeleteUserRequest(id=user_id)
        return self.call("user", "DeleteUser", request)

    def do_list_users(self, page_size: int = 10, page_token: str = "") -> Any:
        """List all users.

        Args:
            page_size: Number of users per page
            page_token: Token for pagination

        Returns:
            List response message with users
        """
        if not HAS_PROTO:
            raise RuntimeError("Protobuf modules not available")

        request = user_pb2.ListUsersRequest(page_size=page_size, page_token=page_token)
        return self.call("user", "ListUsers", request)

    def assert_user_exists(self, user_id: str, context: str = "") -> Any:
        """Assert that a user exists.

        Args:
            user_id: ID of the user to check
            context: Optional context message

        Returns:
            The user message

        Raises:
            AssertionError: If user not found
        """
        user = self.do_get_user(user_id)
        if not user or not user.id:
            message = f"User {user_id} not found"
            if context:
                message = f"{context}: {message}"
            raise AssertionError(message)
        return user

    def assert_user_has_email(self, user_id: str, expected_email: str) -> None:
        """Assert that a user has the expected email.

        Args:
            user_id: ID of the user to check
            expected_email: Expected email address

        Raises:
            AssertionError: If email doesn't match
        """
        user = self.do_get_user(user_id)
        if user.email != expected_email:
            raise AssertionError(
                f"User {user_id} has email '{user.email}', expected '{expected_email}'"
            )
