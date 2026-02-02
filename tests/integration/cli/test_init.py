"""Integration tests for 'e2e init' command.

This module contains integration tests for the socialseed-e2e 'init' CLI command.
These tests verify that the init command properly initializes an E2E project
with the correct directory structure and configuration files.
"""

import os

import pytest

pytestmark = pytest.mark.integration
from click.testing import CliRunner

from socialseed_e2e.cli import cli


class TestE2EInitCommand:
    """Integration tests for 'e2e init' command."""

    def test_init_creates_directory_structure(self, cli_runner, temp_dir):
        """Test that init creates the expected directory structure."""
        result = cli_runner.invoke(cli, ["init", str(temp_dir)])

        assert result.exit_code == 0
        assert (temp_dir / "services").exists()
        assert (temp_dir / "tests").exists()
        assert (temp_dir / ".github" / "workflows").exists()

    def test_init_creates_e2e_conf(self, cli_runner, temp_dir):
        """Test that init creates e2e.conf with correct content."""
        result = cli_runner.invoke(cli, ["init", str(temp_dir)])

        assert result.exit_code == 0

        config_file = temp_dir / "e2e.conf"
        assert config_file.exists()

        content = config_file.read_text()
        assert "general:" in content
        assert "environment:" in content
        assert "services:" in content

    def test_init_creates_gitignore(self, cli_runner, temp_dir):
        """Test that init creates .gitignore file."""
        result = cli_runner.invoke(cli, ["init", str(temp_dir)])

        assert result.exit_code == 0

        gitignore = temp_dir / ".gitignore"
        assert gitignore.exists()

        content = gitignore.read_text()
        assert "__pycache__/" in content
        assert "venv/" in content

    def test_init_with_force_overwrites(self, cli_runner, temp_dir):
        """Test that --force flag overwrites existing files."""
        # First init
        cli_runner.invoke(cli, ["init", str(temp_dir)])

        # Modify e2e.conf
        config_file = temp_dir / "e2e.conf"
        original_content = config_file.read_text()
        config_file.write_text("modified content")

        # Second init with force
        result = cli_runner.invoke(cli, ["init", str(temp_dir), "--force"])

        assert result.exit_code == 0
        # Should be overwritten
        new_content = config_file.read_text()
        assert new_content != "modified content"
        assert "general:" in new_content

    def test_init_without_force_preserves_existing(self, cli_runner, temp_dir):
        """Test that without --force, existing files are preserved."""
        # First init
        cli_runner.invoke(cli, ["init", str(temp_dir)])

        # Modify e2e.conf
        config_file = temp_dir / "e2e.conf"
        config_file.write_text("custom content")

        # Second init without force
        result = cli_runner.invoke(cli, ["init", str(temp_dir)])

        assert result.exit_code == 0
        # Should be preserved
        assert config_file.read_text() == "custom content"

    def test_init_default_directory(self, isolated_cli_runner, temp_dir):
        """Test init with default directory (current directory)."""
        result = isolated_cli_runner.invoke(cli, ["init"])

        assert result.exit_code == 0
        assert (temp_dir / "e2e.conf").exists()

    def test_init_shows_success_message(self, cli_runner, temp_dir):
        """Test that init shows success message."""
        result = cli_runner.invoke(cli, ["init", str(temp_dir)])

        assert result.exit_code == 0
        assert "Proyecto inicializado" in result.output or "initialized" in result.output.lower()
        assert "✅" in result.output or "✓" in result.output
