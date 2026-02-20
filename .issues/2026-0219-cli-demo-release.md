# Issue: Completar release v0.1.4 - CLI Demo Commands

## metadata
- **Issue ID:** #2026-0219-cli-demo-release
- **Fecha de creación:** 2026-02-19
- **Estado:** EN_PROGRESO
- **Prioridad:** ALTA
- **Etiquetas:** cli, release, demo, templates
- **Asignado a:** OpenCode Agent

---

## Resumen

Completar el release v0.1.4 del framework socialseed-e2e con los comandos `e2e init` y `e2e install-demo` funcionando correctamente.

### Objetivo principal
- `e2e init` debe crear proyectos en blanco (sin ejemplos)
- `e2e install-demo` debe agregar servicios demo completos (REST, gRPC, WebSocket, Auth con JWT)

---

## Problema original

El comando `e2e install-demo` tenía errores de sintaxis Python porque el código de los servidores demo (gRPC, WebSocket, Auth) estaba embebido como strings dentro de la función CLI. Los strings con comillas triples (''' ... ''') no se pueden anidar correctamente.

### Error específico
```
File "src/socialseed_e2e/cli.py", line 747
    grpc_server_code = """""gRPC Demo Server...
                        ^
SyntaxError: unexpected character after line continuation character
```

---

## Solución implementada

### 1. Archivos de plantillas creados

Se crearon archivos de plantilla separados para cada tipo de demo:

| Archivo | Descripción |
|---------|-------------|
| `templates/api_rest_demo.py.template` | Servidor REST (ya existía) |
| `templates/api_grpc_demo.py.template` | Servidor gRPC con operaciones CRUD |
| `templates/api_grpc_demo.proto.template` | Definición de Protocol Buffers |
| `templates/api_websocket_demo.py.template` | Servidor WebSocket para tiempo real |
| `templates/api_auth_demo.py.template` | Servidor Auth con JWT Bearer tokens |

### 2. Puertos asignados

| Demo API | Puerto | Endpoint base |
|----------|--------|---------------|
| REST | 5000 | http://localhost:5000 |
| gRPC | 50051 | localhost:50051 |
| WebSocket | 50052 | ws://localhost:50052/ws |
| Auth | 5003 | http://localhost:5003 |

---

## Estado actual

### Completado ✅
- [x] Crear template `api_grpc_demo.py.template`
- [x] Crear template `api_grpc_demo.proto.template`
- [x] Crear template `api_websocket_demo.py.template`
- [x] Crear template `api_auth_demo.py.template`
- [x] Revertir cli.py a estado funcional (sin errores de sintaxis)

### Pendiente 🔲
- [ ] Actualizar función `install_demo` en `cli.py` para usar las nuevas plantillas
- [ ] Probar comando `e2e install-demo`
- [ ] Probar comando `e2e init --demo`
- [ ] Construir wheel y verificar instalación
- [ ] Hacer commit y push con tag v0.1.4

---

## Próximos pasos

### 1. Actualizar cli.py

La función `install_demo` actual (línea 700) necesita ser extendida para incluir las nuevas demos:

```python
# Ubicación: src/socialseed_e2e/cli.py, línea 700+

# Después de crear demo-api (REST), agregar:

# === gRPC Demo ===
grpc_demo_path = target_path / "api-grpc-demo.py"
if not grpc_demo_path.exists() or force:
    engine.render_to_file(
        "api_grpc_demo.py.template",
        {},
        str(grpc_demo_path),
        overwrite=force,
    )
    # También crear el archivo proto
    proto_path = target_path / "api-grpc-demo.proto"
    engine.render_to_file(
        "api_grpc_demo.proto.template",
        {},
        str(proto_path),
        overwrite=force,
    )

# === WebSocket Demo ===
ws_demo_path = target_path / "api-websocket-demo.py"
# ... render template

# === Auth Demo ===
auth_demo_path = target_path / "api-auth-demo.py"
# ... render template
```

### 2. Actualizar e2e.conf

Agregar las configuraciones de los nuevos servicios:

```yaml
services:
  grpc-demo:
    base_url: localhost:50051
    protocol: grpc
    health_endpoint: /health
    
  websocket-demo:
    base_url: ws://localhost:50052
    protocol: websocket
    
  auth-demo:
    base_url: http://localhost:5003
    health_endpoint: /health
```

### 3. Comandos de prueba

```bash
# Crear proyecto en blanco
mkdir test-project && cd test-project
e2e init

# Agregar demos
e2e install-demo

# Probar cada servidor
python api-rest-demo.py      # Puerto 5000
python api-grpc-demo.py      # Puerto 50051
python api-websocket-demo.py # Puerto 50052
python api-auth-demo.py      # Puerto 5003
```

---

## Notas técnicas

### Dependencies requeridas para demos

```txt
# REST
flask

# gRPC
grpcio
grpcio-tools

# WebSocket
aiohttp

# Auth
flask
pyjwt
cryptography
```

### Estructura de archivos generados

```
mi-proyecto/
├── api-rest-demo.py         # Servidor REST
├── api-grpc-demo.py         # Servidor gRPC
├── api-grpc-demo.proto      # Definición proto
├── api-websocket-demo.py    # Servidor WebSocket
├── api-auth-demo.py         # Servidor Auth/JWT
├── services/
│   ├── demo-api/           # Tests REST
│   └── example/            # Ejemplo
└── e2e.conf
```

---

## Historial de cambios

| Fecha | Cambio |
|-------|--------|
| 2026-02-19 | Creado este issue |
| 2026-02-19 | Creadas plantillas para REST, gRPC, WebSocket, Auth demos |
| 2026-02-19 | Revertido cli.py a estado funcional |

---

## Referencias

- **Archivo AGENTS.md:** Guía principal del proyecto
- **Chat history:** `.opencode/chat_history/20260219_fix_demo_templates.md`
- **Template engine:** `src/socialseed_e2e/utils/template_engine.py`
- **Comando install_demo:** `src/socialseed_e2e/cli.py:700`

---

*Este documento fue creado automáticamente para facilitar la continuidad del trabajo en caso de pérdida de conexión.*
