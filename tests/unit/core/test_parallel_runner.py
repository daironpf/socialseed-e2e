"""Tests for parallel test execution runner."""

import os
import tempfile
from pathlib import Path

import pytest

from socialseed_e2e.core.parallel_runner import (
    ParallelConfig,
    WorkerResult,
    WorkerTask,
    get_parallel_config_from_args,
)
from socialseed_e2e.core.test_runner import TestSuiteResult


class TestParallelConfig:
    """Test ParallelConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = ParallelConfig()
        assert config.enabled is False
        assert config.max_workers is not None  # Auto-detected
        assert config.parallel_mode == "service"
        assert config.isolation_level == "process"

    def test_custom_values(self):
        """Test custom configuration values."""
        config = ParallelConfig(
            enabled=True,
            max_workers=4,
            parallel_mode="test",
            isolation_level="service",
        )
        assert config.enabled is True
        assert config.max_workers == 4
        assert config.parallel_mode == "test"
        assert config.isolation_level == "service"

    def test_auto_workers(self):
        """Test auto-detection of worker count."""
        config = ParallelConfig(enabled=True)
        assert config.max_workers is not None
        assert 1 <= config.max_workers <= 8

    def test_invalid_parallel_mode(self):
        """Test validation of parallel mode."""
        with pytest.raises(ValueError, match="Invalid parallel_mode"):
            ParallelConfig(parallel_mode="invalid")

    def test_invalid_isolation_level(self):
        """Test validation of isolation level."""
        with pytest.raises(ValueError, match="Invalid isolation_level"):
            ParallelConfig(isolation_level="invalid")


class TestWorkerTask:
    """Test WorkerTask dataclass."""

    def test_creation(self):
        """Test worker task creation."""
        task = WorkerTask(
            service_name="test-service",
            service_config=None,
            module_paths=[Path("test.py")],
            project_root=Path("/project"),
        )
        assert task.service_name == "test-service"
        assert task.module_paths == [Path("test.py")]
        assert task.project_root == Path("/project")


class TestWorkerResult:
    """Test WorkerResult dataclass."""

    def test_success(self):
        """Test successful worker result."""
        suite = TestSuiteResult(total=5, passed=5)
        result = WorkerResult(
            service_name="test-service",
            suite_result=suite,
        )
        assert result.service_name == "test-service"
        assert result.error is None
        assert result.suite_result.total == 5

    def test_error(self):
        """Test worker result with error."""
        suite = TestSuiteResult()
        result = WorkerResult(
            service_name="test-service",
            suite_result=suite,
            error="Something went wrong",
        )
        assert result.error == "Something went wrong"


class TestGetParallelConfigFromArgs:
    """Test get_parallel_config_from_args function."""

    def test_disabled(self):
        """Test disabled parallel execution."""
        config = get_parallel_config_from_args(
            parallel_workers=0, config_path="/nonexistent/path.conf"
        )
        assert config.enabled is False

    def test_enabled_with_workers(self):
        """Test enabled with specific workers."""
        config = get_parallel_config_from_args(
            parallel_workers=4, config_path="/nonexistent/path.conf"
        )
        assert config.enabled is True
        assert config.max_workers == 4

    def test_enabled_auto_workers(self):
        """Test enabled with auto workers (negative number)."""
        config = get_parallel_config_from_args(
            parallel_workers=-1, config_path="/nonexistent/path.conf"
        )
        assert config.enabled is True
        assert config.max_workers == -1  # Will be auto-detected in runner

    def test_default_disabled(self):
        """Test default is disabled."""
        config = get_parallel_config_from_args(config_path="/nonexistent/path.conf")
        assert config.enabled is False


class TestIntegration:
    """Integration tests for parallel runner."""

    @pytest.mark.slow
    def test_parallel_config_integration(self):
        """Test that parallel config can be imported from main package."""
        from socialseed_e2e import ParallelConfig, run_tests_parallel

        config = ParallelConfig(enabled=True, max_workers=2)
        assert config.enabled is True
        assert config.max_workers == 2

        # Verify function exists
        assert callable(run_tests_parallel)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
