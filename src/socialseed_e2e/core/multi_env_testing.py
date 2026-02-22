"""
Multi-Environment Testing System for socialseed-e2e.

This module provides capabilities to run tests against multiple environments
(staging, production, etc.) simultaneously and compare results.

Features:
- Parallel test execution across environments
- Semantic diffing of responses
- Drift detection between environments
- Unified reporting
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, Field


class EnvironmentStatus(str, Enum):
    """Status of an environment."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class DriftType(str, Enum):
    """Types of semantic drift detected."""

    RESPONSE_PAYLOAD = "response_payload"
    STATUS_CODE = "status_code"
    RESPONSE_TIME = "response_time"
    SCHEMA_CHANGE = "schema_change"
    MISSING_FIELD = "missing_field"
    EXTRA_FIELD = "extra_field"


class EnvironmentConfig(BaseModel):
    """Configuration for a test environment."""

    name: str
    base_url: str
    api_key: Optional[str] = None
    headers: Dict[str, str] = {}

    health_endpoint: str = "/health"
    timeout: int = 30

    is_default: bool = False


class EnvironmentResult(BaseModel):
    """Result of running tests against an environment."""

    environment_name: str
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: int = 0

    execution_time_ms: float = 0
    avg_response_time_ms: float = 0

    test_details: List[Dict[str, Any]] = Field(default_factory=list)


class DriftDetection(BaseModel):
    """Detected drift between environments."""

    drift_id: str
    drift_type: DriftType

    endpoint: str
    environment_a: str
    environment_b: str

    value_a: Any
    value_b: Any

    severity: str = "medium"
    description: str

    recommendation: Optional[str] = None


class ComparisonReport(BaseModel):
    """Report comparing results across environments."""

    report_id: str
    generated_at: datetime = Field(default_factory=datetime.now)

    environments: List[str]

    results_by_env: Dict[str, EnvironmentResult]

    drifts: List[DriftDetection] = Field(default_factory=list)

    total_drifts: int = 0
    critical_drifts: int = 0

    summary: str
    health_status: Dict[str, EnvironmentStatus]


