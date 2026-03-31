"""
AI Performance Anomaly Detection - EPIC-015
ML-based detection of performance degradation.
"""

import statistics
import threading
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np
from pydantic import BaseModel


class AnomalyType(str, Enum):
    """Types of performance anomalies."""
    LATENCY_SPIKE = "latency_spike"
    LATENCY_TREND = "latency_trend"
    THROUGHPUT_DROP = "throughput_drop"
    ERROR_RATE_INCREASE = "error_rate_increase"
    RESOURCE_USAGE = "resource_usage"


class AnomalySeverity(str, Enum):
    """Severity of detected anomalies."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AnomalyStatus(str, Enum):
    """Status of an anomaly."""
    DETECTED = "detected"
    INVESTIGATING = "investigating"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


@dataclass
class PerformanceBaseline:
    """Performance baseline for an endpoint."""
    endpoint: str
    method: str
    sample_size: int = 0
    mean_latency_ms: float = 0.0
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    std_dev: float = 0.0
    requests_per_second: float = 0.0
    error_rate: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class Anomaly:
    """Detected performance anomaly."""
    id: str
    anomaly_type: AnomalyType
    endpoint: str
    severity: AnomalySeverity
    baseline_value: float
    current_value: float
    deviation: float
    status: AnomalyStatus = AnomalyStatus.DETECTED
    detected_at: datetime = field(default_factory=datetime.now)
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    description: str = ""
    recommendations: List[str] = field(default_factory=list)


class PerformanceMetricsCollector:
    """Collects performance metrics for baseline creation."""
    
    def __init__(self, window_size: int = 1000):
        self.window_size = window_size
        self._metrics: Dict[str, deque] = {}
        self._lock = threading.Lock()
    
    def record_request(
        self,
        endpoint: str,
        method: str,
        latency_ms: float,
        status_code: int,
    ) -> None:
        """Record a request for metrics."""
        key = f"{method}:{endpoint}"
        
        with self._lock:
            if key not in self._metrics:
                self._metrics[key] = deque(maxlen=self.window_size)
            
            self._metrics[key].append({
                "latency_ms": latency_ms,
                "status_code": status_code,
                "timestamp": datetime.now(),
            })
    
    def get_baseline(self, endpoint: str, method: str) -> PerformanceBaseline:
        """Calculate baseline for an endpoint."""
        key = f"{method}:{endpoint}"
        
        with self._lock:
            data = self._metrics.get(key, [])
            
            if not data:
                return PerformanceBaseline(endpoint=endpoint, method=method)
            
            latencies = [d["latency_ms"] for d in data]
            errors = [d for d in data if d["status_code"] >= 400]
            
            if not latencies:
                return PerformanceBaseline(endpoint=endpoint, method=method)
            
            sorted_latencies = sorted(latencies)
            n = len(sorted_latencies)
            
            baseline = PerformanceBaseline(
                endpoint=endpoint,
                method=method,
                sample_size=n,
                mean_latency_ms=statistics.mean(latencies),
                p50_latency_ms=sorted_latencies[int(n * 0.5)] if n > 0 else 0,
                p95_latency_ms=sorted_latencies[int(n * 0.95)] if n > 0 else 0,
                p99_latency_ms=sorted_latencies[int(n * 0.99)] if n > 0 else 0,
                std_dev=statistics.stdev(latencies) if len(latencies) > 1 else 0,
                error_rate=len(errors) / n if n > 0 else 0,
                last_updated=datetime.now(),
            )
            
            return baseline
    
    def get_all_baselines(self) -> List[PerformanceBaseline]:
        """Get baselines for all endpoints."""
        baselines = []
        
        with self._lock:
            keys = list(self._metrics.keys())
        
        for key in keys:
            method, endpoint = key.split(":", 1)
            baseline = self.get_baseline(endpoint, method)
            baselines.append(baseline)
        
        return baselines


class AnomalyDetector:
    """Detects performance anomalies using statistical methods."""
    
    def __init__(
        self,
        sensitivity: float = 2.0,
        min_samples: int = 30,
    ):
        self.sensitivity = sensitivity
        self.min_samples = min_samples
        self._active_anomalies: Dict[str, Anomaly] = {}
        self._lock = threading.Lock()
    
    def detect(
        self,
        current_baseline: PerformanceBaseline,
        current_latency: float,
    ) -> List[Anomaly]:
        """Detect anomalies in current metrics."""
        anomalies = []
        
        if current_baseline.sample_size < self.min_samples:
            return anomalies
        
        import uuid
        z_score = (current_latency - current_baseline.mean_latency_ms) / current_baseline.std_dev if current_baseline.std_dev > 0 else 0
        
        if abs(z_score) > self.sensitivity:
            severity = AnomalySeverity.CRITICAL if abs(z_score) > self.sensitivity * 2 else AnomalySeverity.WARNING
            
            anomaly = Anomaly(
                id=f"anomaly-{uuid.uuid4().hex[:8]}",
                anomaly_type=AnomalyType.LATENCY_SPIKE,
                endpoint=current_baseline.endpoint,
                severity=severity,
                baseline_value=current_baseline.mean_latency_ms,
                current_value=current_latency,
                deviation=z_score,
                description=f"Latency deviation of {z_score:.2f} standard deviations from baseline",
            )
            anomalies.append(anomaly)
            
            with self._lock:
                self._active_anomalies[anomaly.id] = anomaly
        
        p95_diff = current_latency - current_baseline.p95_latency_ms
        if p95_diff > 0 and p95_diff / current_baseline.p95_latency_ms > 0.5:
            anomaly = Anomaly(
                id=f"anomaly-{uuid.uuid4().hex[:8]}",
                anomaly_type=AnomalyType.LATENCY_TREND,
                endpoint=current_baseline.endpoint,
                severity=AnomalySeverity.WARNING,
                baseline_value=current_baseline.p95_latency_ms,
                current_value=current_latency,
                deviation=p95_diff,
                description=f"Current latency {p95_diff:.1f}ms above p95 baseline",
                recommendations=[
                    "Check for database query degradation",
                    "Review recent code changes",
                    "Check for increased load or traffic pattern changes",
                ],
            )
            anomalies.append(anomaly)
            
            with self._lock:
                self._active_anomalies[anomaly.id] = anomaly
        
        return anomalies
    
    def get_active_anomalies(self) -> List[Anomaly]:
        """Get all active anomalies."""
        return list(self._active_anomalies.values())
    
    def acknowledge_anomaly(self, anomaly_id: str) -> bool:
        """Acknowledge an anomaly."""
        with self._lock:
            if anomaly_id in self._active_anomalies:
                anomaly = self._active_anomalies[anomaly_id]
                anomaly.status = AnomalyStatus.ACKNOWLEDGED
                anomaly.acknowledged_at = datetime.now()
                return True
            return False
    
    def resolve_anomaly(self, anomaly_id: str) -> bool:
        """Resolve an anomaly."""
        with self._lock:
            if anomaly_id in self._active_anomalies:
                anomaly = self._active_anomalies[anomaly_id]
                anomaly.status = AnomalyStatus.RESOLVED
                anomaly.resolved_at = datetime.now()
                del self._active_anomalies[anomaly_id]
                return True
            return False


class PerformanceAnomalyManager:
    """Main manager for performance anomaly detection."""
    
    def __init__(self):
        self.collector = PerformanceMetricsCollector()
        self.detector = AnomalyDetector()
    
    def record_request(
        self,
        endpoint: str,
        method: str,
        latency_ms: float,
        status_code: int,
    ) -> None:
        """Record a request and check for anomalies."""
        self.collector.record_request(endpoint, method, latency_ms, status_code)
    
    def check_for_anomalies(
        self,
        endpoint: str,
        method: str,
        current_latency: float,
    ) -> List[Anomaly]:
        """Check for anomalies on an endpoint."""
        baseline = self.collector.get_baseline(endpoint, method)
        return self.detector.detect(baseline, current_latency)
    
    def get_baselines(self) -> List[Dict[str, Any]]:
        """Get all performance baselines."""
        baselines = self.collector.get_all_baselines()
        return [
            {
                "endpoint": b.endpoint,
                "method": b.method,
                "sample_size": b.sample_size,
                "mean_latency_ms": round(b.mean_latency_ms, 2),
                "p50_latency_ms": round(b.p50_latency_ms, 2),
                "p95_latency_ms": round(b.p95_latency_ms, 2),
                "p99_latency_ms": round(b.p99_latency_ms, 2),
                "std_dev": round(b.std_dev, 2),
                "error_rate": round(b.error_rate * 100, 2),
                "last_updated": b.last_updated.isoformat(),
            }
            for b in baselines
        ]
    
    def get_anomalies(
        self,
        status: Optional[AnomalyStatus] = None,
    ) -> List[Dict[str, Any]]:
        """Get anomalies."""
        anomalies = self.detector.get_active_anomalies()
        
        if status:
            anomalies = [a for a in anomalies if a.status == status]
        
        return [
            {
                "id": a.id,
                "type": a.anomaly_type.value,
                "endpoint": a.endpoint,
                "severity": a.severity.value,
                "baseline_value": round(a.baseline_value, 2),
                "current_value": round(a.current_value, 2),
                "deviation": round(a.deviation, 2),
                "status": a.status.value,
                "detected_at": a.detected_at.isoformat(),
                "description": a.description,
                "recommendations": a.recommendations,
            }
            for a in anomalies
        ]


_global_manager: Optional[PerformanceAnomalyManager] = None


def get_anomaly_manager() -> PerformanceAnomalyManager:
    """Get global anomaly manager."""
    global _global_manager
    if _global_manager is None:
        _global_manager = PerformanceAnomalyManager()
    return _global_manager
