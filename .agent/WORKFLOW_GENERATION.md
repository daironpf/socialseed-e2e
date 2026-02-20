# Guía de Generación de Tests para Agentes de IA

Sigue este flujo de trabajo cuando el usuario te pida generar tests a partir de su código fuente (Controladores, Routers, etc.).

## 🚨 PASO 0: DETECCIÓN DE PUERTOS (OBLIGATORIO)

**ANTES DE EMPEZAR**, DEBES detectar dónde está corriendo el servicio. **Lee primero:** `SERVICE_DETECTION.md`

### Checklist de Detección

1. **Buscar puerto en configuración:**
   ```bash
   grep -r "port" services/<service-name>/src/main/resources/*.yml
   ```

2. **Verificar servicio activo:**
   ```bash
   curl http://localhost:<puerto_detectado>/actuator/health
   ```

3. **Ver contenedores Docker (si aplica):**
   ```bash
   docker ps --format "table {{.Names}}\t{{.Ports}}"
   ```

4. **Configurar e2e.conf con el puerto correcto:**
   ```yaml
   services:
     <service_name>:
       base_url: http://localhost:<puerto_detectado>
       health_endpoint: /actuator/health
   ```

**⚠️ NUNCA asumas el puerto. Siempre detecta primero.**

---

## IMPORTANT PRINCIPLES

- NO relative imports (from ..x import y) - use absolute imports from `services.xxx.data_schema`
- Always use `by_alias=True` when serializing Pydantic models (REST only)
- Handle authentication headers manually (no `update_headers` method)
- Use `do_*` prefix for methods to avoid name conflicts with attributes
- For gRPC: Compile proto files first, use generated stubs

## Determinar el Tipo de API

Antes de empezar, pregunta al usuario:
- ¿Es una API **REST** (HTTP/JSON)?
- ¿Es una API **gRPC** (Protocol Buffers)?

### Si es REST
Sigue los pasos de esta guía normalmente.

### Si es gRPC
Lee primero: **GRPC_TESTING.md** (guía completa de testing gRPC)

Pasos adicionales para gRPC:
1. Solicitar archivo .proto
2. Compilar: `python -m grpc_tools.protoc --proto_path=. --python_out=./protos --grpc_python_out=./protos service.proto`
3. Heredar de `BaseGrpcPage` en lugar de `BasePage`
4. Registrar stubs gRPC en lugar de configurar endpoints HTTP
5. Crear mensajes protobuf en lugar de Pydantic models

## Paso 1: Entender el Servicio

1. Pide al usuario el path de sus controladores (si no te lo ha dado).
2. Lee los archivos para identificar:
   - Rutas base (ej. `/api/v1/users`).
   - Endpoints específicos (`POST /register`, `POST /login`).
   - Modelos de datos (User, Token, etc.).

## Paso 2: Crear/Actualizar Data Schema (`data_schema.py`)

Define los modelos Pydantic necesarios para interactuar con la API.

```python
# services/users_api/data_schema.py
from pydantic import BaseModel, Field
from typing import Optional

class RegisterRequest(BaseModel):
    email: str = Field(..., alias="emailAddress")
    password: str
    username: str

    class Config:
        populate_by_name = True

# Define constantes para los endpoints
REGISTER_ENDPOINT = "/auth/register"
LOGIN_ENDPOINT = "/auth/login"
```

## Paso 3: Implementar Service Page (`*_page.py`)

Agrega métodos a la clase Page que encapsulen las llamadas a la API. Usa los modelos definidos en el paso anterior.

**CRITICAL RULES:**
- Use `do_*` prefix for all method names (e.g., `do_register`, `do_login`)
- Always use `by_alias=True` when calling `model_dump()`
- Never use `update_headers()` - handle authentication manually

