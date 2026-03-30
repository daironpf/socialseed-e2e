# 📘 Guía para Agentes de IA - SocialSeed E2E Framework

> **Versión 3.0 - Actualizado con Detección Automática de Puertos**

Esta guía te permite generar tests E2E funcionales sin errores de importación, serialización o configuración.

> 🚨 **REGLAS DE ORO - VERIFICAR ANTES DE GENERAR CUALQUIER TEST**
> 
> | # | Regla | Correcto ✅ | Incorrecto ❌ |
> |---|-------|-------------|---------------|
> | 1 | **Importes Absolutos** | `from services.auth.data_schema import LoginRequest` | `from ..data_schema import LoginRequest` |
> | 2 | **Serialización con Alias** | `request.model_dump(by_alias=True)` | `request.model_dump()` |
> | 3 | **Headers Manuales** | Implementar `_get_headers()` | Llamar `self.update_headers()` (¡NO EXISTE!) |
> | 4 | **Métodos con `do_`** | `def do_login(self):` | `def login(self):` (conflicto con atributo) |
> | 5 | **Estado vía Context** | `page.context.set("token", "abc")`<br/>`token = page.context.get("token")` | `self.token = "abc"` (no compartido entre tests) |

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
 
## ⚠️ ERRORES LETALES DE AGENTES IA (Y CÓMO EVITARLOS)
 
Estos son errores específicos que hacen fallar los tests generados por IA, incluso cuando el código *parece* correcto:
 
### Error #1: El Asumidor de Puertos
**Síntoma:** `ERROR: Failed to connect to localhost:8080`  
**Causa:** Asumir puerto 8080 sin verificar configuración real  
**Detección en código:** `base_url: http://localhost:8080` en e2e.conf  
**Prevención Obligatoria:**  
```bash
# ANTES de crear ANY test:
grep -r "port" services/<service-name>/src/main/resources/*.{yml,yaml,properties}
curl -s http://localhost:<PUERTO_DETECTADO>/actuator/health
# Si falla, probar: /health, /healthz, /api/health
```
 
### Error #2: El Olvidado del `by_alias=True`
**Síntoma:** `400 Bad Request: Refresh token is required`  
**Causa:** Pydantic serializa `refresh_token` en lugar de `refreshToken` (camelCase requerido por Java backend)  
**Detección en código:** Cualquier `request.model_dump()` sin `by_alias=True`  
**Prevención Obligatoria:**  
```bash
# Verificar TODOS los model_dump() en service_page.py:
grep -n "model_dump" services/<service>/*_page.py
# CORREGIR: asegurar que TODOS tengan `by_alias=True`
```
 
### Error #3: El Importador Relativo
**Síntoma:** `ImportError: attempted relative import beyond top-level package`  
**Causa:** Usar `from ..data_schema import X` en módulos de test  
**Detección en código:** `from ..` o `from .` en `services/*/modules/*.py`  
**Prevención Obligatoria:**  
```bash
# Verificar imports en modules:
grep -rn "from \." services/<service>/modules/
# CORREGIR: cambiar a imports absolutos:
# FROM: from ..data_schema import LoginRequest
# TO:   from services.<service>.data_schema import LoginRequest
```
 
### Error #4: El Asumidor de Estado
**Síntoma:** Tests pasan aislados pero fallan en suite completa  
**Causa:** Asumir que `self.access_token` persiste entre tests sin usar context  
**Detección en código:** `assert self.access_token is not None` sin establecerlo previamente en el mismo test  
**Prevención Obligatoria:**  
```python
# AL INICIAR CADA TEST QUE NECESITE ESTADO:
def run(page):
    # Verificar dependencia explícitamente
    if not page.context.has("auth_token"):
        raise ValueError("Ejecutar 01_login_flow primero - token no disponible")
    
    token = page.context.get("auth_token")
    # ... resto del test
```
 
### Error #5: El Confundidor de Nombre
**Síntoma:** `Method declaration "refresh_token" is obscured`  
**Causa:** Tener tanto `self.refresh_token = token` (atributo) como `def refresh_token(self):` (método)  
**Detección en código:** Búsqueda de atributo y método con mismo nombre en *_page.py*  
**Prevención Obligatoria:**  
```python
# SIEMPRE usar prefijo do_ para métodos:
# ❌ MAL:
self.refresh_token = token  # atributo
def refresh_token(self):    # método - CONFLICTO
    pass

# ✅ BIEN:
self.refresh_token = token  # atributo
def do_refresh_token(self): # método - SIN CONFLICTO
    pass
```

