# ISSUE-006: Error de Encoding en init_cmd.py

## Estado
**⚠️ PENDIENTE**

## Descripción
El comando `e2e init` falla con `UnicodeEncodeError: 'charmap' codec can't encode characters` al intentar escribir archivos con caracteres UTF-8 (emojis).

## Pasos para Reproducir
```bash
temp_test/venv/Scripts/e2e init temp_test/test_project
```

## Error Completo
```
UnicodeEncodeError: 'charmap' codec can't encode characters in position 1239-1241: character maps to <undefined>
```

## Ubicación del Error
- Archivo: `src/socialseed_e2e/commands/init_cmd.py`
- Línea: 311 (`self._create_agent_docs()`)
- Método: `write_text()` de pathlib

## Causa Raíz
El método `write_text()` en Windows usa por defecto codificación cp1252 en lugar de UTF-8.

## Solución Propuesta
Agregar `encoding='utf-8'` al llamar `write_text()`:
```python
readme_path.write_text(self.AGENT_DOCS, encoding='utf-8')
```

## Impacto
- **Severidad**: Media
- **Usuarios afectados**: Usuarios de Windows que ejecutan `e2e init`

## Notas Adicionales
- Los directorios se crean correctamente
- Solo falla al escribir archivos con contenido UTF-8 que contiene emojis
- Necesita fix en todas las llamadas `write_text()` del comando init
