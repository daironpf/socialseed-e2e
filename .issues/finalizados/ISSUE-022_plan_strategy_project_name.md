# ISSUE-022: plan-strategy usa nombre del directorio del proyecto como service_name

## Estado
**⚠️ PENDIENTE**

## Descripción
El comando `e2e plan-strategy` busca el manifest usando el nombre del directorio del proyecto como service_name, causando error cuando el directorio se llama diferente al servicio.

## Pasos para Reproducir
```bash
e2e init test_project
e2e new-service users-api --base-url http://localhost:8080
e2e manifest ./services/users-api
e2e plan-strategy --name "full-coverage"
```

## Error
```
Manifest not found at .e2e/manifests/test_project/project_knowledge.json
```

## Ubicación del Error
- `src/socialseed_e2e/cli.py` línea 4636 - comando `plan_strategy`
- `src/socialseed_e2e/ai_orchestrator/strategy_planner.py` línea 147
- `src/socialseed_e2e/ai_orchestrator/strategy_planner.py` línea 31 - `CodeAnalyzer` crea `ManifestAPI(project_path)`

## Causa Raíz
`CodeAnalyzer` en `strategy_planner.py` crea `ManifestAPI` pasando solo el `project_path`, lo que hace que `ManifestAPI` use `project_root.name` ("test_project") como service_name en lugar del servicio real ("users-api").

## Solución Propuesta
1. Agregar parámetro `--service` al comando `plan-strategy`
2. O hacer que `CodeAnalyzer` acepte un service_name explícito
3. O escanear todos los manifests disponibles

## Impacto
- **Severidad**: Alta
- **Usuarios afectados**: Usuarios que intenten generar estrategias de test en proyectos con nombres de directorio diferentes a los nombres de servicio
