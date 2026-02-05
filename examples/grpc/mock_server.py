"""Mock gRPC User Service Server.

This module provides a mock gRPC server for testing purposes.
It implements the UserService defined in user.proto.
"""

import uuid
from concurrent import futures
from datetime import datetime
from typing import Dict

import grpc

# Import generated protobuf modules
from examples.grpc.protos import user_pb2
from examples.grpc.protos import user_pb2_grpc


class UserServiceServicer(user_pb2_grpc.UserServiceServicer):
    """Implementation of UserService."""

    def __init__(self):
        """Initialize with an empty user store."""
        self.users: Dict[str, user_pb2.User] = {}
        self._seed_data()

    def _seed_data(self):
        """Add some initial test data."""
        user1 = user_pb2.User(
            id=str(uuid.uuid4()),
            name="John Doe",
            email="john@example.com",
            age=30,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )
        user2 = user_pb2.User(
            id=str(uuid.uuid4()),
            name="Jane Smith",
            email="jane@example.com",
            age=25,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )
        self.users[user1.id] = user1
        self.users[user2.id] = user2

    def GetUser(self, request, context):
        """Get a user by ID."""
        if request.id not in self.users:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"User with ID {request.id} not found")
            return user_pb2.User()

        return self.users[request.id]

    def CreateUser(self, request, context):
        """Create a new user."""
        user_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        user = user_pb2.User(
            id=user_id,
            name=request.name,
            email=request.email,
            age=request.age,
            created_at=now,
            updated_at=now,
        )

        self.users[user_id] = user
        return user

    def UpdateUser(self, request, context):
        """Update an existing user."""
        if request.id not in self.users:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"User with ID {request.id} not found")
            return user_pb2.User()

        existing = self.users[request.id]

        # Update fields if provided
        if request.name:
            existing.name = request.name
        if request.email:
            existing.email = request.email
        if request.age > 0:
            existing.age = request.age

        existing.updated_at = datetime.now().isoformat()

        return existing

    def DeleteUser(self, request, context):
        """Delete a user."""
        if request.id not in self.users:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"User with ID {request.id} not found")
            return user_pb2.DeleteUserResponse(
                success=False, message=f"User with ID {request.id} not found"
            )

        del self.users[request.id]
        return user_pb2.DeleteUserResponse(
            success=True, message="User deleted successfully"
        )

    def ListUsers(self, request, context):
        """List all users."""
        page_size = request.page_size if request.page_size > 0 else 10

        users_list = list(self.users.values())

        # Simple pagination (in real implementation, use page_token)
        paginated_users = users_list[:page_size]

        return user_pb2.ListUsersResponse(
            users=paginated_users, next_page_token="", total_count=len(users_list)
        )

    def clear_data(self):
        """Clear all user data (for testing)."""
        self.users.clear()
        self._seed_data()


class MockGrpcServer:
    """Mock gRPC server for testing."""

    def __init__(self, port: int = 50051):
        """Initialize the mock server.

        Args:
            port: Port to listen on
        """
        self.port = port
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        self.servicer = UserServiceServicer()

        # Register the servicer
        user_pb2_grpc.add_UserServiceServicer_to_server(self.servicer, self.server)

        # Add insecure port
        self.server.add_insecure_port(f"[::]:{port}")

    def start(self):
        """Start the server."""
        self.server.start()
        print(f"Mock gRPC server started on port {self.port}")

    def stop(self, grace_period: float = 5.0):
        """Stop the server.

        Args:
            grace_period: Grace period for shutdown in seconds
        """
        self.server.stop(grace_period)
        print("Mock gRPC server stopped")

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


if __name__ == "__main__":
    # Run the server standalone
    server = MockGrpcServer(port=50051)
    try:
        server.start()
        print("Press Ctrl+C to stop")
        import time

        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        server.stop()
