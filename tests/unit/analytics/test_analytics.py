"""Unit tests for Analytics Module (Issue #110).

Tests for anomaly detection, trend analysis, and forecasting.
"""

import random
from datetime import datetime, timedelta
from typing import List

from socialseed_e2e.analytics.anomaly_detector import (
    AlertSeverity,
    AlertType,
    AnomalyConfig,
    AnomalyDetector,
    AnomalyType,
    DetectionMethod,
    MetricSnapshot,
)
from socialseed_e2e.analytics.forecaster import (
    ForecastConfig,
    ForecastModel,
    PerformanceForecaster,
    TrendDirection,
)
from socialseed_e2e.analytics.trend_analyzer import (
    TrendAnalyzer,
    TrendDirection as TrendDirectionAnalyzer,
)


class TestAnomalyDetector:
    """Test AnomalyDetector class."""

    def test_init(self):
        """Test initialization."""
        detector = AnomalyDetector()
        assert detector.config is not None
        assert len(detector._history) == 0

    def test_init_with_config(self):
        """Test initialization with custom config."""
        config = AnomalyConfig(z_score_threshold=2.5, min_data_points=5)
        detector = AnomalyDetector(config)
        assert detector.config.z_score_threshold == 2.5
        assert detector.config.min_data_points == 5

    def test_add_metric(self):
        """Test adding metric snapshots."""
        detector = AnomalyDetector()
        snapshot = MetricSnapshot(
            timestamp=datetime.utcnow(),
            response_time_ms=100.0,
            error_rate=0.05,
        )
        detector.add_metric(snapshot)
        assert len(detector._history) == 1

    def test_add_error(self):
        """Test adding errors."""
        detector = AnomalyDetector()
        detector.add_error(datetime.utcnow(), "Test error")
        assert len(detector._error_history) == 1

    def test_detect_response_time_anomalies_no_data(self):
        """Test anomaly detection with no data."""
        detector = AnomalyDetector()
        anomalies = detector.detect_response_time_anomalies()
        assert len(anomalies) == 0

    def test_detect_response_time_anomalies_with_data(self):
        """Test anomaly detection with data."""
        detector = AnomalyDetector()

        # Add normal response times
        base_time = datetime.utcnow()
        for i in range(20):
            snapshot = MetricSnapshot(
                timestamp=base_time + timedelta(minutes=i),
                response_time_ms=100.0 + random.gauss(0, 10),
            )
            detector.add_metric(snapshot)

        # Add anomalous response time
        anomaly_snapshot = MetricSnapshot(
            timestamp=base_time + timedelta(minutes=20),
            response_time_ms=500.0,  # Much higher than normal
        )
        detector.add_metric(anomaly_snapshot)

        anomalies = detector.detect_response_time_anomalies()
        assert len(anomalies) > 0

        # Check that anomaly was detected
        z_score_anomalies = [
            a for a in anomalies if a.method == DetectionMethod.Z_SCORE
        ]
        assert len(z_score_anomalies) > 0

    def test_detect_error_rate_anomalies(self):
        """Test error rate anomaly detection."""
        detector = AnomalyDetector(config=AnomalyConfig(error_rate_threshold=0.1))

        base_time = datetime.utcnow()
        for i in range(15):
            snapshot = MetricSnapshot(
                timestamp=base_time + timedelta(minutes=i),
                error_rate=0.02,  # Low error rate
            )
            detector.add_metric(snapshot)

        # Add high error rate
        snapshot = MetricSnapshot(
            timestamp=base_time + timedelta(minutes=15),
            error_rate=0.15,  # Above threshold
        )
        detector.add_metric(snapshot)

        anomalies = detector.detect_error_rate_anomalies()
        assert len(anomalies) > 0

    def test_detect_error_patterns(self):
        """Test error pattern detection."""
        detector = AnomalyDetector()

        base_time = datetime.utcnow()

        # Add repeated errors
        for i in range(10):
            detector.add_error(
                base_time + timedelta(minutes=i), "Connection timeout to database"
            )

        # Add different errors
        for i in range(5):
            detector.add_error(
                base_time + timedelta(minutes=10 + i), f"Unique error {i}"
            )

        patterns = detector.detect_error_patterns()
        assert len(patterns) > 0

        # Check that pattern was detected
        timeout_pattern = [p for p in patterns if "timeout" in p.pattern.lower()]
        assert len(timeout_pattern) > 0

    def test_detect_security_anomalies_sql_injection(self):
        """Test SQL injection detection."""
        detector = AnomalyDetector()

        base_time = datetime.utcnow()

        # Add SQL injection attempts
        sql_errors = [
            "SELECT * FROM users WHERE id = 1 OR 1=1",
            "'; DROP TABLE users; --",
            "UNION SELECT * FROM passwords",
        ]

        for i, error in enumerate(sql_errors * 3):  # Repeat to trigger detection
            detector.add_error(base_time + timedelta(minutes=i), error)

        security_anomalies = detector.detect_security_anomalies()
        assert len(security_anomalies) > 0

        sql_anomalies = [a for a in security_anomalies if "SQL" in a.anomaly_type]
        assert len(sql_anomalies) > 0

    def test_detect_security_anomalies_auth_failures(self):
        """Test authentication failure detection."""
        detector = AnomalyDetector()

        base_time = datetime.utcnow()

        # Add many auth failures
        for i in range(15):
            detector.add_error(
                base_time + timedelta(minutes=i),
                "Authentication failed: Invalid credentials",
            )

        security_anomalies = detector.detect_security_anomalies()
        auth_anomalies = [a for a in security_anomalies if "AUTH" in a.anomaly_type]
        assert len(auth_anomalies) > 0

    def test_generate_alerts(self):
        """Test alert generation."""
        detector = AnomalyDetector()

        # Create mock anomalies
        from socialseed_e2e.analytics.anomaly_detector import AnomalyResult

        anomaly = AnomalyResult(
            is_anomaly=True,
            anomaly_type=AnomalyType.RESPONSE_TIME,
            method=DetectionMethod.Z_SCORE,
            value=500.0,
            expected_range=(0, 200),
            severity=AlertSeverity.HIGH,
            confidence=0.95,
            description="High response time detected",
            timestamp=datetime.utcnow(),
        )

        alerts = detector.generate_alerts([anomaly], [], [])
        assert len(alerts) == 1
        assert alerts[0].severity == AlertSeverity.HIGH
        assert alerts[0].alert_type == AlertType.PERFORMANCE_DEGRADATION

    def test_generate_report(self):
        """Test report generation."""
        detector = AnomalyDetector()

        # Add some data
        base_time = datetime.utcnow()
        for i in range(20):
            snapshot = MetricSnapshot(
                timestamp=base_time + timedelta(minutes=i),
                response_time_ms=100.0,
                error_rate=0.02,
            )
            detector.add_metric(snapshot)

        report = detector.generate_report()
        assert report is not None
        assert "summary" in report.to_dict()

    def test_acknowledge_alert(self):
        """Test alert acknowledgment."""
        detector = AnomalyDetector()

        # Create and add alert
        from socialseed_e2e.analytics.anomaly_detector import AnomalyResult, Alert

        anomaly = AnomalyResult(
            is_anomaly=True,
            anomaly_type=AnomalyType.ERROR_RATE,
            method=DetectionMethod.THRESHOLD,
            value=0.15,
            expected_range=(0, 0.1),
            severity=AlertSeverity.CRITICAL,
            confidence=1.0,
            description="Error rate exceeded threshold",
            timestamp=datetime.utcnow(),
        )

        alert = Alert(
            alert_id="TEST-001",
            alert_type=AlertType.ERROR_SPIKE,
            severity=AlertSeverity.CRITICAL,
            message="Test alert",
            anomaly_result=anomaly,
            timestamp=datetime.utcnow(),
            acknowledged=False,
        )

        detector._alerts.append(alert)

        # Acknowledge
        result = detector.acknowledge_alert("TEST-001")
        assert result is True
        assert alert.acknowledged is True

    def test_get_unacknowledged_alerts(self):
        """Test getting unacknowledged alerts."""
        detector = AnomalyDetector()

        # Create alerts
        from socialseed_e2e.analytics.anomaly_detector import AnomalyResult, Alert

        for i in range(3):
            anomaly = AnomalyResult(
                is_anomaly=True,
                anomaly_type=AnomalyType.RESPONSE_TIME,
                method=DetectionMethod.Z_SCORE,
                value=200.0,
                expected_range=(0, 100),
                severity=AlertSeverity.HIGH,
                confidence=0.9,
                description="Test",
                timestamp=datetime.utcnow(),
            )

            alert = Alert(
                alert_id=f"TEST-{i}",
                alert_type=AlertType.PERFORMANCE_DEGRADATION,
                severity=AlertSeverity.HIGH,
                message=f"Test {i}",
                anomaly_result=anomaly,
                timestamp=datetime.utcnow(),
                acknowledged=(i == 0),  # First one acknowledged
            )
            detector._alerts.append(alert)

        unacknowledged = detector.get_unacknowledged_alerts()
        assert len(unacknowledged) == 2

    def test_clear_history(self):
        """Test clearing history."""
        detector = AnomalyDetector()

        detector.add_metric(MetricSnapshot(timestamp=datetime.utcnow()))
        detector.add_error(datetime.utcnow(), "error")

        detector.clear_history()

        assert len(detector._history) == 0
        assert len(detector._error_history) == 0


