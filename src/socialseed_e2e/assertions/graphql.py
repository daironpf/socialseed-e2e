"""GraphQL-specific assertions for socialseed-e2e."""

from typing import Any, Dict, Optional

from socialseed_e2e.assertions.base import E2EAssertionError


def assert_graphql_success(response_data: Dict[str, Any], message: Optional[str] = None) -> None:
    """Assert that a GraphQL response has no errors and contains data.

    Args:
        response_data: The JSON response from a GraphQL endpoint
        message: Optional custom error message
    """
    errors = response_data.get("errors")
    if errors:
        default_msg = f"GraphQL request failed with {len(errors)} error(s)"
        raise E2EAssertionError(message or default_msg, actual=errors, expected="No errors")

    if "data" not in response_data or response_data["data"] is None:
        raise E2EAssertionError("GraphQL response missing 'data' field", actual=response_data)


def assert_graphql_error(
    response_data: Dict[str, Any],
    contains_message: Optional[str] = None,
    error_code: Optional[str] = None,
) -> None:
    """Assert that a GraphQL response contains expected errors."""
    errors = response_data.get("errors", [])
    if not errors:
        raise E2EAssertionError("Expected GraphQL errors but found none", actual=response_data)

    if contains_message:
        found = any(contains_message.lower() in err.get("message", "").lower() for err in errors)
        if not found:
            raise E2EAssertionError(
                f"None of the GraphQL errors contain message: '{contains_message}'",
                actual=[e.get("message") for e in errors],
            )

    if error_code:
        # Error codes are usually in extensions.code
        found_code = False
        for err in errors:
            extensions = err.get("extensions", {})
            if extensions.get("code") == error_code:
                found_code = True
                break

        if not found_code:
            raise E2EAssertionError(
                f"Expected GraphQL error code '{error_code}' but it was not found",
                actual=[e.get("extensions", {}).get("code") for e in errors],
            )


def assert_graphql_data(
    response_data: Dict[str, Any],
    path: str,
    expected_value: Any = None,
    message: Optional[str] = None,
) -> None:
    """Assert that specific data exists at a given path in a GraphQL response.

    Path uses dot notation, e.g., "user.profile.id"
    """
    data = response_data.get("data")
    if data is None:
        raise E2EAssertionError("GraphQL response has no data", actual=response_data)

    parts = path.split(".")
    current = data
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            raise E2EAssertionError(f"Path '{path}' not found in GraphQL data", actual=data)

    if expected_value is not None:
        if current != expected_value:
            default_msg = f"Value at path '{path}' does not match"
            raise E2EAssertionError(message or default_msg, actual=current, expected=expected_value)
