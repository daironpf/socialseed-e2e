"""
Auth Service Broken - Servicio de autenticación con bugs intencionales.

Este servicio simula un sistema de autenticación con múltiples bugs
que los usuarios deben identificar y corregir usando SocialSeed E2E.

Bugs documentados en BUGS.md
"""

from datetime import datetime, timedelta
from functools import wraps
from typing import Dict, Optional

from flask import Flask, jsonify, request

app = Flask(__name__)

# Base de datos en memoria (simulada)
users_db: Dict[str, dict] = {}
refresh_tokens: Dict[str, str] = {}  # BUG #4: No tiene expiración


def create_token(user_id: str, token_type: str = "access") -> str:
    """Crear un JWT token simulado."""
    import hashlib
    import secrets

    # BUG #1: Usar MD5 en lugar de SHA-256 para el token
    # Esto es inseguro pero lo hacemos a propósito para el ejemplo
    token_data = f"{user_id}:{token_type}:{secrets.token_hex(8)}"
    return f"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.{hashlib.md5(token_data.encode()).hexdigest()}.signature"


def decode_token(token: str) -> Optional[dict]:
    """Decodificar un JWT token simulado."""
    # BUG #2: No validar correctamente el formato del token
    # Acepta cualquier string que tenga 3 partes separadas por puntos
    parts = token.split(".")
    if len(parts) != 3:
        return None

    # BUG #3: No validar la firma del token
    # Simplemente extraemos el user_id del payload sin verificar
    try:
        import base64

        payload = base64.b64decode(parts[1] + "==").decode()
        # BUG: El payload no tiene estructura JSON válida en nuestro caso
        # Pero para el ejemplo, simplemente verificamos si existe en refresh_tokens
        for user_id, stored_token in refresh_tokens.items():
            if stored_token == token:
                return {
                    "user_id": user_id,
                    "exp": datetime.utcnow() + timedelta(hours=1),
                }
        return None
    except Exception:
        return None


def require_auth(f):
    """Decorador para requerir autenticación."""

    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")

        # BUG #5: No verificar el prefijo "Bearer " correctamente
        # Acepta tokens con o sin el prefijo
        token = auth_header.replace("Bearer ", "").strip()

        if not token:
            return jsonify({"error": "Missing token"}), 401

        decoded = decode_token(token)
        if not decoded:
            return jsonify({"error": "Invalid token"}), 401

        # BUG #6: No verificar expiración del token
        # Ignoramos el campo 'exp' del token

        request.user_id = decoded["user_id"]
        return f(*args, **kwargs)

    return decorated


@app.route("/health", methods=["GET"])
def health():
    """Endpoint de health check."""
    return jsonify({"status": "healthy", "service": "auth-service"})


@app.route("/api/v1/auth/register", methods=["POST"])
def register():
    """Registrar un nuevo usuario."""
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    email = data.get("email", "").lower().strip()
    password = data.get("password", "")
    username = data.get("username", "").strip()

    # BUG #7: Validación de email muy básica
    # No verifica formato real de email
    if "@" not in email:
        return jsonify({"error": "Invalid email"}), 400

    # BUG #8: No validar fortaleza de contraseña
    # Acepta contraseñas de cualquier longitud

    # BUG #9: No verificar si el usuario ya existe (case insensitive)
    # Solo verifica email exacto, no username
    if email in users_db:
        return jsonify({"error": "Email already registered"}), 409

    # BUG #10: Almacenar contraseña en texto plano
    # No usar hash ni salt
    user_id = f"user_{len(users_db) + 1}"
    users_db[email] = {
        "id": user_id,
        "email": email,
        "username": username,
        "password": password,  # BUG: Texto plano
        "created_at": datetime.utcnow().isoformat(),
        "role": "user",
    }

    return jsonify({"message": "User registered successfully", "user_id": user_id}), 201


