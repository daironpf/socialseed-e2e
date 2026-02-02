"""Shared fixtures for CLI integration tests.

This module contains fixtures that are shared across all CLI integration tests.
"""

import os
from pathlib import Path

import pytest
from click.testing import CliRunner


@pytest.fixture
def cli_runner():
    """Provide a CliRunner instance."""
    return CliRunner()


@pytest.fixture
def temp_dir(tmp_path):
    """Provide a temporary directory for testing."""
    return tmp_path


@pytest.fixture
def isolated_cli_runner(cli_runner, tmp_path):
    """Provide a CliRunner that runs in an isolated temp directory.

    This fixture changes the current working directory to the temp directory
    before the test and restores it after.
    """
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    yield cli_runner
    os.chdir(original_cwd)


@pytest.fixture
def initialized_project(isolated_cli_runner):
    """Provide a CLI runner with an already initialized project.

    Creates a project with 'e2e init' already executed.
    """
    from socialseed_e2e.cli import cli

    isolated_cli_runner.invoke(cli, ["init"])
    return isolated_cli_runner


@pytest.fixture
def project_with_service(initialized_project):
    """Provide a CLI runner with a project that has one service.

    Creates a project with 'users-api' service already created.
    """
    from socialseed_e2e.cli import cli

    initialized_project.invoke(cli, ["new-service", "users-api"])
    return initialized_project
