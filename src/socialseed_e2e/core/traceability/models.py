"""Models for visual traceability and sequence diagrams.

This module provides data models for capturing test execution traces,
interactions between components, and logical branching decisions.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional


class InteractionType(Enum):
    """Type of interaction between components."""

    HTTP_REQUEST = auto()
    HTTP_RESPONSE = auto()
    SERVICE_CALL = auto()
    DATABASE_QUERY = auto()
    CACHE_ACCESS = auto()
    MESSAGE_QUEUE = auto()
    AUTHENTICATION = auto()
    VALIDATION = auto()
    TRANSFORMATION = auto()
    EXTERNAL_API = auto()


class LogicBranchType(Enum):
    """Type of logical branch decision."""

    CONDITIONAL = auto()
    LOOP = auto()
    TRY_CATCH = auto()
    ASSERTION = auto()
    VALIDATION = auto()
    ERROR_HANDLING = auto()


@dataclass
class Component:
    """Represents a system component (service, database, etc.)."""

    name: str
    type: str = "service"  # service, database, cache, gateway, client, external
    description: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Interaction:
    """Represents an interaction between components."""

    id: str
    type: InteractionType
    from_component: str
    to_component: str
    action: str
    timestamp: datetime
    duration_ms: float = 0.0
    status: str = "pending"  # pending, success, error, warning
    request_data: Optional[Dict[str, Any]] = None
    response_data: Optional[Dict[str, Any]] = None
    headers: Dict[str, str] = field(default_factory=dict)
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LogicBranch:
    """Represents a logical decision point with branching."""

    id: str
    type: LogicBranchType
    condition: str
    decision: str  # The path taken (e.g., "true", "false", "catch")
    timestamp: datetime
    parent_id: Optional[str] = None
    reason: Optional[str] = None  # Why this branch was taken
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestTrace:
    """Complete trace of a test execution."""

    test_id: str
    test_name: str
    service_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    components: List[Component] = field(default_factory=list)
    interactions: List[Interaction] = field(default_factory=list)
    logic_branches: List[LogicBranch] = field(default_factory=list)
    status: str = "running"  # running, passed, failed, error
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_duration_ms(self) -> float:
        """Calculate total test duration in milliseconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return 0.0

    def get_interactions_by_component(self, component_name: str) -> List[Interaction]:
        """Get all interactions involving a specific component."""
        return [
            i
            for i in self.interactions
            if i.from_component == component_name or i.to_component == component_name
        ]

    def get_logic_path(self) -> List[LogicBranch]:
        """Get the complete logical path taken during test execution."""
        return sorted(self.logic_branches, key=lambda x: x.timestamp)


@dataclass
class SequenceDiagram:
    """Generated sequence diagram data."""

    title: str
    format: str  # mermaid, plantuml
    content: str
    components: List[str]
    interactions_count: int
    generated_at: datetime


@dataclass
class LogicFlow:
    """Visual representation of logic flow."""

    title: str
    branches: List[LogicBranch]
    flow_description: str
    decision_points: int


@dataclass
class TraceReport:
    """Complete traceability report for one or more tests."""

    report_id: str
    generated_at: datetime
    traces: List[TestTrace]
    sequence_diagrams: List[SequenceDiagram] = field(default_factory=list)
    logic_flows: List[LogicFlow] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)

    def get_total_interactions(self) -> int:
        """Get total number of interactions across all traces."""
        return sum(len(t.interactions) for t in self.traces)

    def get_total_components(self) -> int:
        """Get total unique components across all traces."""
        components = set()
        for trace in self.traces:
            for comp in trace.components:
                components.add(comp.name)
        return len(components)

    def get_success_rate(self) -> float:
        """Calculate success rate of all traces."""
        if not self.traces:
            return 0.0
        passed = sum(1 for t in self.traces if t.status == "passed")
        return (passed / len(self.traces)) * 100


@dataclass
class TraceConfig:
    """Configuration for trace collection."""

    enabled: bool = True
    capture_request_body: bool = True
    capture_response_body: bool = True
    max_body_size: int = 10000
    capture_headers: bool = True
    track_logic_branches: bool = True
    generate_sequence_diagrams: bool = True
    generate_logic_flows: bool = True
    output_format: str = "mermaid"  # mermaid, plantuml, both
    include_timestamps: bool = True
    include_duration: bool = True
