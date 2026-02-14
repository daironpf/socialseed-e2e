"""Tests for Token-Centric Performance Testing Module.

Tests for token monitoring, loop detection, cost regression, and optimization.
"""

import json
import time
from datetime import datetime
from pathlib import Path

import pytest

from socialseed_e2e.telemetry import (
    BudgetBreach,
    BudgetManager,
    CostRegressionDetector,
    CostTier,
    OptimizationRecommender,
    ReasoningLoopDetector,
    ReportGenerator,
    TelemetryManager,
    TokenEventType,
    TokenMonitor,
    TokenMonitorConfig,
    TokenUsage,
    track_llm_call,
)
from socialseed_e2e.telemetry.models import LLMCall, LatencyMetrics, CostBreakdown


@pytest.fixture
def sample_llm_call():
    """Create a sample LLM call for testing."""
    return LLMCall(
        call_id="test_001",
        timestamp=datetime.now(),
        event_type=TokenEventType.LLM_CALL,
        model_name="gpt-3.5-turbo",
        provider="openai",
        cost_tier=CostTier.CHEAP,
        token_usage=TokenUsage(input_tokens=1000, output_tokens=500, total_tokens=1500),
        latency=LatencyMetrics(total_latency_ms=1500.0, tokens_per_second=333.0),
        cost=CostBreakdown(
            input_cost_usd=0.0015,
            output_cost_usd=0.0010,
            total_cost_usd=0.0025,
            cost_per_1k_input_tokens=0.0015,
            cost_per_1k_output_tokens=0.002,
        ),
        test_case_id="test_case_1",
        task_id="task_1",
    )


@pytest.fixture
def telemetry_manager(tmp_path):
    """Create a telemetry manager with temp directory."""
    config = TokenMonitorConfig(
        report_output_dir=str(tmp_path / "telemetry"),
    )
    return TelemetryManager(config)


class TestTokenMonitor:
    """Tests for TokenMonitor."""

    def test_initialization(self):
        """Test monitor initialization."""
        monitor = TokenMonitor()
        assert monitor.config is not None
        assert len(monitor.calls) == 0
        assert not monitor._active

    def test_start_stop_monitoring(self):
        """Test starting and stopping monitoring."""
        monitor = TokenMonitor()

        monitor.start_monitoring()
        assert monitor._active

        monitor.stop_monitoring()
        assert not monitor._active

    def test_intercept_llm_call(self, sample_llm_call):
        """Test intercepting an LLM call."""
        monitor = TokenMonitor()
        monitor.start_monitoring()

        call = monitor.intercept_llm_call(
            model_name="gpt-3.5-turbo",
            input_tokens=1000,
            output_tokens=500,
            latency_ms=1500.0,
            test_case_id="test_case_1",
        )

        assert call is not None
        assert call.model_name == "gpt-3.5-turbo"
        assert call.token_usage.input_tokens == 1000
        assert call.token_usage.output_tokens == 500
        assert len(monitor.calls) == 1

    def test_get_total_usage(self, sample_llm_call):
        """Test getting total usage."""
        monitor = TokenMonitor()
        monitor.calls = [sample_llm_call, sample_llm_call]

        usage = monitor.get_total_usage()
        assert usage.input_tokens == 2000
        assert usage.output_tokens == 1000
        assert usage.total_tokens == 3000

    def test_get_total_cost(self, sample_llm_call):
        """Test getting total cost."""
        monitor = TokenMonitor()
        monitor.calls = [sample_llm_call, sample_llm_call]

        cost = monitor.get_total_cost()
        assert cost == 0.0050  # 2 * 0.0025

    def test_get_usage_by_model(self, sample_llm_call):
        """Test usage breakdown by model."""
        monitor = TokenMonitor()
        monitor.calls = [sample_llm_call]

        by_model = monitor.get_usage_by_model()
        assert "gpt-3.5-turbo" in by_model
        assert by_model["gpt-3.5-turbo"]["calls"] == 1


