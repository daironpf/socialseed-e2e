# Task: Convertir E2E Framework a Paquete Pip Independiente
# Proyecto: socialseed-e2e
# Prioridad: Alta
# Status: En Progreso
# Fecha Inicio: 2026-01-30

---

## 🎯 Objetivo del Proyecto

Convertir el framework E2E actual de SocialSeed en un paquete pip independiente y reutilizable llamado `socialseed-e2e` que cualquier desarrollador pueda usar para testear sus APIs REST.

**Repositorio**: https://github.com/daironpf/socialseed-e2e
**Paquete Pip**: socialseed-e2e
**Versión Inicial**: 0.1.0

---

## 📋 Checklist General

- [ ] Fase 1: Setup del Repositorio
- [ ] Fase 2: Configuración de Paquete Pip
- [ ] Fase 3: Refactorización del Core
- [ ] Fase 4: Tests del Framework
- [ ] Fase 5: Documentación
- [ ] Fase 6: CI/CD y Automatización
- [ ] Fase 7: Publicación en PyPI
- [ ] Fase 8: Lanzamiento y Mantenimiento

---

## Fase 1: Preparación y Setup del Repositorio (2-3 horas)

### 1.1 Crear Nuevo Repositorio GitHub
- [x] Crear repositorio: github.com/daironpf/socialseed-e2e
- [ ] Agregar descripción: "Framework E2E para testing de APIs REST con Playwright - Extraído de SocialSeed"
- [ ] Agregar LICENSE (MIT)
- [ ] Agregar topics: python, testing, api, e2e, playwright
- [ ] Crear rama main y protegerla (requerir PRs)
- [ ] Crear issue inicial (ver template al final de este archivo)

### 1.2 Estructura de Directorios Inicial
```
socialseed-e2e/
├── src/
│   └── socialseed_e2e/
│       ├── __init__.py
│       ├── __version__.py          # Versión del paquete
│       ├── cli.py                  # Interfaz de línea de comandos
│       ├── core/                   # Motor E2E (agnóstico)
│       │   ├── __init__.py
│       │   ├── base_page.py        # HTTP methods con Playwright
│       │   ├── config_loader.py    # Carga de e2e.conf
│       │   ├── loaders.py          # Carga dinámica de módulos
│       │   ├── test_orchestrator.py # Orquestador de tests
│       │   ├── interfaces.py       # Protocols de tipado
│       │   ├── models.py           # Modelos Pydantic
│       │   ├── headers.py          # Headers por defecto
│       │   └── check_deps.py       # Validador de arquitectura
│       ├── templates/              # Plantillas para scaffolding
│       │   ├── e2e.conf.template
│       │   ├── service_page.py.template
│       │   ├── test_module.py.template
│       │   └── data_schema.py.template
│       └── utils/                  # Utilidades
│           ├── __init__.py
│           └── validators.py
├── tests/
│   ├── __init__.py
│   ├── unit/                       # Tests unitarios
│   │   ├── test_config_loader.py
│   │   ├── test_base_page.py
│   │   ├── test_loaders.py
│   │   └── test_orchestrator.py
│   ├── integration/                # Tests de integración
│   │   └── test_cli.py
│   └── fixtures/                   # Datos de prueba
│       └── mock_api.py
├── examples/                       # Ejemplos funcionales
│   ├── 01-basic-api/
│   │   ├── README.md
│   │   ├── api.py                  # Flask API de ejemplo
│   │   ├── e2e.conf
│   │   └── tests/
│   │       └── test_crud.py
│   └── 02-auth-jwt/
│       ├── README.md
│       ├── api.py
│       ├── e2e.conf
│       └── tests/
│           └── test_auth.py
├── docs/                           # Documentación
│   ├── README.md                   # Inicio rápido
│   ├── installation.md
│   ├── quickstart.md
│   ├── configuration.md
│   ├── writing-tests.md
│   ├── cli-reference.md
│   └── api-reference.md
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                  # Tests en cada PR
│   │   ├── release.yml             # Publicación PyPI
│   │   └── docs.yml                # Publicar docs
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   ├── feature_request.md
│   │   └── question.md
│   └── PULL_REQUEST_TEMPLATE.md
├── scripts/
│   └── setup_dev.sh               # Script de setup local
├── pyproject.toml                 # Configuración moderna
├── setup.py                       # Entry points CLI
├── setup.cfg                      # Metadata adicional
├── README.md                      # Documentación principal
├── LICENSE                        # MIT License
├── CHANGELOG.md                   # Historial de cambios
├── CONTRIBUTING.md                # Guía de contribución
├── CODE_OF_CONDUCT.md            # Código de conducta
├── .gitignore                     # Python standard
├── .pre-commit-config.yaml        # Hooks de calidad
└── MANIFEST.in                    # Archivos adicionales
```

