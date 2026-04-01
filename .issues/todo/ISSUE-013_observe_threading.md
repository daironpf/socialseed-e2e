# ISSUE-013: Error en observe - threading.ThreadPoolExecutor no existe en Python 3.14

## Estado
**⚠️ PENDIENTE**

## Descripción
El comando `e2e observe` falla con `AttributeError: module 'threading' has no attribute 'ThreadPoolExecutor'` en Python 3.14.

## Pasos para Reproducir
```bash
e2e observe --host localhost --ports 8080-8085
```

## Error Completo
```
AttributeError: module 'threading' has no attribute 'ThreadPoolExecutor'
```

## Ubicación del Error
- Archivo: `src/socialseed_e2e/scanner/port_detector.py`
- Línea: 80 (`with threading.ThreadPoolExecutor(max_workers=50) as executor:`)

## Causa Raíz
En Python 3.14, `ThreadPoolExecutor` fue movido de `threading` a `concurrent.futures`. El código usa `threading.ThreadPoolExecutor` que ya no existe.

## Solución Propuesta
```python
# Cambiar:
import threading
# Por:
from concurrent.futures import ThreadPoolExecutor

# Y usar:
with ThreadPoolExecutor(max_workers=50) as executor:
```

## Impacto
- **Severidad**: Alta
- **Usuarios afectados**: Usuarios de Python 3.14+ que usen `e2e observe`
