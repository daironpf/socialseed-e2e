"""Red Team Adversarial Agent Module.

Provides adversarial AI security testing capabilities including:
- Guardrail Discovery
- Adversarial Probing (Prompt Injection, Privilege Escalation, Hallucination Triggering)
- Resilience Scoring
- Security Logging

This module implements Issue #164: Adversarial AI Red Teaming
"""

from socialseed_e2e.agents.red_team_adversary.adversarial_prober import (
    AdversarialPayloads,
    AdversarialProber,
)
from socialseed_e2e.agents.red_team_adversary.guardrail_discovery import (
    GuardrailDiscovery,
)
from socialseed_e2e.agents.red_team_adversary.models import (
    AttackAttempt,
    AttackPayload,
    AttackResult,
    AttackSeverity,
    AttackStrategy,
    AttackType,
    GuardrailInfo,
    GuardrailType,
    RedTeamConfig,
    ResilienceScore,
    VulnerabilityReport,
)
from socialseed_e2e.agents.red_team_adversary.red_team_agent import RedTeamAgent
from socialseed_e2e.agents.red_team_adversary.resilience_scorer import (
    ResilienceScorer,
)
from socialseed_e2e.agents.red_team_adversary.security_logger import SecurityLogger

__all__ = [
    # Main Agent
    "RedTeamAgent",
    # Components
    "GuardrailDiscovery",
    "AdversarialProber",
    "AdversarialPayloads",
    "ResilienceScorer",
    "SecurityLogger",
    # Models
    "AttackAttempt",
    "AttackPayload",
    "AttackResult",
    "AttackSeverity",
    "AttackStrategy",
    "AttackType",
    "GuardrailInfo",
    "GuardrailType",
    "RedTeamConfig",
    "ResilienceScore",
    "VulnerabilityReport",
]
