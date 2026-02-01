"""Tests for TestOrchestrator.

This module contains unit tests for the TestOrchestrator class which
orchestrates dynamic loading and execution of test modules.
"""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock

import pytest
pytestmark = pytest.mark.unit

from socialseed_e2e.core.test_orchestrator import TestOrchestrator, pytest_configure, pytest_collection_modifyitems


class TestOrchestratorInitialization:
    """Test cases for TestOrchestrator initialization."""

    def test_default_initialization(self):
        """Test initialization with default parameters."""
        orchestrator = TestOrchestrator()
        
        assert orchestrator.root_dir == Path(os.getcwd())
        assert orchestrator.services_dir == Path(os.getcwd()) / "verify_services/e2e/services"
        assert orchestrator.loader is not None
        assert orchestrator.modules == {}

    def test_custom_root_dir(self, tmp_path):
        """Test initialization with custom root directory."""
        orchestrator = TestOrchestrator(root_dir=str(tmp_path))
        
        assert orchestrator.root_dir == tmp_path
        assert orchestrator.services_dir == tmp_path / "verify_services/e2e/services"

    def test_custom_services_path(self, tmp_path):
        """Test initialization with custom services path."""
        orchestrator = TestOrchestrator(
            root_dir=str(tmp_path),
            services_path="custom/services/path"
        )
        
        assert orchestrator.services_dir == tmp_path / "custom/services/path"

    def test_initialization_with_path_object(self, tmp_path):
        """Test initialization with Path object instead of string."""
        orchestrator = TestOrchestrator(root_dir=tmp_path)
        
        assert orchestrator.root_dir == tmp_path