### 1.3 Migrar Código desde SocialSeed
- [ ] Copiar `verify_services/e2e/core/` → `src/socialseed_e2e/core/`
- [ ] Mantener estructura de imports (ajustar paths)
- [ ] NO copiar código específico de SocialSeed (services/auth/)
- [ ] Mantener licencia y referencias a SocialSeed en README
- [ ] Crear commits atómicos con mensajes claros

### 1.4 Configuración Inicial Git
- [ ] git init
- [ ] git add .
- [ ] git commit -m "Initial commit: Setup project structure"
- [ ] git remote add origin https://github.com/daironpf/socialseed-e2e.git
- [ ] git push -u origin main

**Estimado**: 2-3 horas

---

## Fase 2: Configuración de Paquete Pip (2-3 horas)

### 2.1 Crear pyproject.toml
```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "socialseed-e2e"
version = "0.1.0"
authors = [
    {name = "Dairon Pérez Frías", email = "dairon.perezfrias@gmail.com"},
]
description = "Framework E2E para testing de APIs REST con Playwright"
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.9"
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "Topic :: Software Development :: Testing",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Operating System :: OS Independent",
]
keywords = ["testing", "e2e", "api", "playwright", "rest", "framework"]
dependencies = [
    "playwright>=1.40.0",
    "pydantic>=2.0.0",
    "pyyaml>=6.0",
    "requests>=2.31.0",
    "typing-extensions>=4.8.0",
    "click>=8.0.0",  # Para CLI
    "rich>=13.0.0",  # Output bonito en terminal
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0.0",
    "isort>=5.12.0",
    "flake8>=6.0.0",
    "mypy>=1.0.0",
    "pre-commit>=3.0.0",
    "twine>=4.0.0",
    "build>=0.10.0",
]
docs = [
    "sphinx>=7.0.0",
    "sphinx-rtd-theme>=1.3.0",
    "myst-parser>=2.0.0",
]

[project.scripts]
e2e = "socialseed_e2e.cli:main"
socialseed-e2e = "socialseed_e2e.cli:main"

[project.urls]
Homepage = "https://github.com/daironpf/socialseed-e2e"
Documentation = "https://socialseed-e2e.readthedocs.io/"
Repository = "https://github.com/daironpf/socialseed-e2e"
Issues = "https://github.com/daironpf/socialseed-e2e/issues"
Changelog = "https://github.com/daironpf/socialseed-e2e/blob/main/CHANGELOG.md"

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
socialseed_e2e = ["templates/*.template"]

# Black formatter
[tool.black]
line-length = 100
target-version = ['py39', 'py310', 'py311', 'py312']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''

# isort
[tool.isort]
profile = "black"
line_length = 100
multi_line_output = 3

# mypy
[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
ignore_missing_imports = true

# pytest
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --tb=short --strict-markers"
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "slow: Slow tests",
]

# Coverage
[tool.coverage.run]
source = ["src/socialseed_e2e"]
omit = ["*/tests/*", "*/templates/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
show_missing = true
fail_under = 80
```

- [ ] Crear archivo pyproject.toml con configuración completa
- [ ] Verificar sintaxis TOML válida
- [ ] Definir classificadores apropiados para PyPI

### 2.2 Crear setup.py (Entry Points)
```python
#!/usr/bin/env python3
"""Setup script for socialseed-e2e package."""
from setuptools import setup

# La configuración principal está en pyproject.toml
# Este archivo es para compatibilidad backward
setup()
```

- [ ] Crear setup.py mínimo
- [ ] Verificar entry points funcionan

### 2.3 Crear setup.cfg
```ini
[metadata]
name = socialseed-e2e
version = attr: socialseed_e2e.__version__.__version__
description = Framework E2E para testing de APIs REST con Playwright
long_description = file: README.md
long_description_content_type = text/markdown
author = Dairon Pérez
author_email = tu-email@example.com
license = MIT
license_files = LICENSE
classifiers =
    Development Status :: 3 - Alpha
    Intended Audience :: Developers
    License :: OSI Approved :: MIT License
    Programming Language :: Python :: 3
    Programming Language :: Python :: 3.9
    Programming Language :: Python :: 3.10
    Programming Language :: Python :: 3.11
    Programming Language :: Python :: 3.12

[options]
package_dir=
    =src
packages=find:
python_requires = >=3.9
install_requires =
    playwright>=1.40.0
    pydantic>=2.0.0
    pyyaml>=6.0
    requests>=2.31.0
    typing-extensions>=4.8.0
    click>=8.0.0
    rich>=13.0.0

[options.packages.find]
where=src

[options.package_data]
socialseed_e2e = templates/*.template

[options.entry_points]
console_scripts =
    e2e = socialseed_e2e.cli:main
    socialseed-e2e = socialseed_e2e.cli:main
```

