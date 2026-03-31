# ISSUE-010: Mensaje de Error Confuso en build-index

## Estado
**⚠️ PENDIENTE**

## Descripción
El comando `e2e build-index` muestra un mensaje de error confuso cuando no se le pasan argumentos.

## Pasos para Reproducir
```bash
temp_test/venv/Scripts/e2e build-index
```

## Error Actual
```
[ERR] Error: Service name is required
Usage: e2e build-index <service_name>
Example: e2e build-index auth-service
```

## Problema
1. El help dice que acepta `[DIRECTORY]` pero el error dice `<service_name>`
2. El mensaje de ejemplo muestra `service_name` pero debería ser `directory`

## Ubicación del Error
- Archivo: `src/socialseed_e2e/commands/manifest_cmd.py` (probablemente)

## Impacto
- **Severidad**: Baja (confusión menor)
