# ISSUE-025: autonomous-run requiere --strategy-id obligatorio

## Estado
**⚠️ PENDIENTE**

## Descripción
El comando `e2e autonomous-run` falla con "Missing option '--strategy-id'" cuando se ejecuta sin argumentos.

## Pasos para Reproducir
```bash
e2e autonomous-run
```

## Error
```
Error: Missing option '--strategy-id' / '-s'.
```

## Ubicación del Error
- `src/socialseed_e2e/cli.py` - comando `autonomous_run`

## Solución Propuesta
Hacer que `--strategy-id` sea opcional con un valor por defecto o generar una estrategia automáticamente si no se proporciona.

## Impacto
- **Severidad**: Media
- **Usuarios afectados**: Usuarios que intenten ejecutar tests autónomos sin crear una estrategia primero
