#!/usr/bin/env python3
"""
Demo REST API for socialseed-e2e Testing

This is a simple Flask API with CRUD operations for users.
Use this API to test the socialseed-e2e framework before applying it to your own projects.

Usage:
    # Start the API server
    python api-rest-demo.py
    
    # The API will be available at http://localhost:5000
    
Endpoints:
    GET    /health           - Health check
    GET    /api/users        - List all users (with pagination)
    GET    /api/users/<id>   - Get a specific user
    POST   /api/users        - Create a new user
    PUT    /api/users/<id>   - Update a user
    DELETE /api/users/<id>   - Delete a user

Examples:
    # Get all users
    curl http://localhost:5000/api/users
    
    # Get a specific user
    curl http://localhost:5000/api/users/1
    
    # Create a new user
    curl -X POST http://localhost:5000/api/users \\
         -H "Content-Type: application/json" \\
         -d '{"name":"John Doe","email":"john@example.com","role":"user"}'
    
    # Update a user
    curl -X PUT http://localhost:5000/api/users/1 \\
         -H "Content-Type: application/json" \\
         -d '{"name":"Jane Doe"}'
    
    # Delete a user
    curl -X DELETE http://localhost:5000/api/users/1
"""

from flask import Flask, jsonify, request
from datetime import datetime
import uuid

app = Flask(__name__)

# In-memory database with 10 sample users
users_db = {
    "1": {
        "id": "1",
        "name": "Alice Johnson",
        "email": "alice@example.com",
        "role": "admin",
        "department": "Engineering",
        "created_at": "2024-01-15T08:30:00Z",
        "is_active": True
    },
    "2": {
        "id": "2", 
        "name": "Bob Smith",
        "email": "bob@example.com",
        "role": "user",
        "department": "Marketing",
        "created_at": "2024-02-20T10:15:00Z",
        "is_active": True
    },
    "3": {
        "id": "3",
        "name": "Carol Williams",
        "email": "carol@example.com", 
        "role": "user",
        "department": "Sales",
        "created_at": "2024-03-10T14:45:00Z",
        "is_active": True
    },
    "4": {
        "id": "4",
        "name": "David Brown",
        "email": "david@example.com",
        "role": "moderator", 
        "department": "Engineering",
        "created_at": "2024-01-25T09:00:00Z",
        "is_active": True
    },
    "5": {
        "id": "5",
        "name": "Emma Davis",
        "email": "emma@example.com",
        "role": "user",
        "department": "HR",
        "created_at": "2024-04-05T11:20:00Z",
        "is_active": False
    },
    "6": {
        "id": "6",
        "name": "Frank Miller",
        "email": "frank@example.com",
        "role": "user",
        "department": "Engineering",
        "created_at": "2024-02-28T16:30:00Z",
        "is_active": True
    },
    "7": {
        "id": "7",
        "name": "Grace Wilson",
        "email": "grace@example.com",
        "role": "admin",
        "department": "Finance",
        "created_at": "2024-03-15T13:10:00Z",
        "is_active": True
    },
    "8": {
        "id": "8",
        "name": "Henry Moore",
        "email": "henry@example.com",
        "role": "user",
        "department": "Support",
        "created_at": "2024-04-12T08:45:00Z",
        "is_active": True
    },
    "9": {
        "id": "9",
        "name": "Ivy Taylor",
        "email": "ivy@example.com",
        "role": "user",
        "department": "Marketing",
        "created_at": "2024-01-30T15:20:00Z",
        "is_active": True
    },
    "10": {
        "id": "10",
        "name": "Jack Anderson",
        "email": "jack@example.com",
        "role": "moderator",
        "department": "Sales",
        "created_at": "2024-03-22T10:00:00Z",
        "is_active": False
    }
}


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint.
    
    Returns:
        JSON with API status and basic statistics
    """
    return jsonify({
        "status": "healthy",
        "service": "demo-api",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "users_count": len(users_db),
        "active_users": sum(1 for u in users_db.values() if u.get("is_active", False))
    }), 200


@app.route('/api/users', methods=['GET'])
def list_users():
    """List all users with pagination and filtering.
    
    Query Parameters:
        page (int): Page number (default: 1)
        per_page (int): Items per page (default: 10)
        role (str): Filter by role (admin, user, moderator)
        active (bool): Filter by active status
        department (str): Filter by department
        search (str): Search by name or email
        
    Returns:
        JSON with users list and pagination info
    """
    # Get query parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    role = request.args.get('role')
    active = request.args.get('active')
    department = request.args.get('department')
    search = request.args.get('search', '').lower()
    
    # Filter users
    filtered_users = list(users_db.values())
    
    if role:
        filtered_users = [u for u in filtered_users if u.get('role') == role]
    
    if active is not None:
        is_active = active.lower() in ('true', '1', 'yes')
        filtered_users = [u for u in filtered_users if u.get('is_active') == is_active]
    
    if department:
        filtered_users = [u for u in filtered_users if u.get('department', '').lower() == department.lower()]
    
    if search:
        filtered_users = [
            u for u in filtered_users 
            if search in u.get('name', '').lower() or search in u.get('email', '').lower()
        ]
    
    # Calculate pagination
    total = len(filtered_users)
    total_pages = (total + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    
    # Get paginated users
    paginated_users = filtered_users[start:end]
    
    return jsonify({
        "data": paginated_users,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages
        },
        "filters": {
            "role": role,
            "active": active,
            "department": department,
            "search": search if search else None
        }
    }), 200


@app.route('/api/users/<user_id>', methods=['GET'])
def get_user(user_id):
    """Get a specific user by ID.
    
    Args:
        user_id: The ID of the user
        
    Returns:
        JSON with user data or 404 if not found
    """
    if user_id in users_db:
        return jsonify({"data": users_db[user_id]}), 200
    else:
        return jsonify({
            "error": "User not found",
            "message": f"No user found with ID: {user_id}"
        }), 404


@app.route('/api/users', methods=['POST'])
def create_user():
    """Create a new user.
    
    Request Body:
        name (str): User's full name (required)
        email (str): User's email address (required)
        role (str): User role - admin, user, or moderator (default: user)
        department (str): User's department (optional)
        
    Returns:
        JSON with created user data (201) or error (400)
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            "error": "Invalid request",
            "message": "Request body must be valid JSON"
        }), 400
    
    # Validate required fields
    if not data.get('name'):
        return jsonify({
            "error": "Validation error",
            "message": "Field 'name' is required"
        }), 400
    
    if not data.get('email'):
        return jsonify({
            "error": "Validation error", 
            "message": "Field 'email' is required"
        }), 400
    
    # Check for duplicate email
    existing = [u for u in users_db.values() if u.get('email') == data.get('email')]
    if existing:
        return jsonify({
            "error": "Conflict",
            "message": f"User with email '{data.get('email')}' already exists"
        }), 409
    
    # Generate new ID
    new_id = str(max([int(k) for k in users_db.keys()]) + 1)
    
    # Create new user
    new_user = {
        "id": new_id,
        "name": data.get('name'),
        "email": data.get('email'),
        "role": data.get('role', 'user'),
        "department": data.get('department', 'General'),
        "created_at": datetime.utcnow().isoformat() + "Z",
        "is_active": data.get('is_active', True)
    }
    
    users_db[new_id] = new_user
    
    return jsonify({
        "message": "User created successfully",
        "data": new_user
    }), 201


