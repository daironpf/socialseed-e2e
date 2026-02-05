"""Integration tests for 'e2e new-test' command.

This module contains integration tests for the socialseed-e2e 'new-test' CLI command.
These tests verify that the new-test command properly creates test module files
with correct content and automatic sequential numbering.
"""

import os

import pytest

pytestmark = pytest.mark.integration
from click.testing import CliRunner

from socialseed_e2e.cli import cli


class TestE2ENewTestCommand:
    """Integration tests for 'e2e new-test' command."""

    def test_new_test_creates_test_file(self, isolated_cli_runner, temp_dir):
        """Test that new-test creates a test file."""
        # Setup
        isolated_cli_runner.invoke(cli, ["init"])

        isolated_cli_runner.invoke(cli, ["new-service", "users-api"])

        result = isolated_cli_runner.invoke(cli, ["new-test", "login", "--service", "users-api"])

        assert result.exit_code == 0

        test_file = temp_dir / "services" / "users-api" / "modules" / "01_login_flow.py"
        assert test_file.exists()

    def test_new_test_automatic_numbering(self, isolated_cli_runner, temp_dir):
        """Test that new-test automatically numbers tests sequentially."""
        isolated_cli_runner.invoke(cli, ["init"])

        isolated_cli_runner.invoke(cli, ["new-service", "users-api"])

        # Create first test
        isolated_cli_runner.invoke(cli, ["new-test", "login", "--service", "users-api"])

        # Create second test
        isolated_cli_runner.invoke(cli, ["new-test", "logout", "--service", "users-api"])

        # Create third test
        isolated_cli_runner.invoke(cli, ["new-test", "register", "--service", "users-api"])

        modules_dir = temp_dir / "services" / "users-api" / "modules"

        assert (modules_dir / "01_login_flow.py").exists()
        assert (modules_dir / "02_logout_flow.py").exists()
        assert (modules_dir / "03_register_flow.py").exists()

    def test_new_test_file_content(self, isolated_cli_runner, temp_dir):
        """Test that new-test creates file with correct content."""
        isolated_cli_runner.invoke(cli, ["init"])

        isolated_cli_runner.invoke(cli, ["new-service", "users-api"])

        result = isolated_cli_runner.invoke(
            cli,
            [
                "new-test",
                "login",
                "--service",
                "users-api",
                "--description",
                "User login flow test",
            ],
        )

        assert result.exit_code == 0

        test_file = temp_dir / "services" / "users-api" / "modules" / "01_login_flow.py"
        content = test_file.read_text()

        assert "def run" in content
        assert "login" in content
        assert "User login flow test" in content
        assert "UsersApiPage" in content

    def test_new_test_outside_project_fails(self, isolated_cli_runner, temp_dir):
        """Test that new-test fails outside an E2E project."""
        result = isolated_cli_runner.invoke(cli, ["new-test", "login", "--service", "users-api"])

        assert result.exit_code != 0

    def test_new_test_nonexistent_service_fails(self, isolated_cli_runner, temp_dir):
        """Test that new-test fails for nonexistent service."""
        isolated_cli_runner.invoke(cli, ["init"])

        result = isolated_cli_runner.invoke(cli, ["new-test", "login", "--service", "nonexistent"])

        assert result.exit_code != 0
        assert any(
            word in result.output.lower() for word in ["no existe", "not found", "does not exist"]
        )
