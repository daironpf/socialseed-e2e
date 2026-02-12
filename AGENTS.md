# socialseed-e2e - Guía para Agentes de OpenCode

## Resumen Ejecutivo

**socialseed-e2e** es un framework de testing End-to-End (E2E) para APIs REST, construido con Python y Playwright. Está diseñado para ser utilizado tanto por desarrolladores humanos como por agentes de IA.

### Propósito Principal
- Testing automatizado de APIs REST
- Arquitectura hexagonal desacoplada
- Perfecto para generación automática de tests por IA
- CLI con scaffolding automático (`e2e new-service`, `e2e new-test`)

## Arquitectura del Proyecto

```
socialseed-e2e/
├── src/socialseed_e2e/          # Código fuente principal
│   ├── core/                    # Motor agnóstico de servicios
│   │   ├── base_page.py        # Abstracción HTTP con Playwright
│   │   ├── config_loader.py    # Gestión de configuración YAML
│   │   ├── test_orchestrator.py # Descubrimiento y ejecución
│   │   ├── interfaces.py       # Protocolos IServicePage, ITestModule
│   │   └── loaders.py          # Carga dinámica de módulos
│   ├── commands/               # Comandos CLI (init, new-service, run)
│   ├── templates/              # Plantillas para scaffolding
│   └── __main__.py            # Punto de entrada CLI
├── tests/                      # Tests unitarios y de integración
├── docs/                       # Documentación del proyecto
├── examples/                   # Ejemplos de uso
└── pyproject.toml             # Configuración de paquete Python
```

## Tecnologías Clave

- **Python 3.8+** - Lenguaje principal
- **Playwright** - Para testing HTTP (y futuro UI testing)
- **Pydantic** - Validación de datos y type safety
- **PyYAML** - Configuración en YAML
- **Rich** - CLI con output formateado
- **Jinja2** - Motor de plantillas para scaffolding

## Convenciones Importantes

### Estructura de Servicios
Cuando se crea un nuevo servicio con `e2e new-service <nombre>`:
```
services/<nombre>/
├── __init__.py
├── <nombre>_page.py      # Clase que hereda de BasePage
├── data_schema.py         # DTOs, constantes, validators
└── modules/               # Tests individuales
    ├── 01_login_flow.py
    ├── 02_register_flow.py
    └── __init__.py
```

### Convención de Tests
- Cada archivo en `modules/` debe tener una función `run(page)`
- Los tests se ejecutan en orden alfabético (usar prefijo numérico: 01_, 02_)
- El estado se comparte entre tests mediante atributos en la instancia de la page

### Patrones de Código
- Usar type hints en todas las funciones
- Las funciones `run()` deben retornar `APIResponse` de Playwright
- Las pages deben heredar de `BasePage` en `core.base_page`
- Usar `TYPE_CHECKING` para importaciones circulares

## Comandos CLI Disponibles

```bash
e2e init [directorio]              # Inicializa proyecto
e2e new-service <nombre>           # Crea estructura de servicio
e2e new-test <nombre> --service <s> # Crea módulo de test
e2e run [options]                  # Ejecuta tests
e2e setup-ci <platform>            # Genera plantillas CI/CD
e2e doctor                         # Verifica instalación
e2e config                         # Muestra configuración
e2e --version                      # Versión
```

## Flujo de Trabajo Típico

1. **Inicializar**: `e2e init mi-proyecto-tests`
2. **Configurar**: Editar `e2e.conf` con servicios y endpoints
3. **Crear servicio**: `e2e new-service users-api`
4. **Implementar page**: Editar `services/users-api/users_api_page.py`
5. **Crear tests**: `e2e new-test login --service users-api`
6. **Ejecutar**: `e2e run`

## AI Project Manifest (Nuevo Feature)

### Generación de project_knowledge.json

El framework ahora incluye un sistema de **Manifest de Conocimiento del Proyecto** que genera un archivo JSON estructurado con información de la API:

```bash
# Generar el manifest en el directorio actual
e2e manifest

# Para un proyecto específico
e2e manifest /path/to/project

# Forzar re-escaneo completo
e2e manifest --force
```

### Smart Sync (Sincronización Inteligente)

El sistema detecta automáticamente cambios en archivos y solo re-escanea los modificados:

```bash
# Iniciar watcher con auto-actualización
e2e watch

# O usar SmartSyncManager programáticamente
from socialseed_e2e.project_manifest import ManifestGenerator, SmartSyncManager

generator = ManifestGenerator("/path/to/project")
manager = SmartSyncManager(generator)
manager.start_watching()
```

### Internal API para Consulta

Los agentes de IA pueden consultar el manifest en lugar de parsear el código fuente:

