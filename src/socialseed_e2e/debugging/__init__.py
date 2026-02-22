"""
Debugging Module for socialseed-e2e.

Provides debugging capabilities including:
- Time-Travel Debugging with state snapshots
- Interactive debugging with state restoration
- Exploration tree logging for audit trails

Usage:
    >>> from socialseed_e2e.debugging import StateSnapshotManager, TimeTravelDebugger
    >>>
    >>> # Start debug session
    >>> manager = StateSnapshotManager()
    >>> session_id = manager.start_session("test_login", "tests/login.py")
    >>>
    >>> # Capture snapshots during test
    >>> snapshot = manager.capture_snapshot(
    ...     SnapshotType.BEFORE_STEP,
    ...     step_number=1,
    ...     step_description="Click login button"
    ... )
    >>>
    >>> # Explore alternative paths
    >>> debugger = TimeTravelDebugger(manager)
    >>> path = debugger.explore_alternative(
    ...     parent_path_id="...",
    ...     action="Try CSS selector instead of XPath",
    ...     reasoning="XPath failed, try alternative"
    ... )
"""

from socialseed_e2e.debugging.time_travel import (
    DebugSession,
    DebugSessionRecorder,
    ExplorationPath,
    InteractionSnapshot,
    SnapshotType,
    StateSnapshotManager,
    TimeTravelDebugger,
)

__all__ = [
    "DebugSession",
    "DebugSessionRecorder",
    "ExplorationPath",
    "InteractionSnapshot",
    "SnapshotType",
    "StateSnapshotManager",
    "TimeTravelDebugger",
]
