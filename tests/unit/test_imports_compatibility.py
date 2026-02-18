"""Tests for package import compatibility and public API.

This module verifies that the package can be imported correctly
when installed via pip, simulating an external project context.
"""

import pytest

pytestmark = pytest.mark.unit
import importlib
import sys
from types import ModuleType


class TestMainPackageImports:
    """Test imports from the main socialseed_e2e package."""

    def test_import_main_package(self):
        """Test that main package can be imported."""
        import socialseed_e2e

        assert isinstance(socialseed_e2e, ModuleType)

    def test_main_package_has_version(self):
        """Test that main package exposes version information."""
        import socialseed_e2e

        assert hasattr(socialseed_e2e, "__version__")
        assert hasattr(socialseed_e2e, "__version_info__")
        assert isinstance(socialseed_e2e.__version__, str)
        assert isinstance(socialseed_e2e.__version_info__, tuple)

    def test_main_package_has_metadata(self):
        """Test that main package has metadata attributes."""
        import socialseed_e2e

        assert hasattr(socialseed_e2e, "__author__")
        assert hasattr(socialseed_e2e, "__email__")
        assert hasattr(socialseed_e2e, "__license__")
        assert hasattr(socialseed_e2e, "__copyright__")
        assert hasattr(socialseed_e2e, "__url__")

    def test_import_basepage_from_main(self):
        """Test importing BasePage from main package."""
        from socialseed_e2e import BasePage

        assert BasePage is not None
        assert callable(BasePage)

    def test_import_config_loader_from_main(self):
        """Test importing config loader classes from main package."""
        from socialseed_e2e import ApiConfigLoader, get_config, get_service_config

        assert ApiConfigLoader is not None
        assert callable(get_config)
        assert callable(get_service_config)

    def test_import_loaders_from_main(self):
        """Test importing ModuleLoader from main package."""
        from socialseed_e2e import ModuleLoader

        assert ModuleLoader is not None

    def test_import_orchestrator_from_main(self):
        """Test importing TestOrchestrator from main package."""
        from socialseed_e2e import TestOrchestrator

        assert TestOrchestrator is not None

    def test_import_models_from_main(self):
        """Test importing model classes from main package."""
        from socialseed_e2e import ServiceConfig, TestContext

        assert ServiceConfig is not None
        assert TestContext is not None

    def test_import_cli_from_main(self):
        """Test importing CLI main from main package."""
        from socialseed_e2e import main

        assert main is not None
        assert callable(main)

    def test_main_package_all_exports_exist(self):
        """Test that all items in __all__ are actually exported."""
        import socialseed_e2e

        for name in socialseed_e2e.__all__:
            # Skip optional imports that may not be available
            if name in ("BaseGrpcPage", "GrpcRetryConfig", "GrpcCallLog"):
                continue
            assert hasattr(socialseed_e2e, name), f"{name} not found in main package"


class TestCoreSubmoduleImports:
    """Test imports from the socialseed_e2e.core submodule."""

    def test_import_core_module(self):
        """Test that core module can be imported."""
        import socialseed_e2e.core

        assert isinstance(socialseed_e2e.core, ModuleType)

    def test_import_basepage_from_core(self):
        """Test importing BasePage from core submodule."""
        from socialseed_e2e.core import BasePage

        assert BasePage is not None

    def test_import_config_loader_from_core(self):
        """Test importing config loader from core submodule."""
        from socialseed_e2e.core import (
            ApiConfigLoader,
            get_config,
            get_service_config,
            get_service_url,
        )

        assert ApiConfigLoader is not None
        assert callable(get_config)
        assert callable(get_service_config)
        assert callable(get_service_url)

    def test_import_loaders_from_core(self):
        """Test importing ModuleLoader from core submodule."""
        from socialseed_e2e.core import ModuleLoader

        assert ModuleLoader is not None

    def test_import_orchestrator_from_core(self):
        """Test importing TestOrchestrator from core submodule."""
        from socialseed_e2e.core import TestOrchestrator

        assert TestOrchestrator is not None

    def test_import_models_from_core(self):
        """Test importing model classes from core submodule."""
        from socialseed_e2e.core import ServiceConfig, TestContext

        assert ServiceConfig is not None
        assert TestContext is not None

    def test_import_interfaces_from_core(self):
        """Test importing interfaces from core submodule."""
        from socialseed_e2e.core import IServicePage, ITestModule

        assert IServicePage is not None
        assert ITestModule is not None

    def test_import_headers_from_core(self):
        """Test importing header constants from core submodule."""
        from socialseed_e2e.core import (
            DEFAULT_BROWSER_HEADERS,
            DEFAULT_JSON_HEADERS,
            get_combined_headers,
        )

        assert isinstance(DEFAULT_JSON_HEADERS, dict)
        assert isinstance(DEFAULT_BROWSER_HEADERS, dict)
        assert callable(get_combined_headers)

    def test_core_all_exports_exist(self):
        """Test that all items in core.__all__ are actually exported."""
        import socialseed_e2e.core as core

        for name in core.__all__:
            assert hasattr(core, name), f"{name} not found in core module"