- [ ] Crear setup.cfg completo
- [ ] Definir entry points CLI

### 2.4 Crear MANIFEST.in
```
include LICENSE
include README.md
include CHANGELOG.md
include CONTRIBUTING.md
recursive-include src/socialseed_e2e/templates *.template
recursive-include docs *.md *.rst
recursive-include examples *.py *.md *.yml *.yaml
```

- [ ] Crear MANIFEST.in
- [ ] Verificar includes correctos

### 2.5 Crear __version__.py
```python
"""Version information for socialseed-e2e."""

__version__ = "0.1.0"
__version_info__ = (0, 1, 0)
__author__ = "Dairon Pérez"
__email__ = "tu-email@example.com"
__license__ = "MIT"
__copyright__ = "Copyright 2026 Dairon Pérez"
__url__ = "https://github.com/daironpf/socialseed-e2e"
```

- [ ] Crear archivo de versión
- [ ] Actualizar metadatos

**Estimado**: 2-3 horas

---

## Fase 3: Refactorización del Core (4-5 horas)

### 3.1 Generalizar ConfigLoader
**Objetivo**: Que funcione con cualquier proyecto, no solo SocialSeed

#### Cambios en config_loader.py:
- [ ] Modificar `_find_config_file()` para buscar en:
  1. `./e2e.conf` (directorio actual)
  2. `./config/e2e.conf`
  3. `./tests/e2e.conf`
  4. `~/.config/socialseed-e2e/default.conf`
  5. Variable `E2E_CONFIG_PATH`
  6. Prompt al usuario si no se encuentra

- [ ] Agregar método `create_default_config()`:
```python
def create_default_config(path: Path) -> None:
    """Crea un archivo e2e.conf por defecto."""
    template = """
general:
  environment: dev
  timeout: 30000
  verbose: true

services:
  myapi:
    name: my-api
    base_url: http://localhost:8080
    health_endpoint: /health
    auto_start: false
    required: true
"""
    path.write_text(template.strip())
    print(f"✓ Created default config: {path}")
```

- [ ] Agregar validación de configuración mínima
- [ ] Mejorar mensajes de error para usuarios

### 3.2 Implementar CLI (cli.py)
**Objetivo**: Interfaz de línea de comandos intuitiva

#### Comandos a implementar:
- [ ] `e2e --version`: Mostrar versión
- [ ] `e2e --help`: Ayuda general

- [ ] `e2e init [directory]`:
  - Crear e2e.conf inicial
  - Crear estructura de directorios
  - Mensaje de bienvenida
  - Sugerir próximos pasos
  ```
  $ e2e init
  ✓ Created e2e.conf
  ✓ Created services/
  ✓ Created tests/

  Next steps:
  1. Edit e2e.conf to configure your API
  2. Run: e2e new-service myapi
  3. Run: e2e new-test login --service myapi
  4. Run: e2e run
  ```

- [ ] `e2e run [options]`:
  - Opciones: `--service`, `--module`, `--verbose`, `--output json/html`
  - Detectar y ejecutar tests
  - Mostrar reporte bonito (con rich)
  - Guardar resultados si se solicita

- [ ] `e2e new-service <name> [options]`:
  - Crear directorio `services/<name>/`
  - Generar archivos desde templates:
    - `<name>_page.py` (extiende BasePage)
    - `config.py`
    - `data_schema.py`
    - `__init__.py`
  - Agregar al e2e.conf automáticamente

- [ ] `e2e new-test <name> --service <svc> [options]`:
  - Buscar próximo número disponible (01, 02...)
  - Crear `services/<svc>/modules/XX_<name>_flow.py`
  - Generar desde template con nombre correcto
  - Agregar imports necesarios

- [ ] `e2e doctor`:
  - Verificar playwright instalado
  - Verificar browsers: `playwright install`
  - Verificar e2e.conf existe
  - Verificar estructura correcta
  - Reportar problemas y soluciones

- [ ] `e2e config`:
  - Mostrar configuración actual
  - Validar sintaxis
  - Mostrar rutas detectadas

