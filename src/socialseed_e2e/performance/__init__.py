"""AI-Powered Performance Profiling and Bottleneck Detection.

This module provides comprehensive performance analysis capabilities:
- Latency tracking for every endpoint during E2E runs
- Threshold analysis comparing current vs historical performance
- Smart alerts for performance regressions with code context
"""

from .performance_models import (
    EndpointPerformanceMetrics,
    PerformanceAlert,
    PerformanceRegression,
    PerformanceReport,
    PerformanceThreshold,
)
from .performance_profiler import PerformanceProfiler
from .threshold_analyzer import ThresholdAnalyzer
from .smart_alerts import SmartAlertGenerator
from .load_generator import LoadGenerator
from .metrics_collector import MetricsCollector, SLAPolicy
from .dashboard import PerformanceDashboard

__all__ = [
    "EndpointPerformanceMetrics",
    "PerformanceAlert",
    "PerformanceRegression",
    "PerformanceReport",
    "PerformanceThreshold",
    "PerformanceProfiler",
    "ThresholdAnalyzer",
    "SmartAlertGenerator",
    "LoadGenerator",
    "MetricsCollector",
    "SLAPolicy",
    "PerformanceDashboard",
]
