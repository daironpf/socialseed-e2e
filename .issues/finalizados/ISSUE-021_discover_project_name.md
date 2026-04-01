# ISSUE-021: discover busca manifest con nombre de directorio del proyecto

## Estado
**⚠️ PENDIENTE**

## Descripción
El comando `e2e discover` busca el manifest en `.e2e/manifests/{nombre_directorio_proyecto}/` en lugar de buscar los manifests de los servicios configurados.

## Pasos para Reproducir
```bash
e2e init test_project
e2e new-service users-api --base-url http://localhost:8080
e2e manifest ./services/users-api
e2e discover
```

## Error
```
Manifest not found at .e2e/manifests/test_project/project_knowledge.json
```

## Ubicación del Error
- `src/socialseed_e2e/cli.py` - comando `discover`
- Usa `project_root.name` como service_name en lugar de listar servicios disponibles

## Causa Raíz
El comando `discover` no acepta un parámetro de servicio y asume que el nombre del directorio del proyecto es el nombre del servicio.

## Solución Propuesta
1. Agregar argumento opcional `--service` al comando `discover`
2. O hacer que escanee todos los manifests disponibles en `.e2e/manifests/`
3. O usar el primer servicio configurado en `e2e.conf`

## Impacto
- **Severidad**: Alta
- **Usuarios afectados**: Usuarios que intenten usar `e2e discover` en proyectos con nombres de directorio diferentes a los nombres de servicio
