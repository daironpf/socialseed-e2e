import pytest
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch

from socialseed_e2e.ai_learning.feedback_collector import (
    FeedbackCollector,
    TestFeedback,
    FeedbackType,
)
from socialseed_e2e.ai_learning.model_trainer import (
    ModelTrainer,
    TrainingData,
    LearningMetrics,
)
from socialseed_e2e.ai_learning.adaptation_engine import (
    AdaptationEngine,
    AdaptationStrategy,
    CodebaseChange,
)
from socialseed_e2e.core.test_runner import (
    get_feedback_collector,
    set_feedback_collector,
    execute_single_test,
    TestResult,
)


class TestFeedbackCollector:
    """Tests for feedback collection."""

    @pytest.fixture
    def temp_storage(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def collector(self, temp_storage):
        return FeedbackCollector(temp_storage)

    def test_collect_test_result_success(self, collector):
        collector.collect_test_result(
            test_name="test_login", success=True, execution_time=1.5
        )

        recent = collector.get_recent_feedback(limit=1)
        assert len(recent) == 1
        assert recent[0].test_name == "test_login"
        assert recent[0].feedback_type == FeedbackType.TEST_SUCCESS
        assert recent[0].execution_time == 1.5

    def test_collect_test_result_failure(self, collector):
        collector.collect_test_result(
            test_name="test_checkout",
            success=False,
            execution_time=2.0,
            error_message="AssertionError: Expected 200, got 500",
        )

        failures = collector.get_feedback_by_type(FeedbackType.TEST_FAILURE)
        assert len(failures) == 1
        assert failures[0].error_message == "AssertionError: Expected 200, got 500"

    def test_collect_user_correction(self, collector):
        collector.collect_user_correction(
            test_name="test_api",
            original_assertion="assert response.status == 200",
            corrected_assertion="assert response.status_code == 200",
            user_comment="Fixed typo in assertion",
        )

        corrections = collector.get_feedback_by_type(FeedbackType.USER_CORRECTION)
        assert len(corrections) == 1
        assert (
            corrections[0].corrected_assertion == "assert response.status_code == 200"
        )

    def test_analyze_patterns(self, collector):
        # Add some feedback
        collector.collect_test_result("test_1", True, 1.0)
        collector.collect_test_result("test_2", False, 2.0, error_message="Error A")
        collector.collect_test_result("test_3", True, 1.5)
        collector.collect_user_correction("test_2", "old", "new")

        patterns = collector.analyze_patterns()

        assert patterns["total"] == 4
        assert patterns["success_rate"] == 2 / 3  # 2 successes out of 3 test results
        assert patterns["user_corrections"] == 1
        assert len(patterns["top_errors"]) > 0

    def test_persistence(self, collector, temp_storage):
        # Collect feedback
        collector.collect_test_result("test_persist", True, 1.0)

        # Create new collector with same storage
        new_collector = FeedbackCollector(temp_storage)
        loaded = new_collector.load_all_feedback()

        assert len(loaded) == 1
        assert loaded[0].test_name == "test_persist"


class TestModelTrainer:
    """Tests for model training."""

    @pytest.fixture
    def trainer(self):
        return ModelTrainer()

    def test_train_from_corrections(self, trainer):
        training_data = TrainingData(
            inputs=["assert x == 1", "assert y == 2"],
            outputs=["assert x == 1.0", "assert y == 2.0"],
            contexts=["Type mismatch", "Type mismatch"],
        )

        metrics = trainer.train_from_corrections(training_data)

        assert metrics.training_samples == 2
        assert metrics.accuracy > 0
        assert len(trainer.training_history) == 1

    def test_predict_correction(self, trainer):
        # Train
        training_data = TrainingData(
            inputs=["assert status == 200"], outputs=["assert status_code == 200"]
        )
        trainer.train_from_corrections(training_data)

        # Predict
        prediction = trainer.predict_correction("assert status == 200")
        assert prediction == "assert status_code == 200"

    def test_optimize_test_order(self, trainer):
        tests = ["slow_test", "fast_test", "medium_test"]
        execution_history = {"slow_test": 10.0, "fast_test": 1.0, "medium_test": 5.0}

        optimized = trainer.optimize_test_order(tests, execution_history)

        # Should be ordered by execution time (fastest first)
        assert optimized == ["fast_test", "medium_test", "slow_test"]

    def test_suggest_improvements(self, trainer):
        suggestions = trainer.suggest_test_improvements("flaky_test", failure_count=6)

        assert len(suggestions) > 0
        assert any("error handling" in s.lower() for s in suggestions)

    def test_learning_progress(self, trainer):
        # Initially empty
        progress = trainer.get_learning_progress()
        assert progress["total_training_sessions"] == 0

        # After training
        training_data = TrainingData(inputs=["a"], outputs=["b"])
        trainer.train_from_corrections(training_data)

        progress = trainer.get_learning_progress()
        assert progress["total_training_sessions"] == 1
        assert progress["total_samples"] == 1


class TestAdaptationEngine:
    """Tests for adaptation engine."""

    @pytest.fixture
    def engine(self):
        return AdaptationEngine(strategy=AdaptationStrategy.BALANCED)

    def test_adapt_test_generation(self, engine):
        test_template = "assert status == 200"
        learned_patterns = {"assert status": ["assert status_code"]}
        confidence_scores = {"assert status": 0.9}

        adapted = engine.adapt_test_generation(
            test_template, learned_patterns, confidence_scores
        )

        assert "status_code" in adapted

    def test_detect_codebase_changes(self, engine):
        file_changes = [
            {"path": "api/users.py", "type": "modified"},
            {"path": "api/auth.py", "type": "added"},
        ]
        test_mapping = {
            "api/users.py": ["test_get_user", "test_create_user"],
            "api/auth.py": ["test_login"],
        }

        changes = engine.detect_codebase_changes(file_changes, test_mapping)

        assert len(changes) == 2
        assert len(changes[0].affected_tests) == 2
        assert len(changes[1].affected_tests) == 1

    def test_prioritize_test_execution(self, engine):
        all_tests = ["test_a", "test_b", "test_c"]
        recent_failures = ["test_b"]

        prioritized = engine.prioritize_test_execution(all_tests, recent_failures)

        # test_b should be first (recent failure)
        assert prioritized[0] == "test_b"

    def test_adapt_to_api_changes(self, engine):
        old_schema = {"id": "int", "name": "str"}
        new_schema = {"id": "int", "name": "str", "email": "str"}

        recommendations = engine.adapt_to_api_changes(
            "/api/users", old_schema, new_schema
        )

        assert len(recommendations["changes"]) > 0
        assert any(c["field"] == "email" for c in recommendations["changes"])

    def test_strategy_change(self, engine):
        assert engine.strategy == AdaptationStrategy.BALANCED

        engine.set_strategy(AdaptationStrategy.AGGRESSIVE)
        assert engine.strategy == AdaptationStrategy.AGGRESSIVE

    def test_suggest_test_updates(self, engine):
        failure_patterns = ["timeout_error"]
        learned_corrections = {"timeout_error": "# Add retry with backoff"}

        suggestions = engine.suggest_test_updates(
            "test_api", failure_patterns, learned_corrections
        )

        assert len(suggestions) > 0
        assert any(s["type"] == "correction" for s in suggestions)


class TestFeedbackCollectorIntegration:
    """Tests for integration with test runner."""

    def test_global_feedback_collector(self):
        """Test that global feedback collector can be set and retrieved."""
        # Reset to None first
        set_feedback_collector(None)

        # Get default collector
        collector1 = get_feedback_collector()
        assert isinstance(collector1, FeedbackCollector)

        # Get again should return same instance
        collector2 = get_feedback_collector()
        assert collector1 is collector2

        # Set custom collector
        custom_collector = FeedbackCollector()
        set_feedback_collector(custom_collector)

        # Should return custom collector
        collector3 = get_feedback_collector()
        assert collector3 is custom_collector

    def test_feedback_collected_on_test_execution(self, tmp_path):
        """Test that feedback is collected when tests are executed."""
        # Create mock collector
        mock_collector = Mock(spec=FeedbackCollector)
        mock_collector.collect_test_result = Mock()
        set_feedback_collector(mock_collector)

        # Create a simple test module
        test_module = tmp_path / "test_module.py"
        test_module.write_text("""
def run(page):
    pass
""")

        # Create mock page
        mock_page = Mock()
        mock_page.base_url = "http://localhost:8080"

        # Execute test (this should trigger feedback collection)
        with patch("socialseed_e2e.core.test_runner.load_test_module") as mock_load:
            mock_load.return_value = lambda page: None
            result = execute_single_test(test_module, mock_page, "test_service")

        # Verify feedback was collected
        assert mock_collector.collect_test_result.called
        call_args = mock_collector.collect_test_result.call_args
        assert call_args[1]["test_name"] == "test_module"
        assert call_args[1]["success"] is True
        assert call_args[1]["endpoint"] == "http://localhost:8080"
        assert call_args[1]["metadata"]["service"] == "test_service"

    def test_feedback_collected_on_test_failure(self, tmp_path):
        """Test that feedback is collected when tests fail."""
        # Create mock collector
        mock_collector = Mock(spec=FeedbackCollector)
        mock_collector.collect_test_result = Mock()
        set_feedback_collector(mock_collector)

        # Create a test module that fails
        test_module = tmp_path / "test_fail_module.py"
        test_module.write_text("""
def run(page):
    assert False, "Test failed"
""")

        # Create mock page
        mock_page = Mock()
        mock_page.base_url = "http://localhost:8080"

        # Execute test (this should trigger feedback collection for failure)
        with patch("socialseed_e2e.core.test_runner.load_test_module") as mock_load:

            def failing_test(page):
                raise AssertionError("Test failed")

            mock_load.return_value = failing_test
            result = execute_single_test(test_module, mock_page, "test_service")

        # Verify feedback was collected with failure
        assert result.status == "failed"
        assert mock_collector.collect_test_result.called
        call_args = mock_collector.collect_test_result.call_args
        assert call_args[1]["test_name"] == "test_fail_module"
        assert call_args[1]["success"] is False
        assert "Test failed" in call_args[1]["error_message"]
