#!/usr/bin/env python3
"""CLI module for socialseed-e2e framework.

This module provides the command-line interface for the E2E testing framework,
enabling developers and AI agents to create, manage, and run API tests.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from . import __version__
from .core.config_loader import ApiConfigLoader, ConfigError

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="socialseed-e2e")
def cli():
    """socialseed-e2e: Framework E2E para APIs REST.
    
    Un framework agnóstico de servicios para testing End-to-End de APIs REST,
    diseñado para desarrolladores y agentes de IA.
    """
    pass


@cli.command()
@click.argument("directory", default=".", required=False)
@click.option("--force", is_flag=True, help="Sobrescribir archivos existentes")
def init(directory: str, force: bool):
    """Inicializa un nuevo proyecto E2E.
    
    Crea la estructura de directorios y archivos de configuración inicial.
    
    Args:
        directory: Directorio donde crear el proyecto (default: directorio actual)
        force: Si es True, sobrescribe archivos existentes
    """
    target_path = Path(directory).resolve()
    
    console.print(f"\n🌱 [bold green]Inicializando proyecto E2E en:[/bold green] {target_path}\n")
    
    # Crear estructura de directorios
    dirs_to_create = [
        target_path / "services",
        target_path / "tests",
        target_path / ".github" / "workflows",
    ]
    
    created_dirs = []
    for dir_path in dirs_to_create:
        if not dir_path.exists():
            dir_path.mkdir(parents=True)
            created_dirs.append(dir_path.name if dir_path.parent == target_path else str(dir_path.relative_to(target_path)))
            console.print(f"  [green]✓[/green] Creado: {dir_path.relative_to(target_path)}")
        else:
            console.print(f"  [yellow]⚠[/yellow] Ya existe: {dir_path.relative_to(target_path)}")
    
    # Crear archivo de configuración
    config_path = target_path / "e2e.conf"
    if not config_path.exists() or force:
        config_content = """# Configuración E2E para socialseed-e2e
# Documentación: https://github.com/daironpf/socialseed-e2e

general:
  environment: dev
  timeout: 30000
  user_agent: "socialseed-e2e/1.0"
  verbose: true

# Configuración de servicios
# Descomenta y modifica según tus necesidades
# services:
#   myapi:
#     name: my-api
#     base_url: http://localhost:8080
#     health_endpoint: /health
#     timeout: 5000
#     auto_start: false
#     required: true
"""
        config_path.write_text(config_content)
        console.print(f"  [green]✓[/green] Creado: e2e.conf")
    else:
        console.print(f"  [yellow]⚠[/yellow] Ya existe: e2e.conf (usa --force para sobrescribir)")
    
    # Crear .gitignore
    gitignore_path = target_path / ".gitignore"
    if not gitignore_path.exists() or force:
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
*.egg-info/
dist/
build/

# Virtual environments
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# E2E Framework
test-results/
.coverage
htmlcov/
"""
        gitignore_path.write_text(gitignore_content)
        console.print(f"  [green]✓[/green] Creado: .gitignore")
    else:
        console.print(f"  [yellow]⚠[/yellow] Ya existe: .gitignore")
    
    # Mostrar mensaje de éxito
    console.print(f"\n[bold green]✅ Proyecto inicializado correctamente![/bold green]\n")
    
    console.print(Panel(
        "[bold]Próximos pasos:[/bold]\n\n"
        "1. Edita [cyan]e2e.conf[/cyan] para configurar tu API\n"
        "2. Ejecuta: [cyan]e2e new-service <nombre>[/cyan]\n"
        "3. Ejecuta: [cyan]e2e new-test <nombre> --service <svc>[/cyan]\n"
        "4. Ejecuta: [cyan]e2e run[/cyan] para correr tests",
        title="🚀 Empezar",
        border_style="green"
    ))


