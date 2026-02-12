"""Statistical assertions for performance and monitoring in socialseed-e2e."""

import math
from typing import List, Optional

from socialseed_e2e.assertions.base import E2EAssertionError


def _calculate_stats(values: List[float]):
    if not values:
        return 0.0, 0.0, 0.0

    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    std_dev = math.sqrt(variance)

    sorted_vals = sorted(values)
    n = len(sorted_vals)
    if n % 2 == 1:
        median = sorted_vals[n // 2]
    else:
        median = (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2

    return mean, median, std_dev


def assert_mean_below(values: List[float], threshold: float, message: Optional[str] = None) -> None:
    """Assert that the average of values is below a threshold."""
    if not values:
        raise E2EAssertionError("Cannot calculate mean of empty list")

    mean = sum(values) / len(values)
    if mean > threshold:
        default_msg = f"Mean value {mean:.2f} exceeds threshold {threshold}"
        raise E2EAssertionError(message or default_msg, actual=mean, expected=f"< {threshold}")


def assert_percentile_below(
    values: List[float], percentile: float, threshold: float, message: Optional[str] = None
) -> None:
    """Assert that the P-th percentile is below a threshold.

    Example: assert_percentile_below(latencies, 95, 200) asserts P95 < 200ms.
    """
    if not values:
        raise E2EAssertionError("Empty values list")

    sorted_vals = sorted(values)
    idx = int(math.ceil((percentile / 100) * len(sorted_vals))) - 1
    p_val = sorted_vals[max(0, min(idx, len(sorted_vals) - 1))]

    if p_val > threshold:
        default_msg = f"P{percentile} value {p_val:.2f} exceeds threshold {threshold}"
        raise E2EAssertionError(
            message or default_msg, actual=p_val, expected=f"P{percentile} < {threshold}"
        )


def assert_no_outliers(
    values: List[float], m_factor: float = 3.0, message: Optional[str] = None
) -> None:
    """Assert there are no values further than M * StdDev from the mean."""
    if len(values) < 2:
        return

    mean, _, std_dev = _calculate_stats(values)
    if std_dev == 0:
        return

    outliers = [x for x in values if abs(x - mean) > m_factor * std_dev]

    if outliers:
        default_msg = f"Found {len(outliers)} outliers exceeding {m_factor} sigma"
        raise E2EAssertionError(
            message or default_msg,
            actual=outliers,
            context={"mean": mean, "std_dev": std_dev, "threshold": m_factor * std_dev},
        )
