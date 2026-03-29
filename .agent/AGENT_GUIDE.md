# 📘 Guía para Agentes de IA - SocialSeed E2E Framework

> **Versión 3.0 - Actualizado con Detección Automática de Puertos**

Esta guía te permite generar tests E2E funcionales sin errores de importación, serialización o configuración.

---

## 🎯 ¿Necesitas resolver un issue?

Si tienes un **problema específico a resolver** (bug, error, test que falla), usa:

```
Read ./.agent/CHIEF_ARCHITECT_INTEGRATION.md and solve:
[TU ISSUE]
```

Esto aplicará la metodología Chief Architect (SPAR-CoT) para resolver el issue con documentación automática.

---

## 🚨 PASO 0: DETECCIÓN DE PUERTOS (OBLIGATORIO)

**ANTES DE GENERAR CUALQUIER TEST**, debes detectar dónde está corriendo el servicio.

**Lee primero:** `SERVICE_DETECTION.md`

### Detección Rápida

```bash
# 1. Buscar puerto en configuración
grep -r "port" services/<service-name>/src/main/resources/*.yml

# 2. Verificar servicio activo
curl http://localhost:<puerto>/actuator/health

# 3. Ver contenedores Docker
docker ps --format "table {{.Names}}\t{{.Ports}}"
```

**⚠️ NUNCA asumas el puerto por defecto (8080). Siempre detecta primero.**

---

## 🚨 REGLAS DE ORO (Lee esto primero)

### 1. **Imports SIEMPRE Absolutos**
```python
# ❌ NUNCA uses imports relativos
from ..data_schema import RegisterRequest  # PROHIBIDO

# ✅ SIEMPRE uses imports absolutos
from services.auth_service.data_schema import RegisterRequest
from services.auth_service.auth_page import AuthServicePage
```

### 2. **Serialización con Aliases**
```python
# ❌ NUNCA sin by_alias=True (envía refresh_token en lugar de refreshToken)
data = request.model_dump()

# ✅ SIEMPRE con by_alias=True (envía refreshToken como espera Java)
data = request.model_dump(by_alias=True)
```

### 3. **Modelos Pydantic con Config**
```python
class RefreshTokenRequest(BaseModel):
    # SIEMPRE incluye esto
    model_config = {"populate_by_name": True}

    # Campos compuestos SIEMPRE con alias camelCase
    refresh_token: str = Field(
        ...,
        alias="refreshToken",
        serialization_alias="refreshToken"
    )
```

### 4. **Manejo Manual de Headers**
```python
# ❌ NO existe update_headers()
self.update_headers({"Authorization": f"Bearer {token}"})

# ✅ Implementa _get_headers() manualmente
def _get_headers(self, extra=None):
    headers = {"Content-Type": "application/json"}
    if self.access_token:
        headers["Authorization"] = f"Bearer {self.access_token}"
    return headers
```

### 5. **Nombres de Métodos sin Conflicto**
```python
# ❌ Conflicto: atributo refresh_token vs método refresh_token()
self.refresh_token = token  # Atributo

# ✅ Usa prefijo do_ para métodos
self.refresh_token = token  # Atributo
self.do_refresh_token()      # Método
```

---

## 📦 Dependencias Requeridas

El archivo `requirements.txt` debe incluir:

```
pydantic>=2.0.0
email-validator>=2.0.0  # REQUERIDO para EmailStr
dnspython>=2.0.0          # Para validación de email
```

**Si falta email-validator:**
```
ImportError: email-validator is not installed
```

**Solución:**
```bash
pip install -r requirements.txt
```

---

## 🎯 Templates Actualizados

### data_schema.py - Estructura Base

```python
"""Data schema for <service> API.

⚠️ IMPORTANTE: Todos los campos compuestos usan camelCase aliases.
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional


class LoginRequest(BaseModel):
    """Login request."""
    model_config = {"populate_by_name": True}

    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""
    model_config = {"populate_by_name": True}

    # ⚠️ camelCase alias requerido para backend Java
    refresh_token: str = Field(
        ...,
        alias="refreshToken",
        serialization_alias="refreshToken"
    )
```

