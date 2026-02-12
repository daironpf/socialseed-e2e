"""Collection-based assertions for socialseed-e2e."""

from typing import Any, Callable, Collection, Iterable, Optional, TypeVar

from socialseed_e2e.assertions.base import E2EAssertionError

T = TypeVar("T")


def assert_all(
    collection: Iterable[T], predicate: Callable[[T], bool], message: Optional[str] = None
) -> None:
    """Assert that all items in a collection satisfy a predicate."""
    items = list(collection)
    failures = [item for item in items if not predicate(item)]

    if failures:
        default_msg = f"{len(failures)} item(s) failed the predicate (total: {len(items)})"
        raise E2EAssertionError(message or default_msg, actual=failures)


def assert_any(
    collection: Iterable[T], predicate: Callable[[T], bool], message: Optional[str] = None
) -> None:
    """Assert that at least one item in a collection satisfies a predicate."""
    items = list(collection)
    if not any(predicate(item) for item in items):
        default_msg = "No items in the collection satisfy the predicate"
        raise E2EAssertionError(message or default_msg, actual=items)


def assert_subset(
    subset: Collection[Any], superset: Collection[Any], message: Optional[str] = None
) -> None:
    """Assert that 'subset' is a subset of 'superset'."""
    missing = [item for item in subset if item not in superset]
    if missing:
        default_msg = f"Subset contains {len(missing)} item(s) not found in superset"
        raise E2EAssertionError(
            message or default_msg, actual=missing, expected=f"Subset of {superset}"
        )


def assert_empty(collection: Collection[Any], message: Optional[str] = None) -> None:
    """Assert that a collection is empty."""
    if len(collection) > 0:
        default_msg = f"Expected collection to be empty, but it has {len(collection)} items"
        raise E2EAssertionError(message or default_msg, actual=len(collection), expected=0)


def assert_not_empty(collection: Collection[Any], message: Optional[str] = None) -> None:
    """Assert that a collection is not empty."""
    if len(collection) == 0:
        default_msg = "Expected collection to be not empty"
        raise E2EAssertionError(message or default_msg, actual=0, expected="> 0")
