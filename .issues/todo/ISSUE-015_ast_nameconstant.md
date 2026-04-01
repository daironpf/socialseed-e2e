# ISSUE-015: Error AST en manifest generator - NameConstant no existe en Python 3.14

## Estado
**⚠️ PENDIENTE**

## Descripción
Al ejecutar `e2e manifest`, aparece el warning: `module 'ast' has no attribute 'NameConstant'`. Esto indica que el parser AST usa atributos deprecated en Python 3.14.

## Pasos para Reproducir
```bash
e2e manifest ./services/users-api
```

## Warning
```
⚠️ Error parsing data_schema.py: module 'ast' has no attribute 'NameConstant'
```

## Ubicación del Error
- Archivo: Probablemente en `src/socialseed_e2e/project_manifest/parsers.py` o similar
- El atributo `ast.NameConstant` fue eliminado en Python 3.8+ y reemplazado por `ast.Constant`

## Causa Raíz
El parser de Python usa `ast.NameConstant` que fue deprecated en Python 3.8 y eliminado en versiones posteriores. En Python 3.14 ya no existe.

## Solución Propuesta
Buscar todas las referencias a `ast.NameConstant` y reemplazarlas por `ast.Constant`.

## Impacto
- **Severidad**: Media
- **Usuarios afectados**: Usuarios de Python 3.14+ que generen manifests de proyectos Python
- **Consecuencia**: No se parsean correctamente los DTOs y endpoints del código fuente
