# ISSUE-008: Error en new-test con Rutas Absolutas

## Estado
**⚠️ PENDIENTE**

## Descripción
El comando `e2e new-test` tiene el mismo problema que new-service - usa la ruta completa en lugar del nombre del test.

## Pasos para Reproducir
```bash
temp_test/venv/Scripts/e2e new-test temp_test/test_project/api-users --service temp_test/test_project/api-users
```

## Problema
El test se crea con la ruta completa en el nombre:
```
Created: services/temp_test/test_project/api-users/modules/api_users_flow.py
```

## Comportamiento Esperado
```
Created: services/api-users/modules/api_users_flow.py
```

## Ubicación del Error
- Archivo: `src/socialseed_e2e/commands/new_test_cmd.py`

## Impacto
- **Severidad**: Alta