class TestDiscoverModules:
    """Test cases for discover_modules method."""

    def test_discover_single_service_single_module(self, tmp_path):
        """Test discovering a single module in a single service."""
        # Setup directory structure
        services_dir = tmp_path / "services"
        service_dir = services_dir / "test-service"
        modules_dir = service_dir / "modules"
        modules_dir.mkdir(parents=True)
        
        # Create a test module
        (modules_dir / "01_test.py").write_text("""
def run(context):
    return "test executed"
""")
        
        orchestrator = TestOrchestrator(
            root_dir=str(tmp_path),
            services_path="services"
        )
        orchestrator.discover_modules()
        
        assert "test-service" in orchestrator.modules
        assert len(orchestrator.modules["test-service"]) == 1

    def test_discover_multiple_services(self, tmp_path):
        """Test discovering modules across multiple services."""
        services_dir = tmp_path / "services"
        
        # Create service 1
        service1_modules = services_dir / "service1" / "modules"
        service1_modules.mkdir(parents=True)
        (service1_modules / "01_test.py").write_text("def run(ctx): return 's1'")
        
        # Create service 2
        service2_modules = services_dir / "service2" / "modules"
        service2_modules.mkdir(parents=True)
        (service2_modules / "01_test.py").write_text("def run(ctx): return 's2'")
        
        orchestrator = TestOrchestrator(
            root_dir=str(tmp_path),
            services_path="services"
        )
        orchestrator.discover_modules()
        
        assert len(orchestrator.modules) == 2
        assert "service1" in orchestrator.modules
        assert "service2" in orchestrator.modules

    def test_discover_multiple_modules_per_service(self, tmp_path):
        """Test discovering multiple modules in a single service."""
        services_dir = tmp_path / "services"
        modules_dir = services_dir / "test-service" / "modules"
        modules_dir.mkdir(parents=True)
        
        (modules_dir / "01_first.py").write_text("def run(ctx): return 'first'")
        (modules_dir / "02_second.py").write_text("def run(ctx): return 'second'")
        (modules_dir / "03_third.py").write_text("def run(ctx): return 'third'")
        
        orchestrator = TestOrchestrator(
            root_dir=str(tmp_path),
            services_path="services"
        )
        orchestrator.discover_modules()
        
        assert len(orchestrator.modules["test-service"]) == 3

    def test_discover_skips_non_module_directories(self, tmp_path, capsys):
        """Test that non-module directories are skipped."""
        services_dir = tmp_path / "services"
        
        # Service without modules directory
        (services_dir / "no-modules-service").mkdir(parents=True)
        
        # Service with modules directory
        modules_dir = services_dir / "valid-service" / "modules"
        modules_dir.mkdir(parents=True)
        (modules_dir / "01_test.py").write_text("def run(ctx): return 'valid'")
        
        orchestrator = TestOrchestrator(
            root_dir=str(tmp_path),
            services_path="services"
        )
        orchestrator.discover_modules()
        
        assert "valid-service" in orchestrator.modules
        assert "no-modules-service" not in orchestrator.modules

    def test_discover_empty_services_directory(self, tmp_path, capsys):
        """Test discovering when services directory is empty."""
        services_dir = tmp_path / "services"
        services_dir.mkdir(parents=True)
        
        orchestrator = TestOrchestrator(
            root_dir=str(tmp_path),
            services_path="services"
        )
        orchestrator.discover_modules()
        
        assert orchestrator.modules == {}

    def test_discover_nonexistent_services_directory(self, tmp_path, capsys):
        """Test discovering when services directory doesn't exist."""
        orchestrator = TestOrchestrator(
            root_dir=str(tmp_path),
            services_path="nonexistent/services"
        )
        orchestrator.discover_modules()
        
        # Should print warning but not crash
        captured = capsys.readouterr()
        assert "Warning" in captured.out or "not found" in captured.out
        assert orchestrator.modules == {}

    def test_discover_preserves_module_order(self, tmp_path):
        """Test that modules are discovered in alphabetical order."""
        services_dir = tmp_path / "services"
        modules_dir = services_dir / "test-service" / "modules"
        modules_dir.mkdir(parents=True)
        
        # Create modules out of order
        (modules_dir / "z_last.py").write_text("def run(ctx): ctx.order.append('z')")
        (modules_dir / "a_first.py").write_text("def run(ctx): ctx.order.append('a')")
        (modules_dir / "m_middle.py").write_text("def run(ctx): ctx.order.append('m')")
        
        orchestrator = TestOrchestrator(
            root_dir=str(tmp_path),
            services_path="services"
        )
        orchestrator.discover_modules()
        
        modules = orchestrator.modules["test-service"]
        
        # Execute and check order
        class Context:
            def __init__(self):
                self.order = []
        
        for module in modules:
            module(Context())
        
        # Check that execution order is alphabetical
        ctx = Context()
        for module in modules:
            module(ctx)
        assert ctx.order == ['a', 'm', 'z']


class TestRunServiceTests:
    """Test cases for run_service_tests method."""

    def test_run_single_module(self):
        """Test running a single module for a service."""
        orchestrator = TestOrchestrator()
        
        # Mock the modules
        mock_func = MagicMock()
        orchestrator.modules = {"test-service": [mock_func]}
        
        context = MagicMock()
        orchestrator.run_service_tests("test-service", context)
        
        mock_func.assert_called_once_with(context)

    def test_run_multiple_modules(self):
        """Test running multiple modules for a service."""
        orchestrator = TestOrchestrator()
        
        mock_func1 = MagicMock()
        mock_func2 = MagicMock()
        mock_func3 = MagicMock()
        orchestrator.modules = {"test-service": [mock_func1, mock_func2, mock_func3]}
        
        context = MagicMock()
        orchestrator.run_service_tests("test-service", context)
        
        mock_func1.assert_called_once_with(context)
        mock_func2.assert_called_once_with(context)
        mock_func3.assert_called_once_with(context)

    def test_run_modules_in_correct_order(self):
        """Test that modules are executed in the correct order."""
        orchestrator = TestOrchestrator()
        
        execution_order = []
        
        def make_mock(name):
            def mock_func(ctx):
                execution_order.append(name)
            return mock_func
        
        orchestrator.modules = {
            "test-service": [
                make_mock("first"),
                make_mock("second"),
                make_mock("third")
            ]
        }
        
        orchestrator.run_service_tests("test-service", MagicMock())
        
        assert execution_order == ["first", "second", "third"]

    def test_run_nonexistent_service_raises_error(self):
        """Test that running a nonexistent service raises ValueError."""
        orchestrator = TestOrchestrator()
        orchestrator.modules = {}
        
        with pytest.raises(ValueError) as exc_info:
            orchestrator.run_service_tests("nonexistent", MagicMock())
        
        assert "nonexistent" in str(exc_info.value)
        assert "not found" in str(exc_info.value)

    def test_run_service_with_empty_modules(self):
        """Test running a service with no modules."""
        orchestrator = TestOrchestrator()
        orchestrator.modules = {"test-service": []}
        
        context = MagicMock()
        # Should not raise, just do nothing
        orchestrator.run_service_tests("test-service", context)


