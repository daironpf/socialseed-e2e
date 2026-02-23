"""
Resource Optimization Agent (FinOps) for socialseed-e2e.

This agent monitors and optimizes LLM resource consumption across all AI agents.
Features:
- Token usage tracking and budgeting
- Model selection based on task complexity
- Graceful degradation to smaller models for simple tasks
- Cost and latency optimization
- Integration with telemetry system
"""

import uuid
from typing import Any, Dict, List, Optional

from socialseed_e2e.agents.resource_optimizer.models import (
    DegradationAction,
    ModelRecommendation,
    ModelSize,
    OptimizationStrategy,
    ResourceAlert,
    ResourceBudget,
    ResourceMetrics,
    TaskComplexity,
)


class ModelSelector:
    """
    Selects optimal LLM model based on task complexity and budget.
    """

    MODEL_CATALOG = {
        "gpt-4o": {
            "provider": "OpenAI",
            "size": ModelSize.LARGE,
            "cost_per_1k_input": 0.0025,
            "cost_per_1k_output": 0.01,
            "latency_ms": 2000,
            "capabilities": ["reasoning", "coding", "analysis"],
        },
        "gpt-4o-mini": {
            "provider": "OpenAI",
            "size": ModelSize.SMALL,
            "cost_per_1k_input": 0.00015,
            "cost_per_1k_output": 0.0006,
            "latency_ms": 500,
            "capabilities": ["fast", "simple_reasoning"],
        },
        "claude-opus": {
            "provider": "Anthropic",
            "size": ModelSize.LARGE,
            "cost_per_1k_input": 0.015,
            "cost_per_1k_output": 0.075,
            "latency_ms": 3000,
            "capabilities": ["reasoning", "writing", "analysis"],
        },
        "claude-sonnet": {
            "provider": "Anthropic",
            "size": ModelSize.MEDIUM,
            "cost_per_1k_input": 0.003,
            "cost_per_1k_output": 0.015,
            "latency_ms": 1000,
            "capabilities": ["balanced"],
        },
        "claude-haiku": {
            "provider": "Anthropic",
            "size": ModelSize.SMALL,
            "cost_per_1k_input": 0.00025,
            "cost_per_1k_output": 0.00125,
            "latency_ms": 500,
            "capabilities": ["fast", "simple_reasoning"],
        },
        "o1": {
            "provider": "OpenAI",
            "size": ModelSize.REASONING,
            "cost_per_1k_input": 0.015,
            "cost_per_1k_output": 0.06,
            "latency_ms": 10000,
            "capabilities": ["advanced_reasoning", "complex_analysis"],
        },
        "o3-mini": {
            "provider": "OpenAI",
            "size": ModelSize.REASONING,
            "cost_per_1k_input": 0.0011,
            "cost_per_1k_output": 0.0044,
            "latency_ms": 4000,
            "capabilities": ["reasoning", "coding"],
        },
    }

    def __init__(self):
        self.strategies = self._build_strategies()

    def _build_strategies(self) -> Dict[TaskComplexity, OptimizationStrategy]:
        """Build optimization strategies for each complexity level."""
        return {
            TaskComplexity.SIMPLE: OptimizationStrategy(
                strategy_id=str(uuid.uuid4()),
                name="Simple Task Strategy",
                description="Use smallest/fastest model for simple tasks",
                task_complexity=TaskComplexity.SIMPLE,
                recommended_model="gpt-4o-mini",
                estimated_savings_percentage=90,
                estimated_latency_improvement_ms=1500,
            ),
            TaskComplexity.MODERATE: OptimizationStrategy(
                strategy_id=str(uuid.uuid4()),
                name="Moderate Task Strategy",
                description="Use medium model for standard tasks",
                task_complexity=TaskComplexity.MODERATE,
                recommended_model="claude-sonnet",
                estimated_savings_percentage=60,
                estimated_latency_improvement_ms=500,
            ),
            TaskComplexity.COMPLEX: OptimizationStrategy(
                strategy_id=str(uuid.uuid4()),
                name="Complex Task Strategy",
                description="Use large model for complex tasks",
                task_complexity=TaskComplexity.COMPLEX,
                recommended_model="gpt-4o",
                estimated_savings_percentage=0,
            ),
            TaskComplexity.ADVANCED: OptimizationStrategy(
                strategy_id=str(uuid.uuid4()),
                name="Advanced Task Strategy",
                description="Use reasoning model for advanced tasks",
                task_complexity=TaskComplexity.ADVANCED,
                recommended_model="o1",
                estimated_savings_percentage=0,
            ),
        }

    def select_model(
        self,
        complexity: TaskComplexity,
        budget: Optional[ResourceBudget] = None,
    ) -> ModelRecommendation:
        """Select optimal model based on complexity and budget."""
        strategy = self.strategies[complexity]
        model_key = strategy.recommended_model or "gpt-4o-mini"
        model_info = self.MODEL_CATALOG.get(model_key)

        if not model_info:
            model_info = self.MODEL_CATALOG["gpt-4o-mini"]

        cost_per_1k = model_info["cost_per_1k_input"] + model_info["cost_per_1k_output"]
        estimated_cost = (cost_per_1k * 1) / 1000

        if budget and budget.max_cost_per_task_usd:
            if estimated_cost > budget.max_cost_per_task_usd:
                return self.select_model(TaskComplexity.SIMPLE, budget)

        return ModelRecommendation(
            model_name=model_key,
            provider=model_info["provider"],
            model_size=model_info["size"],
            estimated_cost_usd=estimated_cost,
            estimated_latency_ms=model_info["latency_ms"],
            confidence=0.9,
            reasoning=f"Selected {strategy.recommended_model} for {complexity.value} task",
        )

    def get_all_models(self) -> Dict[str, Dict[str, Any]]:
        """Get catalog of all available models."""
        return self.MODEL_CATALOG


