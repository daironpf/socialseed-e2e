# 🤖 Guía Definitiva para Agentes de IA - SocialSeed E2E Framework

> **Versión 2.1 - Soporte REST y gRPC**
>
> Esta guía permite a los agentes de IA generar tests E2E perfectos para APIs REST y gRPC sin necesidad de ver el código fuente del framework.

## 📋 Índice

1. [Filosofía del Framework](#filosofía-del-framework)
2. [Estructura de Tests](#estructura-de-tests)
3. [Patrones Obligatorios](#patrones-obligatorios)
4. [API del Framework](#api-del-framework)
5. [Flujo de Trabajo](#flujo-de-trabajo)
6. [Ejemplos Completos](#ejemplos-completos)
7. [Testing de APIs gRPC](#testing-de-apis-grpc)
8. [Errores Comunes y Soluciones](#errores-comunes-y-soluciones)
9. [Checklist Pre-Entrega](#checklist-pre-entrega)

---

## 🎯 Filosofía del Framework

### Principios Fundamentales

1. **Page Object Model**: Cada servicio tiene una clase Page que hereda de `BasePage` (REST) o `BaseGrpcPage` (gRPC)
2. **Tests Secuenciales**: Los tests se ejecutan en orden numérico y comparten estado
3. **Aserciones Explícitas**: Cada test debe validar el resultado
4. **Sin Importaciones Relativas**: Solo imports absolutos permitidos
5. **Java-Compatible**: Serialización camelCase para backends Spring Boot (REST)
6. **Proto-First** (gRPC): Definir siempre primero el archivo .proto antes de implementar

---

## 🏗️ Estructura de Tests

### Estructura de Directorios

```
services/
└── {service_name}/
    ├── __init__.py
    ├── config.py              # Configuración específica del servicio
    ├── data_schema.py         # Modelos Pydantic (DTOs)
    ├── {service}_page.py      # Page Object Model
    └── modules/
        ├── __init__.py
        ├── _01_register_flow.py
        ├── _02_login_flow.py
        ├── _03_user_operations.py
        └── _99_cleanup.py
```

### Convenciones de Nomenclatura

| Elemento | Convención | Ejemplo |
|----------|------------|---------|
| Directorio | snake_case | `auth_service` |
| Archivo Page | `{nombre}_page.py` | `auth_page.py` |
| Clase Page | PascalCase | `AuthServicePage` |
| Métodos Page | `do_*` | `do_register()`, `do_login()` |
| Módulos de Test | `_XX_descripcion.py` | `_01_register_flow.py` |
| Modelos Pydantic | PascalCase | `RegisterRequest`, `UserResponse` |

---

## ⚠️ Patrones Obligatorios

### 1. Imports Absolutos (OBLIGATORIO)

```python
# ❌ NUNCA uses imports relativos
from ..data_schema import RegisterRequest  # PROHIBIDO
from .auth_page import AuthPage             # PROHIBIDO

# ✅ SIEMPRE usa imports absolutos desde services/
from services.auth_service.data_schema import RegisterRequest
from services.auth_service.auth_page import AuthServicePage
```

### 2. Modelos Pydantic con Java-Compatibility (OBLIGATORIO)

```python
from pydantic import BaseModel, Field, EmailStr
from typing import Optional

class RefreshTokenRequest(BaseModel):
    """SIEMPRE incluye estas configuraciones."""
    model_config = {"populate_by_name": True}

    # Campos compuestos SIEMPRE con alias camelCase
    refresh_token: str = Field(
        ...,
        alias="refreshToken",
        serialization_alias="refreshToken"
    )

class LoginRequest(BaseModel):
    """Campos simples no necesitan alias."""
    model_config = {"populate_by_name": True}

    email: EmailStr
    password: str
```

### 3. Serialización con `by_alias=True` (OBLIGATORIO)

```python
# ❌ NUNCA sin by_alias=True
response = self.post(
    ENDPOINTS["login"],
    data=request.model_dump()  # ❌ Envía refresh_token en lugar de refreshToken
)

# ✅ SIEMPRE con by_alias=True
response = self.post(
    ENDPOINTS["login"],
    data=request.model_dump(by_alias=True)  # ✅ Envía refreshToken
)
```

### 4. Métodos de Page con Prefijo `do_` (OBLIGATORIO)

```python
class AuthPage(BasePage):
    def __init__(self, base_url: str, **kwargs):
        super().__init__(base_url=base_url, **kwargs)
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None

    # ✅ Prefijo do_ para evitar conflictos con atributos
    def do_refresh_token(self) -> APIResponse:
        """Refresh access token."""
        pass

    def do_logout(self) -> APIResponse:
        """Logout user."""
        pass
```

### 5. Headers de Autenticación Manuales (OBLIGATORIO)

```python
class AuthPage(BasePage):
    def __init__(self, base_url: str, **kwargs):
        super().__init__(base_url=base_url, **kwargs)
        self.access_token: Optional[str] = None

    def _get_headers(self, extra: Optional[Dict] = None) -> Dict[str, str]:
        """SIEMPRE implementa _get_headers() manualmente."""
        headers = {"Content-Type": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        if extra:
            headers.update(extra)
        return headers

    def do_protected_request(self):
        """Usa _get_headers() en métodos que necesiten auth."""
        headers = self._get_headers()
        return self.get("/protected", headers=headers)
```

---

## 📚 API del Framework

### BasePage - Métodos HTTP

```python
from socialseed_e2e import BasePage

page = BasePage("https://api.example.com")
page.setup()

# GET
response = page.get("/users/123", headers={"Authorization": "Bearer token"})

# POST - con data (dict o string)
response = page.post("/users", data={"name": "John", "email": "john@example.com"})

# POST - con json (alias para data)
response = page.post("/users", json={"name": "John", "email": "john@example.com"})

# PUT
response = page.put("/users/123", json={"name": "Jane"})

# PATCH
response = page.patch("/users/123", json={"status": "active"})

# DELETE - sin body
response = page.delete("/users/123")

# DELETE - con body (para APIs no estándar)
response = page.delete("/auth/roles/remove", json={"userId": "123", "role": "ADMIN"})

page.teardown()
```

### BasePage - Métodos de Asertión

```python
# Asertión de status code
page.assert_status(response, 200)
page.assert_status(response, [200, 201])

# Asertión de rango 2xx
page.assert_ok(response)

# Asertión de JSON
response_data = page.assert_json(response)
user_id = page.assert_json(response, key="data.id")
nested = page.assert_json(response, key="data.user.profile.name")

# Asertión de headers
content_type = page.assert_header(response, "Content-Type")
page.assert_header(response, "Content-Type", "application/json")

# Validación de esquema (JSON Schema o Pydantic)
from services.auth_service.data_schema import UserResponse
page.assert_schema(response, UserResponse)
```

### BasePage - Health Checks

```python
# Verificar si el servicio está saludable
health = page.check_health()
if health.healthy:
    print(f"Service is healthy (response time: {health.response_time_ms}ms)")

# Esperar a que el servicio esté saludable
try:
    page.wait_for_healthy(timeout=30, interval=1.0)
    print("Service is ready!")
except BasePageError:
    print("Service did not become healthy in time")

# Método de clase para esperar sin instancia persistente
BasePage.wait_for_service("http://localhost:8081", timeout=60)
```

### BasePage - Interceptores

```python
# Agregar interceptor de respuesta
page.add_response_interceptor(lambda resp: print(f"Response: {resp.status}"))

# Limpiar interceptores
page.clear_response_interceptors()
```

### BasePage - Estadísticas

```python
# Obtener estadísticas de requests
stats = page.get_request_stats()
print(f"Total requests: {stats['total_requests']}")
print(f"Successful: {stats['successful_requests']}")
print(f"Failed: {stats['failed_requests']}")
print(f"Average duration: {stats['average_duration_ms']:.2f}ms")
```

---

## 🔄 Flujo de Trabajo

### Paso 1: Analizar el Controlador REST

Cuando el usuario te proporcione código Java de controladores:

1. **Identificar endpoints**: Anotar todas las rutas, métodos HTTP y parámetros
2. **Identificar DTOs**: Registrar todos los request/response bodies
3. **Identificar autenticación**: Notar qué endpoints requieren auth
4. **Identificar flujos**: Agrupar endpoints en flujos lógicos

### Paso 2: Crear data_schema.py

```python
"""Data schema for {service} API."""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Set, List
from datetime import datetime
from uuid import UUID

# =============================================================================
# Request DTOs
# =============================================================================

class RegisterRequest(BaseModel):
    """Registration request."""
    model_config = {"populate_by_name": True}

    username: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    """Login request."""
    model_config = {"populate_by_name": True}

    email: EmailStr
    password: str

# ... más modelos

# =============================================================================
# Response DTOs
# =============================================================================

class AuthResponse(BaseModel):
    """Authentication response."""
    model_config = {"populate_by_name": True}

    token: str
    refresh_token: str = Field(
        alias="refreshToken",
        serialization_alias="refreshToken"
    )
    roles: Set[str]

# =============================================================================
# Endpoint Constants
# =============================================================================

ENDPOINTS = {
    "register": "/auth/register",
    "login": "/auth/login",
    "logout": "/auth/logout",
    "refresh": "/auth/token/refresh",
    # ... más endpoints
}

# =============================================================================
# Test Data
# =============================================================================

TEST_USERS = {
    "regular": {
        "username": "testuser_e2e",
        "email": "testuser_e2e@example.com",
        "password": "TestPassword123!"
    },
    "admin": {
        "username": "admin_e2e",
        "email": "admin_e2e@example.com",
        "password": "AdminPassword123!"
    }
}
```

### Paso 3: Crear {service}_page.py

```python
"""Page object for {service} API."""
from typing import Optional, Dict, Any
from playwright.sync_api import APIResponse
from socialseed_e2e import BasePage

from services.{service}.data_schema import (
    ENDPOINTS,
    RegisterRequest,
    LoginRequest,
    # ... otros imports
)


class {Service}Page(BasePage):
    """Page object for {service} service API."""

    def __init__(self, base_url: str, **kwargs):
        super().__init__(base_url=base_url, **kwargs)
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.current_user: Optional[Dict[str, Any]] = None

    def _get_headers(self, extra: Optional[Dict] = None) -> Dict[str, str]:
        """Build headers with authentication if available."""
        headers = {"Content-Type": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        if extra:
            headers.update(extra)
        return headers

    def do_register(self, request: RegisterRequest) -> APIResponse:
        """Register a new user."""
        response = self.post(
            ENDPOINTS["register"],
            data=request.model_dump(by_alias=True)  # ✅ SIEMPRE by_alias=True
        )
        if response.ok:
            data = response.json().get("data", {})
            self.current_user = data
        return response

    def do_login(self, request: LoginRequest) -> APIResponse:
        """Login and store tokens."""
        response = self.post(
            ENDPOINTS["login"],
            data=request.model_dump(by_alias=True)  # ✅ SIEMPRE by_alias=True
        )
        if response.ok:
            data = response.json().get("data", {})
            self.access_token = data.get("token")
            self.refresh_token = data.get("refreshToken")
        return response

    # ... más métodos
```

### Paso 4: Crear Módulos de Test

```python
"""Test module 01: User registration flow."""
from services.{service}.data_schema import RegisterRequest, TEST_USERS

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.{service}.{service}_page import {Service}Page


def run(page: "{Service}Page"):
    """Execute user registration test."""
    print("STEP 01: Testing User Registration")

    user_data = TEST_USERS["regular"]
    register_request = RegisterRequest(
        username=user_data["username"],
        email=user_data["email"],
        password=user_data["password"]
    )

    response = page.do_register(register_request)

    assert response.ok, f"Registration failed: {response.status} - {response.text()[:200]}"

    response_data = response.json()
    assert "data" in response_data, "No data in response"

    user_info = response_data["data"]
    assert user_info["username"] == user_data["username"], f"Username mismatch"

    # Store user info for later tests
    page.current_user = user_info
    page.current_user_id = str(user_info.get("id"))

    print(f"✓ Registration successful")
    print(f"✓ User ID: {page.current_user_id}")
```

---

## 📖 Ejemplos Completos

### Ejemplo 1: API de Autenticación JWT

```python
# services/auth_service/data_schema.py
from pydantic import BaseModel, Field, EmailStr
from typing import Optional

class LoginRequest(BaseModel):
    model_config = {"populate_by_name": True}
    email: EmailStr
    password: str

class AuthResponse(BaseModel):
    model_config = {"populate_by_name": True}
    token: str
    refresh_token: str = Field(alias="refreshToken", serialization_alias="refreshToken")

ENDPOINTS = {
    "login": "/api/auth/login",
    "refresh": "/api/auth/refresh",
}

TEST_USER = {
    "email": "test@example.com",
    "password": "Test123!"
}
```

```python
# services/auth_service/auth_page.py
from socialseed_e2e import BasePage
from services.auth_service.data_schema import *

class AuthServicePage(BasePage):
    def __init__(self, base_url: str, **kwargs):
        super().__init__(base_url=base_url, **kwargs)
        self.token: Optional[str] = None

    def _get_headers(self, extra=None):
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if extra:
            headers.update(extra)
        return headers

    def do_login(self, request: LoginRequest) -> APIResponse:
        response = self.post(ENDPOINTS["login"], data=request.model_dump(by_alias=True))
        if response.ok:
            data = response.json()["data"]
            self.token = data["token"]
        return response
```

```python
# services/auth_service/modules/_01_login.py
from services.auth_service.data_schema import LoginRequest, TEST_USER
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.auth_service.auth_page import AuthServicePage

def run(page: "AuthServicePage"):
    print("STEP 01: Login")

    request = LoginRequest(**TEST_USER)
    response = page.do_login(request)

    assert response.ok, f"Login failed: {response.status}"
    assert page.token is not None, "Token not stored"

    print("✓ Login successful")
```

---

## 🚀 Testing de APIs gRPC

El framework también soporta testing de servicios gRPC. Las diferencias principales con REST son:

### 1. Estructura para gRPC

```
services/
└── user_service/
    ├── protos/
    │   ├── user.proto              # Definición del servicio
    │   ├── user_pb2.py            # Generado (no editar)
    │   └── user_pb2_grpc.py       # Generado (no editar)
    ├── user_page.py               # Hereda de BaseGrpcPage
    └── modules/
        ├── _01_create_user.py
        └── _02_get_user.py
```

### 2. Definir Servicio (.proto)

```protobuf
syntax = "proto3";

package user;

service UserService {
  rpc GetUser (GetUserRequest) returns (User);
  rpc CreateUser (CreateUserRequest) returns (User);
}

message User {
  string id = 1;
  string name = 2;
  string email = 3;
}

message GetUserRequest {
  string id = 1;
}

message CreateUserRequest {
  string name = 1;
  string email = 2;
}
```

### 3. Compilar Protos

```bash
python -m grpc_tools.protoc \
  --proto_path=. \
  --python_out=./protos \
  --grpc_python_out=./protos \
  user.proto
```

### 4. Crear Service Page (gRPC)

```python
"""Page for User gRPC service."""

from socialseed_e2e.core.base_grpc_page import BaseGrpcPage
from services.user_service.protos import user_pb2, user_pb2_grpc


class UserServicePage(BaseGrpcPage):
    """Page for testing User gRPC service."""

    def setup(self) -> "UserServicePage":
        """Setup page and register stubs."""
        super().setup()
        # Registrar el stub gRPC
        self.register_stub("user", user_pb2_grpc.UserServiceStub)
        return self

    def do_get_user(self, user_id: str) -> user_pb2.User:
        """Call GetUser method."""
        # Crear mensaje protobuf
        request = user_pb2.GetUserRequest(id=user_id)
        # Llamar al método gRPC
        return self.call("user", "GetUser", request)

    def do_create_user(self, name: str, email: str) -> user_pb2.User:
        """Call CreateUser method."""
        request = user_pb2.CreateUserRequest(name=name, email=email)
        return self.call("user", "CreateUser", request)
```

### 5. Escribir Tests gRPC

```python
"""Test module: Create user via gRPC."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.user_service.user_page import UserServicePage


def run(page: "UserServicePage"):
    """Execute create user test."""
    print("STEP: Create User via gRPC")

    # Llamar al método gRPC
    response = page.do_create_user("John Doe", "john@example.com")

    # Assert - acceder a atributos del mensaje protobuf
    assert response.id, "User ID should not be empty"
    assert response.name == "John Doe"
    assert response.email == "john@example.com"

    # Guardar ID para siguientes tests
    page.set_state("user_id", response.id)
    print(f"✓ Created user: {response.name} (ID: {response.id})")
```

### 6. Diferencias Clave: REST vs gRPC

| Aspecto | REST | gRPC |
|---------|------|------|
| Base Class | `BasePage` | `BaseGrpcPage` |
| Configuración | Endpoints HTTP | Stubs gRPC |
| Requests | Pydantic models | Protobuf messages |
| Response | `APIResponse` | Protobuf message |
| Serialización | `model_dump(by_alias=True)` | No necesaria (protobuf) |
| Headers | `headers` dict | `metadata` en call |

### 7. Manejo de Errores gRPC

```python
import grpc

def run(page):
    try:
        response = page.do_get_user("nonexistent-id")
    except grpc.RpcError as e:
        # Verificar código de error
        assert e.code() == grpc.StatusCode.NOT_FOUND
        print(f"✓ Got expected error: {e.details()}")
```

### 8. Autenticación con Metadata

```python
def do_create_user_with_auth(self, name: str, email: str, token: str):
    """Create user with auth token."""
    request = user_pb2.CreateUserRequest(name=name, email=email)

    # Pasar metadata (headers) en la llamada
    metadata = {"authorization": f"Bearer {token}"}

    return self.call(
        "user",
        "CreateUser",
        request,
        metadata=metadata
    )
```

---

## 🐛 Errores Comunes y Soluciones

### Error 1: "email-validator is not installed"

**Causa**: Falta la dependencia email-validator para Pydantic EmailStr.

**Solución**:
```bash
pip install email-validator>=2.0.0
```

### Error 2: Campos enviados en snake_case en lugar de camelCase

**Causa**: No se usó `by_alias=True` al serializar.

**Solución**:
```python
# ❌ Incorrecto
data = request.model_dump()

# ✅ Correcto
data = request.model_dump(by_alias=True)
```

### Error 3: "cannot import name '_01_register_flow'"

**Causa**: Python no puede importar archivos que comienzan con números.

**Solución**: Nombrar archivos con prefijo underscore:
```bash
01_register_flow.py  →  _01_register_flow.py
```

### Error 4: "No refresh token available"

**Causa**: El test anterior no guardó el estado correctamente.

**Solución**: Asegurarse de guardar en `page`:
```python
def run(page: "AuthPage"):
    response = page.do_login(request)
    if response.ok:
        data = response.json()["data"]
        page.refresh_token = data["refreshToken"]  # Guardar en page
```

### Error 5: ImportError con imports relativos

**Causa**: Uso de imports relativos (`from .. import`).

**Solución**: Usar siempre imports absolutos:
```python
# ❌ Incorrecto
from ..data_schema import LoginRequest

# ✅ Correcto
from services.auth_service.data_schema import LoginRequest
```

### Error 6 (gRPC): "No module named 'user_pb2'"

**Causa**: No se compilaron los archivos .proto.

**Solución**:
```bash
python -m grpc_tools.protoc \
  --proto_path=. \
  --python_out=./protos \
  --grpc_python_out=./protos \
  user.proto
```

### Error 7 (gRPC): "StatusCode.UNAVAILABLE"

**Causa**: Servidor gRPC no está corriendo o dirección incorrecta.

**Solución**:
```python
# Verificar que el servidor esté corriendo
# Verificar host:port correcto
page = UserServicePage("localhost:50051")  # Puerto correcto
```

### Error 8 (gRPC): "Method not found"

**Causa**: Nombre de método no coincide con el definido en .proto.

**Solución**:
```python
# Verificar que el nombre coincida EXACTAMENTE con el proto
# Si el proto tiene: rpc GetUser -> usar "GetUser"
# Si el proto tiene: rpc GetUserById -> usar "GetUserById"

return self.call("user", "GetUser", request)  # Exacto
```

---

## ✅ Checklist Pre-Entrega

Antes de decir "terminado", verifica:

### Estructura y Organización
- [ ] Todos los archivos están en `services/{nombre_servicio}/`
- [ ] Los módulos de test tienen prefijo `_` (ej: `_01_login.py`)
- [ ] Existe `__init__.py` en cada directorio

### Modelos Pydantic
- [ ] Todos los modelos tienen `model_config = {"populate_by_name": True}`
- [ ] Campos compuestos tienen `alias` y `serialization_alias` en camelCase
- [ ] Se usa `EmailStr` para emails (requiere email-validator)

### Page Object
- [ ] La clase hereda de `BasePage`
- [ ] Implementa `_get_headers()` manualmente
- [ ] Métodos usan prefijo `do_` (ej: `do_login()`)
- [ ] Se usa `by_alias=True` en todos los `model_dump()`

### Tests
- [ ] Todos los imports son absolutos (desde `services.`)
- [ ] Usan `TYPE_CHECKING` para importar la Page class
- [ ] La función `run(page)` está bien definida
- [ ] Hay aserciones con mensajes descriptivos
- [ ] Se guarda estado en `page` para tests siguientes

### Validación
- [ ] Ejecutar `python verify_installation.py` pasa todas las pruebas
- [ ] No hay imports relativos (`from ..` o `from .`)
- [ ] No hay errores de sintaxis obvios

### Si es gRPC (adicional)
- [ ] Archivo .proto está definido correctamente
- [ ] Archivos `_pb2.py` y `_pb2_grpc.py` están generados
- [ ] Service Page hereda de `BaseGrpcPage` (no `BasePage`)
- [ ] Stubs registrados en `setup()` con `register_stub()`
- [ ] Se compilan los protos antes de ejecutar tests
- [ ] Servidor gRPC está corriendo antes de los tests

---

## 🎯 Tips para Éxito

1. **Verifica la serialización**:
   ```python
   print(request.model_dump(by_alias=True))
   # Debe mostrar camelCase: {'refreshToken': 'xxx'}
   # NO snake_case: {'refresh_token': 'xxx'}
   ```

2. **Test incremental**:
   - Ejecuta test 01 primero
   - Verifica que el estado se guarda en `page`
   - Luego ejecuta test 02

3. **Manejo de errores**:
   ```python
   assert response.ok, f"Failed: {response.status} - {response.text()[:100]}"
   ```

4. **Compartir estado**:
   - Guarda en `page` (ej: `page.user_id = data["id"]`)
   - Recupera en siguiente test

---

## 🤖 Generación Autónoma de Tests (Issue #185) - NUEVO

### ¿Qué es la Generación Autónoma?

El framework ahora puede **generar automáticamente tests completos** analizando tu código fuente. No necesitas escribir los tests manualmente - el sistema:

1. **Analiza tu código** y detecta endpoints
2. **Entiende las relaciones** entre endpoints (registro → login → perfil)
3. **Parsea modelos de base de datos** (SQLAlchemy, Prisma, Hibernate)
4. **Genera datos de prueba** válidos basados en constraints
5. **Crea tests de flujo** completos con validaciones

### Cuándo Usar la Generación Autónoma

**✅ Úsala cuando:**
- Tienes una API existente con muchos endpoints
- Quieres tests rápidamente sin escribir código manualmente
- Necesitas cubrir casos edge y validaciones automáticamente
- Tu API tiene flujos complejos que deben probarse en secuencia

**❌ No la uses cuando:**
- Necesitas tests altamente personalizados con lógica de negocio específica
- Tu API no sigue patrones REST estándar
- Quieres control total sobre cada detalle del test

### Paso a Paso: Generación de Tests

#### Paso 1: Preparar el Proyecto

```bash
# Asegúrate de estar en un proyecto E2E inicializado
cd /path/to/your/api-project

# Inicializar si no existe
e2e init

# Generar manifest del proyecto (esto analiza tu código)
e2e manifest
```

#### Paso 2: Generar Tests Automáticamente

```bash
# Generar tests para TODOS los servicios detectados
e2e generate-tests

# O generar para un servicio específico
e2e generate-tests --service users-api

# Preview sin crear archivos (recomendado primero)
e2e generate-tests --dry-run

# Generar solo tests de validación edge case
e2e generate-tests --strategy edge
```

#### Paso 3: Revisar lo Generado

El comando creará esta estructura:

```
services/{service_name}/
├── __init__.py
├── data_schema.py          # ← DTOs detectados + datos de prueba
├── {service_name}_page.py  # ← Page object con métodos de flujo
└── modules/
    ├── __init__.py
    ├── _01_auth_flow.py    # ← Flujo: Registro → Login → Perfil
    ├── _02_crud_flow.py    # ← Flujo: Create → Read → Update → Delete
    └── _99_validation_tests.py  # ← Tests de validación automáticos
```

#### Paso 4: Ejecutar los Tests Generados

```bash
# Ejecutar todos los tests
e2e run

# Ejecutar solo un servicio
e2e run --service users-api

# Ejecutar un flujo específico
e2e run --service users-api --module _01_auth_flow
```

### Cómo Funciona la Detección de Flujos

El sistema detecta automáticamente estos patrones:

#### Flujo de Autenticación
```
POST /auth/register  →  POST /auth/login  →  GET /auth/me
    (guarda datos)       (guarda token)        (usa token)
```

#### Flujo CRUD
```
POST /users       →  GET /users/{id}  →  PUT /users/{id}  →  DELETE /users/{id}
(guarda user_id)      (verifica datos)      (actualiza)         (elimina)
```

#### Flujos Personalizados
Si detecta patrones como `/checkout` → `/payment` → `/confirm`, crea un flujo de checkout automáticamente.

### Personalizar Datos de Prueba

Edita `data_schema.py` después de generarlo:

```python
# En services/users-api/data_schema.py

TEST_DATA = {
    "auth_flow": {
        "register": {
            "email": "tu-email@empresa.com",  # ← Personaliza esto
            "password": "TuPasswordSeguro123!",
            "username": "usuario_prueba"
        },
        "login": {
            "email": "tu-email@empresa.com",  # ← Debe coincidir con register
            "password": "TuPasswordSeguro123!"
        }
    }
}
```

### Estrategias de Generación de Datos

El sistema soporta múltiples estrategias:

```bash
# Valid - Datos que deberían funcionar (default)
e2e generate-tests --strategy valid

# Invalid - Datos que deberían fallar validación
e2e generate-tests --strategy invalid

# Edge - Casos límite (min, max, vacíos)
e2e generate-tests --strategy edge

# Chaos - Datos aleatorios/fuzzy
e2e generate-tests --strategy chaos

# All - Todas las estrategias
e2e generate-tests --strategy all
```

### Ejemplo Completo: API de Usuarios

Supongamos que tienes esta API:

```java
// Tu código Java (Spring Boot)
@RestController
@RequestMapping("/api/users")
public class UserController {

    @PostMapping("/register")
    public ResponseEntity<User> register(@RequestBody RegisterRequest request) {
        // ...
    }

    @PostMapping("/login")
    public ResponseEntity<AuthResponse> login(@RequestBody LoginRequest request) {
        // ...
    }

    @GetMapping("/me")
    public ResponseEntity<User> getCurrentUser(@AuthenticationPrincipal User user) {
        // ...
    }
}
```

**Generas tests automáticamente:**

```bash
e2e manifest
e2e generate-tests --service users-api
```

**El sistema genera:**

```python
# services/users-api/modules/_01_user_authentication_flow.py

def run(page: UsersApiPage) -> APIResponse:
    """Execute User Authentication Flow.

    Steps:
    1. Register new user
    2. Login with credentials
    3. Access protected profile
    """
    # Step 1: Register
    register_data = TEST_DATA["auth_flow"]["register_user"]
    register_request = RegisterRequest(**register_data)
    response = page.do_register(register_request)
    assert response.ok, "Registration failed"

    # Step 2: Login
    login_data = TEST_DATA["auth_flow"]["login_user"]
    login_request = LoginRequest(**login_data)
    response = page.do_login(login_request)
    assert response.ok, "Login failed"

    # Step 3: Get profile (uses token from login)
    response = page.do_get_current_user()
    assert response.ok, "Get profile failed"

    return response
```

### Tests de Validación Generados

Para cada campo con validaciones, genera tests automáticos:

```python
# services/users-api/modules/_99_validation_tests.py

def test_register_username_below_minimum():
    """Test username with less than 3 characters should fail."""
    data = {
        "username": "ab",  # Less than min_length=3
        "email": "test@example.com",
        "password": "Password123!"
    }
    request = RegisterRequest(**data)
    response = page.do_register(request)
    assert response.status == 400, "Should fail with 400"

def test_register_email_invalid_format():
    """Test invalid email format should fail."""
    data = {
        "username": "testuser",
        "email": "not-an-email",  # Invalid format
        "password": "Password123!"
    }
    request = RegisterRequest(**data)
    response = page.do_register(request)
    assert response.status == 400, "Should fail with 400"
```

### Mejores Prácticas para Agentes

**1. Siempre revisa los tests generados**

```bash
# Primero dry-run para ver qué se generará
e2e generate-tests --dry-run

# Luego genera y revisa
e2e generate-tests
vim services/users-api/data_schema.py  # Revisa los datos
```

**2. Personaliza los datos de prueba**

Los tests generados usan datos genéricos. Actualízalos a valores reales:

```python
# Antes (generado automáticamente)
"email": "testuser_123@example.com"

# Después (personalizado)
"email": "test@miempresa.com"
```

**3. Ejecuta incrementalmente**

```bash
# Primero un solo flujo
e2e run --service users-api --module _01_auth_flow

# Si funciona, ejecuta todos
e2e run --service users-api
```

**4. Añade tests personalizados después**

Los tests generados cubren el 80% de los casos. Añade tests manuales para casos específicos:

```bash
# Crear test manual adicional
e2e new-test custom_scenario --service users-api
```

### Troubleshooting de Generación Autónoma

#### "No flows detected"

**Problema**: El sistema no detecta flujos en tu API.

**Solución**: Asegúrate de que tus endpoints tengan nombres descriptivos:
```java
// ❌ Mal - Nombres genéricos
@PostMapping("/action1")
@PostMapping("/process")

// ✅ Bien - Nombres descriptivos
@PostMapping("/register")
@PostMapping("/login")
```

#### "No database models found"

**Problema**: No detecta modelos de base de datos.

**Solución**: Verifica ubicaciones:
```
# SQLAlchemy
models.py, db.py, database.py

# Prisma
prisma/schema.prisma o schema.prisma

# Hibernate
src/main/java/**/model/*.java
```

#### "Validation tests fail"

**Problema**: Los tests de validación generados fallan.

**Solución**: Revisa las validaciones detectadas en `data_schema.py`:
```python
VALIDATION_RULES = {
    "RegisterRequest": {
        "username": {
            "min_length": 3,  # ← ¿Es correcto?
            "max_length": 50
        }
    }
}
```

### Flujo de Trabajo Recomendado para Agentes

Cuando un usuario te pida tests para su API:

**OPCIÓN A: API Existente (Usar Generación Autónoma)**
```bash
# 1. Verificar si hay código fuente
ls /path/to/project

# 2. Si hay código, usar generación autónoma
e2e init
e2e manifest
e2e generate-tests --dry-run  # Mostrar al usuario

# 3. Generar y personalizar
e2e generate-tests
# Editar data_schema.py con datos reales

# 4. Ejecutar
e2e run
```

**OPCIÓN B: API Nueva o Sin Código (Manual)**
```bash
# 1. Crear servicio manualmente
e2e new-service users-api

# 2. Implementar tests manualmente según AGENT_GUIDE.md
# ... crear data_schema.py, page.py, tests ...

# 3. Ejecutar
e2e run
```

### Prompt Sugerido para Usuarios

Si un usuario quiere usar la generación autónoma, diles:

> "Para generar tests automáticamente para tu API, ejecuta estos comandos:
>
> ```bash
> e2e manifest
> e2e generate-tests
> ```
>
> Esto analizará tu código fuente y generará tests completos basados en tus endpoints y modelos de base de datos. Luego revisa y personaliza los datos en `services/{nombre}/data_schema.py`."

---

**Versión**: 2.1
**Fecha**: 2026-02-08
**Feature**: Issue #185 - Autonomous Test Generation

---

## 📞 Soporte

Si encuentras problemas:

1. Revisa la [documentación del framework](https://github.com/daironpf/socialseed-e2e)
2. Consulta los ejemplos en `/examples/`
3. Ejecuta `e2e doctor` para verificar la instalación

---

**Versión**: 2.0
**Fecha**: 2026-02-04
**Framework**: socialseed-e2e v0.2.0+