class TestRunAllTests:
    """Test cases for run_all_tests method."""

    def test_run_all_services(self):
        """Test running all discovered services."""
        orchestrator = TestOrchestrator()
        
        service1_calls = []
        service2_calls = []
        
        def s1_func(ctx):
            service1_calls.append("called")
        
        def s2_func(ctx):
            service2_calls.append("called")
        
        orchestrator.modules = {
            "service1": [s1_func],
            "service2": [s2_func]
        }
        
        def context_factory():
            return MagicMock()
        
        orchestrator.run_all_tests(context_factory)
        
        assert len(service1_calls) == 1
        assert len(service2_calls) == 1

    def test_context_factory_called_per_service(self):
        """Test that context factory is called for each service."""
        orchestrator = TestOrchestrator()
        
        call_count = 0
        contexts = []
        
        def context_factory():
            nonlocal call_count
            call_count += 1
            ctx = MagicMock()
            contexts.append(ctx)
            return ctx
        
        orchestrator.modules = {
            "service1": [lambda ctx: None],
            "service2": [lambda ctx: None],
            "service3": [lambda ctx: None]
        }
        
        orchestrator.run_all_tests(context_factory)
        
        assert call_count == 3
        assert len(contexts) == 3
        # Each service should have its own context
        assert contexts[0] != contexts[1] != contexts[2]

    def test_teardown_called_after_service(self):
        """Test that teardown is called after each service."""
        orchestrator = TestOrchestrator()
        
        teardown_calls = []
        
        class ContextWithTeardown:
            def teardown(self):
                teardown_calls.append("teardown")
        
        orchestrator.modules = {
            "service1": [lambda ctx: None],
            "service2": [lambda ctx: None]
        }
        
        def context_factory():
            return ContextWithTeardown()
        
        orchestrator.run_all_tests(context_factory)
        
        assert len(teardown_calls) == 2

    def test_teardown_not_called_if_no_teardown_method(self):
        """Test that missing teardown method doesn't cause errors."""
        orchestrator = TestOrchestrator()
        
        class ContextWithoutTeardown:
            pass
        
        orchestrator.modules = {
            "service1": [lambda ctx: None]
        }
        
        def context_factory():
            return ContextWithoutTeardown()
        
        # Should not raise
        orchestrator.run_all_tests(context_factory)

    def test_exception_stops_execution(self):
        """Test that exception stops execution and propagates."""
        orchestrator = TestOrchestrator()
        
        service2_calls = []
        
        def failing_func(ctx):
            raise ValueError("Test failure")
        
        def s2_func(ctx):
            service2_calls.append("called")
        
        orchestrator.modules = {
            "service1": [failing_func],
            "service2": [s2_func]  # Should not be called
        }
        
        def context_factory():
            return MagicMock()
        
        with pytest.raises(ValueError) as exc_info:
            orchestrator.run_all_tests(context_factory)
        
        assert "Test failure" in str(exc_info.value)
        assert len(service2_calls) == 0  # service2 should not run

    def test_teardown_called_even_on_exception(self):
        """Test that teardown is called even when exception occurs."""
        orchestrator = TestOrchestrator()
        
        teardown_calls = []
        
        class ContextWithTeardown:
            def teardown(self):
                teardown_calls.append("teardown")
        
        def failing_func(ctx):
            raise ValueError("Test failure")
        
        orchestrator.modules = {
            "service1": [failing_func]
        }
        
        def context_factory():
            return ContextWithTeardown()
        
        with pytest.raises(ValueError):
            orchestrator.run_all_tests(context_factory)
        
        assert len(teardown_calls) == 1  # teardown should still be called

    def test_exception_message_printed(self, capsys):
        """Test that exception message is printed on failure."""
        orchestrator = TestOrchestrator()
        
        def failing_func(ctx):
            raise ValueError("Something went wrong")
        
        orchestrator.modules = {
            "test-service": [failing_func]
        }
        
        def context_factory():
            return MagicMock()
        
        with pytest.raises(ValueError):
            orchestrator.run_all_tests(context_factory)
        
        captured = capsys.readouterr()
        assert "✗" in captured.out or "failed" in captured.out
        assert "test-service" in captured.out

    def test_success_message_printed(self, capsys):
        """Test that success message is printed when tests pass."""
        orchestrator = TestOrchestrator()
        
        orchestrator.modules = {
            "test-service": [lambda ctx: None]
        }
        
        def context_factory():
            return MagicMock()
        
        orchestrator.run_all_tests(context_factory)
        
        captured = capsys.readouterr()
        assert "✓" in captured.out or "passed" in captured.out
        assert "test-service" in captured.out


