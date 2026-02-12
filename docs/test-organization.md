# Advanced Test Organization

socialseed-e2e provides a comprehensive system for organizing, selecting, and ordering your tests using tags, priorities, and dependencies.

## Key Features

-   **Tag-based selection**: Categorize tests (e.g., `smoke`, `critical`, `auth`) and run only specific subsets.
-   **Priority levels**: Define which tests are more important to run first.
-   **Test Dependencies**: Ensure tests run in a specific order (e.g., run Login before Profile).
-   **Include/Exclude patterns**: Powerful CLI options to precisely control test execution.

## Using Decorators

You can use decorators on the `run` function of your test modules to define metadata:

```python
from socialseed_e2e.core import tag, depends_on, priority, Priority

@tag("smoke", "security", "auth")
@priority(Priority.CRITICAL)
@depends_on("test_01_registration") # Name of the module file without .py
def run(page):
    # Test logic here
    pass
```

### Tags

Tags allow you to group tests across different services. You can assign as many tags as you want to a single test.

### Priorities

Priorities help the orchestrator decide the execution order when no strict dependencies are defined. Available levels:
- `Priority.LOW`
- `Priority.MEDIUM` (Default)
- `Priority.HIGH`
- `Priority.CRITICAL`

### Dependencies

When a test `depends_on` another, socialseed-e2e ensures that the dependency runs first. If multiple tests have no dependencies, they are sorted by priority.

## Running Tests with Tags

Use the CLI to filter tests by tags:

### Include only specific tags
```bash
e2e run --tag smoke --tag critical
```
*Note: This will run tests that have **at least one** of these tags.*

### Exclude specific tags
```bash
e2e run --exclude-tag flaky --exclude-tag slow
```

### Combined filtering
```bash
e2e run --tag smoke --exclude-tag experimental
```

## Best Practices

1.  **Atomic Smoke Tests**: Tag your most critical "happy path" tests with `smoke` and run them on every commit.
2.  **Service Isolation**: Use dependencies sparingly to keep tests as isolated as possible. Only use them when a previous state is strictly required.
3.  **Descriptive Tags**: Use a consistent naming convention for tags (e.g., `feature:login`, `env:prod`, `type:api`).
4.  **Priority-driven CI**: In time-constrained environments, you can choose to run only `CRITICAL` and `HIGH` priority tests.
