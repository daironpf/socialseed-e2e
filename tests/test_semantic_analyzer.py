"""Tests for Semantic Analyzer Agent.

Tests for intent extraction, state capture, drift detection, and report generation.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from socialseed_e2e.agents.semantic_analyzer.intent_baseline_extractor import (
    IntentBaselineExtractor,
)
from socialseed_e2e.agents.semantic_analyzer.models import (
    DriftSeverity,
    DriftType,
    IntentBaseline,
    IntentSource,
    LogicDrift,
    SemanticDriftReport,
)
from socialseed_e2e.agents.semantic_analyzer.report_generator import SemanticDriftReportGenerator


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project structure."""
    # Create docs folder
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    # Create a README.md
    readme = docs_dir / "README.md"
    readme.write_text(
        """
# API Documentation

## Feature: User Authentication

When a user logs in, they should receive a valid JWT token.

### Success Criteria
- Token must be returned in response
- Token must expire after 24 hours
- Invalid credentials must return 401

## Feature: User Registration

New users must be able to register with email and password.

### Success Criteria
- Email must be unique
- Password must be at least 8 characters
- Confirmation email must be sent
"""
    )

    # Create tests folder
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()

    # Create a test file
    test_file = tests_dir / "test_auth.py"
    test_file.write_text(
        """
def test_login_success():
    '''Test that login returns a valid token'''
    pass

def test_login_invalid_credentials():
    '''Test that invalid credentials return 401'''
    pass
"""
    )

    return tmp_path


@pytest.fixture
def sample_intent():
    """Create a sample intent baseline."""
    return IntentBaseline(
        intent_id="test_001",
        description="User Login",
        category="user_management",
        expected_behavior="User should receive JWT token after successful login",
        success_criteria=[
            "Token is returned in response",
            "Token expires after 24 hours",
            "Invalid credentials return 401",
        ],
        sources=[
            IntentSource(
                source_type="documentation",
                source_path="docs/README.md",
                title="User Authentication",
            )
        ],
    )


@pytest.fixture
def sample_drift(sample_intent):
    """Create a sample logic drift."""
    return LogicDrift(
        drift_id="drift_001",
        drift_type=DriftType.BEHAVIORAL,
        severity=DriftSeverity.HIGH,
        intent=sample_intent,
        description="Login endpoint no longer returns JWT token",
        affected_endpoints=["/api/auth/login"],
        reasoning="API response structure changed without documentation update",
        confidence=0.85,
    )


@pytest.fixture
def sample_report(temp_project, sample_intent, sample_drift):
    """Create a sample semantic drift report."""
    return SemanticDriftReport(
        report_id="test_report_001",
        project_name="test-project",
        baseline_commit="abc123",
        target_commit="def456",
        intent_baselines=[sample_intent],
        detected_drifts=[sample_drift],
    )


class TestIntentBaselineExtractor:
    """Tests for IntentBaselineExtractor."""

    def test_extract_from_docs(self, temp_project):
        """Test extracting intents from documentation."""
        extractor = IntentBaselineExtractor(temp_project)
        baselines = extractor.extract_all()

        # Should extract intents from docs
        assert len(baselines) > 0

        # Check that baselines have required fields
        for baseline in baselines:
            assert baseline.intent_id
            assert baseline.description
            assert baseline.category
            assert baseline.expected_behavior
            assert baseline.confidence > 0

    def test_categorize_intent(self, temp_project):
        """Test intent categorization."""
        extractor = IntentBaselineExtractor(temp_project)

        # Test various categories
        assert extractor._categorize_intent("user login authentication", "") == "user_management"
        assert (
            extractor._categorize_intent("payment processing billing", "") == "payment_processing"
        )
        assert extractor._categorize_intent("database data create update", "") == "data_management"
        assert extractor._categorize_intent("random unrelated text", "") == "general"

    def test_extract_success_criteria(self, temp_project):
        """Test extracting success criteria."""
        extractor = IntentBaselineExtractor(temp_project)

        content = """
Success Criteria:
- Criterion one
- Criterion two
- Criterion three
"""
        criteria = extractor._extract_success_criteria(content)

        assert len(criteria) >= 2
        assert "Criterion one" in criteria

    def test_extract_expected_behavior(self, temp_project):
        """Test extracting expected behavior."""
        extractor = IntentBaselineExtractor(temp_project)

        content = "The system should return a valid token"
        behavior = extractor._extract_expected_behavior(content)

        assert "return a valid token" in behavior


