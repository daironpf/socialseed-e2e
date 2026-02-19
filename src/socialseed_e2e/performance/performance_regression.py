"""Performance Regression Detection and Baseline Management.

This module provides performance regression detection capabilities:
- Baseline comparison
- Threshold alerts
- Trend analysis
- Historical tracking

Example:
    >>> from socialseed_e2e.performance import PerformanceBaseline, RegressionDetector
    >>> baseline = PerformanceBaseline.load("api-baseline.json")
    >>> detector = RegressionDetector(baseline)
    >>> regressions = detector.detect_regressions(current_metrics)
"""

import json
import logging
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


@dataclass
class MetricBaseline:
    """Baseline data for a single metric.

    Attributes:
        metric_name: Name of the metric
        avg_value: Average value
        min_value: Minimum value
        max_value: Maximum value
        std_deviation: Standard deviation
        p95_value: 95th percentile
        p99_value: 99th percentile
        sample_count: Number of samples
        recorded_at: When baseline was recorded
    """

    metric_name: str
    avg_value: float
    min_value: float
    max_value: float
    std_deviation: float = 0.0
    p95_value: float = 0.0
    p99_value: float = 0.0
    sample_count: int = 0
    recorded_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def tolerance_upper(self) -> float:
        """Calculate upper tolerance bound (2 std deviations)."""
        return self.avg_value + (2 * self.std_deviation)

    @property
    def tolerance_lower(self) -> float:
        """Calculate lower tolerance bound (2 std deviations)."""
        return max(0, self.avg_value - (2 * self.std_deviation))

    def is_within_tolerance(self, value: float) -> bool:
        """Check if value is within tolerance.

        Args:
            value: Value to check

        Returns:
            True if within tolerance
        """
        return self.tolerance_lower <= value <= self.tolerance_upper

    def deviation_percentage(self, value: float) -> float:
        """Calculate deviation percentage from baseline.

        Args:
            value: Current value

        Returns:
            Percentage deviation
        """
        if self.avg_value == 0:
            return 0.0
        return ((value - self.avg_value) / self.avg_value) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "metric_name": self.metric_name,
            "avg_value": self.avg_value,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "std_deviation": self.std_deviation,
            "p95_value": self.p95_value,
            "p99_value": self.p99_value,
            "sample_count": self.sample_count,
            "recorded_at": self.recorded_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MetricBaseline":
        """Create from dictionary."""
        return cls(
            metric_name=data["metric_name"],
            avg_value=data["avg_value"],
            min_value=data["min_value"],
            max_value=data["max_value"],
            std_deviation=data.get("std_deviation", 0.0),
            p95_value=data.get("p95_value", 0.0),
            p99_value=data.get("p99_value", 0.0),
            sample_count=data.get("sample_count", 0),
            recorded_at=datetime.fromisoformat(data["recorded_at"]),
        )

    @classmethod
    def from_values(cls, metric_name: str, values: List[float]) -> "MetricBaseline":
        """Create baseline from list of values.

        Args:
            metric_name: Name of the metric
            values: List of historical values

        Returns:
            MetricBaseline instance
        """
        if not values:
            return cls(metric_name=metric_name, avg_value=0, min_value=0, max_value=0)

        sorted_values = sorted(values)
        n = len(sorted_values)

        return cls(
            metric_name=metric_name,
            avg_value=statistics.mean(values),
            min_value=min(values),
            max_value=max(values),
            std_deviation=statistics.stdev(values) if n > 1 else 0.0,
            p95_value=sorted_values[int(n * 0.95)] if n > 1 else values[0],
            p99_value=sorted_values[int(n * 0.99)] if n > 1 else values[0],
            sample_count=n,
        )


