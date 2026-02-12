"""Models for AI Agent Orchestration Layer.

This module defines the data models used by the orchestration layer
for autonomous testing workflows.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class TestPriority(str, Enum):
    """Priority levels for tests."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TestStatus(str, Enum):
    """Test execution status."""

    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    FLAKY = "flaky"
    SKIPPED = "skipped"
    HEALED = "healed"


class TestType(str, Enum):
    """Types of tests."""

    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    PERFORMANCE = "performance"
    SECURITY = "security"
    REGRESSION = "regression"


class RiskFactor(BaseModel):
    """Risk factor for prioritization."""

    factor_type: str = Field(
        default="general",
        description="Type of risk: code_change, business_impact, complexity, etc.",
    )
    score: float = Field(default=0.5, ge=0.0, le=1.0, description="Risk score from 0.0 to 1.0")
    description: str = Field(default="", description="Description of the risk factor")


class TestCase(BaseModel):
    """Individual test case definition."""

    id: str = Field(default="", description="Unique test identifier")
    name: str = Field(default="", description="Test name")
    description: str = Field(default="", description="Test description")
    test_type: TestType = Field(default=TestType.E2E, description="Type of test")
    priority: TestPriority = Field(default=TestPriority.MEDIUM, description="Test priority")
    service: str = Field(default="", description="Service this test belongs to")
    module: str = Field(default="", description="Test module file path")
    endpoint: Optional[str] = Field(default=None, description="API endpoint being tested")
    http_method: Optional[str] = Field(default=None, description="HTTP method")
    risk_factors: List[RiskFactor] = Field(default_factory=list, description="Risk factors")
    dependencies: List[str] = Field(
        default_factory=list, description="IDs of tests this depends on"
    )
    estimated_duration_ms: int = Field(
        default=1000, description="Estimated test duration in milliseconds"
    )
    tags: List[str] = Field(default_factory=list, description="Test tags/categories")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class TestStrategy(BaseModel):
    """Generated test strategy for a project."""

    id: str = Field(default="", description="Strategy identifier")
    name: str = Field(default="", description="Strategy name")
    description: str = Field(default="", description="Strategy description")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    target_services: List[str] = Field(default_factory=list, description="Services to test")
    test_cases: List[TestCase] = Field(default_factory=list, description="Test cases in strategy")
    execution_order: List[str] = Field(default_factory=list, description="Ordered test IDs")
    parallelization_groups: List[List[str]] = Field(
        default_factory=list, description="Groups for parallel execution"
    )
    total_estimated_duration_ms: int = Field(default=0, description="Total estimated duration")
    coverage_targets: Dict[str, float] = Field(
        default_factory=dict, description="Coverage targets by category"
    )


class TestResult(BaseModel):
    """Result of a test execution."""

    test_id: str = Field(default="", description="Test identifier")
    status: TestStatus = Field(default=TestStatus.PENDING, description="Test status")
    started_at: datetime = Field(default_factory=datetime.utcnow, description="Start timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Completion timestamp")
    duration_ms: Optional[int] = Field(default=None, description="Actual duration in milliseconds")
    attempts: int = Field(default=1, description="Number of execution attempts")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    stack_trace: Optional[str] = Field(default=None, description="Stack trace if failed")
    logs: List[str] = Field(default_factory=list, description="Execution logs")
    screenshots: List[str] = Field(
        default_factory=list, description="Screenshot paths if applicable"
    )
    response_data: Optional[Dict[str, Any]] = Field(
        default=None, description="Response data from API"
    )
    assertions_failed: List[str] = Field(default_factory=list, description="Failed assertions")
    healed: bool = Field(default=False, description="Whether test was auto-healed")
    healing_applied: Optional[str] = Field(
        default=None, description="Description of healing applied"
    )