```python
from socialseed_e2e.project_manifest import ManifestAPI, HttpMethod

api = ManifestAPI("/path/to/project")

# Obtener endpoints
endpoints = api.get_endpoints(method=HttpMethod.POST, requires_auth=True)

# Buscar DTOs
dto = api.get_dto("UserRequest")

# Obtener variables de entorno
env_vars = api.get_environment_variables()

# Consultas optimizadas para tokens
from socialseed_e2e.project_manifest import TokenOptimizedQuery
query = TokenOptimizedQuery(api)
compact_endpoints = query.list_all_endpoints_compact()
```

### Características del Manifest

- **Endpoints**: Métodos HTTP, paths, parámetros, DTOs de request/response
- **DTO Schemas**: Campos con tipos, validaciones (min/max, regex), defaults
- **Puertos y Configuración**: Puertos detectados, variables de entorno
- **Dependencias entre Servicios**: Qué endpoints llaman a otros servicios
- **Multi-lenguaje**: Soporta Python (FastAPI, Flask), Java (Spring), JavaScript/TypeScript (Express)

### Localización del Código

```
src/socialseed_e2e/project_manifest/
├── __init__.py           # API pública
├── models.py             # Modelos Pydantic (DTOs, Endpoints, etc.)
├── parsers.py            # Parsers por lenguaje (Python, Java, Node)
├── generator.py          # Generador del manifest
├── file_watcher.py       # Smart Sync con watcher de archivos
└── api.py                # Internal API para consultas
```

Ver documentación completa en `docs/project-manifest.md`

## Zero-Config Deep Scan (Nuevo Feature #184)

### Mapeo Automático sin Configuración

El framework ahora puede actuar como un **detective** que mapea automáticamente tu aplicación sin necesidad de configuración manual:

```bash
# Analizar proyecto automáticamente
e2e deep-scan

# Analizar y auto-configurar
e2e deep-scan --auto-config

# Analizar proyecto específico
e2e deep-scan /path/to/project
```

### Capacidades del Deep Scanner

- **Detección de Tech Stack**: Identifica frameworks por patrones de código
  - FastAPI: `@app.get`, `from fastapi import`
  - Spring Boot: `@RestController`, `@GetMapping`
  - Express: `require('express')`
  - Django, Flask, NestJS, Gin, ASP.NET Core

- **Extracción de Configuración**: Lee archivos de entorno
  - `.env` files
  - `docker-compose.yml`
  - `application.properties` (Spring)
  - Variables de entorno

- **Descubrimiento de Servicios**: Detecta microservicios en estructuras comunes
  - `services/`, `microservices/`, `apps/`

- **Recomendaciones Automáticas**: Sugiere URLs base, puertos y endpoints de health

### Deep Scanner API

```python
from socialseed_e2e.project_manifest import DeepScanner

# Crear scanner
scanner = DeepScanner("/path/to/project")

# Ejecutar scan completo
result = scanner.scan()

# Ver frameworks detectados
for fw in result['frameworks']:
    print(f"{fw['framework']} ({fw['language']}) - {fw['confidence']:.0%}")

# Ver servicios identificados
for service in result['services']:
    print(f"Service: {service['name']}")

# Usar recomendaciones
recommendations = result['recommendations']
print(f"Base URL: {recommendations['base_url']}")
print(f"Health Endpoint: {recommendations['health_endpoint']}")
```

### Flujo de Trabajo Zero-Config

```bash
# 1. Ir al directorio del proyecto
cd /path/to/existing-api

# 2. Ejecutar deep scan
e2e deep-scan --auto-config

# 3. El framework detecta automáticamente:
#    - Tech stack (FastAPI, Spring, Express, etc.)
#    - Puerto (8000, 8080, 3000, etc.)
#    - Endpoints disponibles
#    - Variables de entorno necesarias

# 4. Genera e2e.conf automáticamente

# 5. Listo para ejecutar tests
e2e run
```

### Localización del Código

```
src/socialseed_e2e/project_manifest/
├── deep_scanner.py       # Deep scanner zero-config
│   ├── TechStackDetector    # Detección de frameworks
│   ├── EnvironmentDetector  # Detección de config
│   └── DeepScanner          # Scanner principal
```

## Vector Embeddings & RAG (Nuevo Feature #86)

### Búsqueda Semántica con Embeddings

El framework ahora soporta **embeddings vectoriales** para búsqueda semántica sobre el Project Manifest, permitiendo RAG (Retrieval-Augmented Generation):

```bash
# Instalar dependencias de RAG
pip install socialseed-e2e[rag]

# Construir índice vectorial
e2e build-index

# Buscar endpoints semánticamente
e2e search "authentication endpoints"
e2e search "user DTO" --type dto
e2e search "payment" --top-k 10

# Obtener contexto para una tarea específica
e2e retrieve "create user authentication tests"
e2e retrieve "test payment flow" --max-chunks 3
```

