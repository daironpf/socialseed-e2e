"""
TradingView-style Charts for Traffic Analysis - Enhanced with error detection.

T03: Implementar 'Velas rojas' para picos de inestabilidad (errores 500)
T04: Slider de zoom en tiempo cronológico

This extends the existing observability/tradingview module.
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class CandlestickData:
    """OHLCV-style data for traffic visualization."""
    timestamp: datetime
    open: float      # Min latency in timeframe
    high: float     # Max latency in timeframe
    close: float    # Avg latency in timeframe
    volume: int     # Number of requests
    errors: int = 0 # Number of 5xx errors
    warnings: int = 0 # Number of 4xx errors


@dataclass
class ErrorCluster:
    """Cluster of consecutive errors for visualization."""
    start_time: datetime
    end_time: datetime
    error_count: int
    error_codes: List[int]
    severity: str  # "critical", "warning"


class TrafficChartAnalyzer:
    """Analyze traffic for chart visualization with error detection."""
    
    def __init__(self):
        self._data: List[CandlestickData] = []
        self._timeframe_seconds = 5
    
    def set_timeframe(self, seconds: int):
        """Set the chart timeframe (T04: Slider de zoom)."""
        self._timeframe_seconds = seconds
    
    def process_traffic_logs(self, logs: List[Dict[str, Any]]):
        """Process traffic logs into candlestick data.
        
        T02: Mapear latencias HTTP a Y (eje vertical), tiempo cronológico a X.
        """
        if not logs:
            return
        
        # Sort logs by timestamp
        sorted_logs = sorted(logs, key=lambda x: x.get('timestamp', ''))
        
        # Group by timeframe
        timeframe_buckets: Dict[str, List[Dict]] = {}
        
        for log in sorted_logs:
            ts = log.get('timestamp', '')
            if not ts:
                continue
            
            try:
                dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
            except:
                continue
            
            # Bucket by timeframe
            bucket_time = dt.replace(
                second=(dt.second // self._timeframe_seconds) * self._timeframe_seconds,
                microsecond=0
            )
            bucket_key = bucket_time.isoformat()
            
            if bucket_key not in timeframe_buckets:
                timeframe_buckets[bucket_key] = []
            
            timeframe_buckets[bucket_key].append(log)
        
        # Convert to candlestick data
        self._data = []
        
        for bucket_time, bucket_logs in sorted(timeframe_buckets.items()):
            latencies = [log.get('duration_ms', 0) for log in bucket_logs]
            status_codes = [log.get('status_code', 200) for log in bucket_logs]
            
            if not latencies:
                continue
            
            # Calculate OHLC
            open_price = min(latencies)
            high_price = max(latencies)
            close_price = sum(latencies) / len(latencies)
            
            # Count errors (T03: Detectar errores 500)
            errors_5xx = sum(1 for s in status_codes if s >= 500)
            errors_4xx = sum(1 for s in status_codes if 400 <= s < 500)
            
            candle = CandlestickData(
                timestamp=datetime.fromisoformat(bucket_time),
                open=open_price,
                high=high_price,
                close=close_price,
                volume=len(bucket_logs),
                errors=errors_5xx,
                warnings=errors_4xx,
            )
            
            self._data.append(candle)
    
    def detect_error_clusters(self) -> List[ErrorCluster]:
        """Detect clusters of consecutive errors.
        
        T03: Identificar picos de inestabilidad (errores 500 consecutivos).
        """
        clusters = []
        current_cluster = None
        
        for candle in self._data:
            if candle.errors > 0:
                if current_cluster is None:
                    current_cluster = ErrorCluster(
                        start_time=candle.timestamp,
                        end_time=candle.timestamp,
                        error_count=candle.errors,
                        error_codes=[500] * candle.errors,
                        severity="critical"
                    )
                else:
                    current_cluster.error_count += candle.errors
                    current_cluster.end_time = candle.timestamp
                    current_cluster.error_codes.extend([500] * candle.errors)
            else:
                if current_cluster is not None:
                    clusters.append(current_cluster)
                    current_cluster = None
        
        # Add last cluster if exists
        if current_cluster is not None:
            clusters.append(current_cluster)
        
        # Mark warning clusters (4xx)
        for cluster in clusters:
            if any(s >= 400 and s < 500 for s in cluster.error_codes):
                cluster.severity = "warning"
        
        return clusters
    
    def get_chart_data(self) -> List[Dict[str, Any]]:
        """Get data in format for TradingView Lightweight Charts."""
        result = []
        
        for candle in self._data:
            # Determine color based on errors (T03: Velas rojas para errores)
            # Red candles indicate errors, green indicates success
            color = "rgba(255, 82, 82, 0.8)" if candle.errors > 0 else "rgba(75, 192, 192, 0.8)"
            
            result.append({
                "time": int(candle.timestamp.timestamp()),
                "open": candle.open,
                "high": candle.high,
                "low": candle.open,  # Min latency
                "close": candle.close,
                "color": color,
                "volume": candle.volume,
                "errors": candle.errors,
                "warnings": candle.warnings,
            })
        
        return result
    
    def get_time_range_options(self) -> Dict[str, int]:
        """Get available time range options.
        
        T04: Opciones de zoom (H1, M15, M1, etc.).
        """
        return {
            "1s": 1,
            "5s": 5,
            "15s": 15,
            "30s": 30,
            "1m": 60,
            "5m": 300,
            "15m": 900,
            "30m": 1800,
            "1h": 3600,
        }
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics for the chart."""
        if not self._data:
            return {}
        
        total_requests = sum(c.volume for c in self._data)
        total_errors = sum(c.errors for c in self._data)
        total_warnings = sum(c.warnings for c in self._data)
        
        all_latencies = []
        for c in self._data:
            all_latencies.extend([c.open, c.high, c.close])
        
        return {
            "total_requests": total_requests,
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "error_rate": total_errors / total_requests if total_requests > 0 else 0,
            "avg_latency_ms": sum(all_latencies) / len(all_latencies) if all_latencies else 0,
            "min_latency_ms": min(all_latencies) if all_latencies else 0,
            "max_latency_ms": max(all_latencies) if all_latencies else 0,
            "timeframe_seconds": self._timeframe_seconds,
        }


