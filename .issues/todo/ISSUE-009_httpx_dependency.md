# ISSUE-009: Falta Dependencia httpx en port_detector.py

## Estado
**⚠️ PENDIENTE**

## Descripción
El comando `e2e observe` falla con `ModuleNotFoundError: No module named 'httpx'`

## Pasos para Reproducir
```bash
temp_test/venv/Scripts/e2e observe
```

## Error Completo
```
ModuleNotFoundError: No module named 'httpx'
```

## Ubicación del Error
- Archivo: `src/socialseed_e2e/scanner/port_detector.py`
- Línea: 14 (`import httpx`)

## Causa Raíz
El módulo `port_detector.py` importa `httpx` pero esta dependencia no está en `pyproject.toml`.

## Solución Propuesta
1. Agregar `httpx` a las dependencias en `pyproject.toml`
2. O hacer la importación opcional con try/except

## Impacto
- **Severidad**: Media
- **Usuarios afectados**: Usuarios que usan `e2e observe`
