"""
socialseed-e2e: Framework E2E para testing de APIs REST con Playwright.

Este paquete proporciona un framework completo para testing end-to-end
de APIs REST, extraído y generalizado desde el proyecto SocialSeed.

Características principales:
    - Arquitectura hexagonal (core agnóstico)
    - Configuración centralizada via YAML
    - Carga dinámica de módulos de test
    - Soporte para API Gateway o conexiones directas
    - CLI completo con Rich y Click
    - Validación de esquemas JSON y Pydantic
    - Health checks y service waiting
    - Interceptores de request/response

Uso básico:
    >>> from socialseed_e2e import BasePage
    >>> page = BasePage("https://api.example.com")
    >>> page.setup()
    >>> response = page.get("/endpoint")
    >>> page.assert_ok(response)
    >>> data = page.assert_json(response)
    >>> page.teardown()

Para más información, visita: https://github.com/daironpf/socialseed-e2e
"""

__version__ = "0.2.0"
__version_info__ = (0, 2, 0)
__author__ = "Dairon Pérez Frías"
__email__ = "dairon.perezfrias@gmail.com"
__license__ = "MIT"
__copyright__ = "Copyright 2026 Dairon Pérez Frías"
__url__ = "https://github.com/daironpf/socialseed-e2e"

# CLI
from socialseed_e2e.cli import main

# Core - BasePage and configuration
from socialseed_e2e.core.base_page import (
    BasePage,
    BasePageError,
    RateLimitConfig,
    RequestLog,
    RetryConfig,
    ServiceHealth,
)
from socialseed_e2e.core.config_loader import (
    ApiConfigLoader,
    ApiGatewayConfig,
    AppConfig,
    DatabaseConfig,
    ReportingConfig,
    SecurityConfig,
)
from socialseed_e2e.core.config_loader import ServiceConfig as ConfigServiceConfig
from socialseed_e2e.core.config_loader import (
    TestDataConfig,
    get_config,
    get_service_config,
    get_service_url,
)
from socialseed_e2e.core.loaders import ModuleLoader
from socialseed_e2e.core.models import ServiceConfig, TestContext
from socialseed_e2e.core.test_orchestrator import TestOrchestrator
from socialseed_e2e.core.test_runner import (
    TestDiscoveryError,
    TestExecutionError,
    TestResult,
    TestSuiteResult,
    run_all_tests,
    run_service_tests,
)

# Utils - Pydantic helpers
from socialseed_e2e.utils.pydantic_helpers import (
    JavaCompatibleModel,
    camel_field,
    to_camel_dict,
    validate_camelcase_model,
)

# Utils - State management
from socialseed_e2e.utils.state_management import AuthStateMixin, DynamicStateMixin

# Utils - Template engine
from socialseed_e2e.utils.template_engine import (
    TemplateEngine,
    to_camel_case,
    to_class_name,
    to_snake_case,
)

# Utils - Validators
from socialseed_e2e.utils.validators import (
    ValidationError,
    validate_base_url,
    validate_email,
    validate_url,
    validate_uuid,
)

__all__ = [
    # Version
    "__version__",
    "__version_info__",
    # CLI
    "main",
    # Core - BasePage
    "BasePage",
    "BasePageError",
    "RetryConfig",
    "RateLimitConfig",
    "RequestLog",
    "ServiceHealth",
    # Core - Configuration
    "ApiConfigLoader",
    "get_config",
    "get_service_config",
    "get_service_url",
    # Core - Loaders and Orchestration
    "ModuleLoader",
    "TestOrchestrator",
    # Core - Test Runner
    "run_all_tests",
    "run_service_tests",
    "TestResult",
    "TestSuiteResult",
    "TestDiscoveryError",
    "TestExecutionError",
    # Core - Models
    "ServiceConfig",
    "TestContext",
    "AppConfig",
    "ApiGatewayConfig",
    "DatabaseConfig",
    "TestDataConfig",
    "SecurityConfig",
    "ReportingConfig",
    # Utils - State Management
    "DynamicStateMixin",
    "AuthStateMixin",
    # Utils - Pydantic
    "JavaCompatibleModel",
    "camel_field",
    "to_camel_dict",
    "validate_camelcase_model",
    # Utils - Validators
    "ValidationError",
    "validate_url",
    "validate_base_url",
    "validate_email",
    "validate_uuid",
    # Utils - Templates
    "TemplateEngine",
    "to_class_name",
    "to_snake_case",
    "to_camel_case",
]
