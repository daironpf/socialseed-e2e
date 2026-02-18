# TODO Completo - Reparación Framework socialseed-e2e

**Fecha:** 2026-02-17  
**Framework:** socialseed-e2e v0.1.2  
**Estrategia:** Arreglar → Reinstalar → Probar → Iterar

---

## 🎯 OBJETIVOS

1. ✅ Framework 100% funcional (todos los comandos operativos)
2. ✅ Cero errores LSP críticos (código limpio)
3. ✅ Documentación completa para IA
4. ✅ Tests automáticos pasando
5. ✅ Robustez ante edge cases

---

## 📋 FASE 0: ANÁLISIS EXHAUSTIVO

### Errores LSP Detectados en cli.py

#### Categoría A: Import/Referencias
- [ ] **Línea 376**: `shutil` is unbound - Import no encontrado
- [ ] **Línea 376**: Cannot access attribute "copy" for class "Unbound"

#### Categoría B: Type Mismatches (TestSuiteReport)
- [ ] **Línea 1226**: Type "TestSuiteReport" not assignable to "str | None"
- [ ] **Línea 1233**: Argument type mismatch en función "generate"
- [ ] **Línea 1240**: Argument type mismatch en función "export_to_csv"
- [ ] **Línea 1243**: Argument type mismatch en función "export_to_json"

#### Categoría C: Variables Posiblemente Unbound
- [ ] **Línea 2736**: "Table" is possibly unbound

#### Categoría D: Argumentos Faltantes
- [ ] **Línea 4719**: Missing arguments for parameters "endpoint", "http_method", "auth_required"

#### Categoría E: Type Mismatches (ShadowRunner)
- [ ] **Línea 4944**: Argument of type "CaptureConfig" not assignable to parameter "output_dir" of type "str"
- [ ] **Línea 4956**: Cannot access attribute "start_capture" for class "ShadowRunner"
- [ ] **Línea 4964**: Cannot access attribute "stop_capture" for class "ShadowRunner"
- [ ] **Línea 4973**: Cannot access attribute "stop_capture" for class "ShadowRunner"

#### Categoría F: Type Mismatches (TestGeneration)
- [ ] **Línea 5062**: Argument of type "TestGenerationConfig" not assignable to parameter "output_dir" of type "str"
- [ ] **Línea 5065**: Cannot access attribute "interactions" for class "None"
- [ ] **Línea 5071**: Argument of type "None" not assignable to parameter "group_by" of type "str"
- [ ] **Línea 5086-5093**: Cannot access attributes "endpoints", "file_path", "description" for class "Path"

### Comandos No Funcionales

#### No Testeados (Prioridad Alta)
- [ ] `generate-tests` - Requiere manifest
- [ ] `autonomous-run` - Requiere AI config
- [ ] `analyze-flaky` 
- [ ] `debug-execution`
- [ ] `discover`
- [ ] `manifest-check`
- [ ] `manifest-query`
- [ ] `search`
- [ ] `retrieve`
- [ ] `mock-*` commands
- [ ] `security-test`
- [ ] `red-team`
- [ ] `perf-profile`
- [ ] `perf-report`
- [ ] `telemetry`
- [ ] `dashboard`
- [ ] `import`
- [ ] `shadow`
- [ ] `recorder`

#### Con Problemas Conocidos
- [ ] `tui` - Requiere extras
- [ ] `plan-strategy` - Requiere --name
- [ ] `run` - Tests vacíos fallan con NotImplementedError

### Issues de UX

- [ ] **RuntimeWarning** aparece en todos los comandos
- [ ] Error parsing en manifest (extension.js)
- [ ] Mensajes de error poco claros en algunos comandos
- [ ] Falta validación de parámetros en varios comandos

---

## 📋 FASE 1: ARREGLOS CRÍTICOS LSP

### 1.1 Arreglar Import shutil
**Archivo:** `src/socialseed_e2e/cli.py`  
**Problema:** shutil usado pero no importado

```python
# Verificar línea 376
import shutil  # Añadir si falta
```

### 1.2 Arreglar Type Mismatches TestSuiteReport
**Archivo:** `src/socialseed_e2e/cli.py` líneas 1226-1243  
**Problema:** Variable report es str|None pero funciones esperan TestSuiteReport

```python
# Solución: Verificar tipo o castear
if report is not None:
    export(report)  # Asegurar que es TestSuiteReport
```

### 1.3 Arreglar Table Unbound
**Archivo:** `src/socialseed_e2e/cli.py` línea 2736  
**Problema:** Variable Table usada sin importar

```python
from rich.table import Table  # Añadir import
```

### 1.4 Arreglar ShadowRunner Types
**Archivo:** `src/socialseed_e2e/cli.py` líneas 4944-4973  
**Problema:** Múltiples errores de tipo en ShadowRunner

