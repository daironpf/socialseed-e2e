"""Integration tests for 'e2e doctor' command.

This module contains integration tests for the socialseed-e2e 'doctor' CLI command.
These tests verify that the doctor command properly checks system dependencies
and displays diagnostic information.
"""

import pytest

pytestmark = pytest.mark.integration
from click.testing import CliRunner

from socialseed_e2e.cli import cli


class TestE2EDoctorCommand:
    """Integration tests for 'e2e doctor' command."""

    def test_doctor_runs_successfully(self, cli_runner):
        """Test that doctor command runs without errors."""
        result = cli_runner.invoke(cli, ["doctor"])

        assert result.exit_code == 0

    def test_doctor_shows_system_check_table(self, cli_runner):
        """Test that doctor shows system check table."""
        result = cli_runner.invoke(cli, ["doctor"])

        assert result.exit_code == 0
        assert any(word in result.output for word in ["Verificación", "Verification", "Check"])
        assert "Python" in result.output

    def test_doctor_checks_python_version(self, cli_runner):
        """Test that doctor checks Python version."""
        result = cli_runner.invoke(cli, ["doctor"])

        assert result.exit_code == 0
        assert "Python" in result.output
        assert "3." in result.output

    def test_doctor_checks_playwright(self, cli_runner):
        """Test that doctor checks Playwright installation."""
        result = cli_runner.invoke(cli, ["doctor"])

        assert result.exit_code == 0
        assert "Playwright" in result.output

    def test_doctor_shows_status_symbols(self, cli_runner):
        """Test that doctor shows check status symbols."""
        result = cli_runner.invoke(cli, ["doctor"])

        assert result.exit_code == 0
        # Should have ✓ or ✗ symbols
        assert "✓" in result.output or "✗" in result.output or "✅" in result.output