class ChartDataAPI:
    """FastAPI endpoints for chart data."""
    
    def __init__(self):
        self.analyzer = TrafficChartAnalyzer()
    
    def get_candlesticks(
        self,
        logs: List[Dict],
        timeframe: int = 5,
    ) -> List[Dict[str, Any]]:
        """Get candlestick data for the chart."""
        self.analyzer.set_timeframe(timeframe)
        self.analyzer.process_traffic_logs(logs)
        return self.analyzer.get_chart_data()
    
    def get_error_clusters(
        self,
        logs: List[Dict],
        timeframe: int = 5,
    ) -> List[Dict[str, Any]]:
        """Get error clusters for highlighting."""
        self.analyzer.set_timeframe(timeframe)
        self.analyzer.process_traffic_logs(logs)
        clusters = self.analyzer.detect_error_clusters()
        
        return [
            {
                "start_time": c.start_time.isoformat(),
                "end_time": c.end_time.isoformat(),
                "error_count": c.error_count,
                "severity": c.severity,
            }
            for c in clusters
        ]
    
    def get_summary(
        self,
        logs: List[Dict],
        timeframe: int = 5,
    ) -> Dict[str, Any]:
        """Get summary statistics."""
        self.analyzer.set_timeframe(timeframe)
        self.analyzer.process_traffic_logs(logs)
        return self.analyzer.get_summary_stats()


# Singleton instance
_chart_api = None

def get_chart_api() -> ChartDataAPI:
    """Get the chart API singleton."""
    global _chart_api
    if _chart_api is None:
        _chart_api = ChartDataAPI()
    return _chart_api


if __name__ == "__main__":
    # Example usage
    print("Traffic Chart Analyzer")
    print("=" * 50)
    print("This module provides:")
    print("  - T02: Map latencies to Y-axis, time to X-axis")
    print("  - T03: Red candles for 500 errors")
    print("  - T04: Time range slider (1s to 1h)")
    print()
    print("Usage:")
    print("  from socialseed_e2e.observability.tradingview.analyzer import get_chart_api")
    print("  chart_api = get_chart_api()")
    print("  data = chart_api.get_candlesticks(logs, timeframe=5)")