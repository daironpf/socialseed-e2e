"""Integration module for traceability with BasePage and TestRunner.

This module provides seamless integration of traceability features
with the existing BasePage and TestRunner components.
"""

import functools
from typing import Callable, Optional

from playwright.sync_api import APIResponse

from socialseed_e2e.core.traceability.collector import (
    TraceCollector,
    get_global_collector,
    set_global_collector,
)
from socialseed_e2e.core.traceability.models import InteractionType, LogicBranchType, TraceConfig


def trace_http_request(func: Callable) -> Callable:
    """Decorator to trace HTTP requests made through BasePage.

    This decorator automatically records HTTP request/response interactions
    when applied to BasePage methods.

    Example:
        @trace_http_request
        def get(self, endpoint, ...):
            # Original implementation
            pass
    """

    @functools.wraps(func)
    def wrapper(self, endpoint: str, *args, **kwargs):
        collector = get_global_collector()

        if collector is None or not collector.config.enabled:
            return func(self, endpoint, *args, **kwargs)

        # Get method name (get, post, put, delete, patch)
        method = func.__name__.upper()

        # Record the request
        interaction = collector.record_interaction(
            from_component="Test Client",
            to_component=self.base_url,
            action=f"{method} {endpoint}",
            interaction_type=InteractionType.HTTP_REQUEST,
            request_data=kwargs.get("json") or kwargs.get("data"),
            headers=kwargs.get("headers"),
            status="pending",
        )

        try:
            # Execute the actual request
            response = func(self, endpoint, *args, **kwargs)

            # Update interaction with response data
            if interaction and isinstance(response, APIResponse):
                try:
                    body = response.json()
                except:
                    body = {"status": response.status}

                interaction.response_data = body
                interaction.status = "success" if 200 <= response.status < 300 else "error"
                interaction.duration_ms = (
                    self._get_last_request_duration()
                    if hasattr(self, "_get_last_request_duration")
                    else 0
                )

            return response

        except Exception as e:
            # Record error
            if interaction:
                interaction.status = "error"
                interaction.error_message = str(e)
            raise

    return wrapper


