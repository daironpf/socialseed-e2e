"""
Payment Service - Microservice Example.

Processes payments and depends on both Users and Orders Services.
Port: 5004
"""

import sqlite3
from datetime import datetime
import requests
from flask import Flask, request, jsonify, g

app = Flask(__name__)
DATABASE = "payments.db"

# Other services URLs
USERS_SERVICE_URL = "http://localhost:5002"
ORDERS_SERVICE_URL = "http://localhost:5003"


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
    """Initialize database with payments table."""
    with app.app_context():
        db = get_db()
        db.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                transaction_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.commit()


def get_user_balance(user_id):
    """Get user balance from Users Service."""
    try:
        response = requests.get(
            f"{USERS_SERVICE_URL}/api/users/{user_id}/balance", timeout=5
        )
        if response.status_code == 200:
            return response.json()
        return None
    except requests.RequestException:
        return None


def update_user_balance(user_id, amount):
    """Update user balance via Users Service."""
    try:
        response = requests.post(
            f"{USERS_SERVICE_URL}/api/users/{user_id}/balance",
            json={"amount": amount},
            timeout=5,
        )
        return (
            response.status_code == 200,
            response.json() if response.status_code == 200 else None,
        )
    except requests.RequestException:
        return False, None


def get_order(order_id):
    """Get order from Orders Service."""
    try:
        response = requests.get(
            f"{ORDERS_SERVICE_URL}/api/orders/{order_id}", timeout=5
        )
        if response.status_code == 200:
            return response.json()
        return None
    except requests.RequestException:
        return None


def update_order_status(order_id, status):
    """Update order status via Orders Service."""
    try:
        response = requests.put(
            f"{ORDERS_SERVICE_URL}/api/orders/{order_id}/status",
            json={"status": status},
            timeout=5,
        )
        return response.status_code == 200
    except requests.RequestException:
        return False


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    # Check dependencies
    users_status = "healthy"
    orders_status = "healthy"

    try:
        response = requests.get(f"{USERS_SERVICE_URL}/health", timeout=2)
        if response.status_code != 200:
            users_status = "unavailable"
    except:
        users_status = "unavailable"

    try:
        response = requests.get(f"{ORDERS_SERVICE_URL}/health", timeout=2)
        if response.status_code != 200:
            orders_status = "unavailable"
    except:
        orders_status = "unavailable"

    return jsonify(
        {
            "status": "healthy",
            "service": "payment-service",
            "port": 5004,
            "dependencies": {
                "users-service": users_status,
                "orders-service": orders_status,
            },
        }
    )


@app.route("/api/payments", methods=["POST"])
def process_payment():
    """Process a payment.

    Requires:
    - Valid order
    - Sufficient user balance
    """
    data = request.get_json()

    if not data:
        return jsonify(
            {"error": "Bad Request", "message": "Request body is required"}
        ), 400

    order_id = data.get("order_id")
    user_id = data.get("user_id")

    if not order_id or not user_id:
        return jsonify(
            {"error": "Bad Request", "message": "order_id and user_id are required"}
        ), 400

    # Get order details
    order = get_order(order_id)
    if not order:
        return jsonify(
            {"error": "Not Found", "message": f"Order with id {order_id} not found"}
        ), 404

    # Verify order belongs to user
    if order.get("user_id") != user_id:
        return jsonify(
            {"error": "Forbidden", "message": "Order does not belong to this user"}
        ), 403

    # Get amount from order
    amount = order.get("total_amount", 0)

    # Check user balance
    user_balance = get_user_balance(user_id)
    if not user_balance:
        return jsonify(
            {"error": "Not Found", "message": f"User with id {user_id} not found"}
        ), 404

    if user_balance["balance"] < amount:
        return jsonify(
            {
                "error": "Insufficient Funds",
                "message": f"Insufficient balance. Current: ${user_balance['balance']:.2f}, Required: ${amount:.2f}",
            }
        ), 400

    # Deduct balance from user
    success, balance_response = update_user_balance(user_id, -amount)
    if not success:
        return jsonify(
            {
                "error": "Payment Failed",
                "message": "Failed to deduct balance from user account",
            }
        ), 500

    # Create payment record
    db = get_db()
    cursor = db.execute(
        """INSERT INTO payments (order_id, user_id, amount, status, transaction_id)
           VALUES (?, ?, ?, ?, ?)""",
        (order_id, user_id, amount, "completed", f"txn_{datetime.now().timestamp()}"),
    )
    db.commit()

    payment_id = cursor.lastrowid

    # Update order status to confirmed
    update_order_status(order_id, "confirmed")

    return jsonify(
        {
            "message": "Payment processed successfully",
            "payment": {
                "id": payment_id,
                "order_id": order_id,
                "user_id": user_id,
                "amount": amount,
                "status": "completed",
                "previous_balance": user_balance["balance"],
                "new_balance": balance_response.get(
                    "new_balance", user_balance["balance"] - amount
                ),
            },
        }
    ), 201


