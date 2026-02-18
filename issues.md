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
| `run` | ⚠️ PARCIAL | Funciona, pero tests vacíos fallan con NotImplementedError |
| `tui` | ⚠️ PARCIAL | Requiere instalar extras primero (mensaje claro) |
| `plan-strategy` | ⚠️ PARCIAL | Requiere flag `--name` (mensaje de error correcto) |
| `generate-tests` | ⚠️ SIN PROBAR | Requiere manifest previo |

### ❌ COMANDOS NO TESTEADOS

Ver lista completa en sección anterior (sin cambios).

---

## Issues Pendientes

### Issue #1: Advertencia RuntimeWarning en TODOS los comandos
**Severidad:** MENOR  
**Descripción:** Al ejecutar cualquier comando aparece:
```
<frozen runpy>:128: RuntimeWarning: 'socialseed_e2e.cli' found in sys.modules after import of package 'socialseed_e2e', but prior to execution of 'package 'socialseed_e2e'.cli'; this may result in unpredictable behaviour
```
**Impacto:** Visual, no afecta funcionalidad  
**Solución:** Revisar importación en `__main__.py` o entry points

---

### Issue #3: Error parsing en manifest
**Severidad:** MENOR  
**Descripción:** Al generar manifest aparece:
```
⚠️ Error parsing /home/dairon/proyectos/socialseed-e2e/ide-extensions/vscode/src/extension.js: int() argument must be a string, a bytes-like object or a real number, not 'NoneType'
```
**Impacto:** Manifest se genera igual, pero con warning  
**Solución:** Mejorar manejo de errores en parser de extension.js

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

*Documento actualizado durante reparación del framework*
