"""Trend Analyzer for Test Results and Performance.

This module provides trend analysis capabilities for:
- Performance metric trends
- Change point detection
- Seasonality analysis
- Trend direction and magnitude
"""

import math
import statistics
from collections import defaultdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

try:
    import numpy as np

    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None


class TrendDirection(str, Enum):
    """Direction of a trend."""

    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    VOLATILE = "volatile"


class MetricTrend:
    """Trend information for a metric."""

    def __init__(
        self,
        metric_name: str,
        direction: TrendDirection,
        magnitude: float,
        slope: float,
        r_squared: float,
        start_value: float,
        end_value: float,
        change_percent: float,
        data_points: int,
        start_time: datetime,
        end_time: datetime,
    ):
        self.metric_name = metric_name
        self.direction = direction
        self.magnitude = magnitude
        self.slope = slope
        self.r_squared = r_squared
        self.start_value = start_value
        self.end_value = end_value
        self.change_percent = change_percent
        self.data_points = data_points
        self.start_time = start_time
        self.end_time = end_time

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "metric_name": self.metric_name,
            "direction": self.direction.value,
            "magnitude": self.magnitude,
            "slope": self.slope,
            "r_squared": self.r_squared,
            "start_value": self.start_value,
            "end_value": self.end_value,
            "change_percent": self.change_percent,
            "data_points": self.data_points,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
        }


class ChangePoint:
    """Detected change point in time series."""

    def __init__(
        self,
        timestamp: datetime,
        metric_name: str,
        change_magnitude: float,
        before_mean: float,
        after_mean: float,
        confidence: float,
        change_type: str,  # "sudden", "gradual", "seasonal"
    ):
        self.timestamp = timestamp
        self.metric_name = metric_name
        self.change_magnitude = change_magnitude
        self.before_mean = before_mean
        self.after_mean = after_mean
        self.confidence = confidence
        self.change_type = change_type

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "metric_name": self.metric_name,
            "change_magnitude": self.change_magnitude,
            "before_mean": self.before_mean,
            "after_mean": self.after_mean,
            "confidence": self.confidence,
            "change_type": self.change_type,
        }


class SeasonalityInfo:
    """Seasonality information for a metric."""

    def __init__(
        self,
        metric_name: str,
        has_seasonality: bool,
        period: Optional[timedelta],
        peak_times: List[datetime],
        trough_times: List[datetime],
        seasonality_strength: float,
    ):
        self.metric_name = metric_name
        self.has_seasonality = has_seasonality
        self.period = period
        self.peak_times = peak_times
        self.trough_times = trough_times
        self.seasonality_strength = seasonality_strength

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "metric_name": self.metric_name,
            "has_seasonality": self.has_seasonality,
            "period_hours": self.period.total_seconds() / 3600 if self.period else None,
            "peak_times": [t.isoformat() for t in self.peak_times],
            "trough_times": [t.isoformat() for t in self.trough_times],
            "seasonality_strength": self.seasonality_strength,
        }


class TrendReport:
    """Complete trend analysis report."""

    def __init__(
        self,
        start_time: datetime,
        end_time: datetime,
        trends: List[MetricTrend],
        change_points: List[ChangePoint],
        seasonalities: List[SeasonalityInfo],
        summary: Dict[str, Any],
    ):
        self.start_time = start_time
        self.end_time = end_time
        self.trends = trends
        self.change_points = change_points
        self.seasonalities = seasonalities
        self.summary = summary

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "trends": [t.to_dict() for t in self.trends],
            "change_points": [cp.to_dict() for cp in self.change_points],
            "seasonalities": [s.to_dict() for s in self.seasonalities],
            "summary": self.summary,
        }