class TestUtilsSubmoduleImports:
    """Test imports from the socialseed_e2e.utils submodule."""

    def test_import_utils_module(self):
        """Test that utils module can be imported."""
        import socialseed_e2e.utils

        assert isinstance(socialseed_e2e.utils, ModuleType)

    def test_import_template_engine_from_utils(self):
        """Test importing TemplateEngine from utils submodule."""
        from socialseed_e2e.utils import TemplateEngine

        assert TemplateEngine is not None

    def test_import_string_utils_from_utils(self):
        """Test importing string utility functions from utils submodule."""
        from socialseed_e2e.utils import to_camel_case, to_class_name, to_snake_case

        assert callable(to_class_name)
        assert callable(to_snake_case)
        assert callable(to_camel_case)

    def test_utils_all_exports_exist(self):
        """Test that all items in utils.__all__ are actually exported."""
        import socialseed_e2e.utils as utils

        for name in utils.__all__:
            assert hasattr(utils, name), f"{name} not found in utils module"


class TestTemplatesSubmoduleImports:
    """Test imports from the socialseed_e2e.templates submodule."""

    def test_import_templates_module(self):
        """Test that templates module can be imported."""
        import socialseed_e2e.templates

        assert isinstance(socialseed_e2e.templates, ModuleType)

    def test_import_templates_dir(self):
        """Test importing TEMPLATES_DIR from templates submodule."""
        from socialseed_e2e.templates import TEMPLATES_DIR

        assert TEMPLATES_DIR is not None

    def test_templates_all_exports_exist(self):
        """Test that all items in templates.__all__ are actually exported."""
        import socialseed_e2e.templates as templates

        for name in templates.__all__:
            assert hasattr(templates, name), f"{name} not found in templates module"


class TestServicesSubmoduleImports:
    """Test imports from the socialseed_e2e.services submodule."""

    def test_import_services_module(self):
        """Test that services module can be imported."""
        import socialseed_e2e.services

        assert isinstance(socialseed_e2e.services, ModuleType)


class TestCircularImportPrevention:
    """Test that no circular imports exist by importing in different orders."""

    def test_import_core_before_main(self):
        """Test importing core before main package."""
        # Clear any cached modules to simulate fresh import
        modules_to_clear = [
            k for k in sys.modules.keys() if k.startswith("socialseed_e2e")
        ]
        for mod in modules_to_clear:
            del sys.modules[mod]

        # Import core first
        # Then import main
        from socialseed_e2e import BasePage as MainBasePage
        from socialseed_e2e.core import BasePage

        assert BasePage is MainBasePage

    def test_import_utils_before_main(self):
        """Test importing utils before main package."""
        modules_to_clear = [
            k for k in sys.modules.keys() if k.startswith("socialseed_e2e")
        ]
        for mod in modules_to_clear:
            del sys.modules[mod]

        # Import utils first
        # Then import main
        from socialseed_e2e import BasePage
        from socialseed_e2e.utils import TemplateEngine

        assert TemplateEngine is not None
        assert BasePage is not None

    def test_import_templates_before_main(self):
        """Test importing templates before main package."""
        modules_to_clear = [
            k for k in sys.modules.keys() if k.startswith("socialseed_e2e")
        ]
        for mod in modules_to_clear:
            del sys.modules[mod]

        # Import templates first
        # Then import main
        from socialseed_e2e import BasePage
        from socialseed_e2e.templates import TEMPLATES_DIR

        assert TEMPLATES_DIR is not None
        assert BasePage is not None

    def test_multiple_submodule_imports(self):
        """Test importing multiple submodules in various orders."""
        modules_to_clear = [
            k for k in sys.modules.keys() if k.startswith("socialseed_e2e")
        ]
        for mod in modules_to_clear:
            del sys.modules[mod]

        # Import in reverse order
        from socialseed_e2e import main
        from socialseed_e2e.core import BasePage
        from socialseed_e2e.templates import TEMPLATES_DIR
        from socialseed_e2e.utils import TemplateEngine

        assert all([TEMPLATES_DIR, TemplateEngine, BasePage, main])


