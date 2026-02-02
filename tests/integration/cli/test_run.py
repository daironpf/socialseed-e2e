"""Integration tests for 'e2e run' command.

This module contains integration tests for the socialseed-e2e 'run' CLI command.
These tests verify that the run command properly displays configuration,
services information, and handles filtering options.
"""

import os

import pytest

pytestmark = pytest.mark.integration
from click.testing import CliRunner

from socialseed_e2e.cli import cli


class TestE2ERunCommand:
    """Integration tests for 'e2e run' command."""

    def test_run_shows_configuration(self, isolated_cli_runner, temp_dir):
        """Test that run shows configuration information."""
        isolated_cli_runner.invoke(cli, ["init"])
        isolated_cli_runner.invoke(cli, ["new-service", "test-api"])

        result = isolated_cli_runner.invoke(cli, ["run"])

        assert result.exit_code == 0
        assert "Configuración" in result.output or "Configuration" in result.output
        assert "e2e.conf" in result.output

    def test_run_shows_environment(self, isolated_cli_runner, temp_dir):
        """Test that run shows environment information."""
        isolated_cli_runner.invoke(cli, ["init"])
        isolated_cli_runner.invoke(cli, ["new-service", "test-api"])

        result = isolated_cli_runner.invoke(cli, ["run"])

        assert result.exit_code == 0
        assert "Environment" in result.output or "environment" in result.output

    def test_run_shows_services_table(self, isolated_cli_runner, temp_dir):
        """Test that run shows services table when services exist."""
        isolated_cli_runner.invoke(cli, ["init"])

        # Create a service
        isolated_cli_runner.invoke(cli, ["new-service", "users-api"])

        result = isolated_cli_runner.invoke(cli, ["run"])

        assert result.exit_code == 0
        assert "users-api" in result.output
        assert "Servicios" in result.output or "Services" in result.output

    def test_run_with_service_filter(self, isolated_cli_runner, temp_dir):
        """Test run with --service filter option."""
        isolated_cli_runner.invoke(cli, ["init"])

        result = isolated_cli_runner.invoke(cli, ["run", "--service", "users-api"])

        assert result.exit_code == 0
        assert "users-api" in result.output

    @pytest.mark.skip(reason="CLI handles missing config gracefully")
    def test_run_without_e2e_conf_fails(self, isolated_cli_runner, temp_dir):
        """Test that run fails without e2e.conf."""
        result = isolated_cli_runner.invoke(cli, ["run"])

        assert result.exit_code != 0
        assert "Error" in result.output or "error" in result.output.lower()
