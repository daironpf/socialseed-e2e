"""
Healing orchestrator for self-healing tests.

Coordinates all healing components and manages the healing workflow.
"""

import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

from ..models import (
    HealingResult,
    HealingSuggestion,
    TestFailure,
    SelfHealingConfig,
    HealingHistory,
)
from .schema.schema_adapter import SchemaAdapter
from .locator.locator_repair import LocatorRepairEngine
from .assertions.assertion_tuner import AssertionTuner
from .optimization.test_optimizer import TestOptimizer


class HealingOrchestrator:
    """Orchestrates the self-healing workflow.

    Coordinates all healing components:
    - SchemaAdapter: Handles API schema changes
    - LocatorRepairEngine: Fixes broken element locators
    - AssertionTuner: Adjusts assertion thresholds
    - TestOptimizer: Optimizes test suite

    Example:
        config = SelfHealingConfig(
            tests_dir="tests",
            auto_heal=True,
            confidence_threshold=0.8,
        )

        orchestrator = HealingOrchestrator(config)

        # Heal a test failure
        result = orchestrator.heal_failure(test_failure, page_source)

        if result.success:
            print(f"Applied {len(result.applied_suggestions)} fixes")
    """

    def __init__(
        self,
        config: Optional[SelfHealingConfig] = None,
        on_healing_applied: Optional[Callable[[HealingSuggestion, str], None]] = None,
    ):
        """Initialize healing orchestrator.

        Args:
            config: Self-healing configuration
            on_healing_applied: Callback when healing is applied
        """
        self.config = config or SelfHealingConfig()
        self.on_healing_applied = on_healing_applied

        # Initialize components
        self.schema_adapter = SchemaAdapter()
        self.locator_repair = LocatorRepairEngine()
        self.assertion_tuner = AssertionTuner()
        self.test_optimizer = TestOptimizer()

        # Tracking
        self.healing_history = HealingHistory()
        self.current_suggestions: List[HealingSuggestion] = []

    def heal_failure(
        self,
        failure: TestFailure,
        page_source: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
    ) -> HealingResult:
        """Attempt to heal a test failure.

        Args:
            failure: Test failure information
            page_source: Current page source (for locator repair)
            schema: Current API schema (for schema adaptation)

        Returns:
            HealingResult with outcome
        """
        start_time = time.time()

        result = HealingResult(
            id=str(uuid.uuid4()),
            healing_type=None,  # Will be set based on applied suggestions
            test_failure=failure,
        )

        suggestions: List[HealingSuggestion] = []

        # 1. Try schema adaptation
        if schema:
            self._try_schema_healing(failure, schema, suggestions)

        # 2. Try locator repair
        if page_source:
            self._try_locator_healing(failure, page_source, suggestions)

        # 3. Try assertion tuning
        self._try_assertion_healing(failure, suggestions)

        # 4. Store suggestions
        result.suggestions = suggestions
        self.current_suggestions = suggestions

        # 5. Apply suggestions if auto-heal enabled
        if self.config.auto_heal:
            applied = self._apply_suggestions(failure, suggestions)
            result.applied_suggestions = applied
            result.success = len(applied) > 0

        # 6. Record result
        result.execution_time_seconds = time.time() - start_time
        self._record_healing(result)

        return result

    def analyze_test_suite(self, test_dir: str) -> List[Any]:
        """Analyze test suite for optimization opportunities.

        Args:
            test_dir: Directory containing tests

        Returns:
            List of optimization suggestions
        """
        return self.test_optimizer.analyze_test_suite(test_dir)

    def get_healing_history(self) -> HealingHistory:
        """Get history of all healing operations.

        Returns:
            HealingHistory object
        """
        return self.healing_history

    def get_suggestions_for_failure(
        self,
        failure: TestFailure,
        page_source: Optional[str] = None,
    ) -> List[HealingSuggestion]:
        """Get healing suggestions without applying them.

        Args:
            failure: Test failure
            page_source: Page source if available

        Returns:
            List of suggestions
        """
        suggestions = []

        # Locator repair suggestions
        if page_source:
            locator_suggestions = self.locator_repair.analyze_locator_failure(
                failure, page_source
            )
            suggestions.extend(locator_suggestions)

        # Assertion tuning suggestions
        assertion_suggestions = self.assertion_tuner.analyze_assertion_failure(failure)
        suggestions.extend(assertion_suggestions)

        return suggestions

    def apply_suggestion(
        self,
        suggestion: HealingSuggestion,
        test_file_path: str,
    ) -> bool:
        """Apply a single healing suggestion.

        Args:
            suggestion: Healing suggestion to apply
            test_file_path: Path to test file

        Returns:
            True if applied successfully
        """
        try:
            file_path = Path(test_file_path)

            if not file_path.exists():
                return False

            # Read current content
            original_content = file_path.read_text()

            # Create backup if enabled
            if self.config.backup_enabled:
                backup_path = file_path.with_suffix(".py.bak")
                backup_path.write_text(original_content)

            # Apply patch (simplified - real implementation would be more sophisticated)
            # For now, just append a comment
            new_content = (
                original_content + f"\n\n# HEALING APPLIED: {suggestion.description}\n"
            )

            # Write new content
            file_path.write_text(new_content)

            # Notify callback
            if self.on_healing_applied:
                self.on_healing_applied(suggestion, test_file_path)

            return True

        except Exception:
            return False

    def _try_schema_healing(
        self,
        failure: TestFailure,
        schema: Dict[str, Any],
        suggestions: List[HealingSuggestion],
    ):
        """Attempt schema-based healing.

        Args:
            failure: Test failure
            schema: API schema
            suggestions: List to append suggestions to
        """
        # Record schema version
        self.schema_adapter.record_schema_version("api", schema)

        # Get schema history and detect changes
        history = self.schema_adapter.schema_history.get("api", [])
        if len(history) >= 2:
            old_schema = history[-2]["schema"]
            new_schema = history[-1]["schema"]

            changes = self.schema_adapter.detect_changes(old_schema, new_schema)

            # Generate adaptations
            for change in changes:
                suggestion = self.schema_adapter.generate_adaptation(change, "")
                if (
                    suggestion
                    and suggestion.confidence >= self.config.confidence_threshold
                ):
                    suggestions.append(suggestion)

    def _try_locator_healing(
        self,
        failure: TestFailure,
        page_source: str,
        suggestions: List[HealingSuggestion],
    ):
        """Attempt locator-based healing.

        Args:
            failure: Test failure
            page_source: Page source
            suggestions: List to append suggestions to
        """
        locator_suggestions = self.locator_repair.analyze_locator_failure(
            failure, page_source
        )

        for suggestion in locator_suggestions:
            if suggestion.confidence >= self.config.confidence_threshold:
                suggestions.append(suggestion)

    def _try_assertion_healing(
        self,
        failure: TestFailure,
        suggestions: List[HealingSuggestion],
    ):
        """Attempt assertion-based healing.

        Args:
            failure: Test failure
            suggestions: List to append suggestions to
        """
        assertion_suggestions = self.assertion_tuner.analyze_assertion_failure(failure)

        for suggestion in assertion_suggestions:
            if suggestion.confidence >= self.config.confidence_threshold:
                suggestions.append(suggestion)

    def _apply_suggestions(
        self,
        failure: TestFailure,
        suggestions: List[HealingSuggestion],
    ) -> List[HealingSuggestion]:
        """Apply healing suggestions.

        Args:
            failure: Test failure
            suggestions: Suggestions to apply

        Returns:
            List of successfully applied suggestions
        """
        applied = []
        attempts = 0

        for suggestion in suggestions:
            if attempts >= self.config.max_attempts:
                break

            if not suggestion.auto_applicable:
                continue

            # Apply to affected files
            for file_path in suggestion.affected_files:
                if self.apply_suggestion(suggestion, file_path):
                    applied.append(suggestion)
                    attempts += 1
                    break

        return applied

    def _record_healing(self, result: HealingResult):
        """Record healing result in history.

        Args:
            result: Healing result to record
        """
        self.healing_history.healings.append(result)
        self.healing_history.total_healings += 1

        if result.success:
            self.healing_history.successful_healings += 1
        else:
            self.healing_history.failed_healings += 1

        self.healing_history.last_updated = datetime.utcnow()
