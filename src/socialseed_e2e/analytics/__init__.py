"""Anomaly Detection for Test Results and Performance (Issue #110).

This module provides statistical analysis and ML-based anomaly detection
for test results, performance metrics, and behavior patterns.

Features:
- Statistical anomaly detection (Z-score, IQR, MAD)
- Time series anomaly detection
- Error pattern analysis
- Data quality anomaly detection
- Security anomaly detection
- Alerting system
"""

from socialseed_e2e.analytics.anomaly_detector import (
    Alert,
    AlertSeverity,
    AlertType,
    AnomalyConfig,
    AnomalyDetector,
    AnomalyReport,
    AnomalyResult,
    AnomalyType,
    DetectionMethod,
    ErrorPattern,
    MetricSnapshot,
    SecurityAnomaly,
)
from socialseed_e2e.analytics.forecaster import (
    ForecastConfig,
    ForecastModel,
    ForecastResult,
    PerformanceForecaster,
    TrendDirection,
)
from socialseed_e2e.analytics.trend_analyzer import (
    ChangePoint,
    MetricTrend,
    SeasonalityInfo,
    TrendAnalyzer,
    TrendDirection as TrendDirectionAnalyzer,
    TrendReport,
)

__all__ = [
    # Anomaly Detector
    "AnomalyDetector",
    "AnomalyConfig",
    "AnomalyResult",
    "AnomalyReport",
    "AnomalyType",
    "DetectionMethod",
    "Alert",
    "AlertSeverity",
    "AlertType",
    "ErrorPattern",
    "SecurityAnomaly",
    "MetricSnapshot",
    # Trend Analyzer
    "TrendAnalyzer",
    "TrendReport",
    "MetricTrend",
    "ChangePoint",
    "SeasonalityInfo",
    "TrendDirectionAnalyzer",
    # Forecaster
    "PerformanceForecaster",
    "ForecastConfig",
    "ForecastModel",
    "ForecastResult",
    "TrendDirection",
]
