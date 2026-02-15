"""Test runner implementation for socialseed-e2e framework.

This module provides the actual test execution logic for the e2e run command.
"""

import importlib
import importlib.util
import sys
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Type

from playwright.sync_api import sync_playwright
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from socialseed_e2e.ai_learning import FeedbackCollector, FeedbackType
from socialseed_e2e.core.base_page import BasePage
from socialseed_e2e.core.config_loader import (
    ApiConfigLoader,
    ServiceConfig,
    get_service_config,
)
from socialseed_e2e.core.organization import Priority, TestOrganizationManager

# Global feedback collector instance
_feedback_collector: Optional[FeedbackCollector] = None


def get_feedback_collector() -> FeedbackCollector:
    """Get or create the global feedback collector instance."""
    global _feedback_collector
    if _feedback_collector is None:
        _feedback_collector = FeedbackCollector()
    return _feedback_collector


def set_feedback_collector(collector: FeedbackCollector):
    """Set the global feedback collector instance."""
    global _feedback_collector
    _feedback_collector = collector


console = Console()


@dataclass
class TestResult:
    """Result of a single test execution."""

    name: str
    service: str
    status: str  # "passed", "failed", "skipped", "error"
    duration_ms: float = 0.0
    error_message: str = ""
    error_traceback: str = ""


@dataclass
class TestSuiteResult:
    """Result of a complete test suite execution."""

    total: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: int = 0
    total_duration_ms: float = 0.0
    results: List[TestResult] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return (self.passed / self.total) * 100


class TestDiscoveryError(Exception):
    """Error during test discovery."""

    pass


class TestExecutionError(Exception):
    """Error during test execution."""

    pass


class SetupError(Exception):
    """Error during test setup/validation."""

    pass


def discover_services(services_path: Path = Path("services")) -> List[str]:
    """Discover all services with test modules.

    Args:
        services_path: Path to services directory

    Returns:
        List of service names
    """
    if not services_path.exists():
        return []

    services = []
    for item in services_path.iterdir():
        if item.is_dir() and not item.name.startswith("__"):
            # Check if it has a modules directory
            modules_path = item / "modules"
            if modules_path.exists():
                services.append(item.name)

    return sorted(services)


def discover_test_modules(service_path: Path) -> List[Path]:
    """Discover all test modules in a service.

    Args:
        service_path: Path to service directory

    Returns:
        List of test module paths, sorted by filename
    """
    modules_path = service_path / "modules"
    if not modules_path.exists():
        return []

    # Find modules with pattern _XX_*.py or XX_*.py
    modules = []
    for item in modules_path.iterdir():
        if item.is_file() and item.suffix == ".py" and not item.name.startswith("__"):
            # Check if it matches test module pattern
            name = item.name
            if name.startswith("_") and len(name) > 3 and name[1:3].isdigit():
                modules.append(item)
            elif len(name) > 2 and name[:2].isdigit():
                modules.append(item)

    # Sort by filename
    return sorted(modules, key=lambda p: p.name)


def load_test_module(module_path: Path) -> Optional[Callable]:
    """Load a test module and return its run function.

    Args:
        module_path: Path to test module

    Returns:
        The run function from the module, or None if not found
    """
    try:
        # Create a module spec
        module_name = f"test_module_{module_path.stem}"
        spec = importlib.util.spec_from_file_location(module_name, module_path)

        if spec is None or spec.loader is None:
            return None

        # Load the module
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        # Get the run function
        if hasattr(module, "run"):
            return module.run

        return None
    except Exception as e:
        console.print(f"[red]Error loading module {module_path}: {e}[/red]")
        return None


def _to_snake_case(name: str) -> str:
    """Convert a name to snake_case.

    Args:
        name: The name to convert

    Returns:
        snake_case version of the name
    """
    import re

    # Insert underscore between lowercase and uppercase
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    # Insert underscore between lowercase/number and uppercase
    s2 = re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1)
    # Replace hyphens with underscores
    s3 = s2.replace("-", "_")
    # Replace spaces with underscores
    s4 = s3.replace(" ", "_")
    return s4.lower()


