# QuickStart Guide - socialseed-e2e

**Meta:** Que cualquier agente de IA pueda empezar a usar el framework en 5 minutos sin leer código fuente.

---

## 🎯 TL;DR - Comandos Esenciales

```bash
# 1. Inicializar proyecto
e2e init my-project
cd my-project

# 2. Crear servicio
e2e new-service users-api

# 3. Editar archivos generados (obligatorio)
# - services/users-api/data_schema.py
# - services/users-api/users_api_page.py

# 4. Ejecutar tests
e2e run

# 5. Ver reporte
open e2e_reports/traceability_report.html
```

---

## 📋 Pre-requisitos

### Instalación
```bash
pip install socialseed-e2e
```

### Verificar instalación
```bash
e2e doctor
```

**Output esperado:**
- ✓ Python 3.x
- ✓ Playwright
- ✓ Pydantic v2
- ✓ Configuration

---

## 🚀 Flujo de Trabajo Estándar

### Paso 1: Inicializar Proyecto
```bash
e2e init nombre-proyecto
```

**Genera:**
```
nombre-proyecto/
├── e2e.conf              # Configuración principal
├── services/             # Tus APIs a testear
│   └── example/          # Servicio de ejemplo
├── tests/                # Tests adicionales
├── .agent/               # Documentación para IA
└── requirements.txt
```

### Paso 2: Configurar Servicio

**Editar `e2e.conf`:**
```yaml
services:
  users-api:
    base_url: http://localhost:8080
    health_endpoint: /actuator/health
    required: true

settings:
  timeout: 30000
  verbose: true
```

### Paso 3: Crear Estructura del Servicio
```bash
e2e new-service users-api
```

**Genera:**
```
services/users-api/
├── __init__.py
├── config.py              # Config específica
├── data_schema.py         # DTOs y endpoints
├── users_api_page.py      # Page Object Model
└── modules/               # Tests
    ├── __init__.py
    └── 01_health_flow.py
```

### Paso 4: Definir Data Schema

**Editar `services/users-api/data_schema.py`:**
```python
from pydantic import BaseModel, Field, EmailStr
from typing import Optional

# ==================== DTOs ====================
class RegisterRequest(BaseModel):
    model_config = {"populate_by_name": True}
    
    email: EmailStr
    password: str
    username: str

class LoginRequest(BaseModel):
    model_config = {"populate_by_name": True}
    
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    model_config = {"populate_by_name": True}
    
    id: str
    email: str
    username: str
    token: Optional[str] = None

# ==================== Endpoints ====================
ENDPOINTS = {
    "register": "/api/v1/users/register",
    "login": "/api/v1/users/login",
    "profile": "/api/v1/users/profile",
    "health": "/actuator/health"
}

# ==================== Test Data ====================
TEST_USER = {
    "email": "test@example.com",
    "password": "Test123!",
    "username": "testuser"
}
```

**REGLAS OBLIGATORIAS:**
- ✅ SIEMPRE incluir `model_config = {"populate_by_name": True}`
- ✅ Usar `EmailStr` para emails (requiere `email-validator`)
- ✅ Definir `ENDPOINTS` como diccionario
- ✅ Usar `Optional` para campos nullable

### Paso 5: Implementar Page Object

**Editar `services/users-api/users_api_page.py`:**
```python
from typing import Optional, Dict, Any
from playwright.sync_api import APIResponse
from socialseed_e2e.core.base_page import BasePage

from .data_schema import (
    ENDPOINTS,
    RegisterRequest,
    LoginRequest,
    UserResponse,
)

class UsersApiPage(BasePage):
    """Page Object para Users API."""
    
    def __init__(self, base_url: str, **kwargs):
        super().__init__(base_url=base_url, **kwargs)
        self.access_token: Optional[str] = None
        self.current_user: Optional[Dict] = None
    
    def _get_headers(self, extra: Optional[Dict] = None) -> Dict[str, str]:
        """Obtener headers con autenticación."""
        headers = {"Content-Type": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        if extra:
            headers.update(extra)
        return headers
    
    def do_register(self, request: RegisterRequest) -> APIResponse:
        """Registrar nuevo usuario."""
        response = self.post(
            ENDPOINTS["register"],
            data=request.model_dump(by_alias=True)  # ✅ SIEMPRE by_alias=True
        )
        if response.ok:
            data = response.json()
            if "data" in data:
                self.current_user = data["data"]
        return response
    
    def do_login(self, request: LoginRequest) -> APIResponse:
        """Login y almacenar token."""
        response = self.post(
            ENDPOINTS["login"],
            data=request.model_dump(by_alias=True)
        )
        if response.ok:
            data = response.json()
            if "data" in data:
                self.access_token = data["data"].get("token")
                self.current_user = data["data"]
        return response
    
    def do_get_profile(self) -> APIResponse:
        """Obtener perfil del usuario autenticado."""
        if not self.access_token:
            raise ValueError("No access token available. Login first.")
        return self.get(ENDPOINTS["profile"])
```

**REGLAS OBLIGATORIAS:**
- ✅ SIEMPRE usar `by_alias=True` en `model_dump()`
- ✅ Implementar `_get_headers()` para autenticación
- ✅ Guardar estado en atributos de instancia (`self.access_token`)
- ✅ Usar prefijo `do_` para métodos (evitar conflictos)

### Paso 6: Crear Tests
```bash
e2e new-test register --service users-api
```

