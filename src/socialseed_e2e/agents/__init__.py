"""AI Agents Module.

This module implements:
- Issue #163: Semantic Regression & Logic Drift Detection Agent
- Issue #164: Adversarial AI Red Teaming Agent
"""

# Semantic Analyzer (Issue #163)
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
    AttackType,
    GuardrailInfo,
    GuardrailType,
    ResilienceScore,
    VulnerabilityReport,
)

# Red Team Adversary (Issue #164)
from socialseed_e2e.agents.red_team_adversary.red_team_agent import RedTeamAgent
from socialseed_e2e.agents.red_team_adversary.resilience_scorer import (
    ResilienceScorer,
)
from socialseed_e2e.agents.red_team_adversary.security_logger import SecurityLogger
from socialseed_e2e.agents.semantic_analyzer.intent_baseline_extractor import (
    IntentBaselineExtractor,
)
from socialseed_e2e.agents.semantic_analyzer.logic_drift_detector import (
    LogicDriftDetector,
)
from socialseed_e2e.agents.semantic_analyzer.models import (
    DriftSeverity,
    DriftType,
    IntentBaseline,
    LogicDrift,
    SemanticDriftReport,
    StateSnapshot,
)
from socialseed_e2e.agents.semantic_analyzer.report_generator import (
    SemanticDriftReportGenerator,
)
from socialseed_e2e.agents.semantic_analyzer.semantic_analyzer_agent import (
    SemanticAnalyzerAgent,
)
from socialseed_e2e.agents.semantic_analyzer.stateful_analyzer import StatefulAnalyzer

__version__ = "1.0.0"
__all__ = [
    # Semantic Analyzer
    "SemanticAnalyzerAgent",
    "IntentBaselineExtractor",
    "StatefulAnalyzer",
    "LogicDriftDetector",
    "SemanticDriftReportGenerator",
    "SemanticDriftReport",
    "DriftType",
    "DriftSeverity",
    "IntentBaseline",
    "StateSnapshot",
    "LogicDrift",
    # Red Team Adversary
    "RedTeamAgent",
    "GuardrailDiscovery",
    "AdversarialProber",
    "AdversarialPayloads",
    "ResilienceScorer",
    "SecurityLogger",
    "AttackAttempt",
    "AttackPayload",
    "AttackResult",
    "AttackSeverity",
    "AttackType",
    "GuardrailInfo",
    "GuardrailType",
    "ResilienceScore",
    "VulnerabilityReport",
]