def validate_service_setup(service_name: str, service_path: Path) -> None:
    """Validate that a service is properly configured before running tests.

    This function checks that:
    1. A file matching {service_name}_page.py exists in the service directory
    2. The file contains a class that inherits from BasePage

    Args:
        service_name: Name of the service
        service_path: Path to service directory

    Raises:
        SetupError: If validation fails with detailed error message
    """
    # Try exact service name first, then snake_case
    page_file = service_path / f"{service_name}_page.py"
    checked_path = f"services/{service_name}/{service_name}_page.py"

    # If not found with exact name, try snake_case (for backward compatibility)
    if not page_file.exists():
        snake_name = _to_snake_case(service_name)
        snake_page_file = service_path / f"{snake_name}_page.py"
        if snake_page_file.exists():
            page_file = snake_page_file
            checked_path = f"services/{service_name}/{snake_name}_page.py"

    # Check if file exists
    if not page_file.exists():
        raise SetupError(
            f"❌ ERROR: No Page class found for '{service_name}'\n"
            f"   Checked: {checked_path}\n\n"
            f"   Issues found:\n"
            f"   - File '{service_name}_page.py' not found.\n\n"
            f"   Solution:\n"
            f"   1. Rename your file to: {service_name}_page.py\n"
            f"   2. Ensure class inherits from BasePage:\n"
            f"      class YourServicePage(BasePage):\n"
        )

    # Add project root to sys.path for imports
    project_root = service_path.parent.parent.absolute()
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    try:
        # Use AST parsing to check for BasePage subclass without executing the module
        # This avoids issues with import errors (e.g., relative imports)
        import ast

        with open(page_file, "r", encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content)

        # Check for class inheriting from BasePage
        found_page_class = False
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Check if any base is 'BasePage'
                for base in node.bases:
                    if isinstance(base, ast.Name) and base.id == "BasePage":
                        found_page_class = True
                        break
                    elif isinstance(base, ast.Attribute):
                        # Handle cases like BasePage or module.BasePage
                        if base.attr == "BasePage":
                            found_page_class = True
                            break
            if found_page_class:
                break

        if not found_page_class:
            raise SetupError(
                f"❌ ERROR: No Page class found for '{service_name}'\n"
                f"   Checked: {checked_path}\n\n"
                f"   Issues found:\n"
                f"   - No class inheriting from BasePage found in the file.\n\n"
                f"   Solution:\n"
                f"   1. Rename your file to: {service_name}_page.py\n"
                f"   2. Ensure class inherits from BasePage:\n"
                f"      class YourServicePage(BasePage):\n"
            )

    except SyntaxError as e:
        raise SetupError(
            f"❌ ERROR: No Page class found for '{service_name}'\n"
            f"   Checked: {checked_path}\n\n"
            f"   Issues found:\n"
            f"   - Syntax error in file: {e}\n\n"
            f"   Solution:\n"
            f"   1. Rename your file to: {service_name}_page.py\n"
            f"   2. Ensure class inherits from BasePage:\n"
            f"      class YourServicePage(BasePage):\n"
        )
    except SetupError:
        raise
    except Exception as e:
        raise SetupError(
            f"❌ ERROR: No Page class found for '{service_name}'\n"
            f"   Checked: {checked_path}\n\n"
            f"   Issues found:\n"
            f"   - Error checking file: {e}\n\n"
            f"   Solution:\n"
            f"   1. Rename your file to: {service_name}_page.py\n"
            f"   2. Ensure class inherits from BasePage:\n"
            f"      class YourServicePage(BasePage):\n"
        )


