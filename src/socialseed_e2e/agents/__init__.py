"""Autonomous Semantic Regression & Logic Drift Detection Agent.

This module implements Issue #163: An agent that detects semantic regressions
and logic drift by comparing actual system behavior against intended business intent.
"""

from socialseed_e2e.agents.semantic_analyzer.semantic_analyzer_agent import (
    SemanticAnalyzerAgent,
)
from socialseed_e2e.agents.semantic_analyzer.intent_baseline_extractor import (
    IntentBaselineExtractor,
)
from socialseed_e2e.agents.semantic_analyzer.stateful_analyzer import StatefulAnalyzer
from socialseed_e2e.agents.semantic_analyzer.logic_drift_detector import (
    LogicDriftDetector,
)
from socialseed_e2e.agents.semantic_analyzer.report_generator import (
    SemanticDriftReportGenerator,
)
from socialseed_e2e.agents.semantic_analyzer.models import (
    SemanticDriftReport,
    DriftType,
    DriftSeverity,
    IntentBaseline,
    StateSnapshot,
    LogicDrift,
)

__version__ = "1.0.0"
__all__ = [
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
]
