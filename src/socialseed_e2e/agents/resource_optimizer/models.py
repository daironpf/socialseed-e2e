"""
Models for Resource Optimization Agent (FinOps).

Defines data structures for tracking and optimizing LLM resource consumption.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ModelSize(str, Enum):
    """LLM model sizes for cost optimization."""

    SMALL = "small"  # e.g., GPT-4o-mini, Claude Haiku
    MEDIUM = "medium"  # e.g., GPT-4o, Claude Sonnet
    LARGE = "large"  # e.g., GPT-4 Turbo, Claude Opus
    reasoning = "reasoning"  # e.g., o1, o3-mini


class TaskComplexity(str, Enum):
    """Classification of task complexity for model selection."""

    SIMPLE = "simple"  # Locator repair, simple assertions
    MODERATE = "moderate"  # Test generation for standard endpoints
    COMPLEX = "complex"  # Test generation for complex flows
    ADVANCED = "advanced"  # Strategic planning, semantic analysis


class ResourceBudget(BaseModel):
    """Budget constraints for resource usage."""

    max_tokens_per_task: Optional[int] = None
    max_cost_per_task_usd: Optional[float] = None
    max_latency_ms: Optional[float] = None
    max_api_calls: Optional[int] = None


class ModelRecommendation(BaseModel):
    """Recommended model for a specific task."""

    model_name: str
    provider: str
    model_size: ModelSize
    estimated_cost_usd: float
    estimated_latency_ms: float
    confidence: float = Field(..., ge=0, le=1)
    reasoning: str


class OptimizationStrategy(BaseModel):
    """Strategy for resource optimization."""

    strategy_id: str
    name: str
    description: str

    # When to apply
    task_complexity: TaskComplexity
    conditions: Dict[str, Any] = {}

    # What to do
    recommended_model: Optional[str] = None
    model_size_downgrade: bool = False
    use_cache: bool = True
    batch_requests: bool = False
    truncate_context: bool = False

    # Expected impact
    estimated_savings_percentage: float
    estimated_latency_improvement_ms: Optional[float] = None


class ResourceMetrics(BaseModel):
    """Current resource usage metrics."""

    timestamp: datetime = Field(default_factory=datetime.now)

    # Token usage
    total_tokens: int = 0
    input_tokens: int = 0
    output_tokens: int = 0

    # Cost
    total_cost_usd: float = 0.0
    cost_per_task: Dict[str, float] = {}

    # Performance
    avg_latency_ms: float = 0.0
    total_api_calls: int = 0

    # Efficiency
    cache_hit_rate: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0


class AgentResourceProfile(BaseModel):
    """Resource profile for a specific agent type."""

    agent_name: str
    model_preferences: Dict[TaskComplexity, str] = {}

    # Default budgets
    budgets: Dict[TaskComplexity, ResourceBudget] = {}

    # Historical performance
    avg_complexity: TaskComplexity = TaskComplexity.MODERATE
    success_rate: float = 1.0
    avg_cost_per_task_usd: float = 0.0


class DegradationAction(BaseModel):
    """Action to take when resources are constrained."""

    action_id: str
    action_type: str  # "downgrade_model", "use_cache", "skip_step", "abort"
    description: str

    # Conditions
    trigger_threshold: float  # e.g., 0.8 for 80% budget
    severity: str  # "low", "medium", "high"

    # Impact
    estimated_savings_percentage: float
    quality_impact: str  # "none", "minimal", "moderate", "significant"


class ResourceAlert(BaseModel):
    """Alert for resource threshold breach."""

    alert_id: str
    timestamp: datetime = Field(default_factory=datetime.now)

    alert_type: str  # "budget_warning", "budget_critical", "latency_high", "cost_spike"
    severity: str  # "info", "warning", "critical"

    # Details
    current_usage: float
    threshold: float
    percentage_used: float

    # Recommended action
    recommended_action: Optional[str] = None


__all__ = [
    "ModelSize",
    "TaskComplexity",
    "ResourceBudget",
    "ModelRecommendation",
    "OptimizationStrategy",
    "ResourceMetrics",
    "AgentResourceProfile",
    "DegradationAction",
    "ResourceAlert",
]
