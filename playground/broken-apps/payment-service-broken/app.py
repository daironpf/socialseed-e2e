"""
Payment Service Broken - Servicio de pagos con bugs intencionales.

Este servicio simula un sistema de procesamiento de pagos con bugs relacionados
a concurrencia, idempotencia, validación de montos y transacciones.

Bugs documentados en BUGS.md
"""

import threading
import uuid
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional

from flask import Flask, jsonify, request

app = Flask(__name__)

# Base de datos en memoria
payments_db: Dict[str, dict] = {}
users_balance: Dict[str, Decimal] = {}
idempotency_keys: set = set()  # BUG #4: Sin expiración
lock = threading.Lock()


def generate_payment_id() -> str:
    """Generar ID único para pago."""
    return f"pay_{uuid.uuid4().hex[:12]}"


def validate_amount(amount: str) -> Optional[Decimal]:
    """Validar y convertir monto a Decimal."""
    try:
        # BUG #1: No validar formato antes de convertir
        # Acepta notación científica y formatos inesperados
        d = Decimal(amount)

        # BUG #2: No validar precisión decimal
        # Permite decimales infinitos
        return d
    except Exception:
        return None


def calculate_fee(amount: Decimal) -> Decimal:
    """Calcular comisión del procesador (2.9% + $0.30)."""
    # BUG #3: Error de precisión en cálculo de comisión
    # Usa float en lugar de Decimal
    fee = float(amount) * 0.029 + 0.30
    return Decimal(str(fee))  # Conversión imprecisa


@app.route("/health", methods=["GET"])
def health():
    """Endpoint de health check."""
    return jsonify({"status": "healthy", "service": "payment-service"})


@app.route("/api/v1/payments", methods=["POST"])
def create_payment():
    """Crear un nuevo pago."""
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    user_id = data.get("user_id", "")
    amount_str = data.get("amount", "")
    currency = data.get("currency", "USD")
    idempotency_key = request.headers.get("Idempotency-Key", "")

    # BUG #4: Validación de idempotencia inconsistente
    # Solo verifica si existe, no si es para el mismo pago
    if idempotency_key and idempotency_key in idempotency_keys:
        # BUG: No retornar el pago original, solo error
        return jsonify({"error": "Duplicate idempotency key"}), 409

    # BUG #5: No validar que el idempotency_key sea único por pago
    # Un key podría usarse para pagos diferentes

    # Validar monto
    amount = validate_amount(amount_str)
    if amount is None:
        return jsonify({"error": "Invalid amount"}), 400

    # BUG #6: No validar monto mínimo
    # Permite montos negativos o cero

    # BUG #7: No validar moneda
    # Acepta cualquier string como moneda

    # Verificar balance del usuario
    # BUG #8: Race condition al verificar balance
    # No hay lock durante la verificación
    current_balance = users_balance.get(user_id, Decimal("0"))
    if current_balance < amount:
        return jsonify({"error": "Insufficient funds"}), 402

    # Crear pago
    payment_id = generate_payment_id()
    fee = calculate_fee(amount)
    net_amount = amount - fee

    # BUG #9: Race condition en procesamiento de pago
    # Múltiples pagos simultáneos pueden procesarse incorrectamente

    with lock:
        # BUG #10: No verificar nuevamente el balance dentro del lock
        # Podría haber cambiado entre verificación y procesamiento

        # Actualizar balance
        users_balance[user_id] = users_balance.get(user_id, Decimal("0")) - amount

        # Almacenar pago
        payments_db[payment_id] = {
            "id": payment_id,
            "user_id": user_id,
            "amount": str(amount),  # BUG #11: Almacenar como string sin normalizar
            "currency": currency,
            "fee": str(fee),
            "net_amount": str(net_amount),
            "status": "completed",
            "created_at": datetime.utcnow().isoformat(),
            "idempotency_key": idempotency_key,  # BUG #12: No encriptar key sensible
        }

        # BUG #13: Registrar idempotency key solo después de éxito
        # Si falla después, el key queda marcado sin pago
        if idempotency_key:
            idempotency_keys.add(idempotency_key)

    return jsonify(
        {
            "payment_id": payment_id,
            "status": "completed",
            "amount": str(amount),
            "fee": str(fee),
            "net_amount": str(net_amount),
        }
    ), 201


@app.route("/api/v1/payments/<payment_id>", methods=["GET"])
def get_payment(payment_id: str):
    """Obtener detalles de un pago."""
    payment = payments_db.get(payment_id)

    if not payment:
        return jsonify({"error": "Payment not found"}), 404

    # BUG #14: Exponer idempotency_key en la respuesta
    # Es información sensible que no debería exponerse
    return jsonify(payment)


