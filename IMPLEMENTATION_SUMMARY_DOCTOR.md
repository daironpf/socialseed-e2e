# AI-Driven Interactive Doctor - Implementation Summary

## Issue #190: Implementación Completada ✅

### Características Implementadas

#### 1. **Error Analysis** (Análisis de Errores)
- Analiza errores de tests usando el Project Manifest
- Identifica tipos de errores:
  - Type Mismatch (tipos incompatibles)
  - Missing Field (campos faltantes)
  - Validation Error (errores de validación)
  - Auth Error (errores de autenticación)
  - Not Found (recursos no encontrados)
  - Server Error (errores del servidor)
  - Assertion Failure (fallas de aserción)
- Consulta automática del Project Manifest para obtener:
  - Información de endpoints
  - Esquemas de DTOs
  - Tipos esperados de campos

#### 2. **Interactive Prompt** (Prompt Interactivo)
- CLI interactivo con Rich para mostrar:
  - Diagnóstico del error con confianza
  - Sugerencias de fixes con previews
  - Información de archivos afectados
- Opciones de respuesta:
  - A) Fix the test data (Corregir datos del test)
  - B) Update DTO logic (Actualizar lógica del DTO)
  - C) Ignore for now (Ignorar por ahora)
  - D) Manual fix (Fix manual)
- Visualización rica con:
  - Tablas de sugerencias
  - Paneles con información detallada
  - Previews de código

#### 3. **Auto-Fixing** (Auto-Corrección)
- Aplica fixes automáticamente:
  - Conversión de tipos (String → Integer)
  - Adición de campos faltantes
  - Ajuste de valores para validaciones
- Crea backups automáticos antes de modificar
- Modifica archivos de test directamente
- Reporta éxito/fallo con detalles

### Estructura del Módulo

```
src/socialseed_e2e/core/interactive_doctor/
├── __init__.py              # API pública del módulo
├── models.py                # Modelos de datos (ErrorContext, DiagnosisResult, etc.)
├── analyzer.py              # Analizador de errores con consulta al Manifest
├── suggester.py             # Generador de sugerencias de fixes
├── fixer.py                 # Aplicador de fixes automáticos
└── doctor.py                # Doctor interactivo con CLI
```

### Uso

#### Desde Python:
```python
from socialseed_e2e import InteractiveDoctor, ErrorContext

# Crear doctor
doctor = InteractiveDoctor("/path/to/project", interactive=True)
session = doctor.start_session()

# Crear contexto de error
context = ErrorContext(
    test_name="test_create_user",
    service_name="user-service",
    error_message="Validation error: 'age' expected Integer but got String",
    request_data={"name": "John", "age": "25"},  # age es string, debería ser int
    response_status=400
)

# Diagnosticar y corregir
result = doctor.diagnose_and_fix(context, session)

# Ver resumen
summary = doctor.end_session(session)
```

#### Desde CLI (futuro):
```bash
# Ejecutar doctor interactivo
e2e doctor

# Para un test específico
e2e doctor --test test_login

# Modo automático
e2e doctor --auto
```

### Flujo de Trabajo

1. **Análisis**:
   ```
   Error Message: "Validation error: 'age' expected Integer but got String"
   ↓
   Analyzer.identify_error_type() → TYPE_MISMATCH
   ↓
   Analyzer._get_manifest_insights() → Consulta Project Manifest
   ↓
   DiagnosisResult con 85% confianza
   ```

2. **Sugerencias**:
   ```
   DiagnosisResult
   ↓
   FixSuggester.suggest_fixes()
   ↓
   [
     FixSuggestion(UPDATE_TEST_DATA, "Convert 'age' to Integer", automatic=True),
     FixSuggestion(UPDATE_DTO_LOGIC, "Modify DTO to accept String", automatic=False),
     FixSuggestion(IGNORE, "Skip this error", automatic=True)
   ]
   ```

3. **Interacción**:
   ```
   ┌─ Diagnosis (test_create_user) ─┐
   │ Error Type: TYPE_MISMATCH      │
   │ Confidence: 85%                │
   │ Description: Type mismatch...  │
   └────────────────────────────────┘
   
   💡 Fix Suggestions:
   #  Strategy           Title                    Auto
   ─────────────────────────────────────────────────
   1  UPDATE_TEST_DATA   Fix Test Data            ✓
   2  UPDATE_DTO_LOGIC   Update DTO Logic         ✗
   3  IGNORE             Ignore for Now           ✓
   
   Select a fix to apply [1/2/3/S]: 1
   Apply this fix? [Y/n]: Y
   ```

