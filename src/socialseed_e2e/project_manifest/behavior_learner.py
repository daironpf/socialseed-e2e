"""User Behavior Pattern Learning module.

This module learns patterns from user interactions, test executions,
and corrections to improve AI understanding of user preferences and behaviors.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


class BehaviorPatternType(str, Enum):
    """Types of behavior patterns."""

    TEST_PREFERENCE = "test_preference"
    CORRECTION_PATTERN = "correction_pattern"
    EXECUTION_TIMING = "execution_timing"
    FOCUS_AREA = "focus_area"
    ERROR_IGNORE = "error_ignore"
    VALIDATION_PRIORITY = "validation_priority"
    NAMING_CONVENTION = "naming_convention"
    WORKFLOW_STYLE = "workflow_style"


@dataclass
class UserAction:
    """A single user action recorded for learning."""

    action_type: str
    timestamp: datetime
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BehaviorPattern:
    """A detected behavior pattern."""

    pattern_type: BehaviorPatternType
    description: str
    confidence: float
    frequency: int
    first_seen: datetime
    last_seen: datetime
    examples: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserProfile:
    """User behavior profile with learned preferences."""

    user_id: str
    patterns: List[BehaviorPattern] = field(default_factory=list)
    preferred_test_types: List[str] = field(default_factory=list)
    preferred_naming_style: Optional[str] = None
    common_corrections: Dict[str, str] = field(default_factory=dict)
    focus_areas: List[str] = field(default_factory=list)
    risk_tolerance: str = "medium"  # low, medium, high
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class CorrectionPattern:
    """Pattern detected from user corrections."""

    original_pattern: str
    corrected_pattern: str
    frequency: int
    confidence: float
    context_type: str  # assertion, validation, naming, etc.
    first_seen: datetime
    last_seen: datetime


class UserBehaviorLearner:
    """Learns and adapts to user behavior patterns."""

    def __init__(self, storage_path: Optional[Path] = None):
        """Initialize the behavior learner.

        Args:
            storage_path: Path to store learned patterns
        """
        self.storage_path = storage_path or Path(".e2e/behavior_learning")
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.actions_file = self.storage_path / "actions.jsonl"
        self.patterns_file = self.storage_path / "patterns.json"
        self.profile_file = self.storage_path / "user_profile.json"

        self.actions: List[UserAction] = []
        self.patterns: List[BehaviorPattern] = []
        self.profile: Optional[UserProfile] = None
        self.correction_patterns: List[CorrectionPattern] = []

        self._load_data()

    def _load_data(self) -> None:
        """Load existing data from storage."""
        # Load patterns
        if self.patterns_file.exists():
            try:
                with open(self.patterns_file, "r") as f:
                    data = json.load(f)
                    self.patterns = [BehaviorPattern(**p) for p in data]
            except Exception:
                pass

        # Load profile
        if self.profile_file.exists():
            try:
                with open(self.profile_file, "r") as f:
                    data = json.load(f)
                    self.profile = UserProfile(**data)
            except Exception:
                pass

    def record_action(self, action_type: str, context: Dict[str, Any] = None) -> None:
        """Record a user action.

        Args:
            action_type: Type of action performed
            context: Additional context about the action
        """
        action = UserAction(
            action_type=action_type,
            timestamp=datetime.now(),
            context=context or {},
        )

        self.actions.append(action)

        # Persist to disk
        with open(self.actions_file, "a") as f:
            action_dict = {
                "action_type": action.action_type,
                "timestamp": action.timestamp.isoformat(),
                "context": action.context,
            }
            f.write(json.dumps(action_dict) + "\n")

        # Update patterns based on new action
        self._update_patterns(action)

    def record_correction(
        self,
        original: str,
        corrected: str,
        context_type: str = "general",
        metadata: Dict[str, Any] = None,
    ) -> None:
        """Record a user correction for pattern learning.

        Args:
            original: Original value/text
            corrected: Corrected value/text
            context_type: Type of context (assertion, naming, etc.)
            metadata: Additional metadata
        """
        # Record as action
        self.record_action(
            "correction",
            {
                "original": original,
                "corrected": corrected,
                "context_type": context_type,
                **(metadata or {}),
            },
        )

        # Update or create correction pattern
        self._update_correction_pattern(original, corrected, context_type)

    def _update_correction_pattern(
        self, original: str, corrected: str, context_type: str
    ) -> None:
        """Update correction patterns."""
        # Look for existing pattern
        for pattern in self.correction_patterns:
            if (
                pattern.original_pattern == original
                and pattern.corrected_pattern == corrected
            ):
                pattern.frequency += 1
                pattern.last_seen = datetime.now()
                pattern.confidence = min(0.95, pattern.confidence + 0.05)
                return

        # Create new pattern
        new_pattern = CorrectionPattern(
            original_pattern=original,
            corrected_pattern=corrected,
            frequency=1,
            confidence=0.5,
            context_type=context_type,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
        )
        self.correction_patterns.append(new_pattern)

    def _update_patterns(self, action: UserAction) -> None:
        """Update behavior patterns based on new action."""
        # Detect test preferences
        if action.action_type == "test_generation":
            self._detect_test_preference(action)

        # Detect focus areas
        if action.action_type == "test_execution":
            self._detect_focus_area(action)

        # Detect naming conventions
        if action.action_type == "correction":
            self._detect_naming_convention(action)

    def _detect_test_preference(self, action: UserAction) -> None:
        """Detect test type preferences."""
        test_type = action.context.get("test_type")
        if not test_type:
            return

        # Look for existing pattern
        for pattern in self.patterns:
            if (
                pattern.pattern_type == BehaviorPatternType.TEST_PREFERENCE
                and pattern.description == test_type
            ):
                pattern.frequency += 1
                pattern.last_seen = datetime.now()
                pattern.confidence = min(0.95, pattern.confidence + 0.02)
                return

        # Create new pattern
        new_pattern = BehaviorPattern(
            pattern_type=BehaviorPatternType.TEST_PREFERENCE,
            description=test_type,
            confidence=0.5,
            frequency=1,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
        )
        self.patterns.append(new_pattern)

    def _detect_focus_area(self, action: UserAction) -> None:
        """Detect user's focus areas."""
        service = action.context.get("service")
        endpoint = action.context.get("endpoint")

        if not service and not endpoint:
            return

        focus_key = service or endpoint

        for pattern in self.patterns:
            if (
                pattern.pattern_type == BehaviorPatternType.FOCUS_AREA
                and pattern.description == focus_key
            ):
                pattern.frequency += 1
                pattern.last_seen = datetime.now()
                return

        new_pattern = BehaviorPattern(
            pattern_type=BehaviorPatternType.FOCUS_AREA,
            description=focus_key,
            confidence=0.6,
            frequency=1,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
        )
        self.patterns.append(new_pattern)

    def _detect_naming_convention(self, action: UserAction) -> None:
        """Detect naming conventions from corrections."""
        original = action.context.get("original", "")
        corrected = action.context.get("corrected", "")

        if not original or not corrected:
            return

        # Detect snake_case vs camelCase
        if "_" in corrected and "_" not in original:
            convention = "snake_case"
        elif any(c.isupper() for c in corrected[1:]) and not any(
            c.isupper() for c in original[1:]
        ):
            convention = "camelCase"
        else:
            return

        for pattern in self.patterns:
            if (
                pattern.pattern_type == BehaviorPatternType.NAMING_CONVENTION
                and pattern.description == convention
            ):
                pattern.frequency += 1
                pattern.last_seen = datetime.now()
                pattern.confidence = min(0.95, pattern.confidence + 0.1)
                return

        new_pattern = BehaviorPattern(
            pattern_type=BehaviorPatternType.NAMING_CONVENTION,
            description=convention,
            confidence=0.7,
            frequency=1,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
        )
        self.patterns.append(new_pattern)

    def get_learned_preferences(self) -> Dict[str, Any]:
        """Get all learned preferences.

        Returns:
            Dictionary with learned preferences
        """
        test_preferences = [
            p
            for p in self.patterns
            if p.pattern_type == BehaviorPatternType.TEST_PREFERENCE
        ]
        naming_conventions = [
            p
            for p in self.patterns
            if p.pattern_type == BehaviorPatternType.NAMING_CONVENTION
        ]
        focus_areas = [
            p for p in self.patterns if p.pattern_type == BehaviorPatternType.FOCUS_AREA
        ]

        return {
            "preferred_test_types": [p.description for p in test_preferences[:5]],
            "preferred_naming_style": naming_conventions[0].description
            if naming_conventions
            else None,
            "focus_areas": [p.description for p in focus_areas[:5]],
            "common_corrections": len(self.correction_patterns),
            "total_actions_recorded": len(self.actions),
            "confidence_scores": {
                "test_preferences": max(
                    [p.confidence for p in test_preferences], default=0
                ),
                "naming_conventions": max(
                    [p.confidence for p in naming_conventions], default=0
                ),
            },
        }

    def suggest_corrections(
        self, text: str, context_type: str = "general"
    ) -> List[str]:
        """Suggest corrections based on learned patterns.

        Args:
            text: Text to check for corrections
            context_type: Type of context

        Returns:
            List of suggested corrections
        """
        suggestions = []

        for pattern in self.correction_patterns:
            if pattern.context_type == context_type:
                # Check for similar patterns
                if self._is_similar(text, pattern.original_pattern):
                    if pattern.confidence > 0.7:
                        suggestions.append(pattern.corrected_pattern)

        return suggestions

    def _is_similar(self, text1: str, text2: str) -> bool:
        """Check if two texts are similar."""
        # Simple similarity check
        return text1.lower() == text2.lower() or text1.lower() in text2.lower()

    def get_test_generation_hints(self) -> Dict[str, Any]:
        """Get hints for test generation based on learned behavior.

        Returns:
            Dictionary with hints and preferences
        """
        hints = {
            "preferred_patterns": [],
            "focus_areas": [],
            "avoid_patterns": [],
            "naming_convention": None,
            "validation_strictness": "medium",
        }

        # Get naming convention
        naming_patterns = [
            p
            for p in self.patterns
            if p.pattern_type == BehaviorPatternType.NAMING_CONVENTION
        ]
        if naming_patterns:
            best = max(naming_patterns, key=lambda p: p.confidence)
            hints["naming_convention"] = best.description

        # Get focus areas
        focus_patterns = [
            p for p in self.patterns if p.pattern_type == BehaviorPatternType.FOCUS_AREA
        ]
        hints["focus_areas"] = [p.description for p in focus_patterns[:5]]

        # Get preferred test types
        test_patterns = [
            p
            for p in self.patterns
            if p.pattern_type == BehaviorPatternType.TEST_PREFERENCE
        ]
        hints["preferred_patterns"] = [p.description for p in test_patterns[:5]]

        return hints

    def analyze_behavior_trends(self, days: int = 30) -> Dict[str, Any]:
        """Analyze behavior trends over time.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with trend analysis
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        recent_actions = [a for a in self.actions if a.timestamp >= cutoff_date]

        if not recent_actions:
            return {"message": "No recent activity"}

        # Count action types
        action_counts = {}
        for action in recent_actions:
            action_counts[action.action_type] = (
                action_counts.get(action.action_type, 0) + 1
            )

        # Most active areas
        focus_patterns = [
            p for p in self.patterns if p.pattern_type == BehaviorPatternType.FOCUS_AREA
        ]
        active_areas = sorted(focus_patterns, key=lambda p: p.frequency, reverse=True)[
            :5
        ]

        return {
            "period_days": days,
            "total_actions": len(recent_actions),
            "action_breakdown": action_counts,
            "most_active_areas": [p.description for p in active_areas],
            "emerging_patterns": [
                p.description for p in self.patterns if p.frequency <= 3
            ],
            "established_patterns": [
                p.description for p in self.patterns if p.frequency > 10
            ],
        }

    def save(self) -> None:
        """Save all learned data to storage."""
        # Save patterns
        patterns_data = []
        for pattern in self.patterns:
            pattern_dict = {
                "pattern_type": pattern.pattern_type.value,
                "description": pattern.description,
                "confidence": pattern.confidence,
                "frequency": pattern.frequency,
                "first_seen": pattern.first_seen.isoformat(),
                "last_seen": pattern.last_seen.isoformat(),
                "examples": pattern.examples,
                "context": pattern.context,
            }
            patterns_data.append(pattern_dict)

        with open(self.patterns_file, "w") as f:
            json.dump(patterns_data, f, indent=2)

        # Save correction patterns
        corrections_data = []
        for pattern in self.correction_patterns:
            corrections_data.append(
                {
                    "original_pattern": pattern.original_pattern,
                    "corrected_pattern": pattern.corrected_pattern,
                    "frequency": pattern.frequency,
                    "confidence": pattern.confidence,
                    "context_type": pattern.context_type,
                    "first_seen": pattern.first_seen.isoformat(),
                    "last_seen": pattern.last_seen.isoformat(),
                }
            )

        corrections_file = self.storage_path / "correction_patterns.json"
        with open(corrections_file, "w") as f:
            json.dump(corrections_data, f, indent=2)
