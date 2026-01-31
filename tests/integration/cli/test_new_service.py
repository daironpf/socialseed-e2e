"""Integration tests for 'e2e new-service' command.

This module contains integration tests for the socialseed-e2e 'new-service' CLI command.
These tests verify that the new-service command properly creates service structures
with pages, configurations, and schemas.
"""

import os
import pytest
from click.testing import CliRunner

from socialseed_e2e.cli import cli


class TestE2ENewServiceCommand:
    """Integration tests for 'e2e new-service' command."""

    def test_new_service_creates_structure(self, isolated_cli_runner, temp_dir):
        """Test that new-service creates the expected file structure."""
        # First init a project
        isolated_cli_runner.invoke(cli, ['init'])
        
        result = isolated_cli_runner.invoke(cli, ['new-service', 'users-api'])
        
        assert result.exit_code == 0
        
        service_dir = temp_dir / "services" / "users-api"
        assert service_dir.exists()
        assert (service_dir / "modules").exists()
        assert (service_dir / "__init__.py").exists()

    def test_new_service_creates_service_page(self, isolated_cli_runner, temp_dir):
        """Test that new-service creates service page file."""
        isolated_cli_runner.invoke(cli, ['init'])
        
        result = isolated_cli_runner.invoke(cli, ['new-service', 'users-api'])
        
        assert result.exit_code == 0
        
        page_file = temp_dir / "services" / "users-api" / "users_api_page.py"
        assert page_file.exists()
        
        content = page_file.read_text()
        assert "class UsersApiPage" in content
        assert "users-api" in content

    def test_new_service_creates_config(self, isolated_cli_runner, temp_dir):
        """Test that new-service creates config file."""
        isolated_cli_runner.invoke(cli, ['init'])
        
        result = isolated_cli_runner.invoke(cli, ['new-service', 'users-api'])
        
        assert result.exit_code == 0
        
        config_file = temp_dir / "services" / "users-api" / "config.py"
        assert config_file.exists()
        
        content = config_file.read_text()
        assert "get_users_api_config" in content

    def test_new_service_creates_data_schema(self, isolated_cli_runner, temp_dir):
        """Test that new-service creates data_schema file."""
        isolated_cli_runner.invoke(cli, ['init'])
        
        result = isolated_cli_runner.invoke(cli, ['new-service', 'users-api'])
        
        assert result.exit_code == 0
        
        schema_file = temp_dir / "services" / "users-api" / "data_schema.py"
        assert schema_file.exists()
        
        content = schema_file.read_text()
        assert "class UsersApiDTO" in content

    def test_new_service_updates_e2e_conf(self, isolated_cli_runner, temp_dir):
        """Test that new-service updates e2e.conf with service config."""
        isolated_cli_runner.invoke(cli, ['init'])
        
        result = isolated_cli_runner.invoke(cli, ['new-service', 'users-api'])
        
        assert result.exit_code == 0
        
        config_file = temp_dir / "e2e.conf"
        content = config_file.read_text()
        assert "users-api:" in content
        assert "base_url: http://localhost:8080" in content

    def test_new_service_with_custom_base_url(self, isolated_cli_runner, temp_dir):
        """Test new-service with custom base URL."""
        isolated_cli_runner.invoke(cli, ['init'])
        
        result = isolated_cli_runner.invoke(cli, [
            'new-service', 'users-api',
            '--base-url', 'https://api.example.com'
        ])
        
        assert result.exit_code == 0
        
        config_file = temp_dir / "e2e.conf"
        content = config_file.read_text()
        assert "base_url: https://api.example.com" in content

    def test_new_service_outside_project_fails(self, isolated_cli_runner, temp_dir):
        """Test that new-service fails outside an E2E project."""
        result = isolated_cli_runner.invoke(cli, ['new-service', 'users-api'])
        
        assert result.exit_code != 0
        assert "e2e.conf" in result.output or "not found" in result.output.lower()