def create_page_class(service_name: str, service_path: Path) -> Type[BasePage]:
    """Create or find the Page class for a service.

    Args:
        service_name: Name of the service
        service_path: Path to service directory

    Returns:
        Page class

    Raises:
        SetupError: If the page class cannot be found or doesn't inherit from BasePage
    """
    # Add project root to sys.path for imports
    project_root = service_path.parent.parent.absolute()
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    # Load the page file - we assume validation already passed
    # Try exact service name first, then snake_case (same logic as validation)
    page_file = service_path / f"{service_name}_page.py"
    if not page_file.exists():
        snake_name = _to_snake_case(service_name)
        snake_page_file = service_path / f"{snake_name}_page.py"
        if snake_page_file.exists():
            page_file = snake_page_file

    try:
        # Set up the service package to allow relative imports
        # The service should be importable as services.{snake_case_name}
        snake_name = _to_snake_case(service_name)

        # Create a unique package name based on service path to avoid conflicts
        # between tests with the same service name in different directories
        import hashlib

        path_hash = hashlib.md5(str(service_path).encode()).hexdigest()[:8]
        package_name = f"services_{path_hash}.{snake_name}"

        # Ensure the services package exists in sys.modules
        services_pkg_name = f"services_{path_hash}"
        if services_pkg_name not in sys.modules:
            services_spec = importlib.util.spec_from_file_location(
                services_pkg_name,
                service_path.parent / "__init__.py",
                submodule_search_locations=[str(service_path.parent)],
            )
            if services_spec:
                services_module = importlib.util.module_from_spec(services_spec)
                sys.modules[services_pkg_name] = services_module

        # Create the service package
        service_spec = importlib.util.spec_from_file_location(
            package_name,
            service_path / "__init__.py",
            submodule_search_locations=[str(service_path)],
        )
        if service_spec:
            service_module = importlib.util.module_from_spec(service_spec)
            sys.modules[package_name] = service_module

        # Load the page module
        module_name = f"{package_name}.{snake_name}_page"
        spec = importlib.util.spec_from_file_location(
            module_name, page_file, submodule_search_locations=None
        )

        if spec is None or spec.loader is None:
            raise SetupError(
                f"❌ ERROR: Could not load module for '{service_name}'\n"
                f"   File: {page_file}\n"
                f"   Error: Failed to create module spec"
            )

        module = importlib.util.module_from_spec(spec)
        module.__package__ = package_name  # Set package for relative imports
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        # Find the Page class (should be the one inheriting from BasePage)
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, BasePage)
                and attr is not BasePage
            ):
                return attr

        # This should not happen if validation passed, but handle it just in case
        raise SetupError(
            f"❌ ERROR: No Page class found for '{service_name}'\n"
            f"   Checked: services/{service_name}/{service_name}_page.py\n\n"
            f"   Issues found:\n"
            f"   - No class inheriting from BasePage found in the file.\n\n"
            f"   Solution:\n"
            f"   1. Rename your file to: {service_name}_page.py\n"
            f"   2. Ensure class inherits from BasePage:\n"
            f"      class YourServicePage(BasePage):\n"
        )
    except SetupError:
        raise
    except Exception as e:
        raise SetupError(
            f"❌ ERROR: Failed to load Page class for '{service_name}'\n"
            f"   File: {page_file}\n"
            f"   Error: {e}"
        )