@cli.command()
@click.argument("name")
@click.option("--base-url", default="http://localhost:8080", help="URL base del servicio")
@click.option("--health-endpoint", default="/health", help="Endpoint de health check")
def new_service(name: str, base_url: str, health_endpoint: str):
    """Crea un nuevo servicio con scaffolding.
    
    Args:
        name: Nombre del servicio (ej: users-api)
        base_url: URL base del servicio
        health_endpoint: Endpoint para health checks
    """
    console.print(f"\n🔧 [bold blue]Creando servicio:[/bold blue] {name}\n")
    
    # Verificar que estamos en un proyecto E2E
    if not _is_e2e_project():
        console.print("[red]❌ Error:[/red] No se encontró e2e.conf. ¿Estás en un proyecto E2E?")
        console.print("   Ejecuta: [cyan]e2e init[/cyan] primero")
        sys.exit(1)
    
    # Crear estructura del servicio
    service_path = Path("services") / name
    modules_path = service_path / "modules"
    
    try:
        service_path.mkdir(parents=True)
        modules_path.mkdir()
        console.print(f"  [green]✓[/green] Creado: services/{name}/")
        console.print(f"  [green]✓[/green] Creado: services/{name}/modules/")
    except FileExistsError:
        console.print(f"  [yellow]⚠[/yellow] El servicio '{name}' ya existe")
        if not click.confirm("¿Deseas continuar y sobrescribir archivos?"):
            return
    
    # Crear __init__.py
    _create_file(service_path / "__init__.py", f'"""Servicio {name}."""\n')
    _create_file(modules_path / "__init__.py", f'"""Módulos de test para {name}."""\n')
    console.print(f"  [green]✓[/green] Creado: services/{name}/__init__.py")
    console.print(f"  [green]✓[/green] Creado: services/{name}/modules/__init__.py")
    
    # Crear página del servicio
    class_name = _to_class_name(name)
    page_content = f'''"""Página de servicio para {name}.

Este módulo define la clase de página para interactuar con el servicio {name}.
"""

from typing import Optional
from playwright.sync_api import APIResponse

from socialseed_e2e.core.base_page import BasePage


class {class_name}Page(BasePage):
    """Página de servicio para {name}.
    
    Gestiona el estado compartido entre módulos de test.
    
    Attributes:
        current_entity: Entidad actualmente seleccionada
        auth_token: Token de autenticación
    """
    
    def __init__(self, playwright=None, base_url: Optional[str] = None):
        """Inicializa la página de servicio.
        
        Args:
            playwright: Instancia de Playwright
            base_url: URL base del servicio (opcional)
        """
        # Cargar configuración desde e2e.conf
        from .config import get_{name.replace("-", "_")}_config
        config = get_{name.replace("-", "_")}_config()
        
        url = base_url or config.base_url
        super().__init__(url, playwright, default_headers=config.default_headers)
        
        # Estado compartido entre módulos
        self.current_entity: Optional[dict] = None
        self.auth_token: Optional[str] = None
    
    def get_entity(self, entity_id: str) -> APIResponse:
        """Obtener entidad por ID.
        
        Args:
            entity_id: ID de la entidad
            
        Returns:
            APIResponse: Respuesta HTTP
        """
        return self.get(f"/entities/{{entity_id}}")
'''
    _create_file(service_path / f"{name.replace('-', '_')}_page.py", page_content)
    console.print(f"  [green]✓[/green] Creado: services/{name}/{name.replace('-', '_')}_page.py")
    
    # Crear archivo de configuración
    config_content = f'''"""Configuración del servicio {name}.

Este módulo maneja la configuración específica del servicio.
"""

from socialseed_e2e.core.config_loader import ApiConfigLoader
from socialseed_e2e.core.models import ServiceConfig


def get_{name.replace("-", "_")}_config() -> ServiceConfig:
    """Obtiene la configuración del servicio {name}.
    
    Returns:
        ServiceConfig: Configuración del servicio
    """
    loader = ApiConfigLoader()
    config = loader.load()
    return config.services["{name}"]
'''
    _create_file(service_path / "config.py", config_content)
    console.print(f"  [green]✓[/green] Creado: services/{name}/config.py")
    
    # Crear data_schema.py
    schema_content = f'''"""Esquemas de datos para {name}.

Define DTOs (Data Transfer Objects) y constantes del servicio.
"""

from pydantic import BaseModel
from typing import Optional, List


class {class_name}DTO(BaseModel):
    """DTO para entidades de {name}.
    
    Attributes:
        id: Identificador único
        name: Nombre de la entidad
        created_at: Fecha de creación (ISO format)
    """
    id: str
    name: str
    created_at: str


# Endpoints comunes
GET_ENDPOINT = "/{{id}}"
POST_ENDPOINT = "/create"
PUT_ENDPOINT = "/{{id}}"
DELETE_ENDPOINT = "/{{id}}"
LIST_ENDPOINT = "/list"
'''
    _create_file(service_path / "data_schema.py", schema_content)
    console.print(f"  [green]✓[/green] Creado: services/{name}/data_schema.py")
    
    # Actualizar e2e.conf
    _update_e2e_conf(name, base_url, health_endpoint)
    
    console.print(f"\n[bold green]✅ Servicio '{name}' creado correctamente![/bold green]\n")
    
    console.print(Panel(
        f"[bold]Próximos pasos:[/bold]\n\n"
        f"1. Edita [cyan]services/{name}/data_schema.py[/cyan] para definir tus DTOs\n"
        f"2. Ejecuta: [cyan]e2e new-test <nombre> --service {name}[/cyan]\n"
        f"3. Ejecuta: [cyan]e2e run --service {name}[/cyan]",
        title="🚀 Continuar",
        border_style="blue"
    ))


