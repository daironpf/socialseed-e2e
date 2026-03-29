"""Unit tests for generate-tests command (Phase 2)."""

import pytest

from socialseed_e2e.commands.ai_commands import TestGenerator


class TestTestGenerator:
    """Tests for TestGenerator with RAG integration."""

    def test_test_generator_init_default(self, tmp_path):
        """Test TestGenerator initialization with defaults."""
        generator = TestGenerator(
            directory=str(tmp_path),
            output="services",
            service=None,
            strategy="all",
            use_manifest=False,
            dry_run=False,
            verbose=False,
        )
        
        assert generator.use_manifest is False
        assert generator.service is None
        assert generator.strategy == "all"

    def test_test_generator_init_with_manifest(self, tmp_path):
        """Test TestGenerator initialization with manifest flag."""
        generator = TestGenerator(
            directory=str(tmp_path),
            output="services",
            service="test-service",
            strategy="all",
            use_manifest=True,
            dry_run=False,
            verbose=False,
        )
        
        assert generator.use_manifest is True
        assert generator.service == "test-service"

    def test_get_manifest_context_no_service(self, tmp_path):
        """Test _get_manifest_context returns None when no service."""
        generator = TestGenerator(
            directory=str(tmp_path),
            output="services",
            service=None,
            strategy="all",
            use_manifest=True,
            dry_run=False,
            verbose=False,
        )
        
        result = generator._get_manifest_context()
        
        assert result is None

    def test_get_manifest_context_missing_manifest(self, tmp_path):
        """Test _get_manifest_context handles missing manifest."""
        generator = TestGenerator(
            directory=str(tmp_path),
            output="services",
            service="nonexistent-service",
            strategy="all",
            use_manifest=True,
            dry_run=False,
            verbose=False,
        )
        
        result = generator._get_manifest_context()
        
        assert result is None


class TestGenerateTestsOutput:
    """Tests for generate-tests command output."""

    def test_generate_without_manifest_flag(self, tmp_path, capsys):
        """Test that generate without manifest works."""
        generator = TestGenerator(
            directory=str(tmp_path),
            output="services",
            service=None,
            strategy="all",
            use_manifest=False,
            dry_run=False,
            verbose=False,
        )
        
        generator.generate()
        
        captured = capsys.readouterr()
        assert "Test Suite Generation" in captured.out or "test" in captured.out.lower()
