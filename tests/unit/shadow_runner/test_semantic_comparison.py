"""Unit tests for semantic comparison in Shadow Runner (Phase 3)."""

import pytest
from unittest.mock import MagicMock, patch

from socialseed_e2e.shadow_runner.models import (
    ReplayConfig,
    SemanticComparisonResult,
    ReplayComparisonReport,
)
from socialseed_e2e.shadow_runner.runner import ShadowRunner


class TestSemanticComparisonModels:
    """Tests for semantic comparison models."""

    def test_replay_config_defaults(self):
        """Test ReplayConfig default values."""
        config = ReplayConfig(target_url="http://localhost:8080")
        
        assert config.target_url == "http://localhost:8080"
        assert config.compare_semantically is True
        assert config.baseline_url is None
        assert config.tolerance_percent == 5.0

    def test_replay_config_with_comparison(self):
        """Test ReplayConfig with semantic comparison."""
        config = ReplayConfig(
            target_url="http://localhost:8080",
            baseline_url="http://production:8080",
            compare_semantically=True,
            tolerance_percent=10.0,
        )
        
        assert config.compare_semantically is True
        assert config.baseline_url == "http://production:8080"
        assert config.tolerance_percent == 10.0

    def test_semantic_comparison_result(self):
        """Test SemanticComparisonResult model."""
        result = SemanticComparisonResult(
            request_id="req-123",
            method="GET",
            url="/api/users",
            baseline_status=200,
            target_status=200,
            status_match=True,
            body_similar=True,
            similarity_score=0.95,
            differences=[],
            severity="none",
        )
        
        assert result.request_id == "req-123"
        assert result.method == "GET"
        assert result.status_match is True

    def test_semantic_comparison_result_with_differences(self):
        """Test SemanticComparisonResult with differences."""
        result = SemanticComparisonResult(
            request_id="req-456",
            method="POST",
            url="/api/users",
            baseline_status=200,
            target_status=500,
            status_match=False,
            body_similar=False,
            similarity_score=0.5,
            differences=["Field 'name': Alice -> Error"],
            severity="critical",
        )
        
        assert result.status_match is False
        assert result.severity == "critical"
        assert len(result.differences) == 1

    def test_replay_comparison_report(self):
        """Test ReplayComparisonReport model."""
        report = ReplayComparisonReport(
            total_requests=10,
            successful_replays=8,
            failed_replays=2,
            critical_issues=1,
            warning_issues=2,
            info_issues=1,
        )
        
        assert report.total_requests == 10
        assert report.successful_replays == 8
        assert report.critical_issues == 1


class TestShadowRunnerComparison:
    """Tests for ShadowRunner semantic comparison."""

    @pytest.fixture
    def runner(self, tmp_path):
        """Create a ShadowRunner fixture."""
        return ShadowRunner(output_dir=str(tmp_path / "shadow"))

    def test_extract_differences_json(self, runner):
        """Test extracting differences from JSON responses."""
        baseline = '{"id": 1, "name": "Alice", "email": "alice@test.com"}'
        target = '{"id": 1, "name": "Bob", "email": "alice@test.com"}'
        
        differences = runner._extract_differences(baseline, target)
        
        assert len(differences) > 0

    def test_extract_differences_no_differences(self, runner):
        """Test extracting differences when bodies are identical."""
        baseline = '{"id": 1, "name": "Alice"}'
        target = '{"id": 1, "name": "Alice"}'
        
        differences = runner._extract_differences(baseline, target)
        
        assert len(differences) == 0

    def test_extract_differences_non_json(self, runner):
        """Test extracting differences from non-JSON responses."""
        baseline = "Hello World"
        target = "Hello Universe"
        
        differences = runner._extract_differences(baseline, target)
        
        assert len(differences) > 0


class TestShadowRunnerWithComparison:
    """Tests for ShadowRunner replay with comparison."""

    @pytest.fixture
    def runner(self, tmp_path):
        """Create a ShadowRunner fixture."""
        return ShadowRunner(output_dir=str(tmp_path / "shadow"))

    def test_replay_with_comparison_config(self, runner, tmp_path):
        """Test replay_traffic uses comparison when configured."""
        from socialseed_e2e.shadow_runner.models import CapturedTraffic
        from datetime import datetime

        capture_file = tmp_path / "capture.json"
        capture_file.write_text('{"capture_id": "test", "requests": [], "metadata": {}}')

        config = ReplayConfig(
            target_url="http://localhost:8080",
            baseline_url="http://production:8080",
            compare_semantically=True,
            tolerance_percent=5.0,
        )

        with patch.object(runner, "load_capture") as mock_load:
            mock_load.return_value = CapturedTraffic(
                capture_id="test",
                capture_time=datetime.now(),
                source_url="http://source",
                requests=[],
                metadata={},
            )
            
            result = runner.replay_traffic(str(capture_file), config)
            
            assert isinstance(result, ReplayComparisonReport)

    def test_replay_without_comparison(self, runner, tmp_path):
        """Test replay_traffic returns dict when comparison disabled."""
        capture_file = tmp_path / "capture.json"
        capture_file.write_text('{"capture_id": "test", "requests": [], "metadata": {}}')

        config = ReplayConfig(
            target_url="http://localhost:8080",
            compare_semantically=False,
        )

        with patch.object(runner, "load_capture") as mock_load:
            from socialseed_e2e.shadow_runner.models import CapturedTraffic
            from datetime import datetime
            
            mock_load.return_value = CapturedTraffic(
                capture_id="test",
                capture_time=datetime.now(),
                source_url="http://source",
                requests=[],
                metadata={},
            )
            
            result = runner.replay_traffic(str(capture_file), config)
            
            assert isinstance(result, dict)
            assert "total" in result