@cli.command()
@click.argument("name")
@click.option("--service", "-s", required=True, help="Nombre del servicio")
@click.option("--description", "-d", default="", help="Descripción del test")
def new_test(name: str, service: str, description: str):
    """Crea un nuevo módulo de test.
    
    Args:
        name: Nombre del test (ej: login, create-user)
        service: Servicio al que pertenece el test
        description: Descripción opcional del test
    """
    console.print(f"\n📝 [bold cyan]Creando test:[/bold cyan] {name}\n")
    
    # Verificar que estamos en un proyecto E2E
    if not _is_e2e_project():
        console.print("[red]❌ Error:[/red] No se encontró e2e.conf. ¿Estás en un proyecto E2E?")
        sys.exit(1)
    
    # Verificar que el servicio existe
    service_path = Path("services") / service
    modules_path = service_path / "modules"
    
    if not service_path.exists():
        console.print(f"[red]❌ Error:[/red] El servicio '{service}' no existe.")
        console.print(f"   Crea el servicio primero: [cyan]e2e new-service {service}[/cyan]")
        sys.exit(1)
    
    if not modules_path.exists():
        modules_path.mkdir(parents=True)
    
    # Encontrar siguiente número disponible
    existing_tests = sorted(modules_path.glob("[0-9][0-9]_*.py"))
    if existing_tests:
        last_num = int(existing_tests[-1].name[:2])
        next_num = last_num + 1
    else:
        next_num = 1
    
    test_filename = f"{next_num:02d}_{name}_flow.py"
    test_path = modules_path / test_filename
    
    # Verificar si ya existe
    if test_path.exists():
        console.print(f"[yellow]⚠[/yellow] El test '{name}' ya existe.")
        if not click.confirm("¿Deseas sobrescribirlo?"):
            return
    
    # Crear contenido del test
    class_name = _to_class_name(service)
    service_var = service.replace("-", "_")
    desc = description or f"Test flow for {name}"
    
    test_content = f'''"""{desc}.

Módulo de test para el servicio {service}.
"""

from playwright.sync_api import APIResponse
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..{service.replace("-", "_")}_page import {class_name}Page


def run({service_var}: "{class_name}Page") -> APIResponse:
    """{desc}.
    
    Este test verifica el flujo de {name} en el servicio {service}.
    
    Args:
        {service_var}: Instancia de {class_name}Page
        
    Returns:
        APIResponse: Respuesta HTTP
        
    Raises:
        AssertionError: Si el test falla
    """
    print(f"🧪 Running {name} test...")
    
    # TODO: Implementar lógica del test
    # Ejemplo:
    # response = {service_var}.get("/endpoint")
    # 
    # if response.ok:
    #     print("✓ Test passed")
    # else:
    #     print(f"✗ Failed: {{response.status}}")
    #     raise AssertionError(f"Expected 200, got {{response.status}}")
    # 
    # return response
    
    # Placeholder - reemplazar con lógica real
    print("⚠ Test not implemented yet")
    return None
'''
    
    _create_file(test_path, test_content)
    console.print(f"  [green]✓[/green] Creado: services/{service}/modules/{test_filename}")
    
    console.print(f"\n[bold green]✅ Test '{name}' creado correctamente![/bold green]\n")
    
    console.print(Panel(
        f"[bold]Próximos pasos:[/bold]\n\n"
        f"1. Edita [cyan]services/{service}/modules/{test_filename}[/cyan]\n"
        f"2. Implementa la lógica del test\n"
        f"3. Ejecuta: [cyan]e2e run --service {service}[/cyan]",
        title="🚀 Implementar",
        border_style="cyan"
    ))


