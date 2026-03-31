"""
Enhanced Traffic Sniffer with Redis/SQLite storage and testing isolation.

This extends the existing TrafficSniffer with:
- Task EPIC-002-T04: Real-time storage (Redis/SQLite)
- Task EPIC-002-T05: Testing traffic isolation
"""

import json
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional, Any
from enum import Enum

from pydantic import BaseModel

from socialseed_e2e.traffic_sniffer import (
    CapturedRequest,
    CapturedResponse,
    CapturedTraffic,
    TrafficSnifferConfig,
    TrafficSniffer,
)


class StorageType(Enum):
    """Type of storage for captured traffic."""
    IN_MEMORY = "in_memory"
    REDIS = "redis"
    SQLITE = "sqlite"


class TestingIsolationConfig(BaseModel):
    """Configuration for testing traffic isolation."""
    enable_isolation: bool = True
    exclude_test_headers: List[str] = ["X-Test-Run", "X-E2E-Test", "X-Test-Id"]
    exclude_test_paths: List[str] = ["/test/", "/e2e/", "/mock/", "/health"]
    exclude_test_ips: List[str] = ["127.0.0.1", "localhost"]


class TrafficIndex:
    """Real-time traffic storage and indexing."""
    
    def __init__(
        self,
        storage_type: StorageType = StorageType.IN_MEMORY,
        redis_url: Optional[str] = None,
        sqlite_path: Optional[Path] = None,
    ):
        self.storage_type = storage_type
        self._memory_store: List[CapturedTraffic] = []
        self._index_by_method: Dict[str, List[int]] = {}
        self._index_by_path: Dict[str, List[int]] = {}
        self._index_by_status: Dict[int, List[int]] = {}
        self._lock = threading.Lock()
        
        # Redis setup
        self.redis_client = None
        if storage_type == StorageType.REDIS and redis_url:
            try:
                import redis
                self.redis_client = redis.from_url(redis_url)
            except ImportError:
                print("Redis not available, falling back to in-memory")
                
        # SQLite setup
        self.sqlite_conn = None
        if storage_type == StorageType.SQLITE and sqlite_path:
            import sqlite3
            self.sqlite_conn = sqlite3.connect(str(sqlite_path))
            self._init_sqlite_db()
    
    def _init_sqlite_db(self):
        """Initialize SQLite database schema."""
        if self.sqlite_conn:
            cursor = self.sqlite_conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS traffic (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    method TEXT,
                    path TEXT,
                    status_code INTEGER,
                    duration_ms REAL,
                    request_headers TEXT,
                    request_body TEXT,
                    response_headers TEXT,
                    response_body TEXT
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_method ON traffic(method)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_path ON traffic(path)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_status ON traffic(status_code)
            """)
            self.sqlite_conn.commit()
    
    def store(self, traffic: CapturedTraffic) -> int:
        """Store a traffic record and return its index."""
        with self._lock:
            index = len(self._memory_store)
            
            # Store in memory
            self._memory_store.append(traffic)
            
            # Update indexes
            method = traffic.request.method
            path = traffic.request.path
            status = traffic.response.status_code
            
            if method not in self._index_by_method:
                self._index_by_method[method] = []
            self._index_by_method[method].append(index)
            
            if path not in self._index_by_path:
                self._index_by_path[path] = []
            self._index_by_path[path].append(index)
            
            if status not in self._index_by_status:
                self._index_by_status[status] = []
            self._index_by_status[status].append(index)
            
            # Store in Redis
            if self.storage_type == StorageType.REDIS and self.redis_client:
                key = f"traffic:{traffic.request.timestamp.isoformat()}"
                self.redis_client.set(
                    key,
                    traffic.model_dump_json(),
                    ex=86400  # 24 hour TTL
                )
            
            # Store in SQLite
            if self.storage_type == StorageType.SQLITE and self.sqlite_conn:
                cursor = self.sqlite_conn.cursor()
                cursor.execute("""
                    INSERT INTO traffic (
                        timestamp, method, path, status_code, duration_ms,
                        request_headers, request_body, response_headers, response_body
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    traffic.request.timestamp.isoformat(),
                    traffic.request.method,
                    traffic.request.path,
                    traffic.response.status_code,
                    traffic.duration_ms,
                    json.dumps(traffic.request.headers),
                    traffic.request.request_body,
                    json.dumps(traffic.response.headers),
                    traffic.response.response_body,
                ))
                self.sqlite_conn.commit()
            
            return index
    
    def get_all(self, limit: int = 100) -> List[CapturedTraffic]:
        """Get recent traffic records."""
        with self._lock:
            return self._memory_store[-limit:].copy()
    
    def query_by_method(self, method: str) -> List[CapturedTraffic]:
        """Query traffic by HTTP method."""
        with self._lock:
            indices = self._index_by_method.get(method, [])
            return [self._memory_store[i] for i in indices]
    
    def query_by_path(self, path_prefix: str) -> List[CapturedTraffic]:
        """Query traffic by path prefix."""
        with self._lock:
            results = []
            for traffic in self._memory_store:
                if traffic.request.path.startswith(path_prefix):
                    results.append(traffic)
            return results
    
    def query_by_status(self, status_code: int) -> List[CapturedTraffic]:
        """Query traffic by status code."""
        with self._lock:
            indices = self._index_by_status.get(status_code, [])
            return [self._memory_store[i] for i in indices]
    
    def query_by_time_range(
        self,
        start: datetime,
        end: datetime
    ) -> List[CapturedTraffic]:
        """Query traffic by time range."""
        with self._lock:
            return [
                t for t in self._memory_store
                if start <= t.request.timestamp <= end
            ]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get traffic statistics."""
        with self._lock:
            total = len(self._memory_store)
            if total == 0:
                return {"total": 0}
            
            methods = {}
            status_codes = {}
            total_duration = 0
            error_count = 0
            
            for traffic in self._memory_store:
                method = traffic.request.method
                methods[method] = methods.get(method, 0) + 1
                
                status = traffic.response.status_code
                status_codes[status] = status_codes.get(status, 0) + 1
                
                total_duration += traffic.duration_ms
                if status >= 400:
                    error_count += 1
            
            return {
                "total": total,
                "by_method": methods,
                "by_status": status_codes,
                "avg_duration_ms": total_duration / total,
                "error_rate": error_count / total,
                "storage_type": self.storage_type.value,
            }
    
    def clear(self):
        """Clear all stored traffic."""
        with self._lock:
            self._memory_store.clear()
            self._index_by_method.clear()
            self._index_by_path.clear()
            self._index_by_status.clear()
            
            if self.storage_type == StorageType.SQLITE and self.sqlite_conn:
                cursor = self.sqlite_conn.cursor()
                cursor.execute("DELETE FROM traffic")
                self.sqlite_conn.commit()
            
            if self.storage_type == StorageType.REDIS and self.redis_client:
                for key in self.redis_client.keys("traffic:*"):
                    self.redis_client.delete(key)


class IsolatedTrafficSniffer(TrafficSniffer):
    """
    Enhanced TrafficSniffer with testing traffic isolation.
    
    Task EPIC-002-T05: Aislar las llamadas exclusivas referentes a testing
    """
    
    def __init__(
        self,
        config: TrafficSnifferConfig,
        storage_type: StorageType = StorageType.IN_MEMORY,
        isolation_config: Optional[TestingIsolationConfig] = None,
        on_traffic_captured: Optional[Callable[[CapturedTraffic], None]] = None,
    ):
        super().__init__(config, on_traffic_captured)
        
        self.isolation_config = isolation_config or TestingIsolationConfig()
        self.traffic_index = TrafficIndex(storage_type=storage_type)
        self._test_traffic_count = 0
        self._production_traffic_count = 0
    
    def _is_test_traffic(self, traffic: CapturedTraffic) -> bool:
        """Determine if traffic is from testing."""
        if not self.isolation_config.enable_isolation:
            return False
        
        request = traffic.request
        
        # Check test headers
        for header in self.isolation_config.exclude_test_headers:
            if header in request.headers:
                return True
        
        # Check test paths
        for path in self.isolation_config.exclude_test_paths:
            if path in request.path:
                return True
        
        # Check test IPs
        client_ip = request.headers.get("X-Forwarded-For") or request.headers.get("X-Real-IP")
        if client_ip:
            for ip in self.isolation_config.exclude_test_ips:
                if ip in client_ip:
                    return True
        
        return False
    
    def _add_traffic(self, traffic: CapturedTraffic) -> None:
        """Add traffic with isolation tracking."""
        # Check if it's test traffic
        is_test = self._is_test_traffic(traffic)
        
        if is_test:
            self._test_traffic_count += 1
            # Still store but could tag it
            traffic.request.headers["X-Test-Isolated"] = "true"
        else:
            self._production_traffic_count += 1
        
        # Store in index
        self.traffic_index.store(traffic)
        
        # Call parent method
        super()._add_traffic(traffic)
    
    def get_isolation_stats(self) -> Dict[str, Any]:
        """Get isolation statistics."""
        return {
            "test_traffic_count": self._test_traffic_count,
            "production_traffic_count": self._production_traffic_count,
            "isolation_enabled": self.isolation_config.enable_isolation,
            "excluded_headers": self.isolation_config.exclude_test_headers,
            "excluded_paths": self.isolation_config.exclude_test_paths,
        }
    
    def get_traffic_stats(self) -> Dict[str, Any]:
        """Get traffic statistics from index."""
        return self.traffic_index.get_stats()


def create_isolated_sniffer(
    target_host: str = "localhost",
    target_port: int = 8080,
    storage_type: StorageType = StorageType.IN_MEMORY,
    redis_url: Optional[str] = None,
    sqlite_path: Optional[Path] = None,
    enable_isolation: bool = True,
) -> IsolatedTrafficSniffer:
    """Create an isolated traffic sniffer with storage."""
    
    config = TrafficSnifferConfig(
        target_host=target_host,
        target_port=target_port,
    )
    
    isolation_config = TestingIsolationConfig(
        enable_isolation=enable_isolation,
    )
    
    return IsolatedTrafficSniffer(
        config=config,
        storage_type=storage_type,
        isolation_config=isolation_config,
    )


if __name__ == "__main__":
    # Example usage
    sniffer = create_isolated_sniffer(
        target_host="localhost",
        target_port=8085,
        storage_type=StorageType.IN_MEMORY,
    )
    
    print("Isolated Traffic Sniffer created")
    print(f"Stats: {sniffer.get_isolation_stats()}")