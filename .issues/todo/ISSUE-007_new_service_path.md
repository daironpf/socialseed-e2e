# ISSUE-007: Error en new-service con Rutas Absolutas

## Estado
**⚠️ PENDIENTE**

## Descripción
El comando `e2e new-service` no funciona correctamente cuando se le pasa una ruta absoluta o con barras.

## Pasos para Reproducir
```bash
temp_test/venv/Scripts/e2e new-service temp_test/test_project/api-users --framework fastapi
```

## Problema
El servicio se crea con la ruta completa en el nombre:
```
Created: services/temp_test/test_project/api-users/
Created: services/temp_test/test_project/api-users/temp_test/test_project/api_users_page.py
```

## Comportamiento Esperado
```
Created: services/api-users/
Created: services/api-users/api_users_page.py
```

## Ubicación del Error
- Archivo: `src/socialseed_e2e/commands/new_service_cmd.py`
- Método: `ServiceCreator.create()`

## Causa Raíz
El comando está usando la ruta completa del argumento `name` en lugar de solo el nombre del servicio.

## Solución Propuesta
- Extraer solo el nombre del servicio del path antes de crear los directorios
- Usar `Path(name).name` para obtener el nombre base
- O documentar que solo se debe usar el nombre del servicio, no una ruta

## Impacto
- **Severidad**: Alta
- **Usuarios afectados**: Usuarios que usan rutas relativas/absolutas con new-service
