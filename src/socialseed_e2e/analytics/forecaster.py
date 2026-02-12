"""Performance Forecaster for Test Results and Metrics.

This module provides forecasting capabilities for:
- Performance metric prediction
- Resource utilization forecasting
- Test execution time prediction
- Trend-based forecasting
"""

import math
import statistics
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

try:
    import numpy as np

    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None


# Helper functions for numpy compatibility
def _mean(values: List[float]) -> float:
    """Calculate mean of values."""
    if HAS_NUMPY:
        return float(_mean(values))
    return statistics.mean(values) if values else 0.0


def _std(values: List[float]) -> float:
    """Calculate standard deviation of values."""
    if HAS_NUMPY:
        return float(_std(values))
    return statistics.stdev(values) if len(values) > 1 else 0.0


def _sqrt(x: float) -> float:
    """Calculate square root."""
    if HAS_NUMPY:
        return float(_sqrt(x))
    return math.sqrt(x) if x >= 0 else float("nan")


def _polyfit(x: List[int], y: List[float], degree: int) -> Tuple[float, ...]:
    """Fit polynomial of given degree."""
    if HAS_NUMPY:
        return tuple(_polyfit(x, y, degree))
    # Simple linear regression fallback
    n = len(x)
    x_mean = sum(x) / n
    y_mean = sum(y) / n
    numerator = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, y))
    denominator = sum((xi - x_mean) ** 2 for xi in x)
    slope = numerator / denominator if denominator != 0 else 0
    intercept = y_mean - slope * x_mean
    return (slope, intercept)


def _arange(start: int, stop: int = None) -> List[int]:
    """Create range of integers.

    Supports both _arange(stop) and _arange(start, stop) signatures.
    """
    if stop is None:
        return list(range(start))
    return list(range(start, stop))


def _corrcoef(x: List[float], y: List[float]) -> float:
    """Calculate correlation coefficient (Pearson's r)."""
    if len(x) < 2 or len(y) < 2:
        return 0.0
    if HAS_NUMPY and np is not None:
        return float(np.corrcoef(x, y)[0, 1])  # type: ignore
    # Pearson correlation
    n = len(x)
    x_mean = sum(x) / n
    y_mean = sum(y) / n
    numerator = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, y))
    x_std = math.sqrt(sum((xi - x_mean) ** 2 for xi in x))
    y_std = math.sqrt(sum((yi - y_mean) ** 2 for yi in y))
    if x_std == 0 or y_std == 0:
        return 0.0
    return numerator / (x_std * y_std)


class ForecastModel(str, Enum):
    """Forecasting models available."""

    LINEAR = "linear"
    EXPONENTIAL_SMOOTHING = "exponential_smoothing"
    MOVING_AVERAGE = "moving_average"
    SEASONAL = "seasonal"
    AUTO = "auto"


class TrendDirection(str, Enum):
    """Direction of forecasted trend."""

    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    UNKNOWN = "unknown"


class ForecastConfig:
    """Configuration for forecasting."""

    def __init__(
        self,
        model: ForecastModel = ForecastModel.AUTO,
        confidence_level: float = 0.95,
        seasonality_period: Optional[int] = None,
        min_data_points: int = 10,
        max_forecast_points: int = 100,
        smoothing_factor: float = 0.3,
    ):
        self.model = model
        self.confidence_level = confidence_level
        self.seasonality_period = seasonality_period
        self.min_data_points = min_data_points
        self.max_forecast_points = max_forecast_points
        self.smoothing_factor = smoothing_factor


class ForecastResult:
    """Result of a forecast."""

    def __init__(
        self,
        metric_name: str,
        forecast_values: List[float],
        forecast_timestamps: List[datetime],
        confidence_intervals: List[Tuple[float, float]],
        model_used: ForecastModel,
        confidence_level: float,
        trend_direction: TrendDirection,
        trend_slope: float,
        accuracy_metrics: Dict[str, float],
    ):
        self.metric_name = metric_name
        self.forecast_values = forecast_values
        self.forecast_timestamps = forecast_timestamps
        self.confidence_intervals = confidence_intervals
        self.model_used = model_used
        self.confidence_level = confidence_level
        self.trend_direction = trend_direction
        self.trend_slope = trend_slope
        self.accuracy_metrics = accuracy_metrics

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "metric_name": self.metric_name,
            "forecast_values": self.forecast_values,
            "forecast_timestamps": [ts.isoformat() for ts in self.forecast_timestamps],
            "confidence_intervals": self.confidence_intervals,
            "model_used": self.model_used.value,
            "confidence_level": self.confidence_level,
            "trend_direction": self.trend_direction.value,
            "trend_slope": self.trend_slope,
            "accuracy_metrics": self.accuracy_metrics,
        }