**Protocolo de Verificación Mejorado:** Antes de decir "terminado", ejecutar estas verificaciones específicas:

```bash
# 1. Verificar puertos detectados vs e2e.conf
echo "🔍 Verificando puertos configurados:"
e2e set show

# 2. Verificar serialización con by_alias=True
echo "🔍 Verificando serialización correcta:"
missing_by_alias=$(grep -L "by_alias=True" services/<service>/*_page.py 2>/dev/null || echo "Ninguno")
if [ -z "$missing_by_alias" ] || [ "$missing_by_alias" = "Ninguno" ]; then
    echo "✅ Todos los model_dump() usan by_alias=True"
else
    echo "❌ FALTA by_alias=True en:"
    echo "$missing_by_alias"
fi

# 3. Verificar imports relativos
echo "🔍 Verificando imports absolutos:"
relative_imports=$(grep -rn "from \." services/<service>/modules/ 2>/dev/null || echo "Ninguno")
if [ -z "$relative_imports" ] || [ "$relative_imports" = "Ninguno" ]; then
    echo "✅ Cero imports relativos encontrados"
else
    echo "❌ IMPORTS RELATIVOS ENCONTRADOS:"
    echo "$relative_imports"
fi

# 4. Verificar métodos sin do_ prefijo (excluyendo especiales)
echo "🔍 Verificando nombramiento de métodos:"
underscored_methods=$(grep -rn "def [a-z]" services/<service>/*_page.py 2>/dev/null | \
  grep -v "__init__\|_get_headers\|do_" | \
  xargs -I {} echo "MÉTODO SIN prefijo do_: {}" || echo "Ninguno")
if [ -z "$underscored_methods" ] || [ "$underscored_methods" = "Ninguno" ]; then
    echo "✅ Todos los métodos de acción usan prefijo do_"
else
    echo "❌ MÉTODOS SIN prefijo do_:"
    echo "$underscored_methods"
fi

# 5. Verificar que NO se usa update_headers() (no existe)
echo "🔍 Verificando manejo manual de headers:"
update_headers_usage=$(grep -rn "update_headers" services/<service>/*_page.py 2>/dev/null || echo "Ninguno")
if [ -z "$update_headers_usage" ] || [ "$update_headers_usage" = "Ninguno" ]; then
    echo "✅ No se usa update_headers() (correcto - se usa _get_headers() manual)"
else
    echo "❌ USO INCORRECTO DE update_headers():"
    echo "$update_headers_usage"
fi

# 6. Verificar uso correcto de context para estado compartido
echo "🔍 Verificando uso correcto de context:"
context_usage=$(grep -rn "self\.[a-zA-Z]" services/<service>/modules/ | grep -v "self\.context" | head -5 || echo "Ninguno uso directo encontrado")
if [ -z "$context_usage" ] || [ "$context_usage" = "Ninguno uso directo encontrado" ]; then
    echo "✅ Estado compartido manejado correctamente mediante page.context"
else
    echo "⚠️  POSIBLE USO INCORRECTO DE ATRIBUTOS PARA ESTADO COMPARTIDO:"
    echo "$context_usage"
    echo "   (Debería usar page.context.set()/get() en lugar de self.attr)"
fi

echo "🎉 Verificación completada. Corregir cualquier error marcado con ❌ antes de continuar."
```
 
---

## ✅ Checklist Final para Trabajo de Agentes IA

Antes de finalizar tu trabajo y decir "terminado", verifica OBLIGATORIAMENTE:

### 🔐 FUNDAMENTALES (Errores que hacen fallar los tests)
[ ] **Puertos verificados:** Confirmé que el puerto en e2e.conf coincide con lo detectado en código/configuración (no asumo 8080)  
[ ] **Serialización correcta:** TODOS los `model_dump()` en *_page.py* incluyen `by_alias=True` (verificar con: `grep -L "by_alias=True" services/<service>/*_page.py`)  
[ ] **Imports absolutos:** CERO imports relativos (`from ..` o `from .`) en modules/ o *_page.py* (verificar con: `grep -rn "from \." services/<service>/`)  
[ ] **Headers manuales:** Implementado `_get_headers()` en *_page.py* y NUNCA se llama a `update_headers()` (¡no existe!)  
[ ] **Métodos con do_:** Todos los métodos de acción usan prefijo `do_` (ej: `do_login`, no `login`)  

