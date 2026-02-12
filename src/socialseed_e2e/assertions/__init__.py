"""Comprehensive Assertion Library for socialseed-e2e.

This package provides a rich set of domain-specific assertions for API testing,
including JSON Schema, GraphQL, time-based, statistical, and collection assertions.
"""

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
    "expect",
    "AssertionBuilder",
    "E2EAssertionError",
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
