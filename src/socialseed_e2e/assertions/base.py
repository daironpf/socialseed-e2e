"""Base classes and exceptions for socialseed-e2e assertions."""

from typing import Any, Dict, Optional, Type


class E2EAssertionError(AssertionError):
    """Exception raised when an E2E assertion fails."""

    def __init__(
        self,
        message: str,
        actual: Any = None,
        expected: Any = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the assertion error with details."""
        super().__init__(message)
        self.message = message
        self.actual = actual
        self.expected = expected
        self.context = context or {}

    def __str__(self) -> str:
        """Return a formatted error message."""
        msg = [self.message]
        if self.expected is not None:
            msg.append(f"  Expected: {self.expected}")
        if self.actual is not None:
            msg.append(f"  Actual: {self.actual}")

        if self.context:
            msg.append("  Context:")
            for k, v in self.context.items():
                msg.append(f"    - {k}: {v}")

        return "\n".join(msg)


class AssertionBuilder:
    """Fluent API for building custom assertions."""

    def __init__(self, value: Any, name: str = "value"):
        """Initialize the builder with the value to test."""
        self.value = value
        self.name = name
        self._negated = False

    @property
    def not_to(self) -> "AssertionBuilder":
        """Negate the next assertion."""
        self._negated = True
        return self

    def _check(self, condition: bool, failure_msg: str, expected_val: Any = None):
        if self._negated:
            condition = not condition
            failure_msg = f"Negation failed: {failure_msg.replace('expected', 'did not expect')}"

        if not condition:
            raise E2EAssertionError(
                message=f"Assertion failed for '{self.name}': {failure_msg}",
                actual=self.value,
                expected=expected_val,
            )

        self._negated = False  # Reset negation
        return self

    def exists(self):
        """Assert that the value is not None."""
        return self._check(self.value is not None, "expected to exist (not None)")

    def equals(self, other: Any):
        """Assert that the value equals the expected one."""
        return self._check(self.value == other, f"expected to equal {other}", other)

    def is_instance(self, cls: Type):
        """Assert that the value is an instance of a specific type."""
        return self._check(
            isinstance(self.value, cls), f"expected to be an instance of {cls.__name__}"
        )

    def matches(self, pattern: str):
        """Assert that the value matches a regex pattern."""
        import re

        return self._check(
            bool(re.search(pattern, str(self.value))),
            f"expected to match regex pattern r'{pattern}'",
        )

    def contains(self, item: Any):
        """Assert that the value (if collection) contains the item."""
        try:
            condition = item in self.value
        except TypeError:
            condition = False
        return self._check(condition, f"expected to contain {item}")

    def has_length(self, length: int):
        """Assert that the value has a specific length."""
        try:
            actual_len = len(self.value)
        except TypeError:
            actual_len = -1
        return self._check(actual_len == length, f"expected to have length {length}", length)


def expect(value: Any, name: str = "value") -> AssertionBuilder:
    """Entry point for fluent assertions."""
    return AssertionBuilder(value, name)
