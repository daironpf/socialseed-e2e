"""
Resource Optimization Agent (FinOps) Module.

This module provides resource optimization capabilities for AI agents:
- Token usage tracking and budgeting
- Model selection based on task complexity
- Graceful degradation to smaller models
- Cost and latency optimization
- Integration with telemetry system

Usage:
    >>> from socialseed_e2e.agents.resource_optimizer import ResourceAgent, SmartModelRouter
    >>>
    >>> # Initialize agent
    >>> agent = ResourceAgent()
    >>> agent.set_budget("task_123", ResourceBudget(max_cost_per_task_usd=0.50))
    >>>
    >>> # Route task to optimal model
    >>> router = SmartModelRouter(agent)
    >>> recommendation = router.route("fix CSS locator", {"task_id": "task_123"})
    >>> print(f"Use model: {recommendation.model_name}")
    >>>
    >>> # Track usage
    >>> agent.track_usage("task_123", 1000, 500, 0.025, 1500)
    >>> alerts = agent.check_budget("task_123")
"""

from socialseed_e2e.agents.resource_optimizer.models import (
    AgentResourceProfile,
    DegradationAction,
    ModelRecommendation,
    ModelSize,
    OptimizationStrategy,
    ResourceAlert,
    ResourceBudget,
    ResourceMetrics,
    TaskComplexity,
)
from socialseed_e2e.agents.resource_optimizer.resource_agent import (
    ModelSelector,
    ResourceAgent,
    SmartModelRouter,
)

__all__ = [
    # Models
    "ModelSize",
    "TaskComplexity",
    "ResourceBudget",
    "ModelRecommendation",
    "OptimizationStrategy",
    "ResourceMetrics",
    "AgentResourceProfile",
    "DegradationAction",
    "ResourceAlert",
    # Agents
    "ResourceAgent",
    "ModelSelector",
    "SmartModelRouter",
]
