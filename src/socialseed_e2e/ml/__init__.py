"""ML-Based Predictive Test Selection for socialseed-e2e.

This module provides machine learning capabilities for:
- Selecting tests most likely to fail based on code changes
- Detecting flaky tests
- Analyzing code impact
- Optimizing test execution order
"""

from socialseed_e2e.ml.flakiness_detector import FlakinessDetector
from socialseed_e2e.ml.impact_analyzer import ImpactAnalyzer
from socialseed_e2e.ml.models import (
    ChangeType,
    CodeChange,
    CoverageGap,
    CoverageReport,
    FileType,
    FlakinessReport,
    ImpactAnalysis,
    MLModelPerformance,
    MLOrchestratorConfig,
    RedundancyReport,
    RedundantTest,
    TestHistory,
    TestMetrics,
    TestPrediction,
    TestPriority,
    TestSelectionResult,
)
from socialseed_e2e.ml.test_selector import TestSelector

__all__ = [
    # Main classes
    "ImpactAnalyzer",
    "FlakinessDetector",
    "TestSelector",
    # Enums
    "ChangeType",
    "FileType",
    "TestPriority",
    # Models
    "CodeChange",
    "CoverageGap",
    "CoverageReport",
    "FlakinessReport",
    "ImpactAnalysis",
    "MLModelPerformance",
    "MLOrchestratorConfig",
    "RedundancyReport",
    "RedundantTest",
    "TestHistory",
    "TestMetrics",
    "TestPrediction",
    "TestSelectionResult",
]