class TrendAnalyzer:
    """Analyzer for detecting trends in performance and test metrics."""

    def __init__(
        self,
        min_data_points: int = 10,
        change_point_threshold: float = 2.0,
        seasonality_detection: bool = True,
    ):
        """Initialize the trend analyzer.

        Args:
            min_data_points: Minimum data points for analysis
            change_point_threshold: Threshold for change point detection
            seasonality_detection: Whether to detect seasonality
        """
        self.min_data_points = min_data_points
        self.change_point_threshold = change_point_threshold
        self.seasonality_detection = seasonality_detection

    def analyze_trend(
        self,
        timestamps: List[datetime],
        values: List[float],
        metric_name: str = "metric",
    ) -> Optional[MetricTrend]:
        """Analyze trend in a time series.

        Args:
            timestamps: List of timestamps
            values: List of values
            metric_name: Name of the metric

        Returns:
            Trend information or None if insufficient data
        """
        if len(values) < self.min_data_points:
            return None

        # Calculate linear regression
        x = list(range(len(values)))
        slope, intercept, r_value, p_value, std_err = self._linear_regression(x, values)
        r_squared = r_value**2

        # Determine direction
        if abs(slope) < 0.01 * statistics.mean(values):
            direction = TrendDirection.STABLE
        elif slope > 0:
            direction = TrendDirection.INCREASING
        else:
            direction = TrendDirection.DECREASING

        # Check volatility
        if self._calculate_cv(values) > 0.5:
            direction = TrendDirection.VOLATILE

        # Calculate magnitude and change
        start_value = values[0]
        end_value = values[-1]
        change_percent = (
            ((end_value - start_value) / start_value) * 100 if start_value != 0 else 0
        )
        magnitude = abs(change_percent)

        return MetricTrend(
            metric_name=metric_name,
            direction=direction,
            magnitude=magnitude,
            slope=slope,
            r_squared=r_squared,
            start_value=start_value,
            end_value=end_value,
            change_percent=change_percent,
            data_points=len(values),
            start_time=timestamps[0],
            end_time=timestamps[-1],
        )

    def detect_change_points(
        self,
        timestamps: List[datetime],
        values: List[float],
        metric_name: str = "metric",
    ) -> List[ChangePoint]:
        """Detect change points in time series.

        Args:
            timestamps: List of timestamps
            values: List of values
            metric_name: Name of the metric

        Returns:
            List of detected change points
        """
        if len(values) < self.min_data_points * 2:
            return []

        change_points = []
        window_size = max(5, len(values) // 10)

        for i in range(window_size, len(values) - window_size):
            before = values[i - window_size : i]
            after = values[i : i + window_size]

            before_mean = statistics.mean(before)
            after_mean = statistics.mean(after)

            # Calculate change magnitude
            change = abs(after_mean - before_mean)
            pooled_std = (
                (statistics.stdev(before) if len(before) > 1 else 0)
                + (statistics.stdev(after) if len(after) > 1 else 0)
            ) / 2

            if pooled_std == 0:
                continue

            z_score = change / pooled_std

            if z_score > self.change_point_threshold:
                # Determine change type
                if z_score > self.change_point_threshold * 2:
                    change_type = "sudden"
                elif z_score > self.change_point_threshold * 1.5:
                    change_type = "gradual"
                else:
                    change_type = "seasonal"

                change_points.append(
                    ChangePoint(
                        timestamp=timestamps[i],
                        metric_name=metric_name,
                        change_magnitude=change,
                        before_mean=before_mean,
                        after_mean=after_mean,
                        confidence=min(
                            1.0, z_score / (self.change_point_threshold * 3)
                        ),
                        change_type=change_type,
                    )
                )

        return change_points

    def detect_seasonality(
        self,
        timestamps: List[datetime],
        values: List[float],
        metric_name: str = "metric",
    ) -> SeasonalityInfo:
        """Detect seasonality in time series.

        Args:
            timestamps: List of timestamps
            values: List of values
            metric_name: Name of the metric

        Returns:
            Seasonality information
        """
        if not self.seasonality_detection or len(values) < 24:
            return SeasonalityInfo(
                metric_name=metric_name,
                has_seasonality=False,
                period=None,
                peak_times=[],
                trough_times=[],
                seasonality_strength=0.0,
            )

        # Group by hour of day to detect daily seasonality
        hourly_values = defaultdict(list)
        for ts, val in zip(timestamps, values):
            hourly_values[ts.hour].append(val)

        hourly_means = {h: statistics.mean(v) for h, v in hourly_values.items()}

        if len(hourly_means) < 6:
            return SeasonalityInfo(
                metric_name=metric_name,
                has_seasonality=False,
                period=None,
                peak_times=[],
                trough_times=[],
                seasonality_strength=0.0,
            )

        # Find peaks and troughs
        sorted_hours = sorted(hourly_means.items(), key=lambda x: x[1], reverse=True)
        peak_hours = [h for h, _ in sorted_hours[:3]]
        trough_hours = [h for h, _ in sorted_hours[-3:]]

        # Calculate seasonality strength
        overall_mean = statistics.mean(values)
        hour_variance = (
            statistics.variance(list(hourly_means.values()))
            if len(hourly_means) > 1
            else 0
        )
        total_variance = statistics.variance(values) if len(values) > 1 else 1

        seasonality_strength = (
            hour_variance / total_variance if total_variance > 0 else 0
        )

        has_seasonality = seasonality_strength > 0.3

        peak_times = [
            timestamps[0].replace(hour=h, minute=0, second=0) for h in peak_hours
        ]
        trough_times = [
            timestamps[0].replace(hour=h, minute=0, second=0) for h in trough_hours
        ]

        return SeasonalityInfo(
            metric_name=metric_name,
            has_seasonality=has_seasonality,
            period=timedelta(hours=24) if has_seasonality else None,
            peak_times=peak_times,
            trough_times=trough_times,
            seasonality_strength=seasonality_strength,
        )

    def compare_periods(
        self,
        period1_values: List[float],
        period2_values: List[float],
        period1_name: str = "Period 1",
        period2_name: str = "Period 2",
    ) -> Dict[str, Any]:
        """Compare two time periods.

        Args:
            period1_values: Values from first period
            period2_values: Values from second period
            period1_name: Name of first period
            period2_name: Name of second period

        Returns:
            Comparison results
        """
        if not period1_values or not period2_values:
            return {"error": "Insufficient data"}

        p1_mean = statistics.mean(period1_values)
        p2_mean = statistics.mean(period2_values)

        p1_std = statistics.stdev(period1_values) if len(period1_values) > 1 else 0
        p2_std = statistics.stdev(period2_values) if len(period2_values) > 1 else 0

        change = p2_mean - p1_mean
        change_percent = (change / p1_mean) * 100 if p1_mean != 0 else 0

        # Perform t-test (simplified)
        pooled_std = ((p1_std**2 + p2_std**2) / 2) ** 0.5
        if pooled_std > 0:
            t_statistic = change / (
                pooled_std * (1 / len(period1_values) + 1 / len(period2_values)) ** 0.5
            )
            significant = abs(t_statistic) > 2
        else:
            significant = False

        return {
            "period1_name": period1_name,
            "period2_name": period2_name,
            "period1_mean": p1_mean,
            "period2_mean": p2_mean,
            "period1_std": p1_std,
            "period2_std": p2_std,
            "change": change,
            "change_percent": change_percent,
            "significant": significant,
            "improvement": change < 0,  # For metrics where lower is better
        }

    def generate_report(
        self,
        timestamps: List[datetime],
        metrics: Dict[str, List[float]],
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> TrendReport:
        """Generate comprehensive trend report.

        Args:
            timestamps: List of timestamps
            metrics: Dictionary of metric names to values
            start_time: Start of analysis period
            end_time: End of analysis period

        Returns:
            Complete trend report
        """
        end_time = end_time or timestamps[-1]
        start_time = start_time or timestamps[0]

        trends = []
        change_points = []
        seasonalities = []

        for metric_name, values in metrics.items():
            # Analyze trend
            trend = self.analyze_trend(timestamps, values, metric_name)
            if trend:
                trends.append(trend)

            # Detect change points
            cps = self.detect_change_points(timestamps, values, metric_name)
            change_points.extend(cps)

            # Detect seasonality
            seasonality = self.detect_seasonality(timestamps, values, metric_name)
            seasonalities.append(seasonality)

        # Generate summary
        summary = {
            "total_metrics": len(metrics),
            "trends_detected": len(trends),
            "increasing_trends": len(
                [t for t in trends if t.direction == TrendDirection.INCREASING]
            ),
            "decreasing_trends": len(
                [t for t in trends if t.direction == TrendDirection.DECREASING]
            ),
            "stable_trends": len(
                [t for t in trends if t.direction == TrendDirection.STABLE]
            ),
            "volatile_trends": len(
                [t for t in trends if t.direction == TrendDirection.VOLATILE]
            ),
            "change_points_detected": len(change_points),
            "seasonal_patterns": len([s for s in seasonalities if s.has_seasonality]),
        }

        return TrendReport(
            start_time=start_time,
            end_time=end_time,
            trends=trends,
            change_points=change_points,
            seasonalities=seasonalities,
            summary=summary,
        )

    def _linear_regression(
        self, x: List[int], y: List[float]
    ) -> Tuple[float, float, float, float, float]:
        """Perform simple linear regression.

        Returns:
            Tuple of (slope, intercept, r_value, p_value, std_err)
        """
        try:
            import scipy.stats as stats

            return stats.linregress(x, y)
        except ImportError:
            # Fallback implementation
            n = len(x)
            x_mean = sum(x) / n
            y_mean = sum(y) / n

            numerator = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, y))
            denominator = sum((xi - x_mean) ** 2 for xi in x)

            slope = numerator / denominator if denominator != 0 else 0
            intercept = y_mean - slope * x_mean

            # Calculate R-value
            ss_res = sum((yi - (slope * xi + intercept)) ** 2 for xi, yi in zip(x, y))
            ss_tot = sum((yi - y_mean) ** 2 for yi in y)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
            r_value = r_squared**0.5 if r_squared > 0 else 0

            return slope, intercept, r_value, 0, 0

    def _calculate_cv(self, values: List[float]) -> float:
        """Calculate coefficient of variation."""
        if not values or len(values) < 2:
            return 0
        mean = statistics.mean(values)
        std = statistics.stdev(values)
        return std / mean if mean != 0 else 0