@app.route("/api/payments", methods=["GET"])
def list_payments():
    """List all payments."""
    user_id = request.args.get("user_id", type=int)

    db = get_db()

    if user_id:
        cursor = db.execute(
            "SELECT * FROM payments WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        )
    else:
        cursor = db.execute("SELECT * FROM payments ORDER BY created_at DESC")

    payments = [dict(row) for row in cursor.fetchall()]
    return jsonify({"payments": payments})


@app.route("/api/payments/<int:payment_id>", methods=["GET"])
def get_payment(payment_id):
    """Get payment by ID."""
    db = get_db()
    cursor = db.execute("SELECT * FROM payments WHERE id = ?", (payment_id,))
    payment = cursor.fetchone()

    if not payment:
        return jsonify(
            {"error": "Not Found", "message": f"Payment with id {payment_id} not found"}
        ), 404

    return jsonify(dict(payment))


@app.route("/api/users/<int:user_id>/payments", methods=["GET"])
def get_user_payments(user_id):
    """Get all payments for a specific user."""
    db = get_db()
    cursor = db.execute(
        "SELECT * FROM payments WHERE user_id = ? ORDER BY created_at DESC", (user_id,)
    )
    payments = [dict(row) for row in cursor.fetchall()]

    # Get user info
    user_balance = get_user_balance(user_id)
    user_name = user_balance.get("username", "Unknown") if user_balance else "Unknown"

    return jsonify({"user_id": user_id, "user_name": user_name, "payments": payments})


@app.route("/api/refund", methods=["POST"])
def refund_payment():
    """Refund a payment.

    Requires payment_id.
    """
    data = request.get_json()

    if not data or "payment_id" not in data:
        return jsonify(
            {"error": "Bad Request", "message": "payment_id is required"}
        ), 400

    payment_id = data["payment_id"]

    db = get_db()

    # Get payment details
    cursor = db.execute("SELECT * FROM payments WHERE id = ?", (payment_id,))
    payment = cursor.fetchone()

    if not payment:
        return jsonify(
            {"error": "Not Found", "message": f"Payment with id {payment_id} not found"}
        ), 404

    payment_dict = dict(payment)

    if payment_dict["status"] != "completed":
        return jsonify(
            {
                "error": "Bad Request",
                "message": f"Cannot refund payment with status: {payment_dict['status']}",
            }
        ), 400

    # Refund to user balance
    success, _ = update_user_balance(payment_dict["user_id"], payment_dict["amount"])
    if not success:
        return jsonify(
            {"error": "Refund Failed", "message": "Failed to refund to user account"}
        ), 500

    # Update payment status
    db.execute("UPDATE payments SET status = 'refunded' WHERE id = ?", (payment_id,))
    db.commit()

    # Update order status back to pending
    update_order_status(payment_dict["order_id"], "pending")

    return jsonify(
        {
            "message": "Payment refunded successfully",
            "payment_id": payment_id,
            "refund_amount": payment_dict["amount"],
        }
    )


if __name__ == "__main__":
    init_db()
    print("💳 Payment Service starting on http://localhost:5004")
    print(f"   Depends on: Users Service ({USERS_SERVICE_URL})")
    print(f"   Depends on: Orders Service ({ORDERS_SERVICE_URL})")
    print("\nPress Ctrl+C to stop")
    app.run(host="0.0.0.0", port=5004, debug=True)
