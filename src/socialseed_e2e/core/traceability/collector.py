"""Trace collector for capturing test execution interactions.

This module provides functionality to capture and store all interactions
between components during test execution.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from socialseed_e2e.core.traceability.models import (
    Component,
    Interaction,
    InteractionType,
    LogicBranch,
    LogicBranchType,
    TestTrace,
    TraceConfig,
)


class TraceCollector:
    """Collects and manages test execution traces.

    This class captures all interactions between components during test execution,
    including HTTP requests/responses, service calls, database queries, and
    logical branching decisions.

    Example:
        >>> collector = TraceCollector()
        >>> trace = collector.start_trace("test_login", "auth-service")
        >>>
        >>> # Record an interaction
        >>> collector.record_interaction(
        ...     from_component="Client",
        ...     to_component="Auth-Service",
        ...     action="POST /login",
        ...     interaction_type=InteractionType.HTTP_REQUEST,
        ...     request_data={"username": "user"}
        ... )
        >>>
        >>> # Record a logic branch
        >>> collector.record_logic_branch(
        ...     condition="response.status == 200",
        ...     decision="true",
        ...     reason="Valid credentials provided"
        ... )
        >>>
        >>> collector.end_trace("passed")
    """

    def __init__(self, config: Optional[TraceConfig] = None):
        """Initialize the trace collector.

        Args:
            config: Configuration for trace collection
        """
        self.config = config or TraceConfig()
        self._current_trace: Optional[TestTrace] = None
        self._completed_traces: List[TestTrace] = []
        self._interaction_counter: int = 0
        self._component_registry: Dict[str, Component] = {}

    def start_trace(
        self,
        test_name: str,
        service_name: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[TestTrace]:
        """Start a new test trace.

        Args:
            test_name: Name of the test
            service_name: Name of the service being tested
            metadata: Optional metadata for the trace

        Returns:
            The created TestTrace instance
        """
        if not self.config.enabled:
            return None

        trace_id = str(uuid.uuid4())
        self._current_trace = TestTrace(
            test_id=trace_id,
            test_name=test_name,
            service_name=service_name,
            start_time=datetime.now(),
            metadata=metadata or {},
        )
        self._interaction_counter = 0
        return self._current_trace

    def end_trace(
        self, status: str = "passed", error_message: Optional[str] = None
    ) -> Optional[TestTrace]:
        """End the current test trace.

        Args:
            status: Final status (passed, failed, error)
            error_message: Optional error message if failed

        Returns:
            The completed TestTrace or None if no trace was active
        """
        if not self._current_trace:
            return None

        self._current_trace.end_time = datetime.now()
        self._current_trace.status = status
        self._current_trace.error_message = error_message

        completed_trace = self._current_trace
        self._completed_traces.append(completed_trace)
        self._current_trace = None

        return completed_trace

    def register_component(
        self,
        name: str,
        component_type: str = "service",
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Component:
        """Register a component for tracking.

        Args:
            name: Component name
            component_type: Type of component (service, database, etc.)
            description: Optional description
            metadata: Optional metadata

        Returns:
            The registered Component
        """
        if name in self._component_registry:
            return self._component_registry[name]

        component = Component(
            name=name,
            type=component_type,
            description=description,
            metadata=metadata or {},
        )
        self._component_registry[name] = component

        if self._current_trace:
            self._current_trace.components.append(component)

        return component

    def record_interaction(
        self,
        from_component: str,
        to_component: str,
        action: str,
        interaction_type: InteractionType = InteractionType.HTTP_REQUEST,
        request_data: Optional[Dict[str, Any]] = None,
        response_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        duration_ms: float = 0.0,
        status: str = "success",
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Interaction]:
        """Record an interaction between components.

        Args:
            from_component: Source component name
            to_component: Target component name
            action: Action being performed (e.g., "POST /login")
            interaction_type: Type of interaction
            request_data: Optional request data
            response_data: Optional response data
            headers: Optional headers
            duration_ms: Duration in milliseconds
            status: Status (success, error, pending, warning)
            error_message: Optional error message
            metadata: Optional metadata

        Returns:
            The recorded Interaction or None if trace not active
        """
        if not self._current_trace or not self.config.enabled:
            return None

        # Register components if not already registered
        if from_component not in self._component_registry:
            self.register_component(from_component)
        if to_component not in self._component_registry:
            self.register_component(to_component)

        self._interaction_counter += 1

        # Truncate data if necessary
        request_data = self._truncate_data(request_data)
        response_data = self._truncate_data(response_data)

        interaction = Interaction(
            id=f"int_{self._interaction_counter:04d}",
            type=interaction_type,
            from_component=from_component,
            to_component=to_component,
            action=action,
            timestamp=datetime.now(),
            duration_ms=duration_ms,
            status=status,
            request_data=request_data if self.config.capture_request_body else None,
            response_data=response_data if self.config.capture_response_body else None,
            headers=headers or {} if self.config.capture_headers else {},
            error_message=error_message,
            metadata=metadata or {},
        )

        self._current_trace.interactions.append(interaction)
        return interaction

    def record_logic_branch(
        self,
        condition: str,
        decision: str,
        branch_type: LogicBranchType = LogicBranchType.CONDITIONAL,
        reason: Optional[str] = None,
        parent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[LogicBranch]:
        """Record a logical branching decision.

        Args:
            condition: The condition being evaluated
            decision: The path taken (e.g., "true", "false")
            branch_type: Type of branch
            reason: Why this branch was taken
            parent_id: Optional parent branch ID
            metadata: Optional metadata

        Returns:
            The recorded LogicBranch or None if trace not active
        """
        if not self._current_trace or not self.config.enabled:
            return None

        if not self.config.track_logic_branches:
            return None

        branch = LogicBranch(
            id=f"branch_{len(self._current_trace.logic_branches) + 1:04d}",
            type=branch_type,
            condition=condition,
            decision=decision,
            timestamp=datetime.now(),
            parent_id=parent_id,
            reason=reason,
            metadata=metadata or {},
        )

        self._current_trace.logic_branches.append(branch)
        return branch

    def record_assertion(
        self,
        assertion: str,
        passed: bool,
        expected_value: Optional[str] = None,
        actual_value: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> Optional[LogicBranch]:
        """Record an assertion result.

        Args:
            assertion: The assertion being made
            passed: Whether the assertion passed
            expected_value: Expected value
            actual_value: Actual value
            reason: Optional reason for failure

        Returns:
            The recorded LogicBranch
        """
        decision = "passed" if passed else "failed"
        full_reason = reason
        if not passed and expected_value and actual_value:
            full_reason = f"Expected: {expected_value}, Got: {actual_value}"
            if reason:
                full_reason += f" - {reason}"

        return self.record_logic_branch(
            condition=assertion,
            decision=decision,
            branch_type=LogicBranchType.ASSERTION,
            reason=full_reason,
        )

    def get_current_trace(self) -> Optional[TestTrace]:
        """Get the currently active trace.

        Returns:
            The active TestTrace or None
        """
        return self._current_trace

    def get_completed_traces(self) -> List[TestTrace]:
        """Get all completed traces.

        Returns:
            List of completed TestTrace instances
        """
        return self._completed_traces.copy()

    def get_all_traces(self) -> List[TestTrace]:
        """Get all traces including the current one if active.

        Returns:
            List of all TestTrace instances
        """
        traces = self._completed_traces.copy()
        if self._current_trace:
            traces.append(self._current_trace)
        return traces

    def clear(self) -> None:
        """Clear all traces and reset the collector."""
        self._current_trace = None
        self._completed_traces = []
        self._interaction_counter = 0
        self._component_registry = {}

    def _truncate_data(self, data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Truncate data to max size if necessary.

        Args:
            data: Data to truncate

        Returns:
            Truncated data or None
        """
        if data is None:
            return None

        # Convert to string to check size
        import json

        try:
            data_str = json.dumps(data)
            if len(data_str) > self.config.max_body_size:
                return {"_truncated": True, "_original_size": len(data_str)}
        except (TypeError, ValueError):
            pass

        return data


# Global collector instance for easy access
_global_collector: Optional[TraceCollector] = None


def get_global_collector() -> Optional[TraceCollector]:
    """Get the global trace collector instance.

    Returns:
        The global TraceCollector or None
    """
    return _global_collector


def set_global_collector(collector: TraceCollector) -> None:
    """Set the global trace collector instance.

    Args:
        collector: TraceCollector instance to set as global
    """
    global _global_collector
    _global_collector = collector


def create_collector(config: Optional[TraceConfig] = None) -> TraceCollector:
    """Create and configure a new trace collector.

    Args:
        config: Optional configuration

    Returns:
        New TraceCollector instance
    """
    return TraceCollector(config)
