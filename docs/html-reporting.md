# Interactive HTML Report Generation

**Issue #50** - Beautiful HTML reports for E2E test results

## Overview

The HTML Report Generation system creates beautiful, interactive HTML reports from E2E test results. Features include charts, statistics, filtering, search, and export capabilities.

## Features

✅ **Beautiful Design** - Modern, responsive HTML5 interface  
✅ **Interactive Charts** - Doughnut charts showing test distribution  
✅ **Statistics Cards** - Summary of passed, failed, and skipped tests  
✅ **Filtering** - Filter by status, service, or search by name  
✅ **Test Details** - View detailed error messages and stack traces  
✅ **Export** - Export to CSV, JSON, or PDF  
✅ **Responsive** - Works on desktop, tablet, and mobile  

## Quick Start

### CLI Usage

Generate HTML report when running tests:

```bash
# Run tests and generate HTML report
e2e run --output html

# Run tests and generate HTML report in custom directory
e2e run --output html --report-dir ./my-reports

# Run specific service and generate report
e2e run --service users-api --output html
```

### Programmatic Usage

```python
from socialseed_e2e.reporting import TestResultCollector, HTMLReportGenerator

# Collect test results
collector = TestResultCollector(title="My Test Suite")
collector.start_collection()

# Record test results during execution
collector.record_test_start("test-1", "test_create_user", "users-api")
collector.record_test_end("test-1", "passed", duration_ms=150)

collector.record_test_start("test-2", "test_delete_user", "users-api")
collector.record_test_end("test-2", "failed", duration_ms=200, 
                          error_message="User not found")

# Generate report
report = collector.generate_report()

# Generate HTML
generator = HTMLReportGenerator()
html_path = generator.generate(report, output_path="report.html")

print(f"Report generated: {html_path}")
```

## Report Features

### Summary Cards

The report displays summary cards showing:
- **Tests Passed** - Number and visual indicator
- **Tests Failed** - Number and visual indicator  
- **Tests Skipped** - Number and visual indicator
- **Success Rate** - Percentage of passed tests

### Interactive Charts

- Doughnut chart showing test distribution
- Visual representation of pass/fail/skip ratio
- Responsive and animated

### Test List

Comprehensive test list with:
- Test name
- Service/module
- Status badge (passed/failed/skipped)
- Duration
- Details button

### Filtering & Search

Filter tests by:
- **Status** - All, Passed, Failed, Skipped
- **Service** - Filter by service name
- **Search** - Text search by test name

### Test Details Modal

Click "View Details" to see:
- Test name and service
- Status and duration
- Timestamp
- Error message (if failed)
- Stack trace (if failed)
- Request/response data (if available)

## Export Options

### Export to CSV

```python
from socialseed_e2e.reporting import HTMLReportGenerator

generator = HTMLReportGenerator()
csv_path = generator.export_to_csv(report, output_path="report.csv")
```

CSV format:
```csv
Test Name,Service,Status,Duration (ms),Timestamp,Error Message
test_create_user,users-api,passed,150,2026-01-15T10:30:00,
test_delete_user,users-api,failed,200,2026-01-15T10:30:05,User not found
```

### Export to JSON

```python
json_path = generator.export_to_json(report, output_path="report.json")
```

JSON format:
```json
{
  "title": "E2E Test Report",
  "summary": {
    "total_tests": 10,
    "passed": 8,
    "failed": 1,
    "skipped": 1,
    "success_rate": 80.0
  },
  "tests": [
    {
      "id": "test-1",
      "name": "test_create_user",
      "service": "users-api",
      "status": "passed",
      "duration": "150ms"
    }
  ]
}
```

### Export to PDF

In the HTML report, click the "Export to PDF" button or use:

```bash
# Open the HTML report in a browser and print to PDF
# Or use a tool like wkhtmltopdf
wkhtmltopdf report.html report.pdf
```

## CLI Options

### `e2e run --output html`

Run tests and generate HTML report.

**Options:**
- `--output html` - Generate HTML report
- `--report-dir` - Directory for reports (default: .e2e/reports)

**Examples:**
```bash
# Generate HTML report
e2e run --output html

# Custom report directory
e2e run --output html --report-dir ./reports

# Specific service with HTML report
e2e run --service users-api --output html

# Verbose with HTML report
e2e run --output html --verbose
```

## Report Data Model

### TestResult

```python
from socialseed_e2e.reporting import TestResult, TestStatus

result = TestResult(
    id="test-1",
    name="test_create_user",
    service="users-api",
    status=TestStatus.PASSED,
    duration_ms=150,
    error_message=None,
    stack_trace=None,
)
```

### ReportSummary

```python
from socialseed_e2e.reporting import ReportSummary

summary = ReportSummary(
    total_tests=100,
    passed=80,
    failed=15,
    skipped=5,
    total_duration_ms=45000
)

print(f"Success Rate: {summary.success_rate}%")
print(f"Duration: {summary.duration_formatted}")
```

## Custom Templates

You can use a custom HTML template:

```python
from pathlib import Path
from socialseed_e2e.reporting import HTMLReportGenerator

# Use custom template
generator = HTMLReportGenerator(
    template_path=Path("my-template.html")
)

html_path = generator.generate(report)
```