4. **Aplicación**:
   ```
   Fixer.apply_fix()
   ↓
   Crea backup: test_create_user_20240209_143052.py
   ↓
   Aplica cambio: "25" → 25
   ↓
   ✓ Fix applied successfully!
   ```

### Modelos Principales

#### ErrorContext
- Información del error: test_name, service_name, error_message
- Datos de request/response
- Endpoint y método HTTP
- Timestamp y metadata

#### DiagnosisResult
- Tipo de error identificado
- Nivel de confianza (0.0 - 1.0)
- Descripción legible
- Detalles específicos (TypeMismatchDetails, MissingFieldDetails, etc.)
- Insights del Project Manifest
- Archivos afectados

#### FixSuggestion
- Estrategia de fix (UPDATE_TEST_DATA, UPDATE_DTO_LOGIC, etc.)
- Título y descripción
- Flag de automático/manual
- Preview de cambios
- Riesgos potenciales
- Cambios de código planificados

#### AppliedFix
- ID del fix aplicado
- Archivos modificados
- Rutas de backups
- Éxito/fallo
- Mensaje de error si falló

### Estrategias de Fix

- **UPDATE_TEST_DATA**: Actualizar datos en archivos de test
- **UPDATE_DTO_LOGIC**: Modificar DTOs (requiere revisión manual)
- **UPDATE_VALIDATION**: Cambiar reglas de validación
- **ADD_MISSING_FIELD**: Agregar campos faltantes
- **CONVERT_TYPE**: Convertir tipos de datos
- **IGNORE**: Ignorar el error
- **MANUAL_FIX**: Requiere implementación manual

### Archivos Creados

1. **Módulo Principal:**
   - `src/socialseed_e2e/core/interactive_doctor/__init__.py`
   - `src/socialseed_e2e/core/interactive_doctor/models.py`
   - `src/socialseed_e2e/core/interactive_doctor/analyzer.py`
   - `src/socialseed_e2e/core/interactive_doctor/suggester.py`
   - `src/socialseed_e2e/core/interactive_doctor/fixer.py`
   - `src/socialseed_e2e/core/interactive_doctor/doctor.py`

2. **Ejemplos:**
   - `examples/interactive_doctor/example_interactive_doctor.py`

3. **Modificaciones a Archivos Existentes:**
   - `src/socialseed_e2e/__init__.py` - Exportaciones del módulo

### Estadísticas

- **Líneas de código**: ~1,800 líneas
- **Módulos**: 6 archivos Python
- **Clases principales**: 12
- **Documentación**: Completamente documentado

### Ejemplo de Interacción

```
🔍 Diagnosis (test_create_user)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Error Type: TYPE_MISMATCH
Confidence: 85%
Description: Type mismatch in field 'age': expected int, got str

Context:
  • Test: test_create_user
  • Service: user-service
  • Endpoint: POST /users

✓ Endpoint found in Project Manifest
✓ DTO schema found in Project Manifest

💡 Fix Suggestions
┏━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┓
┃ # ┃ Strategy          ┃ Title              ┃ Auto ┃ Description          ┃
┡━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━┩
│ 1 │ UPDATE_TEST_DATA  │ Fix Test Data      │ ✓    │ Convert 'age' from   │
│   │                   │                    │      │ str to int           │
│ 2 │ UPDATE_DTO_LOGIC  │ Update DTO Logic   │ ✗    │ Modify DTO to accept │
│   │                   │                    │      │ str instead of int   │
│ 3 │ IGNORE            │ Ignore for Now     │ ✓    │ Skip this error      │
└───┴─────────────────┴────────────────────┴──────┴──────────────────────┘

Select a fix to apply [1/2/3/S]: 1

Preview of changes:
┌─ Code Preview ─┐
│ # age: "25"    │
│ # age: 25      │
└────────────────┘

Apply this fix? [Y/n]: Y

✓ Fix applied successfully!

Modified files:
  • tests/services/user/modules/test_create_user.py

Backups created in: .e2e/backups
```

### Próximos Pasos (Opcionales)

1. Agregar comando CLI `e2e doctor` con flags
2. Integración automática después de `e2e run --doctor`
3. Soporte para más tipos de errores
4. Análisis de múltiples errores simultáneos
5. Historial de fixes aplicados
6. Undo functionality para restaurar backups