### 🔄 ESTADO Y DEPENDENCIAS
[ ] **Compartir estado:** Uso exclusivamentemente `page.context.set()/get()` para datos que deben pasar entre tests (nunca `self.xxx` para compartir)  
[ ] **Dependencias explícitas:** Cada test que requiere estado previo verifica explícitamente al inicio:  
    ```python
    if not page.context.has("token_requerido"):
        raise ValueError("Ejecutar 0X_*_flow primero - token no disponible")
    ```  
[ ] **Numeración secuente:** Archivos en modules/ siguen estrictamente `01_`, `02_`, `03_`, ..., `99_` (sin saltos ni duplicados)

### ✅ CALIDAD DE TESTS
[ ] **Assertions descriptivas:** TODAS las aserciones incluyen mensaje de error claro que explica QUÉ falló y POR QUÉ  
    ```python
    # ✅ BUENO:
    assert response.ok, f"Login failed: {response.status} - {response.text()[:100]}"
    
    # ❌ MALO:
    assert response.ok
    ```  
[ ] **Manejo de errores:** Tests que crean recursos tienen limpieza garantizada (try/finally o fixture)  
[ ] **Independencia cuando sea posible:** Tests que pueden ser independientes lo son (crean y limpian sus propios recursos)  
[ ] **Docstring completo:** Cada módulo tiene docstring con:  
    - Propósito claro del test  
    - Dependencias explícitas (qué tests deben correr antes)  
    - Estado que proporciona para tests posteriores (si aplica)

### 🚦 VALIDACIÓN FINAL
[ ] **Linter pasa:** `e2e lint services/<service>/` no reporta errores  
[ ] **Tests pasan aislados:** `e2e run --service <service> --verbose` pasa todos los tests  
[ ] **Tests pasan en suite:** `e2e run --service <service>` pasa todos los tests en secuencia  
[ ] **Reporte generado:** `e2e run --service <service> --html-report` crea reporte válido en e2e_reports/  
[ ] **Tiempo razonable:** Ningún test individual tarda >30s (salvo operaciones explícitamente lentas documentadas)

### 📚 DOCUMENTACIÓN
[ ] **He revisado:** AGENT_GUIDE.md, SERVICE_DETECTION.md, y BEST_PRACTICES.md para este trabajo  
[ ] **He aplicado:** Las 5 reglas de oro en cada línea de código escrita  
[ ] **He considerado:** Usar capacidades de IA del framework (manifest, search, generate-tests) cuando apropiado  

---

## 🎯 Flujo de Trabajo Recomendado (Caso Práctico: Servicio de Autenticación)

**Ejemplo real:** Crear tests para el servicio de autenticación en `demos/rest/auth-service` (Spring Boot)

### 🔍 PASO 0: DETECCIÓN OBLIGATORIA DE PUERTOS (NUNCA OMITIR)
```bash
# 1. Buscar puerto en configuración Spring Boot
$ grep "server.port" demos/rest/auth-service/src/main/resources/application.properties
server.port=8085

# 2. Verificar servicio activo con health endpoint estándar de Spring Actuator
$ curl -s http://localhost:8085/actuator/health
{"status":"UP"}

# 3. Si falla, probar variantes comunes:
for endpoint in "/actuator/health" "/health" "/healthz" "/api/health"; do
  curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8085$endpoint
done
```

### 📦 PASO 1: INICIALIZAR Y CONFIGURAR EL SERVICIO
```bash
# Desde raíz del proyecto:
e2e init auth-demo-project
cd auth-demo-project

# Configurar e2e.conf con puerto DETECTADO (no asumido):
# services:
#   auth-service:
#     base_url: http://localhost:8085          # ← PUERTO DETECTADO
#     health_endpoint: /actuator/health      # ← ESTANDAR SPRING BOOT
#     required: true

# settings:
#   timeout: 15000                             # ← Aumentado para servicios lentos
```

### 🏗️ PASO 2: CREAR ESTRUCTURA DEL SERVICIO (USANDO TEMPLATES)
```bash
e2e new-service auth-service
# Esto crea:
# services/auth-service/
#   ├── __init__.py
#   ├── data_schema.py
#   ├── auth_service_page.py
#   └── modules/
#       ├── __init__.py
#       └── 01_health_flow.py
```