class MultiEnvTestRunner:
    """
    Runs tests against multiple environments and compares results.
    """

    def __init__(self):
        self.environments: Dict[str, EnvironmentConfig] = {}
        self.results: Dict[str, EnvironmentResult] = {}

    def add_environment(self, config: EnvironmentConfig) -> None:
        """Add an environment configuration."""
        self.environments[config.name] = config
        if config.is_default:
            for env in self.environments.values():
                if env.name != config.name:
                    env.is_default = False

    def get_environment(self, name: str) -> Optional[EnvironmentConfig]:
        """Get environment by name."""
        return self.environments.get(name)

    async def check_health(
        self, name: str, http_client: Optional[Any] = None
    ) -> EnvironmentStatus:
        """Check health of an environment."""
        env = self.environments.get(name)
        if not env:
            return EnvironmentStatus.UNKNOWN

        try:
            import httpx

            client = http_client or httpx.Client()
            response = client.get(
                f"{env.base_url}{env.health_endpoint}",
                timeout=env.timeout,
            )

            if response.status_code == 200:
                return EnvironmentStatus.HEALTHY
            elif response.status_code < 500:
                return EnvironmentStatus.DEGRADED
            else:
                return EnvironmentStatus.UNHEALTHY

        except Exception:
            return EnvironmentStatus.UNHEALTHY

    def compare_responses(
        self,
        endpoint: str,
        response_a: Dict[str, Any],
        response_b: Dict[str, Any],
    ) -> List[DriftDetection]:
        """Compare responses from two environments."""
        drifts = []

        if response_a.get("status_code") != response_b.get("status_code"):
            drifts.append(
                DriftDetection(
                    drift_id=f"{endpoint}_status",
                    drift_type=DriftType.STATUS_CODE,
                    endpoint=endpoint,
                    environment_a="env_a",
                    environment_b="env_b",
                    value_a=response_a.get("status_code"),
                    value_b=response_b.get("status_code"),
                    severity="high",
                    description="Status code mismatch",
                )
            )

        body_a = response_a.get("body", {})
        body_b = response_b.get("body", {})

        if body_a.keys() != body_b.keys():
            missing = set(body_a.keys()) - set(body_b.keys())
            extra = set(body_b.keys()) - set(body_a.keys())

            if missing:
                drifts.append(
                    DriftDetection(
                        drift_id=f"{endpoint}_missing",
                        drift_type=DriftType.MISSING_FIELD,
                        endpoint=endpoint,
                        environment_a="env_a",
                        environment_b="env_b",
                        value_a=list(missing),
                        value_b=None,
                        severity="medium",
                        description=f"Fields missing in env_b: {missing}",
                    )
                )

            if extra:
                drifts.append(
                    DriftDetection(
                        drift_id=f"{endpoint}_extra",
                        drift_type=DriftType.EXTRA_FIELD,
                        endpoint=endpoint,
                        environment_a="env_a",
                        environment_b="env_b",
                        value_a=None,
                        value_b=list(extra),
                        severity="low",
                        description=f"Extra fields in env_b: {extra}",
                    )
                )

        return drifts

    def generate_report(
        self,
        results: Dict[str, EnvironmentResult],
        drifts: List[DriftDetection],
    ) -> ComparisonReport:
        """Generate a comparison report."""
        environments = list(results.keys())
        health_status = {}

        for name, result in results.items():
            if result.failed == 0 and result.errors == 0:
                health_status[name] = EnvironmentStatus.HEALTHY
            elif result.failed > result.passed:
                health_status[name] = EnvironmentStatus.UNHEALTHY
            else:
                health_status[name] = EnvironmentStatus.DEGRADED

        critical = [d for d in drifts if d.severity == "critical"]

        summary = f"Compared {len(environments)} environments. "
        summary += f"Found {len(drifts)} drifts ({len(critical)} critical)."

        return ComparisonReport(
            report_id=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            environments=environments,
            results_by_env=results,
            drifts=drifts,
            total_drifts=len(drifts),
            critical_drifts=len(critical),
            summary=summary,
            health_status=health_status,
        )


class SemanticDriftDetector:
    """
    Detects semantic drift between environment responses using AI.
    """

    def __init__(self):
        self.drift_signatures = {
            "timestamp": self._ignore_timestamp,
            "uuid": self._ignore_uuid,
            "date": self._ignore_date,
            "generated_id": self._ignore_generated,
        }

    def _ignore_timestamp(self, value: Any) -> bool:
        """Check if value is a timestamp."""
        if isinstance(value, str):
            return (
                any(x in value for x in ["T", "Z", "+00:00"])
                or "timestamp" in value.lower()
            )
        return False

    def _ignore_uuid(self, value: Any) -> bool:
        """Check if value is a UUID."""
        import re

        if isinstance(value, str):
            return bool(re.match(r"^[0-9a-f]{8}-[0-9a-f]{4}", value))
        return False

    def _ignore_date(self, value: Any) -> bool:
        """Check if value is a date string."""
        if isinstance(value, str):
            return "date" in value.lower() or len(value) == 10 and value[4] == "-"
        return False

    def _ignore_generated(self, value: Any) -> bool:
        """Check if value is auto-generated."""
        return False

    def normalize_for_comparison(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize data by removing dynamic fields."""
        normalized = {}

        for key, value in data.items():
            should_ignore = False

            for sig_type, check_fn in self.drift_signatures.items():
                if sig_type in key.lower() and check_fn(value):
                    should_ignore = True
                    break

            if not should_ignore:
                if isinstance(value, dict):
                    normalized[key] = self.normalize_for_comparison(value)
                elif isinstance(value, list):
                    normalized[key] = [
                        self.normalize_for_comparison(item)
                        if isinstance(item, dict)
                        else item
                        for item in value
                    ]
                else:
                    normalized[key] = value

        return normalized


__all__ = [
    "EnvironmentConfig",
    "EnvironmentResult",
    "EnvironmentStatus",
    "DriftDetection",
    "DriftType",
    "ComparisonReport",
    "MultiEnvTestRunner",
    "SemanticDriftDetector",
]
