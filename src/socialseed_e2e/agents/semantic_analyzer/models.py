"""Models for Semantic Regression & Logic Drift Detection.

Data models representing intent baselines, state snapshots, drift detections,
and comprehensive reports.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional


class DriftType(Enum):
    """Types of semantic drift that can be detected."""

    BEHAVIORAL = auto()  # Behavior differs from intent
    RELATIONSHIP = auto()  # Entity relationships changed
    STATE_TRANSITION = auto()  # State machine transitions incorrect
    VALIDATION_LOGIC = auto()  # Validation rules changed
    BUSINESS_RULE = auto()  # Core business logic changed
    DATA_INTEGRITY = auto()  # Data consistency issues
    SIDE_EFFECT = auto()  # Unexpected side effects
    MISSING_FUNCTIONALITY = auto()  # Expected behavior not present


class DriftSeverity(Enum):
    """Severity levels for detected drift."""

    CRITICAL = "critical"  # Breaks core business functionality
    HIGH = "high"  # Significant deviation from intent
    MEDIUM = "medium"  # Moderate deviation, may be intentional
    LOW = "low"  # Minor deviation or cosmetic change
    INFO = "info"  # Informational, no action required


@dataclass
class IntentSource:
    """Source of an intent baseline (docs, issue, code comment, etc.)."""

    source_type: str  # "documentation", "github_issue", "code_comment", "test_case"
    source_path: str
    line_number: Optional[int] = None
    url: Optional[str] = None
    title: Optional[str] = None
    content: str = ""
    extracted_at: datetime = field(default_factory=datetime.now)


@dataclass
class IntentBaseline:
    """Represents a single piece of expected system behavior."""

    intent_id: str
    description: str
    category: str  # e.g., "user_management", "payment_processing"
    expected_behavior: str
    success_criteria: List[str]
    related_entities: List[str] = field(default_factory=list)
    preconditions: List[str] = field(default_factory=list)
    postconditions: List[str] = field(default_factory=list)
    sources: List[IntentSource] = field(default_factory=list)
    confidence: float = 1.0  # 0.0 to 1.0

    def __hash__(self):
        return hash(self.intent_id)


@dataclass
class APISnapshot:
    """Snapshot of an API response at a point in time."""

    endpoint: str
    method: str
    request_params: Dict[str, Any] = field(default_factory=dict)
    request_body: Optional[Dict[str, Any]] = None
    response_body: Dict[str, Any] = field(default_factory=dict)
    response_status: int = 200
    response_headers: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert snapshot to dictionary."""
        return {
            "endpoint": self.endpoint,
            "method": self.method,
            "request_params": self.request_params,
            "request_body": self.request_body,
            "response_body": self.response_body,
            "response_status": self.response_status,
            "response_headers": self.response_headers,
            "timestamp": self.timestamp.isoformat(),
            "duration_ms": self.duration_ms,
        }


@dataclass
class DatabaseSnapshot:
    """Snapshot of database state."""

    database_type: str  # "neo4j", "postgresql", "mongodb", etc.
    connection_string: str
    entities: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    relationships: List[Dict[str, Any]] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    indexes: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert snapshot to dictionary."""
        return {
            "database_type": self.database_type,
            "entities": self.entities,
            "relationships": self.relationships,
            "constraints": self.constraints,
            "indexes": self.indexes,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class StateSnapshot:
    """Complete state snapshot combining API and database states."""

    snapshot_id: str
    commit_hash: Optional[str] = None
    branch: Optional[str] = None
    api_snapshots: List[APISnapshot] = field(default_factory=list)
    database_snapshots: List[DatabaseSnapshot] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def get_api_snapshot(
        self, endpoint: str, method: str = "GET"
    ) -> Optional[APISnapshot]:
        """Find API snapshot by endpoint and method."""
        for snapshot in self.api_snapshots:
            if snapshot.endpoint == endpoint and snapshot.method == method:
                return snapshot
        return None


@dataclass
class LogicDrift:
    """Represents a detected logic drift."""

    drift_id: str
    drift_type: DriftType
    severity: DriftSeverity
    intent: IntentBaseline
    description: str
    before_state: Optional[StateSnapshot] = None
    after_state: Optional[StateSnapshot] = None
    affected_endpoints: List[str] = field(default_factory=list)
    affected_entities: List[str] = field(default_factory=list)
    reasoning: str = ""
    recommendation: str = ""
    confidence: float = 0.0
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    detected_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert drift to dictionary."""
        return {
            "drift_id": self.drift_id,
            "drift_type": self.drift_type.name,
            "severity": self.severity.value,
            "intent_id": self.intent.intent_id,
            "intent_description": self.intent.description,
            "description": self.description,
            "reasoning": self.reasoning,
            "recommendation": self.recommendation,
            "confidence": self.confidence,
            "affected_endpoints": self.affected_endpoints,
            "affected_entities": self.affected_entities,
            "evidence": self.evidence,
            "detected_at": self.detected_at.isoformat(),
        }


@dataclass
class SemanticDriftReport:
    """Complete semantic drift analysis report."""

    report_id: str
    project_name: str
    baseline_commit: Optional[str] = None
    target_commit: Optional[str] = None
    intent_baselines: List[IntentBaseline] = field(default_factory=list)
    before_state: Optional[StateSnapshot] = None
    after_state: Optional[StateSnapshot] = None
    detected_drifts: List[LogicDrift] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=datetime.now)

    def get_drifts_by_severity(self, severity: DriftSeverity) -> List[LogicDrift]:
        """Get all drifts of a specific severity."""
        return [d for d in self.detected_drifts if d.severity == severity]

    def get_drifts_by_type(self, drift_type: DriftType) -> List[LogicDrift]:
        """Get all drifts of a specific type."""
        return [d for d in self.detected_drifts if d.drift_type == drift_type]

    def has_critical_drifts(self) -> bool:
        """Check if report contains any critical drifts."""
        return any(d.severity == DriftSeverity.CRITICAL for d in self.detected_drifts)

    def generate_summary(self) -> Dict[str, Any]:
        """Generate summary statistics."""
        severity_counts = {
            "critical": len(self.get_drifts_by_severity(DriftSeverity.CRITICAL)),
            "high": len(self.get_drifts_by_severity(DriftSeverity.HIGH)),
            "medium": len(self.get_drifts_by_severity(DriftSeverity.MEDIUM)),
            "low": len(self.get_drifts_by_severity(DriftSeverity.LOW)),
            "info": len(self.get_drifts_by_severity(DriftSeverity.INFO)),
        }

        type_counts = {}
        for drift_type in DriftType:
            type_counts[drift_type.name] = len(self.get_drifts_by_type(drift_type))

        self.summary = {
            "total_drifts": len(self.detected_drifts),
            "severity_distribution": severity_counts,
            "type_distribution": type_counts,
            "total_intents_analyzed": len(self.intent_baselines),
            "has_critical_issues": self.has_critical_drifts(),
        }

        return self.summary
