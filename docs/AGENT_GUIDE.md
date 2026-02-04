# 🤖 Guía Definitiva para Agentes de IA - SocialSeed E2E Framework

> **Versión 2.0 - Framework Refactorizado**
>
> Esta guía permite a los agentes de IA generar tests E2E perfectos sin necesidad de ver el código fuente del framework.

## 📋 Índice

1. [Filosofía del Framework](#filosofía-del-framework)
2. [Estructura de Tests](#estructura-de-tests)
3. [Patrones Obligatorios](#patrones-obligatorios)
4. [API del Framework](#api-del-framework)
5. [Flujo de Trabajo](#flujo-de-trabajo)
6. [Ejemplos Completos](#ejemplos-completos)
7. [Errores Comunes y Soluciones](#errores-comunes-y-soluciones)
8. [Checklist Pre-Entrega](#checklist-pre-entrega)

---

## 🎯 Filosofía del Framework

### Principios Fundamentales

1. **Page Object Model**: Cada servicio tiene una clase Page que hereda de `BasePage`
2. **Tests Secuenciales**: Los tests se ejecutan en orden numérico y comparten estado
3. **Aserciones Explícitas**: Cada test debe validar el resultado
4. **Sin Importaciones Relativas**: Solo imports absolutos permitidos
5. **Java-Compatible**: Serialización camelCase para backends Spring Boot

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

## 📞 Soporte

Si encuentras problemas:

1. Revisa la [documentación del framework](https://github.com/daironpf/socialseed-e2e)
2. Consulta los ejemplos en `/examples/`
3. Ejecuta `e2e doctor` para verificar la instalación

---

**Versión**: 2.0
**Fecha**: 2026-02-04
**Framework**: socialseed-e2e v0.2.0+
