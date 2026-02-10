# AI-Powered Performance Profiling and Bottleneck Detection

**Issue #87** - Automated performance insights and regression detection

## Overview

The Performance Profiling system automatically tracks endpoint latency during E2E test runs, detects performance regressions, and provides AI-powered insights with specific recommendations.

## Features

✅ **Latency Tracking** - Measure response time of every endpoint  
✅ **Percentile Analysis** - Track P50, P95, P99 latencies  
✅ **Regression Detection** - Compare with baseline and detect degradation  
✅ **Smart Alerts** - AI-powered alerts with context and recommendations  
✅ **Trend Analysis** - Track performance trends over time  
✅ **Integration** - Seamless integration with BasePage  

## Quick Start

### CLI Usage

#### 1. Profile Your Tests

Start a profiling session and run your E2E tests:

```bash
# Start profiling
e2e perf-profile --service users-api

# Run your tests in another terminal
e2e run --service users-api

# Press Ctrl+C in the profiling terminal when done
```

#### 2. Set Baseline

Set current performance as baseline for future comparisons:

```bash
e2e perf-profile --service users-api --set-baseline
```

#### 3. Detect Regressions

Compare with baseline after code changes:

```bash
e2e perf-profile --service users-api --compare-baseline
```

#### 4. Generate Reports

Generate detailed performance reports:

```bash
# Text report
e2e perf-report

# JSON report
e2e perf-report -f json

# Markdown report
e2e perf-report -f markdown
```

## Programmatic Usage

### Basic Usage

```python
from socialseed_e2e.performance import PerformanceProfiler

# Create profiler
profiler = PerformanceProfiler(
    service_name="users-api",
    output_dir=".e2e/performance"
)

# Start profiling
profiler.start_profiling()

# Run your tests
page.get("/users")
page.post("/users", data={"name": "John"})

# Stop and generate report
profiler.stop_profiling()
report = profiler.generate_report()

# Save to disk
profiler.save_report(report)

print(f"Avg latency: {report.overall_avg_latency:.2f}ms")
```

### Integration with BasePage

```python
from socialseed_e2e.performance.integration import PerformanceMixin
from socialseed_e2e import BasePage

# Create profiling-enabled page
class ProfilingBasePage(PerformanceMixin, BasePage):
    pass

# Use in tests
page = ProfilingBasePage("https://api.example.com")
page.enable_profiling(service_name="users-api")

# All requests are automatically profiled
response = page.get("/users")
response = page.post("/users", data={"name": "John"})

# Get report
report = page.get_performance_report()
page.save_performance_report()
```

### Using Decorator

```python
from socialseed_e2e.performance.integration import profile_endpoint

class TestUsers:
    @profile_endpoint
    def test_create_user(self, page):
        response = page.post("/users", data={"name": "John"})
        assert response.status == 201
        # Performance metrics automatically captured
```

## Regression Detection

### Detect Performance Regressions

```python
from socialseed_e2e.performance import ThresholdAnalyzer, SmartAlertGenerator

# Load baseline and compare
analyzer = ThresholdAnalyzer(regression_threshold_pct=50.0)
analyzer.load_baseline()

# Detect regressions
regressions = analyzer.detect_regressions(current_report)

# Generate smart alerts
alert_gen = SmartAlertGenerator(project_root="/path/to/project")
alerts = alert_gen.generate_alerts(current_report, regressions)

for alert in alerts:
    print(f"[{alert.severity.value}] {alert.title}")
    print(alert.message)
    print("Recommendations:")
    for rec in alert.recommendations:
        print(f"  - {rec}")
```

### Example Alert Output

```
🔴 CRITICAL: Latency Increased: GET /users

Endpoint: GET /users
Metric: Latency Increase

Previous Value: 100.00 ms
Current Value: 250.00 ms
Change: +150.0%

⚠️ CRITICAL: This regression is severe and should be addressed immediately.
The latency has more than doubled, which will significantly impact user experience.

Suspected code block:
def get_users():
    # This function was recently modified
    users = User.objects.all()  # N+1 query problem detected
    return [u.to_dict() for u in users]

Recommendations:
  • Check for missing database indexes on queries used by this endpoint
  • Review recent database schema changes that might affect this endpoint
  • Consider implementing caching for this endpoint
  • Check for N+1 query problems in the endpoint implementation
```

## Performance Metrics

### Tracked Metrics

- **Call Count**: Number of requests made
- **Avg Latency**: Average response time
- **Min/Max Latency**: Range of response times
- **P50/P95/P99**: Latency percentiles
- **Error Rate**: Percentage of failed requests
- **Throughput**: Requests per second

### Thresholds

Default thresholds can be customized:

```python
from socialseed_e2e.performance import PerformanceThreshold

# Add custom threshold
threshold = PerformanceThreshold(
    endpoint_pattern="/api/.*",
    max_avg_latency_ms=500,
    max_p95_latency_ms=1000,
    max_error_rate=1.0,
    regression_threshold_pct=30.0
)

analyzer.add_threshold(threshold)
```

## CLI Commands

### `e2e perf-profile`

Run performance profiling session.

**Options:**
- `--service, -s` - Service name (default: "unknown")
- `--output, -o` - Output directory (default: ".e2e/performance")
- `--threshold, -t` - Regression threshold % (default: 50)
- `--compare-baseline` - Compare with baseline
- `--set-baseline` - Set current as baseline

**Examples:**
```bash
# Basic profiling
e2e perf-profile

# Profile specific service
e2e perf-profile --service users-api

# Profile and compare
e2e perf-profile --compare-baseline

# Set baseline
e2e perf-profile --set-baseline
```

### `e2e perf-report`

Generate performance analysis report.

