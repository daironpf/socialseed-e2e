"""Parallel test execution support for socialseed-e2e framework.

This module provides multiprocessing capabilities for running tests in parallel,
with proper state isolation and result aggregation.
"""

import multiprocessing as mp
import os
import sys
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type

from playwright.sync_api import sync_playwright

from socialseed_e2e.core.base_page import BasePage
from socialseed_e2e.core.config_loader import (
    ApiConfigLoader,
    ServiceConfig,
    normalize_service_name,
)
from socialseed_e2e.core.test_runner import (
    TestResult,
    TestSuiteResult,
    create_page_class,
    discover_services,
    discover_test_modules,
    load_test_module,
)
from socialseed_e2e.core.organization import TestOrganizationManager


@dataclass
class ParallelConfig:
    """Configuration for parallel test execution.

    Attributes:
        enabled: Whether parallel execution is enabled
        max_workers: Maximum number of parallel workers (None = auto)
        parallel_mode: Execution mode ('service' or 'test')
        isolation_level: State isolation level ('process', 'service', 'none')
    """

    enabled: bool = False
    max_workers: Optional[int] = None
    parallel_mode: str = "service"  # 'service' or 'test'
    isolation_level: str = "process"  # 'process', 'service', 'none'

    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.max_workers is None:
            # Auto-detect: use CPU count but cap at 8
            self.max_workers = min(os.cpu_count() or 1, 8)

        if self.parallel_mode not in ("service", "test"):
            raise ValueError(
                f"Invalid parallel_mode: {self.parallel_mode}. Use 'service' or 'test'"
            )

        if self.isolation_level not in ("process", "service", "none"):
            raise ValueError(
                f"Invalid isolation_level: {self.isolation_level}. "
                "Use 'process', 'service', or 'none'"
            )


@dataclass
class WorkerTask:
    """Task assigned to a worker process.

    Attributes:
        service_name: Name of the service to test
        service_config: Configuration for the service
        module_paths: List of test module paths to execute
        project_root: Root directory of the project
        debug: Whether to enable debug mode with verbose HTTP logging
        no_agent: Whether to disable AI agent features (boring mode)
    """

    service_name: str
    service_config: Optional[ServiceConfig]
    module_paths: List[Path]
    project_root: Path
    debug: bool = False
    no_agent: bool = False


@dataclass
class WorkerResult:
    """Result returned by a worker process.

    Attributes:
        service_name: Name of the service tested
        suite_result: Test suite execution result
        error: Error message if worker failed
    """

    service_name: str
    suite_result: TestSuiteResult
    error: Optional[str] = None


def execute_service_tests_worker(task: WorkerTask) -> WorkerResult:
    """Execute tests for a service in an isolated worker process.

    This function runs in a separate process and has complete state isolation.
    Each worker creates its own Playwright instance and page objects.

    Args:
        task: WorkerTask containing service configuration and test modules

    Returns:
        WorkerResult with test execution results
    """
    # Ensure project root is in sys.path for imports
    if str(task.project_root) not in sys.path:
        sys.path.insert(0, str(task.project_root))

    service_name = task.service_name
    suite_result = TestSuiteResult()

    try:
        # Get base URL
        base_url = (
            task.service_config.base_url
            if task.service_config
            else f"http://localhost:8080"
        )

        # Create page class
        service_path = Path("services") / service_name
        PageClass = create_page_class(service_name, service_path)
        if PageClass is None:
            PageClass = BasePage

        # Execute tests with isolated Playwright instance
        with sync_playwright() as p:
            page = PageClass(base_url=base_url, playwright=p)
            page.setup()

            try:
                for module_path in task.module_paths:
                    result = execute_single_test_in_worker(
                        module_path,
                        page,
                        service_name,
                        debug=task.debug,
                        no_agent=task.no_agent,
                    )
                    suite_result.results.append(result)
                    suite_result.total += 1

                    if result.status == "passed":
                        suite_result.passed += 1
                    elif result.status == "failed":
                        suite_result.failed += 1
                    elif result.status == "error":
                        suite_result.errors += 1

            finally:
                page.teardown()

        return WorkerResult(service_name=service_name, suite_result=suite_result)

    except Exception as e:
        error_msg = f"Worker failed for service {service_name}: {str(e)}\n{traceback.format_exc()}"
        return WorkerResult(
            service_name=service_name, suite_result=suite_result, error=error_msg
        )


