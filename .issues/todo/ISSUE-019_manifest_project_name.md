# ISSUE-019: manifest usa nombre del directorio actual en lugar del servicio

## Estado
**⚠️ PENDIENTE**

## Descripción
Al ejecutar `e2e manifest` sin argumentos específicos dentro de un proyecto, busca el manifest en `.e2e/manifests/{nombre_directorio_actual}/` en lugar de usar el nombre del servicio configurado.

## Pasos para Reproducir
```bash
e2e plan-strategy --name "full-coverage"
e2e discover
```

## Error
```
Manifest not found at .e2e/manifests/test_project/project_knowledge.json
```

## Ubicación del Error
- `src/socialseed_e2e/ai_orchestrator/strategy_planner.py` línea 147
- `src/socialseed_e2e/project_manifest/api.py` línea 66

## Causa Raíz
Los comandos que usan `ManifestAPI` construyen la ruta del manifest usando el nombre del directorio del proyecto en lugar de buscar los manifests de los servicios configurados en `e2e.conf`.

## Solución Propuesta
1. Cuando no se especifique un servicio, listar los services disponibles en `.e2e/manifests/`
2. O usar el nombre del servicio desde `e2e.conf` en lugar del nombre del directorio

## Impacto
- **Severidad**: Alta
- **Usuarios afectados**: Usuarios que intenten usar comandos AI sin especificar manualmente la ruta del servicio
