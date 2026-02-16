"""Tests to verify CLI has no duplicate short flags.

This module contains tests to ensure no duplicate short flags exist
in CLI commands, which would cause UserWarning messages.
"""

import pytest

pytestmark = pytest.mark.unit


class TestCLINoDuplicateFlags:
    """Test that CLI commands don't have duplicate short flags."""

    def test_run_command_no_duplicate_flags(self):
        """Test that 'run' command has no duplicate -t flags."""
        from socialseed_e2e.cli import cli
        from click.testing import CliRunner

        runner = CliRunner()

        # This should not raise any UserWarning about duplicate flags
        result = runner.invoke(cli, ["run", "--help"])

        assert result.exit_code == 0
        assert "UserWarning" not in result.output
        # Check that -T is for trace and -t is for tag
        assert "-T, --trace" in result.output
        assert "-t, --tag" in result.output

    def test_cli_loads_without_duplicate_flag_warnings(self):
        """Test that CLI loads without any duplicate flag warnings."""
        import warnings

        # Capture all warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # Import and load CLI
            from socialseed_e2e.cli import cli
            from click.testing import CliRunner

            runner = CliRunner()
            result = runner.invoke(cli, ["--help"])

            # Check for duplicate flag warnings
            duplicate_warnings = [
                warning
                for warning in w
                if issubclass(warning.category, UserWarning)
                and "used more than once" in str(warning.message)
            ]

            assert len(duplicate_warnings) == 0, (
                f"Found duplicate flag warnings: {[str(w.message) for w in duplicate_warnings]}"
            )

    def test_all_commands_load_without_flag_warnings(self):
        """Test that all CLI commands load without duplicate flag warnings."""
        import warnings
        from socialseed_e2e.cli import cli
        from click.testing import CliRunner

        runner = CliRunner()

        # List of commands to test (main commands, not subcommands)
        commands_to_test = [
            "run",
            "init",
            "doctor",
            "config",
            "manifest",
            "search",
            "semantic-analyze",
            "perf-profile",
            "perf-report",
        ]

        for cmd in commands_to_test:
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")

                result = runner.invoke(cli, [cmd, "--help"])

                # Check for duplicate flag warnings
                duplicate_warnings = [
                    warning
                    for warning in w
                    if issubclass(warning.category, UserWarning)
                    and "used more than once" in str(warning.message)
                ]

                assert len(duplicate_warnings) == 0, (
                    f"Command '{cmd}' has duplicate flag warnings: {[str(w.message) for w in duplicate_warnings]}"
                )