class TestTrendAnalyzer:
    """Test TrendAnalyzer class."""

    def test_analyze_trend_increasing(self):
        """Test trend analysis with increasing data."""
        analyzer = TrendAnalyzer()

        timestamps = [datetime.utcnow() + timedelta(hours=i) for i in range(20)]
        values = [100 + i * 5 for i in range(20)]  # Increasing trend

        trend = analyzer.analyze_trend(timestamps, values, "response_time")

        assert trend is not None
        assert trend.direction == TrendDirectionAnalyzer.INCREASING
        assert trend.slope > 0

    def test_analyze_trend_decreasing(self):
        """Test trend analysis with decreasing data."""
        analyzer = TrendAnalyzer()

        timestamps = [datetime.utcnow() + timedelta(hours=i) for i in range(20)]
        values = [200 - i * 5 for i in range(20)]  # Decreasing trend

        trend = analyzer.analyze_trend(timestamps, values, "error_rate")

        assert trend is not None
        assert trend.direction == TrendDirectionAnalyzer.DECREASING
        assert trend.slope < 0

    def test_analyze_trend_stable(self):
        """Test trend analysis with stable data."""
        analyzer = TrendAnalyzer()

        timestamps = [datetime.utcnow() + timedelta(hours=i) for i in range(20)]
        values = [100 + random.gauss(0, 2) for _ in range(20)]  # Stable with noise

        trend = analyzer.analyze_trend(timestamps, values, "throughput")

        assert trend is not None
        assert trend.direction == TrendDirectionAnalyzer.STABLE

    def test_detect_change_points(self):
        """Test change point detection."""
        analyzer = TrendAnalyzer()

        timestamps = [datetime.utcnow() + timedelta(hours=i) for i in range(50)]
        # Values with sudden change
        values = [100] * 25 + [200] * 25

        change_points = analyzer.detect_change_points(timestamps, values, "metric")

        assert len(change_points) > 0

        # Check change point around index 25
        cp = change_points[0]
        assert cp.change_magnitude > 50  # Significant change

    def test_compare_periods(self):
        """Test period comparison."""
        analyzer = TrendAnalyzer()

        period1 = [100, 102, 101, 99, 100]
        period2 = [150, 148, 152, 149, 151]

        result = analyzer.compare_periods(period1, period2, "Week 1", "Week 2")

        assert "change" in result
        assert "change_percent" in result
        assert result["change"] > 0  # Period 2 is higher

    def test_generate_report(self):
        """Test trend report generation."""
        analyzer = TrendAnalyzer()

        timestamps = [datetime.utcnow() + timedelta(hours=i) for i in range(30)]
        metrics = {
            "response_time": [100 + i * 2 for i in range(30)],
            "error_rate": [0.02] * 30,
        }

        report = analyzer.generate_report(timestamps, metrics)

        assert report is not None
        assert len(report.trends) == 2
        assert "summary" in report.to_dict()