@app.route('/api/users/<user_id>', methods=['PUT'])
def update_user(user_id):
    """Update an existing user.
    
    Args:
        user_id: The ID of the user to update
        
    Request Body:
        name (str): User's full name (optional)
        email (str): User's email address (optional)
        role (str): User role (optional)
        department (str): User's department (optional)
        is_active (bool): User active status (optional)
        
    Returns:
        JSON with updated user data (200), 404 if not found, or 400 on error
    """
    if user_id not in users_db:
        return jsonify({
            "error": "User not found",
            "message": f"No user found with ID: {user_id}"
        }), 404
    
    data = request.get_json()
    
    if not data:
        return jsonify({
            "error": "Invalid request",
            "message": "Request body must be valid JSON"
        }), 400
    
    user = users_db[user_id]
    
    # Update allowed fields
    allowed_fields = ['name', 'email', 'role', 'department', 'is_active']
    for field in allowed_fields:
        if field in data:
            # Validate email uniqueness if being changed
            if field == 'email':
                existing = [u for u in users_db.values() 
                          if u.get('email') == data[field] and u['id'] != user_id]
                if existing:
                    return jsonify({
                        "error": "Conflict",
                        "message": f"Email '{data[field]}' is already in use"
                    }), 409
            
            user[field] = data[field]
    
    return jsonify({
        "message": "User updated successfully",
        "data": user
    }), 200


@app.route('/api/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete a user.
    
    Args:
        user_id: The ID of the user to delete
        
    Returns:
        204 No Content on success, 404 if not found
    """
    if user_id not in users_db:
        return jsonify({
            "error": "User not found",
            "message": f"No user found with ID: {user_id}"
        }), 404
    
    deleted_user = users_db.pop(user_id)
    
    return jsonify({
        "message": "User deleted successfully",
        "data": {
            "id": user_id,
            "name": deleted_user.get('name')
        }
    }), 200


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get API statistics.
    
    Returns:
        JSON with various statistics about users
    """
    total_users = len(users_db)
    active_users = sum(1 for u in users_db.values() if u.get('is_active', False))
    inactive_users = total_users - active_users
    
    # Count by role
    roles = {}
    for user in users_db.values():
        role = user.get('role', 'unknown')
        roles[role] = roles.get(role, 0) + 1
    
    # Count by department
    departments = {}
    for user in users_db.values():
        dept = user.get('department', 'Unknown')
        departments[dept] = departments.get(dept, 0) + 1
    
    return jsonify({
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": inactive_users,
        "roles": roles,
        "departments": departments
    }), 200


if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Demo REST API for socialseed-e2e Testing")
    print("=" * 60)
    print("\n📍 API URL: http://localhost:5000")
    print("📖 Documentation: http://localhost:5000/")
    print("\nAvailable endpoints:")
    print("  GET    /health           - Health check")
    print("  GET    /api/users        - List users (with filters)")
    print("  GET    /api/users/<id>   - Get user by ID")
    print("  POST   /api/users        - Create user")
    print("  PUT    /api/users/<id>   - Update user")
    print("  DELETE /api/users/<id>   - Delete user")
    print("  GET    /api/stats        - Get statistics")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60 + "\n")
    
    # Run the Flask app
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=False  # Disable reloader to prevent double startup
    )
