"""Unit tests for watch command (Phase 2)."""

import pytest

from socialseed_e2e.commands.watch_cmd import WatchCommand, WatchPresenter


class TestWatchCommand:
    """Tests for WatchCommand."""

    def test_watch_command_init_default(self):
        """Test WatchCommand initialization with defaults."""
        command = WatchCommand()
        
        assert command.sync_index is False
        assert command.service is None

    def test_watch_command_init_with_sync_index(self):
        """Test WatchCommand initialization with sync_index."""
        command = WatchCommand(sync_index=True)
        
        assert command.sync_index is True

    def test_watch_command_init_with_false(self):
        """Test WatchCommand initialization with sync_index=False."""
        command = WatchCommand(sync_index=False)
        
        assert command.sync_index is False


class TestWatchPresenter:
    """Tests for WatchPresenter."""

    def test_display_start_message(self, tmp_path, capsys):
        """Test start message display."""
        manifest_path = tmp_path / "manifest.json"
        
        WatchPresenter.display_start_message("auth-service", manifest_path)
        
        captured = capsys.readouterr()
        assert "auth-service" in captured.out
        assert "manifest" in captured.out.lower()

    def test_display_stop_message(self, capsys):
        """Test stop message display."""
        WatchPresenter.display_stop_message()
        
        captured = capsys.readouterr()
        assert "stopped" in captured.out.lower() or "👋" in captured.out

    def test_display_error(self, capsys):
        """Test error message display."""
        WatchPresenter.display_error("Test error message")
        
        captured = capsys.readouterr()
        assert "Error" in captured.out or "error" in captured.out.lower()
        assert "Test error message" in captured.out

    def test_display_service_required(self, capsys):
        """Test service required message."""
        WatchPresenter.display_service_required()
        
        captured = capsys.readouterr()
        assert "required" in captured.out.lower() or "Usage" in captured.out

    def test_display_manifest_not_found(self, tmp_path, capsys):
        """Test manifest not found message."""
        manifest_path = tmp_path / "manifest.json"
        
        WatchPresenter.display_manifest_not_found(manifest_path, "auth-service")
        
        captured = capsys.readouterr()
        assert "not found" in captured.out.lower() or "manifest" in captured.out.lower()
        assert "auth-service" in captured.out


class TestWatchCommandExecution:
    """Tests for WatchCommand execution."""

    def test_execute_without_service_name(self, capsys):
        """Test execute returns error when no service name provided."""
        command = WatchCommand()
        
        result = command.execute(".")
        
        assert result == 1
        captured = capsys.readouterr()
        assert "required" in captured.out.lower()
