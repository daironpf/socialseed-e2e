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

Uso básico:
    >>> from socialseed_e2e import BasePage, ApiConfigLoader
    >>> config = ApiConfigLoader.load()
    >>> page = BasePage(config.base_url)
    >>> response = page.get("/endpoint")

Para más información, visita: https://github.com/daironpf/socialseed-e2e
"""

__version__ = "0.1.0"
__version_info__ = (0, 1, 0)
__author__ = "Dairon Pérez Frías"
__email__ = "dairon.perezfrias@gmail.com"
__license__ = "MIT"
__copyright__ = "Copyright 2026 Dairon Pérez Frías"
__url__ = "https://github.com/daironpf/socialseed-e2e"

# Hacer disponibles las clases principales
from socialseed_e2e.core.base_page import BasePage
from socialseed_e2e.core.config_loader import (
    ApiConfigLoader,
    get_config,
    get_service_config,
)
from socialseed_e2e.core.loaders import ModuleLoader
from socialseed_e2e.core.test_orchestrator import TestOrchestrator
from socialseed_e2e.core.models import ServiceConfig, TestContext
from socialseed_e2e.cli import main

__all__ = [
    "BasePage",
    "ApiConfigLoader",
    "get_config",
    "get_service_config",
    "ModuleLoader",
    "TestOrchestrator",
    "ServiceConfig",
    "TestContext",
    "main",
    "__version__",
]
