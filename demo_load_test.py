"""Demo script for simulating high-load performance testing."""

import asyncio
import random

from socialseed_e2e.performance import (
    LoadGenerator,
    MetricsCollector,
    PerformanceDashboard,
    SLAPolicy,
)


async def simulated_api_call():
    """Simulate an API call with random latency and occasional failures."""
    # Simulate processing time between 10ms and 150ms
    latency = random.uniform(0.01, 0.15)
    await asyncio.sleep(latency)

    # 5% chance of failure
    if random.random() < 0.05:
        raise Exception("Simulated API Error 500")

    return {"status": "success"}


async def main():
    """Run the high-load simulation and generate a report."""
    print("🚀 Starting High-Load Simulated Test...")
    print("Pattern: 100 concurrent users for 10 seconds")

    # 1. Initialize Generator
    gen = LoadGenerator(target_func=simulated_api_call)

    # 2. Run Load (Constant)
    results = await gen.run_constant_load(users=100, duration_seconds=10)

    # 3. Collect and Analyze Metrics
    collector = MetricsCollector(
        latencies=results.latencies,
        total_requests=results.total_requests,
        failed_requests=results.failed_requests,
    )
    summary = collector.get_summary()

    # 4. Validate SLA
    sla = SLAPolicy(max_avg_latency_ms=100.0, p95_latency_ms=150.0, max_error_rate=0.10)
    violations = collector.validate_sla(sla)

    # 5. Generate Dashboard
    dashboard = PerformanceDashboard(report_dir=".e2e/performance/demo_reports")
    report_path = dashboard.generate_html_report(summary, test_name="CI/CD Load Test Demo")

    # Results Presentation
    print("\n" + "=" * 40)
    print("📊 LOAD TEST RESULTS SUMMARY")
    print("=" * 40)
    print(f"Total Requests:   {summary['total_requests']}")
    print(f"Successful:       {summary['total_requests'] - summary['failed_requests']}")
    print(f"Failed:           {summary['failed_requests']} ({summary['error_rate']*100:.2f}%)")
    print("-" * 20)
    print(f"Avg Latency:      {summary['avg_latency']:.2f} ms")
    print(f"P50 (Median):     {summary['p50']:.2f} ms")
    print(f"P95:              {summary['p95']:.2f} ms")
    print(f"P99:              {summary['p99']:.2f} ms")
    print(f"Max Latency:      {summary['max_latency']:.2f} ms")
    print("-" * 20)

    if violations:
        print("❌ SLA VIOLATIONS DETECTED:")
        for v in violations:
            print(f"  - {v}")
    else:
        print("✅ SLA VALIDATION PASSED")

    print("=" * 40)
    print(f"📈 Dashboard Report generated at: {report_path}")
    print("=" * 40)


if __name__ == "__main__":
    asyncio.run(main())
