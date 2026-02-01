"""
Simple Flask API for CRUD operations example.

This API demonstrates basic CRUD operations with SQLite backend.
Run with: python api.py
"""

import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify, g

app = Flask(__name__)
DATABASE = "items.db"


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
    """Initialize the database with items table."""
    with app.app_context():
        db = get_db()
        db.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.commit()


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "items-api"})


@app.route("/api/items", methods=["POST"])
def create_item():
    """Create a new item."""
    data = request.get_json()

    # Validate required fields
    if not data or "name" not in data or "price" not in data:
        return jsonify(
            {"error": "Bad Request", "message": "Name and price are required fields"}
        ), 400

    name = data.get("name")
    description = data.get("description", "")
    price = float(data.get("price", 0))
    quantity = int(data.get("quantity", 0))

    db = get_db()
    cursor = db.execute(
        """INSERT INTO items (name, description, price, quantity)
           VALUES (?, ?, ?, ?)""",
        (name, description, price, quantity),
    )
    db.commit()

    item_id = cursor.lastrowid

    return jsonify(
        {
            "id": item_id,
            "name": name,
            "description": description,
            "price": price,
            "quantity": quantity,
            "message": "Item created successfully",
        }
    ), 201


@app.route("/api/items", methods=["GET"])
def list_items():
    """List all items with optional filtering and pagination."""
    # Get query parameters
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 10, type=int)
    search = request.args.get("search", "")

    # Ensure reasonable limits
    limit = min(max(limit, 1), 100)
    offset = (page - 1) * limit

    db = get_db()

    # Build query
    if search:
        query = """SELECT * FROM items 
                   WHERE name LIKE ? OR description LIKE ?
                   ORDER BY created_at DESC
                   LIMIT ? OFFSET ?"""
        search_pattern = f"%{search}%"
        cursor = db.execute(query, (search_pattern, search_pattern, limit, offset))

        # Get total count for pagination
        count_cursor = db.execute(
            """SELECT COUNT(*) as total FROM items 
               WHERE name LIKE ? OR description LIKE ?""",
            (search_pattern, search_pattern),
        )
    else:
        query = """SELECT * FROM items 
                   ORDER BY created_at DESC
                   LIMIT ? OFFSET ?"""
        cursor = db.execute(query, (limit, offset))

        # Get total count
        count_cursor = db.execute("SELECT COUNT(*) as total FROM items")

    items = [dict(row) for row in cursor.fetchall()]
    total = count_cursor.fetchone()["total"]

    return jsonify(
        {
            "items": items,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit,
            },
        }
    )


@app.route("/api/items/<int:item_id>", methods=["GET"])
def get_item(item_id):
    """Get a single item by ID."""
    db = get_db()
    cursor = db.execute("SELECT * FROM items WHERE id = ?", (item_id,))
    row = cursor.fetchone()

    if row is None:
        return jsonify(
            {"error": "Not Found", "message": f"Item with id {item_id} not found"}
        ), 404

    return jsonify(dict(row))


@app.route("/api/items/<int:item_id>", methods=["PUT"])
def update_item(item_id):
    """Update an existing item."""
    data = request.get_json()

    if not data:
        return jsonify(
            {"error": "Bad Request", "message": "Request body is required"}
        ), 400

    db = get_db()

    # Check if item exists
    cursor = db.execute("SELECT * FROM items WHERE id = ?", (item_id,))
    if cursor.fetchone() is None:
        return jsonify(
            {"error": "Not Found", "message": f"Item with id {item_id} not found"}
        ), 404

    # Build update query dynamically
    fields = []
    values = []

    if "name" in data:
        fields.append("name = ?")
        values.append(data["name"])

    if "description" in data:
        fields.append("description = ?")
        values.append(data["description"])

    if "price" in data:
        fields.append("price = ?")
        values.append(float(data["price"]))

    if "quantity" in data:
        fields.append("quantity = ?")
        values.append(int(data["quantity"]))

    if not fields:
        return jsonify(
            {"error": "Bad Request", "message": "No valid fields to update"}
        ), 400

    # Add updated_at and item_id
    fields.append("updated_at = CURRENT_TIMESTAMP")
    values.append(item_id)

    query = f"UPDATE items SET {', '.join(fields)} WHERE id = ?"
    db.execute(query, values)
    db.commit()

    # Return updated item
    cursor = db.execute("SELECT * FROM items WHERE id = ?", (item_id,))
    return jsonify(
        {"message": "Item updated successfully", "item": dict(cursor.fetchone())}
    )


@app.route("/api/items/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    """Delete an item."""
    db = get_db()

    # Check if item exists
    cursor = db.execute("SELECT * FROM items WHERE id = ?", (item_id,))
    if cursor.fetchone() is None:
        return jsonify(
            {"error": "Not Found", "message": f"Item with id {item_id} not found"}
        ), 404

    db.execute("DELETE FROM items WHERE id = ?", (item_id,))
    db.commit()

    return jsonify({"message": "Item deleted successfully", "id": item_id}), 200


if __name__ == "__main__":
    init_db()
    print("🚀 Starting Items API on http://localhost:5000")
    print("📚 Endpoints:")
    print("   POST   /api/items       - Create item")
    print("   GET    /api/items       - List items")
    print("   GET    /api/items/{id}  - Get item")
    print("   PUT    /api/items/{id}  - Update item")
    print("   DELETE /api/items/{id}  - Delete item")
    print("   GET    /health          - Health check")
    print("\nPress Ctrl+C to stop")
    app.run(host="0.0.0.0", port=5000, debug=True)
