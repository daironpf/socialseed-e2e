# AI Agent Orchestration Layer

## Overview

The AI Agent Orchestration Layer enables autonomous testing workflows by allowing AI agents to plan, execute, and debug tests without human intervention. This sophisticated system reduces human intervention by up to 80% and enables 24/7 autonomous testing.

## Key Features

### 1. Test Strategy Planning
AI analyzes the codebase and generates comprehensive testing strategies based on:
- **Code Complexity Analysis**: Identifies complex endpoints requiring more thorough testing
- **Business Impact Assessment**: Prioritizes critical paths (payments, authentication, etc.)
- **Change Frequency Analysis**: Identifies frequently modified code that needs regression testing
- **Risk-Based Prioritization**: Assigns priority levels (Critical, High, Medium, Low) based on risk factors

### 2. Risk-Based Prioritization
The system evaluates multiple risk factors:
- **Code Complexity**: Parameters, authentication requirements, DTO usage
- **Business Impact**: Critical operations, write operations, public endpoints
- **Change Frequency**: Historical changes and versioning indicators

### 3. Self-Healing Tests
Automatically detects and fixes flaky tests by:
- **Pattern Detection**: Identifies common flakiness patterns (hardcoded sleeps, race conditions, random data)
- **Smart Fixes**: Suggests and applies fixes for timing issues, assertions, and dependencies
- **Learning**: Tracks healing success rates and improves over time

### 4. Intelligent Retry Logic
Learns from failures to optimize retry strategies:
- **Pattern Recognition**: Identifies recurring failure patterns
- **Adaptive Backoff**: Adjusts retry delays based on failure type (exponential for rate limits, linear for timeouts)
- **Success Tracking**: Monitors retry success rates and adjusts strategies

### 5. Autonomous Debugging
AI-powered debugging that:
- **Error Classification**: Categorizes errors (timeout, network, auth, etc.)
- **Root Cause Analysis**: Identifies underlying causes with confidence scores
- **Fix Suggestions**: Provides actionable fix recommendations
- **Auto-Apply**: Can apply low-risk fixes automatically

## Architecture

```
ai_orchestrator/
├── __init__.py              # Public API exports
├── models.py                # Pydantic models (TestCase, TestStrategy, etc.)
├── strategy_planner.py      # Test strategy generation
├── autonomous_runner.py     # Test execution engine
├── self_healer.py          # Flaky test detection and fixing
└── debugger.py             # AI-powered debugging
```

## Quick Start

### 1. Plan a Test Strategy

```python
from socialseed_e2e.ai_orchestrator import StrategyPlanner

# Create planner
planner = StrategyPlanner("/path/to/project")

# Generate strategy
strategy = planner.generate_strategy(
    name="API Regression Tests",
    description="Comprehensive API testing for regression suite",
    target_services=["users-api", "orders-api"],  # Optional: specific services
)

# Save strategy
planner.save_strategy(strategy)
```

### 2. Run Tests Autonomously

```python
from socialseed_e2e.ai_orchestrator import AutonomousRunner, OrchestratorConfig

# Configure runner
config = OrchestratorConfig(
    enable_self_healing=True,
    enable_intelligent_retry=True,
    parallel_workers=4,
    auto_apply_fixes=False,  # Set True for fully autonomous
)

runner = AutonomousRunner("/path/to/project", config)

# Create context factory
def context_factory():
    from socialseed_e2e.core.base_page import BasePage
    return BasePage("http://localhost:8000")

# Execute strategy
execution = runner.run_strategy(strategy, context_factory)

# Check results
print(f"Status: {execution.status}")
print(f"Summary: {execution.summary}")
```

### 3. Debug Failures

```python
from socialseed_e2e.ai_orchestrator import AIDebugger

debugger = AIDebugger("/path/to/project")

# Get debug report for an execution
report = debugger.get_debug_report(execution.id)

# View analyses
for analysis in report['analyses']:
    print(f"Test: {analysis['test_id']}")
    print(f"Failure Type: {analysis['failure_type']}")
    print(f"Root Cause: {analysis['root_cause']}")
    print(f"Confidence: {analysis['confidence_score']:.2%}")

    for fix in analysis['suggested_fixes']:
        print(f"  - {fix['description']}")
```

## CLI Commands

### Plan Strategy
```bash
# Generate a test strategy for all services
e2e plan-strategy --name "API Regression Strategy"

# Generate strategy for specific services
e2e plan-strategy --name "Critical Path Tests" --services users-api,orders-api
```

### Run Autonomously
```bash
# Run tests with default settings
e2e autonomous-run --strategy-id abc123

# Run with 8 parallel workers and auto-fix
e2e autonomous-run --strategy-id abc123 --parallel 8 --auto-fix

# Run without healing
e2e autonomous-run --strategy-id abc123 --no-healing
```

### Analyze Flaky Tests
```bash
# Analyze a test file for flakiness
e2e analyze-flaky --test-file services/users/modules/test_login.py
```

### Debug Execution
```bash
# Debug a failed execution
e2e debug-execution --execution-id exec_20240211_120000

# Debug and auto-apply fixes
e2e debug-execution --execution-id exec_20240211_120000 --apply-fix
```

### View Healing Stats
```bash
# View self-healing statistics
e2e healing-stats
```

## Configuration

### OrchestratorConfig Options

