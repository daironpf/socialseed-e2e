"""
socialseed-e2e: Universal Framework E2E para testing de APIs REST con Playwright.

Este framework proporciona una solución completa para testing end-to-end
de APIs REST escritas en CUALQUIER lenguaje: Java, C#, Python, Node.js, Go, C++, etc.

Características principales:
    - Soporte multi-lenguaje (Java, C#, Python, Node.js, Go, C++, etc.)
    - Detección automática de naming conventions (camelCase, PascalCase, snake_case)
    - Modelos Pydantic universales (APIModel) con serialización automática
    - Arquitectura hexagonal (core agnóstico)
    - Configuración centralizada via YAML
    - Carga dinámica de módulos de test
    - Soporte para API Gateway o conexiones directas
    - CLI completo con Rich y Click
    - Validación de esquemas JSON y Pydantic
    - Health checks y service waiting
    - Interceptores de request/response
    - Prevención automática de errores comunes
    - Manejo de estado entre tests (DynamicStateMixin)

Uso básico:
    >>> from socialseed_e2e import BasePage, APIModel, api_field
    >>>
    >>> # Crear modelo para API Java (camelCase)
    >>> class LoginRequest(APIModel):
    ...     refresh_token: str = api_field("refreshToken")
    ...     user_name: str = api_field("userName")
    >>>
    >>> page = BasePage("https://api.example.com")
    >>> page.setup()
    >>>
    >>> request = LoginRequest(refresh_token="abc", user_name="john")
    >>> data = request.to_dict()  # {'refreshToken': 'abc', 'userName': 'john'}
    >>> response = page.post("/login", data=data)
    >>>
    >>> page.assert_ok(response)
    >>> page.teardown()

Para más información: https://github.com/daironpf/socialseed-e2e
"""

from socialseed_e2e.__version__ import (
    __author__,
    __copyright__,
    __email__,
    __license__,
    __url__,
    __version__,
    __version_info__,
)

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

# Core - gRPC Support
try:
    from socialseed_e2e.core.base_grpc_page import (
        BaseGrpcPage,
        GrpcCallLog,
        GrpcRetryConfig,
    )

    GRPC_AVAILABLE = True
except ImportError:
    GRPC_AVAILABLE = False

# Utils - Pydantic helpers (universal for all languages)
# New universal model; Field creators for different conventions
# Naming conversion utilities; Serialization utilities
# Convenience field aliases; Backwards compatibility
from socialseed_e2e.utils.pydantic_helpers import (
    APIModel,
    JavaCompatibleModel,
    NamingConvention,
    access_token_field,
    api_field,
    camel_field,
    created_at_field,
    current_password_field,
    detect_naming_convention,
    new_password_field,
    pascal_field,
    refresh_token_field,
    snake_field,
    to_api_dict,
    to_camel_case,
    to_camel_dict,
    to_kebab_case,
    to_pascal_case,
    to_snake_case,
    updated_at_field,
    user_id_field,
    user_name_field,
    validate_api_model,
    validate_camelcase_model,
)

# Utils - State management
from socialseed_e2e.utils.state_management import AuthStateMixin, DynamicStateMixin

# Utils - Template engine
from socialseed_e2e.utils.template_engine import TemplateEngine
from socialseed_e2e.utils.template_engine import to_camel_case as template_to_camel_case
from socialseed_e2e.utils.template_engine import to_class_name
from socialseed_e2e.utils.template_engine import to_snake_case as template_to_snake_case

# Utils - Validators
from socialseed_e2e.utils.validators import (
    ValidationError,
    validate_base_url,
    validate_email,
    validate_url,
    validate_uuid,
)

# Utils - Proto Schema Handler (gRPC support)
try:
    from socialseed_e2e.utils.proto_schema import ProtoRegistry, ProtoSchemaHandler
except ImportError:
    pass

# Core - Interactive Doctor
from socialseed_e2e.core.interactive_doctor import (
    AppliedFix,
    AutoFixer,
    DiagnosisResult,
    DoctorSession,
    ErrorAnalyzer,
    ErrorContext,
    ErrorType,
    FixStrategy,
    FixSuggester,
    FixSuggestion,
    InteractiveDoctor,
    MissingFieldDetails,
    TypeMismatchDetails,
    ValidationErrorDetails,
    run_interactive_doctor,
)

# Core - Visual Traceability
from socialseed_e2e.core.traceability import (
    Component,
    Interaction,
    InteractionType,
    LogicBranch,
    LogicBranchType,
    LogicFlow,
    LogicMapper,
    SequenceDiagram,
    SequenceDiagramGenerator,
    TestTrace,
    TraceCollector,
    TraceConfig,
    TraceContext,
    TraceReport,
    TraceReporter,
    create_collector,
    disable_traceability,
    enable_traceability,
    end_test_trace,
    get_global_collector,
    record_interaction,
    record_logic_branch,
    set_global_collector,
    start_test_trace,
    trace_assertion,
    trace_http_request,
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
    # Core - gRPC Support
    "BaseGrpcPage",
    "GrpcRetryConfig",
    "GrpcCallLog",
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
    # Utils - Pydantic (Universal)
    "APIModel",
    "api_field",
    "NamingConvention",
    "detect_naming_convention",
    "camel_field",
    "pascal_field",
    "snake_field",
    "to_camel_case",
    "to_pascal_case",
    "to_snake_case",
    "to_kebab_case",
    "to_api_dict",
    "validate_api_model",
    "refresh_token_field",
    "access_token_field",
    "user_name_field",
    "user_id_field",
    "created_at_field",
    "updated_at_field",
    "new_password_field",
    "current_password_field",
    # Utils - Pydantic (Backwards compatibility)
    "JavaCompatibleModel",
    "to_camel_dict",
    "validate_camelcase_model",
    # Utils - Validators
    "ValidationError",
    "validate_url",
    "validate_base_url",
    "validate_email",
    "validate_uuid",
    # Utils - Proto Schema (gRPC)
    "ProtoSchemaHandler",
    "ProtoRegistry",
    # Utils - Templates
    "TemplateEngine",
    "to_class_name",
    "template_to_snake_case",
    "template_to_camel_case",
    # Core - Visual Traceability
    "TraceCollector",
    "TraceReporter",
    "SequenceDiagramGenerator",
    "LogicMapper",
    "TestTrace",
    "TraceConfig",
    "TraceReport",
    "Component",
    "Interaction",
    "InteractionType",
    "LogicBranch",
    "LogicBranchType",
    "LogicFlow",
    "SequenceDiagram",
    "enable_traceability",
    "disable_traceability",
    "TraceContext",
    "start_test_trace",
    "end_test_trace",
    "record_interaction",
    "record_logic_branch",
    "trace_http_request",
    "trace_assertion",
    "get_global_collector",
    "set_global_collector",
    "create_collector",
    # Core - Interactive Doctor
    "InteractiveDoctor",
    "ErrorAnalyzer",
    "FixSuggester",
    "AutoFixer",
    "ErrorContext",
    "DiagnosisResult",
    "FixSuggestion",
    "AppliedFix",
    "DoctorSession",
    "ErrorType",
    "FixStrategy",
    "TypeMismatchDetails",
    "MissingFieldDetails",
    "ValidationErrorDetails",
    "run_interactive_doctor",
]
