"""
API Evolution & Auto-Contract Versioning - EPIC-021
Automatically detects API changes and updates contracts.
"""

import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel


class ChangeType(str, Enum):
    """Types of API changes."""
    ADDED_FIELD = "added_field"
    REMOVED_FIELD = "removed_field"
    TYPE_CHANGED = "type_changed"
    BREAKING_CHANGE = "breaking_change"
    UNDOCUMENTED_FEATURE = "undocumented_feature"


class ChangeSeverity(str, Enum):
    """Severity of API change."""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


@dataclass
class APIChange:
    """An API change detected."""
    id: str
    change_type: ChangeType
    field_path: str
    old_value: Any = None
    new_value: Any = None
    severity: ChangeSeverity = ChangeSeverity.INFO
    detected_at: datetime = field(default_factory=datetime.now)
    description: str = ""


@dataclass
class APIContract:
    """An API contract version."""
    version: str
    endpoint: str
    method: str
    fields: Dict[str, str] = field(default_factory=dict)
    required_fields: Set[str] = field(default_factory=set)
    updated_at: datetime = field(default_factory=datetime.now)


class SemanticDiffEngine:
    """Compares API responses to detect changes."""
    
    def __init__(self):
        self._known_contracts: Dict[str, APIContract] = {}
        self._changes: List[APIChange] = []
        self._lock = threading.Lock()
    
    def register_contract(self, contract: APIContract) -> None:
        """Register an API contract."""
        key = f"{contract.method}:{contract.endpoint}"
        self._known_contracts[key] = contract
    
    def diff(
        self,
        endpoint: str,
        method: str,
        old_response: Dict[str, Any],
        new_response: Dict[str, Any],
    ) -> List[APIChange]:
        """Compare two API responses."""
        changes = []
        
        old_fields = set(old_response.keys())
        new_fields = set(new_response.keys())
        
        added_fields = new_fields - old_fields
        removed_fields = old_fields - new_fields
        
        import uuid
        
        for field_name in added_fields:
            changes.append(APIChange(
                id=f"change-{uuid.uuid4().hex[:8]}",
                change_type=ChangeType.ADDED_FIELD,
                field_path=f"{endpoint}.{field_name}",
                new_value=new_response.get(field_name),
                severity=ChangeSeverity.INFO,
                description=f"New field '{field_name}' detected in response",
            ))
        
        for field_name in removed_fields:
            changes.append(APIChange(
                id=f"change-{uuid.uuid4().hex[:8]}",
                change_type=ChangeType.REMOVED_FIELD,
                field_path=f"{endpoint}.{field_name}",
                old_value=old_response.get(field_name),
                severity=ChangeSeverity.WARNING,
                description=f"Field '{field_name}' no longer in response",
            ))
        
        for field_name in old_fields & new_fields:
            old_val = old_response.get(field_name)
            new_val = new_response.get(field_name)
            
            if type(old_val) != type(new_val):
                changes.append(APIChange(
                    id=f"change-{uuid.uuid4().hex[:8]}",
                    change_type=ChangeType.TYPE_CHANGED,
                    field_path=f"{endpoint}.{field_name}",
                    old_value=str(type(old_val)),
                    new_value=str(type(new_val)),
                    severity=ChangeSeverity.CRITICAL,
                    description=f"Type changed for '{field_name}'",
                ))
        
        with self._lock:
            self._changes.extend(changes)
            
            for change in changes:
                if change.severity == ChangeSeverity.CRITICAL:
                    change.change_type = ChangeType.BREAKING_CHANGE
                elif change.change_type == ChangeType.ADDED_FIELD:
                    change.change_type = ChangeType.UNDOCUMENTED_FEATURE
        
        return changes
    
    def get_changes(
        self,
        endpoint: Optional[str] = None,
        severity: Optional[ChangeSeverity] = None,
    ) -> List[Dict[str, Any]]:
        """Get detected changes."""
        changes = self._changes
        
        if endpoint:
            changes = [c for c in changes if endpoint in c.field_path]
        
        if severity:
            changes = [c for c in changes if c.severity == severity]
        
        return [
            {
                "id": c.id,
                "type": c.change_type.value,
                "field_path": c.field_path,
                "old_value": str(c.old_value)[:100] if c.old_value else None,
                "new_value": str(c.new_value)[:100] if c.new_value else None,
                "severity": c.severity.value,
                "detected_at": c.detected_at.isoformat(),
                "description": c.description,
            }
            for c in changes
        ]


class ContractAutoUpdater:
    """Automatically updates contracts when changes detected."""
    
    def __init__(self, diff_engine: SemanticDiffEngine):
        self.diff_engine = diff_engine
        self._update_callbacks: List[callable] = []
    
    def on_contract_update(self, callback: callable) -> None:
        """Register callback for contract updates."""
        self._update_callbacks.append(callback)
    
    def update_contract(
        self,
        endpoint: str,
        method: str,
        new_response: Dict[str, Any],
    ) -> Optional[APIContract]:
        """Update contract based on new response."""
        key = f"{method}:{endpoint}"
        old_contract = self.diff_engine._known_contracts.get(key)
        
        if not old_contract:
            new_contract = APIContract(
                version="v1",
                endpoint=endpoint,
                method=method,
                fields={k: type(v).__name__ for k, v in new_response.items()},
            )
            self.diff_engine.register_contract(new_contract)
            
            for callback in self._update_callbacks:
                callback(new_contract)
            
            return new_contract
        
        old_response = {k: v for k, v in old_contract.fields.items()}
        changes = self.diff_engine.diff(endpoint, method, old_response, new_response)
        
        if changes:
            new_fields = dict(old_contract.fields)
            for field_name, value in new_response.items():
                new_fields[field_name] = type(value).__name__
            
            old_contract.fields = new_fields
            old_contract.updated_at = datetime.now()
            
            for callback in self._update_callbacks:
                callback(old_contract, changes)
            
            return old_contract
        
        return None
    
    def get_contract(self, endpoint: str, method: str) -> Optional[APIContract]:
        """Get current contract."""
        key = f"{method}:{endpoint}"
        return self.diff_engine._known_contracts.get(key)


class BreakingChangeAlert:
    """Alerts for breaking changes."""
    
    def __init__(self):
        self._alerts: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
    
    def create_alert(
        self,
        change: APIChange,
        service_name: str,
    ) -> Dict[str, Any]:
        """Create an alert for a breaking change."""
        alert = {
            "id": change.id,
            "type": "api_change",
            "title": f"API Change Detected: {change.change_type.value}",
            "description": change.description,
            "severity": change.severity.value,
            "field_path": change.field_path,
            "service": service_name,
            "created_at": change.detected_at.isoformat(),
        }
        
        with self._lock:
            self._alerts.append(alert)
        
        return alert
    
    def get_alerts(
        self,
        severity: Optional[ChangeSeverity] = None,
    ) -> List[Dict[str, Any]]:
        """Get all alerts."""
        alerts = self._alerts
        
        if severity:
            alerts = [a for a in alerts if a["severity"] == severity.value]
        
        return alerts


_global_engine: Optional[SemanticDiffEngine] = None


def get_diff_engine() -> SemanticDiffEngine:
    """Get global diff engine."""
    global _global_engine
    if _global_engine is None:
        _global_engine = SemanticDiffEngine()
    return _global_engine
