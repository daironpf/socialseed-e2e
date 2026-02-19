"""
Assertion tuner for self-healing tests.

Adjusts assertion thresholds and handles timing issues automatically.
"""

import re
import uuid
from typing import Any, Dict, List, Optional, Tuple
from statistics import mean, stdev

from ..models import (
    AssertionAdjustment,
    TestFailure,
    HealingSuggestion,
    HealingType,
    ChangeType,
)


class AssertionTuner:
    """Tunes test assertions based on failure patterns.

    Automatically adjusts thresholds and handles timing issues:
    - Timeout adjustments
    - Value threshold tuning
    - Statistical-based thresholds
    - Flaky test detection

    Example:
        tuner = AssertionTuner()

        # Analyze failure and suggest adjustment
        suggestion = tuner.analyze_assertion_failure(
            failure=test_failure,
            assertion_type="timeout",
            current_value=5000,
        )

        if suggestion.confidence > 0.8:
            new_threshold = suggestion.new_threshold
    """

    # Assertion patterns to detect from error messages
    ASSERTION_PATTERNS = {
        "timeout": [
            r"timeout",
            r"timed out",
            r"exceeded.*time",
            r"wait.*failed",
        ],
        "value_mismatch": [
            r"expected.*but got",
            r"assert.*==",
            r"not equal",
            r"mismatch",
        ],
        "range_error": [
            r"greater than",
            r"less than",
            r"between.*and",
            r"exceeds",
        ],
        "exists_error": [
            r"does not exist",
            r"not found",
            r"is None",
            r"is null",
        ],
    }

    def __init__(self):
        """Initialize assertion tuner."""
        self.adjustment_history: List[AssertionAdjustment] = []
        self.failure_patterns: Dict[str, List[float]] = {}

    def analyze_assertion_failure(
        self,
        failure: TestFailure,
        historical_values: Optional[List[float]] = None,
    ) -> List[HealingSuggestion]:
        """Analyze test failure and suggest assertion adjustments.

        Args:
            failure: Test failure information
            historical_values: Historical values for statistical analysis

        Returns:
            List of healing suggestions
        """
        suggestions = []

        # Detect assertion type from error
        assertion_type = self._detect_assertion_type(failure.error_message)

        if assertion_type == "timeout":
            suggestion = self._tune_timeout(failure, historical_values)
            if suggestion:
                suggestions.append(suggestion)

        elif assertion_type == "value_mismatch":
            suggestion = self._tune_value_assertion(failure, historical_values)
            if suggestion:
                suggestions.append(suggestion)

        elif assertion_type == "range_error":
            suggestion = self._tune_range_assertion(failure, historical_values)
            if suggestion:
                suggestions.append(suggestion)

        # Check for flaky test patterns
        flaky_suggestion = self._detect_flaky_pattern(failure)
        if flaky_suggestion:
            suggestions.append(flaky_suggestion)

        return suggestions

    def tune_threshold(
        self,
        field_path: str,
        current_threshold: float,
        observed_values: List[float],
        tolerance_percent: float = 10.0,
    ) -> AssertionAdjustment:
        """Tune assertion threshold based on observed values.

        Args:
            field_path: Path to field being asserted
            current_threshold: Current threshold value
            observed_values: List of observed values
            tolerance_percent: Tolerance percentage to add

        Returns:
            AssertionAdjustment with new threshold
        """
        if not observed_values:
            return AssertionAdjustment(
                id=str(uuid.uuid4()),
                assertion_type="threshold",
                old_threshold=current_threshold,
                new_threshold=current_threshold,
                field_path=field_path,
                reason="No observed values for tuning",
                confidence=0.0,
            )

        # Calculate statistics
        avg_value = mean(observed_values)
        max_value = max(observed_values)

        # Determine if threshold should be increased or decreased
        if current_threshold < max_value:
            # Threshold too low, increase it
            new_threshold = max_value * (1 + tolerance_percent / 100)
            reason = f"Observed values exceed current threshold (max: {max_value})"
            confidence = 0.9
        elif current_threshold > avg_value * 2:
            # Threshold too high, could be tightened
            new_threshold = max(avg_value * 1.2, max_value)
            reason = f"Threshold too loose (avg: {avg_value}, max: {max_value})"
            confidence = 0.7
        else:
            # Threshold seems appropriate
            new_threshold = current_threshold
            reason = "Threshold appears well-tuned"
            confidence = 0.8

        adjustment = AssertionAdjustment(
            id=str(uuid.uuid4()),
            assertion_type="threshold",
            old_threshold=current_threshold,
            new_threshold=round(new_threshold, 2),
            field_path=field_path,
            reason=reason,
            confidence=confidence,
        )

        self.adjustment_history.append(adjustment)
        return adjustment

    def adjust_timing(
        self,
        current_timeout_ms: int,
        actual_duration_ms: float,
        retry_count: int = 3,
    ) -> AssertionAdjustment:
        """Adjust timeout based on actual execution time.

        Args:
            current_timeout_ms: Current timeout in milliseconds
            actual_duration_ms: Actual duration observed
            retry_count: Number of retries to account for

        Returns:
            AssertionAdjustment with new timeout
        """
        # Add buffer to actual duration
        buffer_multiplier = 1.5 + (retry_count * 0.1)
        suggested_timeout = actual_duration_ms * buffer_multiplier

        # Ensure minimum timeout
        min_timeout = max(1000, actual_duration_ms * 1.2)
        new_timeout = max(suggested_timeout, min_timeout)

        # Cap at reasonable maximum
        max_timeout = min(30000, current_timeout_ms * 2)
        new_timeout = min(new_timeout, max_timeout)

        adjustment = AssertionAdjustment(
            id=str(uuid.uuid4()),
            assertion_type="timeout",
            old_threshold=float(current_timeout_ms),
            new_threshold=round(new_timeout, 0),
            field_path="timeout",
            reason=f"Actual duration {actual_duration_ms}ms exceeds current timeout {current_timeout_ms}ms",
            confidence=0.9 if actual_duration_ms > current_timeout_ms else 0.7,
        )

        self.adjustment_history.append(adjustment)
        return adjustment

    def _detect_assertion_type(self, error_message: str) -> str:
        """Detect the type of assertion from error message.

        Args:
            error_message: Error message to analyze

        Returns:
            Assertion type string
        """
        error_lower = error_message.lower()

        for assertion_type, patterns in self.ASSERTION_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, error_lower):
                    return assertion_type

        return "unknown"

    def _tune_timeout(
        self,
        failure: TestFailure,
        historical_values: Optional[List[float]],
    ) -> Optional[HealingSuggestion]:
        """Tune timeout assertion.

        Args:
            failure: Test failure
            historical_values: Historical execution times

        Returns:
            Healing suggestion or None
        """
        # Extract timeout value from error
        timeout_match = re.search(
            r"(\d+)\s*(?:ms|milliseconds?)", failure.error_message, re.IGNORECASE
        )
        current_timeout = int(timeout_match.group(1)) if timeout_match else 5000

        # Extract actual duration if available
        duration_match = re.search(
            r"took\s+(\d+(?:\.\d+)?)\s*(?:ms|seconds?)",
            failure.error_message,
            re.IGNORECASE,
        )
        actual_duration = (
            float(duration_match.group(1)) if duration_match else current_timeout * 1.5
        )

        # Adjust
        adjustment = self.adjust_timing(current_timeout, actual_duration)

        if adjustment.confidence > 0.7:
            return HealingSuggestion(
                id=str(uuid.uuid4()),
                healing_type=HealingType.ASSERTION_TUNING,
                change_type=ChangeType.TIMING_ISSUE,
                description=f"Increase timeout from {current_timeout}ms to {int(adjustment.new_threshold)}ms",
                code_patch=f"""# Timeout Adjustment
# Old timeout: {current_timeout}ms
# New timeout: {int(adjustment.new_threshold)}ms

# Replace:
# wait_for_element(timeout={current_timeout})

# With:
wait_for_element(timeout={int(adjustment.new_threshold)})
""",
                confidence=adjustment.confidence,
                affected_files=[failure.test_file],
                auto_applicable=adjustment.confidence > 0.85,
            )

        return None

    def _tune_value_assertion(
        self,
        failure: TestFailure,
        historical_values: Optional[List[float]],
    ) -> Optional[HealingSuggestion]:
        """Tune value assertion.

        Args:
            failure: Test failure
            historical_values: Historical values

        Returns:
            Healing suggestion or None
        """
        # Extract expected and actual values
        value_match = re.search(
            r"expected\s+([\d.]+)\s+but\s+got\s+([\d.]+)",
            failure.error_message,
            re.IGNORECASE,
        )

        if not value_match:
            return None

        expected = float(value_match.group(1))
        actual = float(value_match.group(2))

        # Calculate adjustment
        if expected > actual:
            # Expected too high, lower it
            new_threshold = actual * 1.1
            reason = f"Lower expectation to match observed value ({actual})"
        else:
            # Expected too low, raise it
            new_threshold = actual * 1.05
            reason = f"Raise expectation to match observed value ({actual})"

        return HealingSuggestion(
            id=str(uuid.uuid4()),
            healing_type=HealingType.ASSERTION_TUNING,
            change_type=ChangeType.ASSERTION_FAILED,
            description=f"Update assertion: expected {expected} -> {round(new_threshold, 2)} (actual: {actual})",
            code_patch=f"""# Value Assertion Adjustment
# Old: assert value == {expected}
# New: assert value == {round(new_threshold, 2)}

# Or use range assertion:
assert {actual * 0.9} <= value <= {actual * 1.1}
""",
            confidence=0.75,
            affected_files=[failure.test_file],
            auto_applicable=False,  # Value changes need review
        )

    def _tune_range_assertion(
        self,
        failure: TestFailure,
        historical_values: Optional[List[float]],
    ) -> Optional[HealingSuggestion]:
        """Tune range-based assertion.

        Args:
            failure: Test failure
            historical_values: Historical values

        Returns:
            Healing suggestion or None
        """
        # Extract values from error
        range_match = re.search(
            r"(\d+(?:\.\d+)?)\s+(?:is\s+)?(greater than|less than|exceeds)\s+(\d+(?:\.\d+)?)",
            failure.error_message,
            re.IGNORECASE,
        )

        if not range_match:
            return None

        value = float(range_match.group(1))
        comparison = range_match.group(2)
        threshold = float(range_match.group(3))

        if "greater" in comparison or "exceeds" in comparison:
            # Value exceeds maximum
            new_threshold = value * 1.1
            description = (
                f"Increase max threshold from {threshold} to {round(new_threshold, 2)}"
            )
        else:
            # Value below minimum
            new_threshold = value * 0.9
            description = (
                f"Decrease min threshold from {threshold} to {round(new_threshold, 2)}"
            )

        return HealingSuggestion(
            id=str(uuid.uuid4()),
            healing_type=HealingType.ASSERTION_TUNING,
            change_type=ChangeType.ASSERTION_FAILED,
            description=description,
            code_patch=f"""# Range Assertion Adjustment
# Old threshold: {threshold}
# New threshold: {round(new_threshold, 2)}

assert value {"<=" if "greater" in comparison else ">="} {round(new_threshold, 2)}
""",
            confidence=0.8,
            affected_files=[failure.test_file],
            auto_applicable=False,
        )

    def _detect_flaky_pattern(
        self, failure: TestFailure
    ) -> Optional[HealingSuggestion]:
        """Detect if test failure is due to flakiness.

        Args:
            failure: Test failure

        Returns:
            Healing suggestion or None
        """
        # Check for flaky indicators in error message
        flaky_indicators = [
            "intermittent",
            "sometimes",
            "race condition",
            "timing",
            "not stable",
        ]

        error_lower = failure.error_message.lower()
        is_flaky = any(indicator in error_lower for indicator in flaky_indicators)

        if is_flaky or "AssertionError" in failure.error_type:
            return HealingSuggestion(
                id=str(uuid.uuid4()),
                healing_type=HealingType.ASSERTION_TUNING,
                change_type=ChangeType.TIMING_ISSUE,
                description="Add retry mechanism for potentially flaky assertion",
                code_patch="""# Flaky Test Fix
# Add retry logic for stability

@retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
def test_with_retry():
    # Original test code here
    pass
""",
                confidence=0.6,
                affected_files=[failure.test_file],
                auto_applicable=False,
            )

        return None

    def get_adjustment_history(self) -> List[AssertionAdjustment]:
        """Get history of all adjustments made.

        Returns:
            List of AssertionAdjustment objects
        """
        return self.adjustment_history