def execute_single_test_in_worker(
    module_path: Path,
    page: BasePage,
    service_name: str,
    debug: bool = False,
    no_agent: bool = False,
) -> TestResult:
    """Execute a single test module within a worker.

    Args:
        module_path: Path to test module
        page: Page instance to pass to test
        service_name: Name of the service
        debug: Whether to enable debug mode with verbose HTTP logging
        no_agent: Whether to disable AI agent features (boring mode)

    Returns:
        TestResult with execution details
    """
    import json

    start_time = time.time()
    test_name = module_path.stem

    try:
        run_func = load_test_module(module_path)

        if run_func is None:
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
        return TestResult(
            name=test_name, service=service_name, status="passed", duration_ms=duration
        )

    except AssertionError as e:
        duration = (time.time() - start_time) * 1000

        # Collect debug info if debug mode is enabled
        debug_info = None
        if debug and page.request_history:
            last_request = page.request_history[-1]
            debug_info = {
                "method": last_request.method,
                "url": last_request.url,
                "request_payload": last_request.body,
                "response_status": last_request.status,
                "response_body": last_request.response_body,
                "expected": str(e),
            }

        return TestResult(
            name=test_name,
            service=service_name,
            status="failed",
            duration_ms=duration,
            error_message=str(e),
            debug_info=debug_info,
        )
    except Exception as e:
        duration = (time.time() - start_time) * 1000

        # Collect debug info if debug mode is enabled
        debug_info = None
        if debug and page.request_history:
            last_request = page.request_history[-1]
            debug_info = {
                "method": last_request.method,
                "url": last_request.url,
                "request_payload": last_request.body,
                "response_status": last_request.status,
                "response_body": last_request.response_body,
                "error": str(e),
            }

        return TestResult(
            name=test_name,
            service=service_name,
            status="error",
            duration_ms=duration,
            error_message=str(e),
            debug_info=debug_info,
        )
    except Exception as e:
        duration = (time.time() - start_time) * 1000

        # Collect debug info if debug mode is enabled
        debug_info = None
        if debug and page.request_history:
            last_request = page.request_history[-1]
            debug_info = {
                "method": last_request.method,
                "url": last_request.url,
                "request_payload": last_request.body,
                "response_status": last_request.status,
                "response_body": last_request.response_body,
                "error": str(e),
            }

        return TestResult(
            name=test_name,
            service=service_name,
            status="error",
            duration_ms=duration,
            error_message=str(e),
            error_traceback=traceback.format_exc(),
        )


