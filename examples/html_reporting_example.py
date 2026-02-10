"""Example: HTML Report Generation for E2E Tests.

This example demonstrates how to use the HTML reporting system
to generate beautiful, interactive reports from test results.
"""

from socialseed_e2e.reporting import (
    HTMLReportGenerator,
    TestResult,
    TestResultCollector,
    TestStatus,
)
from socialseed_e2e.reporting.html_report_generator import generate_report


def example_basic_report():
    """Example: Generate a basic HTML report."""
    print("=" * 70)
    print("Example 1: Basic HTML Report Generation")
    print("=" * 70)

    # Create a test result collector
    collector = TestResultCollector(title="My E2E Test Suite")
    collector.start_collection()

    # Record some test results
    tests = [
        ("test_create_user", "users-api", TestStatus.PASSED, 150),
        ("test_get_user", "users-api", TestStatus.PASSED, 120),
        ("test_update_user", "users-api", TestStatus.PASSED, 180),
        ("test_delete_user", "users-api", TestStatus.FAILED, 200),
        ("test_create_order", "orders-api", TestStatus.PASSED, 250),
        ("test_slow_query", "orders-api", TestStatus.PASSED, 6000),
        ("test_deprecated_feature", "legacy-api", TestStatus.SKIPPED, 0),
    ]

    for i, (name, service, status, duration) in enumerate(tests):
        test_id = f"test-{i}"
        collector.record_test_start(test_id, name, service)

        if status == TestStatus.FAILED:
            collector.record_test_end(
                test_id,
                status=status.value,
                duration_ms=duration,
                error_message="User not found in database",
                stack_trace="Traceback (most recent call last):\n  ...",
            )
        else:
            collector.record_test_end(
                test_id, status=status.value, duration_ms=duration
            )

    # Generate the report
    report = collector.generate_report()

    # Generate HTML
    generator = HTMLReportGenerator()
    html_path = generator.generate(report, output_path="example-report.html")

    print(f"\nReport generated: {html_path}")
    print(f"\nStatistics:")
    print(f"  Total tests: {report.summary.total_tests}")
    print(f"  Passed: {report.summary.passed}")
    print(f"  Failed: {report.summary.failed}")
    print(f"  Skipped: {report.summary.skipped}")
    print(f"  Success rate: {report.summary.success_rate:.1f}%")


def example_multi_format_export():
    """Example: Export to multiple formats."""
    print("\n" + "=" * 70)
    print("Example 2: Multi-Format Export")
    print("=" * 70)

    # Create test results
    collector = TestResultCollector(title="Multi-Format Example")
    collector.start_collection()

    collector.record_test_start("test-1", "test_login", "auth-api")
    collector.record_test_end("test-1", "passed", duration_ms=100)

    collector.record_test_start("test-2", "test_logout", "auth-api")
    collector.record_test_end("test-2", "passed", duration_ms=80)

    report = collector.generate_report()

    # Export to multiple formats
    results = generate_report(
        report, output_dir="./example-reports", formats=["html", "csv", "json"]
    )

    print("\nReports generated:")
    for fmt, path in results.items():
        print(f"  {fmt.upper()}: {path}")


def example_custom_template():
    """Example: Using a custom template."""
    print("\n" + "=" * 70)
    print("Example 3: Custom Template (using default)")
    print("=" * 70)

    # In a real scenario, you would create a custom template
    # For this example, we'll use the default template

    collector = TestResultCollector(title="Custom Template Example")
    collector.start_collection()

    collector.record_test_start("test-1", "test_api", "service")
    collector.record_test_end("test-1", "passed", duration_ms=150)

    report = collector.generate_report()

    # Use custom template path (using default for demo)
    generator = HTMLReportGenerator()
    html_path = generator.generate(report, output_path="custom-template-example.html")

    print(f"\nReport with default template: {html_path}")
    print("\nTo use a custom template:")
    print('  generator = HTMLReportGenerator(template_path="my-template.html")')


def example_analyze_results():
    """Example: Analyze test results."""
    print("\n" + "=" * 70)
    print("Example 4: Analyzing Test Results")
    print("=" * 70)

    collector = TestResultCollector()
    collector.start_collection()

    # Add tests with varying results
    tests = [
        ("test_1", "users-api", "passed", 100),
        ("test_2", "users-api", "passed", 120),
        ("test_3", "users-api", "failed", 200),
        ("test_4", "orders-api", "passed", 5000),
        ("test_5", "orders-api", "passed", 7000),
        ("test_6", "legacy-api", "skipped", 0),
    ]

    for i, (name, service, status, duration) in enumerate(tests):
        test_id = f"test-{i}"
        collector.record_test_start(test_id, name, service)
        collector.record_test_end(test_id, status=status, duration_ms=duration)

    # Analyze results
    print("\nAnalysis Results:")

    # Failed tests
    failed = collector.get_failed_tests()
    print(f"\nFailed tests: {len(failed)}")
    for test in failed:
        print(f"  - {test.name} ({test.service})")

    # Slow tests (> 5 seconds)
    slow = collector.get_slow_tests(threshold_ms=5000)
    print(f"\nSlow tests (> 5s): {len(slow)}")
    for test in slow:
        print(f"  - {test.name}: {test.duration_formatted}")

    # Stats by service
    stats = collector.get_stats_by_service()
    print("\nStats by service:")
    for service, counts in stats.items():
        success_rate = (
            (counts["passed"] / counts["total"] * 100) if counts["total"] > 0 else 0
        )
        print(
            f"  {service}: {counts['passed']}/{counts['total']} passed ({success_rate:.1f}%)"
        )


def example_cli_usage():
    """Example: CLI usage demonstration."""
    print("\n" + "=" * 70)
    print("Example 5: CLI Usage")
    print("=" * 70)

    print("\nCLI Examples:")
    print("\n1. Run tests and generate HTML report:")
    print("   e2e run --output html")

    print("\n2. Run tests and save report to custom directory:")
    print("   e2e run --output html --report-dir ./my-reports")

    print("\n3. Run specific service with HTML report:")
    print("   e2e run --service users-api --output html")

    print("\n4. Generate multiple formats:")
    print("   e2e run --output html")
    print("   # This generates HTML, CSV, and JSON reports")

    print("\nReport Features:")
    print("  ✓ Interactive charts and statistics")
    print("  ✓ Filter by status (passed/failed/skipped)")
    print("  ✓ Filter by service")
    print("  ✓ Search by test name")
    print("  ✓ Export to CSV, JSON, or PDF")
    print("  ✓ Responsive design for mobile/tablet")


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("HTML REPORT GENERATION - EXAMPLES")
    print("=" * 70)

    import tempfile
    import os

    # Change to temp directory for examples
    original_dir = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)

        example_basic_report()
        example_multi_format_export()
        example_custom_template()
        example_analyze_results()
        example_cli_usage()

    os.chdir(original_dir)

    print("\n" + "=" * 70)
    print("Examples completed!")
    print("=" * 70)
    print("\nGenerated files are in the temporary directory.")
    print("For real usage, files will be saved to your specified location.")
    print("\nFor more information, see docs/html-reporting.md")


if __name__ == "__main__":
    main()