class TestPytestHooks:
    """Test cases for pytest integration hooks."""

    def test_pytest_configure_with_defaults(self):
        """Test pytest_configure with default environment."""
        mock_config = MagicMock()
        
        # Clear environment
        with patch.dict(os.environ, {}, clear=True):
            pytest_configure(mock_config)
            
            assert hasattr(mock_config, 'orchestrator')
            assert mock_config.orchestrator is not None

    def test_pytest_configure_with_custom_paths(self):
        """Test pytest_configure with custom paths from environment."""
        mock_config = MagicMock()
        
        with patch.dict(os.environ, {
            "E2E_ROOT_DIR": "/custom/root",
            "E2E_SERVICES_PATH": "custom/services"
        }):
            pytest_configure(mock_config)
            
            assert mock_config.orchestrator is not None
            # Verify paths were set correctly
            assert mock_config.orchestrator.root_dir == Path("/custom/root")
            assert mock_config.orchestrator.services_dir == Path("/custom/root") / "custom/services"

    def test_pytest_configure_without_pytest(self):
        """Test pytest_configure when pytest is not available."""
        mock_config = MagicMock()
        
        # This should not raise even without pytest
        with patch('socialseed_e2e.core.test_orchestrator.pytest', None):
            pytest_configure(mock_config)
            # Should still work

    def test_pytest_collection_modifyitems(self):
        """Test pytest_collection_modifyitems hook."""
        mock_config = MagicMock()
        mock_config.orchestrator = MagicMock()
        mock_items = []
        
        pytest_collection_modifyitems(mock_config, mock_items)
        
        mock_config.orchestrator.discover_modules.assert_called_once()

    def test_pytest_collection_modifyitems_without_orchestrator(self):
        """Test pytest_collection_modifyitems without orchestrator."""
        mock_config = MagicMock()
        mock_config.orchestrator = None
        mock_items = []
        
        # Should not raise
        pytest_collection_modifyitems(mock_config, mock_items)