### service_page.py - Estructura Base

```python
"""Page object for <service> API."""
from typing import Optional, Dict, Any
from playwright.sync_api import APIResponse
from socialseed_e2e.core.base_page import BasePage

from .data_schema import (
    ENDPOINTS,
    LoginRequest,
    RefreshTokenRequest,
)


class AuthPage(BasePage):
    """Page for auth service."""

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
        """Login and store tokens."""
        response = self.post(
            ENDPOINTS["login"],
            data=request.model_dump(by_alias=True)  # ✅ SIEMPRE by_alias=True
        )
        if response.ok:
            data = response.json()["data"]
            self.access_token = data.get("token")
            self.refresh_token = data.get("refreshToken")
        return response

    def do_refresh_token(self) -> APIResponse:
        """Refresh access token."""
        if not self.refresh_token:
            raise ValueError("No refresh token")

        request = RefreshTokenRequest(refresh_token=self.refresh_token)
        response = self.post(
            ENDPOINTS["refresh"],
            data=request.model_dump(by_alias=True)  # ✅ SIEMPRE by_alias=True
        )
        if response.ok:
            data = response.json()["data"]
            self.access_token = data.get("token")
            self.refresh_token = data.get("refreshToken")
        return response
```

### modules/01_login_flow.py - Estructura Base

```python
"""Test module 01: Login flow."""
from services.auth_service.data_schema import LoginRequest, TEST_USER

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from services.auth_service.auth_page import AuthPage


def run(page: "AuthPage"):
    """Execute login test."""
    print("STEP 01: Testing Login")

    login_data = LoginRequest(
        email=TEST_USER["email"],
        password=TEST_USER["password"]
    )

    response = page.do_login(login_data)

    assert response.ok, f"Login failed: {response.status}"
    assert page.access_token is not None, "Token not stored"

    print(f"✓ Login successful")
    print(f"✓ Token: {page.access_token[:20]}...")
```

---

## 🔧 Solución de Problemas

### Problema 1: `ImportError: email-validator is not installed`

**Causa:** Falta la dependencia email-validator.

**Solución:**
1. Asegúrate de que `requirements.txt` incluya `email-validator>=2.0.0`
2. Ejecuta: `pip install -r requirements.txt`

### Problema 2: `cannot import name '_01_register_flow'`

**Causa:** Los módulos con nombres numéricos no pueden importarse normalmente.

**Solución - Tres métodos:**

**Método A: importlib (recomendado para scripts)**
```python
import importlib.util
import importlib.machinery

def load_module(name, path):
    loader = importlib.machinery.SourceFileLoader(name, path)
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module

register_module = load_module(
    "register_flow",
    "/path/to/services/auth/modules/01_register_flow.py"
)
register_module.run(page)
```

**Método B: Import directo**
```python
from services.auth.modules._01_register_flow import run
run(page)
```

**Método C: Import función**
```python
from services.auth.modules import _01_register_flow
_01_register_flow.run(page)
```

### Problema 3: `Refresh token is required` (400 error)

**Causa:** Pydantic serializa `refresh_token` en lugar de `refreshToken`.

**Solución:**
1. En el modelo, usa alias camelCase:
```python
refresh_token: str = Field(
    ...,
    alias="refreshToken",
    serialization_alias="refreshToken"
)
```

2. Al serializar, usa by_alias=True:
```python
data = request.model_dump(by_alias=True)
```

### Problema 4: `Method declaration "logout" is obscured`

**Causa:** Conflicto entre atributo y método con mismo nombre.

**Solución:**
```python
# Atributo
self.refresh_token: Optional[str] = None

# Método con prefijo do_
def do_refresh_token(self):
    pass

def do_logout(self):
    pass
```

### Problema 5: `update_headers not found`

**Causa:** El método `update_headers()` no existe en `BasePage`.

**Solución:** Implementa manejo manual:
```python
def _get_headers(self, extra=None):
    headers = {"Content-Type": "application/json"}
    if self.access_token:
        headers["Authorization"] = f"Bearer {self.access_token}"
    if extra:
        headers.update(extra)
    return headers
```