```python
OrchestratorConfig(
    enable_self_healing=True,           # Enable auto-fixing of flaky tests
    enable_intelligent_retry=True,      # Enable learned retry strategies
    enable_auto_debug=True,             # Enable automatic debugging
    enable_risk_prioritization=True,    # Enable risk-based prioritization
    max_auto_fix_attempts=3,            # Maximum auto-fix attempts per test
    auto_apply_fixes=False,             # Auto-apply fixes without confirmation
    parallel_workers=4,                 # Number of parallel test workers
    history_retention_days=30,          # Days to retain execution history
    learning_enabled=True,              # Enable learning from failures
    min_confidence_for_auto_fix=0.8,    # Min confidence to auto-apply fix
)
```

## Models

### TestCase
```python
TestCase(
    id="test_001",                      # Unique identifier
    name="Test Login",                  # Human-readable name
    description="Test user login",      # Description
    test_type=TestType.E2E,             # Type: UNIT, INTEGRATION, E2E, etc.
    priority=TestPriority.HIGH,         # Priority: CRITICAL, HIGH, MEDIUM, LOW
    service="users-api",                # Service name
    module="path/to/test.py",           # Test file path
    endpoint="/api/login",              # API endpoint (optional)
    http_method="POST",                 # HTTP method (optional)
    risk_factors=[],                    # List of RiskFactor
    dependencies=[],                    # Test IDs this depends on
    estimated_duration_ms=1000,         # Estimated duration
    tags=["auth", "critical"],          # Tags for categorization
)
```

### TestStrategy
```python
TestStrategy(
    id="strategy_001",                  # Unique identifier
    name="API Tests",                   # Strategy name
    description="Description",          # Description
    target_services=[],                 # Services to test
    test_cases=[],                      # List of TestCase
    execution_order=[],                 # Ordered test IDs
    parallelization_groups=[],          # Groups for parallel execution
    total_estimated_duration_ms=0,      # Total estimated duration
    coverage_targets={},                # Coverage targets by category
)
```

### TestResult
```python
TestResult(
    test_id="test_001",                 # Test identifier
    status=TestStatus.PASSED,           # Status: PENDING, PASSED, FAILED, etc.
    started_at=datetime.now(),          # Start timestamp
    completed_at=datetime.now(),        # Completion timestamp
    duration_ms=1000,                   # Actual duration
    attempts=1,                         # Number of attempts
    error_message="",                   # Error message if failed
    stack_trace="",                     # Stack trace if failed
    logs=[],                            # Execution logs
    healed=False,                       # Whether test was auto-healed
    healing_applied="",                 # Description of healing applied
)
```

## Flakiness Patterns Detected

The self-healing system detects these patterns:

1. **Hardcoded Sleep**: `time.sleep()` without polling mechanism
2. **Race Conditions**: Concurrent access patterns
3. **External Dependencies**: Network calls without retry logic
4. **Random Data**: Unseeded random number generation
5. **Time-Dependent**: Tests dependent on current time
6. **Assertion Without Tolerance**: Exact numeric assertions

## Error Classification

The debugger classifies these error types:

- **Assertion Error**: Test assertions failed
- **Timeout Error**: Requests or operations timed out
- **Network Error**: Connection issues
- **Authentication Error**: 401 Unauthorized
- **Authorization Error**: 403 Forbidden
- **Not Found Error**: 404 Resource not found
- **Validation Error**: 422 Bad Request
- **Server Error**: 5xx errors
- **Database Error**: Database-related errors

## Benefits

- **Reduced Human Intervention**: 80% reduction in manual test maintenance
- **24/7 Operation**: Fully autonomous testing pipeline
- **Continuous Learning**: Improves over time based on failures
- **Intelligent Prioritization**: Tests ordered by risk and impact
- **Self-Healing**: Automatically fixes flaky tests
- **Intelligent Debugging**: AI-powered root cause analysis

## Best Practices

1. **Start with Monitoring**: Run with `auto_apply_fixes=False` initially to review suggestions
2. **Review Confidence Scores**: Only auto-apply fixes with high confidence (>0.8)
3. **Monitor Healing Stats**: Regularly review `healing-stats` to identify patterns
4. **Gradual Rollout**: Start with non-critical services before full deployment
5. **Keep History**: Maintain execution history for trend analysis

## Integration with CI/CD

```yaml
# .github/workflows/autonomous-tests.yml
name: Autonomous Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Plan Test Strategy
        run: e2e plan-strategy --name "CI Tests" --output ./strategies

      - name: Run Autonomous Tests
        run: e2e autonomous-run --strategy-id $(cat ./strategies/latest.txt) --parallel 4 --auto-fix

      - name: Debug Failures
        if: failure()
        run: |
          e2e debug-execution --execution-id $(cat ./strategies/latest_exec.txt) --apply-fix
```

## Troubleshooting

### Strategy Generation Fails
- Ensure `project_knowledge.json` exists (run `e2e manifest` first)
- Check that services are properly configured in `e2e.conf`

### Tests Not Executing
- Verify test modules have `run(context)` function
- Check that service directories exist

### Healing Not Working
- Enable with `--enable-self-healing` flag
- Check `healing-stats` for patterns
- Verify test file permissions

### Debugging No Results
- Ensure execution ID is valid
- Check that analysis history path is writable

## API Reference

See docstrings in the source code for detailed API documentation:
- `socialseed_e2e/ai_orchestrator/strategy_planner.py`
- `socialseed_e2e/ai_orchestrator/autonomous_runner.py`
- `socialseed_e2e/ai_orchestrator/self_healer.py`
- `socialseed_e2e/ai_orchestrator/debugger.py`