def execute_single_test(
    module_path: Path, page: BasePage, service_name: str
) -> TestResult:
    """Execute a single test module.

    Args:
        module_path: Path to test module
        page: Page instance to pass to test
        service_name: Name of the service

    Returns:
        TestResult with execution details
    """
    import time
    from pathlib import Path

    start_time = time.time()
    test_name = module_path.stem

    # Initialize traceability
    trace_collector = None
    try:
        from socialseed_e2e.core.traceability import (
            TraceCollector,
            TraceConfig,
            get_global_collector,
            set_global_collector,
        )

        # Check if traceability is already enabled globally
        trace_collector = get_global_collector()
        if trace_collector is None:
            # Create new collector for this test
            trace_config = TraceConfig(
                enabled=True,
                capture_request_body=True,
                capture_response_body=True,
                track_logic_branches=True,
                generate_sequence_diagrams=True,
                output_format="mermaid",
            )
            trace_collector = TraceCollector(trace_config)
            set_global_collector(trace_collector)

        # Start test trace
        trace_collector.start_trace(
            test_name=test_name,
            service_name=service_name,
            metadata={"module_path": str(module_path)},
        )

    except ImportError:
        pass  # Traceability not available

    try:
        # Load the test module
        run_func = load_test_module(module_path)

        if run_func is None:
            # End trace with error
            if trace_collector:
                trace_collector.end_trace("error", "No 'run' function found in module")

            duration = (time.time() - start_time) * 1000
            return TestResult(
                name=test_name,
                service=service_name,
                status="error",
                duration_ms=duration,
                error_message="No 'run' function found in module",
            )

        # Execute the test
        run_func(page)

        duration = (time.time() - start_time) * 1000

        # End trace with success
        if trace_collector:
            trace_collector.end_trace("passed")

        result = TestResult(
            name=test_name, service=service_name, status="passed", duration_ms=duration
        )

        # Collect feedback for successful test
        collector = get_feedback_collector()
        collector.collect_test_result(
            test_name=test_name,
            success=True,
            execution_time=duration,
            endpoint=getattr(page, "base_url", None),
            metadata={"service": service_name},
        )

        return result

    except AssertionError as e:
        duration = (time.time() - start_time) * 1000

        # End trace with failure
        if trace_collector:
            trace_collector.end_trace("failed", str(e))

        result = TestResult(
            name=test_name,
            service=service_name,
            status="failed",
            duration_ms=duration,
            error_message=str(e),
        )

        # Collect feedback for failed test
        collector = get_feedback_collector()
        collector.collect_test_result(
            test_name=test_name,
            success=False,
            execution_time=duration,
            error_message=str(e),
            endpoint=getattr(page, "base_url", None),
            metadata={"service": service_name, "error_type": "assertion"},
        )

        return result
    except Exception as e:
        duration = (time.time() - start_time) * 1000

        # End trace with error
        if trace_collector:
            trace_collector.end_trace("error", str(e))

        error_traceback_str = traceback.format_exc()
        result = TestResult(
            name=test_name,
            service=service_name,
            status="error",
            duration_ms=duration,
            error_message=str(e),
            error_traceback=error_traceback_str,
        )

        # Collect feedback for test with error
        collector = get_feedback_collector()
        collector.collect_test_result(
            test_name=test_name,
            success=False,
            execution_time=duration,
            error_message=str(e),
            stack_trace=error_traceback_str[:500],  # Limit stack trace size
            endpoint=getattr(page, "base_url", None),
            metadata={"service": service_name, "error_type": "exception"},
        )

        return result