#### Implementación CLI:
```python
import click
from rich.console import Console
from rich.table import Table

console = Console()

@click.group()
@click.version_option(version=__version__)
def cli():
    """socialseed-e2e: Framework E2E para APIs REST"""
    pass

@cli.command()
def init():
    """Inicializa un proyecto E2E"""
    # ... implementación
    console.print("✓ [green]Project initialized successfully![/green]")
```

- [ ] Instalar click y rich
- [ ] Implementar cada comando
- [ ] Agregar tests para CLI
- [ ] Crear ayuda detallada por comando

### 3.3 Crear Sistema de Templates
**Objetivo**: Scaffolding automático de código

#### Archivos template a crear:

- [ ] `templates/e2e.conf.template`:
```yaml
general:
  environment: dev
  timeout: 30000
  user_agent: "{{ project_name }}-E2E-Agent/1.0"
  verbose: true

services:
  {{ service_name }}:
    name: "{{ service_name }}-service"
    base_url: {{ base_url }}
    health_endpoint: "/health"
    timeout: 5000
    auto_start: false
    required: true
```

- [ ] `templates/service_page.py.template`:
```python
from socialseed_e2e.core.base_page import BasePage
from .data_schema import {{ ServiceName }}DTO
from .config import get_{{ service_name }}_config
from playwright.sync_api import APIResponse
from typing import Optional

class {{ ServiceName }}Page(BasePage):
    """
    Hub para {{ service_name }} service.
    Gestiona estado y orquesta módulos de test.
    """

    def __init__(self, playwright=None, base_url=None):
        config = get_{{ service_name }}_config()
        url = base_url or config.base_url
        super().__init__(url, playwright, default_headers=config.default_headers)

        # Estado compartido entre módulos
        self.current_entity: Optional[{{ ServiceName }}DTO] = None
        self.auth_token: Optional[str] = None

    def get_entity(self, entity_id: str) -> APIResponse:
        """Obtener entidad por ID."""
        return self.get(f"/entities/{entity_id}")
```

- [ ] `templates/test_module.py.template`:
```python
from playwright.sync_api import APIResponse
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..{{ service_name }}_page import {{ ServiceName }}Page

def run({{ service_var }}: '{{ ServiceName }}Page') -> APIResponse:
    """
    {{ description }}

    Args:
        {{ service_var }}: Instancia de {{ ServiceName }}Page

    Returns:
        APIResponse: Respuesta HTTP
    """
    print("Running {{ module_name }}...")

    # TODO: Implementar lógica de test
    response = {{ service_var }}.get("/endpoint")

    if response.ok:
        print("✓ {{ success_message }}")
    else:
        print(f"✗ Failed: {response.status}")
        raise AssertionError("{{ failure_message }}")

    return response
```

- [ ] `templates/data_schema.py.template`:
```python
from pydantic import BaseModel
from typing import Optional, List

class {{ ServiceName }}DTO(BaseModel):
    """Data Transfer Object para {{ service_name }}."""
    id: str
    name: str
    created_at: str

# Endpoints
GET_ENDPOINT = "/{id}"
POST_ENDPOINT = "/create"
```

#### Implementar TemplateEngine:
```python
from pathlib import Path
from string import Template

class TemplateEngine:
    """Renderiza templates con variables."""

    def __init__(self, template_dir: Path):
        self.template_dir = template_dir

    def render(self, template_name: str, variables: dict) -> str:
        template_path = self.template_dir / f"{template_name}.template"
        template_content = template_path.read_text()
        return Template(template_content).substitute(variables)
```

- [ ] Crear directorio templates/
- [ ] Crear archivos .template
- [ ] Implementar TemplateEngine
- [ ] Integrar con comandos CLI

### 3.4 Mejorar BasePage
- [ ] Agregar logging estructurado
- [ ] Agregar métodos helpers comunes
- [ ] Mejorar mensajes de error
- [ ] Agregar retry automático opcional
- [ ] Soporte para rate limiting

### 3.5 Actualizar Imports y Paths
- [ ] Cambiar imports relativos a absolutos donde sea necesario
- [ ] Asegurar compatibilidad con instalación pip
- [ ] Verificar que `from socialseed_e2e import ...` funcione

**Estimado**: 4-5 horas

---

## Fase 4: Tests del Framework (4-5 horas)

### 4.1 Tests Unitarios (tests/unit/)

#### test_config_loader.py:
- [ ] Test carga de YAML válido
- [ ] Test sustitución de variables de entorno
- [ ] Test búsqueda en múltiples paths
- [ ] Test creación de config por defecto
- [ ] Test manejo de errores (archivo no existe, YAML inválido)
- [ ] Test recarga de configuración

