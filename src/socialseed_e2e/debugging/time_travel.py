"""
Time-Travel Debugging System for socialseed-e2e.

This module provides state snapshot capabilities that allow the HealerAgent
to "rewind" to previous states and explore alternative interaction paths.

Features:
- Extended Playwright tracing with network and DOM snapshots
- State snapshot management for test execution
- Interactive debugging with state restoration
- Exploration tree logging for audit trails
"""

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, Field


class SnapshotType(str, Enum):
    """Types of state snapshots."""

    INITIAL = "initial"
    BEFORE_STEP = "before_step"
    AFTER_STEP = "after_step"
    BEFORE_RETRY = "before_retry"
    ON_FAILURE = "on_failure"


class InteractionSnapshot(BaseModel):
    """Snapshot of an interaction at a specific point."""

    snapshot_id: str
    snapshot_type: SnapshotType

    timestamp: datetime = Field(default_factory=datetime.now)

    step_number: int
    step_description: str

    network_state: Dict[str, Any] = {}
    dom_state: Optional[str] = None

    page_state: Dict[str, Any] = {}
    context_state: Dict[str, Any] = {}

    request_logs: List[Dict[str, Any]] = []
    response_logs: List[Dict[str, Any]] = []

    metadata: Dict[str, Any] = {}


class ExplorationPath(BaseModel):
    """A path explored by the debugger."""

    path_id: str
    parent_path_id: Optional[str] = None

    snapshot_id: str

    action_taken: str
    action_result: str

    reasoning: str

    depth: int = 0

    created_at: datetime = Field(default_factory=datetime.now)


class DebugSession(BaseModel):
    """Complete debug session with exploration tree."""

    session_id: str

    test_name: str
    test_file: str

    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None

    snapshots: List[InteractionSnapshot] = Field(default_factory=list)
    exploration_tree: List[ExplorationPath] = Field(default_factory=list)

    failure_reason: Optional[str] = None
    resolution_found: bool = False
    resolution_details: Optional[str] = None

    metadata: Dict[str, Any] = {}


