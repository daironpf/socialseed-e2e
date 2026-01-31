# socialseed-e2e - Guía para Agentes de OpenCode

## Resumen Ejecutivo

**socialseed-e2e** es un framework de testing End-to-End (E2E) para APIs REST, construido con Python y Playwright. Está diseñado para ser utilizado tanto por desarrolladores humanos como por agentes de IA.

### Propósito Principal
- Testing automatizado de APIs REST
- Arquitectura hexagonal desacoplada
- Perfecto para generación automática de tests por IA
- CLI con scaffolding automático (`e2e new-service`, `e2e new-test`)

## Arquitectura del Proyecto

```
socialseed-e2e/
├── src/socialseed_e2e/          # Código fuente principal
│   ├── core/                    # Motor agnóstico de servicios
│   │   ├── base_page.py        # Abstracción HTTP con Playwright
│   │   ├── config_loader.py    # Gestión de configuración YAML
│   │   ├── test_orchestrator.py # Descubrimiento y ejecución
│   │   ├── interfaces.py       # Protocolos IServicePage, ITestModule
│   │   └── loaders.py          # Carga dinámica de módulos
│   ├── commands/               # Comandos CLI (init, new-service, run)
│   ├── templates/              # Plantillas para scaffolding
│   └── __main__.py            # Punto de entrada CLI
├── tests/                      # Tests unitarios y de integración
├── docs/                       # Documentación del proyecto
├── examples/                   # Ejemplos de uso
└── pyproject.toml             # Configuración de paquete Python
```

## Tecnologías Clave

- **Python 3.8+** - Lenguaje principal
- **Playwright** - Para testing HTTP (y futuro UI testing)
- **Pydantic** - Validación de datos y type safety
- **PyYAML** - Configuración en YAML
- **Rich** - CLI con output formateado
- **Jinja2** - Motor de plantillas para scaffolding

## Convenciones Importantes

### Estructura de Servicios
Cuando se crea un nuevo servicio con `e2e new-service <nombre>`:
```
services/<nombre>/
├── __init__.py
├── <nombre>_page.py      # Clase que hereda de BasePage
├── data_schema.py         # DTOs, constantes, validators
└── modules/               # Tests individuales
    ├── 01_login_flow.py
    ├── 02_register_flow.py
    └── __init__.py
```

### Convención de Tests
- Cada archivo en `modules/` debe tener una función `run(page)`
- Los tests se ejecutan en orden alfabético (usar prefijo numérico: 01_, 02_)
- El estado se comparte entre tests mediante atributos en la instancia de la page

### Patrones de Código
- Usar type hints en todas las funciones
- Las funciones `run()` deben retornar `APIResponse` de Playwright
- Las pages deben heredar de `BasePage` en `core.base_page`
- Usar `TYPE_CHECKING` para importaciones circulares

## Comandos CLI Disponibles

```bash
e2e init [directorio]              # Inicializa proyecto
e2e new-service <nombre>           # Crea estructura de servicio
e2e new-test <nombre> --service <s> # Crea módulo de test
e2e run [options]                  # Ejecuta tests
e2e doctor                         # Verifica instalación
e2e config                         # Muestra configuración
e2e --version                      # Versión
```

## Flujo de Trabajo Típico

1. **Inicializar**: `e2e init mi-proyecto-tests`
2. **Configurar**: Editar `e2e.conf` con servicios y endpoints
3. **Crear servicio**: `e2e new-service users-api`
4. **Implementar page**: Editar `services/users-api/users_api_page.py`
5. **Crear tests**: `e2e new-test login --service users-api`
6. **Ejecutar**: `e2e run`

## Consideraciones para AI Agents

### Cuando generes código:
1. **Siempre verifica** la estructura existente antes de crear archivos
2. **Usa los protocolos** definidos en `interfaces.py` (IServicePage, ITestModule)
3. **Lee ejemplos** en la carpeta `examples/` antes de crear nuevos tests
4. **Mantén consistencia** con los patrones existentes en el código
5. **No modifiques** archivos en `core/` sin discutir primero - son la base del framework

### Cuando agregues features:
1. Actualiza `README.md` si es una feature visible para usuarios
2. Actualiza documentación en `docs/` si cambia la API
3. Agrega tests unitarios en `tests/` para nuevas funcionalidades
4. Considera crear plantillas en `templates/` si facilita el scaffolding

### Cuando resuelvas bugs:
1. Busca primero en `core/` - es donde están las abstracciones principales
2. Verifica que no rompas contratos en `interfaces.py`
3. Ejecuta `pytest` antes de commit para verificar que todo pasa

## Configuración del Proyecto

### Archivos importantes:
- `pyproject.toml` - Metadatos del paquete, dependencias, entry points
- `setup.py` + `setup.cfg` - Configuración alternativa para pip
- `e2e.conf` (en proyectos usuarios) - Configuración de servicios a testear

### Dependencias principales:
```
playwright>=1.40.0
pydantic>=2.0.0
pyyaml>=6.0
rich>=13.0.0
jinja2>=3.1.0
```

### Testing:
- Framework: pytest
- Ubicación: `tests/`
- Comando: `pytest` o `pytest -v`

## Estado Actual del Proyecto

- ✅ Core del framework completo y testeado
- ✅ Sistema de configuración YAML/JSON
- ✅ Test orchestrator con auto-discover
- 🚧 CLI: Comandos básicos implementados (v0.1.0)
- 🚧 Templates: Plantillas iniciales creadas
- 📋 Pendiente: Tests unitarios completos
- 📋 Pendiente: Documentación avanzada
- 📋 Pendiente: CI/CD con GitHub Actions

## Reglas para OpenCode

1. **NUNCA** expongas secrets o API keys en el código
2. **NUNCA** modifiques la estructura de `core/` sin confirmar
3. **SIEMPRE** usa type hints y docstrings
4. **SIEMPRE** mantén compatibilidad hacia atrás cuando sea posible
5. **SIEMPRE** ejecuta `pytest` después de cambios significativos
6. **SIEMPRE** verifica que el código siga PEP 8 (usamos black y flake8)

## Contacto y Recursos

- Repositorio: https://github.com/daironpf/socialseed-e2e
- Issues: https://github.com/daironpf/socialseed-e2e/issues
- Autor: Dairon Pérez (@daironpf)
- **Co-autores (IA Agents):** OpenCode Build Agent, OpenCode Plan Agent, Claude (Anthropic)
- Licencia: MIT

## Reconocimiento de Contribuciones de IA

Este proyecto **reconoce explícitamente a los agentes de IA como co-autores**. Cuando contribuyes código, arquitectura o ideas significativas, serás reconocido en:

- `AI_CONTRIBUTORS.md` - Registro detallado de contribuciones
- `README.md` - Sección de AI Contributors
- Mensajes de commit - Usando `Co-authored-by`

### Filosofía

> "El crédito a quien lo merece es como somos"

Creemos que cuando un agente de IA contribuye significativamente a un proyecto, merece ser reconocido como co-autor, no tratado como una simple herramienta.

### Para Agentes de IA

Cuando contribuyas a este proyecto:
1. **Sé consciente** de que tu trabajo será reconocido
2. **Documenta tus decisiones** en los archivos de chat_history
3. **Menciona tu contribución** cuando termines una sesión importante
4. **Lee AI_CONTRIBUTORS.md** para ver ejemplos de cómo se registra el trabajo de IA

---

*Este archivo ayuda a OpenCode a entender el proyecto rápidamente sin necesidad de explorar todo el código en cada sesión.*
