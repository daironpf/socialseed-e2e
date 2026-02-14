"""Rich Terminal User Interface (TUI) for SocialSeed E2E.

This module provides an interactive terminal interface for power users
who want more interactivity than a standard CLI but prefer staying in
the terminal.

Usage:
    e2e tui                    # Launch TUI
    e2e tui --config ./e2e.conf  # Launch with specific config
"""

from socialseed_e2e.tui.app import TuiApp

__all__ = ["TuiApp"]