@dataclass
class PerformanceBaseline:
    """Complete performance baseline for a service or endpoint.

    Contains baselines for multiple metrics (latency, throughput, errors, etc.)

    Attributes:
        name: Baseline name
        description: Description
        created_at: Creation timestamp
        updated_at: Last update timestamp
        version: Baseline version
        metrics: Dictionary of metric baselines
        metadata: Additional metadata
    """

    name: str
    description: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: str = "1.0.0"
    metrics: Dict[str, MetricBaseline] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_metric(self, baseline: MetricBaseline) -> None:
        """Add a metric baseline.

        Args:
            baseline: MetricBaseline to add
        """
        self.metrics[baseline.metric_name] = baseline
        self.updated_at = datetime.utcnow()

    def get_metric(self, name: str) -> Optional[MetricBaseline]:
        """Get a metric baseline by name.

        Args:
            name: Metric name

        Returns:
            MetricBaseline or None
        """
        return self.metrics.get(name)

    def save(self, filepath: Union[str, Path]) -> None:
        """Save baseline to file.

        Args:
            filepath: Path to save file
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
            "metrics": {k: v.to_dict() for k, v in self.metrics.items()},
            "metadata": self.metadata,
        }

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Baseline saved to {filepath}")

    @classmethod
    def load(cls, filepath: Union[str, Path]) -> "PerformanceBaseline":
        """Load baseline from file.

        Args:
            filepath: Path to load file

        Returns:
            PerformanceBaseline instance
        """
        with open(filepath, "r") as f:
            data = json.load(f)

        baseline = cls(
            name=data["name"],
            description=data.get("description", ""),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            version=data.get("version", "1.0.0"),
            metadata=data.get("metadata", {}),
        )

        for metric_name, metric_data in data.get("metrics", {}).items():
            baseline.metrics[metric_name] = MetricBaseline.from_dict(metric_data)

        logger.info(f"Baseline loaded from {filepath}")
        return baseline

    @classmethod
    def from_historical_results(
        cls, name: str, results: List[Dict[str, Any]], metric_keys: List[str]
    ) -> "PerformanceBaseline":
        """Create baseline from historical test results.

        Args:
            name: Baseline name
            results: List of historical result dictionaries
            metric_keys: Keys to extract from results

        Returns:
            PerformanceBaseline instance
        """
        baseline = cls(
            name=name, description=f"Baseline from {len(results)} historical results"
        )

        for key in metric_keys:
            values = [r.get(key) for r in results if r.get(key) is not None]
            if values:
                metric_baseline = MetricBaseline.from_values(key, values)
                baseline.add_metric(metric_baseline)

        return baseline


@dataclass
class RegressionAlert:
    """Alert for detected performance regression.

    Attributes:
        metric_name: Affected metric
        severity: Alert severity (info, warning, critical)
        baseline_value: Expected baseline value
        current_value: Current measured value
        deviation_percentage: Deviation from baseline
        description: Alert description
        timestamp: When alert was generated
        recommendations: List of recommendations
    """

    metric_name: str
    severity: str
    baseline_value: float
    current_value: float
    deviation_percentage: float
    description: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "metric_name": self.metric_name,
            "severity": self.severity,
            "baseline_value": self.baseline_value,
            "current_value": self.current_value,
            "deviation_percentage": round(self.deviation_percentage, 2),
            "description": self.description,
            "timestamp": self.timestamp.isoformat(),
            "recommendations": self.recommendations,
        }


@dataclass
class TrendDataPoint:
    """A single data point in a trend.

    Attributes:
        timestamp: When measurement was taken
        value: Measured value
        label: Optional label
    """

    timestamp: datetime
    value: float
    label: Optional[str] = None


@dataclass
class TrendAnalysis:
    """Analysis of metric trends over time.

    Attributes:
        metric_name: Name of the metric
        data_points: List of trend data points
        slope: Trend slope (positive = increasing)
        direction: "improving", "degrading", or "stable"
        change_rate: Rate of change per time period
        forecast: Projected future values
    """

    metric_name: str
    data_points: List[TrendDataPoint]
    slope: float = 0.0
    direction: str = "stable"
    change_rate: float = 0.0
    forecast: List[float] = field(default_factory=list)

    def calculate_trend(self) -> None:
        """Calculate trend from data points."""
        if len(self.data_points) < 2:
            return

        # Simple linear regression
        n = len(self.data_points)
        x_values = list(range(n))
        y_values = [dp.value for dp in self.data_points]

        x_mean = sum(x_values) / n
        y_mean = sum(y_values) / n

        # Calculate slope
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values))
        denominator = sum((x - x_mean) ** 2 for x in x_values)

        self.slope = numerator / denominator if denominator != 0 else 0

        # Determine direction (depends on metric type)
        # For latency: positive slope = degrading
        # For throughput: positive slope = improving
        if self.metric_name in ["latency", "error_rate", "memory_usage"]:
            # Lower is better
            if self.slope > 0.01:
                self.direction = "degrading"
            elif self.slope < -0.01:
                self.direction = "improving"
            else:
                self.direction = "stable"
        else:
            # Higher is better
            if self.slope > 0.01:
                self.direction = "improving"
            elif self.slope < -0.01:
                self.direction = "degrading"
            else:
                self.direction = "stable"

        # Calculate change rate
        if n > 1:
            time_span = (
                self.data_points[-1].timestamp - self.data_points[0].timestamp
            ).total_seconds()
            value_change = y_values[-1] - y_values[0]
            self.change_rate = value_change / time_span if time_span > 0 else 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "metric_name": self.metric_name,
            "slope": round(self.slope, 6),
            "direction": self.direction,
            "change_rate": round(self.change_rate, 6),
            "data_points": [
                {
                    "timestamp": dp.timestamp.isoformat(),
                    "value": dp.value,
                    "label": dp.label,
                }
                for dp in self.data_points
            ],
        }


class RegressionDetector:
    """Detect performance regressions by comparing against baselines.

    Provides comprehensive regression detection with configurable thresholds
    and severity levels.

    Example:
        >>> baseline = PerformanceBaseline.load("baseline.json")
        >>> detector = RegressionDetector(
        ...     baseline,
        ...     warning_threshold=10.0,
        ...     critical_threshold=25.0
        ... )
        >>>
        >>> current_metrics = {"latency_avg": 150.5, "error_rate": 2.1}
        >>> alerts = detector.detect_regressions(current_metrics)
        >>>
        >>> for alert in alerts:
        ...     print(f"{alert.severity}: {alert.description}")
    """

    def __init__(
        self,
        baseline: PerformanceBaseline,
        warning_threshold: float = 10.0,
        critical_threshold: float = 25.0,
        use_std_deviation: bool = True,
    ):
        """Initialize regression detector.

        Args:
            baseline: Performance baseline to compare against
            warning_threshold: Percentage deviation for warning
            critical_threshold: Percentage deviation for critical
            use_std_deviation: Use standard deviation for tolerance
        """
        self.baseline = baseline
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.use_std_deviation = use_std_deviation
        self.alerts: List[RegressionAlert] = []

    def detect_regressions(
        self, current_metrics: Dict[str, float]
    ) -> List[RegressionAlert]:
        """Detect regressions in current metrics.

        Args:
            current_metrics: Dictionary of current metric values

        Returns:
            List of regression alerts
        """
        self.alerts = []

        for metric_name, current_value in current_metrics.items():
            metric_baseline = self.baseline.get_metric(metric_name)

            if metric_baseline is None:
                logger.warning(f"No baseline found for metric: {metric_name}")
                continue

            alert = self._check_metric(metric_baseline, current_value)
            if alert:
                self.alerts.append(alert)

        return self.alerts

    def _check_metric(
        self, baseline: MetricBaseline, current_value: float
    ) -> Optional[RegressionAlert]:
        """Check a single metric for regression.

        Args:
            baseline: Metric baseline
            current_value: Current value

        Returns:
            RegressionAlert or None
        """
        deviation = baseline.deviation_percentage(current_value)

        # Determine severity
        if self.use_std_deviation:
            # Use standard deviation-based thresholds
            std_threshold = 2.0  # 2 standard deviations
            is_regression = abs(deviation) > (
                baseline.std_deviation / baseline.avg_value * 100 * std_threshold
            )
        else:
            # Use percentage thresholds
            is_regression = abs(deviation) > self.warning_threshold

        if not is_regression:
            return None

        # Determine severity
        if abs(deviation) > self.critical_threshold:
            severity = "critical"
        elif abs(deviation) > self.warning_threshold:
            severity = "warning"
        else:
            severity = "info"

        # Determine if this is improvement or regression
        is_improvement = deviation < 0 and baseline.metric_name not in [
            "throughput",
            "rps",
        ]

        if is_improvement:
            description = f"{baseline.metric_name} improved by {abs(deviation):.1f}%"
        else:
            description = f"{baseline.metric_name} regressed by {deviation:.1f}%"

        # Generate recommendations
        recommendations = self._generate_recommendations(
            baseline.metric_name, deviation, current_value
        )

        return RegressionAlert(
            metric_name=baseline.metric_name,
            severity=severity,
            baseline_value=baseline.avg_value,
            current_value=current_value,
            deviation_percentage=deviation,
            description=description,
            recommendations=recommendations,
        )

    def _generate_recommendations(
        self, metric_name: str, deviation: float, current_value: float
    ) -> List[str]:
        """Generate recommendations based on regression.

        Args:
            metric_name: Name of the metric
            deviation: Deviation percentage
            current_value: Current value

        Returns:
            List of recommendations
        """
        recommendations = []

        if "latency" in metric_name.lower():
            if deviation > 0:
                recommendations.extend(
                    [
                        "Check for slow database queries",
                        "Review recent code changes for N+1 queries",
                        "Consider adding caching for frequently accessed data",
                        "Profile the application to identify bottlenecks",
                    ]
                )

        elif "error_rate" in metric_name.lower():
            if deviation > 0:
                recommendations.extend(
                    [
                        "Check application logs for error patterns",
                        "Verify database connection pool settings",
                        "Review recent deployments for breaking changes",
                        "Check external service dependencies",
                    ]
                )

        elif "memory" in metric_name.lower():
            if deviation > 0:
                recommendations.extend(
                    [
                        "Check for memory leaks in recent changes",
                        "Review large object allocations",
                        "Consider implementing pagination for large datasets",
                        "Optimize data structures for memory efficiency",
                    ]
                )

        elif "throughput" in metric_name.lower() or "rps" in metric_name.lower():
            if deviation < 0:
                recommendations.extend(
                    [
                        "Check for resource contention",
                        "Review thread pool and connection pool sizes",
                        "Consider horizontal scaling",
                        "Optimize hot code paths",
                    ]
                )

        if not recommendations:
            recommendations.append(f"Investigate changes affecting {metric_name}")
            recommendations.append("Compare current code with baseline version")

        return recommendations

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of regression detection.

        Returns:
            Summary dictionary
        """
        return {
            "baseline_name": self.baseline.name,
            "metrics_checked": len(self.baseline.metrics),
            "regressions_found": len(self.alerts),
            "critical": len([a for a in self.alerts if a.severity == "critical"]),
            "warning": len([a for a in self.alerts if a.severity == "warning"]),
            "info": len([a for a in self.alerts if a.severity == "info"]),
        }


