"""Example: Custom Reporter Plugin.

This example demonstrates how to create a custom test reporter plugin
that tracks test execution and generates reports.

Usage:
    1. Save this file as a plugin
    2. Configure the plugin manager to load it
    3. Run your tests - the plugin will track execution
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from socialseed_e2e.plugins import (
    HookManager,
    ITestReporterPlugin,
    PluginMetadata,
)


class JSONReporterPlugin(ITestReporterPlugin):
    """Example plugin that generates JSON test reports.

    This plugin tracks test execution and generates a JSON report
    with detailed information about each test.

    Attributes:
        name: Plugin identifier
        version: Plugin version
        description: Plugin description
    """

    name = "json-reporter"
    version = "1.0.0"
    description = "Generates JSON test execution reports"

    def __init__(self):
        self.test_results: List[Dict[str, Any]] = []
        self.suite_results: List[Dict[str, Any]] = []
        self.output_path: str = "test-report.json"
        self.start_time: Optional[datetime] = None

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the plugin with configuration.

        Args:
            config: Configuration dictionary with optional 'output_path'
        """
        if config:
            self.output_path = config.get("output_path", self.output_path)
        print(f"✓ JSON Reporter initialized (output: {self.output_path})")

    def shutdown(self) -> None:
        """Clean up resources and generate final report."""
        self.generate_report(self.output_path)
        print(f"✓ JSON Reporter shutdown")

    def on_test_start(self, test_name: str) -> None:
        """Called when a test starts.

        Args:
            test_name: Name of the test
        """
        self.start_time = datetime.now()
        print(f"  📋 Starting test: {test_name}")

    def on_test_end(self, test_name: str, result: Any) -> None:
        """Called when a test ends.

        Args:
            test_name: Name of the test
            result: Test result object
        """
        duration = 0.0
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()

        test_result = {
            "name": test_name,
            "status": getattr(result, "status", "unknown"),
            "duration": duration,
            "timestamp": datetime.now().isoformat(),
            "passed": getattr(result, "passed", False),
        }
        self.test_results.append(test_result)

        status_icon = "✓" if test_result["passed"] else "✗"
        print(f"  {status_icon} Test completed: {test_name} ({duration:.2f}s)")

    def on_suite_start(self, suite_name: str) -> None:
        """Called when a test suite starts.

        Args:
            suite_name: Name of the test suite
        """
        print(f"\n🧪 Starting test suite: {suite_name}")
        self.suite_results.append(
            {
                "name": suite_name,
                "start_time": datetime.now().isoformat(),
            }
        )

    def on_suite_end(self, suite_name: str, results: Any) -> None:
        """Called when a test suite ends.

        Args:
            suite_name: Name of the test suite
            results: Suite results object
        """
        # Update the suite record
        for suite in self.suite_results:
            if suite["name"] == suite_name:
                suite["end_time"] = datetime.now().isoformat()
                suite["total_tests"] = getattr(results, "total", 0)
                suite["passed"] = getattr(results, "passed", 0)
                suite["failed"] = getattr(results, "failed", 0)

        print(f"✓ Suite completed: {suite_name}")

    def generate_report(self, output_path: str) -> None:
        """Generate JSON report.

        Args:
            output_path: Path where to save the report
        """
        report = {
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_tests": len(self.test_results),
                "passed": sum(1 for r in self.test_results if r["passed"]),
                "failed": sum(1 for r in self.test_results if not r["passed"]),
            },
            "test_results": self.test_results,
            "suite_results": self.suite_results,
        }

        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

        print(f"\n📊 Report generated: {output_path}")
        print(f"   Total tests: {report['summary']['total_tests']}")
        print(f"   Passed: {report['summary']['passed']}")
        print(f"   Failed: {report['summary']['failed']}")


# Plugin metadata for discovery
__plugin_metadata__ = {
    "name": JSONReporterPlugin.name,
    "version": JSONReporterPlugin.version,
    "description": JSONReporterPlugin.description,
    "author": "socialseed-e2e",
    "entry_point": "json_reporter_plugin:JSONReporterPlugin",
    "tags": ["reporter", "json", "example"],
}


# Example usage
if __name__ == "__main__":
    print("=" * 60)
    print("Example: JSON Reporter Plugin")
    print("=" * 60)

    # Create plugin
    plugin = JSONReporterPlugin()

    # Initialize
    plugin.initialize({"output_path": "/tmp/test-report.json"})

    # Simulate test execution
    class MockResult:
        def __init__(self, passed=True):
            self.passed = passed
            self.status = "passed" if passed else "failed"

    plugin.on_suite_start("Authentication Tests")
    plugin.on_test_start("test_login")
    plugin.on_test_end("test_login", MockResult(passed=True))
    plugin.on_test_start("test_logout")
    plugin.on_test_end("test_logout", MockResult(passed=True))
    plugin.on_suite_end(
        "Authentication Tests",
        type("obj", (object,), {"total": 2, "passed": 2, "failed": 0})(),
    )

    plugin.on_suite_start("User Tests")
    plugin.on_test_start("test_create_user")
    plugin.on_test_end("test_create_user", MockResult(passed=True))
    plugin.on_test_start("test_delete_user")
    plugin.on_test_end("test_delete_user", MockResult(passed=False))
    plugin.on_suite_end(
        "User Tests", type("obj", (object,), {"total": 2, "passed": 1, "failed": 1})()
    )

    # Shutdown (generates report)
    plugin.shutdown()

    print("\n" + "=" * 60)
    print("Example completed!")
    print("=" * 60)