def run_service_tests(
    service_name: str,
    service_config: Optional[Any],
    services_path: Path = Path("services"),
    specific_module: Optional[str] = None,
    verbose: bool = False,
    include_tags: Optional[List[str]] = None,
    exclude_tags: Optional[List[str]] = None,
) -> TestSuiteResult:
    """Run all tests for a service.

    Args:
        service_name: Name of the service
        service_config: Service configuration
        services_path: Path to services directory
        specific_module: If specified, only run this module
        verbose: Whether to show verbose output

    Returns:
        TestSuiteResult with all test results
    """
    service_path = services_path / service_name
    suite_result = TestSuiteResult()

    # Validate service setup before running tests
    validate_service_setup(service_name, service_path)

    # Discover test modules
    if specific_module:
        # Find specific module
        modules_path = service_path / "modules"
        module_path = modules_path / specific_module
        if not module_path.exists():
            module_path = modules_path / f"_{specific_module}.py"
        if not module_path.exists():
            console.print(f"[red]Module '{specific_module}' not found[/red]")
            return suite_result
        test_modules = [module_path]
    else:
        test_modules = discover_test_modules(service_path)

    if not test_modules:
        console.print(
            f"[yellow]No test modules found for service '{service_name}'[/yellow]"
        )
        return suite_result

    # Advanced Organization: Filtering and Sorting
    if not specific_module:
        # Load and Filter
        include_set = set(include_tags) if include_tags else None
        exclude_set = set(exclude_tags) if exclude_tags else None

        # We need a wrapper class for TestOrganizationManager.filter_tests since it expects objects with 'run'
        class ModuleStub:
            def __init__(self, path):
                self.path = path
                self.run = load_test_module(path)

        stubs = [ModuleStub(p) for p in test_modules]
        filtered_stubs = TestOrganizationManager.filter_tests(
            stubs, include_set, exclude_set
        )
        test_modules = [s.path for s in filtered_stubs]

        # Sort by dependencies and priority
        test_modules = TestOrganizationManager.sort_tests(
            test_modules, load_test_module
        )

    if not test_modules:
        if include_tags or exclude_tags:
            console.print(
                f"[yellow]No tests matched tags for service '{service_name}'[/yellow]"
            )
        else:
            console.print(
                f"[yellow]No test modules found for service '{service_name}'[/yellow]"
            )
        return suite_result

    # Get base URL
    base_url = service_config.base_url if service_config else f"http://localhost:8080"

    # Create page class (validation already passed, so this will not fail)
    PageClass = create_page_class(service_name, service_path)

    console.print(f"\n[bold cyan]Running tests for service: {service_name}[/bold cyan]")
    console.print(f"[dim]Base URL: {base_url}[/dim]")
    console.print(f"[dim]Test modules: {len(test_modules)}[/dim]\n")

    # Execute tests with Playwright
    with sync_playwright() as p:
        # Create page instance
        page = PageClass(base_url=base_url, playwright=p)
        page.setup()

        try:
            for module_path in test_modules:
                result = execute_single_test(module_path, page, service_name)
                suite_result.results.append(result)
                suite_result.total += 1

                if result.status == "passed":
                    suite_result.passed += 1
                    console.print(
                        f"  [green]✓[/green] {result.name} ({result.duration_ms:.0f}ms)"
                    )
                elif result.status == "failed":
                    suite_result.failed += 1
                    console.print(
                        f"  [red]✗[/red] {result.name} - {result.error_message[:50]}"
                    )
                    if verbose and result.error_message:
                        console.print(f"    [dim]{result.error_message}[/dim]")
                elif result.status == "error":
                    suite_result.errors += 1
                    console.print(
                        f"  [red]⚠[/red] {result.name} - Error: {result.error_message[:50]}"
                    )
                    if verbose:
                        console.print(f"    [dim]{result.error_traceback[:200]}[/dim]")
        finally:
            page.teardown()

    return suite_result


