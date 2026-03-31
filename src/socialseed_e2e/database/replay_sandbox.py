"""
Database State Snapshot & Sandbox - EPIC-014
Captures database state for Time-Machine replays with isolated sandbox environments.
"""

import json
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class DatabaseType(str, Enum):
    """Supported database types."""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    MONGODB = "mongodb"
    SQLITE = "sqlite"


class SnapshotStatus(str, Enum):
    """Status of a database snapshot."""
    CAPTURING = "capturing"
    READY = "ready"
    RESTORING = "restoring"
    ACTIVE = "active"
    ARCHIVED = "archived"


@dataclass
class DatabaseSnapshot:
    """Database state snapshot."""
    snapshot_id: str
    time_machine_id: Optional[str]
    database_type: DatabaseType
    database_name: str
    captured_at: datetime
    size_bytes: int = 0
    status: SnapshotStatus = SnapshotStatus.CAPTURING
    tables: List[str] = field(default_factory=list)
    schema: Dict[str, Any] = field(default_factory=dict)
    data_preview: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SandboxConfig:
    """Configuration for a sandbox environment."""
    sandbox_id: str
    source_snapshot_id: str
    database_type: DatabaseType
    container_name: Optional[str] = None
    port: int = 5432
    env_vars: Dict[str, str] = field(default_factory=dict)
    is_active: bool = False
    created_at: datetime = field(default_factory=datetime.now)