def run_tests_parallel(
    services_path: Path = Path("services"),
    specific_service: Optional[str] = None,
    specific_module: Optional[str] = None,
    parallel_config: Optional[ParallelConfig] = None,
    verbose: bool = False,
    debug: bool = False,
    no_agent: bool = False,
    include_tags: Optional[List[str]] = None,
    exclude_tags: Optional[List[str]] = None,
) -> Dict[str, TestSuiteResult]:
    """Run all tests in parallel using multiple worker processes.

    Args:
        services_path: Path to services directory
        specific_service: If specified, only run tests for this service
        specific_module: If specified, only run this module
        no_agent: Whether to disable AI agent features (boring mode)
        parallel_config: Configuration for parallel execution
        verbose: Whether to show verbose output
        debug: Whether to enable debug mode with verbose HTTP logging

    Returns:
        Dictionary mapping service names to their TestSuiteResults
    """
    if parallel_config is None:
        parallel_config = ParallelConfig()

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
        return {}

    # Load configuration
    try:
        loader = ApiConfigLoader()
        config = loader.load()
    except Exception:
        config = None

    # Normalize service names and validate against configuration
    normalized_services = []
    unconfigured_services = []

    for service_name in services:
        normalized_name = normalize_service_name(service_name)
        normalized_services.append(normalized_name)

        # Check if service has configuration (using normalized name)
        if config and normalized_name not in config.services:
            unconfigured_services.append(service_name)

    # Warn about unconfigured services
    if unconfigured_services and config:
        print(
            "\n[yellow]⚠️  WARNING: The following services lack configuration in e2e.conf:[/yellow]"
        )
        for svc in unconfigured_services:
            print(f"   - [yellow]{svc}[/yellow] (will use defaults)")
        print(
            "\n   [dim]Add these services to e2e.conf to configure base_url, port, etc.[/dim]\n"
        )

    # Print services summary
    configured_services = [
        svc for svc in normalized_services if config and svc in config.services
    ]
    print("\n[bold]Services Summary:[/bold]")
    print(f"   Detected:    [{', '.join(services)}]")
    if config:
        print(f"   Configured:  [{', '.join(configured_services)}]")
        if unconfigured_services:
            print(f"   Unconfigured: [{', '.join(unconfigured_services)}]")
    print()

    # Prepare worker tasks
    tasks: List[WorkerTask] = []
    for service_name in services:
        service_path = services_path / service_name

        # Discover test modules
        if specific_module:
            modules_path = service_path / "modules"
            module_path = modules_path / specific_module
            if not module_path.exists():
                module_path = modules_path / f"_{specific_module}.py"
            if module_path.exists():
                test_modules = [module_path]
            else:
                test_modules = []
        else:
            test_modules = discover_test_modules(service_path)
        if not test_modules:
            continue

        # Advanced Organization: Filtering and Sorting
        if not specific_module:
            # Filter
            include_set = set(include_tags) if include_tags else None
            exclude_set = set(exclude_tags) if exclude_tags else None

            class ModuleStub:
                def __init__(self, path):
                    self.path = path
                    self.run = load_test_module(path)

            stubs = [ModuleStub(p) for p in test_modules]
            filtered_stubs = TestOrganizationManager.filter_tests(
                stubs, include_set, exclude_set
            )
            test_modules = [s.path for s in filtered_stubs]

            # Sort
            test_modules = TestOrganizationManager.sort_tests(
                test_modules, load_test_module
            )

        if not test_modules:
            continue

        # Get service configuration (using normalized name for lookup)
        service_config = None
        if config:
            normalized_name = normalize_service_name(service_name)
            service_config = config.services.get(normalized_name)

        task = WorkerTask(
            service_name=service_name,
            service_config=service_config,
            module_paths=test_modules,
            project_root=project_root,
            debug=debug,
            no_agent=no_agent,
        )
        tasks.append(task)

    if not tasks:
        return {}

    # Execute tasks in parallel
    results: Dict[str, TestSuiteResult] = {}

    if verbose:
        print(
            f"Running {len(tasks)} service(s) in parallel with {parallel_config.max_workers} workers..."
        )

    # Use ProcessPoolExecutor for better resource management
    from concurrent.futures import ProcessPoolExecutor, as_completed

    with ProcessPoolExecutor(max_workers=parallel_config.max_workers) as executor:
        # Submit all tasks
        future_to_task = {
            executor.submit(execute_service_tests_worker, task): task for task in tasks
        }

        # Collect results as they complete
        for future in as_completed(future_to_task):
            task = future_to_task[future]
            try:
                worker_result = future.result()
                if worker_result.error:
                    if verbose:
                        print(
                            f"[red]Error in {worker_result.service_name}: {worker_result.error}[/red]"
                        )
                results[worker_result.service_name] = worker_result.suite_result
            except Exception as e:
                if verbose:
                    print(f"[red]Worker crashed for {task.service_name}: {e}[/red]")
                # Create empty result for failed service
                results[task.service_name] = TestSuiteResult()

    return results


def get_parallel_config_from_args(
    parallel_workers: Optional[int] = None,
    parallel_mode: str = "service",
    config_path: Optional[str] = None,
) -> ParallelConfig:
    """Create ParallelConfig from CLI arguments and config file.

    Args:
        parallel_workers: Number of workers from CLI (None = auto, 0 = disabled)
        parallel_mode: Execution mode ('service' or 'test')
        config_path: Path to configuration file

    Returns:
        ParallelConfig instance
    """
    # Check config file first
    try:
        loader = ApiConfigLoader()
        app_config = loader.load(config_path)

        # Check if parallel config exists in app_config
        if hasattr(app_config, "parallel") and app_config.parallel:
            pconf = app_config.parallel
            return ParallelConfig(
                enabled=pconf.enabled,
                max_workers=pconf.max_workers,
                parallel_mode=pconf.mode,
                isolation_level=pconf.isolation_level,
            )
    except Exception:
        pass

    # Use CLI arguments
    if parallel_workers == 0:
        return ParallelConfig(enabled=False)
    elif parallel_workers is not None:
        return ParallelConfig(
            enabled=True, max_workers=parallel_workers, parallel_mode=parallel_mode
        )

    # Default: disabled
    return ParallelConfig(enabled=False)
