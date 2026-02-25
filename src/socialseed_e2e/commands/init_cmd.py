"""Init command for socialseed-e2e.

This module provides the init command functionality.
"""

from pathlib import Path

import click
from rich.console import Console

console = Console()


class InitManager:
    """Handles project initialization (Single Responsibility)."""

    DEFAULT_IGNORE = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
.venv/
ENV/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Testing
.pytest_cache/
.coverage
htmlcov/
.e2e/

# OS
.DS_Store
Thumbs.db

# socialseed-e2e
e2e_reports/
"""

    DEFAULT_REQUIREMENTS = """# socialseed-e2e requirements
socialseed-e2e>=0.1.0
playwright>=1.40.0
pydantic>=2.0.0
email-validator>=2.0.0
pyyaml>=6.0
rich>=13.0.0
jinja2>=3.1.0
click>=8.0.0

# Optional: Flask for demo APIs
flask>=2.0.0

# Optional: For vector embeddings and RAG
numpy>=1.21.0
scikit-learn>=1.0.0
sentence-transformers>=2.2.0
"""

    AGENT_DOCS = """# AI Agent Documentation

This directory contains context for AI agents working on this project.

## Quick Start for AI Agents

1. **Verify service is running**: Check if the API is accessible
   ```bash
   curl http://localhost:8085/actuator/health
   ```

2. **Configure service URL**: Edit `e2e.conf`
   ```yaml
   services:
     auth-service:
       base_url: http://localhost:8085
       health_endpoint: /actuator/health
   ```

3. **Create service page**: `e2e new-service <service-name>`
   - This creates: services/<name>/<name>_page.py
   - And: services/<name>/data_schema.py
   - And: services/<name>/modules/

4. **Add endpoints to data_schema.py**:
   ```python
   ENDPOINTS = {
       "login": "/auth/login",
       "register": "/auth/register",
       "get_user": "/auth/getUserById/{id}",
   }
   ```

5. **Implement methods in <name>_page.py**:
   ```python
   def login(self, email: str, password: str) -> APIResponse:
       return self.post("/auth/login", data={"email": email, "password": password})
   ```

6. **Create test**: `e2e new-test <test-name> --service <service-name>`

7. **Run tests**: `e2e run --service <service-name>`

## Project Structure

```
project/
├── services/           # Service pages and tests
│   └── auth-service/
│       ├── auth_service_page.py   # Page class (extends BasePage)
│       ├── data_schema.py         # DTOs, endpoints, constants
│       ├── config.py              # Service configuration
│       └── modules/                # Test modules
│           └── 01_login.py        # Test files (run function)
├── tests/              # Additional test files
├── demos/              # Demo APIs (optional)
├── .e2e/              # E2E framework data
├── e2e.conf           # E2E configuration
└── requirements.txt   # Dependencies
```

## Key Commands

- `e2e init` - Initialize a new E2E project
- `e2e new-service <name>` - Create new service structure
- `e2e new-test <name> --service <service>` - Create test module
- `e2e run` - Run all tests
- `e2e run --service <name>` - Run specific service tests
- `e2e lint` - Validate test files
- `e2e doctor` - Check installation
- `e2e manifest <path>` - Generate project manifest
- `e2e deep-scan <path>` - Auto-detect tech stack
- `e2e observe` - Detect services and ports

## Configuration (e2e.conf)

```yaml
general:
  environment: dev
  timeout: 30000
  verbose: true

services:
  auth-service:
    base_url: http://localhost:8085
    health_endpoint: /actuator/health
    timeout: 30000
```

## Common Patterns

### Service Page (services/<name>/<name>_page.py)
```python
from socialseed_e2e.core.base_page import BasePage
from .data_schema import ENDPOINTS

class AuthServicePage(BasePage):
    def __init__(self, base_url: str, **kwargs):
        super().__init__(base_url=base_url, **kwargs)
        self.access_token = None

    def login(self, email: str, password: str) -> APIResponse:
        return self.post(ENDPOINTS["login"], data={"email": email, "password": password})
```

### Test Module (services/<name>/modules/01_login.py)
```python
from playwright.sync_api import APIResponse
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.auth_service.auth_service_page import AuthServicePage

def run(auth_service: 'AuthServicePage') -> APIResponse:
    response = auth_service.login("test@example.com", "password123")
    assert response.ok, f"Login failed: {response.text()}"
    return response
```

### DTO with camelCase (data_schema.py)
```python
from pydantic import BaseModel, Field

class LoginRequestDTO(BaseModel):
    model_config = {"populate_by_name": True}
    
    email: str
    password: str = Field(..., alias="password")

# Usage: data.model_dump(by_alias=True)
```

