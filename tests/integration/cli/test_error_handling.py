"""Integration tests for CLI error handling.

This module contains integration tests for error handling in the socialseed-e2e CLI.
These tests verify that the CLI properly handles invalid commands, missing arguments,
and displays appropriate error messages.
"""

import sys
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.integration
from click.testing import CliRunner

from socialseed_e2e.cli import cli, main


class TestCLIErrorHandling:
    """Integration tests for CLI error handling."""

    def test_invalid_command_shows_error(self, cli_runner):
        """Test that invalid command shows error."""
        result = cli_runner.invoke(cli, ["invalid-command"])

        assert result.exit_code != 0
        assert (
            "Error" in result.output
            or "No such command" in result.output
            or "Usage:" in result.output
        )

    def test_missing_argument_shows_error(self, cli_runner):
        """Test that missing argument shows error."""
        result = cli_runner.invoke(cli, ["new-service"])

        assert result.exit_code != 0
        assert (
            "Usage:" in result.output
            or "Error" in result.output
            or "argument" in result.output.lower()
        )

    def test_main_entry_point(self):
        """Test main entry point."""
        with patch.object(sys, "argv", ["e2e", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 0

    def test_cli_version(self, cli_runner):
        """Test CLI version display."""
        result = cli_runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert "socialseed-e2e" in result.output

    def test_cli_help(self, cli_runner):
        """Test CLI help display."""
        result = cli_runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "socialseed-e2e" in result.output
        assert "Commands:" in result.output
        assert "init" in result.output
        assert "new-service" in result.output
        assert "new-test" in result.output
        assert "run" in result.output
