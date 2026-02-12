"""Anomaly Detector for Test Results and Performance.

This module provides statistical and ML-based anomaly detection for:
- Response time anomalies
- Error pattern anomalies
- Data quality issues
- Security anomalies
"""

import hashlib
import re
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


class AnomalyType(str, Enum):
    """Types of anomalies that can be detected."""

    RESPONSE_TIME = "response_time"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"
    DATA_QUALITY = "data_quality"
    SECURITY = "security"
    BEHAVIORAL = "behavioral"
    SEASONAL = "seasonal"


class DetectionMethod(str, Enum):
    """Methods for detecting anomalies."""

    Z_SCORE = "z_score"
    IQR = "iqr"
    MAD = "mad"
    ISOLATION_FOREST = "isolation_forest"
    STATISTICAL = "statistical"
    THRESHOLD = "threshold"
    PATTERN_MATCH = "pattern_match"


class AlertSeverity(str, Enum):
    """Severity levels for alerts."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertType(str, Enum):
    """Types of alerts."""

    PERFORMANCE_DEGRADATION = "performance_degradation"
    ERROR_SPIKE = "error_spike"
    SECURITY_THREAT = "security_threat"
    DATA_QUALITY_ISSUE = "data_quality_issue"
    UNUSUAL_PATTERN = "unusual_pattern"
    THRESHOLD_BREACH = "threshold_breach"


class AnomalyResult:
    """Result of anomaly detection."""

    def __init__(
        self,
        is_anomaly: bool,
        anomaly_type: AnomalyType,
        method: DetectionMethod,
        value: Any,
        expected_range: Tuple[Any, Any],
        severity: AlertSeverity,
        confidence: float,
        description: str,
        timestamp: datetime,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.is_anomaly = is_anomaly
        self.anomaly_type = anomaly_type
        self.method = method
        self.value = value
        self.expected_range = expected_range
        self.severity = severity
        self.confidence = confidence
        self.description = description
        self.timestamp = timestamp
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "is_anomaly": self.is_anomaly,
            "anomaly_type": self.anomaly_type.value,
            "method": self.method.value,
            "value": self.value,
            "expected_range": self.expected_range,
            "severity": self.severity.value,
            "confidence": self.confidence,
            "description": self.description,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


class Alert:
    """Alert for detected anomaly."""

    def __init__(
        self,
        alert_id: str,
        alert_type: AlertType,
        severity: AlertSeverity,
        message: str,
        anomaly_result: AnomalyResult,
        timestamp: datetime,
        acknowledged: bool = False,
    ):
        self.alert_id = alert_id
        self.alert_type = alert_type
        self.severity = severity
        self.message = message
        self.anomaly_result = anomaly_result
        self.timestamp = timestamp
        self.acknowledged = acknowledged

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "alert_id": self.alert_id,
            "alert_type": self.alert_type.value,
            "severity": self.severity.value,
            "message": self.message,
            "anomaly_result": self.anomaly_result.to_dict(),
            "timestamp": self.timestamp.isoformat(),
            "acknowledged": self.acknowledged,
        }


class ErrorPattern:
    """Pattern detected in error messages."""

    def __init__(
        self,
        pattern: str,
        frequency: int,
        first_seen: datetime,
        last_seen: datetime,
        error_type: str,
        severity: AlertSeverity,
        sample_messages: List[str],
    ):
        self.pattern = pattern
        self.frequency = frequency
        self.first_seen = first_seen
        self.last_seen = last_seen
        self.error_type = error_type
        self.severity = severity
        self.sample_messages = sample_messages

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pattern": self.pattern,
            "frequency": self.frequency,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "error_type": self.error_type,
            "severity": self.severity.value,
            "sample_messages": self.sample_messages,
        }


class SecurityAnomaly:
    """Security-related anomaly."""

    def __init__(
        self,
        anomaly_type: str,
        severity: AlertSeverity,
        description: str,
        indicators: List[str],
        timestamp: datetime,
        confidence: float,
    ):
        self.anomaly_type = anomaly_type
        self.severity = severity
        self.description = description
        self.indicators = indicators
        self.timestamp = timestamp
        self.confidence = confidence

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "anomaly_type": self.anomaly_type,
            "severity": self.severity.value,
            "description": self.description,
            "indicators": self.indicators,
            "timestamp": self.timestamp.isoformat(),
            "confidence": self.confidence,
        }


class MetricSnapshot:
    """Snapshot of metric values at a point in time."""

    def __init__(
        self,
        timestamp: datetime,
        response_time_ms: Optional[float] = None,
        error_rate: Optional[float] = None,
        throughput: Optional[float] = None,
        cpu_percent: Optional[float] = None,
        memory_percent: Optional[float] = None,
        custom_metrics: Optional[Dict[str, float]] = None,
    ):
        self.timestamp = timestamp
        self.response_time_ms = response_time_ms
        self.error_rate = error_rate
        self.throughput = throughput
        self.cpu_percent = cpu_percent
        self.memory_percent = memory_percent
        self.custom_metrics = custom_metrics or {}

    def get_all_metrics(self) -> Dict[str, float]:
        """Get all metrics as a dictionary."""
        metrics = {}
        if self.response_time_ms is not None:
            metrics["response_time_ms"] = self.response_time_ms
        if self.error_rate is not None:
            metrics["error_rate"] = self.error_rate
        if self.throughput is not None:
            metrics["throughput"] = self.throughput
        if self.cpu_percent is not None:
            metrics["cpu_percent"] = self.cpu_percent
        if self.memory_percent is not None:
            metrics["memory_percent"] = self.memory_percent
        metrics.update(self.custom_metrics)
        return metrics


class AnomalyConfig:
    """Configuration for anomaly detection."""

    def __init__(
        self,
        z_score_threshold: float = 3.0,
        iqr_multiplier: float = 1.5,
        mad_threshold: float = 3.5,
        min_data_points: int = 10,
        response_time_threshold_ms: Optional[float] = None,
        error_rate_threshold: Optional[float] = None,
        throughput_threshold: Optional[float] = None,
        enable_seasonality_detection: bool = True,
        seasonality_period: Optional[timedelta] = None,
    ):
        self.z_score_threshold = z_score_threshold
        self.iqr_multiplier = iqr_multiplier
        self.mad_threshold = mad_threshold
        self.min_data_points = min_data_points
        self.response_time_threshold_ms = response_time_threshold_ms
        self.error_rate_threshold = error_rate_threshold
        self.throughput_threshold = throughput_threshold
        self.enable_seasonality_detection = enable_seasonality_detection
        self.seasonality_period = seasonality_period or timedelta(hours=24)


class AnomalyReport:
    """Complete anomaly detection report."""

    def __init__(
        self,
        start_time: datetime,
        end_time: datetime,
        anomalies: List[AnomalyResult],
        alerts: List[Alert],
        error_patterns: List[ErrorPattern],
        security_anomalies: List[SecurityAnomaly],
        summary: Dict[str, Any],
    ):
        self.start_time = start_time
        self.end_time = end_time
        self.anomalies = anomalies
        self.alerts = alerts
        self.error_patterns = error_patterns
        self.security_anomalies = security_anomalies
        self.summary = summary

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "anomalies": [a.to_dict() for a in self.anomalies],
            "alerts": [a.to_dict() for a in self.alerts],
            "error_patterns": [p.to_dict() for p in self.error_patterns],
            "security_anomalies": [s.to_dict() for s in self.security_anomalies],
            "summary": self.summary,
        }


class AnomalyDetector:
    """Main class for detecting anomalies in test results and performance."""

    def __init__(self, config: Optional[AnomalyConfig] = None):
        """Initialize the anomaly detector.

        Args:
            config: Configuration for anomaly detection
        """
        self.config = config or AnomalyConfig()
        self._history: List[MetricSnapshot] = []
        self._error_history: List[Tuple[datetime, str]] = []
        self._alerts: List[Alert] = []
        self._baseline_stats: Dict[str, Dict[str, float]] = {}

    def add_metric(self, snapshot: MetricSnapshot) -> None:
        """Add a metric snapshot to history.

        Args:
            snapshot: Metric snapshot to add
        """
        self._history.append(snapshot)
        # Keep only last 1000 snapshots to prevent memory issues
        if len(self._history) > 1000:
            self._history = self._history[-1000:]

    def add_error(self, timestamp: datetime, error_message: str) -> None:
        """Add an error to history.

        Args:
            timestamp: When the error occurred
            error_message: Error message
        """
        self._error_history.append((timestamp, error_message))
        # Keep only last 500 errors
        if len(self._error_history) > 500:
            self._error_history = self._error_history[-500:]

    def detect_response_time_anomalies(self, recent_minutes: int = 30) -> List[AnomalyResult]:
        """Detect anomalies in response times.

        Args:
            recent_minutes: Time window to analyze

        Returns:
            List of detected anomalies
        """
        cutoff = datetime.utcnow() - timedelta(minutes=recent_minutes)
        recent_snapshots = [s for s in self._history if s.timestamp >= cutoff]

        if len(recent_snapshots) < self.config.min_data_points:
            return []

        response_times = [
            s.response_time_ms for s in recent_snapshots if s.response_time_ms is not None
        ]

        if len(response_times) < self.config.min_data_points:
            return []

        anomalies = []

        # Z-score method
        z_anomalies = self._detect_with_z_score(response_times, AnomalyType.RESPONSE_TIME)
        anomalies.extend(z_anomalies)

        # IQR method
        iqr_anomalies = self._detect_with_iqr(response_times, AnomalyType.RESPONSE_TIME)
        anomalies.extend(iqr_anomalies)

        # Threshold-based detection
        if self.config.response_time_threshold_ms:
            for i, rt in enumerate(response_times):
                if rt > self.config.response_time_threshold_ms:
                    anomalies.append(
                        AnomalyResult(
                            is_anomaly=True,
                            anomaly_type=AnomalyType.RESPONSE_TIME,
                            method=DetectionMethod.THRESHOLD,
                            value=rt,
                            expected_range=(0, self.config.response_time_threshold_ms),
                            severity=AlertSeverity.HIGH
                            if rt > self.config.response_time_threshold_ms * 2
                            else AlertSeverity.MEDIUM,
                            confidence=1.0,
                            description=f"Response time {rt}ms exceeds threshold {self.config.response_time_threshold_ms}ms",
                            timestamp=recent_snapshots[i].timestamp,
                        )
                    )

        return anomalies

    def detect_error_rate_anomalies(self, recent_minutes: int = 30) -> List[AnomalyResult]:
        """Detect anomalies in error rates.

        Args:
            recent_minutes: Time window to analyze

        Returns:
            List of detected anomalies
        """
        cutoff = datetime.utcnow() - timedelta(minutes=recent_minutes)
        recent_snapshots = [s for s in self._history if s.timestamp >= cutoff]

        if len(recent_snapshots) < self.config.min_data_points:
            return []

        error_rates = [s.error_rate for s in recent_snapshots if s.error_rate is not None]

        if len(error_rates) < self.config.min_data_points:
            return []

        anomalies = []

        # Statistical detection
        stat_anomalies = self._detect_with_z_score(error_rates, AnomalyType.ERROR_RATE)
        anomalies.extend(stat_anomalies)

        # Threshold-based detection
        if self.config.error_rate_threshold:
            for i, er in enumerate(error_rates):
                if er > self.config.error_rate_threshold:
                    anomalies.append(
                        AnomalyResult(
                            is_anomaly=True,
                            anomaly_type=AnomalyType.ERROR_RATE,
                            method=DetectionMethod.THRESHOLD,
                            value=er,
                            expected_range=(0, self.config.error_rate_threshold),
                            severity=AlertSeverity.CRITICAL if er > 0.1 else AlertSeverity.HIGH,
                            confidence=1.0,
                            description=f"Error rate {er:.2%} exceeds threshold {self.config.error_rate_threshold:.2%}",
                            timestamp=recent_snapshots[i].timestamp,
                        )
                    )

        return anomalies

    def detect_error_patterns(self, recent_minutes: int = 60) -> List[ErrorPattern]:
        """Detect unusual error patterns.

        Args:
            recent_minutes: Time window to analyze

        Returns:
            List of detected error patterns
        """
        cutoff = datetime.utcnow() - timedelta(minutes=recent_minutes)
        recent_errors = [(ts, msg) for ts, msg in self._error_history if ts >= cutoff]

        if len(recent_errors) < 5:
            return []

        patterns = self._extract_error_patterns(recent_errors)

        # Identify unusual patterns (high frequency or new patterns)
        unusual_patterns = []
        for pattern, data in patterns.items():
            frequency = len(data["messages"])
            if frequency >= 5:  # Threshold for pattern significance
                unusual_patterns.append(
                    ErrorPattern(
                        pattern=pattern,
                        frequency=frequency,
                        first_seen=data["first_seen"],
                        last_seen=data["last_seen"],
                        error_type=data["error_type"],
                        severity=AlertSeverity.HIGH if frequency > 20 else AlertSeverity.MEDIUM,
                        sample_messages=data["messages"][:5],
                    )
                )

        return unusual_patterns

    def detect_security_anomalies(self, recent_minutes: int = 60) -> List[SecurityAnomaly]:
        """Detect security-related anomalies.

        Args:
            recent_minutes: Time window to analyze

        Returns:
            List of security anomalies
        """
        cutoff = datetime.utcnow() - timedelta(minutes=recent_minutes)
        recent_errors = [(ts, msg) for ts, msg in self._error_history if ts >= cutoff]

        security_anomalies = []

        # Check for SQL injection attempts
        sql_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER)\b.*\b(FROM|INTO|TABLE)\b)",
            r"(\bOR\b.*\b=\b.*\bOR\b)",
            r"('|--|;|/\*|\*/)",
        ]

        sql_attempts = []
        for ts, msg in recent_errors:
            for pattern in sql_patterns:
                if re.search(pattern, msg, re.IGNORECASE):
                    sql_attempts.append((ts, msg))
                    break

        if len(sql_attempts) >= 3:
            security_anomalies.append(
                SecurityAnomaly(
                    anomaly_type="SQL_INJECTION_ATTEMPT",
                    severity=AlertSeverity.CRITICAL,
                    description=f"Detected {len(sql_attempts)} potential SQL injection attempts",
                    indicators=[msg[:100] for _, msg in sql_attempts[:5]],
                    timestamp=datetime.utcnow(),
                    confidence=min(1.0, len(sql_attempts) / 10),
                )
            )

        # Check for authentication failures
        auth_failures = [
            (ts, msg)
            for ts, msg in recent_errors
            if any(
                keyword in msg.lower()
                for keyword in [
                    "unauthorized",
                    "authentication",
                    "login failed",
                    "invalid credentials",
                ]
            )
        ]

        if len(auth_failures) >= 10:
            security_anomalies.append(
                SecurityAnomaly(
                    anomaly_type="AUTHENTICATION_FAILURE_SPIKE",
                    severity=AlertSeverity.HIGH,
                    description=f"Detected {len(auth_failures)} authentication failures",
                    indicators=["Multiple failed login attempts"],
                    timestamp=datetime.utcnow(),
                    confidence=min(1.0, len(auth_failures) / 50),
                )
            )

        # Check for unusual access patterns
        cutoff_access = datetime.utcnow() - timedelta(minutes=5)
        recent_requests = [s for s in self._history if s.timestamp >= cutoff_access]
        if len(recent_requests) > 1000:  # Unusually high traffic
            security_anomalies.append(
                SecurityAnomaly(
                    anomaly_type="HIGH_TRAFFIC_ANOMALY",
                    severity=AlertSeverity.MEDIUM,
                    description=f"Unusually high traffic: {len(recent_requests)} requests in 5 minutes",
                    indicators=["Possible DDoS or load spike"],
                    timestamp=datetime.utcnow(),
                    confidence=0.7,
                )
            )

        return security_anomalies

    def generate_alerts(
        self,
        anomalies: List[AnomalyResult],
        error_patterns: List[ErrorPattern],
        security_anomalies: List[SecurityAnomaly],
    ) -> List[Alert]:
        """Generate alerts from detected anomalies.

        Args:
            anomalies: Detected anomalies
            error_patterns: Detected error patterns
            security_anomalies: Detected security anomalies

        Returns:
            List of alerts
        """
        alerts = []

        # Generate alerts from anomalies
        for anomaly in anomalies:
            if anomaly.is_anomaly:
                alert_type = self._map_anomaly_to_alert_type(anomaly.anomaly_type)
                alert = Alert(
                    alert_id=self._generate_alert_id(),
                    alert_type=alert_type,
                    severity=anomaly.severity,
                    message=anomaly.description,
                    anomaly_result=anomaly,
                    timestamp=anomaly.timestamp,
                )
                alerts.append(alert)

        # Generate alerts from error patterns
        for pattern in error_patterns:
            if pattern.frequency >= 10:
                alert = Alert(
                    alert_id=self._generate_alert_id(),
                    alert_type=AlertType.ERROR_SPIKE,
                    severity=pattern.severity,
                    message=f"Recurring error pattern detected: {pattern.pattern} ({pattern.frequency} occurrences)",
                    anomaly_result=AnomalyResult(
                        is_anomaly=True,
                        anomaly_type=AnomalyType.ERROR_RATE,
                        method=DetectionMethod.PATTERN_MATCH,
                        value=pattern.frequency,
                        expected_range=(0, 5),
                        severity=pattern.severity,
                        confidence=0.8,
                        description=f"Error pattern: {pattern.pattern}",
                        timestamp=pattern.last_seen,
                    ),
                    timestamp=pattern.last_seen,
                )
                alerts.append(alert)

        # Generate alerts from security anomalies
        for security in security_anomalies:
            alert = Alert(
                alert_id=self._generate_alert_id(),
                alert_type=AlertType.SECURITY_THREAT,
                severity=security.severity,
                message=security.description,
                anomaly_result=AnomalyResult(
                    is_anomaly=True,
                    anomaly_type=AnomalyType.SECURITY,
                    method=DetectionMethod.PATTERN_MATCH,
                    value=security.confidence,
                    expected_range=(0, 0.5),
                    severity=security.severity,
                    confidence=security.confidence,
                    description=security.description,
                    timestamp=security.timestamp,
                    metadata={"indicators": security.indicators},
                ),
                timestamp=security.timestamp,
            )
            alerts.append(alert)

        self._alerts.extend(alerts)
        return alerts

    def generate_report(
        self, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None
    ) -> AnomalyReport:
        """Generate comprehensive anomaly report.

        Args:
            start_time: Start of analysis period
            end_time: End of analysis period

        Returns:
            Complete anomaly report
        """
        end_time = end_time or datetime.utcnow()
        start_time = start_time or (end_time - timedelta(hours=24))

        # Detect all types of anomalies
        response_time_anomalies = self.detect_response_time_anomalies()
        error_rate_anomalies = self.detect_error_rate_anomalies()
        error_patterns = self.detect_error_patterns()
        security_anomalies = self.detect_security_anomalies()

        all_anomalies = response_time_anomalies + error_rate_anomalies
        alerts = self.generate_alerts(all_anomalies, error_patterns, security_anomalies)

        # Generate summary
        summary = {
            "total_anomalies": len(all_anomalies),
            "critical_anomalies": len(
                [a for a in all_anomalies if a.severity == AlertSeverity.CRITICAL]
            ),
            "high_anomalies": len([a for a in all_anomalies if a.severity == AlertSeverity.HIGH]),
            "total_alerts": len(alerts),
            "unacknowledged_alerts": len([a for a in alerts if not a.acknowledged]),
            "error_patterns_found": len(error_patterns),
            "security_threats": len(security_anomalies),
        }

        return AnomalyReport(
            start_time=start_time,
            end_time=end_time,
            anomalies=all_anomalies,
            alerts=alerts,
            error_patterns=error_patterns,
            security_anomalies=security_anomalies,
            summary=summary,
        )

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert.

        Args:
            alert_id: ID of alert to acknowledge

        Returns:
            True if alert was found and acknowledged
        """
        for alert in self._alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                return True
        return False

    def get_unacknowledged_alerts(self) -> List[Alert]:
        """Get all unacknowledged alerts.

        Returns:
            List of unacknowledged alerts
        """
        return [a for a in self._alerts if not a.acknowledged]

    def clear_history(self) -> None:
        """Clear all historical data."""
        self._history.clear()
        self._error_history.clear()
        self._alerts.clear()
        self._baseline_stats.clear()

    def _detect_with_z_score(
        self, values: List[float], anomaly_type: AnomalyType
    ) -> List[AnomalyResult]:
        """Detect anomalies using Z-score method."""
        if len(values) < self.config.min_data_points:
            return []

        mean = statistics.mean(values)
        std_dev = statistics.stdev(values) if len(values) > 1 else 0

        if std_dev == 0:
            return []

        anomalies = []
        for i, value in enumerate(values):
            z_score = abs((value - mean) / std_dev)
            if z_score > self.config.z_score_threshold:
                severity = (
                    AlertSeverity.CRITICAL
                    if z_score > self.config.z_score_threshold * 1.5
                    else AlertSeverity.HIGH
                    if z_score > self.config.z_score_threshold * 1.2
                    else AlertSeverity.MEDIUM
                )
                anomalies.append(
                    AnomalyResult(
                        is_anomaly=True,
                        anomaly_type=anomaly_type,
                        method=DetectionMethod.Z_SCORE,
                        value=value,
                        expected_range=(mean - 2 * std_dev, mean + 2 * std_dev),
                        severity=severity,
                        confidence=min(1.0, z_score / (self.config.z_score_threshold * 2)),
                        description=f"Z-score {z_score:.2f} exceeds threshold {self.config.z_score_threshold}",
                        timestamp=datetime.utcnow(),
                    )
                )

        return anomalies

    def _detect_with_iqr(
        self, values: List[float], anomaly_type: AnomalyType
    ) -> List[AnomalyResult]:
        """Detect anomalies using Interquartile Range method."""
        if len(values) < self.config.min_data_points:
            return []

        sorted_values = sorted(values)
        q1 = sorted_values[len(sorted_values) // 4]
        q3 = sorted_values[3 * len(sorted_values) // 4]
        iqr = q3 - q1

        lower_bound = q1 - self.config.iqr_multiplier * iqr
        upper_bound = q3 + self.config.iqr_multiplier * iqr

        anomalies = []
        for i, value in enumerate(values):
            if value < lower_bound or value > upper_bound:
                anomalies.append(
                    AnomalyResult(
                        is_anomaly=True,
                        anomaly_type=anomaly_type,
                        method=DetectionMethod.IQR,
                        value=value,
                        expected_range=(lower_bound, upper_bound),
                        severity=AlertSeverity.HIGH,
                        confidence=0.8,
                        description=f"Value {value} outside IQR bounds [{lower_bound:.2f}, {upper_bound:.2f}]",
                        timestamp=datetime.utcnow(),
                    )
                )

        return anomalies

    def _extract_error_patterns(
        self, errors: List[Tuple[datetime, str]]
    ) -> Dict[str, Dict[str, Any]]:
        """Extract patterns from error messages."""
        patterns = defaultdict(
            lambda: {
                "messages": [],
                "first_seen": None,
                "last_seen": None,
                "error_type": "unknown",
            }
        )

        for ts, msg in errors:
            # Simplify error message to find patterns
            simplified = self._simplify_error(msg)

            patterns[simplified]["messages"].append(msg)
            if (
                patterns[simplified]["first_seen"] is None
                or ts < patterns[simplified]["first_seen"]
            ):
                patterns[simplified]["first_seen"] = ts
            if patterns[simplified]["last_seen"] is None or ts > patterns[simplified]["last_seen"]:
                patterns[simplified]["last_seen"] = ts

            # Try to determine error type
            if "connection" in msg.lower():
                patterns[simplified]["error_type"] = "connection"
            elif "timeout" in msg.lower():
                patterns[simplified]["error_type"] = "timeout"
            elif "validation" in msg.lower():
                patterns[simplified]["error_type"] = "validation"
            elif "permission" in msg.lower() or "unauthorized" in msg.lower():
                patterns[simplified]["error_type"] = "authorization"

        return dict(patterns)

    def _simplify_error(self, error_message: str) -> str:
        """Simplify error message to extract pattern."""
        # Remove specific values
        simplified = error_message
        simplified = re.sub(r"\d+", "<NUM>", simplified)
        simplified = re.sub(r"[a-f0-9]{8,}", "<HASH>", simplified, flags=re.IGNORECASE)
        simplified = re.sub(r"'[^']+'", "'<STR>'", simplified)
        simplified = re.sub(r'"[^"]+"', '"<STR>"', simplified)

        # Extract core error type
        if ":" in simplified:
            simplified = simplified.split(":")[0]

        return simplified.strip()

    def _map_anomaly_to_alert_type(self, anomaly_type: AnomalyType) -> AlertType:
        """Map anomaly type to alert type."""
        mapping = {
            AnomalyType.RESPONSE_TIME: AlertType.PERFORMANCE_DEGRADATION,
            AnomalyType.ERROR_RATE: AlertType.ERROR_SPIKE,
            AnomalyType.THROUGHPUT: AlertType.UNUSUAL_PATTERN,
            AnomalyType.DATA_QUALITY: AlertType.DATA_QUALITY_ISSUE,
            AnomalyType.SECURITY: AlertType.SECURITY_THREAT,
        }
        return mapping.get(anomaly_type, AlertType.UNUSUAL_PATTERN)

    def _generate_alert_id(self) -> str:
        """Generate unique alert ID."""
        timestamp = datetime.utcnow().isoformat()
        hash_val = hashlib.md5(timestamp.encode()).hexdigest()[:8]
        return f"ALERT-{hash_val}"
