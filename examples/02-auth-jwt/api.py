"""
JWT Authentication API Example.

This API demonstrates JWT-based authentication with:
- User registration
- User login (with access and refresh tokens)
- Token refresh
- Protected endpoints

Run with: python api.py
"""

import sqlite3
from datetime import datetime, timedelta
from functools import wraps
from typing import Optional

from flask import Flask, request, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash
import jwt

app = Flask(__name__)

# Configuration
app.config["SECRET_KEY"] = "your-secret-key-change-in-production"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=15)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=7)
app.config["DATABASE"] = "auth.db"


# JWT Token utilities
def generate_tokens(user_id: int, username: str) -> dict:
    """Generate access and refresh tokens."""
    now = datetime.utcnow()

    # Access token (short-lived)
    access_payload = {
        "user_id": user_id,
        "username": username,
        "type": "access",
        "exp": now + app.config["JWT_ACCESS_TOKEN_EXPIRES"],
        "iat": now,
    }
    access_token = jwt.encode(
        access_payload, app.config["SECRET_KEY"], algorithm="HS256"
    )

    # Refresh token (long-lived)
    refresh_payload = {
        "user_id": user_id,
        "username": username,
        "type": "refresh",
        "exp": now + app.config["JWT_REFRESH_TOKEN_EXPIRES"],
        "iat": now,
    }
    refresh_token = jwt.encode(
        refresh_payload, app.config["SECRET_KEY"], algorithm="HS256"
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
        "expires_in": int(app.config["JWT_ACCESS_TOKEN_EXPIRES"].total_seconds()),
    }


def decode_token(token: str, token_type: str = "access") -> Optional[dict]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])

        # Verify token type
        if payload.get("type") != token_type:
            return None

        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_db():
    """Get database connection."""
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(app.config["DATABASE"])
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    """Close database connection."""
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def init_db():
    """Initialize the database with users table."""
    with app.app_context():
        db = get_db()
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.commit()


def require_auth(f):
    """Decorator to require JWT authentication."""

    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return jsonify(
                {"error": "Unauthorized", "message": "Authorization header is required"}
            ), 401

        # Extract token from "Bearer <token>"
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return jsonify(
                {
                    "error": "Unauthorized",
                    "message": "Invalid authorization header format. Use: Bearer <token>",
                }
            ), 401

        token = parts[1]
        payload = decode_token(token, "access")

        if not payload:
            return jsonify(
                {"error": "Unauthorized", "message": "Invalid or expired token"}
            ), 401

        # Store user info in flask g for use in the endpoint
        g.user_id = payload["user_id"]
        g.username = payload["username"]

        return f(*args, **kwargs)

    return decorated


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "auth-api", "auth_type": "JWT"})


@app.route("/api/auth/register", methods=["POST"])
def register():
    """Register a new user."""
    data = request.get_json()

    # Validate required fields
    if not data:
        return jsonify(
            {"error": "Bad Request", "message": "Request body is required"}
        ), 400

    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "")

    # Validation
    errors = []
    if not username or len(username) < 3:
        errors.append("Username must be at least 3 characters")
    if not email or "@" not in email:
        errors.append("Valid email is required")
    if not password or len(password) < 6:
        errors.append("Password must be at least 6 characters")

    if errors:
        return jsonify(
            {
                "error": "Validation Error",
                "message": "Invalid input data",
                "details": errors,
            }
        ), 400

    # Hash password
    password_hash = generate_password_hash(password)

    # Insert user
    db = get_db()
    try:
        cursor = db.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, password_hash),
        )
        db.commit()

        user_id = cursor.lastrowid

        return jsonify(
            {
                "message": "User registered successfully",
                "user": {"id": user_id, "username": username, "email": email},
            }
        ), 201

    except sqlite3.IntegrityError as e:
        if "username" in str(e).lower():
            return jsonify(
                {"error": "Conflict", "message": "Username already exists"}
            ), 409
        elif "email" in str(e).lower():
            return jsonify(
                {"error": "Conflict", "message": "Email already exists"}
            ), 409
        else:
            return jsonify({"error": "Conflict", "message": "User already exists"}), 409


@app.route("/api/auth/login", methods=["POST"])
def login():
    """Login and receive JWT tokens."""
    data = request.get_json()

    if not data:
        return jsonify(
            {"error": "Bad Request", "message": "Request body is required"}
        ), 400

    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify(
            {"error": "Bad Request", "message": "Username and password are required"}
        ), 400

    # Find user
    db = get_db()
    cursor = db.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()

    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify(
            {"error": "Unauthorized", "message": "Invalid username or password"}
        ), 401

    # Generate tokens
    tokens = generate_tokens(user["id"], user["username"])

    return jsonify(
        {
            "message": "Login successful",
            "user": {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
            },
            "tokens": tokens,
        }
    )


@app.route("/api/auth/refresh", methods=["POST"])
def refresh():
    """Refresh access token using refresh token."""
    data = request.get_json()

    if not data or "refresh_token" not in data:
        return jsonify(
            {"error": "Bad Request", "message": "Refresh token is required"}
        ), 400

    refresh_token = data["refresh_token"]
    payload = decode_token(refresh_token, "refresh")

    if not payload:
        return jsonify(
            {"error": "Unauthorized", "message": "Invalid or expired refresh token"}
        ), 401

    # Verify user still exists
    db = get_db()
    cursor = db.execute("SELECT * FROM users WHERE id = ?", (payload["user_id"],))
    user = cursor.fetchone()

    if not user:
        return jsonify(
            {"error": "Unauthorized", "message": "User no longer exists"}
        ), 401

    # Generate new tokens
    tokens = generate_tokens(user["id"], user["username"])

    return jsonify({"message": "Token refreshed successfully", "tokens": tokens})


@app.route("/api/protected", methods=["GET"])
@require_auth
def protected():
    """Protected endpoint requiring JWT authentication."""
    return jsonify(
        {
            "message": "Access granted to protected resource",
            "user": {"id": g.user_id, "username": g.username},
            "data": {
                "secret": "This is protected data only visible to authenticated users",
                "timestamp": datetime.utcnow().isoformat(),
            },
        }
    )


@app.route("/api/profile", methods=["GET"])
@require_auth
def get_profile():
    """Get current user profile."""
    db = get_db()
    cursor = db.execute(
        "SELECT id, username, email, created_at FROM users WHERE id = ?", (g.user_id,)
    )
    user = cursor.fetchone()

    if not user:
        return jsonify({"error": "Not Found", "message": "User not found"}), 404

    return jsonify({"user": dict(user)})


if __name__ == "__main__":
    init_db()
    print("🔐 Starting JWT Auth API on http://localhost:5001")
    print("📚 Endpoints:")
    print("   POST /api/auth/register  - Register new user")
    print("   POST /api/auth/login     - Login and get tokens")
    print("   POST /api/auth/refresh   - Refresh access token")
    print("   GET  /api/protected      - Protected endpoint (requires auth)")
    print("   GET  /api/profile        - Get user profile (requires auth)")
    print("   GET  /health             - Health check")
    print("\nPress Ctrl+C to stop")
    app.run(host="0.0.0.0", port=5001, debug=True)
