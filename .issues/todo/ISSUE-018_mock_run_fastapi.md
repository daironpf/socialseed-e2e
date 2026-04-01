# ISSUE-018: mock-run falla porque fastapi no está instalado

## Estado
**⚠️ PENDIENTE**

## Descripción
El comando `e2e mock-run` intenta ejecutar los mock servers generados pero falla porque `fastapi` no está instalado como dependencia core. Los mock servers usan FastAPI pero el extra `dashboard` (que incluye fastapi) es opcional.

## Pasos para Reproducir
```bash
e2e mock-generate stripe
e2e mock-run
```

## Error
```
ModuleNotFoundError: No module named 'fastapi'
```

## Ubicación del Error
- `src/socialseed_e2e/cli.py` línea ~4016
- Los mock servers generados usan FastAPI como backend

## Causa Raíz
Los mock servers se generan con FastAPI pero la dependencia no está incluida en las dependencias core ni se instala automáticamente al generar mocks.

## Solución Propuesta
1. Agregar `fastapi` y `uvicorn` como dependencias core (ya que los mocks las necesitan)
2. O hacer que mock-run verifique e instale las dependencias necesarias antes de ejecutar
3. O generar mocks con Flask (que ya es un extra `mock`) en lugar de FastAPI

## Impacto
- **Severidad**: Media
- **Usuarios afectados**: Usuarios que intenten ejecutar mock servers sin instalar extras manualmente
