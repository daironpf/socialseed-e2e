"""Unit tests for ML models.

Tests for the data models used in ML-Based Predictive Test Selection.
"""

from datetime import datetime

import pytest

from socialseed_e2e.ml.models import (
    ChangeType,
    CodeChange,
    CoverageGap,
    CoverageReport,
    FileType,
    FlakinessReport,
    ImpactAnalysis,
    MLModelPerformance,
    MLOrchestratorConfig,
    RedundancyReport,
    RedundantTest,
    TestHistory,
    TestMetrics,
    TestPrediction,
    TestPriority,
    TestSelectionResult,
)


class TestEnums:
    """Test enum definitions."""

    def test_change_type_values(self):
        """Test ChangeType enum has expected values."""
        assert ChangeType.ADDED.value == "added"
        assert ChangeType.MODIFIED.value == "modified"
        assert ChangeType.DELETED.value == "deleted"
        assert ChangeType.RENAMED.value == "renamed"

    def test_file_type_values(self):
        """Test FileType enum has expected values."""
        assert FileType.PYTHON.value == "python"
        assert FileType.JAVASCRIPT.value == "javascript"
        assert FileType.TEST.value == "test"

    def test_test_priority_values(self):
        """Test TestPriority enum has expected values."""
        assert TestPriority.CRITICAL.value == "critical"
        assert TestPriority.HIGH.value == "high"
        assert TestPriority.MEDIUM.value == "medium"
        assert TestPriority.LOW.value == "low"
        assert TestPriority.SKIP.value == "skip"


class TestCodeChange:
    """Test CodeChange model."""

    def test_code_change_creation(self):
        """Test creating a CodeChange instance."""
        change = CodeChange(
            file_path="src/app.py",
            change_type=ChangeType.MODIFIED,
            file_type=FileType.PYTHON,
            lines_added=10,
            lines_deleted=5,
            functions_changed=["main"],
            classes_changed=["App"],
            imports_changed=["os"],
            is_test_file=False,
        )

        assert change.file_path == "src/app.py"
        assert change.change_type == ChangeType.MODIFIED
        assert change.lines_added == 10
        assert change.lines_deleted == 5
        assert change.functions_changed == ["main"]

    def test_code_change_defaults(self):
        """Test CodeChange default values."""
        change = CodeChange(
            file_path="test.py",
            change_type=ChangeType.ADDED,
        )

        assert change.lines_added == 0
        assert change.lines_deleted == 0
        assert change.is_test_file is False
        assert change.functions_changed == []


class TestTestMetrics:
    """Test TestMetrics model."""

    def test_test_metrics_creation(self):
        """Test creating a TestMetrics instance."""
        metrics = TestMetrics(
            test_id="test_001",
            test_name="test_login",
            duration_ms=1000,
            passed=True,
            failed=False,
            coverage_percentage=85.5,
        )

        assert metrics.test_id == "test_001"
        assert metrics.passed is True
        assert metrics.failed is False
        assert metrics.duration_ms == 1000
        assert metrics.coverage_percentage == 85.5

    def test_test_metrics_defaults(self):
        """Test TestMetrics default values."""
        metrics = TestMetrics(
            test_id="test_001",
            test_name="test_login",
            duration_ms=1000,
            passed=True,
            failed=False,
        )

        assert metrics.skipped is False
        assert metrics.coverage_percentage == 0.0
        assert metrics.changed_files == []


class TestTestHistory:
    """Test TestHistory model."""

    def test_test_history_creation(self):
        """Test creating a TestHistory instance."""
        history = TestHistory(
            test_id="test_001",
            test_name="test_login",
            total_runs=10,
            pass_count=8,
            fail_count=2,
            failure_rate=0.2,
            flaky_score=0.3,
        )

        assert history.test_id == "test_001"
        assert history.total_runs == 10
        assert history.failure_rate == 0.2
        assert history.flaky_score == 0.3

    def test_test_history_validation(self):
        """Test TestHistory field validation."""
        # Test failure_rate bounds
        with pytest.raises(Exception):
            TestHistory(
                test_id="test_001",
                test_name="test_login",
                failure_rate=1.5,  # Invalid: > 1.0
            )

    def test_test_history_defaults(self):
        """Test TestHistory default values."""
        history = TestHistory(
            test_id="test_001",
            test_name="test_login",
        )

        assert history.total_runs == 0
        assert history.pass_count == 0
        assert history.failure_rate == 0.0
        assert history.flaky_score == 0.0
        assert history.runs == []


class TestImpactAnalysis:
    """Test ImpactAnalysis model."""

    def test_impact_analysis_creation(self):
        """Test creating an ImpactAnalysis instance."""
        change = CodeChange(
            file_path="src/app.py",
            change_type=ChangeType.MODIFIED,
        )

        analysis = ImpactAnalysis(
            changed_files=[change],
            affected_tests=["test_app.py"],
            impact_score=0.75,
            risk_level=TestPriority.HIGH,
            estimated_tests_to_run=5,
        )

        assert analysis.impact_score == 0.75
        assert analysis.risk_level == TestPriority.HIGH
        assert len(analysis.changed_files) == 1
        assert analysis.affected_tests == ["test_app.py"]

    def test_impact_analysis_validation(self):
        """Test ImpactAnalysis field validation."""
        # Test impact_score bounds
        with pytest.raises(Exception):
            ImpactAnalysis(
                impact_score=1.5,  # Invalid: > 1.0
            )


