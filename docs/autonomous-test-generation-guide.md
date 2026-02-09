# 🚀 Guía de Generación Autónoma de Tests (Issue #185)

> **¿Cansado de escribir tests manualmente?** Déjalo en nuestras manos. Este sistema analiza tu código y genera tests completos automáticamente.

## 📋 Tabla de Contenidos

1. [¿Qué es la Generación Autónoma?](#qué-es-la-generación-autónoma)
2. [¿Para Quién es Esto?](#para-quién-es-esto)
3. [Instalación Rápida](#instalación-rápida)
4. [Guía Paso a Paso](#guía-paso-a-paso)
5. [Ejemplos Prácticos](#ejemplos-prácticos)
6. [Personalización](#personalización)
7. [Solución de Problemas](#solución-de-problemas)
8. [API para Desarrolladores](#api-para-desarrolladores)

---

## ¿Qué es la Generación Autónoma?

La **Generación Autónoma de Tests** es un sistema que:

1. **Analiza tu código fuente** (Java, Python, TypeScript)
2. **Detecta endpoints** y sus relaciones
3. **Parsea modelos de base de datos** (SQLAlchemy, Prisma, Hibernate)
4. **Genera datos de prueba** válidos automáticamente
5. **Crea tests completos** que siguen tus flujos de negocio

### Flujos Detectados Automáticamente

```
Autenticación:  POST /register → POST /login → GET /profile
CRUD:          POST /users → GET /users/{id} → PUT /users/{id} → DELETE /users/{id}
Checkout:      POST /cart → POST /checkout → POST /payment
```

---

## ¿Para Quién es Esto?

### ✅ Úsalo Si:
- Tienes una API con muchos endpoints
- Quieres tests rápidamente
- Tu API sigue patrones REST estándar
- Necesitas cubrir casos edge y validaciones

### ❌ No lo Uses Si:
- Necesitas lógica de negocio muy específica
- Tu API no sigue convenciones REST
- Prefieres control total manual

---

## Instalación Rápida

```bash
# Instalar socialseed-e2e
pip install socialseed-e2e

# Verificar instalación
e2e doctor
```

---

## Guía Paso a Paso

### Paso 1: Navegar al Proyecto

```bash
cd /path/to/your/api-project
```

### Paso 2: Inicializar (Si es Necesario)

```bash
# Si no tienes un proyecto E2E
e2e init
```

### Paso 3: Analizar el Código

```bash
# Esto escanea tu código y crea un manifest
e2e manifest
```

**Salida esperada:**
```
📚 Generating AI Project Manifest
   Project: /path/to/project

   Services detected: 2
   - users-service (java, spring-boot)
   - payment-service (python, fastapi)

   Endpoints: 24
   DTOs: 15

✅ Manifest generated successfully!
```

### Paso 4: Generar Tests (Preview)

```bash
# Primero, ver qué se generará (recomendado)
e2e generate-tests --dry-run
```

**Salida esperada:**
```
🧪 Autonomous Test Suite Generation
   Project: /path/to/project
   Output: services

Step 1/5: Parsing database models...
   ✓ Found 8 entities
   - User (6 columns)
   - Order (5 columns)
   ...

Step 2/5: Loading project manifest...
   ✓ Loaded manifest with 2 services

Step 3/5: Analyzing business logic...
   Analyzing: users-service...
     ✓ Detected 3 flows, 12 relationships
   Analyzing: payment-service...
     ✓ Detected 2 flows, 8 relationships

Step 4/5: Generating test code...
   [DRY RUN - No files created]

   users-service:
     📄 data_schema.py (8 DTOs)
     📄 users-service_page.py (12 endpoints)
     📄 User Authentication Flow (3 steps)
     📄 User CRUD Operations (4 steps)

Summary:
   Services: 2
   Files to generate: 8
   Validation rules: 45

[DRY RUN - Run without --dry-run to create files]
```

### Paso 5: Generar Tests (Real)

```bash
# Generar para todos los servicios
e2e generate-tests

# O solo para uno específico
e2e generate-tests --service users-service
```

**Salida esperada:**
```
✅ Generated test suite for 'users-service'
   Location: services/users-service
   Flows detected: 3
   - User Authentication Flow (3 steps)
   - User CRUD Operations (4 steps)
   - Admin Operations (2 steps)
```

### Paso 6: Revisar lo Generado

```bash
# Ver la estructura generada
ls -la services/users-service/
```

**Estructura creada:**
```
services/users-service/
├── __init__.py
├── data_schema.py          ← DTOs y datos de prueba
├── users-service_page.py   ← Page object con flujos
└── modules/
    ├── __init__.py
    ├── _01_user_authentication_flow.py
    ├── _02_user_crud_operations.py
    ├── _03_admin_operations.py
    └── _99_validation_tests.py
```

### Paso 7: Personalizar Datos de Prueba

Edita `services/users-service/data_schema.py`:

```python
# ANTES (generado automáticamente)
TEST_DATA = {
    "user_authentication_flow": {
        "register_user": {
            "email": "testuser_123@example.com",
            "password": "TestPassword123!",
            "username": "testuser_123"
        }
    }
}

# DESPUÉS (personalizado)
TEST_DATA = {
    "user_authentication_flow": {
        "register_user": {
            "email": "mi-usuario@empresa.com",  # ← Cambia esto
            "password": "MiPasswordSeguro123!",   # ← Cambia esto
            "username": "mi_usuario_e2e"          # ← Cambia esto
        }
    }
}
```

### Paso 8: Ejecutar Tests

```bash
# Ejecutar todos los tests
e2e run

# O solo un servicio
e2e run --service users-service

# O un flujo específico
e2e run --service users-service --module _01_user_authentication_flow
```

**Salida esperada:**
```
🚀 socialseed-e2e v0.1.0
═══════════════════════════════════════

📦 Service: users-service
───────────────────────────────────────
🧪 Running 4 test module(s)

[1/4] _01_user_authentication_flow.py

============================================================
Running Flow: User Authentication Flow
============================================================

✅ PASSED (1.23s)

[2/4] _02_user_crud_operations.py
============================================================
Running Flow: User CRUD Operations
============================================================

✅ PASSED (0.89s)

───────────────────────────────────────
✅ All tests passed! (4/4)
⏱️  Total Duration: 4.56s
```

---

## Ejemplos Prácticos

### Ejemplo 1: API de E-commerce

Supón que tienes estos endpoints:

```java
@RestController
public class OrderController {

    @PostMapping("/cart/items")
    public Cart addToCart(@RequestBody AddItemRequest request) { ... }

    @PostMapping("/checkout")
    public CheckoutResponse checkout(@RequestBody CheckoutRequest request) { ... }

    @PostMapping("/payment")
    public PaymentResponse processPayment(@RequestBody PaymentRequest request) { ... }
}
```

**Comandos:**
```bash
cd /mi-proyecto-ecommerce
e2e init
e2e manifest
e2e generate-tests --service order-service
e2e run
```

**Tests Generados:**
```python
# services/order-service/modules/_01_checkout_flow.py

def run(page: OrderServicePage) -> APIResponse:
    """Execute Complete Checkout Flow.

    Steps:
    1. Add item to cart
    2. Checkout cart
    3. Process payment
    """
    # Step 1: Add item
    item_data = TEST_DATA["checkout_flow"]["add_to_cart"]
    response = page.do_add_to_cart(AddItemRequest(**item_data))
    assert response.ok, "Add to cart failed"

    # Step 2: Checkout
    checkout_data = TEST_DATA["checkout_flow"]["checkout"]
    response = page.do_checkout(CheckoutRequest(**checkout_data))
    assert response.ok, "Checkout failed"
    order_id = response.json()["order_id"]

    # Step 3: Payment
    payment_data = TEST_DATA["checkout_flow"]["process_payment"]
    payment_data["order_id"] = order_id  # Usar ID del paso anterior
    response = page.do_process_payment(PaymentRequest(**payment_data))
    assert response.ok, "Payment failed"

    return response
```

### Ejemplo 2: API con Validaciones Complejas

```python
# Tu modelo SQLAlchemy
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False, unique=True)
    email = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)

# Tu DTO Pydantic
class UserRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    age: int = Field(..., ge=18, le=120)
```

**Tests de Validación Generados:**
```python
# services/user-service/modules/_99_validation_tests.py

def test_username_below_minimum(page: UserServicePage):
    """Test username with less than 3 characters should fail."""
    data = {
        "username": "ab",  # 2 chars, min is 3
        "email": "test@example.com",
        "age": 25
    }
    request = UserRequest(**data)
    response = page.do_create_user(request)
    assert response.status == 400

def test_username_at_boundary(page: UserServicePage):
    """Test username with exactly 3 characters should succeed."""
    data = {
        "username": "abc",  # Exactly 3 chars
        "email": "test@example.com",
        "age": 25
    }
    request = UserRequest(**data)
    response = page.do_create_user(request)
    assert response.ok

def test_age_below_minimum(page: UserServicePage):
    """Test age below 18 should fail."""
    data = {
        "username": "testuser",
        "email": "test@example.com",
        "age": 17  # Below minimum
    }
    request = UserRequest(**data)
    response = page.do_create_user(request)
    assert response.status == 400

def test_chaos_test(page: UserServicePage):
    """Test with random/chaos data."""
    data = {
        "username": "!@#$%^&*()",  # Special chars
        "email": "not-an-email",    # Invalid format
        "age": -999                 # Invalid value
    }
    request = UserRequest(**data)
    response = page.do_create_user(request)
    # Should fail validation
    assert not response.ok
```

---

## Personalización

### Estrategias de Datos

```bash
# Solo datos válidos
e2e generate-tests --strategy valid

# Solo datos inválidos (para probar validaciones)
e2e generate-tests --strategy invalid

# Solo casos límite
e2e generate-tests --strategy edge

# Solo tests de caos (fuzzy testing)
e2e generate-tests --strategy chaos

# Todas las estrategias (default)
e2e generate-tests --strategy all
```

### Servicio Específico

```bash
e2e generate-tests --service users-api
e2e generate-tests --service payment-api --strategy edge
```

### Directorio de Salida

```bash
e2e generate-tests --output ./mi-tests-personalizados
```

---

## Solución de Problemas

### "No flows detected"

**Problema:** El sistema no detecta flujos.

**Causa:** Nombres de endpoints no son descriptivos.

**Solución:** Renombra tus endpoints:
```java
// ❌ Mal
@PostMapping("/action1")
@PostMapping("/process")

// ✅ Bien
@PostMapping("/register")
@PostMapping("/login")
```

### "No database models found"

**Problema:** No detecta modelos de DB.

**Solución:** Verifica ubicaciones:
```
SQLAlchemy: models.py, db.py, database.py
Prisma:     prisma/schema.prisma o schema.prisma
Hibernate:  src/main/java/**/entity/*.java
```

### Tests fallan después de generar

**Problema:** Los tests generados no funcionan.

**Solución:**
1. Revisa `data_schema.py` y personaliza los datos
2. Verifica que tu API esté corriendo
3. Comprueba las URLs en `e2e.conf`

```bash
# Verificar configuración
e2e config

# Probar un solo test
e2e run --service users-api --module _01_auth_flow
```

---

## API para Desarrolladores

### Uso Programático

```python
from socialseed_e2e.project_manifest import (
    BusinessLogicInferenceEngine,
    DummyDataGenerator,
    FlowBasedTestSuiteGenerator,
    DatabaseSchema,
    db_parser_registry,
)

# 1. Parsear modelos de base de datos
db_schema = db_parser_registry.parse_project("/path/to/project")

# 2. Cargar información del servicio
from socialseed_e2e.project_manifest import ManifestAPI
api = ManifestAPI("/path/to/project")
manifest = api._load_manifest()
service = manifest.get_service("users-api")

# 3. Generar suite de tests
generator = FlowBasedTestSuiteGenerator(
    service_info=service,
    db_schema=db_schema
)
suite = generator.generate_test_suite()

# 4. Escribir a archivos
generator.write_to_files("./services")
```

### Generar Datos Manualmente

```python
from socialseed_e2e.project_manifest import DummyDataGenerator, DataGenerationStrategy

# Crear generador
generator = DummyDataGenerator()

# Generar para un DTO específico
from myapp.schemas import UserRequest
dto = UserRequest  # Tu DTO Pydantic

# Datos válidos
valid_data = generator.generate_for_dto(dto, DataGenerationStrategy.VALID)

# Datos inválidos (para testear validaciones)
invalid_data = generator.generate_for_dto(dto, DataGenerationStrategy.INVALID)

# Casos límite
edge_data = generator.generate_for_dto(dto, DataGenerationStrategy.EDGE_CASE)
```

---

## Resumen de Comandos

```bash
# Análisis
e2e manifest                    # Analizar proyecto
e2e manifest --force            # Forzar re-análisis

# Generación
e2e generate-tests              # Generar todos los tests
e2e generate-tests --dry-run    # Preview
e2e generate-tests --service X  # Solo un servicio
e2e generate-tests --strategy X # Estrategia específica

# Ejecución
e2e run                         # Ejecutar todos
e2e run --service X             # Solo un servicio
e2e run --module X              # Solo un módulo

# Utilidades
e2e doctor                      # Verificar instalación
e2e config                      # Mostrar configuración
```

---

## 🎉 ¡Listo!

Ahora puedes generar tests automáticamente para cualquier API.

**Próximos pasos:**
1. Intenta con tu propia API
2. Personaliza los datos en `data_schema.py`
3. Añade tests manuales para casos específicos

**¿Necesitas ayuda?**
- Revisa `docs/autonomous-test-generation.md` para detalles técnicos
- Consulta `docs/AGENT_GUIDE.md` para guía de agentes IA
- Ejecuta `e2e doctor` para verificar tu instalación
