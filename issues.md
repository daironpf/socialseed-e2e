# Issues del Framework E2E - socialseed-e2e

**Fecha de análisis:** 2026-02-17  
**Ubicación:** /home/dairon/proyectos/socialseed-e2e/  
**Versión:** 0.1.2

---

## ✅ ISSUES RESUELTOS

### ✅ Issue #2: Error de sintaxis en test generado por `new-test`
**Estado:** ✅ RESUELTO  
**Fecha:** 2026-02-17  

**Problema:** El comando `new-test` generaba archivos con guiones en el nombre (ej: `01_health-check_flow.py`) que causaban error de sintaxis al importar.

**Solución aplicada:**
1. **cli.py línea 818:** Añadido `safe_name = to_snake_case(name)` para sanitizar el nombre del archivo
2. **test_module.py.template:** Corregidas las variables del template de `snake_case_service` a `snake_case_name`

**Cambios:**
```python
# Antes:
test_filename = f"{next_num:02d}_{name}_flow.py"
# Después:
safe_name = to_snake_case(name)
test_filename = f"{next_num:02d}_{safe_name}_flow.py"
```

**Verificación:**
```bash
e2e new-test health-check --service user-api
# Crea: services/user-api/modules/01_health_check_flow.py ✅
```

---

## Estado de Comandos

### ✅ COMANDOS FUNCIONANDO CORRECTAMENTE

| Comando | Estado | Notas |
|---------|--------|-------|
| `--version` | ✅ OK | Muestra versión 0.1.2 |
| `--help` | ✅ OK | Lista todos los comandos disponibles |
| `doctor` | ✅ OK | Verifica instalación y dependencias |
| `config` | ✅ OK | Muestra configuración actual |
| `init` | ✅ OK | Crea proyecto completo con scaffold |
| `new-service` | ✅ OK | Crea servicio con estructura correcta |
| `new-test` | ✅ OK | ✅ FIXED: Crea módulo de test con nombre sanitizado |
| `observe` | ✅ OK | Detecta servicios en puertos |
| `lint` | ✅ OK | Valida archivos de test |
| `deep-scan` | ✅ OK | Detecta tech stack del proyecto |
| `setup-ci` | ✅ OK | Genera templates CI/CD (github, gitlab, etc.) |
| `manifest` | ✅ OK | Genera project_knowledge.json |
| `install-extras` | ✅ OK | Instala dependencias opcionales |

### ⚠️ COMANDOS CON PROBLEMAS

