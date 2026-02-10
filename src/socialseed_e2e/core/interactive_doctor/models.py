"""Models for Interactive Doctor system.

This module provides data models for error analysis, diagnosis,
and fix suggestions.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional


class ErrorType(Enum):
    """Types of errors that can be diagnosed."""

    TYPE_MISMATCH = auto()
    MISSING_FIELD = auto()
    VALIDATION_ERROR = auto()
    SCHEMA_MISMATCH = auto()
    AUTH_ERROR = auto()
    NOT_FOUND = auto()
    SERVER_ERROR = auto()
    NETWORK_ERROR = auto()
    ASSERTION_FAILURE = auto()
    UNKNOWN = auto()


class FixStrategy(Enum):
    """Strategies for fixing errors."""

    UPDATE_TEST_DATA = auto()
    UPDATE_DTO_LOGIC = auto()
    UPDATE_ENDPOINT_LOGIC = auto()
    UPDATE_VALIDATION = auto()
    ADD_MISSING_FIELD = auto()
    REMOVE_EXTRA_FIELD = auto()
    CONVERT_TYPE = auto()
    IGNORE = auto()
    MANUAL_FIX = auto()


@dataclass
class ErrorContext:
    """Context information about a test error."""

    test_name: str
    service_name: str
    endpoint_path: Optional[str] = None
    http_method: Optional[str] = None
    error_message: str = ""
    error_traceback: str = ""
    request_data: Optional[Dict[str, Any]] = None
    response_data: Optional[Dict[str, Any]] = None
    response_status: Optional[int] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TypeMismatchDetails:
    """Details about a type mismatch error."""

    field_name: str
    expected_type: str
    actual_type: str
    expected_value: Any = None
    actual_value: Any = None
    dto_name: Optional[str] = None


@dataclass
class MissingFieldDetails:
    """Details about a missing field error."""

    field_name: str
    dto_name: Optional[str] = None
    is_required: bool = True
    default_value: Any = None


@dataclass
class ValidationErrorDetails:
    """Details about a validation error."""

    field_name: str
    validation_rule: str
    constraint_value: Any = None
    actual_value: Any = None
    error_message: str = ""


@dataclass
class DiagnosisResult:
    """Result of error diagnosis."""

    error_type: ErrorType
    confidence: float  # 0.0 to 1.0
    description: str
    context: ErrorContext
    details: Any = None  # TypeMismatchDetails, MissingFieldDetails, etc.
    affected_files: List[str] = field(default_factory=list)
    manifest_insights: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FixSuggestion:
    """Suggestion for fixing an error."""

    strategy: FixStrategy
    title: str
    description: str
    automatic: bool  # Whether this fix can be applied automatically
    code_changes: List[Dict[str, Any]] = field(default_factory=list)
    preview: str = ""  # Preview of the fix
    risks: List[str] = field(default_factory=list)


@dataclass
class DoctorSession:
    """Session for interactive doctor."""

    session_id: str
    project_root: str
    errors: List[DiagnosisResult] = field(default_factory=list)
    applied_fixes: List[Dict[str, Any]] = field(default_factory=list)
    skipped_fixes: List[Dict[str, Any]] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None

    def get_duration_seconds(self) -> float:
        """Get session duration in seconds."""
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()


@dataclass
class AppliedFix:
    """Record of an applied fix."""

    fix_id: str
    strategy: FixStrategy
    description: str
    files_modified: List[str] = field(default_factory=list)
    backup_paths: List[str] = field(default_factory=list)
    applied_at: datetime = field(default_factory=datetime.now)
    success: bool = True
    error_message: Optional[str] = None
