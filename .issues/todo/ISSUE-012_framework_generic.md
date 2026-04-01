# ISSUE-012: Error en new-service con --framework default "generic"

## Estado
**⚠️ PENDIENTE**

## Descripción
El comando `e2e new-service` falla cuando no se especifica `--framework` porque el valor por defecto es "generic" pero no está en las opciones permitidas.

## Pasos para Reproducir
```bash
e2e new-service users-api --base-url http://localhost:8080
```

## Error Completo
```
Error: Invalid value for '--framework' / '-w': 'generic' is not one of 'fastapi', 'spring-boot', 'express', 'django'.
```

## Ubicación del Error
- Archivo: `src/socialseed_e2e/commands/new_service_cmd.py`
- Línea: El decorator `@click.option("--framework", type=click.Choice(...))` no incluye "generic"

## Causa Raíz
El valor por defecto del argumento `framework` es `"generic"` pero el `click.Choice` solo permite: `fastapi`, `spring-boot`, `express`, `django`.

## Solución Propuesta
1. Agregar "generic" a las opciones del `click.Choice`
2. O cambiar el default a "fastapi"
3. O permitir None como default y manejarlo en la lógica

## Impacto
- **Severidad**: Alta
- **Usuarios afectados**: Todos los usuarios que usan `e2e new-service` sin especificar framework