class PerformanceForecaster:
    """Forecaster for performance metrics and test results."""

    def __init__(self, config: Optional[ForecastConfig] = None):
        """Initialize the forecaster.

        Args:
            config: Forecast configuration
        """
        self.config = config or ForecastConfig()

    def forecast(
        self,
        timestamps: List[datetime],
        values: List[float],
        metric_name: str = "metric",
        periods: int = 10,
    ) -> Optional[ForecastResult]:
        """Generate forecast for future values.

        Args:
            timestamps: Historical timestamps
            values: Historical values
            metric_name: Name of the metric
            periods: Number of periods to forecast

        Returns:
            Forecast result or None if insufficient data
        """
        if len(values) < self.config.min_data_points:
            return None

        periods = min(periods, self.config.max_forecast_points)

        # Select best model if auto
        if self.config.model == ForecastModel.AUTO:
            model = self._select_best_model(values)
        else:
            model = self.config.model

        # Generate forecast based on model
        if model == ForecastModel.LINEAR:
            forecast_values, confidence_intervals = self._linear_forecast(values, periods)
        elif model == ForecastModel.EXPONENTIAL_SMOOTHING:
            forecast_values, confidence_intervals = self._exponential_smoothing_forecast(
                values, periods
            )
        elif model == ForecastModel.MOVING_AVERAGE:
            forecast_values, confidence_intervals = self._moving_average_forecast(values, periods)
        elif model == ForecastModel.SEASONAL:
            forecast_values, confidence_intervals = self._seasonal_forecast(values, periods)
        else:
            forecast_values, confidence_intervals = self._linear_forecast(values, periods)

        # Generate forecast timestamps
        last_timestamp = timestamps[-1]
        interval = self._estimate_interval(timestamps)
        forecast_timestamps = [last_timestamp + interval * (i + 1) for i in range(periods)]

        # Calculate trend direction
        trend_slope = self._calculate_trend_slope(values)
        if abs(trend_slope) < 0.001:
            trend_direction = TrendDirection.STABLE
        elif trend_slope > 0:
            trend_direction = TrendDirection.INCREASING
        else:
            trend_direction = TrendDirection.DECREASING

        # Calculate accuracy metrics
        accuracy_metrics = self._calculate_accuracy_metrics(values, forecast_values)

        return ForecastResult(
            metric_name=metric_name,
            forecast_values=forecast_values,
            forecast_timestamps=forecast_timestamps,
            confidence_intervals=confidence_intervals,
            model_used=model,
            confidence_level=self.config.confidence_level,
            trend_direction=trend_direction,
            trend_slope=trend_slope,
            accuracy_metrics=accuracy_metrics,
        )

    def forecast_response_time(
        self,
        timestamps: List[datetime],
        response_times: List[float],
        periods: int = 10,
    ) -> Optional[ForecastResult]:
        """Forecast future response times.

        Args:
            timestamps: Historical timestamps
            response_times: Historical response times in ms
            periods: Number of periods to forecast

        Returns:
            Forecast result
        """
        result = self.forecast(timestamps, response_times, "response_time", periods)

        if result:
            # Add warning if forecast exceeds common thresholds
            threshold_warnings = []
            for i, (value, (lower, upper)) in enumerate(
                zip(result.forecast_values, result.confidence_intervals)
            ):
                if lower > 1000:  # > 1 second
                    threshold_warnings.append(
                        f"Period {i + 1}: Response time expected to exceed 1 second"
                    )

            if threshold_warnings:
                result.accuracy_metrics["warnings"] = threshold_warnings

        return result

    def forecast_error_rate(
        self,
        timestamps: List[datetime],
        error_rates: List[float],
        periods: int = 10,
    ) -> Optional[ForecastResult]:
        """Forecast future error rates.

        Args:
            timestamps: Historical timestamps
            error_rates: Historical error rates (0-1)
            periods: Number of periods to forecast

        Returns:
            Forecast result
        """
        result = self.forecast(timestamps, error_rates, "error_rate", periods)

        if result:
            # Cap error rates at 1.0 (100%)
            result.forecast_values = [min(1.0, max(0.0, v)) for v in result.forecast_values]
            result.confidence_intervals = [
                (max(0.0, lower), min(1.0, upper)) for lower, upper in result.confidence_intervals
            ]

            # Add warning if error rate expected to increase
            if (
                result.trend_direction == TrendDirection.INCREASING
                and result.forecast_values[-1] > 0.05
            ):
                result.accuracy_metrics["alert"] = "Error rate expected to exceed 5%"

        return result

    def forecast_throughput(
        self,
        timestamps: List[datetime],
        throughput: List[float],
        periods: int = 10,
    ) -> Optional[ForecastResult]:
        """Forecast future throughput.

        Args:
            timestamps: Historical timestamps
            throughput: Historical throughput (requests/second)
            periods: Number of periods to forecast

        Returns:
            Forecast result
        """
        return self.forecast(timestamps, throughput, "throughput", periods)

    def predict_capacity_breach(
        self,
        timestamps: List[datetime],
        values: List[float],
        capacity_limit: float,
        metric_name: str = "metric",
    ) -> Optional[Dict[str, Any]]:
        """Predict when capacity limit will be breached.

        Args:
            timestamps: Historical timestamps
            values: Historical values
            capacity_limit: Capacity limit threshold
            metric_name: Name of the metric

        Returns:
            Prediction result or None if no breach expected
        """
        # Forecast far into future
        result = self.forecast(timestamps, values, metric_name, periods=100)

        if not result:
            return None

        # Find when capacity will be breached
        for i, (forecast_value, (lower_ci, _)) in enumerate(
            zip(result.forecast_values, result.confidence_intervals)
        ):
            if lower_ci > capacity_limit:
                breach_timestamp = result.forecast_timestamps[i]
                time_to_breach = breach_timestamp - datetime.utcnow()

                return {
                    "metric_name": metric_name,
                    "capacity_limit": capacity_limit,
                    "breach_predicted": True,
                    "breach_timestamp": breach_timestamp.isoformat(),
                    "time_to_breach_hours": time_to_breach.total_seconds() / 3600,
                    "confidence": result.confidence_level,
                    "forecast_at_breach": forecast_value,
                }

        # No breach predicted
        last_forecast = result.forecast_values[-1]
        last_confidence = result.confidence_intervals[-1]

        return {
            "metric_name": metric_name,
            "capacity_limit": capacity_limit,
            "breach_predicted": False,
            "current_utilization": last_forecast / capacity_limit if capacity_limit > 0 else 0,
            "headroom": capacity_limit - last_forecast,
            "confidence": result.confidence_level,
            "forecast_range": f"{last_confidence[0]:.2f} - {last_confidence[1]:.2f}",
        }

    def _select_best_model(self, values: List[float]) -> ForecastModel:
        """Select best forecasting model based on data characteristics."""
        if len(values) < 20:
            return ForecastModel.LINEAR

        # Check for seasonality
        if self._has_seasonality(values):
            return ForecastModel.SEASONAL

        # Check trend strength
        trend_strength = abs(self._calculate_trend_slope(values))
        if trend_strength > 0.1:
            return ForecastModel.LINEAR

        # Use exponential smoothing for stable/noisy data
        return ForecastModel.EXPONENTIAL_SMOOTHING

    def _linear_forecast(
        self, values: List[float], periods: int
    ) -> Tuple[List[float], List[Tuple[float, float]]]:
        """Generate linear forecast."""
        n = len(values)
        x = _arange(n)

        # Linear regression
        slope, intercept = _polyfit(x, values, 1)

        # Forecast - use list comprehension
        forecast_x = _arange(n, n + periods)
        forecast_values = [slope * fx + intercept for fx in forecast_x]

        # Calculate confidence intervals
        residuals = [values[i] - (slope * x[i] + intercept) for i in range(n)]
        squared_residuals = [r * r for r in residuals]
        mse = _mean(squared_residuals)
        std_error = _sqrt(mse)

        confidence_intervals = []
        z_score = 1.96  # 95% confidence
        x_mean = _mean(x)
        x_variance = sum((xi - x_mean) ** 2 for xi in x)

        for i in range(periods):
            if x_variance > 0:
                forecast_std = std_error * _sqrt(
                    1 + 1 / n + (forecast_x[i] - x_mean) ** 2 / x_variance
                )
            else:
                forecast_std = std_error * _sqrt(1 + 1 / n)
            margin = z_score * forecast_std
            confidence_intervals.append((forecast_values[i] - margin, forecast_values[i] + margin))

        return forecast_values, confidence_intervals

    def _exponential_smoothing_forecast(
        self, values: List[float], periods: int
    ) -> Tuple[List[float], List[Tuple[float, float]]]:
        """Generate forecast using exponential smoothing."""
        alpha = self.config.smoothing_factor

        # Initialize with first value
        smoothed = [values[0]]

        # Apply exponential smoothing
        for i in range(1, len(values)):
            smoothed.append(alpha * values[i] + (1 - alpha) * smoothed[i - 1])

        # Forecast
        forecast_values = []
        last_smoothed = smoothed[-1]

        for _ in range(periods):
            forecast_values.append(last_smoothed)

        # Calculate confidence intervals based on historical errors
        errors = [abs(values[i] - smoothed[i]) for i in range(len(values))]
        mean_error = _mean(errors)
        std_error = _std(errors)

        confidence_intervals = []
        for value in forecast_values:
            margin = 1.96 * (std_error + mean_error * 0.1)  # Increase uncertainty with time
            confidence_intervals.append((value - margin, value + margin))

        return forecast_values, confidence_intervals

    def _moving_average_forecast(
        self, values: List[float], periods: int
    ) -> Tuple[List[float], List[Tuple[float, float]]]:
        """Generate forecast using moving average."""
        window_size = min(5, len(values) // 2)

        # Calculate moving averages
        moving_averages = []
        for i in range(window_size, len(values)):
            window = values[i - window_size : i]
            moving_averages.append(_mean(window))

        # Last moving average as forecast
        last_ma = moving_averages[-1] if moving_averages else _mean(values[-window_size:])

        forecast_values = [last_ma] * periods

        # Calculate confidence intervals
        std_dev = _std(moving_averages) if len(moving_averages) > 1 else _std(values) * 0.5
        margin = 1.96 * std_dev

        confidence_intervals = [(value - margin, value + margin) for value in forecast_values]

        return forecast_values, confidence_intervals

    def _seasonal_forecast(
        self, values: List[float], periods: int
    ) -> Tuple[List[float], List[Tuple[float, float]]]:
        """Generate forecast using seasonal decomposition."""
        period = self.config.seasonality_period or 24  # Default to daily

        if len(values) < period * 2:
            # Not enough data for seasonal, fall back to linear
            return self._linear_forecast(values, periods)

        # Calculate seasonal components
        seasonal_components = []
        for i in range(period):
            indices = [j for j in range(i, len(values), period)]
            seasonal_components.append(_mean([values[j] for j in indices]))

        # Detrend
        trend_slope, trend_intercept = _polyfit(range(len(values)), values, 1)
        detrended = [values[i] - (trend_slope * i + trend_intercept) for i in range(len(values))]

        # Calculate trend forecast
        last_trend = trend_slope * len(values) + trend_intercept

        # Generate forecast
        forecast_values = []
        for i in range(periods):
            seasonal_idx = (len(values) + i) % period
            forecast_values.append(last_trend + trend_slope * i + seasonal_components[seasonal_idx])

        # Confidence intervals
        residuals = [
            abs(detrended[i] - seasonal_components[i % period]) for i in range(len(values))
        ]
        std_residual = _std(residuals)
        margin = 1.96 * std_residual

        confidence_intervals = [(value - margin, value + margin) for value in forecast_values]

        return forecast_values, confidence_intervals

    def _has_seasonality(self, values: List[float]) -> bool:
        """Check if data has seasonality."""
        if len(values) < 48:  # Need at least 2 days of hourly data
            return False

        # Simple seasonality detection using autocorrelation
        period = 24  # Assume daily seasonality
        if len(values) < period * 2:
            return False

        # Calculate correlation with lag
        lagged = values[period:]
        original = values[:-period]

        if len(lagged) > 1 and len(original) > 1:
            correlation = _corrcoef(lagged, original)
            return correlation > 0.5

        return False

    def _calculate_trend_slope(self, values: List[float]) -> float:
        """Calculate trend slope."""
        if len(values) < 2:
            return 0.0

        x = _arange(len(values))
        slope, _ = _polyfit(x, values, 1)
        return slope

    def _estimate_interval(self, timestamps: List[datetime]) -> timedelta:
        """Estimate interval between timestamps."""
        if len(timestamps) < 2:
            return timedelta(hours=1)

        intervals = [
            (timestamps[i + 1] - timestamps[i]).total_seconds() for i in range(len(timestamps) - 1)
        ]

        avg_interval = _mean(intervals)
        return timedelta(seconds=avg_interval)

    def _calculate_accuracy_metrics(
        self, actual: List[float], forecast: List[float]
    ) -> Dict[str, float]:
        """Calculate forecast accuracy metrics."""
        # Use simple persistence model as baseline
        persistence_forecast = [actual[-1]] * len(forecast)

        # Calculate MAE (Mean Absolute Error)
        mae = _mean([abs(a - f) for a, f in zip(actual[-len(forecast) :], forecast)])

        # Calculate RMSE (Root Mean Square Error)
        rmse = _sqrt(_mean([(a - f) ** 2 for a, f in zip(actual[-len(forecast) :], forecast)]))

        # Calculate MAPE (Mean Absolute Percentage Error)
        mape = _mean(
            [abs((a - f) / a) * 100 for a, f in zip(actual[-len(forecast) :], forecast) if a != 0]
        )

        return {
            "mae": round(mae, 4),
            "rmse": round(rmse, 4),
            "mape": round(mape, 4) if not math.isnan(mape) else None,
        }
