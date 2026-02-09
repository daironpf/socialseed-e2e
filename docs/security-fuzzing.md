# AI-Driven Intelligent Fuzzing and Security Testing (Issue #189)

## Overview

The **AI-Driven Security Fuzzer** provides intelligent security testing capabilities that automatically generate malicious payloads, test API resilience, and detect vulnerabilities including SQL Injection, NoSQL Injection, Buffer Overflow, and logic-breaking attacks.

## Features

### 🔐 Malicious Payload Generation
- **SQL Injection**: Classic, Union-based, Error-based, Time-based blind, Boolean-based blind
- **NoSQL Injection**: MongoDB-style injection payloads
- **Buffer Overflow**: Large blobs (1KB to 10MB+), overflow patterns
- **Type Manipulation**: Sending wrong types (strings where integers expected)
- **XSS**: Cross-site scripting payloads
- **Command Injection**: OS command injection attempts
- **Path Traversal**: Directory traversal attacks

### 📊 Resilience Monitoring
- Tracks server crashes (500 errors) vs proper validation (400/422)
- Measures response times during attacks
- Calculates resilience score (0-100%)
- Detects security bypass attempts

### 🚨 Vulnerability Reporting
- Detailed markdown reports
- Severity classification (Critical, High, Medium, Low)
- Attack type breakdown
- Specific payloads that bypassed validation
- Recommendations for fixes

## Usage

### Quick Start

```bash
# Run security tests on all services
e2e security-test

# Test specific service
e2e security-test --service users-api

# Thorough testing with more payloads
e2e security-test --max-payloads 50

# Specific attack types only
e2e security-test --attack-types sql,nosql

# Custom output report
e2e security-test --output my-security-report.md
```

### CLI Options

```bash
e2e security-test [DIRECTORY] [OPTIONS]
```

**Arguments:**
- `DIRECTORY`: Project directory (default: current directory)

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--service` | `-s` | Service to test | All services |
| `--max-payloads` | `-m` | Payloads per field | 10 |
| `--output` | `-o` | Report filename | SECURITY_REPORT.md |
| `--attack-types` | `-a` | Attack types (comma-separated) | All |

## Example Output

```
🔒 AI Security Fuzzing
   Project: /home/user/my-api

🎯 Testing service: users-api
   Total tests: 450
   Blocked: 448
   Vulnerabilities: 2
   ⚠ 2 vulnerabilities found!

📝 Generating security report...
   ✓ Report saved: .e2e/SECURITY_REPORT.md

============================================================
🔒 Security Testing Complete
============================================================

📊 Summary:
   Services tested: 1
   Total tests: 450
   Vulnerabilities found: 2
   Average resilience score: 99.6%

   ⚠ 2 vulnerabilities require attention!
   📄 See report: .e2e/SECURITY_REPORT.md
```

## Report Format

### Executive Summary
```markdown
# 🔒 Security Fuzzing Report

**Session ID:** `abc123`
**Start Time:** 2026-02-08 15:30:00
**End Time:** 2026-02-08 15:35:00

## 📊 Executive Summary

**Total Tests Executed:** 450
**Tests Passed (Blocked):** 448
**Tests Failed:** 2
**Vulnerabilities Found:** 2
**Resilience Score:** 99.6%

🟢 **Resilience Level:** Excellent - API properly validates and blocks attacks
```

### Vulnerability Details
```markdown
## 🚨 Vulnerabilities Found

### 🔴 Critical

**Endpoint:** `createUser`
**Field:** `username`
**Attack Type:** sql_injection
**Status Code:** 500
**Payload:** `' OR '1'='1`

**Response Preview:** `Internal Server Error`

---

### 🟠 High

**Endpoint:** `updateProfile`
**Field:** `email`
**Attack Type:** xss
**Status Code:** 200
**Payload:** `<script>alert('XSS')</script>`
```

## Attack Types

### 1. SQL Injection
Tests for SQL injection vulnerabilities:
```sql
' OR '1'='1
' UNION SELECT NULL--
'; DROP TABLE users; --
```

### 2. NoSQL Injection
Tests for MongoDB/NoSQL injection:
```json
{"$gt": ""}
{"$ne": null}
{"$where": "this.password.length > 0"}
```

### 3. Buffer Overflow
Tests with large payloads:
```
A * 10000
"A" * 100000
```

### 4. Type Manipulation
Sends wrong types:
```python
# Where integer expected:
"not_a_number"
"123abc"
"null"

# Where string expected:
12345
True
None
```

### 5. XSS
Cross-site scripting tests:
```html
<script>alert('XSS')</script>
<img src=x onerror=alert('XSS')>
```

### 6. Command Injection
OS command injection:
```bash
; cat /etc/passwd
| whoami
$(whoami)
```

### 7. Path Traversal
Directory traversal:
```
../../../etc/passwd
..\..\..\windows\system32\config\sam
```

## Programmatic Usage

### Basic Usage

```python
from socialseed_e2e.project_manifest import (
    MaliciousPayloadGenerator,
    SecurityTestExecutor,
    SecurityReportGenerator,
)
from socialseed_e2e import BasePage

