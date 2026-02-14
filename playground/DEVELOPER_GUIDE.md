# Guía de Uso del Playground - Para Desarrolladores

Esta guía te ayudará a usar y extender el playground de SocialSeed E2E.

## 📚 Contenido

1. [Cómo Usar el Playground](#cómo-usar-el-playground)
2. [Estructura de Aplicaciones Rotas](#estructura-de-aplicaciones-rotas)
3. [Cómo Crear una Nueva App Rota](#cómo-crear-una-nueva-app-rota)
4. [Patrones de Bugs Comunes](#patrones-de-bugs-comunes)
5. [Mejores Prácticas](#mejores-prácticas)

---

## Cómo Usar el Playground

### Inicio Rápido

```bash
# 1. Clonar el repositorio
git clone https://github.com/daironpf/socialseed-e2e.git
cd socialseed-e2e

# 2. Instalar dependencias del playground
pip install -r playground/broken-apps/auth-service-broken/requirements.txt

# 3. Iniciar el servicio
python playground/broken-apps/auth-service-broken/app.py

# 4. Probar endpoints
curl http://localhost:5001/health
```

### Estructura del Proyecto

```
playground/
├── broken-apps/
│   ├── auth-service-broken/      # 20 bugs de autenticación
│   ├── payment-service-broken/   # 31 bugs de pagos/concurrencia
│   └── ecommerce-broken/         # 35 bugs de e-commerce
├── tutorials/
│   └── 01-getting-started/       # Tutorial completo
├── challenges/
│   └── find-the-bug-01/          # Desafíos interactivos
└── README.md                     # Guía principal
```

### Flujo de Trabajo Típico

1. **Elegir una app**: Empieza con auth-service (más simple)
2. **Leer BUGS.md**: Entender qué bugs existen
3. **Escribir tests**: Crear tests que detecten los bugs
4. **Ejecutar**: Ver los tests fallar (lo cual es correcto)
5. **Corregir**: Modificar la app para arreglar bugs
6. **Verificar**: Tests deberían pasar ahora

---

## Estructura de Aplicaciones Rotas

Cada aplicación sigue una estructura estándar:

```
broken-apps/<nombre>-broken/
├── app.py              # Aplicación Flask con bugs
├── BUGS.md             # Documentación de bugs
├── README.md           # Guía de uso
├── requirements.txt    # Dependencias
└── tests/              # (opcional) Tests de ejemplo
```

### app.py - Componentes Clave

```python
# 1. Imports y configuración
from flask import Flask, jsonify, request

app = Flask(__name__)

# 2. Base de datos en memoria
# Usar diccionarios globales para simular DB
users_db = {}

# 3. Endpoints con bugs intencionales
@app.route("/api/v1/endpoint", methods=["POST"])
def endpoint():
    # BUG #X: Descripción del bug
    # Código con bug...
    pass

# 4. Inicialización de datos de prueba
if __name__ == "__main__":
    # Crear usuarios/productos de prueba
    users_db["test"] = {...}
    app.run(host="0.0.0.0", port=500X, debug=True)
```

### BUGS.md - Formato Estándar

```markdown
# Nombre Service Broken - Lista de Bugs

## 🔴 Bugs Críticos

### BUG #1: Título Descriptivo
**Ubicación:** `app.py:LÍNEA` - función `nombre()`
**Problema:** Descripción del problema
**Impacto:** Qué puede pasar
**Solución:** Cómo arreglarlo

## 🟠 Bugs Medios
...

## 🟡 Bugs Funcionales
...

## 🎯 Ejercicios Sugeridos
...
```

---

## Cómo Crear una Nueva App Rota

### Paso 1: Crear Estructura

```bash
mkdir playground/broken-apps/<nombre>-broken
cd playground/broken-apps/<nombre>-broken
touch app.py BUGS.md README.md requirements.txt
```

### Paso 2: Plantilla de app.py

```python
"""
<Nombre> Service Broken - Breve descripción.

Este servicio simula [dominio] con bugs relacionados a [temas].
Bugs documentados en BUGS.md
"""

from flask import Flask, jsonify, request

app = Flask(__name__)

# Base de datos en memoria
# [Entidades principales]
entity_db = {}

# Endpoints
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"})

# [Endpoints con bugs intencionales]

if __name__ == "__main__":
    # [Datos de prueba]
    app.run(host="0.0.0.0", port=500X, debug=True)
```

### Paso 3: Diseñar Bugs

**Tipos de bugs recomendados:**

1. **Seguridad**: Autenticación, autorización, exposición de datos
2. **Concurrencia**: Race conditions, locks incorrectos
3. **Validación**: Inputs no validados, edge cases
4. **Lógica de negocio**: Cálculos incorrectos, estados inválidos
5. **Performance**: N+1 queries, paginación faltante

**Ejemplo - Bug de seguridad:**
```python
@app.route("/api/v1/users/<user_id>", methods=["GET"])
def get_user(user_id):
    # BUG: No verificar que el requester sea el dueño
    user = users_db.get(user_id)
    return jsonify(user)  # Expone datos de cualquier usuario
```

**Ejemplo - Bug de concurrencia:**
```python
def transfer_funds(from_user, to_user, amount):
    # BUG: Race condition - verificación y transferencia no atómicas
    if balances[from_user] >= amount:  # Verificación
        balances[from_user] -= amount  # Operación
        balances[to_user] += amount
```

### Paso 4: Documentar en BUGS.md

Para cada bug documentar:
- **Ubicación exacta** (archivo y línea)
- **Problema** (qué está mal)
- **Impacto** (qué puede pasar)
- **Caso de ejemplo** (cómo reproducirlo)
- **Solución** (cómo arreglarlo)

### Paso 5: Crear README.md

Incluir:
- Descripción del servicio
- Cómo ejecutar
- Endpoints disponibles
- Ejemplos de uso (curl)
- Lista resumida de bugs

---

## Patrones de Bugs Comunes

### 1. Race Conditions

```python
# ❌ BUG: Verificación y operación separadas
if stock >= quantity:      # Paso 1
    stock -= quantity      # Paso 2 (race condition aquí)

# ✅ SOLUCIÓN: Lock + verificación atómica
with lock:
    if stock >= quantity:
        stock -= quantity
```

### 2. Validación Insuficiente

```python
# ❌ BUG: Validación básica
if "@" in email:  # "a@b" pasa la validación

# ✅ SOLUCIÓN: Validación completa
import re
pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
if re.match(pattern, email):
```

### 3. Autorización Ausente

```python
# ❌ BUG: Cualquiera accede
@app.route("/api/v1/admin/users")
def list_users():
    return jsonify(users_db)

# ✅ SOLUCIÓN: Verificar permisos
@app.route("/api/v1/admin/users")
@require_admin
def list_users():
    return jsonify(users_db)
```

### 4. Exposición de Datos Sensibles

```python
# ❌ BUG: Expone todo
return jsonify({
    "username": user.name,
    "password": user.password,  # 😱
    "ssn": user.ssn,
})

# ✅ SOLUCIÓN: Filtrar campos
return jsonify({
    "username": user.name,
    "email": user.email,
})
```

### 5. Cálculos Financieros Incorrectos

```python
# ❌ BUG: Float para dinero
total = price * 0.029 + 0.30  # Precisión incorrecta

# ✅ SOLUCIÓN: Decimal
from decimal import Decimal
total = price * Decimal("0.029") + Decimal("0.30")
```

---

## Mejores Prácticas

### Para Bugs

1. **Ser realista**: Los bugs deben ser creíbles, no artificiales
2. **Graduar dificultad**: Algunos obvios, otros sutiles
3. **Documentar bien**: Explicar impacto y solución
4. **Categorizar**: Separar por severidad (crítico/medio/bajo)
5. **Numerar**: BUG #1, #2, etc. para fácil referencia

### Para Tests

1. **Un test por bug**: Test específico que falle por un bug
2. **Nombres descriptivos**: `test_password_not_exposed_in_response`
3. **Mensajes claros**: `assert "password" not in response, "BUG: Password exposed!"`
4. **Independientes**: Tests no deben depender de otros

### Para Documentación

1. **Incluir ejemplos de curl**: Fácil de copiar y probar
2. **Datos de prueba**: Usuarios, productos pre-configurados
3. **Escenarios**: Flujos completos de uso
4. **Troubleshooting**: Problemas comunes y soluciones

---

## Ejemplo Completo: Crear App de Inventory

```python
# app.py
from flask import Flask, jsonify, request
import threading

app = Flask(__name__)
inventory = {"item_1": 10}
lock = threading.Lock()

@app.route("/reserve", methods=["POST"])
def reserve():
    """Reservar item del inventario."""
    item_id = request.json.get("item_id")
    quantity = request.json.get("quantity", 1)
    
    # BUG #1: Race condition
    if inventory.get(item_id, 0) >= quantity:
        # BUG #2: No lock
        inventory[item_id] -= quantity
        return jsonify({"status": "reserved"})
    
    return jsonify({"error": "No stock"}), 400

if __name__ == "__main__":
    app.run(port=5004)
```

```markdown
<!-- BUGS.md -->
## 🔴 Bug #1: Race Condition
**Ubicación:** app.py:15
**Problema:** Dos requests simultáneos pueden reservar el mismo item
**Solución:** Lock + verificación atómica
```

---

## Contribuir al Playground

1. Fork del repositorio
2. Crea tu app en `broken-apps/<nombre>-broken/`
3. Documenta bugs en BUGS.md
4. Crea README.md con instrucciones
5. Envía PR con descripción detallada

## Recursos Adicionales

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [Testing Race Conditions](https://example.com/race-conditions)

---

**¿Preguntas?** Abre un issue en GitHub o únete a las Discussions.
