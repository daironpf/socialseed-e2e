# Best Practices - socialseed-e2e

**Meta:** Guía de mejores prácticas para escribir tests E2E robustos, mantenibles y escalables.

---

## 📋 Índice

1. [Estructura del Proyecto](#1-estructura-del-proyecto)
2. [Naming Conventions](#2-naming-conventions)
3. [Organización de Tests](#3-organización-de-tests)
4. [Manejo de Datos](#4-manejo-de-datos)
5. [Autenticación](#5-autenticación)
6. [Aserciones](#6-aserciones)
7. [Manejo de Errores](#7-manejo-de-errores)
8. [Performance](#8-performance)
9. [Mantenibilidad](#9-mantenibilidad)
10. [CI/CD](#10-cicd)

---

## 1. Estructura del Proyecto

### ✅ Estructura Recomendada

```
my-project/
├── e2e.conf                      # Configuración principal
├── services/                     # Un directorio por servicio
│   ├── auth-service/            
│   │   ├── __init__.py
│   │   ├── data_schema.py       # DTOs, endpoints, constantes
│   │   ├── auth_service_page.py # Page Object Model
│   │   └── modules/             # Tests
│   │       ├── 01_health.py
│   │       ├── 02_register.py
│   │       ├── 03_login.py
│   │       └── 04_authenticated_flow.py
│   └── users-service/
│       └── ...
├── tests/                        # Tests generales/fixtures
├── .agent/                       # Documentación para IA
└── e2e_reports/                  # Reportes generados
```

### ❌ Estructuras a Evitar

```
❌ NO: Tests dispersos
├── test1.py
├── test2.py
└── random_folder/
    └── test3.py

❌ NO: Múltiples servicios en un mismo page
├── services/
│   └── all_in_one_page.py

❌ NO: Imports relativos
from ..other_service import something
```

---

## 2. Naming Conventions

### Servicios
```python
# ✅ Kebab-case para directorios
services/
├── user-api/           ✓
├── user_api/           ✗
├── UserAPI/            ✗
└── userApi/            ✗
```

### Archivos
```python
# ✅ snake_case para archivos Python
modules/
├── 01_register_flow.py     ✓
├── 01-register-flow.py     ✗
├── 01RegisterFlow.py       ✗
└── 01 register flow.py     ✗

# ✅ Número secuencial con 2 dígitos
01_health.py               ✓
1_health.py                ✗
001_health.py              ✗
```

### Clases
```python
# ✅ PascalCase para clases
class UserServicePage:     ✓
class user_service_page:   ✗
class userServicePage:     ✗
```

### Métodos
```python
# ✅ Prefijo do_ para acciones
def do_register(self):     ✓
def do_login(self):        ✓
def do_get_profile(self):  ✓

# ❌ Sin prefijo (puede colisionar con atributos)
def register(self):        ✗
def login(self):           ✗
```

### Variables
```python
# ✅ snake_case
access_token              ✓
refresh_token             ✓
created_user_id          ✓

accessToken               ✗
refreshToken              ✗
CreatedUserId             ✗
```

---

## 3. Organización de Tests

### Numeración Secuencial

```
modules/
├── 01_health.py              # Siempre primero: verificar servicio activo
├── 02_register.py            # Crear recursos base
├── 03_login.py               # Autenticación
├── 04_crud_operations.py     # Operaciones CRUD
├── 05_edge_cases.py          # Casos límite
├── 06_cleanup.py             # Limpieza (si es necesaria)
└── 99_logout.py              # Siempre último: logout
```

### Dependencias entre Tests

```python
# ✅ Explicitar dependencias en docstring
"""Test: Create user.

Depends on: 01_health.py (servicio debe estar activo)
Provides: page.created_user_id para tests siguientes
"""

def run(page):
    # Guardar estado para tests siguientes
    page.created_user_id = response.json()["data"]["id"]
```

### Tests Independientes (Cuando sea posible)

```python
# ✅ Test independiente (mejor)
def run(page):
    # Setup
    user = create_test_user()
    
    # Test
    response = page.do_action(user)
    
    # Cleanup
    cleanup_user(user)

# ⚠️ Test dependiente (aceptable si es necesario)
def run(page):
    assert hasattr(page, 'user_id'), "Run 01_create first"
    response = page.do_action(page.user_id)
```

---

## 4. Manejo de Datos

### Test Data Builders

```python
# ✅ Builder pattern para datos de test
from dataclasses import dataclass

@dataclass
class UserBuilder:
    email: str = "test@example.com"
    password: str = "Test123!"
    username: str = "testuser"
    
    def with_email(self, email: str) -> "UserBuilder":
        self.email = email
        return self
    
    def with_password(self, password: str) -> "UserBuilder":
        self.password = password
        return self
    
    def build(self) -> RegisterRequest:
        return RegisterRequest(
            email=self.email,
            password=self.password,
            username=self.username
        )

# Uso
user = UserBuilder().with_email("custom@example.com").build()
```

### Data Factories

```python
# ✅ Factory para crear múltiples usuarios
def create_test_users(count: int = 5) -> List[RegisterRequest]:
    return [
        RegisterRequest(
            email=f"user{i}@test.com",
            password="Test123!",
            username=f"testuser{i}"
        )
        for i in range(count)
    ]
```

### Evitar Hardcoding

```python
# ❌ Mal: Datos hardcodeados
def run(page):
    request = RegisterRequest(
        email="test@example.com",  # Siempre el mismo
        password="password123"     # Predicable
    )

# ✅ Bien: Datos dinámicos
import uuid

def run(page):
    unique_id = str(uuid.uuid4())[:8]
    request = RegisterRequest(
        email=f"test_{unique_id}@example.com",
        password=generate_secure_password()
    )
```

---

## 5. Autenticación

### Token Management

```python
# ✅ Centralizar manejo de tokens en Page Object
class AuthPage(BasePage):
    def __init__(self, base_url: str, **kwargs):
        super().__init__(base_url=base_url, **kwargs)
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
    
    def _get_headers(self, extra: Optional[Dict] = None) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        if extra:
            headers.update(extra)
        return headers
    
    def do_login(self, request: LoginRequest) -> APIResponse:
        response = self.post("/login", data=request.model_dump(by_alias=True))
        if response.ok:
            data = response.json()["data"]
            self.access_token = data["token"]
            self.refresh_token = data["refreshToken"]
        return response
```

### Refresh Token Pattern

```python
# ✅ Auto-refresh cuando expira
class ApiPage(BasePage):
    def _make_request(self, method: str, endpoint: str, **kwargs):
        response = getattr(self, method)(endpoint, **kwargs)
        
        # Si expiró, intentar refresh
        if response.status == 401 and self.refresh_token:
            self.do_refresh_token()
            # Reintentar request original
            response = getattr(self, method)(endpoint, **kwargs)
        
        return response
```

---

## 6. Aserciones

### Mensajes Descriptivos

```python
# ❌ Mal: Mensaje genérico
assert response.ok

# ✅ Bien: Mensaje descriptivo
assert response.ok, f"Request failed with {response.status}: {response.text()}"

# ✅ Mejor: Incluir contexto
data = response.json()
assert "id" in data, f"Expected 'id' in response. Got keys: {list(data.keys())}"
assert data["status"] == "active", f"Expected status='active', got '{data.get('status')}'"
```

### Aserciones Específicas

```python
# ❌ Mal: Aserciones vagas
assert response.status == 200 or response.status == 201

# ✅ Bien: Aserciones específicas
assert response.status == 201, f"Expected 201 Created, got {response.status}"

# ❌ Mal: Solo verificar que existe
assert data["email"]

# ✅ Bien: Verificar formato y contenido
import re
assert re.match(r"^[^@]+@[^@]+$", data["email"]), "Invalid email format"
assert data["email"].endswith("@example.com"), "Email domain mismatch"
```

### Soft Assertions (Cuando sea necesario)

```python
# ✅ Reportar múltiples errores a la vez
errors = []

if response.status != 200:
    errors.append(f"Status: expected 200, got {response.status}")

if "id" not in data:
    errors.append("Missing 'id' field")

if data.get("status") != "active":
    errors.append(f"Status: expected 'active', got '{data.get('status')}'")

if errors:
    raise AssertionError("Validation errors:\n" + "\n".join(f"  - {e}" for e in errors))
```

---

## 7. Manejo de Errores

### Retry Pattern

```python
# ✅ Retry con backoff exponencial
import time

def run_with_retry(page, max_retries=3):
    for attempt in range(max_retries):
        response = page.do_operation()
        
        if response.ok:
            return response
        
        if response.status >= 500:  # Server error, retry
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
        
        # Client error o max retries reached
        response.raise_for_status()
    
    raise Exception("Max retries exceeded")
```

### Graceful Degradation

```python
# ✅ Manejar fallos opcionales
def run(page):
    # Feature opcional
    response = page.do_optional_feature()
    
    if not response.ok:
        print(f"⚠️ Optional feature unavailable: {response.status}")
        # Continuar de todos modos
        return
    
    # Test principal
    assert response.json()["data"]["feature_enabled"]
```

### Cleanup siempre

```python
# ✅ Garantizar cleanup incluso si falla
import contextlib

def run(page):
    resource_id = None
    
    try:
        # Setup
        response = page.do_create()
        resource_id = response.json()["data"]["id"]
        
        # Test
        response = page.do_test(resource_id)
        assert response.ok
        
    finally:
        # Cleanup siempre ejecutado
        if resource_id:
            page.do_delete(resource_id)
```

---

## 8. Performance

### Timeouts

```python
# ✅ Configurar timeouts apropiados
# e2e.conf
settings:
  timeout: 30000  # 30 segundos default
  
# Para operaciones lentas específicas
def do_slow_operation(self):
    return self.post("/slow-endpoint", timeout=60000)
```

### Paralelización

```bash
# ✅ Ejecutar tests en paralelo
e2e run --parallel 4

# Asegurar que tests sean independientes
# Cada test debe crear sus propios recursos
```

### Setup/Teardown eficiente

```python
# ✅ Reusar recursos entre tests del mismo módulo
def run(page):
    # Cachear recursos costosos
    if not hasattr(page, '_shared_resource'):
        page._shared_resource = page.do_expensive_setup()
    
    # Usar recurso compartido
    response = page.do_test(page._shared_resource)
    assert response.ok
```

---

## 9. Mantenibilidad

### Documentación Inline

```python
"""Test: User registration flow.

Prerequisites:
    - Service must be running (health check passed)
    - Database must be accessible

Flow:
    1. Register new user with valid data
    2. Verify response contains user ID
    3. Verify user can login with credentials

Expected Results:
    - Status code: 201 Created
    - Response contains: id, email, username
    - User is persisted in database

Side Effects:
    - Creates user in database
    - May send welcome email (async)
"""

def run(page):
    # Implementation...
```

### Constantes Centralizadas

```python
# ✅ data_schema.py
# Todas las constantes en un lugar

ENDPOINTS = {
    "register": "/api/v1/auth/register",
    "login": "/api/v1/auth/login",
    "profile": "/api/v1/users/profile",
}

TEST_USER = {
    "email": "test@example.com",
    "password": "Test123!",
    "username": "testuser"
}

HTTP_STATUS = {
    "OK": 200,
    "CREATED": 201,
    "BAD_REQUEST": 400,
    "UNAUTHORIZED": 401,
    "NOT_FOUND": 404,
}
```

### DRY (Don't Repeat Yourself)

```python
# ❌ Mal: Código duplicado
def test_create(page):
    response = page.post("/users", data={...}, headers={...})
    assert response.ok

def test_update(page):
    response = page.put("/users/1", data={...}, headers={...})
    assert response.ok

# ✅ Bien: Reutilizar helpers
class UserPage(BasePage):
    def _api_call(self, method: str, endpoint: str, data: dict):
        return getattr(self, method)(
            endpoint,
            data=data,
            headers=self._get_headers()
        )
    
    def do_create(self, request):
        return self._api_call("post", ENDPOINTS["create"], request.model_dump(by_alias=True))
    
    def do_update(self, user_id, request):
        endpoint = ENDPOINTS["update"].format(id=user_id)
        return self._api_call("put", endpoint, request.model_dump(by_alias=True))
```

---

## 10. CI/CD

### Configuración Recomendada

```yaml
# .github/workflows/e2e.yml
name: E2E Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 0 * * *'  # Nightly

jobs:
  e2e:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:6
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install socialseed-e2e
          pip install -r requirements.txt
      
      - name: Start services
        run: |
          docker-compose up -d api
          sleep 30  # Esperar que servicios estén listos
      
      - name: Run health check
        run: e2e doctor
      
      - name: Run E2E tests
        run: e2e run --parallel 4 --html-report
        env:
          API_URL: http://localhost:8080
      
      - name: Upload artifacts
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: e2e-reports
          path: |
            e2e_reports/
            *.log
      
      - name: Notify on failure
        if: failure()
        uses: slack-action@v1
        with:
          message: "E2E tests failed!"
```

### Estrategia de Testing

```bash
# Pull requests: Tests críticos solamente
e2e run --filter "health|register|login"

# Merge a develop: Tests completos
e2e run --service all

# Nightly: Tests + Performance + Security
e2e run --service all
e2e perf-profile --duration 300
e2e security-test --type all
```

### Ambientes

```yaml
# e2e.conf con múltiples environments
environments:
  local:
    services:
      api:
        base_url: http://localhost:8080
  
  staging:
    services:
      api:
        base_url: https://staging-api.example.com
  
  production:
    services:
      api:
        base_url: https://api.example.com
```

```bash
# Ejecutar en ambiente específico
export E2E_ENV=staging
e2e run
```

---

## 🎯 Checklist de Calidad

### Antes de commitear:

- [ ] Tests pasan localmente
- [ ] `e2e lint` no reporta errores
- [ ] Nombres siguen convenciones
- [ ] Mensajes de error son descriptivos
- [ ] Documentación actualizada
- [ ] No hay datos hardcodeados sensibles
- [ ] Cleanup garantizado

### Code Review:

- [ ] Tests son independientes (o dependencias explícitas)
- [ ] Aserciones son específicas
- [ ] Manejo de errores apropiado
- [ ] No hay código duplicado
- [ ] Documentación clara

### CI/CD:

- [ ] Pipeline configura ambiente correctamente
- [ ] Tests ejecutan en paralelo
- [ ] Reportes se guardan como artifacts
- [ ] Notificaciones configuradas
- [ ] Rollback automático en fallo crítico

---

## 📚 Recursos Adicionales

- [Testing Pyramid](https://martinfowler.com/bliki/TestPyramid.html)
- [Playwright Best Practices](https://playwright.dev/python/docs/best-practices)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [CI/CD Patterns](https://www.atlassian.com/continuous-delivery/principles/continuous-integration-vs-delivery-vs-deployment)

---

**Versión:** 1.0  
**Framework:** socialseed-e2e v0.1.2  
**Última actualización:** 2026-02-17
