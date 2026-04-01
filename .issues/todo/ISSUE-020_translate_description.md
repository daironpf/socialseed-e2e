# ISSUE-020: translate requiere --description obligatorio sin aviso claro

## Estado
**⚠️ PENDIENTE**

## Descripción
El comando `e2e translate` falla con "Missing option '--description'" cuando se pasa el texto como argumento posicional. El usuario espera poder escribir `e2e translate "test login"` pero debe usar `e2e translate --description "test login"`.

## Pasos para Reproducir
```bash
e2e translate "test user login with email and password"
```

## Error
```
Error: Missing option '--description' / '-d'.
```

## Ubicación del Error
- `src/socialseed_e2e/commands/translate_cmd.py`

## Solución Propuesta
Hacer que el texto sea un argumento posicional opcional o mejorar el mensaje de error para indicar claramente que se necesita `--description`.

## Impacto
- **Severidad**: Baja (UX)
- **Usuarios afectados**: Usuarios que esperen comportamiento intuitivo de línea de comandos