#### test_base_page.py:
- [ ] Mock de Playwright
- [ ] Test métodos HTTP (GET, POST, PUT, DELETE, PATCH)
- [ ] Test combinación de headers
- [ ] Test parseo de respuestas
- [ ] Test manejo de errores de red
- [ ] Test setup/teardown

#### test_loaders.py:
- [ ] Test descubrimiento de módulos
- [ ] Test carga dinámica de funciones
- [ ] Test ordenamiento alfabético
- [ ] Test manejo de archivos sin función 'run'
- [ ] Test archivos corruptos

#### test_orchestrator.py:
- [ ] Test descubrimiento de servicios
- [ ] Test ejecución en orden correcto
- [ ] Test manejo de excepciones
- [ ] Test cleanup en finally
- [ ] Test factory de contextos

### 4.2 Tests de Integración (tests/integration/)

#### test_cli.py:
- [ ] Test comando `e2e init`
  - Verificar creación de archivos
  - Verificar contenido de e2e.conf
- [ ] Test comando `e2e run`
  - Con mock de servidor Flask
  - Verificar reporte de resultados
- [ ] Test comando `e2e new-service`
  - Verificar creación de archivos
  - Verificar sintaxis válida
- [ ] Test comando `e2e new-test`
  - Verificar numeración automática
  - Verificar contenido del test

#### Mock API (tests/fixtures/mock_api.py):
```python
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({"status": "UP"})

@app.route('/api/users', methods=['GET', 'POST'])
def users():
    # CRUD simple para testing
    pass
```

- [ ] Crear Flask app de prueba
- [ ] Crear fixtures pytest
- [ ] Tests end-to-end reales

### 4.3 Configurar pytest
- [ ] Crear conftest.py
- [ ] Definir fixtures comunes
- [ ] Configurar marks (unit, integration, slow)
- [ ] Configurar cobertura

### 4.4 Meta de Cobertura
- [ ] > 80% cobertura de código
- [ ] Todos los módulos core cubiertos
- [ ] CLI completamente testeado
- [ ] Integrar con codecov.io

**Estimado**: 4-5 horas

---

## Fase 5: Documentación (5-6 horas)

### 5.1 README.md Principal

#### Estructura obligatoria:
- [ ] Badges al inicio:
  ```markdown
  ![PyPI](https://img.shields.io/pypi/v/socialseed-e2e)
  ![Python](https://img.shields.io/pypi/pyversions/socialseed-e2e)
  ![Tests](https://github.com/daironpf/socialseed-e2e/workflows/CI/badge.svg)
  ![Coverage](https://codecov.io/gh/daironpf/socialseed-e2e/branch/main/graph/badge.svg)
  ![License](https://img.shields.io/badge/license-MIT-blue)
  ```

- [ ] Logo/Imagen (opcional pero recomendado)
- [ ] One-liner descriptivo
- [ ] Instalación rápida (1 comando)
- [ ] Ejemplo "Hello World" (5-10 líneas máximo)
- [ ] GIF animado o screenshot del CLI funcionando
- [ ] Características principales (bullet points)
- [ ] Tabla de contenidos
- [ ] Enlaces a documentación completa

#### Secciones detalladas:
- [ ] ¿Por qué socialseed-e2e?
- [ ] Comparación con alternativas (pytest + requests, etc.)
- [ ] Instalación detallada
- [ ] Quick Start (15 minutos)
- [ ] Ejemplos de uso
- [ ] Documentación API
- [ ] Contribuir
- [ ] Roadmap
- [ ] Licencia

### 5.2 Documentación Estructurada (docs/)

#### docs/installation.md:
- [ ] Requisitos (Python 3.9+, Playwright)
- [ ] Instalación con pip
- [ ] Instalación de browsers Playwright
- [ ] Verificación de instalación (`e2e doctor`)
- [ ] Troubleshooting común

#### docs/quickstart.md:
- [ ] Crear proyecto de ejemplo
- [ ] Inicializar E2E (`e2e init`)
- [ ] Crear servicio (`e2e new-service`)
- [ ] Crear test (`e2e new-test`)
- [ ] Ejecutar tests (`e2e run`)
- [ ] Ver resultados

#### docs/configuration.md:
- [ ] Estructura de e2e.conf
- [ ] Opciones de general
- [ ] Configuración de servicios
- [ ] Variables de entorno
- [ ] API Gateway
- [ ] Bases de datos
- [ ] Ejemplos de configuración

#### docs/writing-tests.md:
- [ ] Estructura de un módulo de test
- [ ] Función run(context)
- [ ] Usar ServicePage
- [ ] Assertions y manejo de errores
- [ ] Compartir estado entre tests
- [ ] Mejores prácticas
- [ ] Ejemplos completos