# Create payload generator
generator = MaliciousPayloadGenerator()

# Generate SQL injection payloads
payloads = generator.generate_sql_injection_payloads("string")

# Generate type manipulation payloads
payloads = generator.generate_type_manipulation_payloads("int")
```

### Running Security Tests

```python
from socialseed_e2e.project_manifest import run_security_fuzzing
from socialseed_e2e import BasePage

# Create service page
page = BasePage(base_url="http://localhost:8080")

# Run fuzzing
session = run_security_fuzzing(
    service_page=page,
    service_info=service_info,
    max_payloads_per_field=20
)

# Access results
print(f"Tests: {session.total_tests}")
print(f"Vulnerabilities: {len(session.vulnerabilities_found)}")
print(f"Resilience Score: {session.resilience_score}%")
```

### Custom Testing

```python
from socialseed_e2e.project_manifest import (
    SecurityTestExecutor,
    MaliciousPayloadGenerator,
)

# Create executor
executor = SecurityTestExecutor(
    base_url="http://localhost:8080",
    service_page=page
)

# Start session
session = executor.start_session(["endpoint1", "endpoint2"])

# Test specific endpoint
results = executor.execute_security_tests(
    endpoint=endpoint_info,
    dto=dto_schema,
    max_payloads_per_field=10
)

# End session
executor.end_session()

# Generate report
report_gen = SecurityReportGenerator(session)
report_gen.save_report("security-report.md")
```

## Resilience Scoring

The resilience score is calculated as:

```
Resilience Score = (Blocked Attacks / Total Attacks) * 100
```

### Score Interpretation

| Score | Level | Description |
|-------|-------|-------------|
| 90-100% | 🟢 Excellent | API properly validates and blocks attacks |
| 70-89% | 🟡 Good | Most attacks blocked, minor issues |
| 50-69% | 🟠 Moderate | Several vulnerabilities need attention |
| <50% | 🔴 Poor | Critical vulnerabilities found |

## Vulnerability Severity

### Critical
- SQL/NoSQL Injection causing server crashes
- Command injection
- Authentication bypass

### High
- XSS that executes
- Path traversal successful
- Buffer overflow causing crashes

### Medium
- Information disclosure
- Type confusion
- Logic errors

### Low
- Minor validation issues
- Non-exploitable errors

## Best Practices

### 1. Regular Testing
```bash
# Add to CI/CD pipeline
e2e security-test --max-payloads 20
```

### 2. Focus on Critical Endpoints
```bash
# Test authentication endpoints thoroughly
e2e security-test --service auth --max-payloads 50
```

### 3. Review Reports
Always review the generated security report:
```bash
e2e security-test
cat .e2e/SECURITY_REPORT.md
```

### 4. Fix and Retest
After fixing vulnerabilities:
```bash
e2e security-test
# Verify resilience score improved
```

## Integration with Other Commands

### After Test Generation
```bash
# Generate tests
e2e generate-tests

# Run security tests
e2e security-test
```

### Part of CI/CD
```yaml
# .github/workflows/security.yml
- name: Security Testing
  run: |
    e2e security-test --max-payloads 20
    if [ $? -ne 0 ]; then
      echo "Security vulnerabilities found!"
      exit 1
    fi
```

## Troubleshooting

### "No project manifest found"
Run `e2e manifest` first to analyze the project.

### "Service not found"
Check service names in your `e2e.conf` or manifest.

### Timeout errors
Increase timeout or reduce `--max-payloads`.

### False positives
Review the report manually - some "vulnerabilities" might be expected behavior.

## Recommendations

Based on security testing results:

### Critical Priority
- Implement parameterized queries
- Add input validation middleware
- Set up WAF (Web Application Firewall)

### High Priority
- Sanitize user inputs
- Implement rate limiting
- Add security headers

### General Best Practices
- Keep dependencies updated
- Monitor logs for attacks
- Regular security audits

## API Reference

### MaliciousPayloadGenerator

```python
generator = MaliciousPayloadGenerator()

# Generate payloads
generator.generate_sql_injection_payloads(field_type)
generator.generate_nosql_injection_payloads()
generator.generate_buffer_overflow_payloads(field_name)
generator.generate_type_manipulation_payloads(expected_type)
generator.generate_xss_payloads()
generator.generate_command_injection_payloads()
generator.generate_path_traversal_payloads()

# Generate all for a field
generator.generate_all_payloads_for_field(dto_field)
```

### SecurityTestExecutor

```python
executor = SecurityTestExecutor(base_url, service_page)

# Session management
session = executor.start_session(endpoints)
results = executor.execute_security_tests(endpoint, dto)
session = executor.end_session()
```

### ResilienceMonitor

```python
monitor = ResilienceMonitor()

# Analyze response
result = monitor.analyze_response(response, payload, execution_time)

# Get stats
score = monitor.get_resilience_score()
summary = monitor.get_summary()
```

## See Also

- [Autonomous Test Generation](autonomous-test-generation-guide.md)
- [The Observer](the-observer.md)
- [Discovery Report](ai-discovery-report.md)
