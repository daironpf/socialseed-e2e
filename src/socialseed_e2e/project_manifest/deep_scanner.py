"""Zero-config deep scanner for automatic project mapping.

This module provides intelligent project discovery without requiring
user configuration. It analyzes source code to detect tech stacks,
extract endpoints, and discover environment configuration.
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from socialseed_e2e.project_manifest.models import (
    EnvironmentVariable,
    PortConfig,
)


class TechStackDetector:
    """Detects technology stack by analyzing source code patterns."""

    # Framework detection patterns
    FRAMEWORK_PATTERNS = {
        # Python frameworks
        "fastapi": {
            "patterns": [
                r"from\s+fastapi\s+import",
                r"@app\.(get|post|put|delete|patch)",
                r"@router\.(get|post|put|delete|patch)",
                r"FastAPI\s*\(",
            ],
            "language": "python",
        },
        "flask": {
            "patterns": [
                r"from\s+flask\s+import",
                r"@app\.route",
                r"@bp\.route",
                r"Flask\s*\(__name__\)",
            ],
            "language": "python",
        },
        "django": {
            "patterns": [
                r"from\s+django",
                r"urlpatterns\s*=",
                r"@api_view",
            ],
            "language": "python",
        },
        # Java frameworks
        "spring": {
            "patterns": [
                r"@RestController",
                r"@RequestMapping",
                r"@GetMapping",
                r"@PostMapping",
                r"import\s+org\.springframework",
                r"SpringApplication\.run",
            ],
            "language": "java",
        },
        "spring_boot": {
            "patterns": [
                r"@SpringBootApplication",
                r"spring-boot",
                r"SpringBootTest",
            ],
            "language": "java",
            "parent": "spring",
        },
        # Node.js frameworks
        "express": {
            "patterns": [
                r"require\s*\(\s*['\"]express['\"]\s*\)",
                r"from\s+['\"]express['\"]",
                r"app\.(get|post|put|delete|patch)\s*\(",
                r"router\.(get|post|put|delete|patch)\s*\(",
            ],
            "language": "javascript",
        },
        "nestjs": {
            "patterns": [
                r"@Controller",
                r"@Get",
                r"@Post",
                r"@Module",
                r"import.*@nestjs",
            ],
            "language": "typescript",
        },
        # Go frameworks
        "gin": {
            "patterns": [
                r"github\.com/gin-gonic/gin",
                r"gin\.Default\(\)",
                r"gin\.New\(\)",
            ],
            "language": "go",
        },
        # C# frameworks
        "aspnet_core": {
            "patterns": [
                r"using\s+Microsoft\.AspNetCore",
                r"\[ApiController\]",
                r"\[Route\(",
                r"IActionResult",
            ],
            "language": "csharp",
        },
    }

    def detect(self, project_root: Path) -> List[Dict[str, Any]]:
        """Detect all frameworks used in the project.

        Args:
            project_root: Root directory of the project

        Returns:
            List of detected frameworks with language and confidence
        """
        detected = []

        for framework, config in self.FRAMEWORK_PATTERNS.items():
            confidence = self._check_framework(project_root, config["patterns"])
            if confidence > 0:
                detected.append(
                    {
                        "framework": framework,
                        "language": config["language"],
                        "confidence": confidence,
                    }
                )

        # Sort by confidence
        detected.sort(key=lambda x: x["confidence"], reverse=True)
        return detected

    def _check_framework(self, project_root: Path, patterns: List[str]) -> float:
        """Check how many patterns match in the codebase.

        Args:
            project_root: Project root directory
            patterns: List of regex patterns to search for

        Returns:
            Confidence score (0.0 to 1.0)
        """
        matches = 0
        total_files_checked = 0
        max_files_to_check = 50  # Limit to avoid slow performance

        for file_path in self._get_source_files(project_root):
            if total_files_checked >= max_files_to_check:
                break

            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                total_files_checked += 1

                for pattern in patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        matches += 1

            except Exception:
                continue

        # Calculate confidence based on pattern matches
        if not patterns:
            return 0.0

        return min(matches / len(patterns), 1.0)

    def _get_source_files(self, project_root: Path) -> List[Path]:
        """Get all source code files in the project."""
        source_files = []

        extensions = {
            "python": [".py"],
            "java": [".java"],
            "javascript": [".js", ".mjs"],
            "typescript": [".ts"],
            "go": [".go"],
            "csharp": [".cs"],
        }

        all_extensions = []
        for exts in extensions.values():
            all_extensions.extend(exts)

        for ext in all_extensions:
            source_files.extend(project_root.rglob(f"*{ext}"))

        return source_files


class EnvironmentDetector:
    """Detects environment configuration from common files."""

    def detect(self, project_root: Path) -> Dict[str, Any]:
        """Detect environment configuration.

        Args:
            project_root: Project root directory

        Returns:
            Dictionary with detected configuration
        """
        config = {
            "ports": [],
            "env_vars": [],
            "base_urls": [],
            "config_files": [],
        }

        # Check docker-compose.yml
        config.update(self._parse_docker_compose(project_root))

        # Check .env files
        config.update(self._parse_env_files(project_root))

        # Check application properties (Java)
        config.update(self._parse_application_properties(project_root))

        # Check application config files
        config.update(self._parse_app_config(project_root))

        return config

    def _parse_docker_compose(self, project_root: Path) -> Dict[str, Any]:
        """Parse docker-compose files for ports and env vars."""
        result = {"ports": [], "env_vars": [], "config_files": []}

        docker_files = [
            project_root / "docker-compose.yml",
            project_root / "docker-compose.yaml",
            project_root / "docker-compose.dev.yml",
        ]

        for docker_file in docker_files:
            if docker_file.exists():
                result["config_files"].append(
                    str(docker_file.relative_to(project_root))
                )

                try:
                    import yaml

                    content = yaml.safe_load(docker_file.read_text())

                    if content and "services" in content:
                        for service_name, service_config in content["services"].items():
                            # Extract ports
                            if "ports" in service_config:
                                for port_mapping in service_config["ports"]:
                                    if isinstance(port_mapping, str):
                                        # Format: "host:container"
                                        parts = port_mapping.split(":")
                                        if len(parts) >= 1:
                                            try:
                                                port = int(parts[0])
                                                result["ports"].append(
                                                    PortConfig(
                                                        port=port,
                                                        description=(
                                                            f"Docker service: {service_name}"
                                                        ),
                                                    )
                                                )
                                            except ValueError:
                                                pass

                            # Extract environment variables
                            if "environment" in service_config:
                                env = service_config["environment"]
                                if isinstance(env, dict):
                                    for key, value in env.items():
                                        result["env_vars"].append(
                                            EnvironmentVariable(
                                                name=key,
                                                default_value=str(value)
                                                if value
                                                else None,
                                            )
                                        )
                                elif isinstance(env, list):
                                    for item in env:
                                        if isinstance(item, str) and "=" in item:
                                            key, _, value = item.partition("=")
                                            result["env_vars"].append(
                                                EnvironmentVariable(
                                                    name=key,
                                                    default_value=value or None,
                                                )
                                            )

                except Exception:
                    pass

        return result

    def _parse_env_files(self, project_root: Path) -> Dict[str, Any]:
        """Parse .env files for configuration."""
        result = {"env_vars": [], "config_files": [], "base_urls": []}

        env_files = [
            project_root / ".env",
            project_root / ".env.local",
            project_root / ".env.development",
            project_root / ".env.example",
        ]

        for env_file in env_files:
            if env_file.exists():
                result["config_files"].append(str(env_file.relative_to(project_root)))

                try:
                    content = env_file.read_text()
                    for line in content.split("\n"):
                        line = line.strip()
                        if line and not line.startswith("#"):
                            if "=" in line:
                                key, _, value = line.partition("=")
                                key = key.strip()
                                value = value.strip().strip("'\"")

                                result["env_vars"].append(
                                    EnvironmentVariable(
                                        name=key,
                                        default_value=value if value else None,
                                    )
                                )

                                # Check for URL-related vars
                                if "URL" in key.upper() or "HOST" in key.upper():
                                    if value and not value.startswith("${"):
                                        result["base_urls"].append(value)

                except Exception:
                    pass

        return result

    def _parse_application_properties(self, project_root: Path) -> Dict[str, Any]:
        """Parse Java application.properties or application.yml."""
        result = {"ports": [], "config_files": []}

        # application.properties
        props_files = list(project_root.rglob("application*.properties"))
        props_files.extend(project_root.rglob("application*.yml"))
        props_files.extend(project_root.rglob("application*.yaml"))

        for props_file in props_files:
            result["config_files"].append(str(props_file.relative_to(project_root)))

            try:
                content = props_file.read_text()

                # Look for server.port
                port_match = re.search(r"server\.port\s*=\s*(\d+)", content)
                if port_match:
                    result["ports"].append(
                        PortConfig(
                            port=int(port_match.group(1)),
                            description="Spring Boot server port",
                        )
                    )

            except Exception:
                pass

        return result

    def _parse_app_config(self, project_root: Path) -> Dict[str, Any]:
        """Parse framework-specific config files."""
        result = {"ports": [], "config_files": []}

        # FastAPI/Flask config
        config_files = [
            project_root / "config.py",
            project_root / "config.yml",
            project_root / "config.yaml",
            project_root / "settings.py",
        ]

        for config_file in config_files:
            if config_file.exists():
                result["config_files"].append(
                    str(config_file.relative_to(project_root))
                )

        return result


class DeepScanner:
    """Zero-config deep scanner that maps entire applications automatically.

        This scanner acts as a "detective" - it crawls directories, identifies
    tech stacks, extracts endpoints, and discovers configuration without
        requiring user input.

        Example:
            >>> scanner = DeepScanner("/path/to/project")
            >>> result = scanner.scan()
            >>> print(f"Detected: {result['framework']} on port {result['port']}")
    """

    def __init__(self, project_root: str):
        """Initialize the deep scanner.

        Args:
            project_root: Root directory of the project to scan
        """
        self.project_root = Path(project_root).resolve()
        self.tech_detector = TechStackDetector()
        self.env_detector = EnvironmentDetector()

    def scan(self) -> Dict[str, Any]:
        """Perform deep scan of the project.

        Returns:
            Dictionary with complete project mapping including:
            - Detected tech stack(s)
            - Environment configuration
            - Recommended base URLs
            - Service structure
        """
        print(f"🔍 Deep scanning: {self.project_root}")

        # Step 1: Detect tech stack
        print("  → Detecting tech stack...")
        frameworks = self.tech_detector.detect(self.project_root)

        # Step 2: Detect environment
        print("  → Detecting environment...")
        env_config = self.env_detector.detect(self.project_root)

        # Step 3: Build result
        result = {
            "project_root": str(self.project_root),
            "frameworks": frameworks,
            "environment": env_config,
            "services": self._identify_services(frameworks),
            "recommendations": self._generate_recommendations(frameworks, env_config),
        }

        # Print summary
        self._print_summary(result)

        return result

    def _identify_services(
        self, frameworks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify distinct services in the project."""
        services = []

        # Look for common service patterns
        service_dirs = self._find_service_directories()

        for service_dir in service_dirs:
            service_info = {
                "name": service_dir.name,
                "path": str(service_dir.relative_to(self.project_root)),
                "frameworks": [],
            }

            # Detect frameworks for this specific service
            service_frameworks = self.tech_detector.detect(service_dir)
            service_info["frameworks"] = service_frameworks

            services.append(service_info)

        # If no services found, treat entire project as one service
        if not services and frameworks:
            services.append(
                {
                    "name": self.project_root.name,
                    "path": ".",
                    "frameworks": frameworks,
                }
            )

        return services

    def _find_service_directories(self) -> List[Path]:
        """Find directories that likely contain individual services."""
        service_dirs = []

        # Common patterns for microservices
        patterns = [
            "services/*",
            "microservices/*",
            "apps/*",
            "packages/*",
            "*/api",
            "*/service",
        ]

        for pattern in patterns:
            for match in self.project_root.glob(pattern):
                if match.is_dir():
                    # Check if it looks like a service (has source files)
                    if self._looks_like_service(match):
                        service_dirs.append(match)

        return service_dirs

    def _looks_like_service(self, directory: Path) -> bool:
        """Check if a directory looks like a service."""
        # Check for common service indicators
        indicators = [
            "*.py",
            "*.java",
            "*.js",
            "*.ts",
            "package.json",
            "requirements.txt",
            "pom.xml",
            "Dockerfile",
        ]

        for indicator in indicators:
            if list(directory.glob(indicator)):
                return True

        return False

    def _generate_recommendations(
        self, frameworks: List[Dict[str, Any]], env_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate recommendations based on scan results."""
        recommendations = {
            "base_url": None,
            "health_endpoint": "/health",
            "setup_commands": [],
        }

        # Suggest base URL
        if env_config.get("base_urls"):
            recommendations["base_url"] = env_config["base_urls"][0]
        elif env_config.get("ports"):
            port = env_config["ports"][0].port
            recommendations["base_url"] = f"http://localhost:{port}"
        else:
            # Default ports by framework
            if frameworks:
                framework = frameworks[0]["framework"]
                default_ports = {
                    "fastapi": 8000,
                    "flask": 5000,
                    "django": 8000,
                    "spring": 8080,
                    "spring_boot": 8080,
                    "express": 3000,
                    "nestjs": 3000,
                    "gin": 8080,
                    "aspnet_core": 5000,
                }
                if framework in default_ports:
                    recommendations["base_url"] = (
                        f"http://localhost:{default_ports[framework]}"
                    )

        # Suggest health endpoint by framework
        if frameworks:
            framework = frameworks[0]["framework"]
            health_endpoints = {
                "spring": "/actuator/health",
                "spring_boot": "/actuator/health",
            }
            if framework in health_endpoints:
                recommendations["health_endpoint"] = health_endpoints[framework]

        # Suggest setup commands
        if frameworks:
            framework = frameworks[0]["framework"]
            setup_commands = {
                "fastapi": [
                    "pip install -r requirements.txt",
                    "uvicorn main:app --reload",
                ],
                "flask": ["pip install -r requirements.txt", "flask run"],
                "django": [
                    "pip install -r requirements.txt",
                    "python manage.py runserver",
                ],
                "spring": ["./mvnw spring-boot:run"],
                "spring_boot": ["./mvnw spring-boot:run"],
                "express": ["npm install", "npm run dev"],
                "nestjs": ["npm install", "npm run start:dev"],
            }
            if framework in setup_commands:
                recommendations["setup_commands"] = setup_commands[framework]

        return recommendations

    def _print_summary(self, result: Dict[str, Any]) -> None:
        """Print a summary of the scan results."""
        print("\n📋 Scan Summary:")
        print("-" * 50)

        if result["frameworks"]:
            print("🛠️  Detected Frameworks:")
            for fw in result["frameworks"][:3]:  # Top 3
                print(
                    f"   • {fw['framework']} ({fw['language']}) - {fw['confidence']:.0%} confidence"
                )

        if result["services"]:
            print(f"\n📦 Services Found: {len(result['services'])}")
            for svc in result["services"]:
                print(f"   • {svc['name']}")

        if result["environment"].get("ports"):
            print(f"\n🔌 Ports Detected: {len(result['environment']['ports'])}")
            for port in result["environment"]["ports"][:3]:
                print(f"   • {port.port} - {port.description}")

        if result["recommendations"].get("base_url"):
            print(f"\n🌐 Recommended Base URL: {result['recommendations']['base_url']}")

        print("-" * 50)
