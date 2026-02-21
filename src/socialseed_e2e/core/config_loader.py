"""
ApiConfigLoader - Centralized Configuration Management

This module provides a centralized way to load and manage API configuration
from the api.conf file. It supports environment variable substitution and
provides easy access to all service configurations.
"""

# Try to import yaml, fallback to JSON if not available
import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

HAS_YAML = False
try:
    import yaml  # type: ignore

    HAS_YAML = True
except ImportError:
    pass  # YAML not available, will use JSON

# Import TemplateEngine for default config generation
from socialseed_e2e.utils import TemplateEngine


def normalize_service_name(name: str) -> str:
    """Normalize service name by converting hyphens to underscores.

    This ensures that service names like 'auth-service' and 'auth_service'
    are treated as identical for matching purposes.

    Args:
        name: Service name (may contain hyphens or underscores)

    Returns:
        str: Normalized service name with underscores

    Examples:
        >>> normalize_service_name("auth-service")
        'auth_service'
        >>> normalize_service_name("auth_service")
        'auth_service'
        >>> normalize_service_name("user-api-v2")
        'user_api_v2'
    """
    return name.replace("-", "_")


@dataclass
class ServiceEndpoint:
    """Represents a single API endpoint configuration."""

    name: str
    path: str
    method: str = "POST"
    requires_auth: bool = False


@dataclass
class ServiceConfig:
    """Complete configuration for a microservice."""

    name: str
    base_url: str
    health_endpoint: str = "/actuator/health"
    port: int = 8080
    maven_module: str = ""
    timeout: int = 30000
    headers: Dict[str, str] = field(default_factory=dict)
    auto_start: bool = True
    required: bool = True
    endpoints: Dict[str, str] = field(default_factory=dict)


@dataclass
class ApiGatewayConfig:
    """API Gateway configuration."""

    enabled: bool = False
    url: str = ""
    prefix: str = ""
    auth_type: str = "none"
    auth_token: Optional[str] = None
    api_key_header: Optional[str] = None
    api_key_value: Optional[str] = None


@dataclass
class DatabaseConfig:
    """Database connection configuration."""

    host: str = "localhost"
    port: int = 5432
    database: str = ""
    username: str = ""
    password: str = ""
    enabled: bool = False


@dataclass
class TestDataConfig:
    """Test data generation configuration."""

    email_domain: str = "test.socialseed.com"
    password: str = "StrongPass123!"
    username_prefix: str = "testuser"
    step_delay: int = 100
    async_timeout: int = 10000
    max_retries: int = 3
    retry_backoff_ms: int = 1000


@dataclass
class SecurityConfig:
    """Security and SSL configuration."""

    verify_ssl: bool = True
    ssl_cert: Optional[str] = None
    ssl_key: Optional[str] = None
    ssl_ca: Optional[str] = None
    test_tokens: Dict[str, str] = field(default_factory=dict)


@dataclass
class ReportingConfig:
    """Test reporting configuration."""

    format: str = "console"
    save_logs: bool = True
    log_dir: str = "./logs"
    include_payloads: bool = False
    screenshot_on_failure: bool = False


@dataclass
class ParallelConfig:
    """Parallel test execution configuration.

    Attributes:
        enabled: Whether parallel execution is enabled (default: False)
        max_workers: Maximum number of parallel workers (None = auto)
        mode: Execution mode ('service' or 'test')
        isolation_level: State isolation level ('process', 'service', 'none')
    """

    enabled: bool = False
    max_workers: Optional[int] = None
    mode: str = "service"  # 'service' or 'test'
    isolation_level: str = "process"  # 'process', 'service', 'none'


