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

from socialseed_e2e import BasePage
from socialseed_e2e.core.config_loader import ApiConfigLoader, ServiceConfig, get_service_config

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


def create_page_class(service_name: str, service_path: Path) -> Optional[Type[BasePage]]:
    """Create or find the Page class for a service.

    Args:
        service_name: Name of the service
        service_path: Path to service directory

    Returns:
        Page class, or None if not found
    """
    # Add project root to sys.path for imports
    project_root = service_path.parent.parent.absolute()
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    # Try to find page file
    page_files = list(service_path.glob("*_page.py"))
    if not page_files:
        # Try with service name
        page_file = service_path / f"{service_name}_page.py"
        if not page_file.exists():
            return None
        page_files = [page_file]

    page_file = page_files[0]

    try:
        # Load the page module
        module_name = f"page_{service_name}"
        spec = importlib.util.spec_from_file_location(module_name, page_file)

        if spec is None or spec.loader is None:
            return None

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        # Find the Page class (should be the one inheriting from BasePage)
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, type) and issubclass(attr, BasePage) and attr is not BasePage:
                return attr

        return None
    except Exception as e:
        console.print(f"[red]Error loading page class from {page_file}: {e}[/red]")
        return None


def execute_single_test(module_path: Path, page: BasePage, service_name: str) -> TestResult:
    """Execute a single test module.

    Args:
        module_path: Path to test module
        page: Page instance to pass to test
        service_name: Name of the service

    Returns:
        TestResult with execution details
    """
    start_time = time.time()
    test_name = module_path.stem

    try:
        # Load the test module
        run_func = load_test_module(module_path)

        if run_func is None:
            return TestResult(
                name=test_name,
                service=service_name,
                status="error",
                error_message="No 'run' function found in module",
            )

        # Execute the test
        run_func(page)

        duration = (time.time() - start_time) * 1000
        return TestResult(
            name=test_name, service=service_name, status="passed", duration_ms=duration
        )

    except AssertionError as e:
        duration = (time.time() - start_time) * 1000
        return TestResult(
            name=test_name,
            service=service_name,
            status="failed",
            duration_ms=duration,
            error_message=str(e),
        )
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        return TestResult(
            name=test_name,
            service=service_name,
            status="error",
            duration_ms=duration,
            error_message=str(e),
            error_traceback=traceback.format_exc(),
        )


def run_service_tests(
    service_name: str,
    service_config: Optional[Any],
    services_path: Path = Path("services"),
    specific_module: Optional[str] = None,
    verbose: bool = False,
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
        console.print(f"[yellow]No test modules found for service '{service_name}'[/yellow]")
        return suite_result

    # Get base URL
    base_url = service_config.base_url if service_config else f"http://localhost:8080"

    # Create page class
    PageClass = create_page_class(service_name, service_path)
    if PageClass is None:
        console.print(f"[yellow]No Page class found for '{service_name}', using BasePage[/yellow]")
        PageClass = BasePage

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
                    console.print(f"  [green]✓[/green] {result.name} ({result.duration_ms:.0f}ms)")
                elif result.status == "failed":
                    suite_result.failed += 1
                    console.print(f"  [red]✗[/red] {result.name} - {result.error_message[:50]}")
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
        )

        results[service_name] = suite_result

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
        )

        results[service_name] = suite_result

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

        status_color = "green" if suite_result.failed == 0 and suite_result.errors == 0 else "red"
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
