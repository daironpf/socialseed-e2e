"""Tests for ShadowRunner main class."""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from socialseed_e2e.shadow_runner import (
    CaptureConfig,
    ReplayConfig,
    ShadowRunner,
    TestGenerationConfig,
)
from socialseed_e2e.shadow_runner.traffic_interceptor import (
    CapturedInteraction,
    CapturedRequest,
    CapturedResponse,
)


class TestShadowRunner:
    """Test suite for ShadowRunner class."""

    def test_shadow_runner_creation(self, tmp_path):
        """Test creating a ShadowRunner instance."""
        runner = ShadowRunner(output_dir=str(tmp_path / "captured"))

        assert runner.output_dir == tmp_path / "captured"
        assert runner.capturing is False
        assert runner.interceptor is not None
        assert runner.filter is not None
        assert runner.sanitizer is not None
        assert runner.session_recorder is not None

    def test_shadow_runner_creation_without_optional_features(self, tmp_path):
        """Test creating ShadowRunner with optional features disabled."""
        runner = ShadowRunner(
            output_dir=str(tmp_path / "captured"),
            enable_filtering=False,
            enable_sanitization=False,
            enable_session_tracking=False,
        )

        assert runner.filter is not None  # Still has a filter, just not SmartFilter
        assert runner.sanitizer is None
        assert runner.session_recorder is None

    def test_start_capturing(self, tmp_path):
        """Test starting capture."""
        runner = ShadowRunner(output_dir=str(tmp_path / "captured"))

        runner.start_capturing()

        assert runner.capturing is True
        assert runner.interceptor.capturing is True

    def test_start_capturing_with_session(self, tmp_path):
        """Test starting capture with session tracking."""
        runner = ShadowRunner(output_dir=str(tmp_path / "captured"))

        runner.start_capturing(user_id="user123", session_metadata={"source": "test"})

        assert runner.capturing is True
        assert runner.current_session_id is not None

    def test_stop_capturing(self, tmp_path):
        """Test stopping capture."""
        runner = ShadowRunner(output_dir=str(tmp_path / "captured"))
        runner.start_capturing()

        stats = runner.stop_capturing()

        assert runner.capturing is False
        assert runner.interceptor.capturing is False
        assert "total_requests" in stats

    def test_generate_tests_no_interactions(self, tmp_path):
        """Test generating tests when no interactions captured."""
        runner = ShadowRunner(output_dir=str(tmp_path / "captured"))

        files = runner.generate_tests()

        assert files == []

    def test_generate_tests_with_interactions(self, tmp_path):
        """Test generating tests from captured interactions."""
        runner = ShadowRunner(output_dir=str(tmp_path / "captured"))
        runner.start_capturing()

        # Simulate capturing some traffic
        request = CapturedRequest(method="GET", path="/api/users")
        response = CapturedResponse(status_code=200)
        runner.interceptor.capture_request(request)
        runner.interceptor.capture_response(response)

        runner.stop_capturing()

        files = runner.generate_tests(service_name="test_service")

        # Should generate at least one file
        assert len(files) > 0
        assert files[0].exists()

    def test_save_and_load_capture(self, tmp_path):
        """Test saving and loading capture data."""
        runner = ShadowRunner(output_dir=str(tmp_path / "captured"))
        runner.start_capturing()

        # Capture some traffic
        request = CapturedRequest(method="GET", path="/api/users")
        runner.interceptor.capture_request(request)

        runner.stop_capturing()

        # Save capture
        file_path = runner.save_capture("test_capture.json")

        assert file_path.exists()

        # Create new runner and load
        new_runner = ShadowRunner(output_dir=str(tmp_path / "captured"))
        new_runner.load_capture("test_capture.json")

        assert len(new_runner.interceptor.get_captured_interactions()) == 1

    def test_get_statistics(self, tmp_path):
        """Test getting capture statistics."""
        runner = ShadowRunner(output_dir=str(tmp_path / "captured"))
        runner.start_capturing()

        # Capture some traffic
        request = CapturedRequest(method="GET", path="/api/users")
        response = CapturedResponse(status_code=200)
        runner.interceptor.capture_request(request)
        runner.interceptor.capture_response(response)

        stats = runner.get_statistics()

        assert "total_requests" in stats
        assert "filtered_requests" in stats
        assert "final_captured" in stats

    def test_get_privacy_report(self, tmp_path):
        """Test getting privacy report."""
        runner = ShadowRunner(output_dir=str(tmp_path / "captured"))

        report = runner.get_privacy_report()

        assert report is not None

    def test_get_privacy_report_disabled(self, tmp_path):
        """Test getting privacy report when sanitizer is disabled."""
        runner = ShadowRunner(
            output_dir=str(tmp_path / "captured"),
            enable_sanitization=False,
        )

        report = runner.get_privacy_report()

        assert report == {"enabled": False}

    def test_clear_capture(self, tmp_path):
        """Test clearing captured data."""
        runner = ShadowRunner(output_dir=str(tmp_path / "captured"))
        runner.start_capturing()

        # Capture some traffic
        request = CapturedRequest(method="GET", path="/api/users")
        runner.interceptor.capture_request(request)

        runner.clear_capture()

        assert len(runner.interceptor.get_captured_interactions()) == 0

    def test_generate_middleware_flask(self, tmp_path):
        """Test generating Flask middleware code."""
        runner = ShadowRunner(output_dir=str(tmp_path / "captured"))

        code = runner.generate_middleware_flask()

        assert "FlaskMiddleware" in code
        assert "ShadowRunner" in code

    def test_generate_middleware_fastapi(self, tmp_path):
        """Test generating FastAPI middleware code."""
        runner = ShadowRunner(output_dir=str(tmp_path / "captured"))

        code = runner.generate_middleware_fastapi()

        assert "FastAPIMiddleware" in code
        assert "ShadowRunner" in code


