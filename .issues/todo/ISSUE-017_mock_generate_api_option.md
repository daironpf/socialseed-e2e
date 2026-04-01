# ISSUE-017: mock-generate option --api no existe

## Estado
**⚠️ PENDIENTE**

## Descripción
El comando `e2e mock-generate --api stripe` falla porque la opción `--api` no existe. El help muestra que requiere un argumento posicional `SERVICE` y tiene opciones como `--all` pero no `--api`.

## Pasos para Reproducir
```bash
e2e mock-generate --api stripe
```

## Error
```
Error: No such option: --api Did you mean --all?
```

## Ubicación del Error
- `src/socialseed_e2e/commands/mock_cmd.py`

## Solución Propuesta
Agregar la opción `--api` o actualizar la documentación/help para reflejar el uso correcto:
```bash
e2e mock-generate stripe
```

## Impacto
- **Severidad**: Media
- **Usuarios afectados**: Usuarios que sigan la documentación que menciona `--api`
