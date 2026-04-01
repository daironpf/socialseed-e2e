# ISSUE-024: analyze-flaky requiere --test-file pero el help no lo indica claramente

## Estado
**⚠️ PENDIENTE**

## Descripción
El comando `e2e analyze-flaky` falla con "Missing option '--test-file'" cuando se pasa el archivo como argumento posicional.

## Pasos para Reproducir
```bash
e2e analyze-flaky services/users-api/modules/01_login_flow.py
```

## Error
```
Error: Missing option '--test-file' / '-f'.
```

## Ubicación del Error
- `src/socialseed_e2e/cli.py` - comando `analyze_flaky`

## Solución Propuesta
Hacer que el archivo sea un argumento posicional o mejorar el mensaje de error.

## Impacto
- **Severidad**: Baja (UX)
- **Usuarios afectados**: Usuarios que esperen comportamiento intuitivo