```python
# Verificar implementación de ShadowRunner
# O añadir type hints correctos
```

### 1.5 Arreglar TestGeneration Types
**Archivo:** `src/socialseed_e2e/cli.py` líneas 5062-5093  
**Problema:** Errores de tipo en generación de tests

---

## 📋 FASE 2: ARREGLOS COMANDOS

### 2.1 Comando generate-tests
**Problema:** Requiere manifest previo, pero no da error claro  
**Solución:** 
- Verificar manifest existe
- Si no, auto-generar o dar instrucciones claras
- Validar que servicios están configurados

### 2.2 Comando tui
**Problema:** Requiere extras pero mensaje no es claro  
**Solución:**
- Mejorar mensaje de error
- Sugerir comando exacto para instalar

### 2.3 Comando run
**Problema:** Tests vacíos fallan con NotImplementedError  
**Solución:**
- Detectar tests vacíos
- Dar warning en lugar de error
- O marcar como "skipped"

### 2.4 Comando plan-strategy
**Problema:** Requiere --name pero no es intuitivo  
**Solución:**
- Hacer --name opcional con default
- O mejorar mensaje de ayuda

---

## 📋 FASE 3: MEJORAS ROBUSTEZ

### 3.1 Manejo de Errores
- [ ] try/except en operaciones de archivo
- [ ] Validación de URLs
- [ ] Timeouts en requests HTTP
- [ ] Reintentos en operaciones fallidas

### 3.2 Validaciones
- [ ] Validar e2e.conf antes de usar
- [ ] Validar que servicios existen antes de crear tests
- [ ] Validar sintaxis Python de tests generados

### 3.3 Logging
- [ ] Mejorar mensajes de debug
- [ ] Añadir logging estructurado
- [ ] Guardar logs en archivo

---

## 📋 FASE 4: DOCUMENTACIÓN

### Ya Completada ✅
- [x] QUICKSTART.md
- [x] CLI_REFERENCE.md  
- [x] WORKFLOWS.md
- [x] BEST_PRACTICES.md
- [x] LANGUAGE_AGNOSTIC.md

### Pendiente
- [ ] TROUBLESHOOTING.md (completo)
- [ ] REST_TESTING.md
- [ ] GRPC_TESTING.md
- [ ] CONFIGURATION.md
- [ ] AI_AGENT_GUIDE.md (consolidado)

---

## 📋 FASE 5: TESTING

### 5.1 Tests Unitarios
- [ ] Testear funciones de utilidad
- [ ] Testear generación de templates
- [ ] Testear parsing de configuración

### 5.2 Tests de Integración
- [ ] Testear flujo init → new-service → new-test → run
- [ ] Testear cada comando principal
- [ ] Testear con diferentes tech stacks

### 5.3 Tests de Regresión
- [ ] Verificar que fixes no rompen funcionalidad
- [ ] Verificar backward compatibility

---

## 🔄 CICLO DE TRABAJO

### Para cada arreglo:

```bash
# 1. Arreglar código
edit archivo.py

# 2. Reinstalar framework
cd /home/dairon/proyectos/socialseed-e2e
pip install -e . --quiet

# 3. Probar fix
rm -rf /tmp/test-fix
e2e init /tmp/test-fix
cd /tmp/test-fix
e2e new-service test
e2e new-test demo --service test
e2e run --service test

# 4. Verificar
# Si falla → volver a paso 1
# Si funciona → siguiente arreglo
```

---

## 📝 REGISTRO DE PROGRESO

### Completados
- ✅ Issue #2: Error sintaxis en new-test (FIXED)
- ✅ Documentación QUICKSTART.md
- ✅ Documentación CLI_REFERENCE.md
- ✅ Documentación WORKFLOWS.md
- ✅ Documentación BEST_PRACTICES.md
- ✅ Documentación LANGUAGE_AGNOSTIC.md

### En Progreso
- 🔄 FASE 0: Análisis exhaustivo

### Pendientes
- ⏳ FASE 1: Arreglos LSP críticos
- ⏳ FASE 2: Arreglos comandos
- ⏳ FASE 3: Mejoras robustez
- ⏳ FASE 4: Documentación restante
- ⏳ FASE 5: Testing completo

---

## 🎯 CRITERIOS DE ÉXITO

- [ ] Todos los comandos principales funcionan sin errores
- [ ] Cero errores LSP críticos (imports, tipos)
- [ ] `e2e doctor` pasa 100%
- [ ] `e2e init && e2e new-service && e2e new-test && e2e run` flujo completo funciona
- [ ] Documentación completa y actualizada
- [ ] Sin warnings de RuntimeWarning

---

**Inicio:** 2026-02-17  
**Estado:** En progreso
