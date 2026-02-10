"""Example: Using AI-Powered Performance Profiling.

This example demonstrates how to use the performance profiling system
to track endpoint latency and detect performance regressions.
"""

from socialseed_e2e.performance import (
    EndpointPerformanceMetrics,
    PerformanceProfiler,
    SmartAlertGenerator,
    ThresholdAnalyzer,
)
from socialseed_e2e.performance.integration import create_profiling_page


def example_basic_profiling():
    """Example: Basic performance profiling."""
    print("=" * 70)
    print("Example 1: Basic Performance Profiling")
    print("=" * 70)

    # Create a profiler
    profiler = PerformanceProfiler(
        service_name="users-api",
        output_dir=".e2e/performance",
    )

    # Start profiling
    profiler.start_profiling()
    print("Profiling started...")

    # Simulate API calls
    import time

    for i in range(10):
        request_id = f"req-{i}"
        profiler.start_request(request_id, "GET", "https://api.example.com/users")

        # Simulate processing time
        time.sleep(0.01)

        profiler.end_request(request_id, 200)

    # Generate report
    profiler.stop_profiling()
    report = profiler.generate_report()

    print(f"\nPerformance Report:")
    print(f"  Service: {report.service_name}")
    print(f"  Total Requests: {report.total_requests}")
    print(f"  Avg Latency: {report.overall_avg_latency:.2f}ms")

    # Save report
    report_path = profiler.save_report(report)
    print(f"\nReport saved to: {report_path}")


def example_regression_detection():
    """Example: Detecting performance regressions."""
    print("\n" + "=" * 70)
    print("Example 2: Regression Detection")
    print("=" * 70)

    # Step 1: Create baseline report
    print("\n1. Creating baseline...")
    baseline_profiler = PerformanceProfiler(service_name="test-api")
    baseline_profiler.start_profiling()

    # Simulate baseline requests (fast)
    for i in range(10):
        request_id = f"base-{i}"
        baseline_profiler.start_request(request_id, "GET", "https://api.test/users")
        baseline_profiler.end_request(request_id, 200)

    baseline_report = baseline_profiler.generate_report()

    # Step 2: Simulate current run (slower - regression)
    print("2. Running current tests (with regression)...")
    current_profiler = PerformanceProfiler(service_name="test-api")
    current_profiler.start_profiling()

    # Simulate slower requests
    import time

    for i in range(10):
        request_id = f"curr-{i}"
        current_profiler.start_request(request_id, "GET", "https://api.test/users")
        time.sleep(0.05)  # Slower than baseline
        current_profiler.end_request(request_id, 200)

    current_report = current_profiler.generate_report()

    # Step 3: Detect regressions
    print("3. Analyzing for regressions...")
    analyzer = ThresholdAnalyzer(regression_threshold_pct=20.0)
    analyzer.baseline = baseline_report

    regressions = analyzer.detect_regressions(current_report)

    if regressions:
        print(f"\n⚠️  {len(regressions)} regression(s) detected!")

        # Step 4: Generate smart alerts
        print("4. Generating smart alerts...")
        alert_gen = SmartAlertGenerator()
        alerts = alert_gen.generate_alerts(current_report, regressions)

        for alert in alerts:
            print(f"\n[{alert.severity.value.upper()}] {alert.title}")
            print(alert.message)
            if alert.recommendations:
                print("\nRecommendations:")
                for rec in alert.recommendations[:3]:
                    print(f"  • {rec}")
    else:
        print("\n✅ No regressions detected")


def example_integration_with_basepage():
    """Example: Integrating with BasePage."""
    print("\n" + "=" * 70)
    print("Example 3: Integration with BasePage")
    print("=" * 70)

    # Create a profiling-enabled BasePage
    ProfilingPage = create_profiling_page(service_name="my-api")

    print("Created ProfilingPage class with automatic performance tracking")
    print("Usage:")
    print("""
    page = ProfilingPage("https://api.example.com")
    # Profiling is automatically enabled!
    
    # Make requests - all are automatically profiled
    response = page.get("/users")
    response = page.post("/users", data={"name": "John"})
    
    # Get performance report
    report = page.get_performance_report()
    print(f"Avg latency: {report.overall_avg_latency:.2f}ms")
    
    # Save report
    page.save_performance_report()
    """)


def example_custom_thresholds():
    """Example: Setting custom performance thresholds."""
    print("\n" + "=" * 70)
    print("Example 4: Custom Thresholds")
    print("=" * 70)

    from socialseed_e2e.performance import PerformanceThreshold

    # Create analyzer
    analyzer = ThresholdAnalyzer()

    # Add custom threshold for health checks
    health_threshold = PerformanceThreshold(
        endpoint_pattern=".*health.*",
        max_avg_latency_ms=50,  # Health checks should be very fast
        max_p95_latency_ms=100,
        regression_threshold_pct=20,  # Lower threshold for health
    )
    analyzer.add_threshold(health_threshold)

    # Add custom threshold for search endpoints
    search_threshold = PerformanceThreshold(
        endpoint_pattern=".*search.*",
        max_avg_latency_ms=2000,  # Search can be slower
        max_p95_latency_ms=5000,
        regression_threshold_pct=100,  # Higher tolerance
    )
    analyzer.add_threshold(search_threshold)

    print("Added custom thresholds:")
    print(f"  Health endpoints: max {health_threshold.max_avg_latency_ms}ms")
    print(f"  Search endpoints: max {search_threshold.max_avg_latency_ms}ms")


def example_trend_analysis():
    """Example: Analyzing performance trends."""
    print("\n" + "=" * 70)
    print("Example 5: Trend Analysis")
    print("=" * 70)

    from datetime import datetime, timedelta

    # Create analyzer
    analyzer = ThresholdAnalyzer()

    # Simulate loading historical reports
    print("Simulating loading 30 days of performance history...")

    base_time = datetime.utcnow() - timedelta(days=30)

    for i in range(30):
        report_time = base_time + timedelta(days=i)

        report = PerformanceProfiler(service_name="api").generate_report()
        report.timestamp = report_time

        # Add metrics with trend
        metrics = EndpointPerformanceMetrics(
            endpoint_path="/users",
            method="GET",
            avg_latency_ms=50.0 + (i * 2),  # Increasing trend
        )
        metrics.call_count = 100
        report.endpoints["GET /users"] = metrics

    # Get trend analysis
    trend = analyzer.get_trend_analysis("GET /users", "avg_latency_ms")

    print(f"\nTrend Analysis for GET /users:")
    print(f"  Trend: {trend.get('trend', 'unknown')}")
    if "change_percentage" in trend:
        print(f"  Change: {trend['change_percentage']:+.1f}%")
    print(f"  Data points: {trend.get('count', len(trend.get('values', [])))}")

    if trend.get("trend") == "increasing":
        print("\n⚠️  Warning: Performance is degrading over time!")
        print("   Consider investigating the root cause.")


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("AI-POWERED PERFORMANCE PROFILING - EXAMPLES")
    print("=" * 70)

    example_basic_profiling()
    example_regression_detection()
    example_integration_with_basepage()
    example_custom_thresholds()
    example_trend_analysis()

    print("\n" + "=" * 70)
    print("Examples completed!")
    print("=" * 70)
    print("\nFor more information, see docs/performance-profiling.md")


if __name__ == "__main__":
    main()