@cli.command()
@click.option("--service", "-s", help="Filtrar por servicio específico")
@click.option("--module", "-m", help="Filtrar por módulo específico")
@click.option("--verbose", "-v", is_flag=True, help="Modo verbose")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text", help="Formato de salida")
def run(service: Optional[str], module: Optional[str], verbose: bool, output: str):
    """Ejecuta los tests E2E.
    
    Descubre y ejecuta automáticamente todos los tests disponibles.
    
    Args:
        service: Si se especifica, solo ejecuta tests de este servicio
        module: Si se especifica, solo ejecuta este módulo de test
        verbose: Si es True, muestra información detallada
        output: Formato de salida (text o json)
    """
    from .core.test_orchestrator import TestOrchestrator
    
    console.print(f"\n🚀 [bold green]socialseed-e2e v{__version__}[/bold green]")
    console.print("═" * 50)
    console.print()
    
    # Verificar configuración
    try:
        loader = ApiConfigLoader()
        config = loader.load()
        console.print(f"📋 [cyan]Configuración:[/cyan] {loader._config_path}")
        console.print(f"🌍 [cyan]Environment:[/cyan] {config.environment}")
        console.print()
    except ConfigError as e:
        console.print(f"[red]❌ Error de configuración:[/red] {e}")
        console.print("   Ejecuta: [cyan]e2e init[/cyan] para crear un proyecto")
        sys.exit(1)
    
    # TODO: Implementar ejecución real de tests
    # Por ahora, mostramos información de descubrimiento
    
    if service:
        console.print(f"🔍 [yellow]Filtrando por servicio:[/yellow] {service}")
    if module:
        console.print(f"🔍 [yellow]Filtrando por módulo:[/yellow] {module}")
    if verbose:
        console.print(f"📢 [yellow]Modo verbose activado[/yellow]")
    
    console.print()
    console.print("[yellow]⚠ Nota:[/yellow] La ejecución de tests aún no está implementada")
    console.print("   Este es un placeholder para la versión 0.1.0")
    console.print()
    
    # Mostrar tabla de servicios encontrados
    services_path = Path("services")
    if services_path.exists():
        services = [d.name for d in services_path.iterdir() if d.is_dir() and not d.name.startswith("__")]
        
        if services:
            table = Table(title="Servicios Encontrados")
            table.add_column("Servicio", style="cyan")
            table.add_column("Tests", style="green")
            table.add_column("Estado", style="yellow")
            
            for svc in services:
                modules_path = services_path / svc / "modules"
                if modules_path.exists():
                    test_count = len(list(modules_path.glob("[0-9][0-9]_*.py")))
                    table.add_row(svc, str(test_count), "Ready" if test_count > 0 else "Empty")
                else:
                    table.add_row(svc, "0", "No modules")
            
            console.print(table)
        else:
            console.print("[yellow]⚠ No se encontraron servicios[/yellow]")
            console.print("   Crea uno con: [cyan]e2e new-service <nombre>[/cyan]")
    else:
        console.print("[red]❌ No se encontró el directorio 'services/'[/red]")
    
    console.print()
    console.print("═" * 50)
    console.print("[bold]Para implementar la ejecución real, contribuye en:[/bold]")
    console.print("[cyan]https://github.com/daironpf/socialseed-e2e[/cyan]")


@cli.command()
def doctor():
    """Verifica la instalación y dependencias.
    
    Comprueba que todo esté correctamente configurado para usar el framework.
    """
    console.print("\n🏥 [bold green]socialseed-e2e Doctor[/bold green]\n")
    
    checks = []
    
    # Verificar Python
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    checks.append(("Python", python_version, sys.version_info >= (3, 9)))
    
    # Verificar Playwright
    try:
        from importlib.metadata import version
        pw_version = version("playwright")
        checks.append(("Playwright", pw_version, True))
    except Exception:
        checks.append(("Playwright", "No instalado", False))
    
    # Verificar browsers de Playwright
    try:
        result = subprocess.run(
            ["playwright", "install", "--help"],
            capture_output=True,
            text=True,
            timeout=5
        )
        browsers_installed = result.returncode == 0
        checks.append(("Playwright CLI", "Disponible", browsers_installed))
    except (subprocess.TimeoutExpired, FileNotFoundError):
        checks.append(("Playwright CLI", "No disponible", False))
    
    # Verificar Pydantic
    try:
        import pydantic
        checks.append(("Pydantic", pydantic.__version__, True))
    except ImportError:
        checks.append(("Pydantic", "No instalado", False))
    
    # Verificar e2e.conf
    if _is_e2e_project():
        checks.append(("Configuración", "e2e.conf encontrado", True))
    else:
        checks.append(("Configuración", "e2e.conf no encontrado", False))
    
    # Verificar estructura de directorios
    services_exists = Path("services").exists()
    tests_exists = Path("tests").exists()
    checks.append(("Directorio services/", "OK" if services_exists else "No encontrado", services_exists))
    checks.append(("Directorio tests/", "OK" if tests_exists else "No encontrado", tests_exists))
    
    # Mostrar resultados
    table = Table(title="Verificación del Sistema")
    table.add_column("Componente", style="cyan")
    table.add_column("Versión/Estado", style="white")
    table.add_column("Estado", style="bold")
    
    all_ok = True
    for name, value, ok in checks:
        status = "[green]✓[/green]" if ok else "[red]✗[/red]"
        table.add_row(name, value, status)
        if not ok:
            all_ok = False
    
    console.print(table)
    
    console.print()
    if all_ok:
        console.print("[bold green]✅ Todo está configurado correctamente![/bold green]")
    else:
        console.print("[bold yellow]⚠ Se encontraron algunos problemas[/bold yellow]")
        console.print()
        console.print("[cyan]Soluciones sugeridas:[/cyan]")
        
        if not any(name == "Playwright" and ok for name, _, ok in checks):
            console.print("  • Instala Playwright: [white]pip install playwright[/white]")
        if not any(name == "Playwright CLI" and ok for name, _, ok in checks):
            console.print("  • Instala browsers: [white]playwright install chromium[/white]")
        if not any(name == "Pydantic" and ok for name, _, ok in checks):
            console.print("  • Instala dependencias: [white]pip install socialseed-e2e[/white]")
        if not _is_e2e_project():
            console.print("  • Inicializa proyecto: [white]e2e init[/white]")
    
    console.print()


