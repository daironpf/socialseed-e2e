# ISSUE-016: manifest-query y build-index buscan manifest en ruta duplicada

## Estado
**⚠️ PENDIENTE**

## Descripción
Los comandos `e2e manifest-query` y `e2e build-index` buscan el archivo `project_knowledge.json` en una ruta duplicada: `.e2e/manifests/users-api/.e2e/manifests/users-api/project_knowledge.json` en lugar de `.e2e/manifests/users-api/project_knowledge.json`.

## Pasos para Reproducir
```bash
# 1. Generar manifest
e2e manifest ./services/users-api

# 2. Verificar que existe
ls .e2e/manifests/users-api/project_knowledge.json  # ✅ Existe

# 3. Intentar consultar
e2e manifest-query users-api  # ❌ Falla

# 4. Intentar build-index
e2e build-index users-api  # ❌ Falla
```

## Error
```
Manifest not found at .e2e/manifests/users-api/.e2e/manifests/users-api/project_knowledge.json
```

## Ubicación del Error
- `manifest-query`: `src/socialseed_e2e/commands/manifest_cmd.py`
- `build-index`: `src/socialseed_e2e/commands/build_index_cmd.py`

## Causa Raíz
Los comandos de consulta construyen la ruta del manifest asumiendo que el argumento es un nombre de servicio y luego agregan `.e2e/manifests/` automáticamente. Pero el `build_index_cmd.py` ya recibe la ruta desde el manifest generator que incluye la ruta completa, causando duplicación.

## Solución Propuesta
Estandarizar cómo se resuelven las rutas del manifest en todos los comandos:
1. Usar una función centralizada para resolver rutas de manifest
2. O verificar si la ruta ya es absoluta antes de agregar prefijos

## Impacto
- **Severidad**: Alta
- **Usuarios afectados**: Cualquier usuario que intente usar búsqueda semántica o consultar manifests