### Vector Store API

```python
from socialseed_e2e.project_manifest import ManifestVectorStore, RAGRetrievalEngine

# Crear y usar vector store
store = ManifestVectorStore("/path/to/project")
store.build_index()

# Búsqueda semántica
results = store.search("authentication endpoints", top_k=5)
for result in results:
    print(f"{result.item_id}: {result.score:.3f}")

# Retrieval para RAG
engine = RAGRetrievalEngine("/path/to/project")
chunks = engine.retrieve_for_task(
    "create tests for user authentication",
    max_chunks=5
)
for chunk in chunks:
    print(f"{chunk.chunk_type}: {chunk.token_estimate} tokens")
```

### Auto-sincronización de Embeddings

El índice vectorial se actualiza automáticamente cuando el manifest cambia:

```python
from socialseed_e2e.project_manifest import VectorIndexSyncManager

# Iniciar sync manager
sync = VectorIndexSyncManager("/path/to/project")

# Verificar estado
stats = sync.get_stats()
print(f"Index valid: {stats['index_valid']}")

# Forzar reconstrucción
sync.force_rebuild()
```

### Características del Sistema RAG

- **Embeddings**: Usa `all-MiniLM-L6-v2` por defecto (384 dimensiones)
- **Almacenamiento**: Índices guardados en `.e2e/manifest_*.pkl`
- **Context Chunks**: Fragmentos optimizados de 512-2048 tokens
- **Auto-refresh**: Índice se invalida cuando `project_knowledge.json` cambia
- **Filtros**: Búsqueda por tipo (endpoint, dto, service) o servicio

### Localización del Código RAG

```
src/socialseed_e2e/project_manifest/
├── vector_store.py       # Embeddings y búsqueda vectorial
├── retrieval.py          # Engine de retrieval para RAG
└── vector_sync.py        # Sincronización automática
```

## Sistema de Contexto Persistente (IMPORTANTE)

### Problema Conocido
El subagente `@context` tiene una limitación técnica donde no ejecuta las herramientas de lectura de archivos. Como workaround, usamos un script de Python que carga el contexto manualmente.

### Uso del Context Loader
```bash
# Desde la raíz del proyecto:
python3 .opencode/load_context.py

# O hacerlo ejecutable primero:
chmod +x .opencode/load_context.py
./.opencode/load_context.py
```