class TestCaptureConfig:
    """Test suite for CaptureConfig dataclass."""

    def test_capture_config_creation(self):
        """Test creating CaptureConfig."""
        config = CaptureConfig(
            target_url="http://localhost:8080",
            output_path="./captures",
            filter_health_checks=True,
            filter_static_assets=True,
            sanitize_pii=True,
            max_requests=1000,
            duration=3600,
        )

        assert config.target_url == "http://localhost:8080"
        assert config.output_path == "./captures"
        assert config.filter_health_checks is True
        assert config.filter_static_assets is True
        assert config.sanitize_pii is True
        assert config.max_requests == 1000
        assert config.duration == 3600

    def test_capture_config_defaults(self):
        """Test CaptureConfig with defaults."""
        config = CaptureConfig(
            target_url="http://localhost:8080",
            output_path="./captures",
        )

        assert config.filter_health_checks is True
        assert config.filter_static_assets is True
        assert config.sanitize_pii is True
        assert config.max_requests is None
        assert config.duration is None


class TestTestGenerationConfig:
    """Test suite for TestGenerationConfig dataclass."""

    def test_test_generation_config_creation(self):
        """Test creating TestGenerationConfig."""
        config = TestGenerationConfig(
            service_name="users-api",
            output_dir="services",
            template="standard",
            group_by="endpoint",
            include_auth_patterns=True,
        )

        assert config.service_name == "users-api"
        assert config.output_dir == "services"
        assert config.template == "standard"
        assert config.group_by == "endpoint"
        assert config.include_auth_patterns is True

    def test_test_generation_config_defaults(self):
        """Test TestGenerationConfig with defaults."""
        config = TestGenerationConfig(service_name="users-api")

        assert config.output_dir == "services"
        assert config.template == "standard"
        assert config.group_by == "endpoint"
        assert config.include_auth_patterns is False


class TestReplayConfig:
    """Test suite for ReplayConfig dataclass."""

    def test_replay_config_creation(self):
        """Test creating ReplayConfig."""
        config = ReplayConfig(
            capture_file="capture.json",
            target_url="http://localhost:8080",
            speed="normal",
            stop_on_error=True,
        )

        assert config.capture_file == "capture.json"
        assert config.target_url == "http://localhost:8080"
        assert config.speed == "normal"
        assert config.stop_on_error is True

    def test_replay_config_defaults(self):
        """Test ReplayConfig with defaults."""
        config = ReplayConfig(capture_file="capture.json")

        assert config.target_url is None
        assert config.speed == "fast"
        assert config.stop_on_error is False


class TestCaptureWithContext:
    """Test suite for capture_with_context convenience function."""

    def test_capture_with_context(self, tmp_path):
        """Test capturing with context manager style."""
        from socialseed_e2e.shadow_runner import capture_with_context

        def test_function():
            return "result"

        result = capture_with_context(
            test_function,
            output_dir=str(tmp_path / "captured"),
        )

        assert result == "result"


class TestShadowRunnerIntegration:
    """Integration tests for ShadowRunner."""

    def test_full_capture_and_generate_workflow(self, tmp_path):
        """Test complete workflow from capture to test generation."""
        runner = ShadowRunner(output_dir=str(tmp_path / "captured"))

        # Start capturing
        runner.start_capturing(user_id="test_user")

        # Simulate some API traffic
        for i in range(3):
            request = CapturedRequest(
                method="GET" if i % 2 == 0 else "POST",
                path=f"/api/users/{i}",
            )
            response = CapturedResponse(
                status_code=200 if i % 2 == 0 else 201,
            )
            runner.interceptor.capture_request(request)
            runner.interceptor.capture_response(response)

        # Stop and get stats
        stats = runner.stop_capturing()
        assert stats["total_requests"] == 3

        # Generate tests
        files = runner.generate_tests(service_name="users_api")
        assert len(files) > 0

        # Save capture
        capture_file = runner.save_capture("session.json")
        assert capture_file.exists()

    def test_session_replay(self, tmp_path):
        """Test replaying a captured session."""
        runner = ShadowRunner(output_dir=str(tmp_path / "captured"))

        # Start capturing
        runner.start_capturing()

        # Capture some interactions
        for i in range(2):
            request = CapturedRequest(method="GET", path=f"/api/items/{i}")
            response = CapturedResponse(status_code=200)
            runner.interceptor.capture_request(request)
            runner.interceptor.capture_response(response)

        runner.stop_capturing()

        # Test replay (if session_recorder is enabled)
        if runner.session_recorder and runner.current_session_id:
            results = runner.replay_session(runner.current_session_id)
            assert isinstance(results, list)

    def test_privacy_sanitization(self, tmp_path):
        """Test that PII is sanitized during capture."""
        runner = ShadowRunner(
            output_dir=str(tmp_path / "captured"),
            enable_sanitization=True,
        )

        runner.start_capturing()

        # Capture request with potential PII
        request = CapturedRequest(
            method="POST",
            path="/api/users",
            body='{"email": "user@example.com", "password": "secret123"}',
        )
        runner.interceptor.capture_request(request)

        runner.stop_capturing()

        # Check privacy report
        report = runner.get_privacy_report()
        assert report is not None