```python
# services/users_api/users_api_page.py
from socialseed_e2e.core.base_page import BasePage
from playwright.sync_api import APIResponse, APIRequestContext
from services.users_api.data_schema import REGISTER_ENDPOINT, LOGIN_ENDPOINT, RegisterRequest

class UsersApiPage(BasePage):
    def __init__(self, base_url: str, **kwargs):
        super().__init__(base_url=base_url, **kwargs)
        self.auth_token = None

    def do_register(self, data: RegisterRequest) -> APIResponse:
        """Registra un nuevo usuario."""
        # ALWAYS use by_alias=True when serializing Pydantic models
        return self.post(
            REGISTER_ENDPOINT,
            data=data.model_dump(by_alias=True)
        )

    def do_login(self, username: str, password: str) -> APIResponse:
        """Login and store token manually."""
        resp = self.post(
            LOGIN_ENDPOINT,
            data={"username": username, "password": password}
        )
        if resp.ok:
            token = resp.json().get("token")
            # GUARDAR ESTADO para siguientes tests
            self.auth_token = token
            # Handle headers manually - NEVER use update_headers()
            self.headers = {**self.headers, "Authorization": f"Bearer {token}"}
        return resp

    def do_authenticate_with_token(self, token: str) -> None:
        """Set auth token manually."""
        self.auth_token = token
        # Manually update headers
        self.headers = {**self.headers, "Authorization": f"Bearer {token}"}
```

## Paso 4: Generar Módulos de Test (`modules/`)

Crea archivos numerados para probar flujos completos. **Es crítico que sean secuenciales.**

### Ejemplo: 01_register_flow.py
```python
# ABSOLUTE import - NEVER use relative imports (from ..data_schema)
from services.users_api.data_schema import RegisterRequest
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.users_api.users_api_page import UsersApiPage

def run(page: 'UsersApiPage'):
    print("Testing Registration...")

    user_data = RegisterRequest(
        email="test@example.com",
        password="Password123!",
        username="testuser"
    )

    response = page.do_register(user_data)

    assert response.ok, f"Registration failed: {response.status} - {response.text()}"
    print("✓ Registration successful")

    # Guardar datos necesarios para siguientes tests en la instancia de page
    page.current_user_email = user_data.email
```

### Ejemplo: 02_login_flow.py
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.users_api.users_api_page import UsersApiPage

def run(page: 'UsersApiPage'):
    print("Testing Login...")

    # Usar datos del paso anterior si es necesario
    email = getattr(page, 'current_user_email', "default@test.com")

    response = page.do_login(email, "Password123!")

    assert response.ok, f"Login failed: {response.status} - {response.text()}"
    assert page.auth_token is not None, "Token not stored after login"
    print("✓ Login successful and token stored")
```

### Ejemplo: 03_authenticated_operation.py
```python
from services.users_api.data_schema import SomeAuthenticatedRequest
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.users_api.users_api_page import UsersApiPage

def run(page: 'UsersApiPage'):
    print("Testing Authenticated Operation...")

    # Ensure we have a token from previous step
    assert page.auth_token, "No auth token available. Run login flow first."

    request_data = SomeAuthenticatedRequest(
        field1="value1",
        field2="value2"
    )

    # Token is automatically in headers from do_login()
    # But we can also set it manually if needed:
    # page.do_authenticate_with_token(page.auth_token)

    response = page.post(
        "/api/protected/endpoint",
        data=request_data.model_dump(by_alias=True)
    )

    assert response.ok, f"Authenticated request failed: {response.status} - {response.text()}"
    print("✓ Authenticated operation successful")
```

## Reglas de Oro
1. **Detectar puerto PRIMERO**: Lee SERVICE_DETECTION.md antes de generar nada
2. **No relative imports**: Use absolute imports like `from services.xxx.data_schema import ...`
3. **by_alias=True**: Always use `model_dump(by_alias=True)` when serializing Pydantic models
4. **No update_headers()**: Handle authentication headers manually by setting `self.headers`
5. **do_* prefix**: Use `do_register`, `do_login`, etc. to avoid name conflicts with attributes
6. **No hardcodees URLs** en los tests; úsalas en `data_schema.py` o en la Page class.
7. **Reutiliza la instancia `page`**: Es el vehículo para compartir estado (tokens, IDs creados) entre tests.
8. **Usa Type Hints**: Ayuda a la legibilidad y previene errores.
9. **Validaciones**: Siempre valida `response.ok` o el status code específico.
10. **Error Handling**: Include descriptive error messages in assertions with `response.text()` for debugging
