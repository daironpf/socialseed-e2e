"""Models for Red Team Adversarial Agent.

Data models for security testing and adversarial attacks.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AttackType(str, Enum):
    """Types of adversarial attacks."""

    PROMPT_INJECTION = "prompt_injection"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    HALLUCINATION_TRIGGER = "hallucination_trigger"
    CONTEXT_LEAKAGE = "context_leakage"
    JAILBREAK = "jailbreak"
    ADVERSARIAL_SUFFIX = "adversarial_suffix"
    MULTI_STEP_MANIPULATION = "multi_step_manipulation"


class AttackSeverity(str, Enum):
    """Severity levels for discovered vulnerabilities."""

    CRITICAL = "critical"  # System compromise possible
    HIGH = "high"  # Significant security bypass
    MEDIUM = "medium"  # Partial bypass or info leak
    LOW = "low"  # Minor weakness
    INFO = "info"  # Informational only


class AttackResult(str, Enum):
    """Result of an attack attempt."""

    SUCCESS = "success"  # Attack succeeded
    PARTIAL = "partial"  # Partial success
    FAILURE = "failure"  # Attack failed (good!)
    ERROR = "error"  # Error during attack


class GuardrailType(str, Enum):
    """Types of safety guardrails discovered."""

    INPUT_FILTER = "input_filter"
    OUTPUT_FILTER = "output_filter"
    PROMPT_VALIDATION = "prompt_validation"
    RATE_LIMITING = "rate_limiting"
    CONTENT_MODERATION = "content_moderation"
    AUTH_CHECK = "auth_check"
    CONTEXT_ISOLATION = "context_isolation"


class GuardrailInfo(BaseModel):
    """Information about a discovered guardrail."""

    guardrail_id: str = Field(..., description="Unique identifier")
    guardrail_type: GuardrailType
    description: str
    location: str = Field(..., description="Where it was found (file, prompt, etc.)")
    strength: int = Field(..., ge=0, le=100, description="Estimated strength 0-100")
    bypass_attempted: bool = False
    bypass_successful: bool = False
    bypass_method: Optional[str] = None


class AttackPayload(BaseModel):
    """A single adversarial attack payload."""

    payload_id: str
    attack_type: AttackType
    name: str
    description: str
    payload_text: str
    target_component: str = Field(..., description="Component being targeted")
    expected_behavior: str = Field(..., description="What success looks like")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AttackAttempt(BaseModel):
    """Record of a single attack attempt."""

    attempt_id: str
    timestamp: datetime
    attack_type: AttackType
    payload: AttackPayload
    target_component: str
    result: AttackResult
    success_indicators: List[str] = Field(default_factory=list)
    failure_indicators: List[str] = Field(default_factory=list)
    response_snippet: Optional[str] = None
    severity: AttackSeverity = AttackSeverity.LOW
    evidence: Dict[str, Any] = Field(default_factory=dict)
    mitigation_suggestion: Optional[str] = None


class ResilienceScore(BaseModel):
    """Overall resilience scoring."""

    overall_score: int = Field(..., ge=0, le=100)
    component_scores: Dict[str, int] = Field(default_factory=dict)
    attack_type_scores: Dict[AttackType, int] = Field(default_factory=dict)
    guardrail_effectiveness: Dict[str, int] = Field(default_factory=dict)
    summary: str
    recommendations: List[str] = Field(default_factory=list)


class VulnerabilityReport(BaseModel):
    """Complete vulnerability report."""

    report_id: str
    generated_at: datetime
    target_system: str
    total_attacks: int
    successful_attacks: int
    partial_attacks: int
    failed_attacks: int
    resilience_score: ResilienceScore
    discovered_guardrails: List[GuardrailInfo]
    vulnerabilities: List[AttackAttempt]
    attack_chains: List[List[str]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RedTeamConfig(BaseModel):
    """Configuration for Red Team operations."""

    target_system: str
    attack_types: List[AttackType] = Field(default_factory=lambda: list(AttackType))
    max_iterations: int = 100
    parallel_attacks: int = 5
    use_shadow_runner: bool = True
    shadow_runner_config: Optional[Dict[str, Any]] = None
    custom_payloads: List[AttackPayload] = Field(default_factory=list)
    output_dir: str = "security"
    enable_logging: bool = True
    log_level: str = "INFO"


class AttackStrategy(BaseModel):
    """A complete attack strategy."""

    strategy_id: str
    name: str
    description: str
    attack_chain: List[AttackType]
    payloads: List[AttackPayload]
    prerequisites: List[str] = Field(default_factory=list)
    expected_impact: AttackSeverity
    success_criteria: List[str]