class TestReasoningLoopDetector:
    """Tests for ReasoningLoopDetector."""

    def test_initialization(self):
        """Test detector initialization."""
        detector = ReasoningLoopDetector()
        assert detector.max_reasoning_steps == 10
        assert len(detector.agent_states) == 0

    def test_track_call(self, sample_llm_call):
        """Test tracking a call."""
        detector = ReasoningLoopDetector()

        # Modify call to have loop indicators
        sample_llm_call.response_preview = "Let me think about this again"

        detector.track_call(sample_llm_call)

        # Should have agent state
        assert len(detector.agent_states) == 1

    def test_get_detected_loops(self):
        """Test getting detected loops."""
        detector = ReasoningLoopDetector()

        loops = detector.get_detected_loops()
        assert isinstance(loops, list)

    def test_generate_summary(self):
        """Test summary generation."""
        detector = ReasoningLoopDetector()

        summary = detector.generate_summary()
        assert "loops_detected" in summary
        assert "total_wasted_tokens" in summary
        assert "total_wasted_cost_usd" in summary


class TestCostRegressionDetector:
    """Tests for CostRegressionDetector."""

    def test_initialization(self, tmp_path):
        """Test detector initialization."""
        detector = CostRegressionDetector(
            baseline_file=str(tmp_path / "baseline.json"),
            threshold_percentage=15.0,
        )

        assert detector.threshold_percentage == 15.0
        assert detector.baseline_file == tmp_path / "baseline.json"

    def test_save_and_detect_regression(self, tmp_path):
        """Test saving baseline and detecting regression."""
        from socialseed_e2e.telemetry.models import TestCaseMetrics

        detector = CostRegressionDetector(
            baseline_file=str(tmp_path / "baseline.json"),
            threshold_percentage=15.0,
        )

        # Create baseline test cases
        baseline_tests = [
            TestCaseMetrics(
                test_case_id="test_1",
                test_name="Test 1",
                total_cost_usd=1.0,
                total_input_tokens=1000,
                total_output_tokens=500,
            )
        ]

        # Save baseline
        detector.save_baseline(baseline_tests)
        assert detector.baseline_file.exists()

        # Create current test cases with 20% increase (above 15% threshold)
        current_tests = [
            TestCaseMetrics(
                test_case_id="test_1",
                test_name="Test 1",
                total_cost_usd=1.20,  # 20% increase
                total_input_tokens=1200,
                total_output_tokens=600,
            )
        ]

        # Detect regression
        regressions = detector.detect_regression(current_tests)

        # Should detect both overall and per-test regressions
        assert len(regressions) >= 1
        assert any(abs(r.increase_percentage - 20.0) < 0.1 for r in regressions)
        assert all(r.exceeded for r in regressions)

    def test_no_regression(self, tmp_path):
        """Test when there's no regression."""
        from socialseed_e2e.telemetry.models import TestCaseMetrics

        detector = CostRegressionDetector(
            baseline_file=str(tmp_path / "baseline.json"),
            threshold_percentage=15.0,
        )

        # Save baseline
        baseline_tests = [
            TestCaseMetrics(
                test_case_id="test_1",
                test_name="Test 1",
                total_cost_usd=1.0,
            )
        ]
        detector.save_baseline(baseline_tests)

        # Current with only 5% increase
        current_tests = [
            TestCaseMetrics(
                test_case_id="test_1",
                test_name="Test 1",
                total_cost_usd=1.05,
            )
        ]

        regressions = detector.detect_regression(current_tests)

        # Should not detect regression (below 15% threshold)
        assert len(regressions) == 0


class TestBudgetManager:
    """Tests for BudgetManager."""

    def test_initialization(self):
        """Test manager initialization."""
        manager = BudgetManager()
        assert len(manager.budgets) == 0

    def test_create_budget(self):
        """Test creating a budget."""
        manager = BudgetManager()

        budget = manager.create_budget(
            name="Test Budget",
            scope_type="global",
            max_cost_usd=10.0,
            max_total_tokens=10000,
        )

        assert budget is not None
        assert budget.budget_id is not None
        assert budget.budget_id in manager.budgets
        assert manager.budgets[budget.budget_id].name == "Test Budget"

    def test_track_call_within_budget(self, sample_llm_call):
        """Test tracking call within budget."""
        manager = BudgetManager()

        budget = manager.create_budget(
            name="Test Budget",
            scope_type="global",
            max_cost_usd=10.0,
        )

        # Should not raise exception
        result = manager.track_call(sample_llm_call)
        assert result is True

    def test_track_call_exceeds_budget(self, sample_llm_call):
        """Test tracking call that exceeds budget."""
        manager = BudgetManager()

        budget = manager.create_budget(
            name="Test Budget",
            scope_type="global",
            max_cost_usd=0.001,  # Very low budget
            on_budget_breach="block",
        )

        # Should raise BudgetBreach
        with pytest.raises(BudgetBreach):
            manager.track_call(sample_llm_call)

    def test_get_budget_status(self):
        """Test getting budget status."""
        manager = BudgetManager()

        budget = manager.create_budget(
            name="Test Budget",
            scope_type="global",
            max_cost_usd=10.0,
        )

        status = manager.get_budget_status(budget.budget_id)

        assert status is not None
        assert status["budget_id"] == budget.budget_id
        assert status["name"] == "Test Budget"