### 📋 PASO 3: DEFINIR data_schema.py (Basado en Controladores Java)
```python
# services/auth-service/data_schema.py
"""Data schema for auth service API.
⚠️ IMPORTANTE: Todos los campos compuestos usan camelAlias para backend Java.
"""
from pydantic import BaseModel, Field
from typing import Optional

# ==================== DTOs DE REQUEST ====================
class LoginRequest(BaseModel):
    """Login request."""
    model_config = {"populate_by_name": True}
    email: str
    password: str

class RefreshTokenRequest(BaseModel):
    """Refresh token request - ⚠️ camelAlias OBLIGATORIO para Java."""
    model_config = {"populate_by_name": True}
    refresh_token: str = Field(
        ..., 
        alias="refreshToken",        # ← ENVÍA como refreshToken
        serialization_alias="refreshToken"  # ← SIEMPRE incluir ambos
    )

# ==================== DTOs DE RESPONSE ====================
class TokenResponse(BaseModel):
    """Token response."""
    model_config = {"populate_by_name": True}
    access_token: str = Field(..., alias="accessToken")
    refresh_token: str = Field(..., alias="refreshToken")
    expires_in: int

# ==================== ENDPOINTS (Basado en @RestController) ====================
ENDPOINTS = {
    "login": "/api/auth/login",           # POST
    "refresh": "/api/auth/refresh",       # POST
    "logout": "/api/auth/logout",         # POST
    "health": "/actuator/health"          # GET (Spring Boot Actuator)
}

# ==================== DATOS DE TEST ====================
TEST_USER = {
    "email": "test@example.com",
    "password": "SecurePass123!",
}
```

### 💻 PASO 4: IMPLEMENTAR service_page.py (Page Object Model)
```python
# services/auth-service/auth_service_page.py
"""Page Object for auth service."""
from typing import Optional, Dict, Any
from playwright.sync_api import APIResponse
from socialseed_e2e.core.base_page import BasePage

from .data_schema import (
    ENDPOINTS,
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse
)

class AuthServicePage(BasePage):
    """Page Object para el servicio de autenticación."""
    
    def __init__(self, base_url: str, **kwargs):
        super().__init__(base_url=base_url, **kwargs)
        # Estado que se comparte entre tests mediante context
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None

    def _get_headers(self, extra: Optional[Dict] = None) -> Dict[str, str]:
        """Obtener headers con autenticación Bearer token."""
        headers = {"Content-Type": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        if extra:
            headers.update(extra)
        return headers

    def do_login(self, request: LoginRequest) -> APIResponse:
        """Login y almacenar tokens."""
        response = self.post(
            ENDPOINTS["login"],
            data=request.model_dump(by_alias=True)  # ✅ SIEMPRE by_alias=True
        )
        
        if response.ok:
            data = response.json()["data"]
            # Guardar en atributos de instancia (para acceso rápido)
            self.access_token = data.get("access_token")
            self.refresh_token = data.get("refresh_token")
            # También guardar en context para compartir entre tests
            self.context.set("auth_token", self.access_token)
            self.context.set("refresh_token", self.refresh_token)
            
        return response

    def do_refresh_token(self) -> APIResponse:
        """Refresh access token usando refresh token."""
        if not self.refresh_token:
            raise ValueError("No refresh token available - login first")
            
        request = RefreshTokenRequest(refresh_token=self.refresh_token)
        response = self.post(
            ENDPOINTS["refresh"],
            data=request.model_dump(by_alias=True)  # ✅ SIEMPRE by_alias=True
        )
        
        if response.ok:
            data = response.json()["data"]
            self.access_token = data.get("access_token")
            self.refresh_token = data.get("refresh_token")
            self.context.set("auth_token", self.access_token)
            self.context.set("refresh_token", self.refresh_token)
            
        return response

    def do_logout(self) -> APIResponse:
        """Logout y limpiar tokens."""
        response = self.post(ENDPOINTS["logout"])
        if response.ok:
            # Limpiar estado
            self.access_token = None
            self.refresh_token = None
            self.context.set("auth_token", None)
            self.context.set("refresh_token", None)
        return response
```

