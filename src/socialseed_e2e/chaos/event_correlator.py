"""
Chaos Event Correlator - EPIC-011
Correlates chaos engineering experiments with traffic data.
"""

import json
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any


class ChaosType(str, Enum):
    """Types of chaos experiments."""
    NETWORK_LATENCY = "network_latency"
    NETWORK_PACKET_LOSS = "network_packet_loss"
    CPU_LIMIT = "cpu_limit"
    MEMORY_LIMIT = "memory_limit"
    SERVICE_DOWN = "service_down"
    ERROR_INJECTION = "error_injection"
    DNS_FAILURE = "dns_failure"
    KILL_CONTAINER = "kill_container"


class ChaosEventStatus(str, Enum):
    """Status of a chaos event."""
    STARTED = "started"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ChaosEventMarker:
    """Marker for chaos events in traffic timeline."""
    event_id: str
    chaos_type: ChaosType
    target_service: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: ChaosEventStatus = ChaosEventStatus.STARTED
    config: Dict[str, Any] = field(default_factory=dict)
    results: Dict[str, Any] = field(default_factory=dict)
    affected_requests: int = 0
    failed_requests: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event_id": self.event_id,
            "chaos_type": self.chaos_type.value,
            "target_service": self.target_service,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "status": self.status.value,
            "config": self.config,
            "results": self.results,
            "affected_requests": self.affected_requests,
            "failed_requests": self.failed_requests,
        }