class DatabaseSnapshotManager:
    """Manages database state snapshots."""
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path.home() / ".socialseed" / "snapshots"
        self._snapshots: Dict[str, DatabaseSnapshot] = {}
        self._lock = threading.Lock()
        self._init_storage()
    
    def _init_storage(self) -> None:
        """Initialize storage directory."""
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def capture_snapshot(
        self,
        database_type: DatabaseType,
        database_name: str,
        connection_string: str,
        time_machine_id: Optional[str] = None,
    ) -> str:
        """Capture a database snapshot."""
        import uuid
        snapshot_id = f"snap-{uuid.uuid4().hex[:12]}"
        
        snapshot = DatabaseSnapshot(
            snapshot_id=snapshot_id,
            time_machine_id=time_machine_id,
            database_type=database_type,
            database_name=database_name,
            captured_at=datetime.now(),
            status=SnapshotStatus.CAPTURING,
        )
        
        with self._lock:
            self._snapshots[snapshot_id] = snapshot
        
        threading.Thread(
            target=self._capture_in_background,
            args=(snapshot_id, database_type, connection_string),
            daemon=True,
        ).start()
        
        return snapshot_id
    
    def _capture_in_background(
        self,
        snapshot_id: str,
        database_type: DatabaseType,
        connection_string: str,
    ) -> None:
        """Capture snapshot in background."""
        try:
            tables = self._get_tables(database_type, connection_string)
            schema = self._get_schema(database_type, connection_string, tables)
            
            with self._lock:
                if snapshot_id in self._snapshots:
                    snapshot = self._snapshots[snapshot_id]
                    snapshot.tables = tables
                    snapshot.schema = schema
                    snapshot.status = SnapshotStatus.READY
            
            snapshot_file = self.storage_path / f"{snapshot_id}.json"
            with open(snapshot_file, "w") as f:
                json.dump({
                    "snapshot_id": snapshot_id,
                    "tables": tables,
                    "schema": schema,
                    "captured_at": datetime.now().isoformat(),
                }, f, indent=2)
                
        except Exception as e:
            with self._lock:
                if snapshot_id in self._snapshots:
                    self._snapshots[snapshot_id].status = SnapshotStatus.ARCHIVED
    
    def _get_tables(self, db_type: DatabaseType, conn_str: str) -> List[str]:
        """Get list of tables from database."""
        if db_type == DatabaseType.POSTGRESQL:
            try:
                import psycopg2
                conn = psycopg2.connect(conn_str)
                cur = conn.cursor()
                cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
                tables = [row[0] for row in cur.fetchall()]
                cur.close()
                conn.close()
                return tables
            except ImportError:
                pass
        elif db_type == DatabaseType.MYSQL:
            try:
                import pymysql
                conn = pymysql.connect(conn_str)
                cur = conn.cursor()
                cur.execute("SHOW TABLES")
                tables = [row[0] for row in cur.fetchall()]
                cur.close()
                conn.close()
                return tables
            except ImportError:
                pass
        return []
    
    def _get_schema(
        self,
        db_type: DatabaseType,
        conn_str: str,
        tables: List[str],
    ) -> Dict[str, Any]:
        """Get database schema."""
        schema = {}
        for table in tables[:10]:
            schema[table] = {"columns": [], "row_count": 0}
        return schema
    
    def get_snapshot(self, snapshot_id: str) -> Optional[DatabaseSnapshot]:
        """Get a snapshot by ID."""
        return self._snapshots.get(snapshot_id)
    
    def list_snapshots(
        self,
        time_machine_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List all snapshots."""
        with self._lock:
            snapshots = list(self._snapshots.values())
            
            if time_machine_id:
                snapshots = [
                    s for s in snapshots
                    if s.time_machine_id == time_machine_id
                ]
            
            return [
                {
                    "snapshot_id": s.snapshot_id,
                    "time_machine_id": s.time_machine_id,
                    "database_type": s.database_type.value,
                    "database_name": s.database_name,
                    "captured_at": s.captured_at.isoformat(),
                    "status": s.status.value,
                    "tables": s.tables,
                }
                for s in snapshots
            ]
    
    def link_to_time_machine(
        self,
        snapshot_id: str,
        time_machine_id: str,
    ) -> bool:
        """Link a snapshot to a Time-Machine ID."""
        with self._lock:
            if snapshot_id in self._snapshots:
                self._snapshots[snapshot_id].time_machine_id = time_machine_id
                return True
            return False


class SandboxEnvironment:
    """Manages isolated sandbox environments for replays."""
    
    def __init__(self):
        self._sandboxes: Dict[str, SandboxConfig] = {}
        self._lock = threading.Lock()
    
    def create_sandbox(
        self,
        source_snapshot_id: str,
        database_type: DatabaseType,
    ) -> str:
        """Create a new sandbox environment."""
        import uuid
        sandbox_id = f"sandbox-{uuid.uuid4().hex[:8]}"
        
        config = SandboxConfig(
            sandbox_id=sandbox_id,
            source_snapshot_id=source_snapshot_id,
            database_type=database_type,
            port=5432 + (hash(sandbox_id) % 1000),
        )
        
        with self._lock:
            self._sandboxes[sandbox_id] = config
        
        return sandbox_id
    
    def start_sandbox(self, sandbox_id: str) -> bool:
        """Start a sandbox environment."""
        with self._lock:
            if sandbox_id not in self._sandboxes:
                return False
            
            config = self._sandboxes[sandbox_id]
            config.is_active = True
            return True
    
    def stop_sandbox(self, sandbox_id: str) -> bool:
        """Stop a sandbox environment."""
        with self._lock:
            if sandbox_id not in self._sandboxes:
                return False
            
            config = self._sandboxes[sandbox_id]
            config.is_active = False
            return True
    
    def get_sandbox(self, sandbox_id: str) -> Optional[SandboxConfig]:
        """Get sandbox configuration."""
        return self._sandboxes.get(sandbox_id)
    
    def list_sandboxes(self) -> List[Dict[str, Any]]:
        """List all sandboxes."""
        return [
            {
                "sandbox_id": s.sandbox_id,
                "source_snapshot_id": s.source_snapshot_id,
                "database_type": s.database_type.value,
                "port": s.port,
                "is_active": s.is_active,
                "created_at": s.created_at.isoformat(),
            }
            for s in self._sandboxes.values()
        ]
    
    def delete_sandbox(self, sandbox_id: str) -> bool:
        """Delete a sandbox."""
        with self._lock:
            if sandbox_id in self._sandboxes:
                del self._sandboxes[sandbox_id]
                return True
            return False


class DatabaseReplayCoordinator:
    """Coordinates database snapshots with Time-Machine replays."""
    
    def __init__(self):
        self.snapshot_manager = DatabaseSnapshotManager()
        self.sandbox_manager = SandboxEnvironment()
    
    def capture_for_time_machine(
        self,
        time_machine_id: str,
        database_type: DatabaseType,
        database_name: str,
        connection_string: str,
    ) -> str:
        """Capture snapshot linked to a Time-Machine ID."""
        return self.snapshot_manager.capture_snapshot(
            database_type=database_type,
            database_name=database_name,
            connection_string=connection_string,
            time_machine_id=time_machine_id,
        )
    
    def replay_with_sandbox(
        self,
        time_machine_id: str,
        request_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Replay a request using sandbox database state."""
        snapshots = self.snapshot_manager.list_snapshots(time_machine_id)
        
        if not snapshots:
            return {
                "success": False,
                "error": "No snapshot found for this Time-Machine ID",
            }
        
        snapshot = snapshots[0]
        sandbox_id = self.sandbox_manager.create_sandbox(
            source_snapshot_id=snapshot["snapshot_id"],
            database_type=DatabaseType(snapshot["database_type"]),
        )
        
        self.sandbox_manager.start_sandbox(sandbox_id)
        
        return {
            "success": True,
            "sandbox_id": sandbox_id,
            "snapshot_id": snapshot["snapshot_id"],
            "time_machine_id": time_machine_id,
            "message": "Sandbox ready for replay",
        }
    
    def cleanup_sandbox(self, sandbox_id: str) -> bool:
        """Cleanup a sandbox after replay."""
        return self.sandbox_manager.delete_sandbox(sandbox_id)


_global_coordinator: Optional[DatabaseReplayCoordinator] = None


def get_replay_coordinator() -> DatabaseReplayCoordinator:
    """Get global replay coordinator."""
    global _global_coordinator
    if _global_coordinator is None:
        _global_coordinator = DatabaseReplayCoordinator()
    return _global_coordinator
