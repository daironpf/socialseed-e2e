# 🤖 Guía para Agentes de IA - Uso del Playground

Esta guía está diseñada específicamente para agentes de IA que necesitan entender y trabajar con el playground de SocialSeed E2E.

## 🎯 Propósito

El playground proporciona aplicaciones con bugs documentados para:
1. **Aprender** el framework SocialSeed E2E
2. **Practicar** escritura de tests
3. **Detectar** bugs comunes en APIs
4. **Generar** tests automáticamente

---

## 📋 Información Esencial

### Estructura del Playground

```
playground/
├── broken-apps/
│   ├── auth-service-broken/      # ✅ 20 bugs - Autenticación
│   ├── payment-service-broken/   # ✅ 31 bugs - Pagos/Concurrencia
│   └── ecommerce-broken/         # ✅ 35 bugs - E-commerce completo
├── tutorials/
│   └── 01-getting-started/       # Tutorial paso a paso
└── challenges/
    └── find-the-bug-01/          # Desafíos
```

### Apps Disponibles

| App | Bugs | Puerto | Tipo de Bugs | Dificultad |
|-----|------|--------|--------------|------------|
| auth-service | 20 | 5001 | Seguridad, JWT, Auth | ⭐⭐ Fácil |
| payment-service | 31 | 5002 | Concurrencia, Idempotencia | ⭐⭐⭐ Media |
| ecommerce | 35 | 5003 | Flujo E2E, Race conditions | ⭐⭐⭐⭐ Difícil |

### Documentación de Bugs

Cada app tiene un archivo `BUGS.md` con formato consistente:

```markdown
### BUG #N: Título
**Ubicación:** archivo.py:línea
**Problema:** Descripción
**Impacto:** Consecuencias
**Solución:** Cómo arreglar
```

---

## 🔍 Cómo Analizar una App Rota

### Paso 1: Leer BUGS.md

```python
# Cargar documentación de bugs
bugs_file = "playground/broken-apps/auth-service-broken/BUGS.md"
# Extraer lista de bugs numerados
# Identificar categorías: Seguridad, Funcional, Concurrencia
```

### Paso 2: Examinar el Código

```python
# Leer app.py
# Buscar comentarios con "BUG #N"
# Mapear cada bug a su ubicación en código
```

### Paso 3: Identificar Endpoints

```python
# Extraer todos los endpoints Flask
# @app.route("/path", methods=["METHOD"])
# Mapear métodos HTTP a funciones
```

---

## ✍️ Cómo Escribir Tests

### Patrón de Test Básico

```python
# services/<app>_page.py
from socialseed_e2e import BasePage

class AppServicePage(BasePage):
    """Page object for the service."""
    
    async def endpoint_method(self, param):
        response = await self.page.request.post(
            f"{self.base_url}/api/v1/endpoint",
            data={"param": param}
        )
        return response

# services/modules/test_bug_N.py
async def run(page):
    """Test: Descripción del bug que debería detectar."""
    # Arrange
    app_page = page
    
    # Act
    response = await app_page.endpoint_method("input")
    data = await response.json()
    
    # Assert
    assert "bug_indicator" not in data, "BUG: Descripción del bug"
```

### Ejemplo - Detectar Password Expuesto

```python
# Bug #17: API expone contraseña en respuesta
async def run(page):
    # Login
    response = await page.login("admin@example.com", "admin123")
    data = await response.json()
    token = data["access_token"]
    
    # Get profile
    profile_response = await page.get_profile(token)
    profile_data = await profile_response.json()
    
    # Assert: Password should NOT be in response
    assert "password" not in profile_data, \
        "BUG #17: Password exposed in profile response"
```

### Ejemplo - Race Condition

```python
# Bug #15: Race condition en checkout
async def run(page):
    # Crear dos carritos con el mismo item (stock limitado)
    # Ejecutar checkout simultáneamente
    # Verificar que solo uno tenga éxito
    
    import asyncio
    
    cart1 = await page.create_cart()
    cart2 = await page.create_cart()
    
    await page.add_to_cart(cart1, "low_stock_item", 1)
    await page.add_to_cart(cart2, "low_stock_item", 1)
    
    # Ejecutar simultáneamente
    results = await asyncio.gather(
        page.checkout(cart1),
        page.checkout(cart2),
        return_exceptions=True
    )
    
    # Solo uno debería tener éxito
    success_count = sum(1 for r in results if r.status == 201)
    assert success_count == 1, \
        f"BUG #15: Race condition - {success_count} checkouts succeeded"
```

---

## 🤖 Generación Automática de Tests

### Análisis del Manifest

```python
# Generar manifest del proyecto
from socialseed_e2e.project_manifest import ManifestGenerator

generator = ManifestGenerator("playground/broken-apps/auth-service-broken")
manifest = generator.generate()

# Extraer endpoints
endpoints = []
for service in manifest.services:
    for endpoint in service.endpoints:
        endpoints.append({
            "method": endpoint.method,
            "path": endpoint.path,
            "parameters": endpoint.parameters,
        })
```

### Generación de Tests Basada en Bugs

```python
def generate_test_for_bug(bug_info):
    """Generar código de test basado en descripción del bug."""
    
    template = f'''
async def run(page):
    """Test: {bug_info['title']}"""
    # Arrange
    
    # Act
    
    # Assert
    assert {bug_info['assertion']}, "BUG #{bug_info['number']}: {bug_info['title']}"
'''
    return template
```

---

## 📊 Tipos de Bugs y Cómo Detectarlos

### 1. Bugs de Seguridad

**Indicadores:**
- Campos sensibles en respuestas (password, token, ssn)
- Endpoints admin sin autenticación
- Autorización ausente