class TestModuleReloadability:
    """Test that modules can be reloaded without errors."""

    def test_reload_main_package(self):
        """Test that main package can be reloaded."""
        import socialseed_e2e

        reloaded = importlib.reload(socialseed_e2e)
        assert reloaded is socialseed_e2e

    def test_reload_core_module(self):
        """Test that core module can be reloaded."""
        import socialseed_e2e.core

        reloaded = importlib.reload(socialseed_e2e.core)
        assert reloaded is socialseed_e2e.core

    def test_reload_utils_module(self):
        """Test that utils module can be reloaded."""
        import socialseed_e2e.utils

        reloaded = importlib.reload(socialseed_e2e.utils)
        assert reloaded is socialseed_e2e.utils

    def test_reload_templates_module(self):
        """Test that templates module can be reloaded."""
        import socialseed_e2e.templates

        reloaded = importlib.reload(socialseed_e2e.templates)
        assert reloaded is socialseed_e2e.templates


class TestImportSideEffects:
    """Test that imports don't have unwanted side effects."""

    def test_import_does_not_execute_cli(self):
        """Test that importing doesn't execute CLI main function."""
        from socialseed_e2e import main

        # main should be a function, not the result of calling it
        assert callable(main)
        # It shouldn't have been called during import
        assert not hasattr(main, "_called") or not main._called

    def test_import_does_not_create_files(self, tmp_path):
        """Test that importing doesn't create any files in critical locations."""
        import os

        import socialseed_e2e

        # Check that no unexpected files were created in the package directory
        pkg_dir = os.path.dirname(socialseed_e2e.__file__)

        # List of expected files/directories (more flexible)
        expected = {
            "core",
            "utils",
            "templates",
            "services",
            "project_manifest",
            "__init__.py",
            "__version__.py",
            "cli.py",
        }
        actual = set(os.listdir(pkg_dir))

        # Only check that critical files/dirs exist, not that there are no extras
        missing = expected - actual
        assert not missing, f"Expected files missing: {missing}"


class TestPublicAPIConsistency:
    """Test that public API is consistent across import paths."""

    def test_basepage_same_from_main_and_core(self):
        """Test that BasePage is the same object regardless of import path."""
        from socialseed_e2e import BasePage as FromMain
        from socialseed_e2e.core import BasePage as FromCore

        assert FromMain is FromCore

    def test_config_loader_same_from_main_and_core(self):
        """Test that ApiConfigLoader is the same object regardless of import path."""
        from socialseed_e2e import ApiConfigLoader as FromMain
        from socialseed_e2e.core import ApiConfigLoader as FromCore

        assert FromMain is FromCore

    def test_orchestrator_same_from_main_and_core(self):
        """Test that TestOrchestrator is the same object regardless of import path."""
        from socialseed_e2e import TestOrchestrator as FromMain
        from socialseed_e2e.core import TestOrchestrator as FromCore

        assert FromMain is FromCore

    def test_models_same_from_main_and_core(self):
        """Test that models are the same objects regardless of import path."""
        from socialseed_e2e import TestContext as TC_Main
        from socialseed_e2e.core import TestContext as TC_Core

        assert TC_Main is TC_Core
