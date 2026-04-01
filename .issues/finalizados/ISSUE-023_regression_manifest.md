# ISSUE-023: regression no encuentra manifest generado

## Estado
**⚠️ PENDIENTE**

## Descripción
El comando `e2e regression` falla con "No project manifest found" incluso después de generar el manifest con `e2e manifest`.

## Pasos para Reproducir
```bash
e2e init test_project
e2e new-service users-api --base-url http://localhost:8080
e2e manifest ./services/users-api
e2e regression
```

## Error
```
ValueError: No project manifest found. Run 'e2e manifest' first.
```

## Ubicación del Error
- `src/socialseed_e2e/cli.py` línea 3537 - comando `regression`
- `src/socialseed_e2e/project_manifest/regression_agent.py` línea 468

## Causa Raíz
El regression agent busca el manifest en una ubicación diferente a donde `e2e manifest` lo genera. Probablemente usa el nombre del directorio del proyecto en lugar del nombre del servicio.

## Solución Propuesta
1. Hacer que el regression agent acepte un parámetro `--service`
2. O hacer que escanee todos los manifests disponibles
3. O usar la configuración de `e2e.conf` para determinar el servicio

## Impacto
- **Severidad**: Alta
- **Usuarios afectados**: Usuarios que intenten ejecutar análisis de regresión