@app.route("/api/v1/auth/login", methods=["POST"])
def login():
    """Iniciar sesión."""
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    email = data.get("email", "").lower().strip()
    password = data.get("password", "")

    user = users_db.get(email)

    # BUG #11: Timing attack - comparación de strings no constante
    # Permite ataques de timing para adivinar contraseñas
    if not user or user["password"] != password:
        return jsonify({"error": "Invalid credentials"}), 401

    # BUG #12: Tokens de acceso sin tiempo de expiración
    access_token = create_token(user["id"], "access")
    refresh_token = create_token(user["id"], "refresh")

    # BUG #13: Almacenar refresh token sin expiración
    refresh_tokens[user["id"]] = refresh_token

    return jsonify(
        {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            # BUG #14: No incluir expires_in
        }
    )


@app.route("/api/v1/auth/refresh", methods=["POST"])
def refresh():
    """Refrescar token de acceso."""
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    refresh_token = data.get("refresh_token", "")

    # BUG #15: No validar que el refresh token sea válido
    # Simplemente buscamos en nuestro diccionario
    user_id = None
    for uid, token in refresh_tokens.items():
        if token == refresh_token:
            user_id = uid
            break

    if not user_id:
        return jsonify({"error": "Invalid refresh token"}), 401

    # BUG #16: No revocar el refresh token anterior
    # El mismo refresh token puede usarse múltiples veces

    new_access_token = create_token(user_id, "access")

    return jsonify({"access_token": new_access_token, "token_type": "Bearer"})


@app.route("/api/v1/auth/profile", methods=["GET"])
@require_auth
def get_profile():
    """Obtener perfil del usuario autenticado."""
    user_id = request.user_id

    # Buscar usuario por ID
    user = None
    for u in users_db.values():
        if u["id"] == user_id:
            user = u
            break

    if not user:
        return jsonify({"error": "User not found"}), 404

    # BUG #17: Exponer contraseña en la respuesta
    # No debería incluirse nunca
    return jsonify(
        {
            "id": user["id"],
            "email": user["email"],
            "username": user["username"],
            "created_at": user["created_at"],
            "role": user["role"],
            "password": user["password"],  # BUG: Exponiendo contraseña
        }
    )


@app.route("/api/v1/auth/logout", methods=["POST"])
@require_auth
def logout():
    """Cerrar sesión."""
    user_id = request.user_id

    # BUG #18: Logout no revoca el access token
    # Solo elimina el refresh token
    if user_id in refresh_tokens:
        del refresh_tokens[user_id]

    return jsonify({"message": "Logged out successfully"})


@app.route("/api/v1/auth/admin/users", methods=["GET"])
@require_auth
def list_users():
    """Listar todos los usuarios (solo admin)."""
    # BUG #19: No verificar rol de administrador
    # Cualquier usuario autenticado puede ver todos los usuarios

    users_list = []
    for user in users_db.values():
        users_list.append(
            {
                "id": user["id"],
                "email": user["email"],
                "username": user["username"],
                "role": user["role"],
            }
        )

    return jsonify({"users": users_list})


@app.route("/api/v1/auth/reset-password", methods=["POST"])
def reset_password():
    """Solicitar reset de contraseña."""
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    email = data.get("email", "").lower().strip()

    # BUG #20: No verificar si el email existe
    # Siempre responde con éxito para evitar enumeración de usuarios
    # PERO el mensaje de éxito es diferente si existe o no
    if email in users_db:
        # BUG: Mensaje revela que el usuario existe
        return jsonify({"message": "Password reset email sent to " + email})
    else:
        return jsonify({"message": "If the email exists, a reset link was sent"})


if __name__ == "__main__":
    # Crear algunos usuarios de prueba
    users_db["admin@example.com"] = {
        "id": "user_admin",
        "email": "admin@example.com",
        "username": "admin",
        "password": "admin123",  # BUG: Contraseña débil
        "created_at": datetime.utcnow().isoformat(),
        "role": "admin",
    }

    users_db["user@example.com"] = {
        "id": "user_1",
        "email": "user@example.com",
        "username": "testuser",
        "password": "password123",
        "created_at": datetime.utcnow().isoformat(),
        "role": "user",
    }

    print("🐛 Auth Service Broken iniciado")
    print("   Este servicio tiene 20 bugs intencionales")
    print("   Lee BUGS.md para ver la lista completa")
    print()

    app.run(host="0.0.0.0", port=5001, debug=True)
