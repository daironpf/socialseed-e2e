"""
Users Service - Microservice Example.

Manages user accounts, balances, and user information.
Port: 5002
"""

import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify, g

app = Flask(__name__)
DATABASE = "users.db"


def get_db():
    """Get database connection."""
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    """Close database connection."""
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def init_db():
    """Initialize database with users table."""
    with app.app_context():
        db = get_db()
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                balance REAL DEFAULT 100.00,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.commit()

        # Add sample users if table is empty
        cursor = db.execute("SELECT COUNT(*) as count FROM users")
        if cursor.fetchone()["count"] == 0:
            sample_users = [
                ("alice", "alice@example.com", 500.00),
                ("bob", "bob@example.com", 300.00),
                ("charlie", "charlie@example.com", 150.00),
            ]
            for username, email, balance in sample_users:
                db.execute(
                    "INSERT INTO users (username, email, balance) VALUES (?, ?, ?)",
                    (username, email, balance),
                )
            db.commit()


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "users-service", "port": 5002})


@app.route("/api/users", methods=["GET"])
def list_users():
    """List all users."""
    db = get_db()
    cursor = db.execute("SELECT id, username, email, balance FROM users")
    users = [dict(row) for row in cursor.fetchall()]
    return jsonify({"users": users})


@app.route("/api/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    """Get user by ID."""
    db = get_db()
    cursor = db.execute(
        "SELECT id, username, email, balance FROM users WHERE id = ?", (user_id,)
    )
    user = cursor.fetchone()

    if not user:
        return jsonify(
            {"error": "Not Found", "message": f"User with id {user_id} not found"}
        ), 404

    return jsonify(dict(user))


@app.route("/api/users/<int:user_id>/balance", methods=["GET"])
def get_balance(user_id):
    """Get user balance (used by other services)."""
    db = get_db()
    cursor = db.execute(
        "SELECT id, username, balance FROM users WHERE id = ?", (user_id,)
    )
    user = cursor.fetchone()

    if not user:
        return jsonify(
            {"error": "Not Found", "message": f"User with id {user_id} not found"}
        ), 404

    return jsonify(
        {
            "user_id": user["id"],
            "username": user["username"],
            "balance": user["balance"],
        }
    )


@app.route("/api/users/<int:user_id>/balance", methods=["POST"])
def update_balance(user_id):
    """Update user balance (used by payment service).

    Request body: {"amount": -50.00}  # negative to deduct, positive to add
    """
    data = request.get_json()

    if not data or "amount" not in data:
        return jsonify({"error": "Bad Request", "message": "amount is required"}), 400

    amount = float(data["amount"])

    db = get_db()

    # Check user exists and has sufficient balance
    cursor = db.execute("SELECT balance FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()

    if not user:
        return jsonify(
            {"error": "Not Found", "message": f"User with id {user_id} not found"}
        ), 404

    current_balance = user["balance"]
    new_balance = current_balance + amount

    if new_balance < 0:
        return jsonify(
            {
                "error": "Insufficient Funds",
                "message": f"User has insufficient balance. Current: {current_balance}, Required: {abs(amount)}",
            }
        ), 400

    # Update balance
    db.execute("UPDATE users SET balance = ? WHERE id = ?", (new_balance, user_id))
    db.commit()

    return jsonify(
        {
            "message": "Balance updated successfully",
            "user_id": user_id,
            "previous_balance": current_balance,
            "amount_changed": amount,
            "new_balance": new_balance,
        }
    )


@app.route("/api/users", methods=["POST"])
def create_user():
    """Create a new user."""
    data = request.get_json()

    if not data:
        return jsonify(
            {"error": "Bad Request", "message": "Request body is required"}
        ), 400

    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    balance = float(data.get("balance", 100.00))

    if not username or not email:
        return jsonify(
            {"error": "Bad Request", "message": "username and email are required"}
        ), 400

    db = get_db()
    try:
        cursor = db.execute(
            "INSERT INTO users (username, email, balance) VALUES (?, ?, ?)",
            (username, email, balance),
        )
        db.commit()

        return jsonify(
            {
                "message": "User created successfully",
                "user": {
                    "id": cursor.lastrowid,
                    "username": username,
                    "email": email,
                    "balance": balance,
                },
            }
        ), 201

    except sqlite3.IntegrityError:
        return jsonify(
            {"error": "Conflict", "message": "Username or email already exists"}
        ), 409


if __name__ == "__main__":
    init_db()
    print("👤 Users Service starting on http://localhost:5002")
    print("   Pre-loaded with 3 sample users: alice($500), bob($300), charlie($150)")
    print("\nPress Ctrl+C to stop")
    app.run(host="0.0.0.0", port=5002, debug=True)