@dataclass
class AppConfig:
    """Main application configuration container."""

    environment: str = "dev"
    timeout: int = 30000
    user_agent: str = "SocialSeed-E2E-Agent/2.0"
    verification_level: str = "strict"
    verbose: bool = True
    project_name: str = "SocialSeed"
    project_version: str = "0.0.0"
    api_gateway: ApiGatewayConfig = field(default_factory=ApiGatewayConfig)
    services: Dict[str, ServiceConfig] = field(default_factory=dict)
    databases: Dict[str, DatabaseConfig] = field(default_factory=dict)
    test_data: TestDataConfig = field(default_factory=TestDataConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    reporting: ReportingConfig = field(default_factory=ReportingConfig)
    parallel: ParallelConfig = field(default_factory=ParallelConfig)


class ConfigError(Exception):
    """Custom exception for configuration errors."""

    pass


class ApiConfigLoader:
    """
    Loads and manages API configuration from api.conf file.

    Supports:
    - Environment variable substitution: ${VAR_NAME} or ${VAR_NAME:-default}
    - YAML or JSON format
    - Hot-reloading (reload config without restarting)
    - Singleton pattern for global access

    Usage:
        # Load default configuration
        config = ApiConfigLoader.load()

        # Get specific service configuration
        auth_config = config.services.get("auth")

        # Check if using API Gateway
        if config.api_gateway.enabled:
            base_url = config.api_gateway.url
    """

    _instance: Optional[AppConfig] = None
    _config_path: Optional[Path] = None

    @classmethod
    def load(cls, config_path: Optional[str] = None) -> AppConfig:
        """
        Load configuration from api.conf file.

        Args:
            config_path: Path to configuration file. If None, searches in:
                1. Environment variable E2E_CONFIG_PATH
                2. verify_services/api.conf (relative to project root)
                3. Current working directory ./api.conf

        Returns:
            AppConfig: Parsed configuration object

        Raises:
            FileNotFoundError: If configuration file not found
            ValueError: If configuration file is invalid
        """
        if cls._instance is not None and config_path is None:
            return cls._instance

        # Determine config file path
        if config_path is None:
            config_path = cls._find_config_file()

        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        # Read and parse file
        content = config_file.read_text()

        # Substitute environment variables
        content = cls._substitute_env_vars(content)

        # Parse YAML or JSON
        if HAS_YAML:
            import yaml as yaml_module

            data = yaml_module.safe_load(content)
        else:
            import json as json_module

            data = json_module.loads(content)

        # Build configuration object
        config = cls._parse_config(data)
        cls._instance = config
        cls._config_path = config_file

        return config

    @classmethod
    def reload(cls) -> AppConfig:
        """Reload configuration from file (useful for hot-reloading)."""
        cls._instance = None
        if cls._config_path is not None:
            return cls.load(str(cls._config_path))
        return cls.load()

    @classmethod
    def save(cls, config: AppConfig, config_path: Optional[str] = None) -> None:
        """Save configuration to file.

        Args:
            config: AppConfig object to save
            config_path: Path to save the configuration file.
                         If None, uses the currently loaded config path.
        """
        if config_path is None:
            config_path = str(cls._config_path) if cls._config_path else "e2e.conf"

        config_file = Path(config_path)

        # Convert to dictionary - handle both dataclass and Pydantic models
        try:
            # Try Pydantic model_dump first
            config_dict = config.model_dump(mode="json")
        except AttributeError:
            try:
                # Try dataclass asdict
                from dataclasses import asdict

                config_dict = asdict(config)
            except Exception:
                # Last resort - use __dict__
                config_dict = vars(config)

        # Build YAML content manually for better control
        content_lines = []

        # Write general section
        if hasattr(config, "environment"):
            content_lines.append("general:")
            content_lines.append(
                f"  environment: {getattr(config, 'environment', 'dev')}"
            )
            content_lines.append(f"  timeout: {getattr(config, 'timeout', 30000)}")
            content_lines.append(f"  verbose: {getattr(config, 'verbose', True)}")
            content_lines.append(
                f"  user_agent: {getattr(config, 'user_agent', 'socialseed-e2e/1.0')}"
            )
            content_lines.append(
                f"  project_name: {getattr(config, 'project_name', 'socialseed-e2e')}"
            )
            content_lines.append("")

        # Write services section
        content_lines.append("services:")
        if hasattr(config, "services") and config.services:
            for name, svc in config.services.items():
                content_lines.append(f"  {name}:")
                if hasattr(svc, "base_url"):
                    content_lines.append(f"    base_url: {svc.base_url}")
                if hasattr(svc, "health_endpoint"):
                    content_lines.append(f"    health_endpoint: {svc.health_endpoint}")
                if hasattr(svc, "timeout"):
                    content_lines.append(f"    timeout: {svc.timeout}")
        else:
            content_lines.append("  {}")

        config_file.write_text("\n".join(content_lines))

    @classmethod
    def get_config_path(cls) -> Optional[Path]:
        """Get the path of the currently loaded configuration file."""
        return cls._config_path

    @classmethod
    def _find_config_file(cls) -> str:
        """Find configuration file in common locations.

        Search order (highest priority first):
        1. E2E_CONFIG_PATH environment variable
        2. ./e2e.conf (current directory)
        3. ./config/e2e.conf
        4. ./tests/e2e.conf
        5. ~/.config/socialseed-e2e/default.conf
        6. verify_services/api.conf (legacy, for backward compatibility)
        7. ./api.conf (legacy, for backward compatibility)

        Returns:
            str: Path to the configuration file

        Raises:
            FileNotFoundError: If no configuration file is found
        """
        # Priority 1: Environment variable
        if env_path := os.getenv("E2E_CONFIG_PATH"):
            if Path(env_path).exists():
                return env_path
            raise FileNotFoundError(
                f"Configuration file specified in E2E_CONFIG_PATH not found: {env_path}"
            )

        # Priority 2-4: Search in current directory and subdirectories
        search_paths = [
            Path("e2e.conf"),  # Current directory
            Path("config") / "e2e.conf",  # config subdirectory
            Path("tests") / "e2e.conf",  # tests subdirectory
        ]

        for path in search_paths:
            if path.exists():
                return str(path)

        # Priority 4.5: Search in any immediate subdirectory (useful for monorepos)
        try:
            for sub_item in Path.cwd().iterdir():
                if sub_item.is_dir() and not sub_item.name.startswith("."):
                    sub_config = sub_item / "e2e.conf"
                    if sub_config.exists():
                        return str(sub_config)
        except Exception:
            pass  # Avoid crashes during directory iteration

        # Priority 5: Global config in home directory
        home_config = Path.home() / ".config" / "socialseed-e2e" / "default.conf"
        if home_config.exists():
            return str(home_config)

        # Priority 6-7: Legacy paths (for backward compatibility)
        # Search up the directory tree for verify_services/api.conf
        current_dir = Path.cwd()
        for parent in [current_dir] + list(current_dir.parents):
            verify_services_dir = parent / "verify_services"
            if verify_services_dir.exists():
                legacy_config = verify_services_dir / "api.conf"
                if legacy_config.exists():
                    return str(legacy_config)

        # Legacy: api.conf in current directory
        if Path("api.conf").exists():
            return "api.conf"

        # Configuration not found
        raise FileNotFoundError(
            "Could not find configuration file. Searched in:\n"
            "  1. E2E_CONFIG_PATH environment variable\n"
            "  2. ./e2e.conf\n"
            "  3. ./config/e2e.conf\n"
            "  4. ./tests/e2e.conf\n"
            "  5. Immediate subdirectories (e.g., ./otrotest/e2e.conf)\n"
            "  6. ~/.config/socialseed-e2e/default.conf\n"
            "  7. verify_services/api.conf (legacy)\n"
            "  8. ./api.conf (legacy)\n\n"
            f"Current directory: {os.getcwd()}\n\n"
            "To create a default configuration, run:\n"
            "  e2e init\n\n"
            "Or set the E2E_CONFIG_PATH environment variable:\n"
            "  export E2E_CONFIG_PATH=/path/to/your/e2e.conf"
        )

    @classmethod
    def create_default_config(
        cls, path: Union[str, Path], overwrite: bool = False
    ) -> str:
        """Create a default e2e.conf configuration file.

        Creates a default configuration file at the specified path using
        the e2e.conf.template template. Parent directories are created
        automatically if they don't exist.

        Args:
            path: Path where to create the configuration file
            overwrite: If True, overwrite existing file

        Returns:
            str: Path to the created configuration file

        Raises:
            FileExistsError: If file exists and overwrite=False
            FileNotFoundError: If template file doesn't exist
        """
        path = Path(path)
        engine = TemplateEngine()

        rendered_path = engine.render_to_file(
            "e2e.conf",
            variables={
                "environment": "dev",
                "timeout": "30000",
                "user_agent": "SocialSeed-E2E-Agent/2.0",
                "verbose": "true",
                "services_config": "",
            },
            output_path=path,
            overwrite=overwrite,
        )

        return str(rendered_path)

    @classmethod
    def _substitute_env_vars(cls, content: str) -> str:
        """Substitute environment variables in configuration content."""
        # Pattern: ${VAR_NAME} or ${VAR_NAME:-default_value}
        pattern = r"\$\{(\w+)(?::-([^}]*))?\}"

        def replace_var(match):
            var_name = match.group(1)
            default_value = match.group(2)

            env_value = os.getenv(var_name)
            if env_value is not None:
                return env_value
            elif default_value is not None:
                return default_value
            else:
                # Keep original if no value found
                return match.group(0)

        return re.sub(pattern, replace_var, content)

    @classmethod
    def validate_config(cls, data: Dict[str, Any], strict: bool = False) -> None:
        """Validate minimum configuration requirements.

        Args:
            data: Raw configuration dictionary
            strict: If True, raises error for missing optional fields

        Raises:
            ConfigError: If configuration is invalid or missing required fields
        """
        errors = []
        warnings = []

        # Check for required 'general' section
        if "general" not in data:
            errors.append("Missing required 'general' section")
        else:
            general = data["general"]

            # Validate environment
            if "environment" in general:
                valid_envs = [
                    "dev",
                    "development",
                    "staging",
                    "prod",
                    "production",
                    "test",
                ]
                if general["environment"] not in valid_envs:
                    warnings.append(
                        f"Unusual environment value: {general['environment']}. "
                        f"Recommended: {', '.join(valid_envs)}"
                    )

            # Validate timeout is positive integer
            if "timeout" in general:
                try:
                    timeout = int(general["timeout"])
                    if timeout <= 0:
                        errors.append("general.timeout must be a positive integer")
                    elif timeout < 1000:
                        warnings.append(f"general.timeout is very short ({timeout}ms)")
                except (ValueError, TypeError):
                    errors.append("general.timeout must be a valid integer")

        # Check for services section (at least one service recommended)
        services = data.get("services", {})
        if not services:
            warnings.append("No services defined. Add at least one service to test.")
        else:
            # Validate each service has required fields
            for service_name, service_data in services.items():
                if not isinstance(service_data, dict):
                    errors.append(f"Service '{service_name}' must be a dictionary")
                    continue

                if "base_url" not in service_data:
                    errors.append(
                        f"Service '{service_name}' missing required field: base_url"
                    )
                elif not service_data.get("base_url"):
                    warnings.append(f"Service '{service_name}' has empty base_url")

                # Validate port if provided
                if "port" in service_data:
                    try:
                        port = int(service_data["port"])
                        if port < 1 or port > 65535:
                            errors.append(
                                f"Service '{service_name}' port must be between 1 and 65535"
                            )
                    except (ValueError, TypeError):
                        errors.append(
                            f"Service '{service_name}' port must be a valid integer"
                        )

        # Raise error if there are validation errors
        if errors:
            raise ConfigError(
                "Configuration validation failed:\n  - " + "\n  - ".join(errors)
            )

        # Print warnings if strict mode
        if strict and warnings:
            import warnings as warnings_module

            for warning in warnings:
                warnings_module.warn(f"Config warning: {warning}")

    @classmethod
    def _parse_config(cls, data: Dict[str, Any]) -> AppConfig:
        """Parse raw dictionary into AppConfig object."""
        # Validate configuration before parsing
        cls.validate_config(data)

        # General configuration
        general = data.get("general", {})
        project = general.get("project", {})

        config = AppConfig(
            environment=general.get("environment", "dev"),
            timeout=general.get("timeout", 30000),
            user_agent=general.get("user_agent", "SocialSeed-E2E-Agent/2.0"),
            verification_level=general.get("verification_level", "strict"),
            verbose=general.get("verbose", True),
            project_name=project.get("name", "SocialSeed"),
            project_version=project.get("version", "0.0.0"),
        )

        # API Gateway
        gateway_data = data.get("api_gateway", {})
        auth_data = gateway_data.get("auth", {})
        config.api_gateway = ApiGatewayConfig(
            enabled=gateway_data.get("enabled", False),
            url=gateway_data.get("url", ""),
            prefix=gateway_data.get("prefix", ""),
            auth_type=auth_data.get("type", "none"),
            auth_token=auth_data.get("bearer_token"),
            api_key_header=auth_data.get("api_key_header"),
            api_key_value=auth_data.get("api_key_value"),
        )

        # Services
        services_data = data.get("services") or {}
        for service_name, service_data in services_data.items():
            # Normalize service name (convert hyphens to underscores)
            normalized_name = normalize_service_name(service_name)
            config.services[normalized_name] = ServiceConfig(
                name=service_data.get("name", service_name),
                base_url=service_data.get("base_url", ""),
                health_endpoint=service_data.get("health_endpoint", "/actuator/health"),
                port=service_data.get("port", 8080),
                maven_module=service_data.get(
                    "maven_module", f"services/{service_name}"
                ),
                timeout=service_data.get("timeout", config.timeout),
                headers=service_data.get("headers", {}),
                auto_start=service_data.get("auto_start", True),
                required=service_data.get("required", True),
                endpoints=service_data.get("endpoints", {}),
            )

        # Databases
        databases_data = data.get("databases") or {}
        for db_name, db_data in databases_data.items():
            config.databases[db_name] = DatabaseConfig(
                host=db_data.get("host", "localhost"),
                port=db_data.get("port", 5432),
                database=db_data.get("database", ""),
                username=db_data.get("username", ""),
                password=db_data.get("password", ""),
                enabled=db_data.get("enabled", False),
            )

        # Test data
        test_data = data.get("test_data", {})
        user_data = test_data.get("user", {})
        timing_data = test_data.get("timing", {})
        retries_data = test_data.get("retries", {})
        config.test_data = TestDataConfig(
            email_domain=user_data.get("email_domain", "test.socialseed.com"),
            password=user_data.get("password", "StrongPass123!"),
            username_prefix=user_data.get("username_prefix", "testuser"),
            step_delay=timing_data.get("step_delay", 100),
            async_timeout=timing_data.get("async_timeout", 10000),
            max_retries=retries_data.get("max_attempts", 3),
            retry_backoff_ms=retries_data.get("backoff_ms", 1000),
        )

        # Security
        security_data = data.get("security", {})
        config.security = SecurityConfig(
            verify_ssl=security_data.get("verify_ssl", True),
            ssl_cert=security_data.get("ssl_cert"),
            ssl_key=security_data.get("ssl_key"),
            ssl_ca=security_data.get("ssl_ca"),
            test_tokens=security_data.get("test_tokens", {}),
        )

        # Reporting
        reporting_data = data.get("reporting", {})
        config.reporting = ReportingConfig(
            format=reporting_data.get("format", "console"),
            save_logs=reporting_data.get("save_logs", True),
            log_dir=reporting_data.get("log_dir", "./logs"),
            include_payloads=reporting_data.get("include_payloads", False),
            screenshot_on_failure=reporting_data.get("screenshot_on_failure", False),
        )

        # Parallel execution
        parallel_data = data.get("parallel", {})
        config.parallel = ParallelConfig(
            enabled=parallel_data.get("enabled", False),
            max_workers=parallel_data.get("max_workers"),
            mode=parallel_data.get("mode", "service"),
            isolation_level=parallel_data.get("isolation_level", "process"),
        )

        return config

    @classmethod
    def get_service_url(
        cls, service_name: str, use_gateway: Optional[bool] = None
    ) -> str:
        """
        Get the effective URL for a service.

        If API Gateway is enabled, returns gateway URL + service path.
        Otherwise, returns the service's base_url.

        Args:
            service_name: Name of the service
            use_gateway: Force gateway mode (None = use config setting)

        Returns:
            str: Full URL for the service
        """
        config = cls.load()
        normalized_name = normalize_service_name(service_name)
        service = config.services.get(normalized_name)

        if not service:
            raise ValueError(f"Service '{service_name}' not found in configuration")

        # Determine if we should use gateway
        should_use_gateway = (
            use_gateway if use_gateway is not None else config.api_gateway.enabled
        )

        if should_use_gateway and config.api_gateway.url:
            gateway_url = config.api_gateway.url.rstrip("/")
            prefix = config.api_gateway.prefix.rstrip("/")
            return f"{gateway_url}{prefix}/{service_name}"

        return service.base_url

    @classmethod
    def get_all_required_services(cls) -> List[str]:
        """Get list of services marked as required."""
        config = cls.load()
        return [name for name, service in config.services.items() if service.required]

    @classmethod
    def get_auto_start_services(cls) -> List[str]:
        """Get list of services configured for auto-start."""
        config = cls.load()
        return [name for name, service in config.services.items() if service.auto_start]

    @classmethod
    def get_service_by_maven_module(cls, maven_module: str) -> Optional[ServiceConfig]:
        """Find service configuration by Maven module name."""
        config = cls.load()
        for service in config.services.values():
            if service.maven_module == maven_module:
                return service
        return None


# Convenience functions for direct import
def get_config() -> AppConfig:
    """Get the global configuration instance."""
    return ApiConfigLoader.load()


def get_service_config(service_name: str) -> Optional[ServiceConfig]:
    """Get configuration for a specific service.

    Args:
        service_name: Name of the service (hyphens or underscores allowed)

    Returns:
        Optional[ServiceConfig]: Service configuration if found, None otherwise

    Example:
        >>> get_service_config("auth-service")  # Matches auth_service in config
        >>> get_service_config("auth_service")  # Matches auth_service in config
    """
    config = ApiConfigLoader.load()
    normalized_name = normalize_service_name(service_name)
    return config.services.get(normalized_name)


def get_service_url(service_name: str) -> str:
    """Get effective URL for a service (considers API Gateway)."""
    return ApiConfigLoader.get_service_url(service_name)