#### docs/cli-reference.md:
- [ ] Todos los comandos documentados
- [ ] Opciones y flags
- [ ] Ejemplos de uso por comando
- [ ] Mensajes de error comunes

#### docs/api-reference.md:
- [ ] Generar con Sphinx autodoc
- [ ] Documentar todas las clases públicas
- [ ] Métodos con ejemplos
- [ ] Atributos y propiedades

### 5.3 Ejemplos Funcionales (examples/)

#### examples/01-basic-crud/:
- [ ] API Flask simple (SQLite opcional)
- [ ] e2e.conf configurado
- [ ] Tests para:
  - Crear recurso (POST)
  - Listar recursos (GET)
  - Obtener uno (GET /id)
  - Actualizar (PUT/PATCH)
  - Eliminar (DELETE)
- [ ] README con instrucciones paso a paso
- [ ] Debe poder ejecutarse: `cd examples/01-basic-crud && pip install -r requirements.txt && python api.py & && e2e run`

#### examples/02-auth-jwt/:
- [ ] API con autenticación JWT
- [ ] Login/Register
- [ ] Endpoints protegidos
- [ ] Refresh token
- [ ] Tests de flujo completo

#### examples/03-microservices/:
- [ ] 2-3 servicios pequeños
- [ ] Comunicación entre ellos
- [ ] Tests orquestados
- [ ] Docker Compose opcional

### 5.4 Otros Archivos de Documentación

#### CHANGELOG.md:
- [ ] Formato: Keep a Changelog
- [ ] Versiones: 0.1.0 (initial), 0.2.0, etc.
- [ ] Secciones: Added, Changed, Deprecated, Removed, Fixed, Security

#### CONTRIBUTING.md:
- [ ] Cómo reportar bugs
- [ ] Cómo sugerir features
- [ ] Setup de desarrollo
- [ ] Guía de estilo de código
- [ ] Proceso de PRs
- [ ] Código de conducta

#### CODE_OF_CONDUCT.md:
- [ ] Basado en Contributor Covenant
- [ ] Comportamiento esperado
- [ ] Comportamiento inaceptable
- [ ] Aplicación

**Estimado**: 5-6 horas

---

## Fase 6: CI/CD y Automatización (3-4 horas)

### 6.1 GitHub Actions Workflows

#### .github/workflows/ci.yml:
```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.9', '3.10', '3.11', '3.12']

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"
          playwright install chromium

      - name: Lint with black
        run: black --check src/ tests/

      - name: Lint with flake8
        run: flake8 src/ tests/ --count --select=E9,F63,F7,F82 --show-source --statistics

      - name: Type check with mypy
        run: mypy src/socialseed_e2e

      - name: Test with pytest
        run: pytest --cov=socialseed_e2e --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          fail_ci_if_error: true
```

- [ ] Crear workflow CI
- [ ] Configurar matrix de Python versions
- [ ] Agregar linting (black, flake8, mypy)
- [ ] Configurar coverage con codecov
- [ ] Verificar que funcione en PRs

#### .github/workflows/release.yml:
```yaml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install build twine

      - name: Run tests
        run: |
          pip install -e ".[dev]"
          pytest

      - name: Build package
        run: python -m build

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          password: ${{ secrets.PYPI_API_TOKEN }}

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v1
        with:
          files: dist/*
          generate_release_notes: true
```

- [ ] Crear workflow de release
- [ ] Configurar triggers en tags v*
- [ ] Agregar secreto PYPI_API_TOKEN
- [ ] Verificar publicación automática

#### .github/workflows/docs.yml:
```yaml
name: Docs

on:
  push:
    branches: [main]

jobs:
  docs:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -e ".[docs]"

      - name: Build docs
        run: |
          cd docs
          make html

      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./docs/_build/html
```

- [ ] Crear workflow de docs
- [ ] Configurar GitHub Pages
- [ ] Verificar deploy automático

### 6.2 Pre-commit Hooks (.pre-commit-config.yaml)
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-json
      - id: check-toml
      - id: check-merge-conflict

  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
        additional_dependencies: [flake8-docstrings]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

- [ ] Crear archivo de configuración
- [ ] Instalar hooks: `pre-commit install`
- [ ] Verificar que corran en cada commit

### 6.3 Templates de GitHub

