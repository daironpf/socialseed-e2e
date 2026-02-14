"""Models for Token-Centric Performance Testing.

Data models for tracking LLM token usage, costs, and performance metrics.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TokenEventType(str, Enum):
    """Types of token usage events."""

    LLM_CALL = "llm_call"
    PROMPT_SUBMITTED = "prompt_submitted"
    RESPONSE_RECEIVED = "response_received"
    REASONING_STEP = "reasoning_step"
    TOOL_CALL = "tool_call"
    CONTEXT_UPDATE = "context_update"
    CACHE_HIT = "cache_hit"
    CACHE_MISS = "cache_miss"


class CostTier(str, Enum):
    """Cost tiers for different LLM models."""

    CHEAP = "cheap"  # < $0.001 per 1K tokens
    STANDARD = "standard"  # $0.001 - $0.01 per 1K tokens
    PREMIUM = "premium"  # $0.01 - $0.1 per 1K tokens
    ENTERPRISE = "enterprise"  # > $0.1 per 1K tokens


class TokenUsage(BaseModel):
    """Token usage for a single LLM call."""

    input_tokens: int = Field(..., ge=0)
    output_tokens: int = Field(..., ge=0)
    total_tokens: int = Field(..., ge=0)

    @classmethod
    def from_counts(cls, input_tokens: int, output_tokens: int) -> "TokenUsage":
        """Create TokenUsage from input and output counts."""
        return cls(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
        )


class LatencyMetrics(BaseModel):
    """Latency metrics for an operation."""

    time_to_first_token_ms: Optional[float] = None
    total_latency_ms: float
    tokens_per_second: Optional[float] = None
    queue_time_ms: Optional[float] = None


class CostBreakdown(BaseModel):
    """Cost breakdown for token usage."""

    input_cost_usd: float = Field(..., ge=0)
    output_cost_usd: float = Field(..., ge=0)
    total_cost_usd: float = Field(..., ge=0)
    currency: str = "USD"

    # Cost per token metrics
    cost_per_1k_input_tokens: float
    cost_per_1k_output_tokens: float


class LLMCall(BaseModel):
    """Record of a single LLM call."""

    call_id: str
    timestamp: datetime
    event_type: TokenEventType

    # Model information
    model_name: str
    provider: str
    cost_tier: CostTier

    # Token usage
    token_usage: TokenUsage

    # Latency
    latency: LatencyMetrics

    # Cost
    cost: CostBreakdown

    # Context
    test_case_id: Optional[str] = None
    task_id: Optional[str] = None
    issue_id: Optional[str] = None
    agent_name: Optional[str] = None
    operation_type: Optional[str] = None

    # Metadata
    cache_hit: bool = False
    reasoning_steps: int = 0
    tool_calls_count: int = 0
    context_window_size: Optional[int] = None

    # Raw data (optional, for debugging)
    prompt_preview: Optional[str] = None  # First 200 chars
    response_preview: Optional[str] = None  # First 200 chars


class ReasoningLoop(BaseModel):
    """Detected reasoning loop (zombie agent)."""

    loop_id: str
    detected_at: datetime
    agent_name: Optional[str] = None
    task_id: Optional[str] = None

    # Loop characteristics
    reasoning_steps: int
    time_spent_seconds: float
    tokens_consumed: int
    cost_incurred_usd: float

    # Pattern
    repeated_phrases: List[str] = Field(default_factory=list)
    circular_references: List[str] = Field(default_factory=list)
    no_progress_indicators: List[str] = Field(default_factory=list)

    # Conclusion
    reached_conclusion: bool
    conclusion_quality: Optional[str] = None  # "high", "medium", "low", "none"


class CostRegression(BaseModel):
    """Cost regression detected in CI/CD."""

    regression_id: str
    detected_at: datetime

    # Baseline vs Current
    baseline_cost_usd: float
    current_cost_usd: float
    increase_percentage: float
    increase_absolute_usd: float

    # Threshold
    threshold_percentage: float = 15.0
    exceeded: bool

    # Details
    affected_flows: List[str] = Field(default_factory=list)
    test_cases_affected: List[str] = Field(default_factory=list)


class OptimizationRecommendation(BaseModel):
    """Recommendation for cost/performance optimization."""

    recommendation_id: str
    category: str  # "truncation", "caching", "model_downgrade", "batching", "other"
    priority: str  # "critical", "high", "medium", "low"

    title: str
    description: str

    # Impact estimation
    estimated_savings_usd: Optional[float] = None
    estimated_savings_percentage: Optional[float] = None
    estimated_latency_improvement_ms: Optional[float] = None

    # Implementation
    affected_files: List[str] = Field(default_factory=list)
    suggested_changes: Optional[str] = None
    code_example: Optional[str] = None

    # Effort
    implementation_effort: str  # "low", "medium", "high"
    risk_level: str  # "low", "medium", "high"


class TokenBudget(BaseModel):
    """Budget configuration for token usage."""

    budget_id: str
    name: str
    description: Optional[str] = None

    # Budget limits
    max_input_tokens: Optional[int] = None
    max_output_tokens: Optional[int] = None
    max_total_tokens: Optional[int] = None
    max_cost_usd: Optional[float] = None

    # Time window
    time_window_minutes: Optional[int] = None

    # Scope
    scope_type: str  # "issue", "task", "test_case", "agent", "global"
    scope_id: Optional[str] = None

    # Actions on breach
    on_budget_breach: str = "warn"  # "warn", "block", "alert"
    alert_channels: List[str] = Field(default_factory=list)

    # Current usage
    current_usage: TokenUsage = Field(
        default_factory=lambda: TokenUsage(
            input_tokens=0, output_tokens=0, total_tokens=0
        )
    )
    current_cost_usd: float = 0.0

    # Status
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)


class TestCaseMetrics(BaseModel):
    """Metrics for a single test case."""

    test_case_id: str
    test_name: str

    # Token usage
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0

    # Cost
    total_cost_usd: float = 0.0

    # Latency
    avg_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    min_latency_ms: float = 0.0

    # Calls
    llm_calls_count: int = 0
    cache_hits: int = 0
    cache_misses: int = 0

    # Issues
    reasoning_loops_detected: int = 0
    budget_breaches: int = 0

    # Timestamp
    executed_at: datetime = Field(default_factory=datetime.now)


class TaskMetrics(BaseModel):
    """Metrics aggregated at task level."""

    task_id: str
    task_name: str

    # Aggregated metrics
    test_cases: List[TestCaseMetrics] = Field(default_factory=list)

    # Totals
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0

    # Performance
    avg_latency_ms: float = 0.0
    total_execution_time_seconds: float = 0.0

    # Issues
    total_reasoning_loops: int = 0
    total_budget_breaches: int = 0

    # Efficiency
    cache_hit_rate: float = 0.0
    tokens_per_second: float = 0.0
    cost_per_1k_tokens: float = 0.0


class CostEfficiencyReport(BaseModel):
    """Complete cost efficiency report."""

    report_id: str
    generated_at: datetime

    # Overall metrics
    total_llm_calls: int
    total_input_tokens: int
    total_output_tokens: int
    total_tokens: int
    total_cost_usd: float

    # Performance
    avg_latency_ms: float
    total_execution_time_seconds: float

    # Breakdowns
    by_model: Dict[str, Dict[str, Any]]
    by_test_case: List[TestCaseMetrics]
    by_task: List[TaskMetrics]

    # Issues detected
    reasoning_loops: List[ReasoningLoop]
    cost_regressions: List[CostRegression]
    budget_breaches: List[Dict[str, Any]]

    # Recommendations
    optimization_recommendations: List[OptimizationRecommendation]

    # Trends
    cost_trend_percentage: Optional[float] = None  # vs previous run
    latency_trend_percentage: Optional[float] = None  # vs previous run

    # Summary
    summary: str
    health_score: int = Field(..., ge=0, le=100)  # Overall efficiency score
    status: str  # "healthy", "warning", "critical"


class TokenMonitorConfig(BaseModel):
    """Configuration for token monitoring."""

    enabled: bool = True

    # Tracking settings
    track_all_llm_calls: bool = True
    track_prompts: bool = False  # For privacy, only track previews
    track_responses: bool = False

    # Cost settings
    default_input_cost_per_1k: float = 0.01  # $0.01 per 1K input tokens
    default_output_cost_per_1k: float = 0.03  # $0.03 per 1K output tokens

    # Model costs override
    model_costs: Dict[str, Dict[str, float]] = Field(default_factory=dict)

    # Regression detection
    regression_threshold_percentage: float = 15.0
    compare_with_baseline: bool = True
    baseline_file: Optional[str] = None

    # Loop detection
    loop_detection_enabled: bool = True
    max_reasoning_steps: int = 10
    max_reasoning_time_seconds: float = 30.0

    # Budgeting
    global_budget_enabled: bool = False
    global_max_cost_usd: Optional[float] = None
    global_max_tokens: Optional[int] = None

    # Reporting
    report_output_dir: str = "telemetry"
    report_format: str = "json"
    generate_report_after_execution: bool = True

    # CI/CD
    fail_on_regression: bool = True
    fail_on_budget_breach: bool = False
    fail_health_score_below: Optional[int] = 50