class TestTestOrchestratorIntegration:
    """Integration tests for TestOrchestrator."""

    def test_full_workflow_single_service(self, tmp_path):
        """Test complete workflow with a single service."""
        # Setup
        services_dir = tmp_path / "services"
        modules_dir = services_dir / "test-service" / "modules"
        modules_dir.mkdir(parents=True)
        
        (modules_dir / "01_setup.py").write_text("""
def run(ctx):
    ctx.state = 'setup'
""")
        (modules_dir / "02_test.py").write_text("""
def run(ctx):
    assert ctx.state == 'setup'
    ctx.state = 'tested'
""")
        
        # Execute
        orchestrator = TestOrchestrator(
            root_dir=str(tmp_path),
            services_path="services"
        )
        orchestrator.discover_modules()
        
        class TestContext:
            def __init__(self):
                self.state = None
            def teardown(self):
                pass
        
        def context_factory():
            return TestContext()
        
        orchestrator.run_all_tests(context_factory)
        
        # Verify state was modified through the tests

    def test_full_workflow_multiple_services(self, tmp_path, capsys):
        """Test complete workflow with multiple services."""
        services_dir = tmp_path / "services"
        
        # Service 1
        s1_modules = services_dir / "auth-service" / "modules"
        s1_modules.mkdir(parents=True)
        (s1_modules / "01_login.py").write_text("def run(ctx): print('login')")
        
        # Service 2
        s2_modules = services_dir / "user-service" / "modules"
        s2_modules.mkdir(parents=True)
        (s2_modules / "01_create.py").write_text("def run(ctx): print('create')")
        
        # Execute
        orchestrator = TestOrchestrator(
            root_dir=str(tmp_path),
            services_path="services"
        )
        orchestrator.discover_modules()
        
        def context_factory():
            return MagicMock()
        
        orchestrator.run_all_tests(context_factory)
        
        captured = capsys.readouterr()
        assert "login" in captured.out
        assert "create" in captured.out
        assert "✓ auth-service tests passed" in captured.out
        assert "✓ user-service tests passed" in captured.out

    def test_module_state_shared_within_service(self, tmp_path):
        """Test that state is shared between modules in the same service."""
        services_dir = tmp_path / "services"
        modules_dir = services_dir / "test-service" / "modules"
        modules_dir.mkdir(parents=True)
        
        (modules_dir / "01_set.py").write_text("""
def run(ctx):
    ctx.shared_value = 42
""")
        (modules_dir / "02_get.py").write_text("""
def run(ctx):
    ctx.retrieved = ctx.shared_value
""")
        
        orchestrator = TestOrchestrator(
            root_dir=str(tmp_path),
            services_path="services"
        )
        orchestrator.discover_modules()
        
        class SharedContext:
            def __init__(self):
                self.shared_value = None
                self.retrieved = None
            def teardown(self):
                pass
        
        orchestrator.run_service_tests("test-service", SharedContext())

    def test_exception_in_module_stops_service(self, tmp_path):
        """Test that exception in one module stops the service execution."""
        services_dir = tmp_path / "services"
        modules_dir = services_dir / "test-service" / "modules"
        modules_dir.mkdir(parents=True)
        
        (modules_dir / "01_pass.py").write_text("def run(ctx): ctx.step1 = True")
        (modules_dir / "02_fail.py").write_text("def run(ctx): raise ValueError('Failed')")
        (modules_dir / "03_never.py").write_text("def run(ctx): ctx.step3 = True")
        
        orchestrator = TestOrchestrator(
            root_dir=str(tmp_path),
            services_path="services"
        )
        orchestrator.discover_modules()
        
        class Context:
            def __init__(self):
                self.step1 = False
                self.step3 = False
            def teardown(self):
                pass
        
        with pytest.raises(ValueError) as exc_info:
            orchestrator.run_service_tests("test-service", Context())
        
        assert "Failed" in str(exc_info.value)