class TestSemanticDriftReportGenerator:
    """Tests for SemanticDriftReportGenerator."""

    def test_generate_markdown_report(
        self, sample_report, sample_intent, sample_drift, temp_project
    ):
        """Test generating markdown report."""
        generator = SemanticDriftReportGenerator(temp_project)

        output_path = temp_project / "report.md"
        result_path = generator.generate_report(sample_report, output_path)

        assert result_path.exists()
        content = result_path.read_text()

        # Check for key sections
        assert "# Semantic Drift Analysis Report" in content
        assert sample_report.report_id in content
        assert sample_report.project_name in content
        assert sample_intent.description in content
        assert sample_drift.description in content

    def test_generate_json_report(self, sample_report, temp_project):
        """Test generating JSON report."""
        generator = SemanticDriftReportGenerator(temp_project)

        output_path = temp_project / "report.json"
        result_path = generator.generate_json_report(sample_report, output_path)

        assert result_path.exists()
        content = result_path.read_text()
        data = json.loads(content)

        assert data["report_id"] == sample_report.report_id
        assert data["project_name"] == sample_report.project_name
        assert len(data["intent_baselines"]) == 1
        assert len(data["detected_drifts"]) == 1

    def test_report_summary_generation(self, sample_report):
        """Test report summary generation."""
        summary = sample_report.generate_summary()

        assert summary["total_drifts"] == 1
        assert summary["total_intents_analyzed"] == 1
        assert summary["has_critical_issues"] == False
        assert "severity_distribution" in summary
        assert "type_distribution" in summary

    def test_get_drifts_by_severity(self, sample_report):
        """Test filtering drifts by severity."""
        high_drifts = sample_report.get_drifts_by_severity(DriftSeverity.HIGH)
        assert len(high_drifts) == 1

        critical_drifts = sample_report.get_drifts_by_severity(DriftSeverity.CRITICAL)
        assert len(critical_drifts) == 0

    def test_get_drifts_by_type(self, sample_report):
        """Test filtering drifts by type."""
        behavioral_drifts = sample_report.get_drifts_by_type(DriftType.BEHAVIORAL)
        assert len(behavioral_drifts) == 1

        relationship_drifts = sample_report.get_drifts_by_type(DriftType.RELATIONSHIP)
        assert len(relationship_drifts) == 0


class TestLogicDriftModels:
    """Tests for drift and intent models."""

    def test_intent_baseline_hash(self, sample_intent):
        """Test that intent baselines are hashable."""
        # Should not raise TypeError
        hash(sample_intent)

    def test_drift_to_dict(self, sample_drift):
        """Test converting drift to dictionary."""
        drift_dict = sample_drift.to_dict()

        assert drift_dict["drift_id"] == sample_drift.drift_id
        assert drift_dict["drift_type"] == sample_drift.drift_type.name
        assert drift_dict["severity"] == sample_drift.severity.value
        assert drift_dict["intent_id"] == sample_drift.intent.intent_id

    def test_drift_has_critical_method(self, sample_report):
        """Test has_critical_drifts method."""
        assert sample_report.has_critical_drifts() == False

        # Add a critical drift
        critical_drift = LogicDrift(
            drift_id="critical_001",
            drift_type=DriftType.BUSINESS_RULE,
            severity=DriftSeverity.CRITICAL,
            intent=sample_report.intent_baselines[0],
            description="Critical business rule violation",
        )
        sample_report.detected_drifts.append(critical_drift)

        assert sample_report.has_critical_drifts() == True


class TestEndToEnd:
    """End-to-end tests for semantic analyzer."""

    @pytest.mark.integration
    def test_full_analysis_workflow(self, temp_project):
        """Test complete analysis workflow."""
        from socialseed_e2e.agents.semantic_analyzer import SemanticAnalyzerAgent

        agent = SemanticAnalyzerAgent(
            project_root=temp_project,
            project_name="test-project",
        )

        # Run quick check (no state capture)
        result = agent.quick_check()

        assert "total_intents" in result
        assert "by_category" in result
        assert result["total_intents"] > 0

    def test_intent_summary(self, temp_project):
        """Test getting intent summary."""
        from socialseed_e2e.agents.semantic_analyzer import SemanticAnalyzerAgent

        agent = SemanticAnalyzerAgent(
            project_root=temp_project,
            project_name="test-project",
        )

        summary = agent.get_intent_summary()

        assert "total" in summary
        assert "by_category" in summary
        assert "by_source_type" in summary
        assert summary["total"] > 0