### 🧪 PASO 5: CREAR MÓDULOS DE TEST (Con Flujo Lógico)
```python
# services/auth-service/modules/01_health_flow.py
"""Test 01: Verificar que el servicio está saludable."""
def run(page: "AuthServicePage"):
    """Verificar health endpoint del servicio."""
    print("🔍 STEP 01: Verifying Service Health")
    
    response = page.get(ENDPOINTS["health"])
    
    assert response.ok, f"Health check failed: {response.status}"
    data = response.json()
    assert data.get("status") == "UP", f"Service not healthy: {data}"
    
    print("✅ Service is healthy")

# services/auth-service/modules/02_login_flow.py
"""Test 02: Flujo de login (depende de 01_health_flow)."""
def run(page: "AuthServicePage"):
    """Ejecutar login y almacenar tokens."""
    print("🔑 STEP 02: Testing Login Flow")
    
    # Verificar dependencia explícitamente (buena práctica)
    if not page.context.has("auth_token"):
        print("⚠️  No token in context - realizando login")
    
    login_data = LoginRequest(
        email=TEST_USER["email"],
        password=TEST_USER["password"]
    )
    
    response = page.do_login(login_data)
    
    assert response.ok, f"Login failed: {response.status} - {response.text()}"
    assert page.access_token is not None, "Access token not stored"
    assert page.refresh_token is not None, "Refresh token not stored"
    
    # También guardar en context (forma recomendada para compartir)
    assert page.context.get("auth_token") == page.access_token
    
    print(f"✅ Login successful")
    print(f"🔑 Access token: {page.access_token[:15]}...")

# services/auth-service/modules/03_refresh_flow.py
"""Test 03: Flujo de refresh token (depende de 02_login_flow)."""
def run(page: "AuthServicePage"):
    """Ejecutar refresh de token."""
    print("🔄 STEP 03: Testing Refresh Token Flow")
    
    # Verificar que tenemos refresh token del test anterior
    assert page.context.has("refresh_token"), "Run 02_login_flow primero"
    
    response = page.do_refresh_token()
    
    assert response.ok, f"Refresh failed: {response.status} - {response.text()}"
    assert page.access_token is not None, "New access token not stored"
    
    print(f"✅ Token refreshed")
    print(f"🔑 New access token: {page.access_token[:15]}...")

# services/auth-service/modules/99_logout_flow.py
"""Test 99: Limpiar sesión (siempre último)."""
def run(page: "AuthServicePage"):
    """Ejecutar logout y limpiar estado."""
    print("🚪 STEP 99: Testing Logout Flow")
    
    response = page.do_logout()
    
    assert response.ok, f"Logout failed: {response.status}"
    assert page.access_token is None, "Access token not cleared"
    assert page.refresh_token is None, "Refresh token not cleared"
    
    print("✅ Logout successful - session cleaned")
```

### ✅ PASO 6: VERIFICAR Y EJECUTAR
```bash
# Validar estructura y reglas de oro
e2e lint services/auth-service/

# Ejecutar todos los tests en orden
e2e run --service auth-service --verbose

# Generar reporte de traceabilidad
e2e run --service auth-service --html-report
# Abrir: open e2e_reports/traceability_report.html
```

**Tiempo estimado:** 3-5 minutos siguiendo estos pasos exactamente.
**Resultado esperado:** Tests que pasan consistentemente en ejecución aislada y en suite.

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

## 🤖 Aprovechar las Capacidades de IA del Framework

socialseed-e2e incluye herramientas de IA que pueden acelerar tu trabajo como agente:

### 🔍 1. Generación Automática de Manifest (Para Comprender Servicios Rápidamente)
Antes de escribir tests manuales, genera un conocimiento estructurado del servicio:
```bash
# Generar manifest del servicio real (NO del demo)
# El manifest se guarda en: manifests/<nombre-servicio>/project_knowledge.json
e2e manifest ../services/mi-servicio

# Consultar endpoints específicos:
e2e manifest-query mi-servicio -f markdown
e2e manifest-query mi-servicio --endpoint "/api/users/*" --method POST

# Buscar DTOs por nombre o campo:
e2e manifest-query mi-servicio --type dto --query "User"
e2e manifest-query mi-servicio --type dto --field "email"

# Ver variables de entorno necesarias:
e2e manifest-query mi-servicio --type env
```

**Beneficio:** Obtienes inmediatamente la estructura exacta de endpoints, DTOs y requerimientos sin leer código fuente.

### 🧠 2. Búsqueda Semántica (Para Encontrar Patrones Similares)
Busca ejemplos de implementación similares en todo el código base:
```bash
# Buscar flujos de autenticación similares
e2e search "login flow with refresh token" -s mi-servicio

# Buscar manejo específico de errores
e2e search "401 unauthorized handling" -s mi-servicio

# Buscar patrones de paginación
e2e search "pagination page size limit" -s mi-servicio --type dto

# Buscar ejemplos de campos con validación específica
e2e search "email validation pattern" -s mi-servicio --type dto --field "email"
```

