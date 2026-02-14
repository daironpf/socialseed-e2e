"""
E-commerce Broken - Aplicación de e-commerce con bugs intencionales.

Este servicio simula un sistema completo de e-commerce con bugs en flujos
end-to-end: inventario, carrito, checkout, órdenes, cupones, etc.

Bugs documentados en BUGS.md
"""

import threading
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

from flask import Flask, jsonify, request

app = Flask(__name__)

# Base de datos en memoria
products_db: Dict[str, dict] = {}
carts_db: Dict[str, dict] = {}  # BUG #1: Carritos no expiran
orders_db: Dict[str, dict] = {}
coupons_db: Dict[str, dict] = {}
users_db: Dict[str, dict] = {}

# Lock para operaciones críticas
inventory_lock = threading.Lock()
order_lock = threading.Lock()


def generate_id(prefix: str) -> str:
    """Generar ID único."""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def calculate_cart_total(cart: dict) -> Decimal:
    """Calcular total del carrito."""
    total = Decimal("0")
    for item in cart["items"]:
        product = products_db.get(item["product_id"])
        if product:
            # BUG #2: No verificar si el precio cambió desde que se agregó al carrito
            total += Decimal(product["price"]) * item["quantity"]
    return total


def apply_coupon(total: Decimal, coupon_code: str) -> tuple[Decimal, str]:
    """Aplicar cupón al total."""
    coupon = coupons_db.get(coupon_code)

    if not coupon:
        return total, "invalid"

    # BUG #3: No verificar expiración del cupón
    # BUG #4: No verificar si ya fue usado (por usuario o global)
    # BUG #5: No verificar mínimo de compra

    if coupon["type"] == "percentage":
        # BUG #6: Descuento porcentual sin límite máximo
        discount = total * (Decimal(coupon["value"]) / 100)
        total = total - discount
    elif coupon["type"] == "fixed":
        # BUG #7: Descuento fijo puede resultar en total negativo
        total = total - Decimal(coupon["value"])

    return total, "applied"


@app.route("/health", methods=["GET"])
def health():
    """Health check."""
    return jsonify({"status": "healthy", "service": "ecommerce-service"})


# ==================== PRODUCTS ====================


@app.route("/api/v1/products", methods=["GET"])
def list_products():
    """Listar productos disponibles."""
    # BUG #8: No paginación - puede retornar miles de productos
    products_list = list(products_db.values())
    return jsonify({"products": products_list})


@app.route("/api/v1/products/<product_id>", methods=["GET"])
def get_product(product_id: str):
    """Obtener detalle de producto."""
    product = products_db.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    # BUG #9: Exponer stock real (información sensible para competencia)
    return jsonify(product)


# ==================== CART ====================


@app.route("/api/v1/carts", methods=["POST"])
def create_cart():
    """Crear nuevo carrito."""
    data = request.get_json() or {}
    user_id = data.get("user_id", "")

    # BUG #10: No validar user_id - permite crear carritos sin usuario
    cart_id = generate_id("cart")

    carts_db[cart_id] = {
        "id": cart_id,
        "user_id": user_id,
        "items": [],
        "created_at": datetime.utcnow().isoformat(),
        # BUG #11: No expiración de carritos
    }

    return jsonify({"cart_id": cart_id}), 201


@app.route("/api/v1/carts/<cart_id>/items", methods=["POST"])
def add_to_cart(cart_id: str):
    """Agregar item al carrito."""
    cart = carts_db.get(cart_id)
    if not cart:
        return jsonify({"error": "Cart not found"}), 404

    data = request.get_json()
    product_id = data.get("product_id", "")
    quantity = data.get("quantity", 1)

    product = products_db.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    # BUG #12: No verificar stock al agregar al carrito
    # El stock se verifica solo en checkout

    # BUG #13: No validar quantity > 0
    if quantity < 0:
        # BUG: Quantity negativo reduce items del carrito
        for i, item in enumerate(cart["items"]):
            if item["product_id"] == product_id:
                item["quantity"] += quantity  # Reduce si quantity es negativo
                if item["quantity"] <= 0:
                    cart["items"].pop(i)
                break
    else:
        # Agregar o actualizar item
        for item in cart["items"]:
            if item["product_id"] == product_id:
                item["quantity"] += quantity
                break
        else:
            cart["items"].append(
                {
                    "product_id": product_id,
                    "quantity": quantity,
                    "added_at": datetime.utcnow().isoformat(),
                }
            )

    return jsonify({"cart": cart})


