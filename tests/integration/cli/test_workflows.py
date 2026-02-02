"""End-to-end workflow integration tests.

This module contains end-to-end integration tests for the socialseed-e2e CLI.
These tests verify complete workflows from project initialization through
creating services and tests to running commands.
"""

import os

import pytest

pytestmark = pytest.mark.integration
from click.testing import CliRunner

from socialseed_e2e.cli import cli


class TestFullWorkflow:
    """End-to-end workflow integration tests."""

    def test_complete_project_setup(self, isolated_cli_runner, temp_dir):
        """Test complete project setup workflow."""
        # Step 1: Init project
        result = isolated_cli_runner.invoke(cli, ["init"])
        assert result.exit_code == 0

        # Step 2: Create service
        result = isolated_cli_runner.invoke(cli, ["new-service", "users-api"])
        assert result.exit_code == 0

        # Step 3: Create test
        result = isolated_cli_runner.invoke(cli, ["new-test", "login", "--service", "users-api"])
        assert result.exit_code == 0

        # Step 4: Check config
        result = isolated_cli_runner.invoke(cli, ["config"])
        assert result.exit_code == 0

        # Step 5: Run doctor
        result = isolated_cli_runner.invoke(cli, ["doctor"])
        assert result.exit_code == 0

        # Verify final state
        assert (temp_dir / "e2e.conf").exists()
        assert (temp_dir / "services" / "users-api").exists()
        assert (temp_dir / "services" / "users-api" / "modules" / "01_login_flow.py").exists()

    def test_multiple_services_workflow(self, isolated_cli_runner, temp_dir):
        """Test workflow with multiple services."""
        # Init
        isolated_cli_runner.invoke(cli, ["init"])

        # Create multiple services
        isolated_cli_runner.invoke(cli, ["new-service", "users-api"])
        isolated_cli_runner.invoke(cli, ["new-service", "auth-api"])
        isolated_cli_runner.invoke(cli, ["new-service", "orders-api"])

        # Create tests for each
        isolated_cli_runner.invoke(cli, ["new-test", "login", "--service", "users-api"])
        isolated_cli_runner.invoke(cli, ["new-test", "authenticate", "--service", "auth-api"])
        isolated_cli_runner.invoke(cli, ["new-test", "create", "--service", "orders-api"])

        # Verify all exist
        services_dir = temp_dir / "services"
        assert (services_dir / "users-api").exists()
        assert (services_dir / "auth-api").exists()
        assert (services_dir / "orders-api").exists()

    def test_project_recreation_with_force(self, isolated_cli_runner, temp_dir):
        """Test recreating project with force flag."""
        # First setup
        isolated_cli_runner.invoke(cli, ["init"])
        isolated_cli_runner.invoke(cli, ["new-service", "api"])

        # Re-init with force
        result = isolated_cli_runner.invoke(cli, ["init", "--force"])
        assert result.exit_code == 0

        # Should still have structure
        assert (temp_dir / "e2e.conf").exists()
        assert (temp_dir / "services").exists()