class TrendAnalyzer:
    """Analyze performance trends over time.

    Tracks metrics over multiple test runs and identifies trends,
    forecasts, and anomalies.

    Example:
        >>> analyzer = TrendAnalyzer()
        >>>
        >>> # Add historical data
        >>> for result in historical_results:
        ...     analyzer.add_data_point("latency", result["timestamp"], result["latency"])
        ...     analyzer.add_data_point("throughput", result["timestamp"], result["throughput"])
        >>>
        >>> # Analyze trends
        >>> trends = analyzer.analyze_trends()
        >>> for trend in trends:
        ...     print(f"{trend.metric_name}: {trend.direction} ({trend.slope:.4f})")
    """

    def __init__(self):
        """Initialize trend analyzer."""
        self.data: Dict[str, List[TrendDataPoint]] = {}

    def add_data_point(
        self,
        metric_name: str,
        timestamp: datetime,
        value: float,
        label: Optional[str] = None,
    ) -> None:
        """Add a data point for trend analysis.

        Args:
            metric_name: Name of the metric
            timestamp: When measurement was taken
            value: Measured value
            label: Optional label
        """
        if metric_name not in self.data:
            self.data[metric_name] = []

        self.data[metric_name].append(
            TrendDataPoint(timestamp=timestamp, value=value, label=label)
        )

        # Keep data sorted by timestamp
        self.data[metric_name].sort(key=lambda x: x.timestamp)

    def analyze_trends(self) -> List[TrendAnalysis]:
        """Analyze trends for all metrics.

        Returns:
            List of TrendAnalysis objects
        """
        analyses = []

        for metric_name, data_points in self.data.items():
            if len(data_points) < 2:
                continue

            analysis = TrendAnalysis(metric_name=metric_name, data_points=data_points)
            analysis.calculate_trend()
            analyses.append(analysis)

        return analyses

    def get_metric_trend(self, metric_name: str) -> Optional[TrendAnalysis]:
        """Get trend for a specific metric.

        Args:
            metric_name: Name of the metric

        Returns:
            TrendAnalysis or None
        """
        if metric_name not in self.data:
            return None

        data_points = self.data[metric_name]
        if len(data_points) < 2:
            return None

        analysis = TrendAnalysis(metric_name=metric_name, data_points=data_points)
        analysis.calculate_trend()
        return analysis

    def detect_anomalies(
        self, metric_name: str, threshold_std: float = 2.0
    ) -> List[TrendDataPoint]:
        """Detect anomalous data points.

        Args:
            metric_name: Name of the metric
            threshold_std: Standard deviation threshold

        Returns:
            List of anomalous data points
        """
        if metric_name not in self.data:
            return []

        data_points = self.data[metric_name]
        if len(data_points) < 3:
            return []

        values = [dp.value for dp in data_points]
        mean = statistics.mean(values)
        std_dev = statistics.stdev(values)

        anomalies = []
        for dp in data_points:
            z_score = abs(dp.value - mean) / std_dev if std_dev > 0 else 0
            if z_score > threshold_std:
                anomalies.append(dp)

        return anomalies

    def export_data(self, filepath: Union[str, Path]) -> None:
        """Export trend data to file.

        Args:
            filepath: Path to export file
        """
        data = {
            metric: [
                {
                    "timestamp": dp.timestamp.isoformat(),
                    "value": dp.value,
                    "label": dp.label,
                }
                for dp in points
            ]
            for metric, points in self.data.items()
        }

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Trend data exported to {filepath}")

    def import_data(self, filepath: Union[str, Path]) -> None:
        """Import trend data from file.

        Args:
            filepath: Path to import file
        """
        with open(filepath, "r") as f:
            data = json.load(f)

        for metric, points in data.items():
            for point in points:
                self.add_data_point(
                    metric_name=metric,
                    timestamp=datetime.fromisoformat(point["timestamp"]),
                    value=point["value"],
                    label=point.get("label"),
                )

        logger.info(f"Trend data imported from {filepath}")