## Framework Version
See: https://github.com/daironpf/socialseed-e2e
"""

    def __init__(self, target_path: Path, force: bool = False, demo: bool = False):
        self.target_path = target_path
        self.force = force
        self.demo = demo

    def initialize(self) -> None:
        """Initialize the project."""
        self._create_directories()
        self._create_e2e_conf()
        self._create_gitignore()
        self._create_requirements()
        self._create_agent_docs()

    def _create_directories(self) -> None:
        """Create directory structure."""
        dirs = [
            self.target_path / "services",
            self.target_path / "tests",
            self.target_path / ".github" / "workflows",
        ]

        for dir_path in dirs:
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                console.print(
                    f"  [green]✓[/green] Created: {dir_path.relative_to(self.target_path)}"
                )
            else:
                console.print(
                    f"  [yellow]⚠[/yellow] Already exists: {dir_path.relative_to(self.target_path)}"
                )

    def _create_e2e_conf(self) -> None:
        """Create e2e.conf file."""
        config_path = self.target_path / "e2e.conf"

        if config_path.exists() and not self.force:
            console.print("  [yellow]⚠[/yellow] Already exists: e2e.conf")
            return

        config_content = """# SocialSeed E2E Configuration
# Documentation: https://github.com/daironpf/socialseed-e2e

general:
  environment: dev
  timeout: 30000
  verbose: true
  user_agent: socialseed-e2e/1.0
  project_name: my-project