| Comando | Estado | Issue |
|---------|--------|-------|
| `run` | ✅ OK | Tests funcionan correctamente (Issue #4 corregido) |
| `tui` | ✅ OK | Muestra mensaje informativo cuando faltan dependencias |
| `plan-strategy` | ✅ OK | Requiere flag `--name` (mensaje de error correcto) |
| `generate-tests` | ✅ OK | Funciona correctamente, detecta entidades automáticamente |

### ❌ COMANDOS NO TESTEADOS

Ver lista completa en sección anterior (sin cambios).

---

## ✅ Issues Resueltos (2026-02-18)

### ✅ Issue #1: Advertencia RuntimeWarning en TODOS los comandos
**Estado:** ✅ RESUELTO  
**Fecha:** 2026-02-18  

**Problema:** Al ejecutar cualquier comando aparecía:
```
<frozen runpy>:128: RuntimeWarning: 'socialseed_e2e.cli' found in sys.modules...
```

**Solución aplicada:**
- **Archivo:** `src/socialseed_e2e/__init__.py`
- **Cambio:** Eliminada importación circular de `main` desde `__init__.py`
- El entry point en `pyproject.toml` ya apunta directamente a `socialseed_e2e.cli:main`, por lo que no es necesario importar `main` en `__init__.py`

---

### ✅ Issue #3: Error parsing en manifest
**Estado:** ✅ RESUELTO  
**Fecha:** 2026-02-18  

**Problema:** Al generar manifest aparecía error al parsear archivos JavaScript de extensiones IDE:
```
⚠️ Error parsing extension.js: int() argument must be a string... not 'NoneType'
```

**Solución aplicada:**
1. **Archivo:** `src/socialseed_e2e/project_manifest/generator.py`
   - Agregadas exclusiones para `**/ide-extensions/**`, `**/.agent/**`, `**/.github/**`

2. **Archivo:** `src/socialseed_e2e/project_manifest/parsers.py` (NodeParser)
   - Mejorado manejo de errores en `_parse_ports()` para evitar `int(None)`
   - Agregada validación de `match.lastindex` antes de acceder a grupos
   - Agregado manejo de `TypeError` en excepciones

---

## Issues Pendientes

---

## Recomendaciones de Mejora

### 1. Prioridad Alta ✅ PARCIALMENTE COMPLETADO
- ✅ Arreglar Issue #2 (sintaxis en new-test) - **HECHO**
- 🔄 Crear documentación completa en .agent/
- 🔄 Hacer framework agnóstico de lenguaje (soportar APIs de cualquier lenguaje)

### 2. Prioridad Media
- [ ] Eliminar RuntimeWarning (Issue #1)
- [ ] Mejorar manejo de errores en manifest parser (Issue #3)

### 3. Prioridad Baja
- [ ] Testear todos los comandos no testeados
- [ ] Agregar ejemplos de uso a cada comando --help
- [ ] Crear tutorial interactivo

---

## Documentación Creada en .agent/

✅ **Completados:**
1. QUICKSTART.md - Guía rápida de inicio
2. CLI_REFERENCE.md - Referencia completa de comandos
3. WORKFLOWS.md - Flujos de trabajo completos
4. TROUBLESHOOTING.md - Guía de problemas y soluciones

⏳ **Pendientes:**
5. REST_TESTING.md - Testing REST detallado
6. GRPC_TESTING.md - Testing gRPC
7. BEST_PRACTICES.md - Mejores prácticas
8. CONFIGURATION.md - Configuración exhaustiva

---

## Arquitectura Agnóstica de Lenguaje (Diseño Futuro)

Para hacer el framework agnóstico de lenguaje de programación:

### 1. Detectores de Tech Stack (Implementados ✅)
- `deep-scan` detecta Flask, FastAPI, Django, Express, Spring, etc.

### 2. Generadores de Contratos (Pendiente)
- OpenAPI/Swagger parser
- gRPC proto parser
- GraphQL schema parser
- WSDL parser (SOAP)

### 3. Validadores de Respuesta Agnósticos (Pendiente)
- JSON Schema validation (independiente del lenguaje)
- XML validation
- Protocol Buffers validation

### 4. Adaptadores de Protocolo (Parcial)
- HTTP/REST ✅
- gRPC (requiere extras)
- WebSocket (pendiente)
- SOAP (pendiente)

---

## Próximos Pasos

1. ✅ Arreglar Issue #2 (sintaxis en new-test) - **HECHO**
2. ✅ Reinstalar framework - **HECHO**  
3. ✅ Probar fixes - **HECHO**
4. 🔄 Completar documentación .agent/
5. ⏳ Testear más comandos
6. ⏳ Implementar arquitectura agnóstica de lenguaje

---

## Nuevos Issues Encontrados - Prueba de Instalación Limpia (2026-02-18)

**Contexto:** Instalación del framework siguiendo el README.md paso a paso en entorno limpio

### Resumen de Ejecución

Al seguir los 5 pasos del Quick Start en el README, el paso 5 (`e2e run`) falla con múltiples errores.

**Pasos Ejecutados:**
1. ✅ `pip install socialseed-e2e` - Instalación exitosa
2. ✅ `e2e init demo` - Inicialización exitosa  
3. ✅ `e2e new-service demo-api --base-url http://localhost:8080` - Servicio creado
4. ✅ `e2e new-test health --service demo-api` - Test creado
5. ❌ `e2e run` - **FALLA** con 3 errores

---

### Issue #4: Template de Test Genera Código No Funcional [CRÍTICO]

**Archivo:** `src/socialseed_e2e/templates/test_module.py.template`

**Problema:**
El template genera un test con `raise NotImplementedError` en la línea 60, lo que hace que todos los tests nuevos fallen inmediatamente.

**Comportamiento Actual:**
```python
def run(demo_api: 'DemoApiPage') -> APIResponse:
    print(f"Running health test...")
    # ... TODOs y comentarios ...
    print(f"✓ health test completed successfully")
    raise NotImplementedError("Test implementation incomplete - replace with actual test logic")
```

**Comportamiento Esperado (según README):**
El README promete que después de crear el test, `e2e run` debería ejecutar los tests exitosamente.

**Error Mostrado:**
```
⚠ 01_health_flow - Error: Test implementation incomplete - replace with actual test logic
```

**Impacto:**
- Todos los usuarios nuevos experimentan fallos inmediatos
- Contradice la promesa del README de "Get up and running in under 5 minutes"
- Experiencia de usuario frustrante

**Solución Propuesta:**
1. Cambiar el template para generar un test mínimo funcional que haga un health check básico
2. O cambiar el README para indicar que se debe editar el test antes de ejecutar
3. O agregar una opción `--with-example` al comando `new-test` que genere código funcional

---

### Issue #5: Mock Server Requiere Flask No Instalado [CRÍTICO]

**Archivo:** `src/socialseed_e2e/mock_server.py`

**Problema:**
El mock server intenta importar Flask, pero Flask no está incluido en las dependencias del proyecto.

**Error:**
```python
ModuleNotFoundError: No module named 'flask'
```

**Causa Raíz:**
En `mock_server.py` línea 17:
```python
from tests.fixtures.mock_api import MockAPIServer
```

Y en `tests/fixtures/mock_api.py` línea 29:
```python
from flask import Flask, jsonify, request
```

**Impacto:**
- El mock server no puede iniciarse
- Los usuarios no pueden probar el framework sin un API real
- El servicio 'example' incluido en `e2e init` falla automáticamente

**Solución Propuesta:**
1. Agregar `flask` a las dependencias opcionales `[mock]` en `pyproject.toml`
2. O reimplementar el mock server usando solo la librería estándar de Python
3. O usar un servidor HTTP simple con `http.server`

---

### Issue #6: Importación Incorrecta en mock_server.py [CRÍTICO]

**Archivo:** `src/socialseed_e2e/mock_server.py`

**Problema:**
Intenta importar desde `tests.fixtures.mock_api`, pero `tests/` es parte del código fuente del framework y no se incluye en el paquete PyPI.

**Código Problemático:**
```python
from tests.fixtures.mock_api import MockAPIServer
```

**Impacto:**
- Los usuarios que instalan desde PyPI no tienen acceso a `tests/`
- El mock server falla incluso si Flask estuviera instalado
- Rompe la funcionalidad del servicio 'example'

**Solución Propuesta:**
1. Mover `tests/fixtures/mock_api.py` a `src/socialseed_e2e/` para que sea parte del paquete distribuible
2. Actualizar la importación a: `from socialseed_e2e.mock_api import MockAPIServer`
3. Asegurar que mock_api.py se incluya en el paquete wheel/sdist

---

### Issue #7: README No Explica Requisito de Servidor [ALTO]

**Archivo:** `README.md` - Sección "Quick Start"

**Problema:**
El README sugiere que `e2e run` funcionará inmediatamente después de crear el servicio y test, sin mencionar que se necesita:
1. Un API real corriendo, O
2. Iniciar el mock server

**Texto del README (paso 5):**
```bash
### 5. Run Tests

```bash
e2e run
```

**Expected Output:**
```
✅ All tests passed!
```
```

**Realidad:**
Los tests fallan con:
```
✗ 3 of 3 tests failed
  - demo-api: Error: Test implementation incomplete
  - example: Connection refused (no server running)
```

**Solución Propuesta:**
1. Agregar un paso adicional: "Iniciar servidor mock" con `e2e mock-start` o similar
2. O modificar `e2e init` para preguntar si se quiere incluir el servidor mock
3. O actualizar el paso 5 para mostrar output realista (con fallos esperados)

---

### Issue #8: Servicio 'example' Auto-Incluido Falla por Defecto [ALTO]

**Archivo:** `src/socialseed_e2e/templates/e2e.conf.template`

**Problema:**
`e2e init` crea automáticamente un servicio 'example' configurado para localhost:8765, pero no inicia el servidor mock automáticamente.

**Configuración Generada:**
```yaml
services:
  example:
    base_url: http://localhost:8765
    health_endpoint: /health
```

**Comportamiento:**
- Todos los nuevos proyectos tienen un servicio que falla por defecto
- Los usuarios ven tests fallando que no crearon ellos mismos
- Causa confusión sobre si el problema es de su servicio o del framework

**Solución Propuesta:**
1. Opción A: No incluir el servicio 'example' por defecto
2. Opción B: Incluirlo pero comentado en e2e.conf
3. Opción C: Agregar flag `--with-example` a `e2e init`
4. Opción D: Hacer que `e2e run` inicie automáticamente el mock server si está configurado

---

### Issue #9: Tests del Servicio 'example' Usan Puerto Hardcodeado [MEDIO]

**Archivo:** `src/socialseed_e2e/templates/conftest.py.template`

**Problema:**
El conftest.py generado tiene el puerto 8765 hardcodeado sin forma de configurarlo.

**Código:**
```python
MOCK_SERVER_PORT = 8765
MOCK_SERVER_URL = f"http://localhost:{MOCK_SERVER_PORT}"
```

**Impacto:**
- Si el puerto 8765 está ocupado, no se puede usar el mock server
- No hay forma de cambiar el puerto sin editar el archivo

**Solución Propuesta:**
1. Leer el puerto desde una variable de entorno `E2E_MOCK_PORT`
2. O leerlo desde el archivo de configuración e2e.conf
3. O permitir configurarlo vía CLI: `e2e mock-start --port 9000`

---

## Recomendaciones de Prioridad para Nuevos Issues

### Alta Prioridad (Bloqueantes):
1. **Issue #4** - Template de test no funcional
2. **Issue #5** - Flask no en dependencias
3. **Issue #6** - Importación incorrecta de mock_server

### Media Prioridad (UX):
4. **Issue #7** - README incompleto
5. **Issue #8** - Servicio example auto-falla

### Baja Prioridad (Mejoras):
6. **Issue #9** - Puerto hardcodeado

---

*Documento actualizado durante reparación del framework*
