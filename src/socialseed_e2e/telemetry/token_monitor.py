"""Token Monitor - Intercepts and tracks LLM calls.

Main component for monitoring token usage, latency, and costs across all LLM calls.
"""

import time
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from socialseed_e2e.telemetry.models import (
    CostBreakdown,
    CostTier,
    LatencyMetrics,
    LLMCall,
    TokenEventType,
    TokenMonitorConfig,
    TokenUsage,
)


class TokenMonitor:
    """Monitors and tracks all LLM token usage and costs."""

    # Default cost per 1K tokens for common models
    DEFAULT_MODEL_COSTS = {
        "gpt-4": {"input": 0.03, "output": 0.06, "tier": CostTier.PREMIUM},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03, "tier": CostTier.STANDARD},
        "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002, "tier": CostTier.CHEAP},
        "claude-3-opus": {"input": 0.015, "output": 0.075, "tier": CostTier.PREMIUM},
        "claude-3-sonnet": {"input": 0.003, "output": 0.015, "tier": CostTier.STANDARD},
        "claude-3-haiku": {"input": 0.00025, "output": 0.00125, "tier": CostTier.CHEAP},
    }

    def __init__(self, config: Optional[TokenMonitorConfig] = None):
        self.config = config or TokenMonitorConfig()
        self.calls: List[LLMCall] = []
        self._interceptors: List[Callable] = []
        self._active = False

        # Merge custom model costs
        if self.config.model_costs:
            for model, costs in self.config.model_costs.items():
                self.DEFAULT_MODEL_COSTS[model] = {
                    "input": costs.get("input", 0.01),
                    "output": costs.get("output", 0.03),
                    "tier": costs.get("tier", CostTier.STANDARD),
                }

    def start_monitoring(self):
        """Start monitoring LLM calls."""
        self._active = True
        self.calls = []

    def stop_monitoring(self):
        """Stop monitoring LLM calls."""
        self._active = False

    def intercept_llm_call(
        self,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: float,
        provider: str = "openai",
        test_case_id: Optional[str] = None,
        task_id: Optional[str] = None,
        issue_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        operation_type: Optional[str] = None,
        cache_hit: bool = False,
        reasoning_steps: int = 0,
        tool_calls_count: int = 0,
        prompt_preview: Optional[str] = None,
        response_preview: Optional[str] = None,
    ) -> LLMCall:
        """Intercept and record an LLM call."""
        if not self._active or not self.config.enabled:
            return None

        call_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now()

        # Get model cost info
        model_info = self.DEFAULT_MODEL_COSTS.get(
            model_name.lower(),
            {
                "input": self.config.default_input_cost_per_1k,
                "output": self.config.default_output_cost_per_1k,
                "tier": CostTier.STANDARD,
            },
        )

        # Calculate token usage
        token_usage = TokenUsage.from_counts(input_tokens, output_tokens)

        # Calculate latency metrics
        latency = LatencyMetrics(
            total_latency_ms=latency_ms,
            tokens_per_second=(output_tokens / (latency_ms / 1000))
            if latency_ms > 0
            else None,
        )

        # Calculate cost
        input_cost = (input_tokens / 1000) * model_info["input"]
        output_cost = (output_tokens / 1000) * model_info["output"]
        cost = CostBreakdown(
            input_cost_usd=input_cost,
            output_cost_usd=output_cost,
            total_cost_usd=input_cost + output_cost,
            cost_per_1k_input_tokens=model_info["input"],
            cost_per_1k_output_tokens=model_info["output"],
        )

        # Create LLM call record
        llm_call = LLMCall(
            call_id=call_id,
            timestamp=timestamp,
            event_type=TokenEventType.LLM_CALL,
            model_name=model_name,
            provider=provider,
            cost_tier=model_info["tier"],
            token_usage=token_usage,
            latency=latency,
            cost=cost,
            test_case_id=test_case_id,
            task_id=task_id,
            issue_id=issue_id,
            agent_name=agent_name,
            operation_type=operation_type,
            cache_hit=cache_hit,
            reasoning_steps=reasoning_steps,
            tool_calls_count=tool_calls_count,
            prompt_preview=prompt_preview[:200]
            if prompt_preview and self.config.track_prompts
            else None,
            response_preview=response_preview[:200]
            if response_preview and self.config.track_responses
            else None,
        )

        self.calls.append(llm_call)

        # Notify interceptors
        for interceptor in self._interceptors:
            try:
                interceptor(llm_call)
            except Exception:
                pass

        return llm_call

    def register_interceptor(self, callback: Callable[[LLMCall], None]):
        """Register a callback to be called on each LLM call."""
        self._interceptors.append(callback)

    def unregister_interceptor(self, callback: Callable[[LLMCall], None]):
        """Unregister a callback."""
        if callback in self._interceptors:
            self._interceptors.remove(callback)

    def get_total_usage(self) -> TokenUsage:
        """Get total token usage across all calls."""
        total_input = sum(c.token_usage.input_tokens for c in self.calls)
        total_output = sum(c.token_usage.output_tokens for c in self.calls)
        return TokenUsage.from_counts(total_input, total_output)

    def get_total_cost(self) -> float:
        """Get total cost across all calls."""
        return sum(c.cost.total_cost_usd for c in self.calls)

    def get_average_latency(self) -> float:
        """Get average latency across all calls."""
        if not self.calls:
            return 0.0
        return sum(c.latency.total_latency_ms for c in self.calls) / len(self.calls)

    def get_usage_by_model(self) -> Dict[str, Dict[str, Any]]:
        """Get usage breakdown by model."""
        by_model: Dict[str, Dict[str, Any]] = {}

        for call in self.calls:
            model = call.model_name
            if model not in by_model:
                by_model[model] = {
                    "calls": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "cost_usd": 0.0,
                    "avg_latency_ms": 0.0,
                }

            by_model[model]["calls"] += 1
            by_model[model]["input_tokens"] += call.token_usage.input_tokens
            by_model[model]["output_tokens"] += call.token_usage.output_tokens
            by_model[model]["total_tokens"] += call.token_usage.total_tokens
            by_model[model]["cost_usd"] += call.cost.total_cost_usd

        # Calculate averages
        for model in by_model:
            calls = by_model[model]["calls"]
            model_calls = [c for c in self.calls if c.model_name == model]
            by_model[model]["avg_latency_ms"] = (
                sum(c.latency.total_latency_ms for c in model_calls) / calls
                if calls > 0
                else 0.0
            )

        return by_model

    def get_usage_by_test_case(self) -> Dict[str, Dict[str, Any]]:
        """Get usage breakdown by test case."""
        by_test: Dict[str, Dict[str, Any]] = {}

        for call in self.calls:
            test_id = call.test_case_id or "unknown"
            if test_id not in by_test:
                by_test[test_id] = {
                    "calls": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "cost_usd": 0.0,
                }

            by_test[test_id]["calls"] += 1
            by_test[test_id]["input_tokens"] += call.token_usage.input_tokens
            by_test[test_id]["output_tokens"] += call.token_usage.output_tokens
            by_test[test_id]["total_tokens"] += call.token_usage.total_tokens
            by_test[test_id]["cost_usd"] += call.cost.total_cost_usd

        return by_test

    def reset(self):
        """Reset all tracked calls."""
        self.calls = []

    def export_calls(self) -> List[Dict[str, Any]]:
        """Export all calls as dictionaries."""
        return [call.model_dump() for call in self.calls]


class TokenMonitorContext:
    """Context manager for monitoring a block of code."""

    def __init__(self, monitor: TokenMonitor, test_case_id: Optional[str] = None):
        self.monitor = monitor
        self.test_case_id = test_case_id
        self.start_time: Optional[float] = None

    def __enter__(self):
        self.monitor.start_monitoring()
        self.start_time = time.time()
        return self.monitor

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.monitor.stop_monitoring()
        elapsed = time.time() - self.start_time if self.start_time else 0
        return False
