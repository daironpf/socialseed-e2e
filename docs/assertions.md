# Comprehensive Assertion Library

socialseed-e2e provides a rich, domain-specific assertion library designed to make your tests more expressive and robust.

## Core Concepts

The library is organized into specialized modules for different testing needs:
- **Fluent API**: Use `expect()` for a more readable, chainable assertion style.
- **JSON Schema**: Validate response structures against standard schemas.
- **GraphQL**: Assert on data presence and absence of errors in GraphQL responses.
- **Time/Date**: Validate ISO 8601 formats, execution times, and date recency.
- **Statistical**: Assert on latencies and metrics using mean, percentiles, and outlier detection.
- **Collections**: Comprehensive checks for lists, sets, and mappings.

## 1. Fluent Assertions (expect)

The `expect` function provides a chainable interface for common checks.

```python
from socialseed_e2e.assertions import expect

expect(user_id, "user_id").exists().is_instance(int).equals(123)
expect(response_body, "response").contains("success").not_to.contains("error")
expect(items).has_length(5)
```

## 2. JSON Schema Validation

Power by `jsonschema`, this allows strict structural validation.

```python
from socialseed_e2e.assertions import assert_valid_schema

schema = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "email": {"type": "string", "format": "email"}
    },
    "required": ["id", "email"]
}

assert_valid_schema(response.json(), schema)
```

## 3. GraphQL Assertions

Specialized for GraphQL response structures.

```python
from socialseed_e2e.assertions import assert_graphql_success, assert_graphql_error

# Generic success check (no errors + data present)
assert_graphql_success(response.json())

# Specific error check
assert_graphql_error(response.json(), contains_message="Unauthorized", error_code="AUTH_001")
```

## 4. Time and Performance Assertions

Validate temporal constraints.

```python
from socialseed_e2e.assertions import assert_execution_time, assert_iso8601

# Assert latency
assert_execution_time(duration_ms, max_ms=500, min_ms=10)

# Validate ISO dates
assert_iso8601(user.created_at)
```

## 5. Statistical Assertions

Useful for load and performance testing.

```python
from socialseed_e2e.assertions import assert_mean_below, assert_percentile_below

# Assert that P95 latency is below 300ms
assert_percentile_below(latencies, percentile=95, threshold=300)

# Detect and fail on statistical outliers (default: > 3 sigma)
assert_no_outliers(latencies)
```

## 6. Collection Assertions

Advanced checks for iterables.

```python
from socialseed_e2e.assertions import assert_all, assert_subset

# All users must be active
assert_all(users, lambda u: u['status'] == 'ACTIVE')

# Check required fields exist in response
assert_subset(['id', 'token'], response.json().keys())
```

## Custom Assertion Errors

All assertions in this library raise `E2EAssertionError`, which provides detailed context about expected vs. actual values, making failure reports much easier to debug.
