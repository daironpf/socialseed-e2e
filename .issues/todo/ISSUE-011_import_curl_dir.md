# ISSUE-011: Directorio Incorrecto en import curl

## Estado
**⚠️ PENDIENTE**

## Descripción
El comando `e2e import curl` crea los archivos en un directorio incorrecto `.services/imported/` en lugar de `services/imported/`.

## Pasos para Reproducir
```bash
temp_test/venv/Scripts/e2e import curl "curl -X POST http://localhost:5000/users"
```

## Problema
El output muestra:
```
Output: ./services/imported
Generated test: ./services/imported/curl_import.py
```

Pero el directorio se crea como `.services/` (con punto).

## Impacto
- **Severidad**: Media
