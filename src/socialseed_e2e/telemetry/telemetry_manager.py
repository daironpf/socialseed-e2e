"""Telemetry Manager.

Main orchestrator for token-centric performance testing and
cost optimization.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from socialseed_e2e.telemetry.budget_manager import BudgetManager, BudgetBreach
from socialseed_e2e.telemetry.cost_regression import CostRegressionDetector
from socialseed_e2e.telemetry.loop_detector import ReasoningLoopDetector
from socialseed_e2e.telemetry.models import (
    CostEfficiencyReport,
    LLMCall,
    TestCaseMetrics,
    TokenMonitorConfig,
)
from socialseed_e2e.telemetry.optimization_recommender import OptimizationRecommender
from socialseed_e2e.telemetry.report_generator import ReportGenerator
from socialseed_e2e.telemetry.token_monitor import TokenMonitor


class TelemetryManager:
    """Main manager for token telemetry and cost optimization."""

    def __init__(self, config: Optional[TokenMonitorConfig] = None):
        self.config = config or TokenMonitorConfig()

        # Initialize components
        self.token_monitor = TokenMonitor(self.config)
        self.loop_detector = ReasoningLoopDetector(
            max_reasoning_steps=self.config.max_reasoning_steps,
            max_reasoning_time_seconds=self.config.max_reasoning_time_seconds,
        )
        self.cost_regression_detector = CostRegressionDetector(
            baseline_file=self.config.baseline_file,
            threshold_percentage=self.config.regression_threshold_percentage,
            output_dir=self.config.report_output_dir,
        )
        self.budget_manager = BudgetManager()
        self.optimization_recommender = OptimizationRecommender()
        self.report_generator = ReportGenerator(self.config.report_output_dir)

        # Connect interceptors
        self._setup_interceptors()

    def _setup_interceptors(self):
        """Setup interceptors between components."""
        # Track calls for loop detection
        self.token_monitor.register_interceptor(self.loop_detector.track_call)

        # Track calls for budget checking
        self.token_monitor.register_interceptor(self._track_budget)

    def _track_budget(self, call: LLMCall):
        """Track call against budgets."""
        try:
            self.budget_manager.track_call(call)
        except BudgetBreach as e:
            # Log the breach but don't block (budget manager handles action)
            pass

    def start_session(self):
        """Start a telemetry session."""
        self.token_monitor.start_monitoring()
        self.loop_detector.reset()

    def end_session(self) -> CostEfficiencyReport:
        """End session and generate report."""
        self.token_monitor.stop_monitoring()

        # Generate report
        return self.generate_report()

    def generate_report(self) -> CostEfficiencyReport:
        """Generate cost efficiency report."""
        calls = self.token_monitor.calls

        # Build test case metrics
        test_cases = self._build_test_case_metrics(calls)

        # Detect cost regressions
        regressions = self.cost_regression_detector.detect_regression(test_cases)

        # Get reasoning loops
        loops = self.loop_detector.get_detected_loops()

        # Get budget breaches
        breaches = self._get_budget_breaches()

        # Generate optimization recommendations
        recommendations = self.optimization_recommender.analyze_and_recommend(
            calls, test_cases
        )

        # Generate report
        report = self.report_generator.generate_report(
            calls=calls,
            test_cases=test_cases,
            reasoning_loops=loops,
            cost_regressions=regressions,
            recommendations=recommendations,
            budget_breaches=breaches,
        )

        # Save report
        if self.config.generate_report_after_execution:
            self.report_generator.save_report(report)

        return report

    def _build_test_case_metrics(self, calls: List[LLMCall]) -> List[TestCaseMetrics]:
        """Build test case metrics from calls."""
        # Group calls by test case
        by_test: Dict[str, List[LLMCall]] = {}
        for call in calls:
            test_id = call.test_case_id or "unknown"
            if test_id not in by_test:
                by_test[test_id] = []
            by_test[test_id].append(call)

        test_cases = []
        for test_id, test_calls in by_test.items():
            metrics = TestCaseMetrics(
                test_case_id=test_id,
                test_name=test_id,
                total_input_tokens=sum(c.token_usage.input_tokens for c in test_calls),
                total_output_tokens=sum(
                    c.token_usage.output_tokens for c in test_calls
                ),
                total_tokens=sum(c.token_usage.total_tokens for c in test_calls),
                total_cost_usd=sum(c.cost.total_cost_usd for c in test_calls),
                avg_latency_ms=sum(c.latency.total_latency_ms for c in test_calls)
                / len(test_calls)
                if test_calls
                else 0,
                max_latency_ms=max(c.latency.total_latency_ms for c in test_calls)
                if test_calls
                else 0,
                min_latency_ms=min(c.latency.total_latency_ms for c in test_calls)
                if test_calls
                else 0,
                llm_calls_count=len(test_calls),
                cache_hits=sum(1 for c in test_calls if c.cache_hit),
                cache_misses=sum(1 for c in test_calls if not c.cache_hit),
                reasoning_loops_detected=sum(c.reasoning_steps for c in test_calls),
                executed_at=datetime.now(),
            )
            test_cases.append(metrics)

        return test_cases

    def _get_budget_breaches(self) -> List[Dict[str, Any]]:
        """Get all budget breaches."""
        breaches = []
        for budget_id, budget in self.budget_manager.budgets.items():
            if self.budget_manager._check_budget_breach(budget):
                breaches.append(
                    {
                        "budget_id": budget_id,
                        "budget_name": budget.name,
                        "scope": f"{budget.scope_type}:{budget.scope_id or 'all'}",
                        "current_cost": budget.current_cost_usd,
                        "max_cost": budget.max_cost_usd,
                        "current_tokens": budget.current_usage.total_tokens,
                        "max_tokens": budget.max_total_tokens,
                    }
                )
        return breaches

    def has_regression(self) -> bool:
        """Check if cost regression detected."""
        return self.cost_regression_detector.has_regression()

    def get_regression_summary(self) -> Dict:
        """Get regression summary for CI/CD."""
        return self.cost_regression_detector.get_regression_summary()

    def get_ci_message(self) -> str:
        """Get CI/CD message."""
        return self.cost_regression_detector.generate_ci_message()

    def save_baseline(self):
        """Save current metrics as baseline."""
        test_cases = self._build_test_case_metrics(self.token_monitor.calls)
        self.cost_regression_detector.save_baseline(test_cases)

    def get_summary(self) -> Dict[str, Any]:
        """Get quick summary of current session."""
        total_usage = self.token_monitor.get_total_usage()
        total_cost = self.token_monitor.get_total_cost()
        avg_latency = self.token_monitor.get_average_latency()

        return {
            "calls": len(self.token_monitor.calls),
            "input_tokens": total_usage.input_tokens,
            "output_tokens": total_usage.output_tokens,
            "total_tokens": total_usage.total_tokens,
            "total_cost_usd": total_cost,
            "avg_latency_ms": avg_latency,
            "reasoning_loops": len(self.loop_detector.get_detected_loops()),
            "cost_regressions": len(self.cost_regression_detector.detected_regressions),
        }

    def create_budget(self, name: str, scope_type: str, **kwargs) -> str:
        """Create a token budget."""
        budget = self.budget_manager.create_budget(
            name=name, scope_type=scope_type, **kwargs
        )
        return budget.budget_id

    def get_budget_status(self, budget_id: str) -> Optional[Dict]:
        """Get budget status."""
        return self.budget_manager.get_budget_status(budget_id)

    def reset(self):
        """Reset all telemetry data."""
        self.token_monitor.reset()
        self.loop_detector.reset()
        self.cost_regression_detector.detected_regressions = []


# Global instance for convenience
_global_telemetry_manager: Optional[TelemetryManager] = None


def get_telemetry_manager(
    config: Optional[TokenMonitorConfig] = None,
) -> TelemetryManager:
    """Get or create global telemetry manager."""
    global _global_telemetry_manager
    if _global_telemetry_manager is None:
        _global_telemetry_manager = TelemetryManager(config)
    return _global_telemetry_manager


def configure_telemetry(config: TokenMonitorConfig):
    """Configure global telemetry manager."""
    global _global_telemetry_manager
    _global_telemetry_manager = TelemetryManager(config)


# Convenience functions for tracking


def track_llm_call(**kwargs) -> Optional[LLMCall]:
    """Track an LLM call using global manager."""
    manager = get_telemetry_manager()
    return manager.token_monitor.intercept_llm_call(**kwargs)


def start_telemetry_session():
    """Start telemetry session using global manager."""
    manager = get_telemetry_manager()
    manager.start_session()


def end_telemetry_session() -> CostEfficiencyReport:
    """End telemetry session using global manager."""
    manager = get_telemetry_manager()
    return manager.end_session()
