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

    def _create_agent_docs(self) -> None:
        """Create .agent directory with AI documentation."""
        agent_dir = self.target_path / ".agent"

        if not agent_dir.exists():
            agent_dir.mkdir(parents=True, exist_ok=True)
            console.print("  [green]✓[/green] Created: .agent/")

        readme_path = agent_dir / "README.md"
        if not readme_path.exists() or self.force:
            readme_path.write_text(self.AGENT_DOCS)
            console.print("  [green]✓[/green] Created: .agent/README.md")


@click.command(name="init")
@click.argument("directory", default=".", required=False)
@click.option("--force", is_flag=True, help="Overwrite existing files")
@click.option("--demo", is_flag=True, help="Include demo API and example services")
def init_command(directory: str, force: bool, demo: bool) -> None:
    """Initialize a new E2E project."""
    target_path = Path(directory).resolve()

    console.print(f"\n🌱 [bold green]Initializing E2E project at:[/bold green] {target_path}\n")

    manager = InitManager(target_path, force, demo)
    manager.initialize()

    console.print("\n[bold green]✅ Project initialized successfully![/bold green]\n")
    console.print("[bold]Next steps:[/bold]")
    console.print("  1. Install demo: [cyan]e2e install-demo[/cyan]")
    console.print("  2. Run tests: [cyan]e2e run[/cyan]\n")
    console.print("[dim]Note: Dependencies will be installed automatically when needed.[/dim]\n")


# Registration function
def get_command():
    return init_command


def get_name():
    return "init"


def get_help():
    return "Initialize a new E2E project"
