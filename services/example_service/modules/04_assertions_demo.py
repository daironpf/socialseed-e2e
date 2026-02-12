"""Demo of the comprehensive assertion library."""

from socialseed_e2e.assertions import (
    assert_all,
    assert_execution_time,
    assert_graphql_success,
    assert_iso8601,
    assert_subset,
    assert_valid_schema,
)
from socialseed_e2e.core import tag


@tag("assertions", "demo")
def run(page):
    """Run assertions demo."""
    print("Running assertions demo...")

    # 1. Fluent Assertions
    page.expect(10, "score").equals(10)
    page.expect("hello world", "greeting").matches(r"hello")
    page.expect([1, 2, 3], "list").contains(2).has_length(3)
    page.expect(None, "missing").not_to.exists()

    # 2. JSON Schema
    schema = {
        "type": "object",
        "properties": {"id": {"type": "number"}, "name": {"type": "string"}},
        "required": ["id", "name"],
    }
    data = {"id": 1, "name": "Test User"}
    assert_valid_schema(data, schema)
    print("✅ JSON Schema validation passed")

    # 3. GraphQL
    gql_response = {"data": {"user": {"id": "123", "name": "SocialSeed"}}}
    assert_graphql_success(gql_response)
    print("✅ GraphQL success assertion passed")

    # 4. Time assertions
    assert_execution_time(150, max_ms=500)
    assert_iso8601("2026-02-12T15:00:00Z")
    print("✅ Time assertions passed")

    # 5. Collection assertions
    assert_all([2, 4, 6], lambda x: x % 2 == 0)
    assert_subset(["a", "b"], ["a", "b", "c"])
    print("✅ Collection assertions passed")

    print("\n🎉 All demo assertions passed!")