**Tests:**
```python
# Verificar que campos sensibles no estén expuestos
sensitive_fields = ["password", "token", "secret", "ssn"]
for field in sensitive_fields:
    assert field not in response_data, f"{field} should not be exposed"

# Verificar endpoints protegidos
response = await page.admin_endpoint()
assert response.status == 401, "Admin endpoint should require auth"
```

### 2. Bugs de Concurrencia

**Indicadores:**
- Verificación de condición antes de operación
- Uso de variables compartidas sin locks
- Operaciones de lectura-escritura separadas

**Tests:**
```python
# Ejecutar múltiples requests simultáneos
import asyncio

async def concurrent_requests(page, n=5):
    tasks = [page.operation() for _ in range(n)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Verificar consistencia
    success = sum(1 for r in results if r.status == 200)
    # Lógica específica según el bug
```

### 3. Bugs de Validación

**Indicadores:**
- Validaciones básicas (ej: solo verificar "@" en email)
- Inputs numéricos sin rangos
- Strings sin longitudes máximas

**Tests:**
```python
# Probar inputs inválidos
invalid_inputs = [
    ("", 400),  # Vacío
    ("a", 400),  # Muy corto
    ("a" * 10000, 400),  # Muy largo
    ("<script>", 400),  # XSS
    ("-1", 400),  # Negativo
]

for input_val, expected_status in invalid_inputs:
    response = await page.submit(input_val)
    assert response.status == expected_status
```

### 4. Bugs de Lógica de Negocio

**Indicadores:**
- Cálculos matemáticos (precios, descuentos)
- Cambios de estado (órdenes, pagos)
- Lógica condicional compleja

**Tests:**
```python
# Verificar cálculos
subtotal = Decimal("100.00")
discount = Decimal("10.00")
tax = Decimal("8.00")
expected_total = subtotal - discount + tax

response = await page.calculate_total(subtotal, discount, tax)
data = await response.json()
assert Decimal(data["total"]) == expected_total
```

---

## 🎓 Aprendizaje por Categorías

### Para Principiantes (Auth Service)

Enfocarse en:
- Bugs de validación (#7, #8)
- Bugs de exposición de datos (#14, #17)
- Bugs de autenticación (#5, #6)

### Para Intermedios (Payment Service)

Enfocarse en:
- Race conditions (#8, #9, #10, #15, #18)
- Idempotencia (#4, #12, #14)
- Cálculos financieros (#1, #2, #3, #6, #7)

### Para Avanzados (E-commerce)

Enfocarse en:
- Flujos E2E completos
- Gestión de estado (carrito, órdenes, inventario)
- Múltiples bugs en interacción

---

## 🛠️ Herramientas Útiles

### Extraer Endpoints de Flask

```python
import re

def extract_flask_endpoints(app_code):
    """Extraer endpoints de código Flask."""
    pattern = r'@app\.route\(["\'](.+?)["\'].*?methods=\[(.+?)\]'
    matches = re.findall(pattern, app_code, re.DOTALL)
    
    endpoints = []
    for path, methods in matches:
        endpoints.append({
            "path": path,
            "methods": [m.strip().strip('"\'') for m in methods.split(",")]
        })
    return endpoints
```

### Parsear BUGS.md

```python
import re

def parse_bugs_md(content):
    """Extraer información estructurada de BUGS.md."""
    pattern = r'### BUG #(\d+): (.+?)\n.*?\*\*Ubicación:\*\* (.+?)\n.*?\*\*Problema:\*\* (.+?)\n.*?\*\*Impacto:\*\* (.+?)\n.*?\*\*Solución:\*\* (.+?)(?=\n###|\Z)'
    
    bugs = []
    for match in re.finditer(pattern, content, re.DOTALL):
        bugs.append({
            "number": match.group(1),
            "title": match.group(2).strip(),
            "location": match.group(3).strip(),
            "problem": match.group(4).strip(),
            "impact": match.group(5).strip(),
            "solution": match.group(6).strip(),
        })
    return bugs
```

---

## 📝 Plantillas de Prompts

### Para Generar Tests

```
Dada la siguiente app con bugs documentados:

APP: [nombre]
ENDPOINTS: [lista]
BUGS: [lista de bugs]

Genera tests de SocialSeed E2E que detecten cada bug.
Cada test debe:
1. Tener un nombre descriptivo
2. Incluir Arrange/Act/Assert
3. Fallar si el bug está presente
4. Pasar si el bug está corregido
```

### Para Analizar Cobertura

```
Analiza los tests generados para la app [nombre]:

BUGS DOCUMENTADOS: [N]
TESTS GENERADOS: [M]

Indica:
1. Qué bugs tienen tests
2. Qué bugs faltan por testear
3. Sugerencias de tests adicionales
```

---

## 🎯 Casos de Uso para IA

### 1. Generación de Suite de Tests

**Input:** Archivo BUGS.md  
**Output:** Directorio con tests individuales para cada bug

### 2. Análisis de Cobertura

**Input:** Código fuente + Tests existentes  
**Output:** Reporte de qué bugs están cubiertos y cuáles no

### 3. Sugerencias de Corrección

**Input:** Bug específico con código  
**Output:** Código corregido con explicación

### 4. Generación de Documentación

**Input:** Lista de bugs  
**Output:** README.md con ejemplos de uso y curl commands

---

## 🔗 Recursos para IA

- [SocialSeed E2E Docs](../../docs/)
- [Testing Patterns](../../docs/testing-patterns.md)
- [API Reference](../../docs/api.md)
- [DEVELOPER_GUIDE.md](./DEVELOPER_GUIDE.md) - Guía para desarrolladores humanos

---

**Versión:** 1.0  
**Última actualización:** 2026-02-14  
**Mantenido por:** Agentes de IA y contribuidores humanos