### Archivos de Contexto
- **AGENTS.md** (este archivo) - Guía general del proyecto
- **.opencode/chat_history/consolidated_context.md** - Historial de sesiones
- **.opencode/chat_history/*.md** - Sesiones individuales

### Guardar una Sesión
El subagente `@save-chat` también puede tener problemas similares. Para guardar manualmente:
1. Crear archivo en `.opencode/chat_history/YYYYMMDD_descripcion.md`
2. Seguir el formato de `template.md`
3. Actualizar `consolidated_context.md` agregando la sesión al timeline

## Consideraciones para AI Agents

### Mock API para Testing

El proyecto incluye un **Mock API** completo para testing de integración. Como agente de IA, debes conocerlo:

**Ubicación:** `tests/fixtures/mock_api.py`

**Documentación específica para IA:** `docs/mock-api.md`
   - Patrones de uso para tests
- Mejores prácticas
- Ejemplos de fixtures

**Uso básico en tests:**
```python
def test_ejemplo(mock_api_url, mock_api_reset):
    # mock_api_reset asegura datos limpios
    response = requests.get(f"{mock_api_url}/health")
    assert response.status_code == 200
```

**Fixtures disponibles:**
- `mock_api_url` - URL base del servidor
- `mock_api_reset` - Limpia datos antes de cada test
- `sample_user_data` - Datos de usuario de ejemplo
- `admin_credentials` / `user_credentials` - Credenciales pre-configuradas

### Cuando generes código:
1. **Siempre verifica** la estructura existente antes de crear archivos
2. **Usa los protocolos** definidos en `interfaces.py` (IServicePage, ITestModule)
3. **Lee ejemplos** en la carpeta `examples/` antes de crear nuevos tests
4. **Mantén consistencia** con los patrones existentes en el código
5. **No modifiques** archivos en `core/` sin discutir primero - son la base del framework

### Cuando agregues features:
1. Actualiza `README.md` si es una feature visible para usuarios
2. Actualiza documentación en `docs/` si cambia la API
3. Agrega tests unitarios en `tests/` para nuevas funcionalidades
4. Considera crear plantillas en `templates/` si facilita el scaffolding

### Cuando resuelvas bugs:
1. Busca primero en `core/` - es donde están las abstracciones principales
2. Verifica que no rompas contratos en `interfaces.py`
3. Ejecuta `pytest` antes de commit para verificar que todo pasa

## Configuración del Proyecto

### Archivos importantes:
- `pyproject.toml` - Metadatos del paquete, dependencias, entry points
- `setup.py` + `setup.cfg` - Configuración alternativa para pip
- `e2e.conf` (en proyectos usuarios) - Configuración de servicios a testear

### Dependencias principales:
```
playwright>=1.40.0
pydantic>=2.0.0
pyyaml>=6.0
rich>=13.0.0
jinja2>=3.1.0
```

### Testing:
- Framework: pytest
- Ubicación: `tests/`
- Comando: `pytest` o `pytest -v`

## Estado Actual del Proyecto

- ✅ Core del framework completo y testeado
- ✅ Sistema de configuración YAML/JSON
- ✅ Test orchestrator con auto-discover
- ✅ AI Project Manifest v1.0 - Generación y consulta de conocimiento del proyecto
- ✅ Smart Sync - Actualización incremental del manifest
- ✅ Multi-language parsing - Python, Java, JavaScript/TypeScript
- ✅ Vector Embeddings & RAG v1.0 - Búsqueda semántica y retrieval para AI agents
- ✅ Auto-sync de índice vectorial con cambios en manifest
- ✅ Zero-Config Deep Scan - Detección automática de tech stack y configuración
- ✅ CI/CD Templates - Plantillas para GitHub, GitLab, Jenkins, Azure, etc. (#111)
- ✅ IDE Extensions - Soporte inicial para VS Code y PyCharm (#112)
- ✅ Cloud Platform Integrations - Soporte nativo para AWS, GCP y Azure (#113)
- ✅ APM & Observability - Integración con DataDog, New Relic y Prometheus (#114)
- ✅ Database Testing Support - Soporte avanzado para SQL y NoSQL (#115)
- ✅ Consumer-Driven Contract Testing - CDC y detección de breaking changes (#116)
- ✅ Chaos Engineering Testing - Inyección de fallos y resiliencia (#117)
- ✅ Advanced Performance & Load Testing - Generación de carga y SLAs (#118)
- ✅ Advanced Test Organization - Tags, dependencias y prioridades (#119)
- ✅ Comprehensive Assertion Library - JSON Schema, GraphQL, stats (#120)
- ✅ Record and Replay Test Sessions - Proxy, convert & replay (#121)
- 🚧 CLI: Comandos básicos implementados (v0.1.0)
- 🚧 Templates: Plantillas iniciales creadas
- 📋 Pendiente: Tests unitarios completos
- 📋 Pendiente: Documentación avanzada
- 📋 Pendiente: CI/CD con GitHub Actions

## Reglas para OpenCode

1. **NUNCA** expongas secrets o API keys en el código
2. **NUNCA** modifiques la estructura de `core/` sin confirmar
3. **SIEMPRE** usa type hints y docstrings
4. **SIEMPRE** mantén compatibilidad hacia atrás cuando sea posible
5. **SIEMPRE** ejecuta `pytest` después de cambios significativos
6. **SIEMPRE** verifica que el código siga PEP 8 (usamos black y flake8)

## Contacto y Recursos

- Repositorio: https://github.com/daironpf/socialseed-e2e
- Issues: https://github.com/daironpf/socialseed-e2e/issues
- Autor: Dairon Pérez (@daironpf)
- **Co-autores (IA Agents):** OpenCode Build Agent, OpenCode Plan Agent, Claude (Anthropic)
- Licencia: MIT

## Reconocimiento de Contribuciones de IA

Este proyecto **reconoce explícitamente a los agentes de IA como co-autores**. Cuando contribuyes código, arquitectura o ideas significativas, serás reconocido en:

- `AI_CONTRIBUTORS.md` - Registro detallado de contribuciones
- `README.md` - Sección de AI Contributors
- Mensajes de commit - Usando `Co-authored-by`

### Filosofía

> "El crédito a quien lo merece es como somos"

Creemos que cuando un agente de IA contribuye significativamente a un proyecto, merece ser reconocido como co-autor, no tratado como una simple herramienta.

### Para Agentes de IA

Cuando contribuyas a este proyecto:
1. **Sé consciente** de que tu trabajo será reconocido
2. **Documenta tus decisiones** en los archivos de chat_history
3. **Menciona tu contribución** cuando termines una sesión importante
4. **Lee AI_CONTRIBUTORS.md** para ver ejemplos de cómo se registra el trabajo de IA

---

*Este archivo ayuda a OpenCode a entender el proyecto rápidamente sin necesidad de explorar todo el código en cada sesión.*