**Beneficio:** En lugar de inventar desde cero, adaptas patrones probados que ya funcionan en el framework.

### ⚡ 3. Generación Autónoma de Tests Supervisada
Para servicios bien definidos con buenos manifests:
```bash
# Generar tests base supervisados por IA
e2e generate-tests ../services/mi-servicio --service mi-servicio --max-tests 10

# EL AGENTE DEBE:
# 1. Revisar cada test generado en services/mi-servicio/modules/
# 2. Corregir cualquier error de lógica o adaptación necesaria
# 3. Asegurar que siguen las 5 reglas de oro
# 4. Eliminar tests redundantes o innecesarios
# 5. Añadir assertions de negocio específicas

# Luego ejecutar para validar:
e2e run --service mi-servicio
```

**Importante:** Nunca usar tests generados sin revisión. La IA ayuda con el boilerplate, pero tú debes asegurar la corrección lógica y de negocio.

### 📉 4. Análisis de Tests Flaky (Para Mejorar Calidad)
Si notas inestabilidad en tus tests:
```bash
# Analizar qué tests son flaky y por qué
e2e analyze-flaky --service mi-servicio --threshold 0.3 --verbose

# El output mostrará:
# - Tests con alta variabilidad en tiempo de ejecución
# - Tests que dependen de estado no limpiado correctamente
# - Tests sensibles a condiciones de carrera
# - Recomendaciones específicas de mejora
```

**Beneficio:** Mejora proactivamente la robustez de tus tests antes de que fallen en CI.

### 💡 Flujo de Trabajo IA-Potenciado Recomendado:
1. **Detectar puertos** (SERVICE_DETECTION.md)
2. **Generar manifest** (`e2e manifest ../servicio`)
3. **Consultar manifest** para entender API (`e2e manifest-query`)
4. **Crear estructura** con `e2e new-service`
5. **Usar búsqueda semántica** para encontrar patrones similares (`e2e search "flujo que necesito"`)
6. **Generar tests base** con IA (`e2e generate-tests --max-tests 5`)
7. **Revisar y corregir** cada test generado (aplicando las 5 reglas de oro)
8. **Añadir assertions de negocio específicas**
9. **Validar** con `e2e lint` y `e2e run`
10. **Analizar flakiness** si es suite crítica (`e2e analyze-flaky`)

### 🌟 Capacidades Avanzadas Disponibles

Más allá de las herramientas básicas de IA, el framework incluye capacidades especializadas que los agentes pueden aprovechar para tareas complejas:

#### 🤖 AI Orchestrator (Autonomous Test Execution)
```bash
# Ejecutar tests con capacidades de auto-curación y aprendizaje
e2e autonomous-run --service mi-servicio --strategy adaptive

# Analizar patrones de inestabilidad (flakiness)
e2e analyze-flaky --service mi-servicio --threshold 0.2 --auto-heal

# Generar estrategia de testing impulsada por IA
e2e plan-strategy --service mi-servicio --business-goals "validar flujos críticos de usuario"
```

#### 🛡️ Red Team & Security Testing
```bash
# Ejecutar pruebas de seguridad impulsadas por IA
e2e red-team --service mi-servicio --owasp-top10 --duration 300

# Fuzzing semántico avanzado
e2e security-test --service mi-servicio --strategy intelligent --mutations 50
```

#### 📊 Semantic Analysis & Logic Drift Detection
```bash
# Detectar desviaciones lógicas en el comportamiento del API
e2e semantic-analyze run --service mi-servicio --baseline v1.0 --target v1.1

# Analizar intenciones de negocio desde documentación
e2e semantic-analyze intents --service mi-servicio --sources docs/ requirements/
```

#### 🔄 Self-Healing & Adaptive Testing
```bash
# Ver estadísticas de auto-curación
e2e healing-stats --service mi-servicio

# Ejecutar con capacidades de auto-reparación activas
e2e run --service mi-servicio --self-healing --max-retries 3
```

**Beneficio:** Estas capacidades permiten a los agentes ir más allá de la generación básica de tests y crear estrategias de testing sofisticadas, autónomas y resilientes.

---

## 📝 Contribuyendo al Mejoramiento de la Interacción Agente-Framework

Como agente de IA, tu experiencia interactuando con este framework es invaluable para mejorar tanto el framework como la guía para futuros agentes. Se te anima a documentar:

