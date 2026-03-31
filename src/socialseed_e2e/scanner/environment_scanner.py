"""Environment scanner for detecting environment variables.

This module detects environment variables and classifies them by environment.
"""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class EnvVar:
    """Represents an environment variable."""

    name: str
    value: Optional[str] = None
    default: Optional[str] = None
    description: str = ""
    required: bool = False
    sensitive: bool = False


@dataclass
class EnvironmentInfo:
    """Represents environment information."""

    variables: List[EnvVar] = field(default_factory=list)
    by_environment: Dict[str, List[str]] = field(default_factory=dict)
    secrets: List[str] = field(default_factory=list)


class EnvironmentScanner:
    """Scans for environment variables."""

    SENSITIVE_PATTERNS = [
        r"password",
        r"secret",
        r"token",
        r"api_key",
        r"apikey",
        r"private_key",
        r"credential",
        r"auth",
    ]

    COMMON_VARS = [
        ("DATABASE_URL", "URL de conexión a la base de datos", True),
        ("DATABASE_HOST", "Host de la base de datos", False),
        ("DATABASE_PORT", "Puerto de la base de datos", False),
        ("DATABASE_USER", "Usuario de la base de datos", False),
        ("DATABASE_PASSWORD", "Password de la base de datos", True),
        ("REDIS_URL", "URL de Redis", False),
        ("REDIS_PASSWORD", "Password de Redis", True),
        ("JWT_SECRET", "Secret para JWT", True),
        ("JWT_EXPIRATION", "Tiempo de expiración del JWT", False),
        ("AWS_ACCESS_KEY_ID", "Access Key de AWS", True),
        ("AWS_SECRET_ACCESS_KEY", "Secret Key de AWS", True),
        ("AWS_REGION", "Región de AWS", False),
        ("SENDGRID_API_KEY", "API Key de SendGrid", True),
        ("STRIPE_API_KEY", "API Key de Stripe", True),
        ("PORT", "Puerto del servidor", False),
        ("HOST", "Host del servidor", False),
        ("DEBUG", "Modo debug", False),
        ("LOG_LEVEL", "Nivel de logging", False),
    ]

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def scan(self) -> EnvironmentInfo:
        """Scan project for environment variables."""
        info = EnvironmentInfo()

        self._scan_env_files(info)
        self._scan_config_files(info)
        self._classify_by_environment(info)

        return info

    def _scan_env_files(self, info: EnvironmentInfo) -> None:
        """Scan .env files."""
        env_files = [
            self.project_root / ".env",
            self.project_root / ".env.local",
            self.project_root / ".env.example",
            self.project_root / ".env.development",
            self.project_root / ".env.production",
            self.project_root / ".env.test",
        ]

        for env_file in env_files:
            if env_file.exists():
                content = env_file.read_text(errors="ignore")
                lines = content.split("\n")

                for line in lines:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")

                        is_sensitive = any(
                            re.search(p, key, re.IGNORECASE)
                            for p in self.SENSITIVE_PATTERNS
                        )

                        var = EnvVar(
                            name=key,
                            value=value if not is_sensitive else None,
                            required=False,
                            sensitive=is_sensitive,
                        )

                        info.variables.append(var)

                        if is_sensitive:
                            info.secrets.append(key)

    def _scan_config_files(self, info: EnvironmentInfo) -> None:
        """Scan configuration files for env var references."""
        for name, desc, required in self.COMMON_VARS:
            if not any(v.name == name for v in info.variables):
                var = EnvVar(
                    name=name,
                    description=desc,
                    required=required,
                    sensitive=any(re.search(p, name, re.IGNORECASE) for p in self.SENSITIVE_PATTERNS),
                )
                info.variables.append(var)

    def _classify_by_environment(self, info: EnvironmentInfo) -> None:
        """Classify variables by environment."""
        env_patterns = {
            "development": [r"dev", r"local", r"debug"],
            "staging": [r"staging", r"stage", r"stg"],
            "production": [r"prod", r"production", r"prd"],
        }

        for var in info.variables:
            for env, patterns in env_patterns.items():
                if any(re.search(p, var.name, re.IGNORECASE) for p in patterns):
                    if env not in info.by_environment:
                        info.by_environment[env] = []
                    info.by_environment[env].append(var.name)


def generate_environment_doc(project_root: Path, output_path: Optional[Path] = None) -> str:
    """Generate ENVIRONMENT.md document."""
    scanner = EnvironmentScanner(project_root)
    info = scanner.scan()

    doc = "# Variables de Entorno\n\n"

    if info.secrets:
        doc += "⚠️ **Variables Sensibles** (NO exponer en código)\n\n"
        for secret in info.secrets:
            doc += f"- `{secret}`\n"
        doc += "\n"

    doc += "## Variables Definidas\n\n"
    doc += "| Variable | Descripción | Requerida | Sensible |\n"
    doc += "|----------|-------------|-----------|----------|\n"
    for var in info.variables:
        doc += f"| {var.name} | {var.description} | {'Sí' if var.required else 'No'} | {'Sí' if var.sensitive else 'No'} |\n"
    doc += "\n"

    if info.by_environment:
        doc += "## Por Entorno\n\n"
        for env, vars_list in info.by_environment.items():
            doc += f"### {env.title()}\n\n"
            doc += ", ".join([f"`{v}`" for v in vars_list])
            doc += "\n\n"

    doc += "---\n\n"
    doc += "## Ejemplo .env\n\n"
    doc += "```bash\n"
    for var in info.variables[:10]:
        if var.sensitive:
            doc += f"# {var.name}=<value>\n"
        else:
            default = var.default or ""
            doc += f"{var.name}={default}\n"
    doc += "```\n"

    if output_path:
        output_path.write_text(doc)

    return doc


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        project_root = Path(sys.argv[1])
        print(generate_environment_doc(project_root))
    else:
        print("Usage: python environment_scanner.py <project_root>")
