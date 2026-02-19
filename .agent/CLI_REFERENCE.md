# CLI Reference - socialseed-e2e

**Meta:** Referencia completa de TODOS los comandos CLI con ejemplos, opciones y casos de uso.

---

## 📖 Índice de Comandos

### Core
- [`e2e --version`](#version)
- [`e2e --help`](#help)
- [`e2e doctor`](#doctor)
- [`e2e config`](#config)

### Inicialización
- [`e2e init`](#init)
- [`e2e new-service`](#new-service)
- [`e2e new-test`](#new-test)

### Ejecución
- [`e2e run`](#run)
- [`e2e autonomous-run`](#autonomous-run)
- [`e2e observe`](#observe)

### Análisis
- [`e2e deep-scan`](#deep-scan)
- [`e2e lint`](#lint)
- [`e2e analyze-flaky`](#analyze-flaky)
- [`e2e discover`](#discover)
- [`e2e plan-strategy`](#plan-strategy)

### Documentación y AI
- [`e2e manifest`](#manifest)
- [`e2e manifest-check`](#manifest-check)
- [`e2e manifest-query`](#manifest-query)
- [`e2e search`](#search)
- [`e2e retrieve`](#retrieve)

### Generación
- [`e2e generate-tests`](#generate-tests)
- [`e2e translate`](#translate)
- [`e2e gherkin-translate`](#gherkin-translate)

### Mocking
- [`e2e mock-analyze`](#mock-analyze)
- [`e2e mock-generate`](#mock-generate)
- [`e2e mock-run`](#mock-run)
- [`e2e mock-validate`](#mock-validate)

### Seguridad
- [`e2e security-test`](#security-test)
- [`e2e red-team`](#red-team)

### Performance
- [`e2e perf-profile`](#perf-profile)
- [`e2e perf-report`](#perf-report)
- [`e2e telemetry`](#telemetry)

### UI
- [`e2e tui`](#tui)
- [`e2e dashboard`](#dashboard)

### CI/CD
- [`e2e setup-ci`](#setup-ci)

### Utilidades
- [`e2e install-extras`](#install-extras)
- [`e2e import`](#import)
- [`e2e set`](#set)
- [`e2e watch`](#watch)
- [`e2e debug-execution`](#debug-execution)
- [`e2e regression`](#regression)
- [`e2e semantic-analyze`](#semantic-analyze)
- [`e2e healing-stats`](#healing-stats)
- [`e2e recorder`](#recorder)
- [`e2e shadow`](#shadow)
- [`e2e build-index`](#build-index)
- [`e2e ai-learning`](#ai-learning)
- [`e2e community`](#community)

---

## Core Commands

### `--version`
Muestra la versión del framework.

```bash
e2e --version
```

**Output:**
```
socialseed-e2e, version 0.1.3
```

---

### `--help`
Muestra ayuda general o de un comando específico.

```bash
e2e --help                           # Ayuda general
e2e run --help                       # Ayuda del comando run
e2e generate-tests --help            # Ayuda de generación
```

---

### `doctor`
Verifica instalación, dependencias y conectividad.

```bash
e2e doctor
```

**Verifica:**
- Python version
- Playwright installation
- Pydantic version
- Configuration file
- Directory structure
- Service connectivity

**Output:**
```
🏥 socialseed-e2e Doctor

System Verification
✓ Python 3.12.3
✓ Playwright 1.58.0
✓ Pydantic 2.12.5
✓ Configuration
✓ services/ directory

Service Connectivity Check
✓ my-service: http://localhost:8080 - OK
```

**Casos de uso:**
- Verificar instalación después de `pip install`
- Diagnosticar problemas de conectividad
- Validar configuración del proyecto

---

### `config`
Muestra y valida configuración actual.

```bash
e2e config
```

**Muestra:**
- Archivo de configuración activo
- Environment (dev/prod)
- Timeouts
- Servicios configurados
- Estado de health de servicios

**Output:**
```
⚙️  E2E Configuration

Configuration: e2e.conf
Environment: dev
Timeout: 30000ms

Configured Services:
- users-api: http://localhost:8080
- payments: http://localhost:8081
```

---

## Inicialización

### `init`
Inicializa un nuevo proyecto E2E completo.

```bash
e2e init nombre-proyecto
e2e init nombre-proyecto --template advanced
e2e init .                           # En directorio actual
```

**Opciones:**
- `--template`: basic (default), advanced, minimal

**Genera:**
```
nombre-proyecto/
├── e2e.conf
├── services/
├── tests/
├── .agent/
├── requirements.txt
└── README.md
```

**Incluye:**
- Verificación de instalación automática
- Servicio de ejemplo funcional
- Tests de verificación
- Documentación para IA

**Post-init:**
```bash
cd nombre-proyecto
e2e new-service mi-api
# Editar e2e.conf con URLs reales
```

---

### `new-service`
Crea estructura para un nuevo servicio.

```bash
e2e new-service users-api
e2e new-service payments --template crud
```

**Opciones:**
- `--template`: default, crud, auth, empty

**Genera:**
```
services/users-api/
├── __init__.py
├── config.py
├── data_schema.py          # DTOs y endpoints
├── users_api_page.py       # Page Object
└── modules/
    ├── __init__.py
    └── 01_health_flow.py   # Test inicial
```

**Ejemplo de uso:**
```bash
# 1. Crear servicio
e2e new-service inventory

# 2. Editar data_schema.py (definir DTOs)
# 3. Editar inventory_page.py (implementar métodos)
# 4. Crear tests
e2e new-test list-products --service inventory

# 5. Ejecutar
e2e run --service inventory
```

---

### `new-test`
Crea un nuevo módulo de test.

```bash
e2e new-test nombre-test --service users-api
e2e new-test create-user --service users-api
```

**Opciones:**
- `--service` (requerido): Nombre del servicio

**Genera:**
```
services/users-api/modules/
└── XX_nombre_test_flow.py    # XX = número secuencial
```

**⚠️ IMPORTANTE:**
- El nombre se sanitiza automáticamente
- Se asigna número secuencial automáticamente
- Debes implementar la función `run(page)`

**Ejemplo generado:**
```python
# services/users-api/modules/02_create_user_flow.py
def run(page):
    """Test: create_user."""
    print("Testing: create_user")
    # Implement your test logic here
    pass
```

---

## Ejecución

### `run`
Ejecuta tests E2E.

```bash
e2e run                                    # Todos los servicios
e2e run --service users-api                # Solo un servicio
e2e run --service users-api --verbose      # Modo verbose
e2e run --html-report                      # Generar reporte HTML
e2e run --parallel 4                       # Ejecución paralela
e2e run --filter "register|login"          # Filtrar tests
e2e run --dry-run                          # Simular ejecución
```

**Opciones:**
- `--service, -s`: Ejecutar solo este servicio
- `--verbose, -v`: Output detallado
- `--html-report`: Generar reporte HTML
- `--parallel, -p`: Número de workers paralelos
- `--filter, -f`: Regex para filtrar tests
- `--dry-run`: Mostrar qué se ejecutaría sin ejecutar
- `--fail-fast`: Detener en primer error
- `--timeout`: Timeout por test (ms)

**Output:**
```
🚀 socialseed-e2e v0.1.2

Running tests for service: users-api
Base URL: http://localhost:8080
Test modules: 3

01_health_flow.py         ✓ PASSED
02_register_flow.py       ✓ PASSED
03_login_flow.py          ✓ PASSED

═══════════════════════════════════════════════════
Test Execution Summary
═══════════════════════════════════════════════════

users-api: 3/3 passed (100.0%)

✓ All tests passed
```

**Reportes generados:**
- `e2e_reports/traceability_report.html`
- `e2e_reports/traceability_report.md`
- `e2e_reports/traceability_report.json`

---

### `autonomous-run`
Ejecuta tests autónomos con orquestación AI.

```bash
e2e autonomous-run
e2e autonomous-run --mode self-healing
e2e autonomous-run --strategy exploration
```

**Opciones:**
- `--mode`: standard, self-healing, exploratory
- `--strategy`: conservative, balanced, aggressive
- `--max-iterations`: Límite de iteraciones

**Características:**
- Auto-detección de cambios en APIs
- Self-healing de tests rotos
- Exploración automática de endpoints

**⚠️ Requiere:**
- Manifest generado (`e2e manifest`)
- Configuración AI habilitada

---

### `observe`
Detecta automáticamente servicios en ejecución.

```bash
e2e observe
e2e observe --port-range 8000-9000
e2e observe --docker
```

**Opciones:**
- `--port-range`: Rango de puertos a escanear
- `--docker`: Incluir contenedores Docker
- `--update-config`: Actualizar e2e.conf automáticamente

**Detecta:**
- Servicios en localhost
- Contenedores Docker
- Puertos abiertos
- Health endpoints

**Output:**
```
🔭 The Observer - Service Detection

📡 Scanning for services...
✓ Found 2 running services:
  - http://localhost:8080 (users-api)
  - http://localhost:8081 (payments)

🐳 Docker containers:
  - postgres:5432
  - redis:6379
```

**Uso típico:**
```bash
# 1. Iniciar tus servicios
# 2. Detectar automáticamente
e2e observe --update-config
# 3. Ejecutar tests
e2e run
```

---

## Análisis

### `deep-scan`
Escanea proyecto para detectar tech stack automáticamente.

```bash
e2e deep-scan
e2e deep-scan --output scan-results.json
```

**Detecta:**
- Framework (Flask, FastAPI, Django, Express, etc.)
- Lenguaje (Python, Node.js, Java, etc.)
- Puertos sugeridos
- Estructura de proyecto

**Output:**
```
🔍 Deep scanning: /project

📋 Scan Summary:
--------------------------------------------------
🛠️  Detected Frameworks:
   • flask (python) - 95% confidence

📦 Services Found: 2
   • users-service (port 5000)
   • api-gateway (port 8080)

🌐 Recommended Base URL: http://localhost:5000
```

**Casos de uso:**
- Zero-config setup
- Migración de proyectos existentes
- Auditoría de tech stack

---

### `lint`
Valida archivos de test.

```bash
e2e lint
e2e lint --fix                    # Auto-corregir issues
e2e lint --service users-api      # Solo un servicio
```

**Verifica:**
- Sintaxis Python válida
- Estructura de módulos correcta
- Imports válidos
- Presencia de función `run()`
- Convenciones de nomenclatura

**Output:**
```
🔍 Validating Test Files

Checking: users-api
  ✓ No issues found

✓ All tests passed validation!
```

**Issues detectados:**
- ❌ Syntax errors
- ❌ Missing `run()` function
- ❌ Invalid imports
- ⚠️ Relative imports (warning)
- ⚠️ Missing docstrings (warning)

---

### `analyze-flaky`
Analiza tests inestables (flaky).

```bash
e2e analyze-flaky
e2e analyze-flaky --runs 10       # 10 ejecuciones
e2e analyze-flaky --threshold 20  # Umbral de 20% variabilidad
```

**Opciones:**
- `--runs`: Número de ejecuciones (default: 5)
- `--threshold`: % de variabilidad para considerar flaky

**Output:**
```
🔍 Flaky Test Analysis

Running each test 5 times...

Test: 03_payment_flow.py
  ✗ Inconsistent (40% failure rate)
  🔍 Possible causes:
    - Race condition in payment processing
    - External service dependency
    - Insufficient wait time

Recommendations:
  1. Add explicit wait after payment creation
  2. Mock external payment gateway in tests
```

---

### `discover`
Genera AI Discovery Report del proyecto.

```bash
e2e discover
e2e discover --output report.md
```

**Genera reporte con:**
- Endpoints detectados
- Relaciones entre servicios
- Contratos de API
- Sugerencias de tests

**Output:**
```
📊 AI Discovery Report

Endpoints Discovered: 15
├── GET /api/v1/users
├── POST /api/v1/users
├── GET /api/v1/users/{id}
└── ...

Suggested Test Coverage:
✓ CRUD operations (4/4)
⚠ Validation tests (2/5)
✗ Error handling (0/3)
```

---

### `plan-strategy`
Genera estrategia de testing AI-driven.

```bash
e2e plan-strategy --name "users-api-strategy"
e2e plan-strategy --name "full-coverage" --coverage 100
```

**Opciones:**
- `--name` (requerido): Nombre de la estrategia
- `--coverage`: Cobertura objetivo (%)
- `--risk-level`: low, medium, high
- `--time-budget`: Horas disponibles

**Output:**
```
🎯 AI Test Strategy: users-api-strategy

Priority Matrix:
  P0 (Critical): 5 tests
    - Authentication flows
    - Payment processing
  
  P1 (High): 8 tests
    - CRUD operations
    - Input validation
  
  P2 (Medium): 12 tests
    - Edge cases
    - Error scenarios

Estimated time: 4.5 hours
Risk coverage: 95%
```

---

## Documentación y AI

### `manifest`
Genera AI Project Manifest (manifiesto del proyecto) para un microservicio.

El manifest se guarda en: `<framework_root>/manifests/<service_name>/project_knowledge.json`

```bash
e2e manifest ../services/auth-service    # Generar manifest para auth-service
e2e manifest ../services/user-service     # Generar manifest para user-service
e2e manifest ../services/auth-service --force  # Forzar re-escaneo completo
```

**Argumentos:**
- `directory`: Ruta al directorio del microservicio (e.g., `../services/auth-service`)

**Genera:** `<framework_root>/manifests/<service_name>/project_knowledge.json`

**Contiene:**
- Hash de archivos fuente
- Endpoints documentados
- DTOs y schemas
- Dependencias entre servicios
- Variables de entorno

**Uso:**
- Token optimization para AI
- Detección de cambios
- Contexto para LLMs
- Mantiene el código del microservicio limpio

---

### `manifest-check`
Valida freshness del manifest vs código fuente.

```bash
e2e manifest-check auth-service    # Verificar freshness de auth-service
e2e manifest-check user-service    # Verificar freshness de user-service
```

**Argumentos:**
- `directory`: Nombre del servicio (e.g., `auth-service`)

**Output:**
```
🔍 Checking Manifest Freshness
   Service: auth-service
   Manifest: .../manifests/auth-service/project_knowledge.json

✅ Manifest is FRESH
   All source files match stored hashes.
   Version: 2.0
   Last updated: 2026-02-18 02:01:50
   Total files tracked: 15
```

---

### `manifest-query`
Consulta el manifest usando el nombre del servicio.

```bash
e2e manifest-query auth-service           # Consulta manifest de auth-service
e2e manifest-query auth-service -f markdown  # Formato markdown
```

**Argumentos:**
- `directory`: Nombre del servicio (e.g., `auth-service`)

**Opciones:**
- `--format, -f`: Formato de salida (`json` o `markdown`)

**Uso:**
- Buscar información específica del servicio
- Debugging
- Auditoría

---

### `search`
Búsqueda semántica en el manifest de un servicio específico.

```bash
e2e search "authentication flow" -s auth-service
e2e search "payment validation" -s payment-service
e2e search "user DTO" -s user-service --type dto
```

**Argumentos:**
- `query`: Query de búsqueda

**Opciones:**
- `--service, -s`: Nombre del servicio (requerido)
- `--top-k, -k`: Número de resultados (default: 5)
- `--type, -t`: Filtrar por tipo (`endpoint`, `dto`, `service`)

**Requiere:**
```bash
e2e install-extras rag
e2e build-index auth-service
```

**Características:**
- Búsqueda semántica (no solo keyword)
- Results ordenados por relevancia
- Busca en el manifest del servicio específico

---

### `retrieve`
Recupera contexto para una tarea específica desde el manifest de un servicio.

```bash
e2e retrieve "implement user registration" -s auth-service
e2e retrieve "fix payment bug" -s payment-service --max-chunks 3
```

**Argumentos:**
- `task`: Descripción de la tarea

**Opciones:**
- `--service, -s`: Nombre del servicio (requerido)
- `--max-chunks, -c`: Máximo de chunks (default: 5)

**Uso:**
- Obtener contexto relevante para una tarea
- Optimizar prompts para LLMs
- Debugging dirigido

---

## Generación

### `generate-tests`
Genera tests automáticamente basado en el código.

```bash
e2e generate-tests                          # Todos los servicios
e2e generate-tests --service users-api      # Solo un servicio
e2e generate-tests --dry-run                # Preview
e2e generate-tests --strategy chaos         # Estrategia chaos
```

**Opciones:**
- `--service, -s`: Servicio específico
- `--strategy`: valid, invalid, edge, chaos, all
- `--dry-run`: Preview sin crear archivos
- `--output, -o`: Directorio de salida
- `--verbose, -v`: Verbose

**Estrategias:**
- `valid`: Solo datos válidos (happy path)
- `invalid`: Datos inválidos (error handling)
- `edge`: Casos límite
- `chaos`: Datos aleatorios/fuzzing
- `all`: Todas las estrategias

**Requiere:**
```bash
e2e manifest    # Generar manifest primero
```

**Output:**
```
🤖 Generating Tests

Analyzing users-api...
✓ Detected 5 endpoints
✓ Found 8 DTOs

Generating:
  ✓ 01_register_flow.py
  ✓ 02_login_flow.py
  ✓ 03_profile_flow.py
  ✓ 04_validation_tests.py

✅ 4 test files generated
```

---

### `translate`
Traduce lenguaje natural a código de test.

```bash
e2e translate "test user can register and login"
e2e translate --input requirements.txt --output tests/
```

**Ejemplo:**
```bash
e2e translate "verify that a user can add items to cart and checkout"
```

**Genera:**
```python
# services/shop/modules/XX_cart_checkout_flow.py
def run(page):
    """Test: Cart checkout flow."""
    # Add items to cart
    response = page.do_add_to_cart(item_id="123")
    assert response.ok
    
    # Checkout
    response = page.do_checkout()
    assert response.ok
```

---

### `gherkin-translate`
Convierte archivos Gherkin (.feature) a código.

```bash
e2e gherkin-translate features/user.feature
e2e gherkin-translate features/ --output services/users/modules/
```

**Input (Gherkin):**
```gherkin
Feature: User Registration
  Scenario: Successful registration
    Given I am on the registration page
    When I fill in valid credentials
    Then I should be registered successfully
```

**Output:**
```python
# modules/XX_user_registration_flow.py
def run(page):
    """Feature: User Registration - Scenario: Successful registration"""
    # Given I am on the registration page
    page.navigate_to("/register")
    
    # When I fill in valid credentials
    page.fill_credentials(valid=True)
    
    # Then I should be registered successfully
    assert page.is_registered()
```

---

## Mocking

### `mock-analyze`
Analiza proyecto para detectar dependencias externas.

```bash
e2e mock-analyze
e2e mock-analyze --service payments
```

**Detecta:**
- Llamadas a APIs externas
- Servicios de terceros
- Bases de datos externas
- Colas de mensajes

**Output:**
```
🔍 External Dependency Analysis

Service: payments
External APIs detected:
  ✓ Stripe API (payments)
  ✓ SendGrid API (emails)
  ⚠ AWS S3 (file storage)

Recommendations:
  - Mock Stripe for testing
  - Mock SendGrid for testing
  - Use local S3-compatible (MinIO) for tests
```

---

### `mock-generate`
Genera mock servers para APIs externas.

```bash
e2e mock-generate
e2e mock-generate --service payments --api stripe
e2e mock-generate --contract stripe-openapi.yaml
```

**Opciones:**
- `--service`: Servicio a analizar
- `--api`: API específica a mockear
- `--contract`: Archivo de contrato (OpenAPI)

**Genera:**
```
mocks/
├── stripe/
│   ├── server.py
│   ├── routes/
│   └── data/
└── sendgrid/
    └── ...
```

---

### `mock-run`
Ejecuta los mock servers.

```bash
e2e mock-run
e2e mock-run --services stripe,sendgrid
e2e mock-run --port 3000
```

**Opciones:**
- `--services`: Lista de servicios a mockear
- `--port`: Puerto base (default: 3000)
- `--background`: Ejecutar en background

---

### `mock-validate`
Valida contrato contra mock.

```bash
e2e mock-validate --contract api.yaml
e2e mock-validate --service payments
```

**Verifica:**
- Endpoints implementados
- Schemas coinciden
- Status codes correctos

---

## Seguridad

### `security-test`
Ejecuta tests de seguridad fuzzing.

```bash
e2e security-test
e2e security-test --service users-api
e2e security-test --type sqli,xss,auth
```

**Tipos:**
- `sqli`: SQL Injection
- `xss`: Cross-Site Scripting
- `auth`: Authentication bypass
- `idor`: Insecure Direct Object Reference
- `all`: Todos

**Output:**
```
🔒 Security Testing

Running security tests on users-api...

SQL Injection:
  ✓ No vulnerabilities found

XSS:
  ⚠️ Potential XSS in comment field
  CWE-79: Improper Neutralization of Input
  
Authentication:
  ✓ Rate limiting working
  ✓ JWT validation secure
```

---

### `red-team`
Comandos para Red Team testing (adversarial AI).

```bash
e2e red-team --attack prompt-injection
e2e red-team --attack jailbreak --target users-api
e2e red-team --full-suite
```

**Ataques:**
- `prompt-injection`: Inyección de prompts
- `jailbreak`: Intentos de bypass
- `data-extraction`: Extracción de datos
- `model-inversion`: Inversión de modelo
- `full-suite`: Todos los ataques

**⚠️ Solo para entornos de testing controlados**

---

## Performance

### `perf-profile`
Ejecuta profiling de performance.

```bash
e2e perf-profile
e2e perf-profile --service users-api --duration 60
```

**Opciones:**
- `--duration`: Duración en segundos
- `--concurrency`: Usuarios concurrentes
- `--ramp-up`: Tiempo de ramp-up

**Output:**
```
📊 Performance Profile

Duration: 60s
Concurrency: 10 users

Results:
  Mean response time: 245ms
  95th percentile: 520ms
  99th percentile: 890ms
  Requests/sec: 45.2
  Error rate: 0.1%

Bottlenecks detected:
  ⚠️ /api/v1/users (GET) - Slow query
  ⚠️ Database connection pool
```

---

### `perf-report`
Genera reporte de performance con análisis AI.

```bash
e2e perf-report --input perf-results.json
e2e perf-report --compare baseline.json current.json
```

**Genera:**
- Gráficos de latencia
- Análisis de cuellos de botella
- Recomendaciones de optimización
- Comparación con baseline

---

### `telemetry`
Comandos para testing basado en telemetría.

```bash
e2e telemetry collect --service users-api
e2e telemetry analyze --input telemetry.json
e2e telemetry replay --trace trace-id
```

**Subcomandos:**
- `collect`: Recolectar métricas
- `analyze`: Analizar patrones
- `replay`: Reproducir trazas

---

## UI

### `tui`
Lanza Terminal User Interface (interactivo).

```bash
e2e tui
```

**Requiere:**
```bash
e2e install-extras tui
```

**Características:**
- Dashboard interactivo
- Ejecución de tests con UI
- Logs en tiempo real
- Navegación de reportes

---

### `dashboard`
Lanza web dashboard.

```bash
e2e dashboard
e2e dashboard --port 8080
```

**Características:**
- UI web moderna
- Resultados históricos
- Tendencias
- Integración CI/CD

---

## CI/CD

### `setup-ci`
Genera templates de CI/CD.

```bash
e2e setup-ci github
e2e setup-ci gitlab
e2e setup-ci jenkins
e2e setup-ci azure
e2e setup-ci circleci
e2e setup-ci travis
e2e setup-ci bitbucket
```

**Genera:**
```
.github/workflows/     (para GitHub)
├── e2e-basic.yml      # Pipeline básica
├── e2e-parallel.yml   # Ejecución paralela
└── e2e-matrix.yml     # Matriz de tests

.gitlab-ci.yml         (para GitLab)
Jenkinsfile            (para Jenkins)
azure-pipelines.yml    (para Azure)
```

---

## Utilidades

### `install-extras`
Instala dependencias opcionales.

```bash
e2e install-extras tui           # Terminal UI
e2e install-extras grpc          # Soporte gRPC
e2e install-extras dev           # Dependencias de desarrollo
e2e install-extras docs          # Documentación
e2e install-extras rag           # RAG/Vector search
e2e install-extras secrets       # Vault/AWS Secrets
e2e install-extras test-data     # Faker para datos de test
```

**Instalar múltiples:**
```bash
e2e install-extras tui,grpc,dev
```

---

### `import`
Importa formatos externos.

```bash
e2e import --format postman collection.json
e2e import --format openapi api.yaml
e2e import --format swagger swagger.json
e2e import --format curl requests.txt
e2e import --format har network.har
```

**Convierte a:** Estructura de servicios E2E

---

### `set`
Gestiona configuración.

```bash
# Ver configuración
e2e set --list

# Establecer valor
e2e set --key timeout --value 60000
e2e set --key services.users-api.base_url --value http://localhost:8080

# Eliminar valor
e2e set --key services.legacy --delete
```

---

### `watch`
Modo watch - auto-actualización del manifest para un servicio específico.

```bash
e2e watch auth-service         # Watch para auth-service
e2e watch user-service          # Watch para user-service
```

**Argumentos:**
- `directory`: Nombre del servicio (e.g., `auth-service`)

**Características:**
- Detecta cambios en código fuente del microservicio
- Regenera manifest automáticamente usando smart sync
- Monitorea el manifest en `<framework_root>/manifests/<service_name>/`

---

### `debug-execution`
Debug de ejecución fallida.

```bash
e2e debug-execution --test 03_payment_flow.py
e2e debug-execution --trace-id abc123
```

**Proporciona:**
- Stack trace detallado
- Variables en contexto
- Sugerencias de fix
- Replay del fallo

---

### `regression`
Análisis de regresión.

```bash
e2e regression --baseline v1.0 --current v2.0
e2e regression --compare results-v1.json results-v2.json
```

**Detecta:**
- Tests que antes pasaban y ahora fallan
- Cambios de performance
- Nuevos errores

---

### `semantic-analyze`
Análisis semántico de regresiones.

```bash
e2e semantic-analyze
e2e semantic-analyze --drift-threshold 0.1
```

**Detecta:**
- Cambios en lógica de negocio
- Drift semántico
- Inconsistencias de comportamiento

---

### `healing-stats`
Estadísticas de self-healing.

```bash
e2e healing-stats
e2e healing-stats --detailed
```

**Muestra:**
- Tests auto-reparados
- Tasa de éxito de healing
- Patrones de cambios

---

### `recorder`
Grabación y reproducción de sesiones.

```bash
e2e recorder start --name "user-flow"
# ... interactuar con API ...
e2e recorder stop
e2e recorder replay --name "user-flow"
```

**Subcomandos:**
- `start`: Iniciar grabación
- `stop`: Detener grabación
- `replay`: Reproducir grabación
- `list`: Listar grabaciones

---

### `shadow`
Shadow Runner - captura tráfico.

```bash
e2e shadow start --service users-api
e2e shadow analyze --capture capture.json
e2e shadow generate-tests --capture capture.json
```

**Características:**
- Captura tráfico de producción
- Genera tests automáticamente
- Anonimiza datos sensibles

---

### `build-index`
Construye índice vectorial para búsqueda semántica de un servicio específico.

```bash
e2e build-index auth-service         # Build index para auth-service
e2e build-index user-service          # Build index para user-service
```

**Argumentos:**
- `directory`: Nombre del servicio (e.g., `auth-service`)

**Requiere:** `e2e install-extras rag`

**Uso:** Preparar para `e2e search` y `e2e retrieve`

**Nota:** El índice se guarda en `<framework_root>/manifests/<service_name>/.index/`

---

### `ai-learning`
Comandos para AI learning loop.

```bash
e2e ai-learning feedback --test-id 123 --feedback "needs retry"
e2e ai-learning improve --test 03_payment_flow.py
e2e ai-learning report
```

**Subcomandos:**
- `feedback`: Enviar feedback sobre tests
- `improve`: Mejorar test con AI
- `report`: Reporte de aprendizaje

---

### `community`
Community Hub y Test Marketplace.

```bash
e2e community search --query "authentication"
e2e community download --test "jwt-auth-flow"
e2e community upload --test my-test.py
```

**Subcomandos:**
- `search`: Buscar tests compartidos
- `download`: Descargar tests
- `upload`: Compartir tests
- `list`: Listar contribuciones

---

## 🎯 Casos de Uso Completos

### Caso 1: Nuevo Proyecto desde Cero
```bash
# 1. Inicializar
e2e init my-api-tests
cd my-api-tests

# 2. Configurar servicios
e2e new-service users-api
e2e new-service payments-api

# 3. Detectar automáticamente
e2e observe --update-config

# 4. Generar manifest
e2e manifest

# 5. Generar tests
e2e generate-tests

# 6. Ejecutar
e2e run

# 7. Setup CI/CD
e2e setup-ci github
```

### Caso 2: Proyecto Existente
```bash
# 1. Detectar tech stack
e2e deep-scan

# 2. Crear estructura
e2e init . --template minimal

# 3. Importar desde OpenAPI
e2e import --format openapi api.yaml

# 4. Ejecutar
e2e run
```

### Caso 3: Modo AI-First
```bash
# 1. Generar manifiesto
e2e manifest

# 2. Descubrir endpoints
e2e discover

# 3. Planear estrategia
e2e plan-strategy --name "full-coverage"

# 4. Generar tests autónomos
e2e generate-tests --strategy all

# 5. Ejecutar con self-healing
e2e autonomous-run --mode self-healing
```

---

## 📝 Notas Importantes

### Variables de Entorno
```bash
export E2E_CONFIG=/path/to/e2e.conf
export E2E_ENV=prod
export E2E_VERBOSE=true
```

### Archivos de Configuración
- `e2e.conf` - Configuración principal
- `socialseed.config.yaml` - Configuración extendida
- `project_knowledge.json` - Manifest AI (auto-generado)

### Patrones de Nombres
- Servicios: `kebab-case` (ej: `users-api`)
- Tests: `snake_case` (ej: `register_flow`)
- Módulos: `XX_nombre_flow.py` (ej: `01_register_flow.py`)

---

**Versión:** 1.0  
**Framework:** socialseed-e2e v0.1.2  
**Última actualización:** 2026-02-17