def run_all_tests(
    services_path: Path = Path("services"),
    specific_service: Optional[str] = None,
    specific_module: Optional[str] = None,
    verbose: bool = False,
    include_tags: Optional[List[str]] = None,
    exclude_tags: Optional[List[str]] = None,
) -> Dict[str, TestSuiteResult]:
    """Run all tests for all services or a specific service.

    Args:
        services_path: Path to services directory
        specific_service: If specified, only run tests for this service
        specific_module: If specified, only run this module
        verbose: Whether to show verbose output

    Returns:
        Dictionary mapping service names to their TestSuiteResults
    """
    results: Dict[str, TestSuiteResult] = {}

    # Add project root to sys.path for imports
    project_root = services_path.parent.absolute()
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    # Discover services
    if specific_service:
        services = [specific_service]
    else:
        services = discover_services(services_path)

    if not services:
        console.print("[yellow]No services found with test modules[/yellow]")
        return results

    # Load configuration
    try:
        loader = ApiConfigLoader()
        config = loader.load()
    except Exception:
        config = None

    # Run tests for each service
    for service_name in services:
        # Get service configuration
        service_config = None
        if config and service_name in config.services:
            service_config = config.services[service_name]

        suite_result = run_service_tests(
            service_name=service_name,
            service_config=service_config,
            services_path=services_path,
            specific_module=specific_module,
            verbose=verbose,
            include_tags=include_tags,
            exclude_tags=exclude_tags,
        )

        results[service_name] = suite_result

    # Generate traceability report if traces were collected
    try:
        from socialseed_e2e.core.traceability import TraceReporter, get_global_collector

        collector = get_global_collector()
        if collector and collector.get_all_traces():
            console.print("\n[bold cyan]Generating traceability report...[/bold cyan]")

            reporter = TraceReporter(collector)
            report = reporter.generate_report()

            # Save reports
            output_dir = Path("e2e_reports")
            output_dir.mkdir(exist_ok=True)

            html_path = reporter.save_html_report(
                report, str(output_dir / "traceability_report.html")
            )
            md_path = reporter.save_markdown_report(
                report, str(output_dir / "traceability_report.md")
            )
            json_path = reporter.save_json_report(
                report, str(output_dir / "traceability_report.json")
            )

            console.print(f"[green]✓[/green] HTML report: {html_path}")
            console.print(f"[green]✓[/green] Markdown report: {md_path}")
            console.print(f"[green]✓[/green] JSON report: {json_path}")

            # Print summary
            summary = report.summary
            console.print(f"\n[dim]Trace Summary:[/dim]")
            console.print(f"  Total Tests: {summary.get('total_tests', 0)}")
            console.print(
                f"  Total Interactions: {summary.get('total_interactions', 0)}"
            )
            console.print(f"  Total Components: {summary.get('total_components', 0)}")
            console.print(
                f"  Total Logic Branches: {summary.get('total_logic_branches', 0)}"
            )

    except ImportError:
        pass  # Traceability not available

    return results


def print_summary(results: Dict[str, TestSuiteResult]) -> bool:
    """Print summary of all test results.

    Args:
        results: Dictionary of service results

    Returns:
        True if all tests passed, False otherwise
    """
    console.print("\n" + "═" * 60)
    console.print("[bold]Test Execution Summary[/bold]")
    console.print("═" * 60)

    total_tests = 0
    total_passed = 0
    total_failed = 0
    total_errors = 0

    for service_name, suite_result in results.items():
        total_tests += suite_result.total
        total_passed += suite_result.passed
        total_failed += suite_result.failed
        total_errors += suite_result.errors

        status_color = (
            "green" if suite_result.failed == 0 and suite_result.errors == 0 else "red"
        )
        console.print(
            f"\n[{status_color}]{service_name}[/{status_color}]: "
            f"{suite_result.passed}/{suite_result.total} passed "
            f"({suite_result.success_rate:.1f}%)"
        )

        # Show failed tests
        for result in suite_result.results:
            if result.status in ("failed", "error"):
                console.print(f"  [red]  - {result.name}[/red]")

    console.print("\n" + "─" * 60)

    if total_tests == 0:
        console.print("[yellow]No tests were executed[/yellow]")
        return False

    overall_success = total_failed == 0 and total_errors == 0

    if overall_success:
        console.print(f"[bold green]✓ All {total_tests} tests passed![/bold green]")
    else:
        console.print(
            f"[bold red]✗ {total_failed + total_errors} of {total_tests} tests failed[/bold red]"
        )
        console.print(f"  [green]Passed: {total_passed}[/green]")
        console.print(f"  [red]Failed: {total_failed}[/red]")
        console.print(f"  [red]Errors: {total_errors}[/red]")

    console.print("═" * 60)

    return overall_success
