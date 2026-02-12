"""Models for ML-Based Predictive Test Selection.

This module defines data models used by machine learning components for
test selection, impact analysis, and flakiness detection.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TestPriority(str, Enum):
    """Priority levels for tests based on ML predictions."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    SKIP = "skip"


class ChangeType(str, Enum):
    """Types of code changes."""

    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"
    RENAMED = "renamed"


class FileType(str, Enum):
    """Types of source files."""

    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CONFIG = "config"
    TEST = "test"
    OTHER = "other"


class TestMetrics(BaseModel):
    """Metrics for a single test execution."""

    test_id: str = Field(..., description="Unique test identifier")
    test_name: str = Field(..., description="Test name")
    duration_ms: int = Field(..., description="Execution time in milliseconds")
    passed: bool = Field(..., description="Whether test passed")
    failed: bool = Field(..., description="Whether test failed")
    skipped: bool = Field(default=False, description="Whether test was skipped")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    git_commit: Optional[str] = Field(None, description="Git commit hash")
    git_branch: Optional[str] = Field(None, description="Git branch")
    changed_files: List[str] = Field(default_factory=list, description="Files changed")
    coverage_percentage: float = Field(default=0.0, description="Code coverage %")


class TestHistory(BaseModel):
    """Historical data for a test."""

    test_id: str = Field(..., description="Test identifier")
    test_name: str = Field(..., description="Test name")
    total_runs: int = Field(default=0, description="Total executions")
    pass_count: int = Field(default=0, description="Number of passes")
    fail_count: int = Field(default=0, description="Number of failures")
    skip_count: int = Field(default=0, description="Number of skips")
    avg_duration_ms: float = Field(default=0.0, description="Average duration")
    last_run: Optional[datetime] = Field(None, description="Last execution time")
    failure_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Failure rate")
    recent_failures: int = Field(default=0, description="Failures in last 10 runs")
    flaky_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Flakiness score")
    runs: List[TestMetrics] = Field(default_factory=list, description="Recent runs")


class CodeChange(BaseModel):
    """Represents a code change in git."""

    file_path: str = Field(..., description="Path to changed file")
    change_type: ChangeType = Field(..., description="Type of change")
    file_type: FileType = Field(default=FileType.OTHER, description="File type")
    lines_added: int = Field(default=0, description="Lines added")
    lines_deleted: int = Field(default=0, description="Lines deleted")
    functions_changed: List[str] = Field(default_factory=list, description="Changed functions")
    classes_changed: List[str] = Field(default_factory=list, description="Changed classes")
    imports_changed: List[str] = Field(default_factory=list, description="Changed imports")
    is_test_file: bool = Field(default=False, description="Whether file is a test")


class ImpactAnalysis(BaseModel):
    """Analysis of impact from code changes."""

    changed_files: List[CodeChange] = Field(default_factory=list, description="Changed files")
    affected_tests: List[str] = Field(default_factory=list, description="Tests likely affected")
    impact_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Overall impact score")
    risk_level: TestPriority = Field(default=TestPriority.LOW, description="Risk level")
    new_code_coverage: float = Field(default=0.0, description="Coverage of new code")
    modified_code_coverage: float = Field(default=0.0, description="Coverage of modified code")
    estimated_tests_to_run: int = Field(default=0, description="Estimated tests needed")


class TestPrediction(BaseModel):
    """ML prediction for a test."""

    test_id: str = Field(..., description="Test identifier")
    test_name: str = Field(..., description="Test name")
    failure_probability: float = Field(..., ge=0.0, le=1.0, description="Probability of failure")
    estimated_duration_ms: int = Field(..., description="Estimated execution time")
    priority: TestPriority = Field(..., description="Recommended priority")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Prediction confidence")
    reasons: List[str] = Field(default_factory=list, description="Reasons for prediction")
    affected_by_changes: bool = Field(default=False, description="Affected by code changes")
    suggested_order: int = Field(default=0, description="Suggested execution order")


