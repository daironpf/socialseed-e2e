#!/usr/bin/env python3
"""Auth Demo API for socialseed-e2e Testing

This is a simple Flask API with JWT Bearer token authentication.
Use this API to test authentication and authorization in socialseed-e2e.

Usage:
    # Install required packages first
    pip install flask pyjwt cryptography
    
    # Start the Auth server
    python api-auth-demo.py
    
    # The API will be available at http://localhost:5003

Endpoints:
    POST /auth/login         - Login and get JWT token
    POST /auth/register     - Register a new user
    POST /auth/refresh      - Refresh access token
    GET  /auth/me           - Get current user info (requires auth)
    GET  /auth/admin       - Admin-only endpoint (requires admin role)
    GET  /health            - Health check (public)

Authentication:
    Include the JWT token in the Authorization header:
        Authorization: Bearer <your_token>

Examples:
    # Login
    curl -X POST http://localhost:5003/auth/login \\
         -H "Content-Type: application/json" \\
         -d '{"username":"admin","password":"admin123"}'
    
    # Get current user (replace <token> with actual token)
    curl http://localhost:5003/auth/me \\
         -H "Authorization: Bearer <token>"
    
    # Access admin endpoint (requires admin role)
    curl http://localhost:5003/auth/admin \\
         -H "Authorization: Bearer <token>"
"""

from flask import Flask, jsonify, request
from datetime import datetime, timedelta
import jwt
import uuid
import hashlib
import os

app = Flask(__name__)

# Secret key for JWT signing (in production, use environment variable)
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# In-memory user database
users_db = {
    "admin": {
        "id": "1",
        "username": "admin",
        "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
        "email": "admin@example.com",
        "role": "admin",
        "created_at": "2024-01-01T00:00:00Z"
    },
    "user1": {
        "id": "2",
        "username": "user1",
        "password_hash": hashlib.sha256("user123".encode()).hexdigest(),
        "email": "user1@example.com",
        "role": "user",
        "created_at": "2024-01-15T00:00:00Z"
    },
    "moderator1": {
        "id": "3",
        "username": "moderator1",
        "password_hash": hashlib.sha256("mod123".encode()).hexdigest(),
        "email": "mod1@example.com",
        "role": "moderator",
        "created_at": "2024-02-01T00:00:00Z"
    }
}

# Active tokens (in production, use Redis or database)
active_tokens = set()


def generate_tokens(user):
    """Generate access and refresh tokens for a user"""
    access_token_exp = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_exp = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    access_payload = {
        "sub": user["username"],
        "user_id": user["id"],
        "role": user["role"],
        "exp": access_token_exp,
        "type": "access"
    }
    
    refresh_payload = {
        "sub": user["username"],
        "user_id": user["id"],
        "exp": refresh_token_exp,
        "type": "refresh"
    }
    
    access_token = jwt.encode(access_payload, SECRET_KEY, algorithm=ALGORITHM)
    refresh_token = jwt.encode(refresh_payload, SECRET_KEY, algorithm=ALGORITHM)
    
    return access_token, refresh_token


def verify_token(token):
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload["type"] != "access":
            return None
        if token in active_tokens or token not in active_tokens:
            return payload
        return None
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def require_auth(f):
    """Decorator to require authentication"""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Missing Authorization header"}), 401
        
        parts = auth_header.split()
        if len(parts) != 2 or parts[0] != "Bearer":
            return jsonify({"error": "Invalid Authorization header format"}), 401
        
        token = parts[1]
        payload = verify_token(token)
        
        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401
        
        request.user = payload
        return f(*args, **kwargs)
    return decorated