@app.route("/api/v1/carts/<cart_id>", methods=["GET"])
def get_cart(cart_id: str):
    """Obtener carrito."""
    cart = carts_db.get(cart_id)
    if not cart:
        return jsonify({"error": "Cart not found"}), 404

    # Calcular totales
    subtotal = calculate_cart_total(cart)

    # BUG #14: No incluir impuestos en el cálculo
    tax = Decimal("0")
    total = subtotal

    return jsonify(
        {
            "cart": cart,
            "subtotal": str(subtotal),
            "tax": str(tax),
            "total": str(total),
        }
    )


# ==================== CHECKOUT ====================


@app.route("/api/v1/checkout", methods=["POST"])
def checkout():
    """Procesar checkout y crear orden."""
    data = request.get_json()
    cart_id = data.get("cart_id", "")
    coupon_code = data.get("coupon_code", "")

    cart = carts_db.get(cart_id)
    if not cart:
        return jsonify({"error": "Cart not found"}), 404

    if not cart["items"]:
        return jsonify({"error": "Cart is empty"}), 400

    # BUG #15: Race condition en checkout
    # Verificar stock y crear orden debería ser atómico

    # Verificar stock
    for item in cart["items"]:
        product = products_db.get(item["product_id"])
        if not product:
            return jsonify({"error": f"Product {item['product_id']} not found"}), 400

        # BUG #16: Verificación de stock fuera del lock
        if product["stock"] < item["quantity"]:
            return jsonify(
                {
                    "error": f"Insufficient stock for {product['name']}",
                    "available": product["stock"],
                    "requested": item["quantity"],
                }
            ), 400

    # Calcular totales
    subtotal = calculate_cart_total(cart)

    # BUG #17: Aplicar cupón antes de calcular impuestos
    # Los impuestos deberían calcularse sobre el subtotal
    if coupon_code:
        subtotal, status = apply_coupon(subtotal, coupon_code)
        if status == "invalid":
            return jsonify({"error": "Invalid coupon"}), 400

    # BUG #18: Cálculo incorrecto de impuestos
    # Tasa fija en lugar de basada en ubicación
    tax_rate = Decimal("0.08")  # 8% fijo
    tax = subtotal * tax_rate

    total = subtotal + tax

    # Crear orden
    order_id = generate_id("ord")

    with order_lock:
        # BUG #19: Reducir stock dentro del lock, pero verificación fue afuera
        for item in cart["items"]:
            product = products_db[item["product_id"]]
            # BUG #20: No verificar nuevamente el stock dentro del lock
            product["stock"] -= item["quantity"]

        orders_db[order_id] = {
            "id": order_id,
            "user_id": cart["user_id"],
            "cart_id": cart_id,
            "items": cart["items"].copy(),
            "subtotal": str(subtotal),
            "tax": str(tax),
            "total": str(total),
            "status": "completed",  # BUG #21: Marcar como completado inmediatamente
            "created_at": datetime.utcnow().isoformat(),
            # BUG #22: No tracking de estado (pending → processing → completed)
        }

    # BUG #23: No limpiar el carrito después del checkout
    # El carrito sigue con los items

    return jsonify(
        {
            "order_id": order_id,
            "status": "completed",
            "total": str(total),
        }
    ), 201


# ==================== ORDERS ====================


@app.route("/api/v1/orders/<order_id>", methods=["GET"])
def get_order(order_id: str):
    """Obtener orden."""
    order = orders_db.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404

    # BUG #24: No verificar que el usuario sea el dueño de la orden
    return jsonify(order)


