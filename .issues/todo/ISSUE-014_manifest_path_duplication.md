# ISSUE-014: manifest genera rutas duplicadas para project_knowledge.json

## Estado
**⚠️ PENDIENTE**

## Descripción
El comando `e2e manifest` genera correctamente el archivo en `.e2e/manifests/users-api/project_knowledge.json`, pero otros comandos como `manifest-query` y `build-index` buscan en `.e2e/manifests/users-api/.e2e/manifests/users-api/project_knowledge.json` (ruta duplicada).

## Pasos para Reproducir
```bash
# 1. Generar manifest (funciona)
e2e manifest ./services/users-api

# 2. Intentar consultar (falla)
e2e manifest-query users-api

# 3. Intentar build-index (falla)
e2e build-index users-api
```

## Error en manifest-query
```
Error querying manifest: Manifest not found at 
.e2e/manifests/users-api/.e2e/manifests/users-api/project_knowledge.json
```

## Error en build-index
```
Error: Manifest not found at 
.e2e/manifests/users-api/.e2e/manifests/users-api/project_knowledge.json
```

## Ubicación del Error
- `manifest-query`: Probablemente en `src/socialseed_e2e/commands/manifest_cmd.py`
- `build-index`: `src/socialseed_e2e/commands/build_index_cmd.py`

## Causa Raíz
Los comandos de consulta están agregando `.e2e/manifests/` a una ruta que ya contiene esa estructura, causando duplicación.

## Solución Propuesta
Revisar la construcción de rutas en `manifest-query` y `build-index` para usar la ruta base del proyecto correctamente.

## Impacto
- **Severidad**: Alta
- **Usuarios afectados**: Cualquier usuario que intente consultar o usar el índice vectorial después de generar un manifest
