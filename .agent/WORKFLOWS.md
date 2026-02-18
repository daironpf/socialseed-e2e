# Workflows - socialseed-e2e

**Meta:** Flujos de trabajo completos y reutilizables para casos de uso comunes.

---

## 📋 Índice de Workflows

1. [Workflow Básico: REST API](#workflow-1-rest-api-básico)
2. [Workflow Autenticación JWT](#workflow-2-autenticación-jwt)
3. [Workflow CRUD Completo](#workflow-3-crud-completo)
4. [Workflow Microservicios](#workflow-4-microservicios)
5. [Workflow gRPC](#workflow-5-grpc)
6. [Workflow con Mocks](#workflow-6-con-mocks-externos)
7. [Workflow CI/CD](#workflow-7-ci-cd)
8. [Workflow AI-First](#workflow-8-ai-first)

---

## Workflow 1: REST API Básico

**Escenario:** API REST simple sin autenticación

### Paso 1: Inicializar
```bash
e2e init my-project
cd my-project
```

### Paso 2: Configurar
**e2e.conf:**
```yaml
services:
  public-api:
    base_url: http://localhost:8080
    health_endpoint: /health
    required: true

settings:
  timeout: 30000
  verbose: true
```

### Paso 3: Crear Servicio
```bash
e2e new-service public-api
```

### Paso 4: Implementar

**data_schema.py:**
```python
from pydantic import BaseModel
from typing import Optional, List

class Item(BaseModel):
    model_config = {"populate_by_name": True}
    
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    price: float

class ItemList(BaseModel):
    model_config = {"populate_by_name": True}
    
    items: List[Item]
    total: int

ENDPOINTS = {
    "list": "/api/v1/items",
    "create": "/api/v1/items",
    "get": "/api/v1/items/{id}",
    "update": "/api/v1/items/{id}",
    "delete": "/api/v1/items/{id}"
}

TEST_ITEM = {
    "name": "Test Product",
    "description": "A test product",
    "price": 29.99
}
```

**public_api_page.py:**
```python
from typing import Optional, Dict, Any
from playwright.sync_api import APIResponse
from socialseed_e2e.core.base_page import BasePage

from .data_schema import ENDPOINTS, Item, ItemList

class PublicApiPage(BasePage):
    def __init__(self, base_url: str, **kwargs):
        super().__init__(base_url=base_url, **kwargs)
        self.created_item_id: Optional[str] = None
    
    def do_list_items(self) -> APIResponse:
        """List all items."""
        return self.get(ENDPOINTS["list"])
    
    def do_create_item(self, item: Item) -> APIResponse:
        """Create a new item."""
        return self.post(
            ENDPOINTS["create"],
            data=item.model_dump(by_alias=True, exclude={"id"})
        )
    
    def do_get_item(self, item_id: str) -> APIResponse:
        """Get item by ID."""
        path = ENDPOINTS["get"].format(id=item_id)
        return self.get(path)
    
    def do_update_item(self, item_id: str, item: Item) -> APIResponse:
        """Update an item."""
        path = ENDPOINTS["update"].format(id=item_id)
        return self.put(path, data=item.model_dump(by_alias=True))
    
    def do_delete_item(self, item_id: str) -> APIResponse:
        """Delete an item."""
        path = ENDPOINTS["delete"].format(id=item_id)
        return self.delete(path)
```

### Paso 5: Crear Tests
```bash
e2e new-test list-items --service public-api
e2e new-test create-item --service public-api
e2e new-test item-lifecycle --service public-api
```

**modules/02_create_item_flow.py:**
```python
from services.public_api.data_schema import Item, TEST_ITEM
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.public_api.public_api_page import PublicApiPage

def run(page: "PublicApiPage"):
    print("STEP: Create Item")
    
    item = Item(**TEST_ITEM)
    response = page.do_create_item(item)
    
    assert response.ok, f"Create failed: {response.text()}"
    
    data = response.json()["data"]
    page.created_item_id = data["id"]
    
    print(f"✓ Created item: {page.created_item_id}")
```

**modules/03_item_lifecycle_flow.py:**
```python
from services.public_api.data_schema import Item
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.public_api.public_api_page import PublicApiPage

def run(page: "PublicApiPage"):
    print("STEP: Item Lifecycle (CRUD)")
    
    # Dependencia del test anterior
    assert hasattr(page, 'created_item_id'), "Run 02_create_item first"
    item_id = page.created_item_id
    
    # READ
    response = page.do_get_item(item_id)
    assert response.ok, "Get item failed"
    
    # UPDATE
    updated_item = Item(
        id=item_id,
        name="Updated Product",
        description="Updated description",
        price=39.99
    )
    response = page.do_update_item(item_id, updated_item)
    assert response.ok, "Update failed"
    
    # DELETE
    response = page.do_delete_item(item_id)
    assert response.ok, "Delete failed"
    
    # VERIFY DELETION
    response = page.do_get_item(item_id)
    assert response.status == 404, "Item should not exist"
    
    print("✓ Full CRUD lifecycle passed")
```

### Paso 6: Ejecutar
```bash
e2e run --service public-api
```

---

## Workflow 2: Autenticación JWT

**Escenario:** API con login/registro y endpoints protegidos

### Estructura

**data_schema.py:**
```python
from pydantic import BaseModel, Field, EmailStr
from typing import Optional

# Requests
class RegisterRequest(BaseModel):
    model_config = {"populate_by_name": True}
    
    email: EmailStr
    password: str
    username: str

class LoginRequest(BaseModel):
    model_config = {"populate_by_name": True}
    
    email: EmailStr
    password: str

class RefreshTokenRequest(BaseModel):
    model_config = {"populate_by_name": True}
    
    refresh_token: str = Field(
        ...,
        alias="refreshToken",
        serialization_alias="refreshToken"
    )

# Responses
class AuthResponse(BaseModel):
    model_config = {"populate_by_name": True}
    
    token: str
    refresh_token: str = Field(alias="refreshToken")
    expires_in: int = Field(alias="expiresIn")

class UserProfile(BaseModel):
    model_config = {"populate_by_name": True}
    
    id: str
    email: str
    username: str

ENDPOINTS = {
    "register": "/api/v1/auth/register",
    "login": "/api/v1/auth/login",
    "refresh": "/api/v1/auth/refresh",
    "logout": "/api/v1/auth/logout",
    "profile": "/api/v1/users/profile",
    "health": "/actuator/health"
}

TEST_USER = {
    "email": "test@example.com",
    "password": "SecurePass123!",
    "username": "testuser"
}
```

**auth_page.py:**
```python
from typing import Optional, Dict, Any
from playwright.sync_api import APIResponse
from socialseed_e2e.core.base_page import BasePage

from .data_schema import (
    ENDPOINTS,
    RegisterRequest,
    LoginRequest,
    RefreshTokenRequest,
    AuthResponse,
    UserProfile
)

class AuthPage(BasePage):
    def __init__(self, base_url: str, **kwargs):
        super().__init__(base_url=base_url, **kwargs)
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.user_id: Optional[str] = None
    
    def _get_headers(self, extra: Optional[Dict] = None) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        if extra:
            headers.update(extra)
        return headers
    
    def do_register(self, request: RegisterRequest) -> APIResponse:
        """Register new user."""
        response = self.post(
            ENDPOINTS["register"],
            data=request.model_dump(by_alias=True)
        )
        if response.ok:
            data = response.json()["data"]
            self._update_tokens(data)
            self.user_id = data.get("id")
        return response
    
    def do_login(self, request: LoginRequest) -> APIResponse:
        """Login and store tokens."""
        response = self.post(
            ENDPOINTS["login"],
            data=request.model_dump(by_alias=True)
        )
        if response.ok:
            data = response.json()["data"]
            self._update_tokens(data)
        return response
    
    def do_refresh_token(self) -> APIResponse:
        """Refresh access token."""
        if not self.refresh_token:
            raise ValueError("No refresh token available")
        
        request = RefreshTokenRequest(refresh_token=self.refresh_token)
        response = self.post(
            ENDPOINTS["refresh"],
            data=request.model_dump(by_alias=True)
        )
        if response.ok:
            data = response.json()["data"]
            self._update_tokens(data)
        return response
    
    def do_logout(self) -> APIResponse:
        """Logout and clear tokens."""
        if not self.access_token:
            raise ValueError("No access token available")
        
        response = self.post(ENDPOINTS["logout"])
        if response.ok:
            self.access_token = None
            self.refresh_token = None
        return response
    
    def do_get_profile(self) -> APIResponse:
        """Get authenticated user profile."""
        if not self.access_token:
            raise ValueError("Not authenticated")
        return self.get(ENDPOINTS["profile"])
    
    def _update_tokens(self, data: Dict):
        """Update tokens from response data."""
        self.access_token = data.get("token")
        self.refresh_token = data.get("refreshToken")

    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        return self.access_token is not None
```

### Tests

**01_register_flow.py:**
```python
from services.auth.data_schema import RegisterRequest, TEST_USER
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.auth.auth_page import AuthPage

def run(page: "AuthPage"):
    print("STEP 01: User Registration")
    
    request = RegisterRequest(**TEST_USER)
    response = page.do_register(request)
    
    assert response.ok, f"Registration failed: {response.text()}"
    assert page.is_authenticated(), "Not authenticated after registration"
    assert page.user_id is not None, "No user ID"
    
    print(f"✓ Registered and authenticated: {page.user_id}")
```

**02_login_flow.py:**
```python
from services.auth.data_schema import LoginRequest, TEST_USER
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.auth.auth_page import AuthPage

def run(page: "AuthPage"):
    print("STEP 02: User Login")
    
    # Clear previous auth
    page.access_token = None
    page.refresh_token = None
    
    request = LoginRequest(
        email=TEST_USER["email"],
        password=TEST_USER["password"]
    )
    response = page.do_login(request)
    
    assert response.ok, f"Login failed: {response.text()}"
    assert page.is_authenticated(), "Not authenticated after login"
    
    print("✓ Login successful")
```

**03_authenticated_operations.py:**
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.auth.auth_page import AuthPage

def run(page: "AuthPage"):
    print("STEP 03: Authenticated Operations")
    
    # Verify authenticated
    assert page.is_authenticated(), "Not authenticated"
    
    # Get profile
    response = page.do_get_profile()
    assert response.ok, f"Get profile failed: {response.text()}"
    
    profile_data = response.json()["data"]
    assert profile_data["email"] == "test@example.com"
    
    print("✓ Authenticated operations passed")
```

**04_token_refresh.py:**
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.auth.auth_page import AuthPage

def run(page: "AuthPage"):
    print("STEP 04: Token Refresh")
    
    old_token = page.access_token
    
    response = page.do_refresh_token()
    assert response.ok, f"Token refresh failed: {response.text()}"
    assert page.access_token is not None, "No new access token"
    assert page.access_token != old_token, "Token not refreshed"
    
    print("✓ Token refreshed successfully")
```

**05_logout_flow.py:**
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.auth.auth_page import AuthPage

def run(page: "AuthPage"):
    print("STEP 05: Logout")
    
    response = page.do_logout()
    assert response.ok, f"Logout failed: {response.text()}"
    assert not page.is_authenticated(), "Still authenticated after logout"
    
    # Verify cannot access protected endpoint
    try:
        response = page.do_get_profile()
        assert response.status == 401, "Should be unauthorized"
    except ValueError:
        pass  # Expected - no token
    
    print("✓ Logout successful")
```

---

## Workflow 3: CRUD Completo

**Estructura de tests secuenciales:**

```
modules/
├── 01_create.py       # Crea recurso, guarda ID
├── 02_list.py         # Lista y verifica recurso existe
├── 03_get.py          # Obtiene recurso específico
├── 04_update.py       # Actualiza recurso
├── 05_delete.py       # Elimina recurso
└── 06_verify_delete.py # Verifica que ya no existe
```

**Patrón de estado compartido:**
```python
# 01_create.py
def run(page):
    response = page.do_create(data)
    page.resource_id = response.json()["data"]["id"]
    page.resource_data = data

# 03_get.py  
def run(page):
    assert hasattr(page, 'resource_id'), "Run 01_create first"
    response = page.do_get(page.resource_id)
    assert response.json()["data"]["id"] == page.resource_id
```

---

## Workflow 4: Microservicios

**Escenario:** Múltiples servicios con dependencias

**e2e.conf:**
```yaml
services:
  auth-service:
    base_url: http://localhost:8081
    health_endpoint: /actuator/health
    required: true
    
  users-service:
    base_url: http://localhost:8082
    health_endpoint: /actuator/health
    required: true
    
  orders-service:
    base_url: http://localhost:8083
    health_endpoint: /actuator/health
    required: true

dependencies:
  orders-service:
    - users-service
    - auth-service
```

**Flujo cross-service:**
```python
# orders/modules/01_create_order.py
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.orders.orders_page import OrdersPage
    from services.auth.auth_page import AuthPage

def run(orders_page: "OrdersPage", auth_page: "AuthPage"):
    # 1. Login via auth service
    auth_page.do_login(credentials)
    
    # 2. Use token in orders service
    orders_page.set_auth_token(auth_page.access_token)
    
    # 3. Create order
    response = orders_page.do_create_order(order_data)
    assert response.ok
```

---

## Workflow 5: gRPC

**Preparación:**
```bash
e2e install-extras grpc
```

**Estructura:**
```python
# data_schema.py (con gRPC)
import grpc
from generated import user_pb2, user_pb2_grpc

class UserServiceGrpcPage(BaseGrpcPage):
    def __init__(self, target: str, **kwargs):
        super().__init__(target=target, **kwargs)
        self.channel = grpc.insecure_channel(target)
        self.stub = user_pb2_grpc.UserServiceStub(self.channel)
    
    def do_register(self, request: RegisterRequest):
        grpc_request = user_pb2.RegisterRequest(
            email=request.email,
            password=request.password
        )
        return self.stub.Register(grpc_request)
```

---

## Workflow 6: Con Mocks Externos

```bash
# 1. Analizar dependencias externas
e2e mock-analyze --service payments

# 2. Generar mocks
e2e mock-generate --api stripe --output mocks/

# 3. Ejecutar mocks
e2e mock-run --services stripe,sendgrid

# 4. Configurar e2e.conf para usar mocks
```

**e2e.conf:**
```yaml
services:
  payments:
    base_url: http://localhost:8080
    mock_dependencies:
      stripe: http://localhost:3001
      sendgrid: http://localhost:3002
```

---

## Workflow 7: CI/CD

```bash
# 1. Generar templates
e2e setup-ci github

# 2. Configurar secrets en GitHub
# - E2E_CONFIG_BASE64 (e2e.conf en base64)
# - API_KEYS, etc.

# 3. Ejecutar localmente primero
e2e run --service all

# 4. Push y verificar pipeline
```

**GitHub Actions (generado):**
```yaml
name: E2E Tests
on: [push, pull_request]
jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install socialseed-e2e
          e2e install-extras tui
      - name: Run E2E tests
        run: e2e run --service all
      - name: Upload reports
        uses: actions/upload-artifact@v3
        with:
          name: e2e-reports
          path: e2e_reports/
```

---

## Workflow 8: AI-First

**Flujo automatizado completo:**

```bash
# 1. Detectar todo automáticamente
e2e observe --update-config

# 2. Generar manifiesto
e2e manifest

# 3. Descubrir endpoints
e2e discover --output discovery-report.md

# 4. Planear estrategia
e2e plan-strategy --name "full-coverage" --coverage 90

# 5. Generar tests
e2e generate-tests --strategy all --service all

# 6. Ejecutar con auto-healing
e2e autonomous-run --mode self-healing

# 7. Analizar flaky tests
e2e analyze-flaky --runs 10

# 8. Generar reporte
e2e perf-report --output report.html
```

---

## 🎯 Plantillas Rápidas

### Template: API Pública
```bash
e2e init . && \
e2e new-service api && \
e2e observe --update-config && \
e2e run
```

### Template: API con Auth
```bash
e2e init . && \
e2e new-service auth && \
e2e new-test register --service auth && \
e2e new-test login --service auth && \
e2e run --service auth
```

### Template: CRUD Resource
```bash
e2e new-service resources && \
e2e new-test create --service resources && \
e2e new-test list --service resources && \
e2e new-test update --service resources && \
e2e new-test delete --service resources && \
e2e run --service resources
```

---

**Versión:** 1.0  
**Framework:** socialseed-e2e v0.1.2  
**Última actualización:** 2026-02-17
