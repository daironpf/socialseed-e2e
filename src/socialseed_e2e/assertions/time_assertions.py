"""Time-based assertions for socialseed-e2e."""

import datetime
from typing import Optional, Union

from socialseed_e2e.assertions.base import E2EAssertionError


def assert_execution_time(
    duration_ms: float, max_ms: float, min_ms: float = 0.0, message: Optional[str] = None
) -> None:
    """Assert that an operation took within the expected time range.

    Args:
        duration_ms: Actual duration in milliseconds
        max_ms: Maximum allowed duration
        min_ms: Minimum allowed duration (default: 0)
        message: Optional custom error message
    """
    if duration_ms > max_ms:
        default_msg = f"Operation took too long: {duration_ms:.2f}ms (Max: {max_ms}ms)"
        raise E2EAssertionError(message or default_msg, actual=duration_ms, expected=max_ms)

    if duration_ms < min_ms:
        default_msg = f"Operation was too fast: {duration_ms:.2f}ms (Min: {min_ms}ms)"
        raise E2EAssertionError(message or default_msg, actual=duration_ms, expected=min_ms)


def assert_iso8601(date_str: str, message: Optional[str] = None) -> None:
    """Assert that a string is a valid ISO 8601 date.

    Supports formats like:
    - 2023-10-27
    - 2023-10-27T10:30:00
    - 2023-10-27T10:30:00Z
    - 2023-10-27T10:30:00+02:00
    """
    try:
        datetime.datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        default_msg = f"String '{date_str}' is not a valid ISO 8601 date"
        raise E2EAssertionError(message or default_msg, actual=date_str)


def assert_recent(
    date_val: Union[datetime.datetime, str], seconds: int = 60, message: Optional[str] = None
) -> None:
    """Assert that a date is within the last X seconds from now (UTC)."""
    if isinstance(date_val, str):
        try:
            dt = datetime.datetime.fromisoformat(date_val.replace("Z", "+00:00"))
        except ValueError:
            raise E2EAssertionError(f"Invalid date format: {date_val}")
    else:
        dt = date_val

    # Ensure dt is timezone-aware if comparing with utcnow
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)

    now = datetime.datetime.now(datetime.timezone.utc)
    diff = (now - dt).total_seconds()

    if abs(diff) > seconds:
        default_msg = f"Date is not recent: {dt} (Diff: {diff:.2f}s, Threshold: {seconds}s)"
        raise E2EAssertionError(
            message or default_msg, actual=dt, expected=f"within {seconds}s of {now}"
        )