#### .github/ISSUE_TEMPLATE/bug_report.md:
```markdown
---
name: Bug report
about: Reportar un bug
---

**Describe el bug**
Descripción clara del bug.

**Para reproducir**
Pasos:
1. Instalar '...'
2. Ejecutar '....'
3. Ver error

**Comportamiento esperado**
Qué debería pasar.

**Screenshots**
Si aplica.

**Entorno:**
 - OS: [e.g. Ubuntu 22.04]
 - Python: [e.g. 3.11]
 - Version: [e.g. 0.1.0]
```

#### .github/ISSUE_TEMPLATE/feature_request.md:
```markdown
---
name: Feature request
about: Sugerir una nueva feature
---

**¿Tu feature está relacionada a un problema?**
Descripción clara del problema.

**Describe la solución que te gustaría**
Qué te gustaría que pasara.

**Describe alternativas que has considerado**
Otras soluciones.

**Contexto adicional**
Cualquier otra información.
```

#### .github/PULL_REQUEST_TEMPLATE.md:
```markdown
## Descripción
Breve descripción de los cambios.

## Tipo de cambio
- [ ] Bug fix
- [ ] Nueva feature
- [ ] Breaking change
- [ ] Documentación

## Checklist
- [ ] Tests pasan
- [ ] Código sigue estilo del proyecto
- [ ] Documentación actualizada
- [ ] CHANGELOG.md actualizado
```

- [ ] Crear templates
- [ ] Verificar que aparecen en GitHub

**Estimado**: 3-4 horas

---

## Fase 7: Publicación en PyPI (2-3 horas)

### 7.1 Preparación Pre-lanzamiento

- [ ] Verificar que todos los tests pasan: `pytest`
- [ ] Verificar cobertura > 80%: `pytest --cov`
- [ ] Verificar linting: `black --check`, `flake8`, `mypy`
- [ ] Actualizar `__version__.py` a 0.1.0
- [ ] Actualizar CHANGELOG.md con versión inicial
- [ ] Actualizar README.md (quitar notas de "en desarrollo")
- [ ] Verificar que no hay secrets en el código
- [ ] Verificar LICENSE está incluido
- [ ] Verificar MANIFEST.in incluye todo necesario

### 7.2 Testing en Test PyPI

- [ ] Crear cuenta en https://test.pypi.org/
- [ ] Generar API token en Test PyPI
- [ ] Configurar secreto en GitHub: `TEST_PYPI_API_TOKEN`
- [ ] Build del paquete:
  ```bash
  python -m build
  ```
- [ ] Verificar distribución:
  ```bash
  twine check dist/*
  ```
- [ ] Subir a Test PyPI:
  ```bash
  twine upload --repository testpypi dist/*
  ```
- [ ] Instalar desde Test PyPI:
  ```bash
  pip install --index-url https://test.pypi.org/simple/ --no-deps socialseed-e2e
  ```
- [ ] Probar funcionalidad:
  ```bash
  e2e --version
  e2e --help
  e2e init /tmp/test-project
  ```
- [ ] Si hay errores, corregir y repetir

### 7.3 Publicación en PyPI (Producción)

- [ ] Crear cuenta en https://pypi.org/
- [ ] Generar API token en PyPI
- [ ] Configurar secreto en GitHub: `PYPI_API_TOKEN`
- [ ] Crear tag git:
  ```bash
  git tag -a v0.1.0 -m "Initial release - v0.1.0"
  git push origin v0.1.0
  ```
- [ ] Verificar que GitHub Action publica automáticamente
- [ ] Verificar en https://pypi.org/project/socialseed-e2e/
- [ ] Verificar instalación desde PyPI:
  ```bash
  pip install socialseed-e2e
  e2e --version
  ```
- [ ] 🎉 Celebrar!

### 7.4 Post-lanzamiento

- [ ] Crear release en GitHub con notas
- [ ] Anunciar en redes (Twitter, LinkedIn, etc.)
- [ ] Enviar a Python Weekly, Reddit r/Python, Hacker News
- [ ] Responder issues rápidamente (24-48h)
- [ ] Agregar badge de PyPI al README

**Estimado**: 2-3 horas

---

## Fase 8: Mantenimiento y Mejoras (Contínuo)

### 8.1 Inmediato Post-lanzamiento (Semana 1)
- [ ] Monitorear issues y responder rápido
- [ ] Fixear bugs reportados urgentemente
- [ ] Recopilar feedback de usuarios
- [ ] Agregar más ejemplos si se solicitan

### 8.2 Mejoras Planificadas (v0.2.0+)

#### v0.2.0 - Estabilidad y Features Core
- [ ] Soporte para gRPC
- [ ] Reportes HTML interactivos
- [ ] Parallel test execution
- [ ] Mejor manejo de autenticación (OAuth2, API Keys)