1. **Huecos en la documentación** - Información que faltaba y tuviste que descubrir por cuenta propia
2. **Sugerencias de mejora** - Ideas para hacer el framework más fácil de usar para agentes IA
3. **Patrones de comportamiento** - Cómo tu enfoque evoluciona al trabajar repetidamente con el framework
4. **Lecciones aprendidas** - Qué funcionó bien y qué no en tu proceso de resolución

### Formato Recomendado para Contribuciones

Cuando identifiques algo que podría mejorarse, documenta un "Agent Experience Report" siguiendo este formato:

```bash
# Crear reporte de experiencia del agente
echo "
## Agent Experience Report: [Breve descripción del tema]
**Date:** $(date +%Y-%m-%d)
**Agent:** [Tu identificador de agente, ej: OpenCode Build Agent]
**Type:** [gap|suggestion|behavior|lesson]
**Area:** [ej: documentation, testing workflow, IA capabilities]

### 1. Observación
[Describe what you observed or experienced]

### 2. Impacto
[How this affected your work - time spent, confusion, etc.]

### 3. Sugerencia de Mejora
[Specific, actionable recommendation]

### 4. Beneficio Esperado
[How this would improve future agent interactions]

### 5. Estado
[Proposed|Implemented|Rejected|Duplicate]
" >> .agent/agent_experiences/$(date +%Y/%m/%d)_$(date +%H-%M-%S)_[topic].md
```

### Directorio de Almacenamiento
Los reportes de experiencia se almacenan en:
```
.agent/agent_experiences/
├── 2026/
│   └── 03/
│       ├── 30_14-22-15_gap_documentation_serialization.md
│       └── 30_15-05-30_suggestion_test_naming.md
└── ...
```

### Ejemplo Práctico

Imagina que descubriste que la detección de puertos falla para ciertos tipos de servicios:

```bash
echo "
## Agent Experience Report: Puerto detection falla en servicios Node.js con .env.local
**Date:** 2026-03-30
**Agent:** OpenCode Build Agent
**Type:** gap
**Area:** service detection

### 1. Observación
El servicio detection en SERVICE_DETECTION.md solo busca archivos .env estándar, pero mi proyecto usaba .env.local que no estaba siendo detectado, causando fallos de conexión.

### 2. Impacto
Perdí 15 minutos depurando por qué e2e set show mostraba el puerto incorrecto antes de descubrir que necesitaba buscar en .env.local también.

### 3. Sugerencia de Mejora
Actualizar SERVICE_DETECTION.md para incluir búsqueda en .env*.local files y agregar este caso común al flujo de detección.

### 4. Beneficio Esperado
Reducir tiempo de depuración para agentes que trabajen con proyectos Node.js que usan archivos de entorno locales.

### 5. Estado
Proposed
" >> .agent/agent_experiences/$(date +%Y/%m/%d)_$(date +%H-%M-%S)_gap_nodejs_env_local.md
```

### Integración con el Proceso de Mejora Continua

Estos reportes de experiencia se revisan periódicamente para:
1. Actualizar AGENT_GUIDE.md y otros documentos .agent/
2. Mejorar las plantillas y scripts del framework
3. Identificar patrones comunes en el trabajo de agentes IA
4. Desarrollar nuevas capacidades basadas en necesidades reales observadas

**Nota:** Al igual que con los issue logs, estos reportes contribuyen al conocimiento colectivo que mejora la experiencia de todos los agentes que trabajan con este framework.

---

## 🔗 Integración con Otras Guías .agent/

Para maximizar tu efectividad como agente IA, aprende a combinar esta guía con otras documentos especializados en el directorio `.agent/`:

### 📚 Flujo de Trabajo Recomendado con Múltiples Guías:

1. **Inicio Rápido** → Lee `QUICKSTART.md` para entender el flujo básico
2. **Detección de Servicios** → Consulta `SERVICE_DETECTION.md` antes de crear ANY test
3. **Pruebas Especializadas** → Usa guías específicas según el tipo de API:
   - `REST_TESTING.md` para APIs REST
   - `GRPC_TESTING.md` para servicios gRPC  
   - WebSocket testing en desarrollo
4. **Mejores Prácticas** → Consulta `BEST_PRACTICES.md` para escribir tests robustos
5. **Resolución de Problemas** → Usa `TROUBLESHOOTING.md` cuando encuentres errores comunes
6. **Metodología Formal** → Aplica `CHIEF_ARCHITECT_INTEGRATION.md` para resolver issues complejos
7. **Capacidades de IA** → Esta guía (AGENT_GUIDE.md) para aprovechar herramientas de IA del framework

### 💡 Ejemplo de Flujo Integrado:

