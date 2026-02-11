"""Example: Hook Plugin.

This example demonstrates how to create a hook-based plugin that
registers callbacks at various points in the test lifecycle.

Usage:
    1. Save this file as a plugin
    2. The plugin will register hooks when loaded
    3. Hooks will be triggered automatically during test execution
"""

import logging
import time
from datetime import datetime
from typing import Any, Dict, Optional

from socialseed_e2e.plugins import (
    HookManager,
    IHookPlugin,
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestLifecycleHooksPlugin(IHookPlugin):
    """Example plugin that provides test lifecycle hooks.

    This plugin demonstrates how to use hooks to execute code at
    various points during test execution.

    Hooks Registered:
        - before_test: Called before each test
        - after_test: Called after each test
        - before_suite: Called before test suite
        - after_suite: Called after test suite
        - on_error: Called when an error occurs
    """

    name = "test-lifecycle-hooks"
    version = "1.0.0"
    description = "Provides test lifecycle hooks"

    def __init__(self):
        self.test_start_times: Dict[str, float] = {}
        self.suite_start_time: Optional[float] = None
        self.hook_manager: Optional[HookManager] = None

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the plugin.

        Args:
            config: Optional configuration
        """
        print(f"✓ Test Lifecycle Hooks plugin initialized")

    def shutdown(self) -> None:
        """Clean up resources."""
        print(f"✓ Test Lifecycle Hooks plugin shutdown")

    def register_hooks(self, hook_manager: HookManager) -> None:
        """Register hooks with the framework.

        Args:
            hook_manager: Hook manager to register with
        """
        self.hook_manager = hook_manager

        # Register all lifecycle hooks
        hook_manager.subscribe("before_test", self.before_test, priority=1)
        hook_manager.subscribe("after_test", self.after_test, priority=99)
        hook_manager.subscribe("before_suite", self.before_suite, priority=1)
        hook_manager.subscribe("after_suite", self.after_suite, priority=99)
        hook_manager.subscribe("on_error", self.on_error, priority=1)

        print(f"  Registered 5 lifecycle hooks")

    def before_test(self, test_name: str, **kwargs) -> Dict[str, Any]:
        """Called before each test starts.

        Args:
            test_name: Name of the test

        Returns:
            Context data for the test
        """
        self.test_start_times[test_name] = time.time()
        logger.info(f"[HOOK] Before test: {test_name}")

        # You can return data that will be passed to other hooks
        return {
            "start_time": datetime.now().isoformat(),
            "test_name": test_name,
        }

    def after_test(self, test_name: str, result: Any, **kwargs) -> Dict[str, Any]:
        """Called after each test completes.

        Args:
            test_name: Name of the test
            result: Test result

        Returns:
            Context data
        """
        duration = 0.0
        if test_name in self.test_start_times:
            duration = time.time() - self.test_start_times[test_name]
            del self.test_start_times[test_name]

        passed = getattr(result, "passed", True)
        status = "✓ PASSED" if passed else "✗ FAILED"

        logger.info(f"[HOOK] After test: {test_name} - {status} ({duration:.2f}s)")

        return {
            "test_name": test_name,
            "duration": duration,
            "passed": passed,
        }

    def before_suite(self, suite_name: str, **kwargs) -> Dict[str, Any]:
        """Called before test suite starts.

        Args:
            suite_name: Name of the test suite

        Returns:
            Context data
        """
        self.suite_start_time = time.time()
        logger.info(f"[HOOK] Before suite: {suite_name}")
        print(f"\n{'=' * 60}")
        print(f"Starting Test Suite: {suite_name}")
        print(f"{'=' * 60}")

        return {
            "suite_name": suite_name,
            "start_time": datetime.now().isoformat(),
        }

    def after_suite(self, suite_name: str, results: Any, **kwargs) -> Dict[str, Any]:
        """Called after test suite completes.

        Args:
            suite_name: Name of the test suite
            results: Suite results

        Returns:
            Context data
        """
        duration = 0.0
        if self.suite_start_time:
            duration = time.time() - self.suite_start_time

        total = getattr(results, "total", 0)
        passed = getattr(results, "passed", 0)
        failed = getattr(results, "failed", 0)

        logger.info(f"[HOOK] After suite: {suite_name} ({duration:.2f}s)")
        print(f"\n{'=' * 60}")
        print(f"Test Suite Completed: {suite_name}")
        print(f"  Total:  {total}")
        print(f"  Passed: {passed}")
        print(f"  Failed: {failed}")
        print(f"  Time:   {duration:.2f}s")
        print(f"{'=' * 60}\n")

        return {
            "suite_name": suite_name,
            "duration": duration,
            "total": total,
            "passed": passed,
            "failed": failed,
        }

    def on_error(
        self, error: Exception, context: Optional[Dict] = None, **kwargs
    ) -> None:
        """Called when an error occurs.

        Args:
            error: The exception that occurred
            context: Optional context information
        """
        logger.error(f"[HOOK] Error occurred: {error}")
        print(f"\n⚠️  ERROR: {error}")
        if context:
            print(f"   Context: {context}")


class PerformanceMonitorPlugin(IHookPlugin):
    """Example plugin that monitors test performance.

    Tracks execution times and reports slow tests.
    """

    name = "performance-monitor"
    version = "1.0.0"
    description = "Monitors test performance and reports slow tests"

    def __init__(self):
        self.timings: Dict[str, float] = {}
        self.slow_threshold: float = 1.0  # seconds

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the plugin."""
        if config:
            self.slow_threshold = config.get("slow_threshold", 1.0)
        print(f"✓ Performance Monitor initialized (threshold: {self.slow_threshold}s)")

    def shutdown(self) -> None:
        """Clean up and report."""
        self._report_slow_tests()
        print(f"✓ Performance Monitor shutdown")

    def register_hooks(self, hook_manager: HookManager) -> None:
        """Register performance monitoring hooks."""
        hook_manager.subscribe("before_test", self._track_start, priority=0)
        hook_manager.subscribe("after_test", self._track_end, priority=100)

    def _track_start(self, test_name: str, **kwargs) -> None:
        """Track test start time."""
        self.timings[test_name] = time.time()

    def _track_end(self, test_name: str, **kwargs) -> None:
        """Track test end and check if slow."""
        if test_name in self.timings:
            duration = time.time() - self.timings[test_name]

            if duration > self.slow_threshold:
                logger.warning(f"Slow test detected: {test_name} ({duration:.2f}s)")
                print(f"⚠️  Slow test: {test_name} took {duration:.2f}s")

    def _report_slow_tests(self) -> None:
        """Report all slow tests."""
        # This would be called at shutdown
        pass


# Plugin metadata for discovery
__plugin_metadata__ = {
    "name": TestLifecycleHooksPlugin.name,
    "version": TestLifecycleHooksPlugin.version,
    "description": TestLifecycleHooksPlugin.description,
    "author": "socialseed-e2e",
    "entry_point": "hook_plugin:TestLifecycleHooksPlugin",
    "tags": ["hooks", "lifecycle", "example"],
}


# Example usage
if __name__ == "__main__":
    print("=" * 60)
    print("Example: Hook Plugin")
    print("=" * 60)

    # Create hook manager
    from socialseed_e2e.plugins import HookManager

    hook_manager = HookManager()

    # Create and initialize plugin
    plugin = TestLifecycleHooksPlugin()
    plugin.initialize()
    plugin.register_hooks(hook_manager)

    # Simulate test execution
    class MockResult:
        def __init__(self, passed=True):
            self.passed = passed

    print("\n🚀 Simulating test execution:\n")

    # Suite start
    hook_manager.trigger("before_suite", suite_name="API Tests")

    # Test 1
    hook_manager.trigger("before_test", test_name="test_login")
    time.sleep(0.1)  # Simulate test execution
    hook_manager.trigger("after_test", test_name="test_login", result=MockResult(True))

    # Test 2
    hook_manager.trigger("before_test", test_name="test_create_user")
    time.sleep(0.2)
    hook_manager.trigger(
        "after_test", test_name="test_create_user", result=MockResult(True)
    )

    # Test 3 (failed)
    hook_manager.trigger("before_test", test_name="test_delete_user")
    time.sleep(0.15)
    hook_manager.trigger(
        "after_test", test_name="test_delete_user", result=MockResult(False)
    )

    # Suite end
    suite_results = type("obj", (object,), {"total": 3, "passed": 2, "failed": 1})()
    hook_manager.trigger("after_suite", suite_name="API Tests", results=suite_results)

    # Trigger error hook
    print("\n💥 Simulating error:")
    try:
        raise ValueError("Connection timeout")
    except Exception as e:
        hook_manager.trigger("on_error", error=e, context={"test": "test_login"})

    plugin.shutdown()

    print("\n" + "=" * 60)
    print("Example completed!")
    print("=" * 60)