---

## ✅ Checklist Pre-Entrega

Antes de decir "terminado", verifica:

- [ ] `email-validator` está en requirements.txt
- [ ] Todos los modelos tienen `model_config = {"populate_by_name": True}`
- [ ] Campos compuestos tienen `alias` y `serialization_alias` en camelCase
- [ ] En todos los métodos de page: `request.model_dump(by_alias=True)`
- [ ] NINGÚN import relativo (`from ..x`)
- [ ] Todos los imports son absolutos (`from services.xxx`)
- [ ] Métodos conflictivos usan prefijo `do_` (do_refresh_token, do_logout)
- [ ] Headers manejados manualmente (no update_headers)
- [ ] Funciones `run(page)` bien definidas en módulos
- [ ] Type hints usando `TYPE_CHECKING` para evitar imports circulares

---

## 🎯 Flujo de Trabajo Recomendado

### Para Agentes de IA:

1. **Lee los controladores Java** del servicio target
2. **Identifica endpoints**: rutas, métodos HTTP, body params
3. **Crea data_schema.py**:
   - Modelos Pydantic con aliases camelCase
   - Constantes de endpoints
   - Datos de test
4. **Crea service_page.py**:
   - Hereda de BasePage
   - Implementa _get_headers()
   - Métodos para cada endpoint
   - Usa by_alias=True siempre
5. **Crea modules/**:
   - 01_*_flow.py: Crear/Login
   - 02_*_flow.py: Operaciones CRUD
   - 99_*_flow.py: Cleanup/Logout
6. **Verifica** ejecutando: `python verify_installation.py`

---

## 📚 Recursos Adicionales

- **Ejemplo Completo:** Ver `.agent/EXAMPLE_TEST.md`
- **Flujo de Generación:** Ver `.agent/WORKFLOW_GENERATION.md`
- **Documentación Framework:** https://daironpf.github.io/socialseed-e2e/
- **Pydantic v2:** https://docs.pydantic.dev/latest/

---

## 🎓 Tips para Éxito

1. **Siempre verifica serialización:**
   ```python
   print(request.model_dump(by_alias=True))
   # Debe mostrar camelCase: {'refreshToken': 'xxx'}
   # NO snake_case: {'refresh_token': 'xxx'}
   ```

2. **Test incremental:**
   - Ejecuta test 01 primero
   - Verifica que el estado se guarda en `page`
   - Luego ejecuta test 02

3. **Manejo de errores:**
   ```python
   assert response.ok, f"Failed: {response.status} - {response.text()[:100]}"
   ```

4. **Compartir estado:**
   - Guarda en `page` (ej: `page.user_id = data["id"]`)
   - Recupera en siguiente test

5. **Ejecución Flexible:**
   Si ejecutas desde el root del proyecto y el config está en una subcarpeta:
   ```bash
   e2e run -c otrotest/e2e.conf
   ```
   El framework encontrará los servicios automáticamente.

---

## 🚀 Resultado Esperado

Siguiendo esta guía, los agentes de IA pueden generar:

- ✅ Tests funcionales sin errores de importación
- ✅ Serialización correcta camelCase ↔ snake_case
- ✅ Manejo de autenticación entre tests
- ✅ Tests secuenciales con estado compartido

**Tiempo estimado:** 2-5 minutos por servicio
**Intervención humana:** Mínima o ninguna

---

## 🚀 Integración CI/CD

Como agente, puedes ayudar a configurar el pipeline de integración continua del proyecto:

```bash
# Sugiere al usuario o ejecuta:
e2e setup-ci <platform>
```

**Plataformas soportadas:** `github`, `gitlab`, `jenkins`, `azure`, `circleci`, `travis`, `bitbucket`.

**Beneficios:**
- Ejecución paralela configurable.
- Reportes HTML automáticos as artifacts.
- Caching de browsers y dependencias.
- Matriz de ejecución para microservicios.

---

**Versión:** 2.1
**Última actualización:** 2026-02-03
**Framework:** socialseed-e2e v0.1.0+
