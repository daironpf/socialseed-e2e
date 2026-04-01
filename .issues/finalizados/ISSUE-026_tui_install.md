# ISSUE-026: tui no puede instalar dependencias automáticamente

## Estado
**⚠️ PENDIENTE**

## Descripción
El comando `e2e tui` pregunta si desea instalar dependencias pero falla al intentar hacerlo en modo interactivo.

## Pasos para Reproducir
```bash
e2e tui
# Responder "y" a la pregunta
```

## Error
```
Aborted!
```

## Ubicación del Error
- `src/socialseed_e2e/cli.py` - comando `tui`

## Solución Propuesta
Hacer que la instalación de dependencias sea no interactiva o usar `e2e install-extras tui` antes de ejecutar `tui`.

## Impacto
- **Severidad**: Baja
- **Usuarios afectados**: Usuarios que intenten usar la TUI sin instalar dependencias primero
