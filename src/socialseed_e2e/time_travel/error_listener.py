"""
Enhanced Time-Machine Debugging - Error Detection and Replay.

This module extends the existing time_travel module with:
- T01: Real-time error detection with triggers for 4xx/5xx status codes
- T02: Serialization of failed payload, env vars, and time traces
- T03: CLI command to replay failed requests
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from pydantic import BaseModel


class ErrorSeverity(Enum):
    """Severity of detected error."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorTriggerType(Enum):
    """Type of error trigger."""
    HTTP_4XX = "http_4xx"
    HTTP_5XX = "http_5xx"
    TIMEOUT = "timeout"
    EXCEPTION = "exception"
    CUSTOM = "custom"


@dataclass
class ErrorSnapshot:
    """Complete snapshot of a failed request."""
    incident_id: str
    timestamp: datetime
    
    # Request details
    method: str
    path: str
    headers: Dict[str, str]
    body: Optional[str]
    query_params: Dict[str, str] = field(default_factory=dict)
    
    # Response details
    status_code: int
    response_headers: Dict[str, str] = field(default_factory=dict)
    response_body: Optional[str] = None
    error_message: Optional[str] = None
    
    # Context
    environment_variables: Dict[str, str] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    duration_ms: float = 0.0
    
    # Metadata
    severity: ErrorSeverity = ErrorSeverity.ERROR
    trigger_type: ErrorTriggerType = ErrorTriggerType.HTTP_4XX
    retry_count: int = 0


class ErrorListenerConfig(BaseModel):
    """Configuration for error listener."""
    trigger_on_4xx: bool = True
    trigger_on_5xx: bool = True
    trigger_on_timeout: bool = True
    trigger_on_exception: bool = True
    
    # Custom status codes to trigger on
    custom_status_codes: List[int] = []
    
    # Environment variables to capture
    capture_env_vars: List[str] = [
        "PATH", "HOME", "USER", "LANG",
        "SERVICE_URL", "API_KEY", "TOKEN",
        "DB_HOST", "DB_PORT", "REDIS_HOST",
    ]
    
    # Storage
    storage_path: Path = Path(".e2e/time_machine/errors")
    max_snapshots: int = 1000


