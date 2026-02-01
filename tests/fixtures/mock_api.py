"""Mock Flask API for integration testing.

This module provides a Flask-based mock API for testing the socialseed-e2e framework.
It implements a simple REST API with authentication and CRUD operations for users.

Usage:
    # Start the mock API server
    python tests/fixtures/mock_api.py
    
    # Or use as a fixture in tests
    from tests.fixtures.mock_api import mock_api_server

Endpoints:
    GET    /health           - Health check
    GET    /api/users        - List all users
    POST   /api/users        - Create a new user
    GET    /api/users/{id}   - Get a specific user
    PUT    /api/users/{id}   - Update a user
    DELETE /api/users/{id}   - Delete a user
    POST   /api/auth/login   - Authenticate a user
    POST   /api/auth/register - Register a new user
"""

import uuid
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Dict, List, Optional

from flask import Flask, jsonify, request


class MockAPIServer:
    """Flask-based mock API server for integration testing.
    
    This class provides a complete mock REST API with:
    - Health check endpoint
    - User CRUD operations
    - Authentication endpoints
    - In-memory data storage
    
    Attributes:
        app: The Flask application instance
        users: In-memory storage for users (dict: id -> user_data)
        auth_tokens: In-memory storage for active auth tokens
        port: The port number the server runs on
    """
    
    def __init__(self, port: int = 8765):
        """Initialize the mock API server.
        
        Args:
            port: The port number to run the server on (default: 8765)
        """
        self.port = port
        self.app = Flask(__name__)
        self.users: Dict[str, Dict[str, Any]] = {}
        self.auth_tokens: Dict[str, str] = {}  # token -> user_id
        
        # Seed with some initial data
        self._seed_data()
        
        # Register routes
        self._register_routes()
    
    def _seed_data(self) -> None:
        """Seed the database with initial test data."""
        initial_users = [
            {
                "id": str(uuid.uuid4()),
                "email": "admin@example.com",
                "password": "admin123",  # In real apps, never store plain passwords!
                "name": "Admin User",
                "role": "admin",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
            {
                "id": str(uuid.uuid4()),
                "email": "user@example.com",
                "password": "user123",
                "name": "Test User",
                "role": "user",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
        ]
        
        for user in initial_users:
            self.users[user["id"]] = user
    
    def _register_routes(self) -> None:
        """Register all API routes."""
        
        # Health check
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint.
            
            Returns:
                JSON with status and timestamp
            """
            return jsonify({
                "status": "healthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "service": "mock-api",
                "version": "1.0.0"
            }), 200
        
        # Users CRUD
        @self.app.route('/api/users', methods=['GET'])
        def list_users():
            """List all users.
            
            Query Parameters:
                page: Page number (default: 1)
                limit: Items per page (default: 10)
                search: Search term for name or email
            
            Returns:
                JSON with users list and pagination info
            """
            # Parse query parameters
            page = request.args.get('page', 1, type=int)
            limit = request.args.get('limit', 10, type=int)
            search = request.args.get('search', '').lower()
            
            # Filter users
            filtered_users = list(self.users.values())
            if search:
                filtered_users = [
                    u for u in filtered_users
                    if search in u['name'].lower() or search in u['email'].lower()
                ]
            
            # Paginate
            total = len(filtered_users)
            start = (page - 1) * limit
            end = start + limit
            paginated_users = filtered_users[start:end]
            
            # Remove passwords from response
            users_response = [
                {k: v for k, v in u.items() if k != 'password'}
                for u in paginated_users
            ]
            
            return jsonify({
                "items": users_response,
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": (total + limit - 1) // limit
            }), 200
        
        @self.app.route('/api/users', methods=['POST'])
        def create_user():
            """Create a new user.
            
            Request Body:
                email: User email (required)
                password: User password (required)
                name: User name (required)
                role: User role (optional, default: 'user')
            
            Returns:
                JSON with created user data
            """
            data = request.get_json()
            
            # Validation
            if not data:
                return jsonify({"error": "Request body is required"}), 400
            
            required_fields = ['email', 'password', 'name']
            for field in required_fields:
                if field not in data or not data[field]:
                    return jsonify({"error": f"Field '{field}' is required"}), 400
            
            # Check for duplicate email
            if any(u['email'] == data['email'] for u in self.users.values()):
                return jsonify({"error": "Email already exists"}), 409
            
            # Create user
            user_id = str(uuid.uuid4())
            new_user = {
                "id": user_id,
                "email": data['email'],
                "password": data['password'],
                "name": data['name'],
                "role": data.get('role', 'user'),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            
            self.users[user_id] = new_user
            
            # Return user without password
            user_response = {k: v for k, v in new_user.items() if k != 'password'}
            return jsonify(user_response), 201
        
        @self.app.route('/api/users/<user_id>', methods=['GET'])
        def get_user(user_id: str):
            """Get a specific user by ID.
            
            Args:
                user_id: The UUID of the user
            
            Returns:
                JSON with user data
            """
            if user_id not in self.users:
                return jsonify({"error": "User not found"}), 404
            
            user = self.users[user_id]
            user_response = {k: v for k, v in user.items() if k != 'password'}
            
            return jsonify(user_response), 200
        
        @self.app.route('/api/users/<user_id>', methods=['PUT'])
        def update_user(user_id: str):
            """Update a user.
            
            Args:
                user_id: The UUID of the user
            
            Request Body:
                email: User email (optional)
                name: User name (optional)
                role: User role (optional)
            
            Returns:
                JSON with updated user data
            """
            if user_id not in self.users:
                return jsonify({"error": "User not found"}), 404
            
            data = request.get_json()
            if not data:
                return jsonify({"error": "Request body is required"}), 400
            
            user = self.users[user_id]
            
            # Update fields
            allowed_fields = ['email', 'name', 'role']
            for field in allowed_fields:
                if field in data:
                    user[field] = data[field]
            
            user['updated_at'] = datetime.now(timezone.utc).isoformat()
            
            user_response = {k: v for k, v in user.items() if k != 'password'}
            return jsonify(user_response), 200
        
        @self.app.route('/api/users/<user_id>', methods=['DELETE'])
        def delete_user(user_id: str):
            """Delete a user.
            
            Args:
                user_id: The UUID of the user
            
            Returns:
                Empty response with 204 status
            """
            if user_id not in self.users:
                return jsonify({"error": "User not found"}), 404
            
            del self.users[user_id]
            
            # Also remove any auth tokens for this user
            tokens_to_remove = [
                token for token, uid in self.auth_tokens.items()
                if uid == user_id
            ]
            for token in tokens_to_remove:
                del self.auth_tokens[token]
            
            return '', 204
        
        # Authentication
        @self.app.route('/api/auth/login', methods=['POST'])
        def login():
            """Authenticate a user.
            
            Request Body:
                email: User email (required)
                password: User password (required)
            
            Returns:
                JSON with auth token and user data
            """
            data = request.get_json()
            
            if not data:
                return jsonify({"error": "Request body is required"}), 400
            
            if 'email' not in data or 'password' not in data:
                return jsonify({"error": "Email and password are required"}), 400
            
            # Find user by email
            user = None
            for u in self.users.values():
                if u['email'] == data['email'] and u['password'] == data['password']:
                    user = u
                    break
            
            if not user:
                return jsonify({"error": "Invalid email or password"}), 401
            
            # Generate token
            token = str(uuid.uuid4())
            self.auth_tokens[token] = user['id']
            
            user_response = {k: v for k, v in user.items() if k != 'password'}
            
            return jsonify({
                "token": token,
                "user": user_response
            }), 200
        
        @self.app.route('/api/auth/register', methods=['POST'])
        def register():
            """Register a new user.
            
            Request Body:
                email: User email (required)
                password: User password (required)
                name: User name (required)
            
            Returns:
                JSON with created user data and auth token
            """
            data = request.get_json()
            
            if not data:
                return jsonify({"error": "Request body is required"}), 400
            
            required_fields = ['email', 'password', 'name']
            for field in required_fields:
                if field not in data or not data[field]:
                    return jsonify({"error": f"Field '{field}' is required"}), 400
            
            # Check for duplicate email
            if any(u['email'] == data['email'] for u in self.users.values()):
                return jsonify({"error": "Email already exists"}), 409
            
            # Create user
            user_id = str(uuid.uuid4())
            new_user = {
                "id": user_id,
                "email": data['email'],
                "password": data['password'],
                "name": data['name'],
                "role": "user",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            
            self.users[user_id] = new_user
            
            # Generate token
            token = str(uuid.uuid4())
            self.auth_tokens[token] = user_id
            
            user_response = {k: v for k, v in new_user.items() if k != 'password'}
            
            return jsonify({
                "token": token,
                "user": user_response
            }), 201
    
    def run(self, debug: bool = False) -> None:
        """Run the Flask server.
        
        Args:
            debug: Enable Flask debug mode (default: False)
        """
        self.app.run(host='0.0.0.0', port=self.port, debug=debug)
    
    def reset(self) -> None:
        """Reset the mock data to initial state."""
        self.users.clear()
        self.auth_tokens.clear()
        self._seed_data()
    
    def get_base_url(self) -> str:
        """Get the base URL for the mock API.
        
        Returns:
            String with the base URL (e.g., "http://localhost:8765")
        """
        return f"http://localhost:{self.port}"


# Global instance for simple usage
_mock_api_instance: Optional[MockAPIServer] = None


def get_mock_api_server(port: int = 8765) -> MockAPIServer:
    """Get or create the global mock API server instance.
    
    Args:
        port: The port number to use (default: 8765)
    
    Returns:
        MockAPIServer instance
    """
    global _mock_api_instance
    if _mock_api_instance is None:
        _mock_api_instance = MockAPIServer(port=port)
    return _mock_api_instance


if __name__ == '__main__':
    # Run the mock API server directly
    print("🚀 Starting Mock API Server...")
    print("📍 URL: http://localhost:8765")
    print("📖 Endpoints:")
    print("   GET    /health")
    print("   GET    /api/users")
    print("   POST   /api/users")
    print("   GET    /api/users/{id}")
    print("   PUT    /api/users/{id}")
    print("   DELETE /api/users/{id}")
    print("   POST   /api/auth/login")
    print("   POST   /api/auth/register")
    print("\nPress Ctrl+C to stop\n")
    
    server = MockAPIServer(port=8765)
    server.run(debug=True)