def require_role(role):
    """Decorator to require a specific role"""
    def decorator(f):
        @require_auth
        def decorated(*args, **kwargs):
            if request.user.get("role") != role:
                return jsonify({"error": "Insufficient permissions"}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator


@app.route('/health', methods=['GET'])
def health_check():
    """Public health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "auth-demo",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }), 200


@app.route('/auth/login', methods=['POST'])
def login():
    """Login endpoint - returns JWT tokens"""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Invalid request body"}), 400
    
    username = data.get("username")
    password = data.get("password")
    
    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400
    
    user = users_db.get(username)
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    if password_hash != user["password_hash"]:
        return jsonify({"error": "Invalid credentials"}), 401
    
    access_token, refresh_token = generate_tokens(user)
    active_tokens.add(access_token)
    
    return jsonify({
        "message": "Login successful",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "role": user["role"]
        }
    }), 200


@app.route('/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Invalid request body"}), 400
    
    username = data.get("username")
    password = data.get("password")
    email = data.get("email")
    
    if not username or not password or not email:
        return jsonify({"error": "Username, password, and email are required"}), 400
    
    if username in users_db:
        return jsonify({"error": "Username already exists"}), 409
    
    new_id = str(len(users_db) + 1)
    new_user = {
        "id": new_id,
        "username": username,
        "password_hash": hashlib.sha256(password.encode()).hexdigest(),
        "email": email,
        "role": "user",
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    
    users_db[username] = new_user
    
    return jsonify({
        "message": "User registered successfully",
        "user": {
            "id": new_user["id"],
            "username": new_user["username"],
            "email": new_user["email"],
            "role": new_user["role"]
        }
    }), 201


@app.route('/auth/refresh', methods=['POST'])
def refresh():
    """Refresh access token using refresh token"""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Invalid request body"}), 400
    
    refresh_token = data.get("refresh_token")
    
    if not refresh_token:
        return jsonify({"error": "Refresh token is required"}), 400
    
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            return jsonify({"error": "Invalid token type"}), 401
        
        username = payload.get("sub")
        user = users_db.get(username)
        
        if not user:
            return jsonify({"error": "User not found"}), 401
        
        access_token, new_refresh_token = generate_tokens(user)
        active_tokens.add(access_token)
        
        return jsonify({
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "Bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }), 200
        
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Refresh token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid refresh token"}), 401


@app.route('/auth/me', methods=['GET'])
@require_auth
def get_current_user():
    """Get current authenticated user info"""
    username = request.user.get("sub")
    user = users_db.get(username)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify({
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "role": user["role"],
        "created_at": user["created_at"]
    }), 200


@app.route('/auth/admin', methods=['GET'])
@require_role("admin")
def admin_only():
    """Admin-only endpoint"""
    return jsonify({
        "message": "Welcome, admin!",
        "secret_data": "This is admin-only content",
        "all_users": [
            {
                "id": u["id"],
                "username": u["username"],
                "email": u["email"],
                "role": u["role"]
            }
            for u in users_db.values()
        ]
    }), 200


@app.route('/auth/logout', methods=['POST'])
@require_auth
def logout():
    """Logout - invalidate current token"""
    auth_header = request.headers.get("Authorization")
    token = auth_header.split()[1] if auth_header else None
    
    if token:
        active_tokens.discard(token)
    
    return jsonify({"message": "Logout successful"}), 200


if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Auth Demo API for socialseed-e2e Testing")
    print("=" * 60)
    print("\n📍 API URL: http://localhost:5003")
    print("\nDefault users:")
    print("  admin / admin123 (role: admin)")
    print("  user1 / user123 (role: user)")
    print("  moderator1 / mod123 (role: moderator)")
    print("\nAvailable endpoints:")
    print("  POST /auth/login      - Login")
    print("  POST /auth/register  - Register new user")
    print("  POST /auth/refresh   - Refresh token")
    print("  GET  /auth/me        - Get current user (auth required)")
    print("  GET  /auth/admin     - Admin only (admin required)")
    print("  POST /auth/logout    - Logout")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60 + "\n")
    
    app.run(host='0.0.0.0', port=5003, debug=True)