services: {}
"""
        config_path.write_text(config_content)
        console.print("  [green]✓[/green] Created: e2e.conf")

    def _create_gitignore(self) -> None:
        """Create .gitignore file."""
        gitignore_path = self.target_path / ".gitignore"

        if gitignore_path.exists() and not self.force:
            console.print("  [yellow]⚠[/yellow] Already exists: .gitignore")
            return

        gitignore_path.write_text(self.DEFAULT_IGNORE)
        console.print("  [green]✓[/green] Created: .gitignore")

    def _create_requirements(self) -> None:
        """Create requirements.txt file."""
        req_path = self.target_path / "requirements.txt"

        if req_path.exists() and not self.force:
            console.print("  [yellow]⚠[/yellow] Already exists: requirements.txt")
            return

        req_path.write_text(self.DEFAULT_REQUIREMENTS)
        console.print("  [green]✓[/green] Created: requirements.txt")

    def _create_agent_docs(self, source_path: str | None = None) -> None:
        """Create .agent directory with AI documentation.

        Args:
            source_path: Optional path to source code for auto-scanning
        """
        agent_dir = self.target_path / ".agent"

        if not agent_dir.exists():
            agent_dir.mkdir(parents=True, exist_ok=True)
            console.print("  [green]✓[/green] Created: .agent/")

        readme_path = agent_dir / "README.md"
        if not readme_path.exists() or self.force:
            readme_path.write_text(self.AGENT_DOCS)
            console.print("  [green]✓[/green] Created: .agent/README.md")

        # Auto-scan source code if provided
        if source_path is not None and Path(source_path).exists():
            self._generate_agent_docs_from_scan(agent_dir, source_path)

    def _generate_agent_docs_from_scan(self, agent_dir: Path, source_path: str) -> None:
        """Generate documentation files by scanning source code."""
        console.print("\n[cyan]🔍 Scanning source code for documentation...[/cyan]\n")

        try:
            from socialseed_e2e.scanner.endpoint_scanner import (
                generate_endpoints_doc,
                EndpointScanner,
            )
            from socialseed_e2e.scanner.schema_scanner import (
                generate_schemas_doc,
                SchemaScanner,
            )
            from socialseed_e2e.scanner.auth_flow_generator import generate_auth_flows
            from socialseed_e2e.scanner.test_pattern_generator import generate_test_patterns
            from socialseed_e2e.scanner.error_code_scanner import generate_error_codes_doc

            # Scan first to get endpoints and schemas
            ep_scanner = EndpointScanner(source_path)
            endpoints = ep_scanner.scan()
            schema_scanner = SchemaScanner(source_path)
            schemas = schema_scanner.scan()

            # Generate ENDPOINTS.md
            endpoints_md = generate_endpoints_doc(source_path)
            endpoints_path = agent_dir / "ENDPOINTS.md"
            endpoints_path.write_text(endpoints_md)
            console.print(f"  [green]✓[/green] Created: .agent/ENDPOINTS.md")

            # Generate DATA_SCHEMAS.md
            schemas_md = generate_schemas_doc(source_path)
            schemas_path = agent_dir / "DATA_SCHEMAS.md"
            schemas_path.write_text(schemas_md)
            console.print(f"  [green]✓[/green] Created: .agent/DATA_SCHEMAS.md")

            # Generate ERROR_CODES.md
            error_md = generate_error_codes_doc(source_path)
            error_path = agent_dir / "ERROR_CODES.md"
            error_path.write_text(error_md)
            console.print(f"  [green]✓[/green] Created: .agent/ERROR_CODES.md")

            # Generate AUTH_FLOWS.md
            auth_md = generate_auth_flows(endpoints, schemas)
            auth_path = agent_dir / "AUTH_FLOWS.md"
            auth_path.write_text(auth_md)
            console.print(f"  [green]✓[/green] Created: .agent/AUTH_FLOWS.md")

            # Generate TEST_PATTERNS.md
            patterns_md = generate_test_patterns(endpoints, schemas)
            patterns_path = agent_dir / "TEST_PATTERNS.md"
            patterns_path.write_text(patterns_md)
            console.print(f"  [green]✓[/green] Created: .agent/TEST_PATTERNS.md")

            console.print("\n[green]✅ Source code documentation generated![/green]\n")

        except ImportError as e:
            console.print(f"  [yellow]⚠[/yellow] Scanner modules not available: {e}")
            console.print("  [dim]Run: pip install socialseed-e2e[full] to enable[/dim]\n")
        except Exception as e:
            console.print(f"  [yellow]⚠[/yellow] Error scanning: {str(e)[:80]}")


@click.command(name="init")
@click.argument("directory", default=".", required=False)
@click.option("--force", is_flag=True, help="Overwrite existing files")
@click.option("--demo", is_flag=True, help="Include demo API and example services")
@click.option(
    "--scan",
    "scan_path",
    default=None,
    help="Scan source code and generate .agent docs. Can be a path like ../services/auth or 'auto' to detect",
)
@click.option(
    "--api",
    "api_path",
    default=None,
    help="Shortcut: auto-detect and scan API from common paths (src, app, api)",
)
def init_command(directory: str, force: bool, demo: bool, scan_path: str, api_path: str) -> None:
    """Initialize a new E2E project.

    Examples:
        e2e init my-project
        e2e init . --api           # Auto-detect API in current dir
        e2e init . --scan ../services/auth
        e2e init . --scan ../services/auth --api
    """
    target_path = Path(directory).resolve()

    console.print(f"\n🌱 [bold green]Initializing E2E project at:[/bold green] {target_path}\n")

    manager = InitManager(target_path, force, demo)
    manager.initialize()

    # Determine scan path
    final_scan_path = None

    if scan_path == "auto" or api_path:
        # Auto-detect source code
        possible_paths = [
            target_path / ".." / "services" / target_path.name,
            target_path / "src",
            target_path / "app",
            target_path / "api",
            target_path / ".." / "src",
            target_path / ".." / "app",
        ]
        for p in possible_paths:
            if (
                p.exists()
                and any(p.rglob("*.java"))
                or any(p.rglob("*.py"))
                or any(p.rglob("*.ts"))
            ):
                final_scan_path = str(p)
                console.print(f"[cyan]🔍 Auto-detected API at: {final_scan_path}[/cyan]\n")
                break

        if not final_scan_path:
            console.print("[yellow]⚠ Could not auto-detect API source code[/yellow]\n")
    elif scan_path:
        final_scan_path = scan_path

    # Generate docs if scan path determined
    if final_scan_path and Path(final_scan_path).exists():
        manager._create_agent_docs(final_scan_path)
    else:
        manager._create_agent_docs()

    console.print("\n[bold green]✅ Project initialized successfully![/bold green]\n")

    # AI Agent information
    console.print("[bold cyan]🤖 AI Agent Setup:[/bold cyan]\n")

    if final_scan_path:
        console.print("  ✅ AI documentation generated from source code!")
        console.print("  🤖 AI agents can now understand your API.\n")
    else:
        console.print("  To enable AI agents, run:")
        console.print("  [cyan]  e2e init . --api[/cyan]  # Auto-detect API")
        console.print("  [cyan]  e2e init . --scan ../path/to/your-api[/cyan]\n")
        console.print("  This generates .agent/ with:")
        console.print("  • ENDPOINTS.md    • DATA_SCHEMAS.md")
        console.print("  • AUTH_FLOWS.md  • TEST_PATTERNS.md")
        console.print("  • ERROR_CODES.md\n")

    console.print("[bold]Next steps:[/bold]")
    console.print("  1. Configure: e2e new-service <name> --base-url <url>")
    console.print("  2. Run: e2e run --service <name>\n")
    console.print("[dim]For AI agents: Just run 'opencode .' and ask to create tests![/dim]\n")


# Registration function
def get_command():
    return init_command


def get_name():
    return "init"


def get_help():
    return "Initialize a new E2E project"
