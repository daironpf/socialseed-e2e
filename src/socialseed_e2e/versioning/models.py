"""Pydantic models for API versioning."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class VersionStrategy(str, Enum):
    """API versioning strategies."""

    URL_PATH = "url_path"
    HEADER = "header"
    QUERY_PARAM = "query_param"
    MEDIA_TYPE = "media_type"


class APIVersion(BaseModel):
    """Represents an API version."""

    version: str
    base_url: str
    is_deprecated: bool = False
    deprecation_date: Optional[datetime] = None
    sunset_date: Optional[datetime] = None
    notes: Optional[str] = None


class VersionTestResult(BaseModel):
    """Result of version-specific test."""

    version: str
    test_name: str
    passed: bool
    duration_ms: float
    error_message: Optional[str] = None
    response_status: Optional[int] = None


class MigrationTestResult(BaseModel):
    """Result of migration test between versions."""

    from_version: str
    to_version: str
    test_name: str
    passed: bool
    breaking_changes: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    backward_compatible: bool = True


class VersionCoverage(BaseModel):
    """Coverage report for API versions."""

    total_versions: int
    tested_versions: int
    untested_versions: List[str] = Field(default_factory=list)
    version_coverage_percent: float = 0.0


class DeprecationInfo(BaseModel):
    """Information about API deprecation."""

    version: str
    deprecated_date: datetime
    sunset_date: Optional[datetime] = None
    migration_guide: Optional[str] = None
    alternative_version: Optional[str] = None
    breaking_changes: List[str] = Field(default_factory=list)


class BreakingChange(BaseModel):
    """Represents a breaking change between API versions."""

    type: str
    description: str
    severity: str
    from_version: str
    to_version: str
    affected_endpoints: List[str] = Field(default_factory=list)