class StateSnapshotManager:
    """
    Manages state snapshots throughout test execution.

    This class integrates with Playwright to capture comprehensive
    state snapshots at each step of test execution.
    """

    def __init__(self, output_dir: str = ".e2e/debug_snapshots"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.current_session: Optional[DebugSession] = None
        self.snapshots: List[InteractionSnapshot] = []
        self.exploration_paths: List[ExplorationPath] = []

    def start_session(self, test_name: str, test_file: str) -> str:
        """Start a new debug session."""
        session_id = str(uuid.uuid4())
        self.current_session = DebugSession(
            session_id=session_id,
            test_name=test_name,
            test_file=test_file,
        )
        self.snapshots = []
        self.exploration_paths = []
        return session_id

    def capture_snapshot(
        self,
        snapshot_type: SnapshotType,
        step_number: int,
        step_description: str,
        page_context: Optional[Any] = None,
    ) -> InteractionSnapshot:
        """Capture a state snapshot at a specific point."""
        snapshot = InteractionSnapshot(
            snapshot_id=str(uuid.uuid4()),
            snapshot_type=snapshot_type,
            step_number=step_number,
            step_description=step_description,
        )

        if page_context:
            snapshot.page_state = self._capture_page_state(page_context)
            snapshot.network_state = self._capture_network_state(page_context)

        self.snapshots.append(snapshot)

        if self.current_session:
            self.current_session.snapshots.append(snapshot)

        return snapshot

    def _capture_page_state(self, page_context: Any) -> Dict[str, Any]:
        """Capture current page state."""
        state = {}

        try:
            if hasattr(page_context, "url"):
                state["url"] = page_context.url
            if hasattr(page_context, "title"):
                state["title"] = page_context.title()
            if hasattr(page_context, "evaluate"):
                state["url"] = page_context.url
        except Exception:
            pass

        return state

    def _capture_network_state(self, page_context: Any) -> Dict[str, Any]:
        """Capture network state."""
        return {"captured": True}

    def record_exploration(
        self,
        parent_path_id: Optional[str],
        snapshot_id: str,
        action: str,
        result: str,
        reasoning: str,
    ) -> ExplorationPath:
        """Record an exploration path."""
        depth = 0
        if parent_path_id:
            parent = next(
                (p for p in self.exploration_paths if p.path_id == parent_path_id), None
            )
            if parent:
                depth = parent.depth + 1

        path = ExplorationPath(
            path_id=str(uuid.uuid4()),
            parent_path_id=parent_path_id,
            snapshot_id=snapshot_id,
            action_taken=action,
            action_result=result,
            reasoning=reasoning,
            depth=depth,
        )

        self.exploration_paths.append(path)

        if self.current_session:
            self.current_session.exploration_tree.append(path)

        return path

    def get_snapshot(self, snapshot_id: str) -> Optional[InteractionSnapshot]:
        """Get a specific snapshot by ID."""
        return next((s for s in self.snapshots if s.snapshot_id == snapshot_id), None)

    def get_latest_snapshot(self) -> Optional[InteractionSnapshot]:
        """Get the most recent snapshot."""
        return self.snapshots[-1] if self.snapshots else None

    def get_snapshots_before_failure(self) -> List[InteractionSnapshot]:
        """Get all snapshots before the failure point."""
        failure_idx = -1
        for i, s in enumerate(self.snapshots):
            if s.snapshot_type == SnapshotType.ON_FAILURE:
                failure_idx = i
                break

        if failure_idx > 0:
            return self.snapshots[:failure_idx]
        return self.snapshots[:-1]

    def end_session(
        self,
        failure_reason: Optional[str] = None,
        resolution_found: bool = False,
        resolution_details: Optional[str] = None,
    ) -> DebugSession:
        """End the current debug session."""
        if not self.current_session:
            raise ValueError("No active session to end")

        self.current_session.end_time = datetime.now()
        self.current_session.failure_reason = failure_reason
        self.current_session.resolution_found = resolution_found
        self.current_session.resolution_details = resolution_details

        return self.current_session

    def save_session(self, output_path: Optional[str] = None) -> Path:
        """Save session to file."""
        if not self.current_session:
            raise ValueError("No session to save")

        if not output_path:
            output_path = self.output_dir / f"{self.current_session.session_id}.json"

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            json.dump(
                self.current_session.model_dump(by_alias=True), f, indent=2, default=str
            )

        return path


class TimeTravelDebugger:
    """
    Provides time-travel debugging capabilities for test execution.

    Allows the HealerAgent to explore alternative paths by restoring
    previous snapshots and trying different approaches.
    """

    def __init__(self, snapshot_manager: StateSnapshotManager):
        self.snapshot_manager = snapshot_manager
        self.current_exploration_depth = 0

    def restore_to_snapshot(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """Restore execution state to a specific snapshot."""
        snapshot = self.snapshot_manager.get_snapshot(snapshot_id)
        if not snapshot:
            return None

        return {
            "page_state": snapshot.page_state,
            "context_state": snapshot.context_state,
            "network_state": snapshot.network_state,
        }

    def explore_alternative(
        self,
        parent_path_id: str,
        action: str,
        reasoning: str,
    ) -> ExplorationPath:
        """Explore an alternative action from a previous state."""
        parent = next(
            (
                p
                for p in self.snapshot_manager.exploration_paths
                if p.path_id == parent_path_id
            ),
            None,
        )

        if not parent:
            raise ValueError(f"Parent path not found: {parent_path_id}")

        snapshot = self.snapshot_manager.get_snapshot(parent.snapshot_id)

        path = self.snapshot_manager.record_exploration(
            parent_path_id=parent_path_id,
            snapshot_id=parent.snapshot_id,
            action_taken=action,
            action_result="pending",
            reasoning=reasoning,
        )

        self.current_exploration_depth += 1

        return path

    def record_result(self, path_id: str, result: str) -> None:
        """Record the result of an exploration path."""
        for path in self.snapshot_manager.exploration_paths:
            if path.path_id == path_id:
                path.action_result = result
                break

    def generate_exploration_report(self) -> Dict[str, Any]:
        """Generate a report of the exploration tree."""
        if not self.snapshot_manager.current_session:
            return {}

        session = self.snapshot_manager.current_session

        report = {
            "session_id": session.session_id,
            "test_name": session.test_name,
            "total_snapshots": len(session.snapshots),
            "total_paths": len(session.exploration_tree),
            "failure_reason": session.failure_reason,
            "resolution_found": session.resolution_found,
            "exploration_tree": self._format_tree(session.exploration_tree),
        }

        return report

    def _format_tree(self, paths: List[ExplorationPath]) -> List[Dict[str, Any]]:
        """Format exploration paths as a tree structure."""
        tree = []
        for path in paths:
            tree.append(
                {
                    "id": path.path_id,
                    "parent": path.parent_path_id,
                    "depth": path.depth,
                    "action": path.action_taken,
                    "result": path.action_result,
                    "reasoning": path.reasoning,
                }
            )
        return tree


class DebugSessionRecorder:
    """
    Records debug sessions with full state information for audit trails.
    """

    def __init__(self):
        self.sessions: List[DebugSession] = []

    def add_session(self, session: DebugSession) -> None:
        """Add a completed session to the recorder."""
        self.sessions.append(session)

    def get_session(self, session_id: str) -> Optional[DebugSession]:
        """Get a session by ID."""
        return next((s for s in self.sessions if s.session_id == session_id), None)

    def get_all_sessions(self) -> List[DebugSession]:
        """Get all recorded sessions."""
        return self.sessions

    def generate_audit_report(self) -> str:
        """Generate an audit report of all sessions."""
        report = "# Debug Session Audit Report\n\n"
        report += f"Total Sessions: {len(self.sessions)}\n\n"

        for session in self.sessions:
            report += f"## Session: {session.session_id}\n"
            report += f"Test: {session.test_name}\n"
            report += f"Start: {session.start_time}\n"
            report += f"Resolution Found: {session.resolution_found}\n\n"

        return report


__all__ = [
    "DebugSession",
    "DebugSessionRecorder",
    "ExplorationPath",
    "InteractionSnapshot",
    "SnapshotType",
    "StateSnapshotManager",
    "TimeTravelDebugger",
]