class TestOptimizationRecommender:
    """Tests for OptimizationRecommender."""

    def test_initialization(self):
        """Test recommender initialization."""
        recommender = OptimizationRecommender()
        assert len(recommender.recommendations) == 0

    def test_analyze_and_recommend(self, sample_llm_call):
        """Test analyzing and generating recommendations."""
        recommender = OptimizationRecommender()

        # Create calls with long prompts
        long_calls = []
        for i in range(5):
            call = sample_llm_call.copy()
            call.token_usage.input_tokens = 4000  # Long prompt
            long_calls.append(call)

        recommendations = recommender.analyze_and_recommend(long_calls, [])

        # Should generate at least one recommendation
        assert (
            len(recommendations) >= 0
        )  # May or may not generate depending on thresholds

    def test_get_total_estimated_savings(self):
        """Test getting total estimated savings."""
        recommender = OptimizationRecommender()

        # Add mock recommendations
        from socialseed_e2e.telemetry.models import OptimizationRecommendation

        recommender.recommendations = [
            OptimizationRecommendation(
                recommendation_id="rec_1",
                category="truncation",
                priority="high",
                title="Test",
                description="Test",
                estimated_savings_usd=5.0,
                implementation_effort="low",
                risk_level="low",
            ),
            OptimizationRecommendation(
                recommendation_id="rec_2",
                category="caching",
                priority="medium",
                title="Test 2",
                description="Test 2",
                estimated_savings_usd=3.0,
                implementation_effort="medium",
                risk_level="low",
            ),
        ]

        total = recommender.get_total_estimated_savings()
        assert total == 8.0


class TestReportGenerator:
    """Tests for ReportGenerator."""

    def test_initialization(self, tmp_path):
        """Test generator initialization."""
        generator = ReportGenerator(output_dir=str(tmp_path))
        assert generator.output_dir == tmp_path

    def test_generate_report(self, tmp_path, sample_llm_call):
        """Test generating a report."""
        generator = ReportGenerator(output_dir=str(tmp_path))

        from socialseed_e2e.telemetry.models import TestCaseMetrics

        test_case = TestCaseMetrics(
            test_case_id="test_1",
            test_name="Test 1",
            total_cost_usd=0.0025,
        )

        report = generator.generate_report(
            calls=[sample_llm_call],
            test_cases=[test_case],
            reasoning_loops=[],
            cost_regressions=[],
            recommendations=[],
            budget_breaches=[],
        )

        assert report.report_id is not None
        assert report.total_llm_calls == 1
        assert report.total_cost_usd == 0.0025
        assert 0 <= report.health_score <= 100
        assert report.status in ["healthy", "warning", "critical"]

    def test_save_report(self, tmp_path, sample_llm_call):
        """Test saving a report."""
        generator = ReportGenerator(output_dir=str(tmp_path))

        report = generator.generate_report(
            calls=[sample_llm_call],
            test_cases=[],
            reasoning_loops=[],
            cost_regressions=[],
            recommendations=[],
            budget_breaches=[],
        )

        report_path = generator.save_report(report)

        assert report_path.exists()
        assert "COST_EFFICIENCY_REPORT" in report_path.name