class TestPerformanceForecaster:
    """Test PerformanceForecaster class."""

    def test_forecast_linear(self):
        """Test linear forecasting."""
        forecaster = PerformanceForecaster(
            config=ForecastConfig(model=ForecastModel.LINEAR)
        )

        timestamps = [datetime.utcnow() + timedelta(hours=i) for i in range(20)]
        values = [100 + i * 5 for i in range(20)]  # Linear trend

        result = forecaster.forecast(timestamps, values, "metric", periods=5)

        assert result is not None
        assert len(result.forecast_values) == 5
        assert result.model_used == ForecastModel.LINEAR
        assert result.trend_direction == TrendDirection.INCREASING

    def test_forecast_exponential_smoothing(self):
        """Test exponential smoothing forecast."""
        forecaster = PerformanceForecaster(
            config=ForecastConfig(model=ForecastModel.EXPONENTIAL_SMOOTHING)
        )

        timestamps = [datetime.utcnow() + timedelta(hours=i) for i in range(20)]
        values = [100 + random.gauss(0, 10) for _ in range(20)]

        result = forecaster.forecast(timestamps, values, "metric", periods=5)

        assert result is not None
        assert len(result.forecast_values) == 5

    def test_forecast_moving_average(self):
        """Test moving average forecast."""
        forecaster = PerformanceForecaster(
            config=ForecastConfig(model=ForecastModel.MOVING_AVERAGE)
        )

        timestamps = [datetime.utcnow() + timedelta(hours=i) for i in range(20)]
        values = [100 + random.gauss(0, 5) for _ in range(20)]

        result = forecaster.forecast(timestamps, values, "metric", periods=5)

        assert result is not None
        assert len(result.forecast_values) == 5

    def test_forecast_response_time(self):
        """Test response time forecasting."""
        forecaster = PerformanceForecaster()

        timestamps = [datetime.utcnow() + timedelta(minutes=i) for i in range(30)]
        response_times = [100 + i * 10 for i in range(30)]

        result = forecaster.forecast_response_time(
            timestamps, response_times, periods=5
        )

        assert result is not None
        assert result.metric_name == "response_time"
        assert len(result.forecast_values) == 5

    def test_forecast_error_rate(self):
        """Test error rate forecasting."""
        forecaster = PerformanceForecaster()

        timestamps = [datetime.utcnow() + timedelta(minutes=i) for i in range(30)]
        error_rates = [0.02 + i * 0.001 for i in range(30)]

        result = forecaster.forecast_error_rate(timestamps, error_rates, periods=5)

        assert result is not None
        assert result.metric_name == "error_rate"

        # Check values are capped at 1.0
        assert all(v <= 1.0 for v in result.forecast_values)

    def test_predict_capacity_breach(self):
        """Test capacity breach prediction."""
        forecaster = PerformanceForecaster()

        timestamps = [datetime.utcnow() + timedelta(hours=i) for i in range(20)]
        values = [50 + i * 5 for i in range(20)]  # Increasing toward limit

        prediction = forecaster.predict_capacity_breach(
            timestamps, values, capacity_limit=200, metric_name="cpu_usage"
        )

        assert prediction is not None
        assert "breach_predicted" in prediction

    def test_forecast_confidence_intervals(self):
        """Test that confidence intervals are generated."""
        forecaster = PerformanceForecaster()

        timestamps = [datetime.utcnow() + timedelta(hours=i) for i in range(20)]
        values = [100 + random.gauss(0, 5) for _ in range(20)]

        result = forecaster.forecast(timestamps, values, "metric", periods=5)

        assert result is not None
        assert len(result.confidence_intervals) == 5

        # Check interval structure
        lower, upper = result.confidence_intervals[0]
        assert lower < upper
        assert lower < result.forecast_values[0] < upper