@app.route("/api/v1/orders/<order_id>/cancel", methods=["POST"])
def cancel_order(order_id: str):
    """Cancelar orden."""
    order = orders_db.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404

    # BUG #25: No verificar que la orden esté en estado cancelable
    # Permite cancelar órdenes ya completadas

    # BUG #26: No restaurar stock al cancelar
    # El inventario se pierde

    order["status"] = "cancelled"
    order["cancelled_at"] = datetime.utcnow().isoformat()

    return jsonify({"status": "cancelled", "order_id": order_id})


# ==================== COUPONS ====================


@app.route("/api/v1/coupons/validate", methods=["POST"])
def validate_coupon():
    """Validar cupón."""
    data = request.get_json()
    code = data.get("code", "")
    cart_total = Decimal(data.get("cart_total", "0"))

    coupon = coupons_db.get(code)
    if not coupon:
        return jsonify({"valid": False, "error": "Invalid coupon"}), 400

    # BUG #27: No verificar expiración
    # BUG #28: No verificar usos máximos
    # BUG #29: No verificar mínimo de compra

    new_total, status = apply_coupon(cart_total, code)

    return jsonify(
        {
            "valid": True,
            "discount": str(cart_total - new_total),
            "new_total": str(new_total),
        }
    )


# ==================== ADMIN ====================


@app.route("/api/v1/admin/products", methods=["POST"])
def create_product():
    """Crear producto (admin)."""
    # BUG #30: No verificar autenticación de admin

    data = request.get_json()

    product_id = generate_id("prod")
    products_db[product_id] = {
        "id": product_id,
        "name": data.get("name", ""),
        "description": data.get("description", ""),
        "price": str(Decimal(data.get("price", "0"))),  # BUG #31: No validar price > 0
        "stock": data.get("stock", 0),
        "created_at": datetime.utcnow().isoformat(),
    }

    return jsonify({"product_id": product_id}), 201


@app.route("/api/v1/admin/coupons", methods=["POST"])
def create_coupon():
    """Crear cupón (admin)."""
    # BUG #32: No verificar autenticación

    data = request.get_json()

    code = data.get("code", "")
    coupons_db[code] = {
        "code": code,
        "type": data.get("type", "percentage"),  # percentage o fixed
        "value": str(data.get("value", "0")),
        "created_at": datetime.utcnow().isoformat(),
        # BUG #33: No expires_at
        # BUG #34: No max_uses
        # BUG #35: No min_purchase
    }

    return jsonify({"coupon_code": code}), 201


if __name__ == "__main__":
    # Inicializar productos de prueba
    products_db["prod_laptop"] = {
        "id": "prod_laptop",
        "name": "Laptop Gaming",
        "description": "Laptop de alta performance",
        "price": "999.99",
        "stock": 5,
    }
    products_db["prod_mouse"] = {
        "id": "prod_mouse",
        "name": "Mouse Inalámbrico",
        "description": "Mouse ergonómico",
        "price": "29.99",
        "stock": 10,
    }
    products_db["prod_keyboard"] = {
        "id": "prod_keyboard",
        "name": "Teclado Mecánico",
        "description": "Teclado RGB",
        "price": "79.99",
        "stock": 3,  # Stock bajo para testing
    }

    # Inicializar cupones
    coupons_db["SAVE10"] = {
        "code": "SAVE10",
        "type": "percentage",
        "value": "10",
    }
    coupons_db["DISCOUNT50"] = {
        "code": "DISCOUNT50",
        "type": "fixed",
        "value": "50",
    }

    print("🛒 E-commerce Broken iniciado")
    print("   Este servicio tiene 35 bugs intencionales")
    print("   Lee BUGS.md para ver la lista completa")
    print()
    print("   Productos de prueba:")
    print("   - Laptop Gaming: $999.99 (stock: 5)")
    print("   - Mouse Inalámbrico: $29.99 (stock: 10)")
    print("   - Teclado Mecánico: $79.99 (stock: 3)")
    print()
    print("   Cupones:")
    print("   - SAVE10: 10% de descuento")
    print("   - DISCOUNT50: $50 de descuento")
    print()

    app.run(host="0.0.0.0", port=5003, debug=True, threaded=True)