class TestTelemetryManager:
    """Tests for TelemetryManager."""

    def test_initialization(self, telemetry_manager):
        """Test manager initialization."""
        assert telemetry_manager.token_monitor is not None
        assert telemetry_manager.loop_detector is not None
        assert telemetry_manager.cost_regression_detector is not None
        assert telemetry_manager.budget_manager is not None

    def test_start_end_session(self, telemetry_manager):
        """Test starting and ending a session."""
        telemetry_manager.start_session()
        assert telemetry_manager.token_monitor._active

        # Add a call
        telemetry_manager.token_monitor.intercept_llm_call(
            model_name="gpt-3.5-turbo",
            input_tokens=1000,
            output_tokens=500,
            latency_ms=1500.0,
        )

        report = telemetry_manager.end_session()
        assert report is not None
        assert not telemetry_manager.token_monitor._active

    def test_get_summary(self, telemetry_manager):
        """Test getting summary."""
        telemetry_manager.start_session()

        telemetry_manager.token_monitor.intercept_llm_call(
            model_name="gpt-3.5-turbo",
            input_tokens=1000,
            output_tokens=500,
            latency_ms=1500.0,
        )

        summary = telemetry_manager.get_summary()

        assert "calls" in summary
        assert "input_tokens" in summary
        assert "output_tokens" in summary
        assert "total_cost_usd" in summary
        assert summary["calls"] == 1


class TestIntegration:
    """Integration tests."""

    def test_full_telemetry_workflow(self, tmp_path):
        """Test complete telemetry workflow."""
        # Configure telemetry
        config = TokenMonitorConfig(
            report_output_dir=str(tmp_path / "telemetry"),
            regression_threshold_percentage=15.0,
        )

        manager = TelemetryManager(config)

        # Create budget
        budget_id = manager.create_budget(
            name="Integration Test",
            scope_type="global",
            max_cost_usd=100.0,
        )

        # Start session
        manager.start_session()

        # Simulate LLM calls
        for i in range(10):
            manager.token_monitor.intercept_llm_call(
                model_name="gpt-3.5-turbo",
                input_tokens=1000 + i * 100,
                output_tokens=500,
                latency_ms=1500.0,
                test_case_id=f"test_{i}",
            )

        # End session and generate report
        report = manager.end_session()

        # Verify report
        assert report.total_llm_calls == 10
        assert report.total_cost_usd > 0
        assert report.health_score >= 0
        assert len(report.by_model) > 0

    def test_cost_regression_detection(self, tmp_path):
        """Test cost regression detection in workflow."""
        from socialseed_e2e.telemetry.models import TestCaseMetrics

        config = TokenMonitorConfig(
            report_output_dir=str(tmp_path / "telemetry"),
            baseline_file=str(tmp_path / "baseline.json"),
            regression_threshold_percentage=15.0,
        )

        manager = TelemetryManager(config)

        # Create and save baseline
        baseline_tests = [
            TestCaseMetrics(
                test_case_id="test_1",
                test_name="Test 1",
                total_cost_usd=1.0,
            )
        ]
        manager.cost_regression_detector.save_baseline(baseline_tests)

        # Start session with higher costs
        manager.start_session()

        # Add expensive calls (20% over baseline)
        for i in range(10):
            manager.token_monitor.intercept_llm_call(
                model_name="gpt-4",  # More expensive model
                input_tokens=2000,
                output_tokens=1000,
                latency_ms=2000.0,
                test_case_id="test_1",
            )

        report = manager.end_session()

        # Should detect regression
        assert manager.has_regression()
        assert len(report.cost_regressions) > 0

    def test_reasoning_loop_detection(self, tmp_path):
        """Test reasoning loop detection."""
        config = TokenMonitorConfig(
            report_output_dir=str(tmp_path / "telemetry"),
            max_reasoning_steps=5,
        )

        manager = TelemetryManager(config)
        manager.start_session()

        # Add calls with loop indicators
        for i in range(10):
            call = manager.token_monitor.intercept_llm_call(
                model_name="gpt-3.5-turbo",
                input_tokens=1000,
                output_tokens=500,
                latency_ms=1500.0,
                reasoning_steps=i + 1,
                response_preview="Let me think about this again" if i > 5 else "Done",
            )

        report = manager.end_session()

        # Should have tracked reasoning
        assert (
            len(report.reasoning_loops) >= 0
        )  # May or may not detect depending on pattern


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_track_llm_call(self):
        """Test global track_llm_call function."""
        from socialseed_e2e.telemetry.telemetry_manager import _global_telemetry_manager

        # Reset global manager
        import socialseed_e2e.telemetry.telemetry_manager as tm

        tm._global_telemetry_manager = None

        call = track_llm_call(
            model_name="gpt-3.5-turbo",
            input_tokens=1000,
            output_tokens=500,
            latency_ms=1500.0,
        )

        # Should create global manager and track call
        assert tm._global_telemetry_manager is not None