@cli.command()
def config():
    """Muestra y valida la configuración actual.
    
    Muestra la configuración cargada desde e2e.conf y valida su sintaxis.
    """
    console.print("\n⚙️  [bold blue]Configuración E2E[/bold blue]\n")
    
    try:
        loader = ApiConfigLoader()
        config = loader.load()
        
        console.print(f"📋 [cyan]Configuración:[/cyan] {loader._config_path}")
        console.print(f"🌍 [cyan]Environment:[/cyan] {config.environment}")
        console.print(f"[cyan]Timeout:[/cyan] {config.timeout}ms")
        console.print(f"[cyan]Verbose:[/cyan] {config.verbose}")
        console.print()
        
        if config.services:
            table = Table(title="Servicios Configurados")
            table.add_column("Nombre", style="cyan")
            table.add_column("Base URL", style="green")
            table.add_column("Health", style="yellow")
            table.add_column("Requerido", style="white")
            
            for name, svc in config.services.items():
                table.add_row(
                    name,
                    svc.base_url,
                    svc.health_endpoint or "N/A",
                    "✓" if svc.required else "✗"
                )
            
            console.print(table)
        else:
            console.print("[yellow]⚠ No hay servicios configurados[/yellow]")
            console.print("   Usa: [cyan]e2e new-service <nombre>[/cyan]")
        
        console.print()
        console.print("[bold green]✅ Configuración válida[/bold green]")
        
    except ConfigError as e:
        console.print(f"[red]❌ Error de configuración:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]❌ Error inesperado:[/red] {e}")
        sys.exit(1)


# Funciones auxiliares

def _is_e2e_project() -> bool:
    """Verifica si el directorio actual es un proyecto E2E."""
    return Path("e2e.conf").exists()


def _to_class_name(name: str) -> str:
    """Convierte un nombre de servicio a nombre de clase.
    
    Args:
        name: Nombre del servicio (ej: users-api)
        
    Returns:
        str: Nombre de clase (ej: UsersApi)
    """
    return "".join(word.capitalize() for word in name.replace("-", "_").split("_"))


def _create_file(path: Path, content: str) -> None:
    """Crea un archivo con el contenido especificado.
    
    Args:
        path: Ruta del archivo
        content: Contenido a escribir
    """
    path.write_text(content)


def _update_e2e_conf(service_name: str, base_url: str, health_endpoint: str) -> None:
    """Actualiza e2e.conf para incluir el nuevo servicio.
    
    Args:
        service_name: Nombre del servicio
        base_url: URL base
        health_endpoint: Endpoint de health check
    """
    config_path = Path("e2e.conf")
    
    if not config_path.exists():
        return
    
    content = config_path.read_text()
    
    # Verificar si ya existe la sección de servicios
    if "services:" not in content:
        content += "\nservices:\n"
    
    # Agregar configuración del servicio
    service_config = f'''  {service_name}:
    name: {service_name}-service
    base_url: {base_url}
    health_endpoint: {health_endpoint}
    timeout: 5000
    auto_start: false
    required: true
'''
    
    content += service_config
    config_path.write_text(content)
    console.print(f"  [green]✓[/green] Actualizado: e2e.conf")


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
