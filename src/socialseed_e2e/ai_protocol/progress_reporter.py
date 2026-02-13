"""Progress Reporter for AI Agent Communication Protocol.

This module provides progress reporting capabilities for long-running operations.
"""

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from socialseed_e2e.ai_protocol.message_formats import (
    MessageHeader,
    MessageType,
    ProgressPayload,
    ProtocolMessage,
)


@dataclass
class ProgressStep:
    """A single step in a progress sequence."""

    name: str
    description: str
    weight: float = 1.0  # Relative weight of this step
    estimated_duration_seconds: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProgressState:
    """Current state of progress."""

    total_steps: int
    current_step: int
    current_step_name: str
    overall_progress: float  # 0.0 to 100.0
    step_progress: float  # 0.0 to 100.0 for current step
    status: str
    start_time: datetime
    estimated_end_time: Optional[datetime] = None
    details: Dict[str, Any] = field(default_factory=dict)


class ProgressReporter:
    """Reporter for tracking and reporting progress of operations."""

    def __init__(self, operation_id: str, total_steps: int = 1):
        """Initialize the progress reporter.

        Args:
            operation_id: Unique identifier for the operation
            total_steps: Total number of steps in the operation
        """
        self.operation_id = operation_id
        self.total_steps = total_steps
        self.current_step = 0
        self.step_progress = 0.0
        self.overall_progress = 0.0
        self.status = "initialized"
        self.start_time = datetime.utcnow()
        self.steps: List[ProgressStep] = []
        self.step_weights: List[float] = []
        self.current_step_start_time: Optional[datetime] = None
        self.callbacks: List[Callable[[ProtocolMessage], None]] = []
        self.history: List[ProgressState] = []

    def define_steps(self, steps: List[ProgressStep]) -> None:
        """Define the steps for this operation.

        Args:
            steps: List of progress steps
        """
        self.steps = steps
        self.total_steps = len(steps)
        self.step_weights = [step.weight for step in steps]
        # Normalize weights
        total_weight = sum(self.step_weights) or 1.0
        self.step_weights = [w / total_weight for w in self.step_weights]

    def register_callback(self, callback: Callable[[ProtocolMessage], None]) -> None:
        """Register a callback for progress updates.

        Args:
            callback: Function to call with progress messages
        """
        self.callbacks.append(callback)

    def start_step(self, step_name: str, details: Dict[str, Any] = None) -> None:
        """Start a new step.

        Args:
            step_name: Name of the step
            details: Additional details about the step
        """
        self.current_step += 1
        self.current_step_name = step_name
        self.step_progress = 0.0
        self.current_step_start_time = datetime.utcnow()
        self.status = f"running_{step_name}"

        # Calculate overall progress
        completed_weight = sum(self.step_weights[: self.current_step - 1])
        self.overall_progress = completed_weight * 100.0

        # Report progress
        self._report_progress(details)

    def update_progress(
        self, step_progress: float, status: str = None, details: Dict[str, Any] = None
    ) -> None:
        """Update progress for the current step.

        Args:
            step_progress: Progress within current step (0.0 to 100.0)
            status: Optional status message
            details: Additional details
        """
        self.step_progress = max(0.0, min(100.0, step_progress))

        if status:
            self.status = status

        # Calculate overall progress
        completed_weight = sum(self.step_weights[: self.current_step - 1])
        current_weight = (
            self.step_weights[self.current_step - 1]
            if self.current_step <= len(self.step_weights)
            else 0
        )
        self.overall_progress = (
            completed_weight + current_weight * (self.step_progress / 100.0)
        ) * 100.0

        # Report progress
        self._report_progress(details)

    def complete_step(self, details: Dict[str, Any] = None) -> None:
        """Mark the current step as complete.

        Args:
            details: Additional details about completion
        """
        self.step_progress = 100.0

        # Calculate overall progress
        completed_weight = sum(self.step_weights[: self.current_step])
        self.overall_progress = completed_weight * 100.0

        # Save state to history
        self._save_state()

        # Report progress
        self._report_progress(details)

    def complete_operation(
        self, message: str = "Operation completed successfully"
    ) -> None:
        """Mark the entire operation as complete.

        Args:
            message: Completion message
        """
        self.current_step = self.total_steps
        self.step_progress = 100.0
        self.overall_progress = 100.0
        self.status = "completed"

        # Report final progress
        self._report_progress({"completion_message": message})

    def fail_operation(
        self, error_message: str, details: Dict[str, Any] = None
    ) -> None:
        """Mark the operation as failed.

        Args:
            error_message: Error message
            details: Additional error details
        """
        self.status = "failed"

        # Report failure as progress
        error_details = details or {}
        error_details["error"] = error_message
        self._report_progress(error_details)

    def _calculate_estimated_remaining(self) -> Optional[int]:
        """Calculate estimated remaining time in seconds."""
        if not self.current_step_start_time or self.step_progress == 0:
            return None

        elapsed = (datetime.utcnow() - self.start_time).total_seconds()

        if self.overall_progress > 0:
            estimated_total = elapsed / (self.overall_progress / 100.0)
            remaining = estimated_total - elapsed
            return int(remaining)

        return None

    def _save_state(self) -> None:
        """Save current state to history."""
        state = ProgressState(
            total_steps=self.total_steps,
            current_step=self.current_step,
            current_step_name=getattr(self, "current_step_name", ""),
            overall_progress=self.overall_progress,
            step_progress=self.step_progress,
            status=self.status,
            start_time=self.start_time,
            estimated_end_time=None,
        )
        self.history.append(state)

    def _report_progress(self, details: Dict[str, Any] = None) -> None:
        """Report progress to all callbacks.

        Args:
            details: Additional details to include
        """
        if not self.callbacks:
            return

        # Create progress message
        header = MessageHeader(
            message_id=f"{self.operation_id}_{int(time.time() * 1000)}",
            message_type=MessageType.PROGRESS,
            correlation_id=self.operation_id,
        )

        payload = ProgressPayload(
            progress_percent=self.overall_progress,
            status=self.status,
            current_step=getattr(
                self, "current_step_name", f"Step {self.current_step}"
            ),
            total_steps=self.total_steps,
            current_step_number=self.current_step,
            estimated_remaining_seconds=self._calculate_estimated_remaining(),
            details=details or {},
        )

        message = ProtocolMessage(header=header, payload=payload)

        # Send to all callbacks
        for callback in self.callbacks:
            try:
                callback(message)
            except Exception:
                # Don't let callback errors stop progress
                pass

    def get_progress_summary(self) -> Dict[str, Any]:
        """Get a summary of current progress.

        Returns:
            Progress summary dictionary
        """
        elapsed = (datetime.utcnow() - self.start_time).total_seconds()

        return {
            "operation_id": self.operation_id,
            "total_steps": self.total_steps,
            "current_step": self.current_step,
            "step_name": getattr(self, "current_step_name", ""),
            "overall_progress": self.overall_progress,
            "step_progress": self.step_progress,
            "status": self.status,
            "elapsed_seconds": elapsed,
            "estimated_remaining_seconds": self._calculate_estimated_remaining(),
            "is_complete": self.overall_progress >= 100.0,
        }

    def create_progress_message(self) -> ProtocolMessage:
        """Create a progress protocol message.

        Returns:
            Progress message
        """
        header = MessageHeader(
            message_id=f"{self.operation_id}_{int(time.time() * 1000)}",
            message_type=MessageType.PROGRESS,
            correlation_id=self.operation_id,
        )

        payload = ProgressPayload(
            progress_percent=self.overall_progress,
            status=self.status,
            current_step=getattr(
                self, "current_step_name", f"Step {self.current_step}"
            ),
            total_steps=self.total_steps,
            current_step_number=self.current_step,
            estimated_remaining_seconds=self._calculate_estimated_remaining(),
        )

        return ProtocolMessage(header=header, payload=payload)


