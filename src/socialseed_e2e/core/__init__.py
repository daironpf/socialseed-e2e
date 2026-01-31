"""
Core Engine - Motor agnóstico de testing E2E.

Este módulo proporciona las clases y funciones principales del framework.
Todo es agnóstico de servicios específicos.
"""

from .base_page import BasePage
from .config_loader import ApiConfigLoader, get_config, get_service_config, get_service_url
from .loaders import ModuleLoader
from .test_orchestrator import TestOrchestrator
from .models import ServiceConfig, TestContext
from .interfaces import IServicePage, ITestModule
from .headers import DEFAULT_JSON_HEADERS, DEFAULT_BROWSER_HEADERS, get_combined_headers

__all__ = [
    # Clases principales
    "BasePage",
    "ApiConfigLoader",
    "ModuleLoader",
    "TestOrchestrator",
    "ServiceConfig",
    "TestContext",
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