class TestTestPrediction:
    """Test TestPrediction model."""

    def test_test_prediction_creation(self):
        """Test creating a TestPrediction instance."""
        prediction = TestPrediction(
            test_id="test_001",
            test_name="test_login",
            failure_probability=0.8,
            estimated_duration_ms=1500,
            priority=TestPriority.HIGH,
            confidence=0.9,
            reasons=["Recent failures", "Code changes"],
            affected_by_changes=True,
            suggested_order=1,
        )

        assert prediction.failure_probability == 0.8
        assert prediction.priority == TestPriority.HIGH
        assert prediction.confidence == 0.9
        assert prediction.affected_by_changes is True


class TestTestSelectionResult:
    """Test TestSelectionResult model."""

    def test_test_selection_result_creation(self):
        """Test creating a TestSelectionResult instance."""
        prediction = TestPrediction(
            test_id="test_001",
            test_name="test_login",
            failure_probability=0.8,
            estimated_duration_ms=1500,
            priority=TestPriority.HIGH,
        )

        result = TestSelectionResult(
            total_tests=10,
            selected_tests=[prediction],
            skipped_tests=["test_002"],
            estimated_duration_ms=1500,
            estimated_coverage=75.0,
            risk_reduction=0.6,
            savings_percentage=50.0,
        )

        assert result.total_tests == 10
        assert len(result.selected_tests) == 1
        assert result.savings_percentage == 50.0


class TestFlakinessReport:
    """Test FlakinessReport model."""

    def test_flakiness_report_creation(self):
        """Test creating a FlakinessReport instance."""
        report = FlakinessReport(
            total_tests=100,
            flaky_tests=[{"test_id": "t1", "flaky_score": 0.5}],
            flaky_count=5,
            flaky_rate=0.05,
            top_flaky_tests=["test_1", "test_2"],
        )

        assert report.total_tests == 100
        assert report.flaky_count == 5
        assert report.flaky_rate == 0.05


class TestCoverageReport:
    """Test CoverageReport model."""

    def test_coverage_report_creation(self):
        """Test creating a CoverageReport instance."""
        gap = CoverageGap(
            file_path="src/app.py",
            function_name="main",
            line_start=10,
            line_end=20,
            gap_type="branch",
            severity=TestPriority.HIGH,
        )

        report = CoverageReport(
            overall_coverage=85.5,
            line_coverage=90.0,
            branch_coverage=75.0,
            function_coverage=95.0,
            gaps=[gap],
            gap_count=1,
            files_without_tests=["src/utils.py"],
        )

        assert report.overall_coverage == 85.5
        assert report.line_coverage == 90.0
        assert len(report.gaps) == 1

    def test_coverage_report_validation(self):
        """Test CoverageReport field validation."""
        # Test coverage bounds
        with pytest.raises(Exception):
            CoverageReport(
                overall_coverage=150.0,  # Invalid: > 100
            )


class TestRedundancyReport:
    """Test RedundancyReport model."""

    def test_redundancy_report_creation(self):
        """Test creating a RedundancyReport instance."""
        redundant = RedundantTest(
            test_id="test_001",
            test_name="test_login",
            similar_to=["test_002"],
            similarity_score=0.9,
            coverage_overlap=80.0,
            recommendation="merge",
        )

        report = RedundancyReport(
            total_tests=50,
            redundant_tests=[redundant],
            redundancy_count=1,
            potential_savings_ms=5000,
        )

        assert report.total_tests == 50
        assert report.redundancy_count == 1
        assert report.potential_savings_ms == 5000


class TestMLOrchestratorConfig:
    """Test MLOrchestratorConfig model."""

    def test_ml_orchestrator_config_creation(self):
        """Test creating an MLOrchestratorConfig instance."""
        config = MLOrchestratorConfig(
            enable_predictions=True,
            enable_flakiness_detection=True,
            selection_threshold=0.3,
            flakiness_threshold=0.2,
            max_tests_to_select=50,
        )

        assert config.enable_predictions is True
        assert config.selection_threshold == 0.3
        assert config.max_tests_to_select == 50

    def test_ml_orchestrator_config_defaults(self):
        """Test MLOrchestratorConfig default values."""
        config = MLOrchestratorConfig()

        assert config.enable_predictions is True
        assert config.enable_flakiness_detection is True
        assert config.selection_threshold == 0.3
        assert config.flakiness_threshold == 0.2
        assert config.min_confidence == 0.6

    def test_ml_orchestrator_config_validation(self):
        """Test MLOrchestratorConfig field validation."""
        # Test threshold bounds
        with pytest.raises(Exception):
            MLOrchestratorConfig(
                selection_threshold=1.5,  # Invalid: > 1.0
            )

        with pytest.raises(Exception):
            MLOrchestratorConfig(
                min_confidence=-0.1,  # Invalid: < 0.0
            )


class TestMLModelPerformance:
    """Test MLModelPerformance model."""

    def test_ml_model_performance_creation(self):
        """Test creating an MLModelPerformance instance."""
        performance = MLModelPerformance(
            model_name="failure_predictor",
            accuracy=0.85,
            precision=0.82,
            recall=0.88,
            f1_score=0.85,
            training_samples=1000,
        )

        assert performance.model_name == "failure_predictor"
        assert performance.accuracy == 0.85
        assert performance.precision == 0.82
        assert performance.f1_score == 0.85

    def test_ml_model_performance_validation(self):
        """Test MLModelPerformance field validation."""
        # Test metric bounds
        with pytest.raises(Exception):
            MLModelPerformance(
                model_name="test",
                accuracy=1.5,  # Invalid: > 1.0
            )