class TestSelectionResult(BaseModel):
    """Result of ML-based test selection."""

    total_tests: int = Field(..., description="Total tests available")
    selected_tests: List[TestPrediction] = Field(default_factory=list, description="Selected tests")
    skipped_tests: List[str] = Field(default_factory=list, description="Tests to skip")
    estimated_duration_ms: int = Field(default=0, description="Total estimated duration")
    estimated_coverage: float = Field(default=0.0, description="Estimated coverage %")
    risk_reduction: float = Field(default=0.0, description="Risk reduction score")
    savings_percentage: float = Field(default=0.0, description="Time savings %")
    impact_analysis: Optional[ImpactAnalysis] = Field(None, description="Impact analysis")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class FlakinessReport(BaseModel):
    """Report on flaky tests."""

    total_tests: int = Field(..., description="Total tests analyzed")
    flaky_tests: List[Dict[str, Any]] = Field(default_factory=list, description="Flaky tests found")
    flaky_count: int = Field(default=0, description="Number of flaky tests")
    flaky_rate: float = Field(default=0.0, description="Percentage of flaky tests")
    top_flaky_tests: List[str] = Field(default_factory=list, description="Top flaky test names")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class CoverageGap(BaseModel):
    """Represents a coverage gap in the codebase."""

    file_path: str = Field(..., description="File with gap")
    function_name: Optional[str] = Field(None, description="Function with gap")
    line_start: int = Field(..., description="Start line")
    line_end: int = Field(..., description="End line")
    gap_type: str = Field(..., description="Type of gap (branch, line, function)")
    severity: TestPriority = Field(..., description="Gap severity")
    suggested_test: Optional[str] = Field(None, description="Suggested test to add")


class CoverageReport(BaseModel):
    """Coverage analysis report."""

    overall_coverage: float = Field(..., ge=0.0, le=100.0, description="Overall coverage %")
    line_coverage: float = Field(default=0.0, description="Line coverage %")
    branch_coverage: float = Field(default=0.0, description="Branch coverage %")
    function_coverage: float = Field(default=0.0, description="Function coverage %")
    gaps: List[CoverageGap] = Field(default_factory=list, description="Coverage gaps")
    gap_count: int = Field(default=0, description="Number of gaps")
    files_without_tests: List[str] = Field(default_factory=list, description="Files needing tests")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class RedundantTest(BaseModel):
    """Represents a potentially redundant test."""

    test_id: str = Field(..., description="Test identifier")
    test_name: str = Field(..., description="Test name")
    similar_to: List[str] = Field(default_factory=list, description="Similar test names")
    similarity_score: float = Field(default=0.0, description="Similarity score")
    coverage_overlap: float = Field(default=0.0, description="Coverage overlap %")
    recommendation: str = Field(default="review", description="Recommendation")


class RedundancyReport(BaseModel):
    """Report on redundant tests."""

    total_tests: int = Field(..., description="Total tests analyzed")
    redundant_tests: List[RedundantTest] = Field(
        default_factory=list, description="Redundant tests"
    )
    redundancy_count: int = Field(default=0, description="Number of redundant tests")
    potential_savings_ms: int = Field(default=0, description="Potential time savings")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class MLModelPerformance(BaseModel):
    """Performance metrics for ML models."""

    model_name: str = Field(..., description="Model name")
    accuracy: float = Field(default=0.0, ge=0.0, le=1.0, description="Model accuracy")
    precision: float = Field(default=0.0, ge=0.0, le=1.0, description="Model precision")
    recall: float = Field(default=0.0, ge=0.0, le=1.0, description="Model recall")
    f1_score: float = Field(default=0.0, ge=0.0, le=1.0, description="F1 score")
    last_trained: Optional[datetime] = Field(None, description="Last training time")
    training_samples: int = Field(default=0, description="Number of training samples")


class MLOrchestratorConfig(BaseModel):
    """Configuration for ML orchestrator."""

    enable_predictions: bool = Field(default=True, description="Enable predictions")
    enable_flakiness_detection: bool = Field(default=True, description="Enable flakiness detection")
    enable_coverage_analysis: bool = Field(default=True, description="Enable coverage analysis")
    enable_redundancy_detection: bool = Field(
        default=True, description="Enable redundancy detection"
    )
    selection_threshold: float = Field(
        default=0.3, ge=0.0, le=1.0, description="Test selection threshold"
    )
    flakiness_threshold: float = Field(
        default=0.2, ge=0.0, le=1.0, description="Flakiness threshold"
    )
    max_tests_to_select: Optional[int] = Field(None, description="Maximum tests to select")
    min_confidence: float = Field(default=0.6, ge=0.0, le=1.0, description="Minimum confidence")
    history_window_days: int = Field(default=30, description="Days of history to use")
