"""Token-Centric Performance Testing & Inference Cost Optimization.

This module implements Issue #165: Monitoring and testing suite for ensuring
the system remains economically viable and efficient.

Core Components:
- Token Telemetry: Intercepts LLM calls to track tokens and latency
- Reasoning Loop Detection: Identifies zombie agents in infinite loops
- Cost Regression: Fails CI/CD if costs increase > 15%
- Optimization Recommendations: Suggests prompt truncations and caching
- Budget Management: Prevents runaway costs per issue/task
"""

from socialseed_e2e.telemetry.budget_manager import BudgetBreach, BudgetManager
from socialseed_e2e.telemetry.cost_regression import CostRegressionDetector
from socialseed_e2e.telemetry.loop_detector import ReasoningLoopDetector
from socialseed_e2e.telemetry.models import (
    CostBreakdown,
    CostEfficiencyReport,
    CostRegression,
    CostTier,
    LatencyMetrics,
    LLMCall,
    OptimizationRecommendation,
    ReasoningLoop,
    TestCaseMetrics,
    TokenBudget,
    TokenEventType,
    TokenMonitorConfig,
    TokenUsage,
)
from socialseed_e2e.telemetry.optimization_recommender import OptimizationRecommender
from socialseed_e2e.telemetry.report_generator import ReportGenerator
from socialseed_e2e.telemetry.telemetry_manager import (
    TelemetryManager,
    configure_telemetry,
    end_telemetry_session,
    get_telemetry_manager,
    start_telemetry_session,
    track_llm_call,
)
from socialseed_e2e.telemetry.token_monitor import TokenMonitor, TokenMonitorContext

__all__ = [
    # Models
    "CostBreakdown",
    "CostEfficiencyReport",
    "CostRegression",
    "CostTier",
    "LatencyMetrics",
    "LLMCall",
    "OptimizationRecommendation",
    "ReasoningLoop",
    "TestCaseMetrics",
    "TokenBudget",
    "TokenEventType",
    "TokenMonitorConfig",
    "TokenUsage",
    # Components
    "TokenMonitor",
    "TokenMonitorContext",
    "ReasoningLoopDetector",
    "CostRegressionDetector",
    "OptimizationRecommender",
    "BudgetManager",
    "BudgetBreach",
    "ReportGenerator",
    "TelemetryManager",
    # Convenience functions
    "get_telemetry_manager",
    "configure_telemetry",
    "track_llm_call",
    "start_telemetry_session",
    "end_telemetry_session",
]
