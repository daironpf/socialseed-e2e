"""
Core Engine - Motor agnóstico de testing E2E.

Este módulo proporciona las clases y funciones principales del framework.
Todo es agnóstico de servicios específicos.
"""

from .base_page import BasePage
from .config_loader import ApiConfigLoader, get_config, get_service_config, get_service_url
from .headers import DEFAULT_BROWSER_HEADERS, DEFAULT_JSON_HEADERS, get_combined_headers
from .interfaces import IServicePage, ITestModule
from .loaders import ModuleLoader
from .models import ServiceConfig, TestContext
from .test_orchestrator import TestOrchestrator

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