class ErrorListener:
    """Real-time error listener with triggers.
    
    T01: Crear Listener en tiempo real capaz deazziaccionar triggers al encontrar un status code de error.
    """
    
    def __init__(
        self,
        config: Optional[ErrorListenerConfig] = None,
        on_error_detected: Optional[Callable[[ErrorSnapshot], None]] = None,
    ):
        self.config = config or ErrorListenerConfig()
        self.on_error_detected = on_error_detected
        
        self._snapshots: List[ErrorSnapshot] = []
        self._storage_path = self.config.storage_path
        self._storage_path.mkdir(parents=True, exist_ok=True)
        
        # Load existing snapshots
        self._load_existing_snapshots()
    
    def _load_existing_snapshots(self):
        """Load existing error snapshots from storage."""
        if not self._storage_path.exists():
            return
        
        for file in self._storage_path.glob("*.json"):
            try:
                data = json.loads(file.read_text())
                # Reconstruct ErrorSnapshot from JSON
                snapshot = ErrorSnapshot(
                    incident_id=data.get("incident_id", ""),
                    timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat())),
                    method=data.get("method", ""),
                    path=data.get("path", ""),
                    headers=data.get("headers", {}),
                    body=data.get("body"),
                    status_code=data.get("status_code", 0),
                    response_headers=data.get("response_headers", {}),
                    response_body=data.get("response_body"),
                    error_message=data.get("error_message"),
                    environment_variables=data.get("environment_variables", {}),
                    stack_trace=data.get("stack_trace"),
                    duration_ms=data.get("duration_ms", 0.0),
                )
                self._snapshots.append(snapshot)
            except Exception:
                pass
    
    def should_trigger(self, status_code: int) -> bool:
        """Determine if a status code should trigger error recording."""
        if status_code >= 400 and status_code < 500 and self.config.trigger_on_4xx:
            return True
        if status_code >= 500 and self.config.trigger_on_500 and self.config.trigger_on_5xx:
            return True
        if status_code in self.config.custom_status_codes:
            return True
        return False
    
    def detect_error(
        self,
        method: str,
        path: str,
        headers: Dict[str, str],
        body: Optional[str],
        status_code: int,
        response_body: Optional[str] = None,
        error_message: Optional[str] = None,
        duration_ms: float = 0.0,
    ) -> Optional[ErrorSnapshot]:
        """Detect and record an error.
        
        Returns ErrorSnapshot if error was detected and recorded, None otherwise.
        """
        if not self.should_trigger(status_code):
            return None
        
        # Determine trigger type
        if status_code >= 500:
            trigger = ErrorTriggerType.HTTP_5XX
        elif status_code >= 400:
            trigger = ErrorTriggerType.HTTP_4XX
        else:
            trigger = ErrorTriggerType.CUSTOM
        
        # Determine severity
        if status_code >= 500:
            severity = ErrorSeverity.CRITICAL
        elif status_code >= 400:
            severity = ErrorSeverity.ERROR
        else:
            severity = ErrorSeverity.WARNING
        
        # Capture environment variables
        env_vars = {}
        for var in self.config.capture_env_vars:
            env_vars[var] = os.environ.get(var, "")
        
        # Create snapshot
        snapshot = ErrorSnapshot(
            incident_id=self._generate_incident_id(),
            timestamp=datetime.now(),
            method=method,
            path=path,
            headers=headers,
            body=body,
            status_code=status_code,
            response_body=response_body,
            error_message=error_message,
            environment_variables=env_vars,
            duration_ms=duration_ms,
            severity=severity,
            trigger_type=trigger,
        )
        
        # Store snapshot
        self._snapshots.append(snapshot)
        
        # Trim if exceeds max
        if len(self._snapshots) > self.config.max_snapshots:
            self._snapshots = self._snapshots[-self.config.max_snapshots:]
        
        # Save to disk
        self._save_snapshot(snapshot)
        
        # Call callback
        if self.on_error_detected:
            self.on_error_detected(snapshot)
        
        return snapshot
    
    def _generate_incident_id(self) -> str:
        """Generate unique incident ID."""
        import uuid
        return f"INC-{uuid.uuid4().hex[:12]}"
    
    def _save_snapshot(self, snapshot: ErrorSnapshot):
        """Save snapshot to disk."""
        file_path = self._storage_path / f"{snapshot.incident_id}.json"
        
        data = {
            "incident_id": snapshot.incident_id,
            "timestamp": snapshot.timestamp.isoformat(),
            "method": snapshot.method,
            "path": snapshot.path,
            "headers": snapshot.headers,
            "body": snapshot.body,
            "status_code": snapshot.status_code,
            "response_headers": snapshot.response_headers,
            "response_body": snapshot.response_body,
            "error_message": snapshot.error_message,
            "environment_variables": snapshot.environment_variables,
            "stack_trace": snapshot.stack_trace,
            "duration_ms": snapshot.duration_ms,
            "severity": snapshot.severity.value,
            "trigger_type": snapshot.trigger_type.value,
        }
        
        file_path.write_text(json.dumps(data, indent=2))
    
    def get_all_snapshots(self) -> List[ErrorSnapshot]:
        """Get all recorded error snapshots."""
        return self._snapshots.copy()
    
    def get_snapshot_by_id(self, incident_id: str) -> Optional[ErrorSnapshot]:
        """Get a specific snapshot by incident ID."""
        for snapshot in self._snapshots:
            if snapshot.incident_id == incident_id:
                return snapshot
        return None
    
    def get_recent_snapshots(self, count: int = 10) -> List[ErrorSnapshot]:
        """Get recent error snapshots."""
        return self._snapshots[-count:]


class ErrorReplay:
    """Replay recorded error snapshots.
    
    T03: CLI command `e2e time-machine replay <id-error>` para re-lanzar exactamente el request anómalo.
    """
    
    def __init__(self, base_url: str = "http://localhost:8085"):
        self.base_url = base_url
    
    def replay_snapshot(
        self,
        snapshot: ErrorSnapshot,
        mock_responses: bool = False,
    ) -> Dict[str, Any]:
        """Replay a recorded error snapshot."""
        import requests
        
        url = f"{self.base_url}{snapshot.path}"
        
        # Prepare headers (remove auth for replay if needed)
        replay_headers = snapshot.headers.copy()
        
        print(f"Replaying: {snapshot.method} {url}")
        print(f"Original status: {snapshot.status_code}")
        
        try:
            if mock_responses:
                # Return mock response
                return {
                    "success": True,
                    "mock": True,
                    "original_status": snapshot.status_code,
                    "original_response": snapshot.response_body,
                }
            
            # Make actual request
            response = requests.request(
                method=snapshot.method,
                url=url,
                headers=replay_headers,
                data=snapshot.body,
                timeout=30,
            )
            
            return {
                "success": response.ok,
                "status_code": response.status_code,
                "response_body": response.text[:500],
                "duration_ms": response.elapsed.total_seconds() * 1000,
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }


def create_error_listener(
    on_error: Optional[Callable[[ErrorSnapshot], None]] = None,
    storage_path: str = ".e2e/time_machine/errors",
) -> ErrorListener:
    """Create an error listener with default configuration."""
    config = ErrorListenerConfig(
        storage_path=Path(storage_path),
    )
    
    return ErrorListener(config=config, on_error_detected=on_error)


if __name__ == "__main__":
    # Example usage
    listener = create_error_listener()
    print("Error Listener created")
    print(f"Snapshots: {len(listener.get_all_snapshots())}")
    print(f"Recent: {len(listener.get_recent_snapshots())}")