**Editar `services/users-api/modules/02_register_flow.py`:**
```python
"""Test: Register flow."""
from services.users_api.data_schema import RegisterRequest, TEST_USER
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.users_api.users_api_page import UsersApiPage

def run(page: "UsersApiPage"):
    """Execute register test."""
    print("STEP: Testing User Registration")
    
    # Crear request
    request = RegisterRequest(
        email=TEST_USER["email"],
        password=TEST_USER["password"],
        username=TEST_USER["username"]
    )
    
    # Ejecutar
    response = page.do_register(request)
    
    # Validar
    assert response.ok, f"Register failed: {response.status} - {response.text()}"
    assert page.current_user is not None, "User not stored"
    assert "id" in page.current_user, "No user ID in response"
    
    print(f"✓ User registered: {page.current_user['id']}")
```

**REGLAS OBLIGATORIAS:**
- ✅ Usar imports absolutos (`from services.xxx`)
- ✅ Type hints con `TYPE_CHECKING`
- ✅ Función `run(page)` como entry point
- ✅ Assertions descriptivos con mensajes de error

### Paso 7: Ejecutar Tests
```bash
# Todos los servicios
e2e run

# Solo un servicio
e2e run --service users-api

# Con verbose
e2e run --verbose

# Generar reporte HTML
e2e run --html-report
```

---

## 🔧 Comandos Útiles

### Diagnóstico
```bash
e2e doctor              # Verificar instalación
e2e config              # Ver configuración
e2e observe             # Detectar servicios activos
e2e lint                # Validar tests
```

### Generación
```bash
e2e init <name>                    # Nuevo proyecto
e2e new-service <name>             # Nuevo servicio
e2e new-test <name> --service <s>  # Nuevo test
e2e setup-ci github                # Templates CI/CD
```

### Análisis
```bash
e2e deep-scan           # Detectar tech stack
e2e manifest            # Generar manifiesto AI
e2e analyze-flaky       # Analizar tests flaky
```

### Instalación de Extras
```bash
e2e install-extras tui        # Terminal UI
e2e install-extras grpc       # Soporte gRPC
e2e install-extras secrets    # Vault/AWS Secrets
```

---

## 🎓 Patrones Comunes

### Patrón 1: Flujo Completo (Register → Login → Action)
```python
# 01_register_flow.py
def run(page):
    response = page.do_register(user_data)
    assert response.ok
    page.user_id = response.json()["data"]["id"]

# 02_login_flow.py  
def run(page):
    response = page.do_login(credentials)
    assert response.ok
    # Token se guarda automáticamente en page.access_token

# 03_authenticated_action.py
def run(page):
    response = page.do_get_profile()
    assert response.ok
```

### Patrón 2: CRUD Lifecycle
```python
# 01_create.py - Crea recurso, guarda ID
# 02_read.py - Lee recurso usando ID
# 03_update.py - Actualiza recurso
# 04_delete.py - Elimina recurso
```

### Patrón 3: Tests con Dependencias
```python
def run(page):
    # Verificar dependencias de tests anteriores
    if not hasattr(page, 'user_id'):
        raise ValueError("Run 01_register_flow first")
    
    # Usar datos previos
    response = page.do_get_user(page.user_id)
    assert response.ok
```

---

## ⚠️ Errores Comunes y Soluciones

### Error: `ImportError: email-validator is not installed`
**Solución:**
```bash
pip install email-validator
```

### Error: `Refresh token is required` (o similar)
**Causa:** No usar `by_alias=True`  
**Solución:**
```python
# ❌ INCORRECTO
data = request.model_dump()

# ✅ CORRECTO
data = request.model_dump(by_alias=True)
```

### Error: `invalid syntax` en módulo generado
**Causa:** Nombre con guiones (`01_health-check_flow.py`)  
**Solución:** Renombrar archivo (usar guiones bajos):
```bash
mv 01_health-check_flow.py 01_health_check_flow.py
```

### Error: `No 'run' function found in module`
**Causa:** El archivo no tiene función `run(page)`  
**Solución:** Asegurar que existe:
```python
def run(page):
    # test logic here
    pass
```

---

## 📊 Estructura de Respuesta HTTP

El framework espera respuestas JSON con esta estructura:
```json
{
  "data": { ... },           // Datos de respuesta
  "message": "success",      // Mensaje opcional
  "status": 200              // Código HTTP
}
```

**Acceder a datos:**
```python
response = page.do_login(request)
data = response.json()
user_data = data["data"]           # Payload principal
token = user_data["token"]         # Token JWT
```

---

## 🧪 Testing Local

### Usar Mock Server (Flask)
```bash
# El proyecto inicializado incluye mock server
python -m pytest tests/ -v
```

### Verificar un servicio específico
```bash
e2e run --service users-api --verbose
```

---

## 📚 Siguientes Pasos

1. **Leer:** `CLI_REFERENCE.md` - Todos los comandos detallados
2. **Leer:** `REST_TESTING.md` - Testing REST avanzado
3. **Leer:** `TROUBLESHOOTING.md` - Más problemas y soluciones
4. **Leer:** `WORKFLOWS.md` - Flujos de trabajo completos

---

## 🆘 Necesitas Ayuda?

1. Verificar instalación: `e2e doctor`
2. Ver configuración: `e2e config`
3. Leer logs con: `e2e run --verbose`
4. Consultar: `TROUBLESHOOTING.md`

---

**Versión:** 1.0  
**Framework:** socialseed-e2e v0.1.2  
**Última actualización:** 2026-02-17