class BaselineManager:
    """Manage multiple performance baselines.

    Provides versioning and organization of baselines for different
    services, endpoints, and test scenarios.

    Example:
        >>> manager = BaselineManager(".e2e/baselines")
        >>>
        >>> # Save baseline
        >>> manager.save_baseline(baseline, "user-service-v1.2.0")
        >>>
        >>> # Load baseline
        >>> baseline = manager.load_baseline("user-service-v1.2.0")
        >>>
        >>> # List all baselines
        >>> baselines = manager.list_baselines()
    """

    def __init__(self, storage_dir: Union[str, Path] = ".e2e/baselines"):
        """Initialize baseline manager.

        Args:
            storage_dir: Directory for storing baselines
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save_baseline(
        self, baseline: PerformanceBaseline, name: Optional[str] = None
    ) -> Path:
        """Save a baseline.

        Args:
            baseline: Baseline to save
            name: Optional name override

        Returns:
            Path to saved file
        """
        save_name = name or baseline.name
        filename = f"{save_name}.json"
        filepath = self.storage_dir / filename

        baseline.save(filepath)
        return filepath

    def load_baseline(self, name: str) -> Optional[PerformanceBaseline]:
        """Load a baseline by name.

        Args:
            name: Baseline name

        Returns:
            PerformanceBaseline or None
        """
        filepath = self.storage_dir / f"{name}.json"

        if not filepath.exists():
            logger.warning(f"Baseline not found: {name}")
            return None

        return PerformanceBaseline.load(filepath)

    def list_baselines(self) -> List[str]:
        """List all available baselines.

        Returns:
            List of baseline names
        """
        baselines = []
        for filepath in self.storage_dir.glob("*.json"):
            baselines.append(filepath.stem)
        return sorted(baselines)

    def delete_baseline(self, name: str) -> bool:
        """Delete a baseline.

        Args:
            name: Baseline name

        Returns:
            True if deleted, False if not found
        """
        filepath = self.storage_dir / f"{name}.json"

        if not filepath.exists():
            return False

        filepath.unlink()
        logger.info(f"Baseline deleted: {name}")
        return True

    def compare_baselines(
        self, baseline1_name: str, baseline2_name: str
    ) -> Dict[str, Any]:
        """Compare two baselines.

        Args:
            baseline1_name: First baseline name
            baseline2_name: Second baseline name

        Returns:
            Comparison results
        """
        baseline1 = self.load_baseline(baseline1_name)
        baseline2 = self.load_baseline(baseline2_name)

        if not baseline1 or not baseline2:
            return {"error": "One or both baselines not found"}

        comparison = {
            "baseline1": baseline1.name,
            "baseline2": baseline2.name,
            "metrics_compared": [],
            "improvements": [],
            "regressions": [],
            "unchanged": [],
        }

        all_metrics = set(baseline1.metrics.keys()) | set(baseline2.metrics.keys())

        for metric_name in all_metrics:
            m1 = baseline1.get_metric(metric_name)
            m2 = baseline2.get_metric(metric_name)

            if not m1 or not m2:
                continue

            comparison["metrics_compared"].append(metric_name)

            deviation = m1.deviation_percentage(m2.avg_value)

            if abs(deviation) < 5.0:
                comparison["unchanged"].append(
                    {"metric": metric_name, "change": f"{deviation:+.1f}%"}
                )
            elif deviation > 0:
                # Regression (depends on metric type)
                if metric_name in ["latency", "error_rate"]:
                    comparison["regressions"].append(
                        {
                            "metric": metric_name,
                            "change": f"+{deviation:.1f}%",
                            "from": m1.avg_value,
                            "to": m2.avg_value,
                        }
                    )
                else:
                    comparison["improvements"].append(
                        {
                            "metric": metric_name,
                            "change": f"+{deviation:.1f}%",
                            "from": m1.avg_value,
                            "to": m2.avg_value,
                        }
                    )
            else:
                # Improvement
                if metric_name in ["latency", "error_rate"]:
                    comparison["improvements"].append(
                        {
                            "metric": metric_name,
                            "change": f"{deviation:.1f}%",
                            "from": m1.avg_value,
                            "to": m2.avg_value,
                        }
                    )
                else:
                    comparison["regressions"].append(
                        {
                            "metric": metric_name,
                            "change": f"{deviation:.1f}%",
                            "from": m1.avg_value,
                            "to": m2.avg_value,
                        }
                    )

        return comparison