class ResourceAgent:
    """
    Main Resource Optimization Agent (FinOps).

    Monitors and controls LLM resource consumption across all AI agents.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.model_selector = ModelSelector()
        self.metrics = ResourceMetrics()
        self.alerts: List[ResourceAlert] = []
        self.budgets: Dict[str, ResourceBudget] = {}

        self.degradation_actions = self._build_degradation_actions()

    def _build_degradation_actions(self) -> List[DegradationAction]:
        """Build graceful degradation actions."""
        return [
            DegradationAction(
                action_id="downgrade_to_small",
                action_type="downgrade_model",
                description="Downgrade from large to small model",
                trigger_threshold=0.8,
                severity="medium",
                estimated_savings_percentage=90,
                quality_impact="minimal",
            ),
            DegradationAction(
                action_id="use_cache",
                action_type="use_cache",
                description="Use cached responses when available",
                trigger_threshold=0.6,
                severity="low",
                estimated_savings_percentage=30,
                quality_impact="none",
            ),
            DegradationAction(
                action_id="skip_reasoning",
                action_type="skip_step",
                description="Skip reasoning steps for simple tasks",
                trigger_threshold=0.7,
                severity="low",
                estimated_savings_percentage=20,
                quality_impact="minimal",
            ),
            DegradationAction(
                action_id="abort_task",
                action_type="abort",
                description="Abort task if budget exceeded",
                trigger_threshold=0.95,
                severity="high",
                estimated_savings_percentage=100,
                quality_impact="significant",
            ),
        ]

    def set_budget(self, task_id: str, budget: ResourceBudget) -> None:
        """Set budget for a specific task."""
        self.budgets[task_id] = budget

    def get_budget(self, task_id: str) -> Optional[ResourceBudget]:
        """Get budget for a specific task."""
        return self.budgets.get(task_id)

    def track_usage(
        self,
        task_id: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        latency_ms: float,
    ) -> None:
        """Track resource usage for a task."""
        self.metrics.total_tokens += input_tokens + output_tokens
        self.metrics.input_tokens += input_tokens
        self.metrics.output_tokens += output_tokens
        self.metrics.total_cost_usd += cost_usd
        self.metrics.total_api_calls += 1
        self.metrics.avg_latency_ms = (
            self.metrics.avg_latency_ms * (self.metrics.total_api_calls - 1)
            + latency_ms
        ) / self.metrics.total_api_calls

        if task_id not in self.metrics.cost_per_task:
            self.metrics.cost_per_task[task_id] = 0
        self.metrics.cost_per_task[task_id] += cost_usd

    def check_budget(self, task_id: str) -> List[ResourceAlert]:
        """Check if task is within budget and generate alerts."""
        alerts = []
        budget = self.budgets.get(task_id)

        if not budget:
            return alerts

        cost = self.metrics.cost_per_task.get(task_id, 0)

        if budget.max_cost_per_task_usd:
            percentage = cost / budget.max_cost_per_task_usd
            if percentage >= 1.0:
                alerts.append(
                    ResourceAlert(
                        alert_id=str(uuid.uuid4()),
                        alert_type="budget_critical",
                        severity="critical",
                        current_usage=cost,
                        threshold=budget.max_cost_per_task_usd,
                        percentage_used=percentage * 100,
                        recommended_action="abort_task",
                    )
                )
            elif percentage >= 0.8:
                alerts.append(
                    ResourceAlert(
                        alert_id=str(uuid.uuid4()),
                        alert_type="budget_warning",
                        severity="warning",
                        current_usage=cost,
                        threshold=budget.max_cost_per_task_usd,
                        percentage_used=percentage * 100,
                        recommended_action="downgrade_to_small",
                    )
                )

        self.alerts.extend(alerts)
        return alerts

    def recommend_degradation(self, task_id: str) -> Optional[DegradationAction]:
        """Recommend degradation action based on current usage."""
        budget = self.budgets.get(task_id)
        if not budget:
            return None

        cost = self.metrics.cost_per_task.get(task_id, 0)
        percentage = cost / (budget.max_cost_per_task_usd or 1)

        for action in self.degradation_actions:
            if percentage >= action.trigger_threshold:
                return action

        return None

    def optimize_task(
        self,
        task_id: str,
        task_description: str,
        complexity: TaskComplexity,
    ) -> ModelRecommendation:
        """Get optimized model recommendation for a task."""
        budget = self.budgets.get(task_id)
        return self.model_selector.select_model(complexity, budget)

    def get_optimization_report(self) -> Dict[str, Any]:
        """Generate optimization report."""
        return {
            "total_tokens": self.metrics.total_tokens,
            "total_cost_usd": self.metrics.total_cost_usd,
            "avg_latency_ms": self.metrics.avg_latency_ms,
            "total_api_calls": self.metrics.total_api_calls,
            "cache_hit_rate": self.metrics.cache_hit_rate,
            "alerts": [a.model_dump() for a in self.alerts],
            "active_budgets": len(self.budgets),
        }

    def reset_metrics(self) -> None:
        """Reset all metrics."""
        self.metrics = ResourceMetrics()
        self.alerts = []


class SmartModelRouter:
    """
    Routes tasks to appropriate models based on complexity analysis.
    """

    def __init__(self, resource_agent: ResourceAgent):
        self.resource_agent = resource_agent

    def route(
        self,
        task_description: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> ModelRecommendation:
        """Route task to optimal model."""
        complexity = self._analyze_complexity(task_description, context)

        task_id = (
            context.get("task_id", str(uuid.uuid4())) if context else str(uuid.uuid4())
        )

        return self.resource_agent.optimize_task(task_id, task_description, complexity)

    def _analyze_complexity(
        self,
        task_description: str,
        context: Optional[Dict[str, Any]],
    ) -> TaskComplexity:
        """Analyze task complexity based on description and context."""
        desc_lower = task_description.lower()

        simple_keywords = ["fix", "repair", "locator", "simple", "basic"]
        moderate_keywords = ["generate", "create", "test", "validate"]
        complex_keywords = ["analyze", "strategy", "complex", "design"]
        advanced_keywords = ["reasoning", "advanced", "semantic", "planning"]

        if any(kw in desc_lower for kw in advanced_keywords):
            return TaskComplexity.ADVANCED
        elif any(kw in desc_lower for kw in complex_keywords):
            return TaskComplexity.COMPLEX
        elif any(kw in desc_lower for kw in moderate_keywords):
            return TaskComplexity.MODERATE

        return TaskComplexity.SIMPLE


__all__ = [
    "ResourceAgent",
    "ModelSelector",
    "SmartModelRouter",
]