```bash
# 1. Detectar servicio (SERVICE_DETECTION.md)
grep -r "port" services/payment-service/src/main/resources/*.yml
curl http://localhost:8081/actuator/health

# 2. Entender arquitectura (QUICKSTART.md + ARCHITECTURE_MAP.md)
e2e init payment-demo
cd payment-demo

# 3. Crear estructura (esta guía)
e2e new-service payment-service

# 4. Implementar con mejores prácticas (BEST_PRACTICES.md)
#    - Usar imports absolutos
#    - Serialización con by_alias=True
#    - Manejo manual de headers
#    - Prefijo do_ para métodos

# 5. Generar conocimiento con IA (esta guía)
e2e manifest ../services/payment-service
e2e manifest-query payment-service --endpoint "/api/payments/*"

# 6. Generar tests base con IA (esta guía)
e2e generate-tests ../services/payment-service --service payment-service --max-tests 5

# 7. Revisar y corregir (esta guía)
#    - Aplicar las 5 reglas de oro
#    - Añadir assertions de negocio específicas

# 8. Validar (esta guía)
e2e lint services/payment-service/
e2e run --service payment-service --verbose
```

**Resultado:** Un flujo de trabajo que combina detección obligatoria, mejores prácticas de codificación, y aprovechamiento inteligente de las capacidades de IA del framework para producir tests E2E robustos y mantenibles en minutos, no horas.

## 🚫 Detección de Anti-Patrones para Agentes IA

Aprende a reconocer y evitar estos anti-patrones comunes que disminuyen la calidad y mantenibilidad de los tests:

### Anti-Patrón #1: El "Test de Todo"
**Síntoma:** Un solo módulo de test que verifica login, creación, actualización, eliminación y logout
**Problema:** Tests no independientes, difícil de mantener, fallos en cascada
**Solución:** Separar en módulos específicos: 01_login, 02_create, 03_update, 04_delete, 05_logout

### Anti-Patrón #2: El "Hardcodeador de Credenciales"
**Síntoma:** Usuario y contraseña hardcodeados en múltiples tests
**Problema:** Riesgo de seguridad, tests frágiles cuando cambian credenciales
**Solución:** Usar variables de entorno o fixtures de test:
```python
# ❌ MALO:
login_data = LoginRequest(email="admin@test.com", password="admin123")

# ✅ BUENO:
login_data = LoginRequest(
    email=os.getenv("TEST_USER_EMAIL", "admin@test.com"),
    password=os.getenv("TEST_USER_PASSWORD", "admin123")
)
```

### Anti-Patrón #3: El "Ignorador de Estados de Error"
**Síntoma:** Tests solo verifican caminos felices (200 OK) y ignoran manejo de errores
**Problema:** Falsa sensación de seguridad, falta de cobertura de resiliencia
**Solución:** Añadir tests específicos para casos de error:
```python
def run(page):
    # Test caso de error 400 - datos inválidos
    invalid_request = LoginRequest(email="invalid-email", password="123")
    response = page.do_login(invalid_request)
    assert response.status == 400, f"Expected 400, got {response.status}"
    assert "invalid email" in response.text().lower()
```

### Anti-Patrón #4: El "Duplicador de Lógica"
**Síntoma:** Misma lógica de setup/teardown repetida en múltiples tests
**Problema:** Mantenimiento difícil, inconsistencia cuando se necesita cambiar
**Solución:** Extraer a métodos helper en el page object o usar fixtures:
```python
# En page object:
def setup_test_user(self, email, password):
    # Lógica reutilizable de creación de usuario
    
# En tests:
def run(page):
    page.setup_test_user("test@example.com", "SecurePass123!")
    # ... resto del test
```

### Anti-Patrón #5: El "Asumidor de Estado Limpio"
**Síntoma:** Tests asumen que empiezan con estado limpio sin verificar o limpiar explícitamente
**Problema:** Tests dependientes del orden de ejecución, flaky en ejecución paralela
**Solución:** Siempre limpiar estado al inicio y/o verificar dependencias explícitamente:
```python
def run(page):
    # Limpiar estado previo si es necesario
    page.context.set("auth_token", None)
    page.context.set("user_id", None)
    
    # O verificar dependencia explícitamente
    if not page.context.has("user_id"):
        raise ValueError("Ejecutar 02_create_user_first antes de este test")
```

**Detectar estos anti-patrones:** Antes de decir "terminado", revisar tu código buscando estos patrones y corregirlos.

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
