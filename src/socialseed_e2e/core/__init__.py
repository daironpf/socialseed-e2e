"""
Core Engine - Motor agnóstico de testing E2E.

Este módulo proporciona las clases y funciones principales del framework.
Todo es agnóstico de servicios específicos.
"""

from .base_page import BasePage
from .base_websocket_page import (
    WEBSOCKET_AVAILABLE,
    BaseWebSocketPage,
    WebSocketConfig,
    WebSocketError,
    WebSocketLog,
    WebSocketMessage,
)
from .config_loader import (
    ApiConfigLoader,
    get_config,
    get_service_config,
    get_service_url,
)
from .headers import DEFAULT_BROWSER_HEADERS, DEFAULT_JSON_HEADERS, get_combined_headers
from .interfaces import IServicePage, ITestModule
from .loaders import ModuleLoader
from .models import ServiceConfig, TestContext
from .parallel_runner import ParallelConfig, run_tests_parallel
from .test_orchestrator import TestOrchestrator

__all__ = [
    # Clases principales
    "BasePage",
    "BaseWebSocketPage",
    "ApiConfigLoader",
    "ModuleLoader",
    "TestOrchestrator",
    "ServiceConfig",
    "TestContext",
    # WebSocket support
    "WebSocketConfig",
    "WebSocketMessage",
    "WebSocketLog",
    "WebSocketError",
    "WEBSOCKET_AVAILABLE",
    # Parallel execution
    "ParallelConfig",
    "run_tests_parallel",
    # Interfaces
    "IServicePage",
    "ITestModule",
    # Funciones utilitarias
    "get_config",
    "get_service_config",
    "get_service_url",
    # Constants
    "DEFAULT_JSON_HEADERS",
    "DEFAULT_BROWSER_HEADERS",
    "get_combined_headers",
]
