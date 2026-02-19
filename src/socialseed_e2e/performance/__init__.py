"""Enterprise Performance Testing Suite.

This module provides comprehensive performance testing capabilities:

**Load Testing:**
- Constant load: Steady traffic testing
- Spike testing: Sudden traffic surges
- Stress testing: Finding breaking points
- Endurance testing: Long-duration stability
- Volume testing: Large data handling
- Ramp testing: Gradual load changes

**Scenario-Based Testing:**
- User journey simulation
- Complex workflow testing
- Multi-step scenarios with think times
- Conditional logic and branching
- Data-dependent scenarios

**Resource Monitoring:**
- CPU and Memory profiling
- Database query analysis
- Network performance tracking
- System resource snapshots

**Performance Regression:**
- Baseline comparison
- Threshold alerts
- Trend analysis
- Historical tracking

Example:
    >>> from socialseed_e2e.performance import (
    ...     AdvancedLoadTester,
    ...     ScenarioBuilder,
    ...     ResourceMonitor,
    ...     PerformanceBaseline,
    ...     RegressionDetector
    ... )
    >>>
    >>> # Load testing
    >>> tester = AdvancedLoadTester()
    >>> result = await tester.spike_test(api_call, base_users=10, spike_users=1000)
    >>>
    >>> # Scenario testing
    >>> builder = ScenarioBuilder()
    >>> journey = builder.create_user_journey("checkout")
    >>> result = await journey.execute(users=100, duration=300)
    >>>
    >>> # Resource monitoring
    >>> monitor = ResourceMonitor()
    >>> async with monitor.track():
    ...     await run_test()
    >>> report = monitor.get_report()
    >>>
    >>> # Regression detection
    >>> baseline = PerformanceBaseline.load("baseline.json")
    >>> detector = RegressionDetector(baseline)
    >>> alerts = detector.detect_regressions(current_metrics)
"""

# Original performance testing components
from socialseed_e2e.performance.performance_models import (
    AlertSeverity,
    EndpointPerformanceMetrics,
    PerformanceAlert,
    PerformanceRegression,
    PerformanceReport,
    PerformanceThreshold,
    RegressionType,
)
from socialseed_e2e.performance.performance_profiler import PerformanceProfiler
from socialseed_e2e.performance.threshold_analyzer import ThresholdAnalyzer
from socialseed_e2e.performance.smart_alerts import SmartAlertGenerator
from socialseed_e2e.performance.load_generator import LoadGenerator, LoadTestResult
from socialseed_e2e.performance.metrics_collector import MetricsCollector, SLAPolicy
from socialseed_e2e.performance.dashboard import PerformanceDashboard

# Advanced load testing
from socialseed_e2e.performance.advanced_load_testing import (
    AdvancedLoadTester,
    LoadTestConfig,
    LoadTestResult as AdvancedLoadTestResult,
    LoadTestType,
    RequestMetrics,
)

# Scenario-based testing
from socialseed_e2e.performance.scenario_testing import (
    ScenarioBuilder,
    ScenarioResult,
    ScenarioStep,
    ScenarioTransition,
    StepType,
    UserJourney,
    UserJourneyMetrics,
    WorkflowSimulator,
)

# Resource monitoring
from socialseed_e2e.performance.resource_monitoring import (
    CPUStats,
    DatabaseQuery,
    DatabaseStats,
    DatabaseTracker,
    MemoryProfiler,
    MemoryStats,
    NetworkStats,
    NetworkTracker,
    QueryProfiler,
    ResourceMonitor,
    ResourceReport,
    ResourceSnapshot,
)

# Performance regression
from socialseed_e2e.performance.performance_regression import (
    BaselineManager,
    MetricBaseline,
    PerformanceBaseline,
    RegressionAlert,
    RegressionDetector,
    TrendAnalysis,
    TrendAnalyzer,
    TrendDataPoint,
)

__all__ = [
    # Performance Models
    "AlertSeverity",
    "EndpointPerformanceMetrics",
    "PerformanceAlert",
    "PerformanceRegression",
    "PerformanceReport",
    "PerformanceThreshold",
    "RegressionType",
    # Core Performance
    "PerformanceProfiler",
    "ThresholdAnalyzer",
    "SmartAlertGenerator",
    "LoadGenerator",
    "LoadTestResult",
    "MetricsCollector",
    "SLAPolicy",
    "PerformanceDashboard",
    # Advanced Load Testing
    "AdvancedLoadTester",
    "AdvancedLoadTestResult",
    "LoadTestConfig",
    "LoadTestType",
    "RequestMetrics",
    # Scenario Testing
    "ScenarioBuilder",
    "ScenarioResult",
    "ScenarioStep",
    "ScenarioTransition",
    "StepType",
    "UserJourney",
    "UserJourneyMetrics",
    "WorkflowSimulator",
    # Resource Monitoring
    "CPUStats",
    "DatabaseQuery",
    "DatabaseStats",
    "DatabaseTracker",
    "MemoryProfiler",
    "MemoryStats",
    "NetworkStats",
    "NetworkTracker",
    "QueryProfiler",
    "ResourceMonitor",
    "ResourceReport",
    "ResourceSnapshot",
    # Performance Regression
    "BaselineManager",
    "MetricBaseline",
    "PerformanceBaseline",
    "RegressionAlert",
    "RegressionDetector",
    "TrendAnalysis",
    "TrendAnalyzer",
    "TrendDataPoint",
]
