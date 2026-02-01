"""
Orders Service - Microservice Example.

Manages orders and depends on Users Service for validation.
Port: 5003
"""

import sqlite3
from datetime import datetime
import requests
from flask import Flask, request, jsonify, g

app = Flask(__name__)
DATABASE = "orders.db"

# Users service URL
USERS_SERVICE_URL = "http://localhost:5002"


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
    """Initialize database with orders table."""
    with app.app_context():
        db = get_db()
        db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                items TEXT NOT NULL,
                total_amount REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.commit()


def validate_user(user_id):
    """Validate user exists by calling Users Service."""
    try:
        response = requests.get(f"{USERS_SERVICE_URL}/api/users/{user_id}", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except requests.RequestException:
        return None


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    # Check if users service is available
    users_service_status = "healthy"
    try:
        response = requests.get(f"{USERS_SERVICE_URL}/health", timeout=2)
        if response.status_code != 200:
            users_service_status = "unavailable"
    except requests.RequestException:
        users_service_status = "unavailable"

    return jsonify(
        {
            "status": "healthy",
            "service": "orders-service",
            "port": 5003,
            "dependencies": {"users-service": users_service_status},
        }
    )


@app.route("/api/orders", methods=["POST"])
def create_order():
    """Create a new order.

    Validates user exists by calling Users Service.
    """
    data = request.get_json()

    if not data:
        return jsonify(
            {"error": "Bad Request", "message": "Request body is required"}
        ), 400

    user_id = data.get("user_id")
    items = data.get("items")
    total_amount = data.get("total_amount")

    if not user_id or not items or total_amount is None:
        return jsonify(
            {
                "error": "Bad Request",
                "message": "user_id, items, and total_amount are required",
            }
        ), 400

    # Validate user exists (call Users Service)
    user = validate_user(user_id)
    if not user:
        return jsonify(
            {"error": "Not Found", "message": f"User with id {user_id} not found"}
        ), 404

    # Create order
    db = get_db()
    cursor = db.execute(
        "INSERT INTO orders (user_id, items, total_amount) VALUES (?, ?, ?)",
        (user_id, str(items), float(total_amount)),
    )
    db.commit()

    return jsonify(
        {
            "message": "Order created successfully",
            "order": {
                "id": cursor.lastrowid,
                "user_id": user_id,
                "user_name": user.get("username"),
                "items": items,
                "total_amount": float(total_amount),
                "status": "pending",
            },
        }
    ), 201


@app.route("/api/orders", methods=["GET"])
def list_orders():
    """List all orders with optional user filter."""
    user_id = request.args.get("user_id", type=int)

    db = get_db()

    if user_id:
        cursor = db.execute(
            "SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        )
    else:
        cursor = db.execute("SELECT * FROM orders ORDER BY created_at DESC")

    orders = []
    for row in cursor.fetchall():
        order = dict(row)
        # Try to enrich with user data
        try:
            user_response = requests.get(
                f"{USERS_SERVICE_URL}/api/users/{order['user_id']}", timeout=2
            )
            if user_response.status_code == 200:
                user_data = user_response.json()
                order["user_name"] = user_data.get("username")
        except:
            order["user_name"] = "Unknown"
        orders.append(order)

    return jsonify({"orders": orders})


@app.route("/api/orders/<int:order_id>", methods=["GET"])
def get_order(order_id):
    """Get order by ID."""
    db = get_db()
    cursor = db.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
    order = cursor.fetchone()

    if not order:
        return jsonify(
            {"error": "Not Found", "message": f"Order with id {order_id} not found"}
        ), 404

    order_dict = dict(order)

    # Enrich with user data
    try:
        user_response = requests.get(
            f"{USERS_SERVICE_URL}/api/users/{order_dict['user_id']}", timeout=2
        )
        if user_response.status_code == 200:
            user_data = user_response.json()
            order_dict["user"] = user_data
    except:
        pass

    return jsonify(order_dict)


@app.route("/api/orders/<int:order_id>/status", methods=["PUT"])
def update_order_status(order_id):
    """Update order status."""
    data = request.get_json()

    if not data or "status" not in data:
        return jsonify({"error": "Bad Request", "message": "status is required"}), 400

    new_status = data["status"]
    valid_statuses = ["pending", "confirmed", "shipped", "delivered", "cancelled"]

    if new_status not in valid_statuses:
        return jsonify(
            {
                "error": "Bad Request",
                "message": f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
            }
        ), 400

    db = get_db()

    # Check order exists
    cursor = db.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
    if not cursor.fetchone():
        return jsonify(
            {"error": "Not Found", "message": f"Order with id {order_id} not found"}
        ), 404

    # Update status
    db.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
    db.commit()

    return jsonify(
        {
            "message": "Order status updated",
            "order_id": order_id,
            "new_status": new_status,
        }
    )


@app.route("/api/users/<int:user_id>/orders", methods=["GET"])
def get_user_orders(user_id):
    """Get all orders for a specific user."""
    # Validate user exists
    user = validate_user(user_id)
    if not user:
        return jsonify(
            {"error": "Not Found", "message": f"User with id {user_id} not found"}
        ), 404

    db = get_db()
    cursor = db.execute(
        "SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC", (user_id,)
    )
    orders = [dict(row) for row in cursor.fetchall()]

    return jsonify(
        {"user_id": user_id, "user_name": user.get("username"), "orders": orders}
    )


if __name__ == "__main__":
    init_db()
    print("📦 Orders Service starting on http://localhost:5003")
    print(f"   Depends on: Users Service ({USERS_SERVICE_URL})")
    print("\nPress Ctrl+C to stop")
    app.run(host="0.0.0.0", port=5003, debug=True)
