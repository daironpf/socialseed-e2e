"""Integration module for performance profiling with BasePage.

This module provides easy integration between BasePage and PerformanceProfiler
for automatic latency tracking during E2E tests.
"""

from functools import wraps
from typing import Any, Callable, Optional, TypeVar

from socialseed_e2e.performance.performance_profiler import PerformanceProfiler

F = TypeVar("F", bound=Callable[..., Any])


class PerformanceMixin:
    """Mixin class to add performance profiling to BasePage.

    This mixin adds automatic performance tracking to all HTTP methods
    when used with BasePage.

    Example:
        >>> from socialseed_e2e import BasePage
        >>> from socialseed_e2e.performance import PerformanceMixin
        >>>
        >>> class ProfilingBasePage(PerformanceMixin, BasePage):
        ...     pass
        >>>
        >>> page = ProfilingBasePage("https://api.example.com")
        >>> page.enable_profiling()
        >>>
        >>> # All requests are now automatically profiled
        >>> response = page.get("/users")
        >>>
        >>> report = page.get_performance_report()
        >>> print(report.summary)
    """

    def __init__(self, *args, **kwargs):
        """Initialize with performance profiler support."""
        super().__init__(*args, **kwargs)
        self._profiler: Optional[PerformanceProfiler] = None
        self._profiling_enabled = False

    def enable_profiling(
        self, service_name: Optional[str] = None, output_dir: Optional[str] = None
    ) -> None:
        """Enable performance profiling for this page.

        Args:
            service_name: Name of the service (defaults to base_url)
            output_dir: Directory to save reports
        """
        from pathlib import Path

        if service_name is None:
            service_name = getattr(self, "base_url", "unknown")

        self._profiler = PerformanceProfiler(
            service_name=service_name,
            output_dir=Path(output_dir) if output_dir else None,
        )
        self._profiler.start_profiling()
        self._profiling_enabled = True

    def disable_profiling(self) -> None:
        """Disable performance profiling."""
        if self._profiler:
            self._profiler.stop_profiling()
        self._profiling_enabled = False

    def get_performance_report(self):
        """Get the current performance report.

        Returns:
            PerformanceReport or None if profiling not enabled
        """
        if not self._profiler:
            return None
        return self._profiler.generate_report()

    def save_performance_report(self) -> Optional[str]:
        """Save the performance report to disk.

        Returns:
            Path to saved report or None
        """
        if not self._profiler:
            return None
        path = self._profiler.save_report()
        return str(path)

    def _make_request_with_profiling(self, method: str, url: str, **kwargs) -> Any:
        """Make an HTTP request with performance profiling.

        Args:
            method: HTTP method
            url: Request URL
            **kwargs: Additional request arguments

        Returns:
            APIResponse
        """
        import uuid

        if not self._profiling_enabled or not self._profiler:
            # Call parent method without profiling
            return super()._make_request(method, url, **kwargs)

        request_id = str(uuid.uuid4())
        full_url = getattr(self, "base_url", "") + url

        # Start profiling
        self._profiler.start_request(request_id, method, full_url)

        try:
            # Make the actual request
            response = super()._make_request(method, url, **kwargs)

            # End profiling with success
            status_code = getattr(response, "status", 200)
            self._profiler.end_request(request_id, status_code)

            return response
        except Exception as e:
            # End profiling with error
            self._profiler.end_request(request_id, 0, error=str(e))
            raise

    def get(self, url: str, **kwargs) -> Any:
        """Make a GET request with profiling if enabled."""
        if self._profiling_enabled:
            return self._make_request_with_profiling("GET", url, **kwargs)
        return super().get(url, **kwargs)

    def post(self, url: str, **kwargs) -> Any:
        """Make a POST request with profiling if enabled."""
        if self._profiling_enabled:
            return self._make_request_with_profiling("POST", url, **kwargs)
        return super().post(url, **kwargs)

    def put(self, url: str, **kwargs) -> Any:
        """Make a PUT request with profiling if enabled."""
        if self._profiling_enabled:
            return self._make_request_with_profiling("PUT", url, **kwargs)
        return super().put(url, **kwargs)

    def delete(self, url: str, **kwargs) -> Any:
        """Make a DELETE request with profiling if enabled."""
        if self._profiling_enabled:
            return self._make_request_with_profiling("DELETE", url, **kwargs)
        return super().delete(url, **kwargs)

    def patch(self, url: str, **kwargs) -> Any:
        """Make a PATCH request with profiling if enabled."""
        if self._profiling_enabled:
            return self._make_request_with_profiling("PATCH", url, **kwargs)
        return super().patch(url, **kwargs)


def profile_endpoint(func: F) -> F:
    """Decorator to profile a specific test method.

    This decorator automatically enables performance profiling
    for the duration of the test.

    Example:
        >>> class MyTests:
        ...     @profile_endpoint
        ...     def test_get_users(self, page):
        ...         response = page.get("/users")
        ...         assert response.status == 200
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        # Find the page argument
        page = None
        for arg in args:
            if hasattr(arg, "enable_profiling"):
                page = arg
                break

        if page is None:
            for key, value in kwargs.items():
                if hasattr(value, "enable_profiling"):
                    page = value
                    break

        if page:
            page.enable_profiling()
            try:
                result = func(*args, **kwargs)
            finally:
                page.disable_profiling()
                report = page.get_performance_report()
                if report:
                    print(f"\nPerformance Summary: {report.summary}")
            return result
        else:
            return func(*args, **kwargs)

    return wrapper


def create_profiling_page(base_page_class=None, service_name: Optional[str] = None):
    """Factory function to create a BasePage subclass with profiling.

    Args:
        base_page_class: BasePage class to extend (defaults to BasePage)
        service_name: Service name for profiling

    Returns:
        Profiling-enabled BasePage class
    """
    if base_page_class is None:
        from socialseed_e2e import BasePage

        base_page_class = BasePage

    class ProfilingPage(PerformanceMixin, base_page_class):
        """BasePage with automatic performance profiling."""

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            if service_name:
                self.enable_profiling(service_name=service_name)

    return ProfilingPage