class TestIntegration:
    """Integration tests combining multiple components."""

    def test_end_to_end_workflow(self):
        """Test complete analytics workflow."""
        # Create timestamps and data
        base_time = datetime.utcnow()
        timestamps = [base_time + timedelta(minutes=i * 5) for i in range(50)]

        # Generate synthetic data with trend and anomaly
        values = []
        for i in range(50):
            if i == 40:  # Inject anomaly
                values.append(500)  # Spike
            else:
                values.append(100 + i * 2 + random.gauss(0, 5))

        # 1. Analyze trends
        trend_analyzer = TrendAnalyzer()
        trend = trend_analyzer.analyze_trend(timestamps, values, "response_time")
        assert trend is not None

        # 2. Detect anomalies
        detector = AnomalyDetector()
        for ts, val in zip(timestamps, values):
            detector.add_metric(MetricSnapshot(timestamp=ts, response_time_ms=val))

        anomalies = detector.detect_response_time_anomalies()
        assert len(anomalies) > 0  # Should detect the spike

        # 3. Forecast future
        forecaster = PerformanceForecaster()
        forecast = forecaster.forecast(timestamps, values, "response_time", periods=10)
        assert forecast is not None
        assert len(forecast.forecast_values) == 10

        # 4. Generate comprehensive report
        report = detector.generate_report()
        assert report is not None
        assert len(report.anomalies) > 0

    def test_trend_anomaly_forecast_correlation(self):
        """Test correlation between trend detection and anomaly detection."""
        timestamps = [datetime.utcnow() + timedelta(hours=i) for i in range(30)]

        # Create data with strong trend
        values = [100 + i * 10 for i in range(30)]

        # Analyze trend
        trend_analyzer = TrendAnalyzer()
        trend = trend_analyzer.analyze_trend(timestamps, values, "metric")

        # Should be increasing trend
        assert trend.direction == TrendDirectionAnalyzer.INCREASING

        # Forecast should continue trend
        forecaster = PerformanceForecaster()
        forecast = forecaster.forecast(timestamps, values, "metric", periods=5)

        assert forecast.trend_direction == TrendDirection.INCREASING

        # Forecasted values should be higher than last actual value
        assert forecast.forecast_values[0] > values[-1]