def trace_assertion(assertion_name: str):
    """Decorator factory to trace assertion calls.

    Args:
        assertion_name: Name of the assertion being traced

    Returns:
        Decorator function

    Example:
        @trace_assertion("status_check")
        def assert_status(self, response, expected_status):
            # Original implementation
            pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            collector = get_global_collector()

            if collector is None or not collector.config.enabled:
                return func(*args, **kwargs)

            try:
                result = func(*args, **kwargs)

                # Record successful assertion
                collector.record_logic_branch(
                    condition=assertion_name,
                    decision="passed",
                    branch_type=LogicBranchType.ASSERTION,
                    reason=f"Assertion '{assertion_name}' passed",
                )

                return result

            except AssertionError as e:
                # Record failed assertion
                collector.record_logic_branch(
                    condition=assertion_name,
                    decision="failed",
                    branch_type=LogicBranchType.ASSERTION,
                    reason=str(e),
                )
                raise

        return wrapper

    return decorator


def enable_traceability(
    config: Optional[TraceConfig] = None, auto_instrument: bool = True
) -> TraceCollector:
    """Enable traceability for test execution.

    This function initializes the global trace collector and optionally
    instruments the BasePage class for automatic tracing.

    Args:
        config: Trace configuration (uses defaults if None)
        auto_instrument: Whether to automatically instrument BasePage

    Returns:
        Initialized TraceCollector

    Example:
        >>> from socialseed_e2e import enable_traceability
        >>> collector = enable_traceability()
        >>> # Run tests...
        >>> report = generate_trace_report()
    """
    # Create and set global collector
    collector = TraceCollector(config or TraceConfig())
    set_global_collector(collector)

    if auto_instrument:
        instrument_base_page()

    return collector


def disable_traceability() -> None:
    """Disable traceability and clear the global collector."""
    collector = get_global_collector()
    if collector:
        collector.clear()
    set_global_collector(None)


def instrument_base_page() -> None:
    """Instrument BasePage methods for automatic tracing.

    This function patches BasePage HTTP methods to automatically
    record interactions. Call this after importing BasePage.
    """
    try:
        from socialseed_e2e.core.base_page import BasePage

        # Store original methods
        if not hasattr(BasePage, "_original_get"):
            BasePage._original_get = BasePage.get
            BasePage._original_post = BasePage.post
            BasePage._original_put = BasePage.put
            BasePage._original_delete = BasePage.delete
            BasePage._original_patch = BasePage.patch

        # Patch methods with tracing
        BasePage.get = _create_traced_method("GET")
        BasePage.post = _create_traced_method("POST")
        BasePage.put = _create_traced_method("PUT")
        BasePage.delete = _create_traced_method("DELETE")
        BasePage.patch = _create_traced_method("PATCH")

    except ImportError:
        pass


def deinstrument_base_page() -> None:
    """Remove tracing instrumentation from BasePage."""
    try:
        from socialseed_e2e.core.base_page import BasePage

        # Restore original methods
        if hasattr(BasePage, "_original_get"):
            BasePage.get = BasePage._original_get
            BasePage.post = BasePage._original_post
            BasePage.put = BasePage._original_put
            BasePage.delete = BasePage._original_delete
            BasePage.patch = BasePage._original_patch

            # Remove stored originals
            delattr(BasePage, "_original_get")
            delattr(BasePage, "_original_post")
            delattr(BasePage, "_original_put")
            delattr(BasePage, "_original_delete")
            delattr(BasePage, "_original_patch")

    except ImportError:
        pass


def _create_traced_method(method: str):
    """Create a traced version of an HTTP method.

    Args:
        method: HTTP method name (GET, POST, etc.)

    Returns:
        Traced method function
    """

    def traced_method(self, endpoint: str, *args, **kwargs):
        from socialseed_e2e.core.base_page import BasePage

        collector = get_global_collector()

        if collector is None or not collector.config.enabled:
            # Call original method
            original = getattr(BasePage, f"_original_{method.lower()}")
            return original(self, endpoint, *args, **kwargs)

        # Record request start
        import time

        start_time = time.time()

        # Get request data
        request_data = kwargs.get("json") or kwargs.get("data")
        headers = kwargs.get("headers")

        # Record the interaction
        interaction = collector.record_interaction(
            from_component="Test Client",
            to_component=self.base_url,
            action=f"{method} {endpoint}",
            interaction_type=InteractionType.HTTP_REQUEST,
            request_data=request_data,
            headers=headers,
            status="pending",
        )

        try:
            # Call original method
            original = getattr(BasePage, f"_original_{method.lower()}")
            response = original(self, endpoint, *args, **kwargs)

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Update interaction with response
            if interaction:
                try:
                    response_body = response.json()
                except:
                    response_body = {"status_code": response.status}

                interaction.response_data = response_body
                interaction.status = "success" if 200 <= response.status < 300 else "error"
                interaction.duration_ms = duration_ms
                interaction.headers = dict(response.headers)

            return response

        except Exception as e:
            # Record error
            if interaction:
                interaction.status = "error"
                interaction.error_message = str(e)
            raise

    return traced_method


def start_test_trace(test_name: str, service_name: str, **metadata) -> None:
    """Start a test trace using the global collector.

    Args:
        test_name: Name of the test
        service_name: Name of the service
        **metadata: Additional metadata
    """
    collector = get_global_collector()
    if collector:
        collector.start_trace(test_name, service_name, metadata)


def end_test_trace(status: str = "passed", error_message: Optional[str] = None) -> None:
    """End the current test trace.

    Args:
        status: Final status (passed, failed, error)
        error_message: Optional error message
    """
    collector = get_global_collector()
    if collector:
        collector.end_trace(status, error_message)


def record_interaction(from_component: str, to_component: str, action: str, **kwargs) -> None:
    """Record an interaction using the global collector.

    Args:
        from_component: Source component
        to_component: Target component
        action: Action description
        **kwargs: Additional interaction data
    """
    collector = get_global_collector()
    if collector:
        collector.record_interaction(from_component, to_component, action, **kwargs)


def record_logic_branch(condition: str, decision: str, **kwargs) -> None:
    """Record a logic branch using the global collector.

    Args:
        condition: Condition being evaluated
        decision: Decision made
        **kwargs: Additional branch data
    """
    collector = get_global_collector()
    if collector:
        collector.record_logic_branch(condition, decision, **kwargs)


class TraceContext:
    """Context manager for test tracing.

    This context manager provides a convenient way to trace test execution.

    Example:
        >>> with TraceContext("test_login", "auth-service"):
        ...     # Run test code
        ...     response = page.post("/login", json=credentials)
        ...     assert response.status == 200
        >>> # Trace automatically ended with status
    """

    def __init__(self, test_name: str, service_name: str, **metadata):
        """Initialize trace context.

        Args:
            test_name: Name of the test
            service_name: Name of the service
            **metadata: Additional metadata
        """
        self.test_name = test_name
        self.service_name = service_name
        self.metadata = metadata
        self.collector = get_global_collector()

    def __enter__(self):
        """Start trace when entering context."""
        if self.collector:
            self.collector.start_trace(self.test_name, self.service_name, self.metadata)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """End trace when exiting context."""
        if self.collector:
            if exc_type is None:
                self.collector.end_trace("passed")
            elif exc_type is AssertionError:
                self.collector.end_trace("failed", str(exc_val))
            else:
                self.collector.end_trace("error", str(exc_val))
