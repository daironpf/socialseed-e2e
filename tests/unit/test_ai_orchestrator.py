"""Unit tests for AI Orchestration Layer.

This module contains tests for the ai_orchestrator components.
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from socialseed_e2e.ai_orchestrator.debugger import FixSuggester, LogAnalyzer, RootCauseAnalyzer
from socialseed_e2e.ai_orchestrator.models import (
    FailurePattern,
    OrchestratorConfig,
    RetryStrategy,
    RiskFactor,
    TestCase,
    TestExecution,
    TestPriority,
    TestResult,
    TestStatus,
    TestStrategy,
    TestType,
)
from socialseed_e2e.ai_orchestrator.self_healer import FlakyPatternDetector, SelfHealer, TestHealer


class TestModels:
    """Tests for orchestration models."""

    def test_test_priority_enum(self):
        """Test TestPriority enum values."""
        assert TestPriority.CRITICAL.value == "critical"
        assert TestPriority.HIGH.value == "high"
        assert TestPriority.MEDIUM.value == "medium"
        assert TestPriority.LOW.value == "low"

    def test_test_status_enum(self):
        """Test TestStatus enum values."""
        assert TestStatus.PENDING.value == "pending"
        assert TestStatus.PASSED.value == "passed"
        assert TestStatus.FAILED.value == "failed"
        assert TestStatus.FLAKY.value == "flaky"
        assert TestStatus.HEALED.value == "healed"

    def test_test_type_enum(self):
        """Test TestType enum values."""
        assert TestType.UNIT.value == "unit"
        assert TestType.INTEGRATION.value == "integration"
        assert TestType.E2E.value == "e2e"

    def test_test_case_creation(self):
        """Test TestCase model creation."""
        test_case = TestCase(
            id="test_001",
            name="Test Login",
            description="Test user login endpoint",
            test_type=TestType.E2E,
            priority=TestPriority.HIGH,
            service="users-api",
            module="services/users-api/modules/test_login.py",
        )

        assert test_case.id == "test_001"
        assert test_case.name == "Test Login"
        assert test_case.priority == TestPriority.HIGH
        assert test_case.service == "users-api"
        assert test_case.estimated_duration_ms == 1000  # default

    def test_test_case_with_risk_factors(self):
        """Test TestCase with risk factors."""
        risk_factor = RiskFactor(
            factor_type="complexity",
            score=0.7,
            description="High complexity endpoint",
        )

        test_case = TestCase(
            id="test_002",
            name="Test Complex Endpoint",
            description="Test with high complexity",
            test_type=TestType.E2E,
            service="orders-api",
            module="services/orders-api/modules/test_complex.py",
            risk_factors=[risk_factor],
        )

        assert len(test_case.risk_factors) == 1
        assert test_case.risk_factors[0].score == 0.7

    def test_test_strategy_creation(self):
        """Test TestStrategy model creation."""
        strategy = TestStrategy(
            id="strategy_001",
            name="API Test Strategy",
            description="Comprehensive API testing",
        )

        assert strategy.id == "strategy_001"
        assert strategy.name == "API Test Strategy"
        assert strategy.total_estimated_duration_ms == 0
        assert strategy.test_cases == []

    def test_test_result_creation(self):
        """Test TestResult model creation."""
        result = TestResult(
            test_id="test_001",
            status=TestStatus.PASSED,
            started_at=datetime.utcnow(),
        )

        assert result.test_id == "test_001"
        assert result.status == TestStatus.PASSED
        assert result.attempts == 1  # default
        assert result.healed == False  # default

    def test_test_execution_creation(self):
        """Test TestExecution model creation."""
        execution = TestExecution(
            id="exec_001",
            strategy_id="strategy_001",
        )

        assert execution.id == "exec_001"
        assert execution.strategy_id == "strategy_001"
        assert execution.status == TestStatus.PENDING  # default

    def test_failure_pattern_creation(self):
        """Test FailurePattern model creation."""
        pattern = FailurePattern(
            pattern_id="pattern_001",
            pattern_type="timeout",
            signature="abc123",
        )

        assert pattern.pattern_id == "pattern_001"
        assert pattern.pattern_type == "timeout"
        assert pattern.frequency == 1  # default

    def test_retry_strategy_creation(self):
        """Test RetryStrategy model creation."""
        strategy = RetryStrategy(
            pattern_id="pattern_001",
            max_retries=5,
            backoff_type="exponential",
        )

        assert strategy.pattern_id == "pattern_001"
        assert strategy.max_retries == 5
        assert strategy.backoff_type == "exponential"
        assert strategy.base_delay_ms == 1000  # default

    def test_orchestrator_config_defaults(self):
        """Test OrchestratorConfig default values."""
        config = OrchestratorConfig()

        assert config.enable_self_healing == True
        assert config.enable_intelligent_retry == True
        assert config.enable_auto_debug == True
        assert config.max_auto_fix_attempts == 3
        assert config.parallel_workers == 4


class TestFlakyPatternDetector:
    """Tests for FlakyPatternDetector."""

    def test_detect_hardcoded_sleep(self):
        """Test detection of hardcoded sleep patterns."""
        detector = FlakyPatternDetector()
        source_code = """