class TestExecution(BaseModel):
    """Complete test execution record."""

    id: str = Field(default="", description="Execution identifier")
    strategy_id: str = Field(default="", description="Strategy ID")
    started_at: datetime = Field(default_factory=datetime.utcnow, description="Start timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Completion timestamp")
    status: TestStatus = Field(default=TestStatus.PENDING, description="Overall status")
    results: List[TestResult] = Field(default_factory=list, description="Individual test results")
    summary: Dict[str, int] = Field(default_factory=dict, description="Summary counts by status")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class FailurePattern(BaseModel):
    """Detected failure pattern for learning."""

    pattern_id: str = Field(default="", description="Pattern identifier")
    pattern_type: str = Field(
        default="unknown",
        description="Type: assertion_error, timeout, network_error, etc.",
    )
    signature: str = Field(default="", description="Unique pattern signature")
    frequency: int = Field(default=1, description="How many times this pattern occurred")
    affected_tests: List[str] = Field(default_factory=list, description="Test IDs affected")
    first_seen: datetime = Field(default_factory=datetime.utcnow, description="First occurrence")
    last_seen: datetime = Field(default_factory=datetime.utcnow, description="Last occurrence")
    suggested_fix: Optional[str] = Field(default=None, description="AI-suggested fix")
    success_rate_after_fix: Optional[float] = Field(
        default=None, description="Success rate after applying fix"
    )


class RetryStrategy(BaseModel):
    """Intelligent retry strategy learned from failures."""

    pattern_id: str = Field(default="", description="Associated failure pattern")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    backoff_type: str = Field(
        default="exponential", description="Backoff type: fixed, exponential, linear"
    )
    base_delay_ms: int = Field(default=1000, description="Base delay in milliseconds")
    max_delay_ms: int = Field(default=30000, description="Maximum delay in milliseconds")
    conditions: Dict[str, Any] = Field(
        default_factory=dict, description="When to apply this strategy"
    )
    success_rate: float = Field(default=0.0, description="Observed success rate")
    total_applied: int = Field(default=0, description="Times this strategy was applied")


class DebugAnalysis(BaseModel):
    """AI-powered debug analysis result."""

    analysis_id: str = Field(default="", description="Analysis identifier")
    test_id: str = Field(default="", description="Test being analyzed")
    execution_id: str = Field(default="", description="Execution ID")
    failure_type: str = Field(default="unknown", description="Classified failure type")
    root_cause: str = Field(default="", description="Identified root cause")
    confidence_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Confidence in analysis"
    )
    suggested_fixes: List[Dict[str, Any]] = Field(
        default_factory=list, description="Suggested fixes"
    )
    code_changes: List[Dict[str, Any]] = Field(
        default_factory=list, description="Specific code changes"
    )
    related_issues: List[str] = Field(default_factory=list, description="Related known issues")
    requires_human_review: bool = Field(default=False, description="Whether human review is needed")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Analysis timestamp")


class OrchestratorConfig(BaseModel):
    """Configuration for the AI Orchestrator."""

    enable_self_healing: bool = Field(default=True, description="Enable auto-fixing of flaky tests")
    enable_intelligent_retry: bool = Field(
        default=True, description="Enable learned retry strategies"
    )
    enable_auto_debug: bool = Field(default=True, description="Enable automatic debugging")
    enable_risk_prioritization: bool = Field(
        default=True, description="Enable risk-based prioritization"
    )
    max_auto_fix_attempts: int = Field(default=3, description="Maximum auto-fix attempts per test")
    auto_apply_fixes: bool = Field(
        default=False, description="Auto-apply fixes without confirmation"
    )
    parallel_workers: int = Field(default=4, description="Number of parallel test workers")
    history_retention_days: int = Field(default=30, description="Days to retain execution history")
    learning_enabled: bool = Field(default=True, description="Enable learning from failures")
    min_confidence_for_auto_fix: float = Field(
        default=0.8, ge=0.0, le=1.0, description="Min confidence to auto-apply fix"
    )
