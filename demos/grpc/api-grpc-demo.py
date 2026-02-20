#!/usr/bin/env python3
"""gRPC Demo API for socialseed-e2e Testing

This is a simple gRPC API with user management operations.
Use this API to test gRPC functionality in socialseed-e2e.

Usage:
    # Install grpcio-tools first
    pip install grpcio grpcio-tools
    
    # Generate Python code from proto (in separate terminal)
    python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. api-grpc-demo.proto
    
    # Start the gRPC server
    python api-grpc-demo.py
    
    # The gRPC server will be available at localhost:50051

Proto Definition:
    See api-grpc-demo.proto for the service definition.
"""

import asyncio
from concurrent import futures
import grpc

# Import generated proto modules (run: python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. api-grpc-demo.proto)
try:
    import api_pb2
    import api_pb2_grpc
except ImportError:
    print("ERROR: Proto modules not found.")
    print("Run: python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. api-grpc-demo.proto")
    raise


class UserServiceServicer(api_pb2_grpc.UserServiceServicer):
    """gRPC User Service implementation"""
    
    def __init__(self):
        self.users = {
            "1": {"id": "1", "name": "Alice Johnson", "email": "alice@example.com", "role": "admin"},
            "2": {"id": "2", "name": "Bob Smith", "email": "bob@example.com", "role": "user"},
            "3": {"id": "3", "name": "Charlie Brown", "email": "charlie@example.com", "role": "user"},
            "4": {"id": "4", "name": "Diana Prince", "email": "diana@example.com", "role": "moderator"},
            "5": {"id": "5", "name": "Eve Adams", "email": "eve@example.com", "role": "user"},
        }
        self.next_id = 6
    
    def GetUser(self, request, context):
        """Get a single user by ID"""
        user_id = request.id
        if user_id in self.users:
            user = self.users[user_id]
            return api_pb2.GetUserResponse(
                user=api_pb2.User(
                    id=user["id"], 
                    name=user["name"], 
                    email=user["email"], 
                    role=user["role"]
                )
            )
        return api_pb2.GetUserResponse(error="User not found")
    
    def ListUsers(self, request, context):
        """List all users"""
        users = [
            api_pb2.User(id=u["id"], name=u["name"], email=u["email"], role=u["role"]) 
            for u in self.users.values()
        ]
        return api_pb2.ListUsersResponse(users=users, total=len(users))
    
    def CreateUser(self, request, context):
        """Create a new user"""
        user_id = str(self.next_id)
        self.next_id += 1
        user = {
            "id": user_id, 
            "name": request.name, 
            "email": request.email, 
            "role": request.role if request.role else "user"
        }
        self.users[user_id] = user
        return api_pb2.CreateUserResponse(
            user=api_pb2.User(id=user["id"], name=user["name"], email=user["email"], role=user["role"]),
            message="User created successfully"
        )
    
    def UpdateUser(self, request, context):
        """Update an existing user"""
        user_id = request.id
        if user_id in self.users:
            user = self.users[user_id]
            if request.name:
                user["name"] = request.name
            if request.email:
                user["email"] = request.email
            if request.role:
                user["role"] = request.role
            return api_pb2.UpdateUserResponse(
                user=api_pb2.User(id=user["id"], name=user["name"], email=user["email"], role=user["role"]),
                message="User updated successfully"
            )
        return api_pb2.UpdateUserResponse(error="User not found")
    
    def DeleteUser(self, request, context):
        """Delete a user"""
        user_id = request.id
        if user_id in self.users:
            del self.users[user_id]
            return api_pb2.DeleteUserResponse(message="User deleted successfully")
        return api_pb2.DeleteUserResponse(error="User not found")


def serve():
    """Start the gRPC server"""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    api_pb2_grpc.add_UserServiceServicer_to_server(UserServiceServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    
    print("=" * 60)
    print("🚀 gRPC Demo API for socialseed-e2e Testing")
    print("=" * 60)
    print("\n📍 gRPC URL: localhost:50051")
    print("\nAvailable methods:")
    print("  GetUser    - Get a single user by ID")
    print("  ListUsers  - List all users")
    print("  CreateUser - Create a new user")
    print("  UpdateUser - Update an existing user")
    print("  DeleteUser - Delete a user")
    print("\nTo generate Python stubs:")
    print("  python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. api-grpc-demo.proto")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60 + "\n")
    
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