class MultiOperationProgressTracker:
    """Track progress of multiple concurrent operations."""

    def __init__(self):
        """Initialize the multi-operation tracker."""
        self.operations: Dict[str, ProgressReporter] = {}
        self.callbacks: List[Callable[[str, ProtocolMessage], None]] = []

    def register_operation(
        self, operation_id: str, total_steps: int = 1
    ) -> ProgressReporter:
        """Register a new operation.

        Args:
            operation_id: Unique operation identifier
            total_steps: Total steps in operation

        Returns:
            Progress reporter for the operation
        """
        reporter = ProgressReporter(operation_id, total_steps)

        # Wrap callback to include operation_id
        def callback_wrapper(message: ProtocolMessage):
            for cb in self.callbacks:
                try:
                    cb(operation_id, message)
                except Exception:
                    pass

        reporter.register_callback(callback_wrapper)
        self.operations[operation_id] = reporter

        return reporter

    def register_callback(
        self, callback: Callable[[str, ProtocolMessage], None]
    ) -> None:
        """Register a callback for all operations.

        Args:
            callback: Function(operation_id, message) to call
        """
        self.callbacks.append(callback)

    def get_operation(self, operation_id: str) -> Optional[ProgressReporter]:
        """Get a registered operation.

        Args:
            operation_id: Operation identifier

        Returns:
            Progress reporter or None
        """
        return self.operations.get(operation_id)

    def get_all_progress(self) -> Dict[str, Dict[str, Any]]:
        """Get progress summary for all operations.

        Returns:
            Dictionary mapping operation_id to progress summary
        """
        return {
            op_id: reporter.get_progress_summary()
            for op_id, reporter in self.operations.items()
        }

    def get_overall_progress(self) -> float:
        """Get overall progress across all operations.

        Returns:
            Average progress percentage
        """
        if not self.operations:
            return 0.0

        total = sum(r.overall_progress for r in self.operations.values())
        return total / len(self.operations)

    def remove_operation(self, operation_id: str) -> None:
        """Remove a completed operation.

        Args:
            operation_id: Operation to remove
        """
        if operation_id in self.operations:
            del self.operations[operation_id]