@app.route("/api/v1/payments/<payment_id>/refund", methods=["POST"])
def refund_payment(payment_id: str):
    """Reembolsar un pago."""
    payment = payments_db.get(payment_id)

    if not payment:
        return jsonify({"error": "Payment not found"}), 404

    # BUG #15: No verificar que el pago no haya sido reembolsado ya
    # Permite reembolsos múltiples del mismo pago

    # BUG #16: No verificar permisos
    # Cualquiera puede reembolsar cualquier pago

    data = request.get_json() or {}
    reason = data.get("reason", "")

    # BUG #17: No validar reason (puede ser muy largo o tener caracteres especiales)

    amount = Decimal(payment["amount"])
    user_id = payment["user_id"]

    # BUG #18: Race condition en reembolso
    with lock:
        # BUG #19: Reembolsar amount completo sin verificar fee
        # El usuario podría ganar dinero con reembolsos
        users_balance[user_id] = users_balance.get(user_id, Decimal("0")) + amount

        # BUG #20: No marcar el pago como reembolsado
        # No hay tracking de reembolsos
        payment["refund_reason"] = reason
        payment["refunded_at"] = datetime.utcnow().isoformat()

    return jsonify(
        {
            "status": "refunded",
            "payment_id": payment_id,
            "amount": str(amount),
        }
    )


@app.route("/api/v1/payments", methods=["GET"])
def list_payments():
    """Listar pagos de un usuario."""
    user_id = request.args.get("user_id", "")

    # BUG #21: No validar user_id
    # Lista todos los pagos si no se proporciona

    payments_list = []
    for payment in payments_db.values():
        # BUG #22: Filtro inseguro
        # Si user_id está vacío, no filtra nada
        if not user_id or payment["user_id"] == user_id:
            payments_list.append(payment)

    # BUG #23: No paginación
    # Podría retornar miles de resultados

    # BUG #24: No ordenar por fecha
    # Resultados en orden arbitrario

    return jsonify(
        {
            "payments": payments_list,
            "total": len(payments_list),
        }
    )


@app.route("/api/v1/users/<user_id>/balance", methods=["GET"])
def get_balance(user_id: str):
    """Obtener balance de un usuario."""
    balance = users_balance.get(user_id, Decimal("0"))

    # BUG #25: No verificar autenticación
    # Cualquiera puede ver el balance de cualquier usuario

    return jsonify(
        {
            "user_id": user_id,
            "balance": str(balance),
            "currency": "USD",
        }
    )


@app.route("/api/v1/users/<user_id>/deposit", methods=["POST"])
def deposit(user_id: str):
    """Depositar fondos en cuenta de usuario."""
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    amount_str = data.get("amount", "")
    amount = validate_amount(amount_str)

    if amount is None:
        return jsonify({"error": "Invalid amount"}), 400

    # BUG #26: No validar método de pago
    # Permite depositar sin verificar fuente de fondos

    # BUG #27: No verificar límite de depósito
    # Podría permitir lavado de dinero

    with lock:
        current = users_balance.get(user_id, Decimal("0"))
        users_balance[user_id] = current + amount

    return jsonify(
        {
            "status": "deposited",
            "user_id": user_id,
            "amount": str(amount),
            "new_balance": str(users_balance[user_id]),
        }
    )


@app.route("/api/v1/admin/payments/report", methods=["GET"])
def generate_report():
    """Generar reporte de transacciones (solo admin)."""
    # BUG #28: No verificar autenticación de admin
    # Cualquiera puede acceder

    # BUG #29: No rate limiting
    # Reportes pueden ser generados infinitamente

    total_volume = Decimal("0")
    total_fees = Decimal("0")

    for payment in payments_db.values():
        total_volume += Decimal(payment["amount"])
        total_fees += Decimal(payment["fee"])

    return jsonify(
        {
            "total_payments": len(payments_db),
            "total_volume": str(total_volume),
            "total_fees": str(total_fees),
            "net_revenue": str(total_fees),
        }
    )


@app.route("/api/v1/payments/<payment_id>/void", methods=["POST"])
def void_payment(payment_id: str):
    """Anular un pago pendiente."""
    payment = payments_db.get(payment_id)

    if not payment:
        return jsonify({"error": "Payment not found"}), 404

    # BUG #30: No verificar que el pago esté pendiente
    # Permite anular pagos completados

    # BUG #31: No reembolsar al anular
    # El dinero desaparece del sistema

    payment["status"] = "voided"
    payment["voided_at"] = datetime.utcnow().isoformat()

    return jsonify(
        {
            "status": "voided",
            "payment_id": payment_id,
        }
    )


if __name__ == "__main__":
    # Inicializar usuarios de prueba
    users_balance["user_1"] = Decimal("1000.00")
    users_balance["user_2"] = Decimal("500.00")
    users_balance["user_3"] = Decimal("50.00")  # Balance bajo para testing

    print("💳 Payment Service Broken iniciado")
    print("   Este servicio tiene 31 bugs intencionales")
    print("   Lee BUGS.md para ver la lista completa")
    print()
    print("   Usuarios de prueba:")
    print("   - user_1: $1000.00")
    print("   - user_2: $500.00")
    print("   - user_3: $50.00")
    print()

    app.run(host="0.0.0.0", port=5002, debug=True, threaded=True)