def test_something():
    do_something()
    time.sleep(2)  # Bad practice
    assert result == expected
"""
        patterns = detector.detect_patterns(source_code)

        assert len(patterns) > 0
        assert any(p["pattern"] == "hardcoded_sleep" for p in patterns)

    def test_detect_external_dependency(self):
        """Test detection of external dependency patterns."""
        detector = FlakyPatternDetector()
        source_code = """
def test_api():
    response = requests.get('http://api.example.com/data')
    assert response.status_code == 200
"""
        patterns = detector.detect_patterns(source_code)

        assert any(p["pattern"] == "external_dependency" for p in patterns)

    def test_detect_random_data(self):
        """Test detection of random data patterns."""
        detector = FlakyPatternDetector()
        source_code = """
def test_with_random():
    user_id = random.randint(1, 1000)
    assert user_id > 0
"""
        patterns = detector.detect_patterns(source_code)

        assert any(p["pattern"] == "random_data" for p in patterns)

    def test_no_patterns_detected(self):
        """Test that clean code has no patterns."""
        detector = FlakyPatternDetector()
        source_code = """
def test_clean():
    result = calculate(2, 3)
    assert result == 5
"""
        patterns = detector.detect_patterns(source_code)

        assert len(patterns) == 0


class TestLogAnalyzer:
    """Tests for LogAnalyzer."""

    def test_classify_timeout_error(self):
        """Test classification of timeout errors."""
        analyzer = LogAnalyzer()
        error_msg = "Request timed out after 30 seconds"
        stack_trace = ""

        error_type = analyzer.classify_error(error_msg, stack_trace)

        assert error_type == "timeout_error"

    def test_classify_assertion_error(self):
        """Test classification of assertion errors."""
        analyzer = LogAnalyzer()
        error_msg = "AssertionError: expected 200 but got 404"
        stack_trace = ""

        error_type = analyzer.classify_error(error_msg, stack_trace)

        assert error_type == "assertion_error"

    def test_classify_network_error(self):
        """Test classification of network errors."""
        analyzer = LogAnalyzer()
        error_msg = "Connection refused"
        stack_trace = ""

        error_type = analyzer.classify_error(error_msg, stack_trace)

        assert error_type == "network_error"

    def test_classify_authentication_error(self):
        """Test classification of authentication errors."""
        analyzer = LogAnalyzer()
        error_msg = "401 Unauthorized: Invalid token"
        stack_trace = ""

        error_type = analyzer.classify_error(error_msg, stack_trace)

        assert error_type == "authentication_error"

    def test_extract_request_info(self):
        """Test extraction of request info from logs."""
        analyzer = LogAnalyzer()
        logs = [
            "INFO: Starting test",
            "GET /api/users/123 - 200 (150ms)",
            "INFO: Test complete",
        ]

        request_info = analyzer.extract_request_info(logs)

        assert request_info is not None
        assert request_info["method"] == "GET"
        assert request_info["status"] == 200


class TestRootCauseAnalyzer:
    """Tests for RootCauseAnalyzer."""

    def test_analyze_timeout_cause(self):
        """Test analysis of timeout root cause."""
        analyzer = RootCauseAnalyzer()
        test_case = TestCase(
            id="test_001",
            name="Test API",
            description="Test endpoint",
            test_type=TestType.E2E,
            service="api",
            module="test.py",
        )

        root_cause, confidence = analyzer.analyze(
            test_case,
            "Request timed out",
            "",
            [],
        )

        assert root_cause is not None
        assert 0.0 <= confidence <= 1.0

    def test_analyze_network_cause(self):
        """Test analysis of network error root cause."""
        analyzer = RootCauseAnalyzer()
        test_case = TestCase(
            id="test_002",
            name="Test API",
            description="Test endpoint",
            test_type=TestType.E2E,
            service="api",
            module="test.py",
        )

        root_cause, confidence = analyzer.analyze(
            test_case,
            "Connection refused",
            "",
            [],
        )

        assert root_cause is not None
        assert 0.0 <= confidence <= 1.0


class TestFixSuggester:
    """Tests for FixSuggester."""

    def test_suggest_timeout_fixes(self):
        """Test fix suggestions for timeout errors."""
        suggester = FixSuggester()
        test_case = TestCase(
            id="test_001",
            name="Test API",
            description="Test endpoint",
            test_type=TestType.E2E,
            service="api",
            module="test.py",
        )

        fixes = suggester.suggest_fixes(
            "timeout_error",
            "Service timeout",
            test_case,
        )

        assert len(fixes) > 0
        assert all("description" in fix for fix in fixes)

    def test_fix_risk_assessment(self):
        """Test fix risk assessment."""
        suggester = FixSuggester()

        low_risk_fix = {
            "description": "Simple fix",
            "code_changes": [{"pattern": "x", "replacement": "y"}],
        }

        risk = suggester._assess_risk(low_risk_fix)

        assert risk == "low"


class TestSelfHealer:
    """Tests for SelfHealer."""

    def test_healer_initialization(self, tmp_path):
        """Test SelfHealer initialization."""
        healer = SelfHealer(str(tmp_path))

        assert healer.project_path == tmp_path
        assert healer.healing_history == []

    def test_get_healing_statistics_empty(self, tmp_path):
        """Test healing statistics with no healings."""
        healer = SelfHealer(str(tmp_path))
        stats = healer.get_healing_statistics()

        assert stats["total_healings"] == 0
        assert stats["most_common_patterns"] == []

    def test_analyze_flaky_code(self, tmp_path):
        """Test analysis of flaky code."""
        # Create a test file with flaky patterns
        test_file = tmp_path / "test_flaky.py"
        test_file.write_text(
            """