### Template Variables

Available template variables:
- `{{ title }}` - Report title
- `{{ timestamp }}` - Generation timestamp
- `{{ duration }}` - Total duration
- `{{ total_passed }}` - Number of passed tests
- `{{ total_failed }}` - Number of failed tests
- `{{ total_skipped }}` - Number of skipped tests
- `{{ success_rate }}` - Success rate percentage
- `{{#tests}}...{{/tests}}` - Test list loop
- `{{#services}}...{{/services}}` - Services list loop

## Advanced Usage

### Record Tests Automatically

Use the decorator to automatically record tests:

```python
from socialseed_e2e.reporting.test_result_collector import record_test

@record_test
def test_create_user(collector):
    # Test code here
    pass
```

### Analyze Test Results

```python
from socialseed_e2e.reporting import TestResultCollector

collector = TestResultCollector()
collector.start_collection()

# ... run tests ...

report = collector.generate_report()

# Get failed tests
failed = collector.get_failed_tests()
print(f"Failed tests: {len(failed)}")

# Get slow tests
slow = collector.get_slow_tests(threshold_ms=5000)
print(f"Slow tests: {len(slow)}")

# Get stats by service
stats = collector.get_stats_by_service()
for service, counts in stats.items():
    print(f"{service}: {counts['passed']}/{counts['total']} passed")
```

### Generate Reports in Multiple Formats

```python
from socialseed_e2e.reporting.html_report_generator import generate_report

# Generate HTML, CSV, and JSON reports
results = generate_report(
    report,
    output_dir=".e2e/reports",
    formats=["html", "csv", "json"]
)

print(f"HTML: {results['html']}")
print(f"CSV: {results['csv']}")
print(f"JSON: {results['json']}")
```

## Report Customization

### Custom Styling

The default template uses modern CSS with:
- CSS Grid for responsive layouts
- Flexbox for component alignment
- CSS transitions for smooth animations
- Media queries for mobile responsiveness

You can customize the template with your own styles.

### Adding Custom Data

```python
from socialseed_e2e.reporting import TestResult

result = TestResult(
    id="test-1",
    name="test_create_user",
    service="users-api",
    status=TestStatus.PASSED,
    duration_ms=150,
    metadata={
        "environment": "staging",
        "browser": "chrome",
        "user_agent": "Mozilla/5.0..."
    }
)
```

## Best Practices

### 1. Organize by Service

Structure your tests by service for better organization:

```python
collector.record_test_start("test-1", "test_create", "users-api")
collector.record_test_start("test-2", "test_delete", "users-api")
collector.record_test_start("test-3", "test_create", "orders-api")
```

### 2. Include Error Details

Always include error details for failed tests:

```python
try:
    # Run test
    pass
except Exception as e:
    import traceback
    collector.record_test_end(
        test_id,
        status="failed",
        error_message=str(e),
        stack_trace=traceback.format_exc()
    )
```

### 3. Track Duration

Track test duration for performance analysis:

```python
import time

start_time = time.time()
# Run test
end_time = time.time()

duration_ms = (end_time - start_time) * 1000
collector.record_test_end(test_id, "passed", duration_ms=duration_ms)
```

### 4. Archive Reports

Archive old reports for historical comparison:

```bash
# Add timestamp to reports
e2e run --output html --report-dir "./reports/$(date +%Y%m%d_%H%M%S)"
```

## Integration with CI/CD

### GitHub Actions

```yaml
- name: Run E2E Tests with HTML Report
  run: e2e run --output html --report-dir ./e2e-reports

- name: Upload HTML Report
  uses: actions/upload-artifact@v2
  with:
    name: e2e-report
    path: ./e2e-reports/*.html
```

### GitLab CI

```yaml
e2e_tests:
  script:
    - e2e run --output html --report-dir ./e2e-reports
  artifacts:
    paths:
      - ./e2e-reports/*.html
    expire_in: 1 week
```

## Troubleshooting

### Report Not Generated

If the HTML report is not generated:

1. Check the `--report-dir` path exists and is writable
2. Verify the template file exists (default: `templates/report.html.template`)
3. Check for errors in the console output

### Large Reports

For large test suites, the HTML file may be large. To optimize:

1. Use pagination in the template
2. Filter tests by status or service
3. Export to CSV for data analysis

### Custom Fonts

The default template uses system fonts. To use custom fonts:

```html
<!-- In your custom template -->
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
<style>
  body { font-family: 'Inter', sans-serif; }
</style>
```

## Example Report Structure

```
.e2e/reports/
├── report_20260115_103000.html
├── report_20260115_103000.csv
├── report_20260115_103000.json
├── report_20260115_113000.html
└── report_20260115_113000.csv
```

## Browser Compatibility

The HTML reports work in all modern browsers:
- Chrome/Edge 80+
- Firefox 75+
- Safari 13+
- Mobile browsers (iOS Safari, Chrome Mobile)

## Future Enhancements

- [ ] Dark mode support
- [ ] Test history trends
- [ ] Performance graphs over time
- [ ] Integration with test management tools
- [ ] Email report notifications
- [ ] Slack/Teams notifications
