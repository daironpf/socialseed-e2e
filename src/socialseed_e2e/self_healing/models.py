"""
Models for self-healing test automation.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class HealingType(str, Enum):
    """Types of self-healing operations."""

    SCHEMA_ADAPTATION = "schema_adaptation"
    LOCATOR_REPAIR = "locator_repair"
    ASSERTION_TUNING = "assertion_tuning"
    TEST_OPTIMIZATION = "test_optimization"


class ChangeType(str, Enum):
    """Types of changes detected."""

    FIELD_RENAMED = "field_renamed"
    FIELD_REMOVED = "field_removed"
    FIELD_ADDED = "field_added"
    TYPE_CHANGED = "type_changed"
    SCHEMA_STRUCTURE = "schema_structure"
    LOCATOR_BROKEN = "locator_broken"
    LOCATOR_CHANGED = "locator_changed"
    ASSERTION_FAILED = "assertion_failed"
    THRESHOLD_ADJUST = "threshold_adjust"
    TIMING_ISSUE = "timing_issue"


class SchemaChange(BaseModel):
    """Represents a schema change."""

    change_type: ChangeType = Field(..., description="Type of change")
    field_path: str = Field(..., description="Path to affected field")
    old_value: Optional[str] = Field(default=None, description="Previous value")
    new_value: Optional[str] = Field(default=None, description="New value")
    severity: str = Field(default="medium", description="Change severity")
    description: str = Field(..., description="Human-readable description")

    model_config = {"populate_by_name": True}


class LocatorRepair(BaseModel):
    """Represents a locator repair operation."""

    id: str = Field(..., description="Repair ID")
    old_locator: str = Field(..., description="Original broken locator")
    new_locator: str = Field(..., description="Repaired locator")
    locator_type: str = Field(..., description="Type of locator (css, xpath, id, etc.)")
    confidence: float = Field(
        default=0.8, ge=0.0, le=1.0, description="Confidence level"
    )
    repair_strategy: str = Field(..., description="Strategy used for repair")
    element_attributes: Dict[str, Any] = Field(
        default_factory=dict, description="Element attributes found"
    )

    model_config = {"populate_by_name": True}


class AssertionAdjustment(BaseModel):
    """Represents an assertion adjustment."""

    id: str = Field(..., description="Adjustment ID")
    assertion_type: str = Field(..., description="Type of assertion")
    old_threshold: Optional[float] = Field(
        default=None, description="Previous threshold"
    )
    new_threshold: float = Field(..., description="Adjusted threshold")
    field_path: str = Field(..., description="Field being asserted")
    reason: str = Field(..., description="Reason for adjustment")
    confidence: float = Field(
        default=0.8, ge=0.0, le=1.0, description="Confidence level"
    )

    model_config = {"populate_by_name": True}


class TestOptimization(BaseModel):
    """Represents a test optimization suggestion."""

    id: str = Field(..., description="Optimization ID")
    optimization_type: str = Field(..., description="Type of optimization")
    test_files: List[str] = Field(
        default_factory=list, description="Affected test files"
    )
    description: str = Field(..., description="Optimization description")
    expected_improvement: str = Field(..., description="Expected improvement")
    confidence: float = Field(
        default=0.8, ge=0.0, le=1.0, description="Confidence level"
    )

    model_config = {"populate_by_name": True}


class TestFailure(BaseModel):
    """Represents a test failure."""

    id: str = Field(..., description="Failure ID")
    test_file: str = Field(..., description="Test file path")
    test_name: str = Field(..., description="Test name")
    error_message: str = Field(..., description="Error message")
    error_type: str = Field(default="AssertionError", description="Type of error")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    stack_trace: Optional[str] = Field(default=None, description="Full stack trace")
    screenshot: Optional[str] = Field(
        default=None, description="Screenshot path if available"
    )

    model_config = {"populate_by_name": True}


class HealingSuggestion(BaseModel):
    """Represents a healing suggestion."""

    id: str = Field(..., description="Suggestion ID")
    healing_type: HealingType = Field(..., description="Type of healing")
    change_type: ChangeType = Field(..., description="Type of change")
    description: str = Field(..., description="Human-readable description")
    code_patch: str = Field(..., description="Suggested code patch")
    confidence: float = Field(
        default=0.8, ge=0.0, le=1.0, description="Confidence level"
    )
    affected_files: List[str] = Field(
        default_factory=list, description="Files to modify"
    )
    auto_applicable: bool = Field(
        default=False, description="Whether fix can be auto-applied"
    )

    model_config = {"populate_by_name": True}


class HealingResult(BaseModel):
    """Result of a healing operation."""

    id: str = Field(..., description="Result ID")
    healing_type: HealingType = Field(..., description="Type of healing performed")
    test_failure: TestFailure = Field(..., description="Original test failure")
    suggestions: List[HealingSuggestion] = Field(
        default_factory=list, description="Healing suggestions"
    )
    applied_suggestions: List[HealingSuggestion] = Field(
        default_factory=list, description="Applied suggestions"
    )
    success: bool = Field(default=False, description="Whether healing was successful")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    execution_time_seconds: float = Field(
        default=0.0, description="Time to execute healing"
    )
    error_message: Optional[str] = Field(
        default=None, description="Error if healing failed"
    )

    model_config = {"populate_by_name": True}


class SelfHealingConfig(BaseModel):
    """Configuration for self-healing engine."""

    tests_dir: str = Field(default="tests", description="Tests directory")
    services_dir: str = Field(default="services", description="Services directory")
    auto_heal: bool = Field(default=False, description="Enable auto-healing")
    auto_commit: bool = Field(default=False, description="Auto-commit changes")
    confidence_threshold: float = Field(
        default=0.8, ge=0.0, le=1.0, description="Minimum confidence for auto-heal"
    )
    max_attempts: int = Field(default=3, description="Maximum healing attempts")
    backup_enabled: bool = Field(
        default=True, description="Create backups before healing"
    )
    learning_enabled: bool = Field(
        default=True, description="Enable learning from failures"
    )

    model_config = {"populate_by_name": True}


class HealingHistory(BaseModel):
    """History of healing operations."""

    healings: List[HealingResult] = Field(
        default_factory=list, description="List of healings"
    )
    total_healings: int = Field(default=0, description="Total number of healings")
    successful_healings: int = Field(
        default=0, description="Number of successful healings"
    )
    failed_healings: int = Field(default=0, description="Number of failed healings")
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"populate_by_name": True}