**Options:**
- `--output, -o` - Reports directory
- `--baseline, -b` - Path to baseline
- `--threshold, -t` - Regression threshold %
- `--format, -f` - Output format (text, json, markdown)

**Examples:**
```bash
# Text report
e2e perf-report

# JSON output
e2e perf-report -f json > report.json

# Markdown report
e2e perf-report -f markdown > PERFORMANCE_REPORT.md
```

## Report Format

### JSON Report Structure

```json
{
  "test_run_id": "abc123",
  "timestamp": "2026-01-15T10:30:00",
  "service_name": "users-api",
  "total_requests": 1000,
  "overall_avg_latency": 45.5,
  "endpoints": {
    "GET /users": {
      "path": "/users",
      "method": "GET",
      "call_count": 500,
      "avg_latency_ms": 42.3,
      "p95_latency_ms": 85.2,
      "p99_latency_ms": 120.5,
      "error_rate": 0.1
    }
  },
  "regressions": [
    {
      "endpoint": "GET /users",
      "type": "latency_increase",
      "change_pct": 55.3,
      "severity": "warning"
    }
  ],
  "alerts": [],
  "summary": "Performance Report Summary..."
}
```

## Best Practices

### 1. Set Baselines Regularly

Set a new baseline after performance improvements:

```bash
e2e perf-profile --set-baseline
```

### 2. Profile in CI/CD

Add profiling to your CI pipeline:

```yaml
# GitHub Actions example
- name: Performance Profiling
  run: |
    e2e perf-profile --service api --compare-baseline
  continue-on-error: true  # Don't fail build, just report
```

### 3. Monitor Trends

Track performance over time:

```python
analyzer = ThresholdAnalyzer()
analyzer.load_history(days=30)

trend = analyzer.get_trend_analysis("GET /users")
print(f"Trend: {trend['trend']}, Change: {trend['change_percentage']:.1f}%")
```

### 4. Investigate Regressions

When alerts fire:

1. Check the suspected code block in the alert
2. Review recent changes to that code
3. Run profiler with `--set-baseline` after fixing
4. Document the fix in your changelog

### 5. Set Appropriate Thresholds

Different endpoints have different requirements:

```python
# Health checks should be fast
health_threshold = PerformanceThreshold(
    endpoint_pattern=".*health.*",
    max_avg_latency_ms=50,
    max_p95_latency_ms=100
)

# Search endpoints can be slower
search_threshold = PerformanceThreshold(
    endpoint_pattern=".*search.*",
    max_avg_latency_ms=2000,
    max_p95_latency_ms=5000
)
```

## Troubleshooting

### No Baseline Found

```
⚠ No baseline found. Run with --set-baseline first.
```

**Solution:** Run profiling with `--set-baseline` flag.

### High Variability

If you see inconsistent results:

1. Run tests multiple times and average
2. Ensure test environment is consistent
3. Check for background processes
4. Increase warmup time before profiling

### False Positives

If you're getting too many alerts:

1. Adjust threshold percentage: `--threshold 100`
2. Add custom thresholds for specific endpoints
3. Focus on P95/P99 instead of average

## Performance Report Examples

### Healthy System

```
======================================================================
AI-POWERED PERFORMANCE ANALYSIS REPORT
======================================================================

Service: users-api
Test Run: xyz789
Timestamp: 2026-01-15T10:30:00

Total Requests: 1000
Overall Avg Latency: 45.23ms
Endpoints Analyzed: 15

✅ NO REGRESSIONS DETECTED

All endpoints are performing within expected thresholds.
======================================================================
```

### System with Regressions

```
======================================================================
AI-POWERED PERFORMANCE ANALYSIS REPORT
======================================================================

Service: users-api
Test Run: abc123
Timestamp: 2026-01-15T11:45:00

Total Requests: 1000
Overall Avg Latency: 89.45ms
Endpoints Analyzed: 15

REGRESSIONS DETECTED
----------------------------------------------------------------------
Total: 3

🔴 CRITICAL:

  - GET /users: +150.0% (latency_increase)

🟡 WARNINGS:

  - POST /users: +65.0% (p95_increase)
  - GET /orders: +55.0% (latency_increase)

======================================================================
```

## Integration with Other Features

### Combine with Mock API Testing

```python
# Profile tests with mocked external APIs
profiler = PerformanceProfiler()
profiler.start_profiling()

# Run tests with mocks
e2e mock-run -s stripe
e2e run --service payment-api

profiler.stop_profiling()
```

### Security Testing Integration

```python
# Profile security fuzzing tests
profiler = PerformanceProfiler()
profiler.start_profiling()

# Run security tests
e2e security-test --service users-api

profiler.stop_profiling()
```

## API Reference

### PerformanceProfiler

Main class for profiling E2E tests.

**Methods:**
- `start_profiling()` - Start profiling session
- `stop_profiling()` - Stop profiling session
- `start_request(request_id, method, url)` - Mark request start
- `end_request(request_id, status_code, error)` - Mark request end
- `generate_report()` - Generate performance report
- `save_report(report)` - Save report to disk

### ThresholdAnalyzer

Analyze performance against baselines and thresholds.

**Methods:**
- `load_baseline(path)` - Load baseline report
- `detect_regressions(report)` - Detect performance regressions
- `set_baseline(report)` - Set current as baseline
- `get_trend_analysis(endpoint, metric)` - Get trend analysis

### SmartAlertGenerator

Generate intelligent alerts with context.

**Methods:**
- `generate_alerts(report, regressions)` - Generate alerts
- `generate_summary_report(report, regressions)` - Generate summary

## Future Enhancements

- [ ] CPU/Memory profiling integration
- [ ] Database query profiling
- [ ] Flame graph generation
- [ ] Performance prediction using ML
- [ ] Automated performance optimization suggestions