class ChaosEventRegistry:
    """Registry for tracking chaos events."""
    
    def __init__(self):
        self._events: Dict[str, ChaosEventMarker] = {}
        self._lock = threading.Lock()
    
    def start_event(
        self,
        event_id: str,
        chaos_type: ChaosType,
        target_service: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> ChaosEventMarker:
        """Register a new chaos event."""
        with self._lock:
            marker = ChaosEventMarker(
                event_id=event_id,
                chaos_type=chaos_type,
                target_service=target_service,
                start_time=datetime.now(),
                status=ChaosEventStatus.STARTED,
                config=config or {},
            )
            self._events[event_id] = marker
            return marker
    
    def complete_event(
        self,
        event_id: str,
        results: Optional[Dict[str, Any]] = None,
    ) -> Optional[ChaosEventMarker]:
        """Mark a chaos event as completed."""
        with self._lock:
            if event_id in self._events:
                marker = self._events[event_id]
                marker.end_time = datetime.now()
                marker.status = ChaosEventStatus.COMPLETED
                if results:
                    marker.results = results
                return marker
            return None
    
    def update_event_stats(
        self,
        event_id: str,
        affected_requests: int = 0,
        failed_requests: int = 0,
    ) -> None:
        """Update event statistics."""
        with self._lock:
            if event_id in self._events:
                marker = self._events[event_id]
                marker.affected_requests = affected_requests
                marker.failed_requests = failed_requests
    
    def get_event(self, event_id: str) -> Optional[ChaosEventMarker]:
        """Get a specific event."""
        with self._lock:
            return self._events.get(event_id)
    
    def get_events_in_range(
        self,
        start: datetime,
        end: datetime,
    ) -> List[ChaosEventMarker]:
        """Get events within a time range."""
        with self._lock:
            return [
                e for e in self._events.values()
                if e.start_time >= start and e.start_time <= end
            ]
    
    def get_active_events(self) -> List[ChaosEventMarker]:
        """Get currently active chaos events."""
        with self._lock:
            return [
                e for e in self._events.values()
                if e.status in [ChaosEventStatus.STARTED, ChaosEventStatus.RUNNING]
            ]
    
    def get_all_events(self) -> List[Dict[str, Any]]:
        """Get all events as dictionaries."""
        with self._lock:
            return [e.to_dict() for e in self._events.values()]
    
    def clear(self) -> None:
        """Clear all events."""
        with self._lock:
            self._events.clear()


class ChaosTrafficCorrelator:
    """Correlates chaos events with traffic data."""
    
    def __init__(self):
        self.registry = ChaosEventRegistry()
    
    def start_chaos_experiment(
        self,
        chaos_type: ChaosType,
        target_service: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Start a chaos experiment and return event ID."""
        from uuid import uuid4
        event_id = f"chaos-{uuid4().hex[:8]}"
        self.registry.start_event(event_id, chaos_type, target_service, config)
        return event_id
    
    def end_chaos_experiment(
        self,
        event_id: str,
        results: Optional[Dict[str, Any]] = None,
    ) -> None:
        """End a chaos experiment."""
        self.registry.complete_event(event_id, results)
    
    def correlate_traffic_with_chaos(
        self,
        traffic_logs: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Correlate traffic logs with chaos events."""
        if not traffic_logs:
            return []
        
        active_events = self.registry.get_active_events()
        all_events = self.registry.get_all_events()
        
        enriched_logs = []
        for log in traffic_logs:
            log_time_str = log.get("timestamp", "")
            if not log_time_str:
                enriched_logs.append({**log, "chaos_events": []})
                continue
            
            try:
                log_time = datetime.fromisoformat(log_time_str.replace("Z", "+00:00"))
            except Exception:
                enriched_logs.append({**log, "chaos_events": []})
                continue
            
            matching_events = []
            for event in all_events:
                event_start = datetime.fromisoformat(event["start_time"])
                event_end = event.get("end_time")
                
                if event_end:
                    event_end_dt = datetime.fromisoformat(event_end)
                    if event_start <= log_time <= event_end_dt:
                        matching_events.append(event)
                elif event_start <= log_time:
                    matching_events.append(event)
            
            enriched_logs.append({
                **log,
                "chaos_events": matching_events,
                "has_chaos_injection": len(matching_events) > 0,
            })
        
        return enriched_logs
    
    def get_chaos_timeline(
        self,
        start: datetime,
        end: datetime,
    ) -> List[Dict[str, Any]]:
        """Get chaos events for a time range (for chart markers)."""
        events = self.registry.get_events_in_range(start, end)
        
        return [
            {
                "time": e.start_time.isoformat(),
                "type": "chaos_start",
                "chaos_type": e.chaos_type.value,
                "target": e.target_service,
                "event_id": e.event_id,
                "config": e.config,
            }
            for e in events
        ] + [
            {
                "time": e.end_time.isoformat(),
                "type": "chaos_end",
                "chaos_type": e.chaos_type.value,
                "target": e.target_service,
                "event_id": e.event_id,
                "results": e.results,
            }
            for e in events
            if e.end_time is not None
        ]
    
    def analyze_chaos_impact(
        self,
        event_id: str,
        traffic_logs: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Analyze the impact of a chaos event on traffic."""
        event = self.registry.get_event(event_id)
        if not event:
            return {"error": "Event not found"}
        
        event_start = event.start_time
        event_end = event.end_time or datetime.now()
        
        affected_logs = [
            log for log in traffic_logs
            if log.get("timestamp")
            and event_start <= datetime.fromisoformat(
                log.get("timestamp", "").replace("Z", "+00:00")
            ) <= event_end
        ]
        
        total_requests = len(affected_logs)
        failed_requests = sum(
            1 for log in affected_logs
            if log.get("status_code", 200) >= 500
        )
        
        self.registry.update_event_stats(
            event_id,
            affected_requests=total_requests,
            failed_requests=failed_requests,
        )
        
        return {
            "event_id": event_id,
            "chaos_type": event.chaos_type.value,
            "target_service": event.target_service,
            "duration_seconds": (event_end - event_start).total_seconds(),
            "total_requests": total_requests,
            "failed_requests": failed_requests,
            "failure_rate": failed_requests / total_requests if total_requests > 0 else 0,
        }


_global_correlator: Optional[ChaosTrafficCorrelator] = None


def get_correlator() -> ChaosTrafficCorrelator:
    """Get global chaos traffic correlator."""
    global _global_correlator
    if _global_correlator is None:
        _global_correlator = ChaosTrafficCorrelator()
    return _global_correlator