import time
import random

def test_with_sleep():
    time.sleep(2)
    assert True

def test_with_random():
    value = random.randint(1, 10)
    assert value > 0
"""
        )

        healer = SelfHealer(str(tmp_path))
        report = healer.analyze_test_file(str(test_file))

        assert "flakiness_patterns" in report
        assert len(report["flakiness_patterns"]) > 0


@pytest.mark.unit
class TestIntegration:
    """Integration tests for orchestrator components."""

    def test_end_to_end_model_flow(self):
        """Test complete flow with models."""
        # Create risk factors
        risk = RiskFactor(
            factor_type="business_impact",
            score=0.8,
            description="High business impact",
        )

        # Create test case
        test_case = TestCase(
            id="test_e2e_001",
            name="End-to-end Test",
            description="Complete flow test",
            test_type=TestType.E2E,
            priority=TestPriority.HIGH,
            service="api",
            module="test.py",
            risk_factors=[risk],
        )

        # Create strategy
        strategy = TestStrategy(
            id="strategy_e2e",
            name="E2E Strategy",
            description="Test strategy",
            test_cases=[test_case],
        )

        # Create execution
        execution = TestExecution(
            id="exec_e2e",
            strategy_id=strategy.id,
        )

        # Create result
        result = TestResult(
            test_id=test_case.id,
            status=TestStatus.PASSED,
            started_at=datetime.utcnow(),
        )

        execution.results.append(result)

        assert execution.results[0].test_id == test_case.id
        assert execution.results[0].status == TestStatus.PASSED
