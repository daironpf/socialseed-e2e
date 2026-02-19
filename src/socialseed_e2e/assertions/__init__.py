"""Comprehensive Assertion Library for socialseed-e2e.

This package provides a rich set of domain-specific assertions for API testing,
including JSON Schema, GraphQL, time-based, statistical, and collection assertions.
"""

from socialseed_e2e.assertions.advanced import (
    BusinessRuleValidator,
    DataQualityValidator,
    PerformanceValidator,
    SchemaType,
    SchemaValidator,
    SecurityValidator,
    ValidationResult,
    assert_no_pii,
    assert_no_sql_injection,
    assert_response_time,
    assert_valid_json_schema,
)
from socialseed_e2e.assertions.base import AssertionBuilder, E2EAssertionError, expect
from socialseed_e2e.assertions.collections import (
    assert_all,
    assert_any,
    assert_empty,
    assert_not_empty,
    assert_subset,
)
from socialseed_e2e.assertions.graphql import (
    assert_graphql_data,
    assert_graphql_error,
    assert_graphql_success,
)
from socialseed_e2e.assertions.json_schema import assert_valid_schema
from socialseed_e2e.assertions.statistical import (
    assert_mean_below,
    assert_no_outliers,
    assert_percentile_below,
)
from socialseed_e2e.assertions.time_assertions import (
    assert_execution_time,
    assert_iso8601,
    assert_recent,
)

__all__ = [
    # Base
    "expect",
    "AssertionBuilder",
    "E2EAssertionError",
    # Advanced
    "SchemaValidator",
    "BusinessRuleValidator",
    "PerformanceValidator",
    "SecurityValidator",
    "DataQualityValidator",
    "SchemaType",
    "ValidationResult",
    "assert_valid_json_schema",
    "assert_response_time",
    "assert_no_sql_injection",
    "assert_no_pii",
    # Existing
    "assert_valid_schema",
    "assert_graphql_success",
    "assert_graphql_error",
    "assert_graphql_data",
    "assert_execution_time",
    "assert_iso8601",
    "assert_recent",
    "assert_mean_below",
    "assert_percentile_below",
    "assert_no_outliers",
    "assert_all",
    "assert_any",
    "assert_subset",
    "assert_empty",
    "assert_not_empty",
]