#### v0.3.0 - Developer Experience
- [ ] Plugin system
- [ ] Integración con Docker Compose
- [ ] Visual regression testing (screenshots)
- [ ] Mejor CLI con TUI (Text User Interface)

#### v0.4.0 - Escalabilidad
- [ ] Soporte para WebSockets
- [ ] Soporte para GraphQL
- [ ] Distributed testing
- [ ] Performance testing básico

### 8.3 Marketing y Comunidad
- [ ] Crear Twitter/X para el proyecto
- [ ] Escribir blog post de lanzamiento
- [ ] Crear video tutorial (YouTube)
- [ ] Participar en conferencias Python
- [ ] Roadmap público en GitHub Projects

**Estimado**: Contínuo

---

## Estimación de Tiempo Total

| Fase | Tiempo Estimado | Prioridad |
|------|----------------|-----------|
| Fase 1: Setup Repo | 2-3 horas | 🔴 Alta |
| Fase 2: Config Paquete | 2-3 horas | 🔴 Alta |
| Fase 3: Refactor Core | 4-5 horas | 🔴 Alta |
| Fase 4: Tests | 4-5 horas | 🔴 Alta |
| Fase 5: Documentación | 5-6 horas | 🟡 Media |
| Fase 6: CI/CD | 3-4 horas | 🟡 Media |
| Fase 7: Publicación | 2-3 horas | 🔴 Alta |
| **TOTAL Mínimo Viable** | **22-29 horas** | |
| Fase 8: Mantenimiento | Contínuo | 🟢 Baja |

---

## Checklist Final Pre-lanzamiento

### Calidad de Código ✅
- [ ] Todos los tests pasan
- [ ] Cobertura > 80%
- [ ] No hay errores de mypy
- [ ] Código formateado con black
- [ ] Docstrings en todas las funciones públicas

### Paquete ✅
- [ ] Instala correctamente desde Test PyPI
- [ ] CLI funciona: `e2e --help`
- [ ] `e2e init` crea archivos correctamente
- [ ] `e2e run` ejecuta tests de ejemplo
- [ ] No incluye archivos __pycache__

### Documentación ✅
- [ ] README.md completo y atractivo
- [ ] Ejemplo "Hello World" funciona
- [ ] Guía de instalación clara
- [ ] Changelog actualizado
- [ ] Guía de contribución

### Seguridad ✅
- [ ] No hay secrets en el código
- [ ] No hay credenciales hardcodeadas
- [ ] .gitignore excluye archivos sensibles
- [ ] LICENSE claramente definido

---

## Recursos Útiles

### Documentación Oficial
- [Python Packaging Guide](https://packaging.python.org/)
- [Setuptools Documentation](https://setuptools.pypa.io/)
- [Playwright Python](https://playwright.dev/python/)

### Ejemplos de Paquetes Similares
- [pytest](https://github.com/pytest-dev/pytest) - Estructura de plugins
- [click](https://github.com/pallets/click) - CLI framework
- [requests](https://github.com/psf/requests) - Documentación excelente
- [black](https://github.com/psf/black) - Tooling profesional

### Herramientas
- [Black](https://black.readthedocs.io/) - Formateador
- [Mypy](https://mypy.readthedocs.io/) - Type checker
- [Pre-commit](https://pre-commit.com/) - Git hooks
- [Sphinx](https://www.sphinx-doc.org/) - Documentación

---

## Notas y Tips

1. **Empieza simple**: Lanza v0.1.0 con lo básico, itera rápido
2. **Test PyPI primero**: Siempre prueba en Test PyPI antes de producción
3. **Documentación > Código**: Mejor documentación que más features
4. **Responder rápido**: Issues respondidos en 24h crean comunidad
5. **Semantic Versioning**: Usa semver.org (MAJOR.MINOR.PATCH)
6. **Changelog**: Mantén CHANGELOG.md actualizado desde el inicio
7. **Tests primero**: Escribe tests para cada nueva feature

---

## Issues Relacionadas

- #1: Setup inicial del repositorio
- #2: Implementar CLI con click
- #3: Sistema de templates
- #4: Tests unitarios core
- #5: Tests de integración
- #6: Documentación README y docs/
- #7: CI/CD GitHub Actions
- #8: Publicación PyPI

---

Status: 📋 Planificación Completa - Listo para Implementación
Prioridad: 🔴 Alta
Asignado: @daironpf
Fecha de Inicio: 2026-01-30
Fecha Estimada Lanzamiento v0.1.0: 2026-02-07 (1 semana de trabajo)
