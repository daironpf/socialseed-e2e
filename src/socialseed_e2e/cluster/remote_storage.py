"""
Remote Cluster Storage - EPIC-012
PostgreSQL-based remote storage for multi-cluster traffic data.
"""

import json
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ClusterType(str, Enum):
    """Type of cluster environment."""
    LOCAL = "local"
    STAGING = "staging"
    PRODUCTION = "production"


class StorageTypeRemote(str, Enum):
    """Type of remote storage."""
    IN_MEMORY = "in_memory"
    REDIS = "redis"
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"


class ConnectionSecurity(str, Enum):
    """Connection security level."""
    INSECURE = "insecure"
    TLS = "tls"
    MTLS = "mtls"


@dataclass
class ClusterConfig:
    """Configuration for a remote cluster."""
    name: str
    cluster_type: ClusterType
    api_endpoint: str
    ws_endpoint: str
    storage_type: StorageTypeRemote = StorageTypeRemote.POSTGRESQL
    connection_security: ConnectionSecurity = ConnectionSecurity.TLS
    database_url: Optional[str] = None
    redis_url: Optional[str] = None
    api_key: Optional[str] = None
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


class ClusterSelector(BaseModel):
    """Cluster selector for dashboard."""
    clusters: List[ClusterConfig]
    selected_cluster: str = "local"


class RemoteTrafficStorage:
    """Remote traffic storage with PostgreSQL/Redis support."""
    
    def __init__(
        self,
        storage_type: StorageTypeRemote = StorageTypeRemote.IN_MEMORY,
        database_url: Optional[str] = None,
        redis_url: Optional[str] = None,
    ):
        self.storage_type = storage_type
        self._memory_store: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        
        self._postgres_conn = None
        self._redis_client = None
        
        self._init_storage(database_url, redis_url)
    
    def _init_storage(
        self,
        database_url: Optional[str],
        redis_url: Optional[str],
    ) -> None:
        """Initialize storage backend."""
        if self.storage_type == StorageTypeRemote.POSTGRESQL and database_url:
            try:
                import asyncpg
                self._database_url = database_url
            except ImportError:
                print("PostgreSQL not available (install asyncpg)")
        
        elif self.storage_type == StorageTypeRemote.REDIS and redis_url:
            try:
                import redis
                self._redis_client = redis.from_url(redis_url)
            except ImportError:
                print("Redis not available")
    
    async def _get_postgres_pool(self):
        """Get PostgreSQL connection pool."""
        if not self._postgres_conn:
            import asyncpg
            self._postgres_conn = await asyncpg.create_pool(
                self._database_url,
                min_size=2,
                max_size=10,
            )
        return self._postgres_conn
    
    def store(self, traffic_data: Dict[str, Any]) -> int:
        """Store traffic data."""
        with self._lock:
            if self.storage_type == StorageTypeRemote.IN_MEMORY:
                self._memory_store.append(traffic_data)
                return len(self._memory_store) - 1
            
            elif self.storage_type == StorageTypeRemote.REDIS and self._redis_client:
                import uuid
                key = f"traffic:{uuid.uuid4().hex[:8]}"
                self._redis_client.set(key, json.dumps(traffic_data))
                return 0
            
            return -1
    
    async def store_async(self, traffic_data: Dict[str, Any]) -> int:
        """Store traffic data asynchronously."""
        if self.storage_type == StorageTypeRemote.POSTGRESQL:
            pool = await self._get_postgres_pool()
            async with pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO traffic_logs (timestamp, method, path, status_code, 
                                           duration_ms, request_data, response_data, cluster)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    """,
                    traffic_data.get("timestamp"),
                    traffic_data.get("method"),
                    traffic_data.get("path"),
                    traffic_data.get("status_code"),
                    traffic_data.get("duration_ms"),
                    json.dumps(traffic_data.get("request_data", {})),
                    json.dumps(traffic_data.get("response_data", {})),
                    traffic_data.get("cluster", "local"),
                )
            return 0
        
        return self.store(traffic_data)
    
    def query(
        self,
        cluster: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        method: Optional[str] = None,
        status_code: Optional[int] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Query traffic data."""
        with self._lock:
            if self.storage_type == StorageTypeRemote.IN_MEMORY:
                results = self._memory_store.copy()
                
                if cluster:
                    results = [r for r in results if r.get("cluster") == cluster]
                if start_time:
                    results = [
                        r for r in results
                        if datetime.fromisoformat(r.get("timestamp", "").replace("Z", "+00:00")) >= start_time
                    ]
                if end_time:
                    results = [
                        r for r in results
                        if datetime.fromisoformat(r.get("timestamp", "").replace("Z", "+00:00")) <= end_time
                    ]
                if method:
                    results = [r for r in results if r.get("method") == method]
                if status_code:
                    results = [r for r in results if r.get("status_code") == status_code]
                
                return results[-limit:]
            
            return []
    
    async def query_async(
        self,
        cluster: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        method: Optional[str] = None,
        status_code: Optional[int] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Query traffic data asynchronously."""
        if self.storage_type == StorageTypeRemote.POSTGRESQL:
            pool = await self._get_postgres_pool()
            
            query = "SELECT * FROM traffic_logs WHERE 1=1"
            params = []
            param_idx = 1
            
            if cluster:
                query += f" AND cluster = ${param_idx}"
                params.append(cluster)
                param_idx += 1
            
            if start_time:
                query += f" AND timestamp >= ${param_idx}"
                params.append(start_time.isoformat())
                param_idx += 1
            
            if end_time:
                query += f" AND timestamp <= ${param_idx}"
                params.append(end_time.isoformat())
                param_idx += 1
            
            if method:
                query += f" AND method = ${param_idx}"
                params.append(method)
                param_idx += 1
            
            if status_code:
                query += f" AND status_code = ${param_idx}"
                params.append(status_code)
                param_idx += 1
            
            query += f" ORDER BY timestamp DESC LIMIT ${param_idx}"
            params.append(limit)
            
            async with pool.acquire() as conn:
                rows = await conn.fetch(query, *params)
                return [dict(row) for row in rows]
        
        return self.query(cluster, start_time, end_time, method, status_code, limit)
    
    def clear(self, cluster: Optional[str] = None) -> int:
        """Clear traffic data."""
        with self._lock:
            if cluster:
                if self.storage_type == StorageTypeRemote.IN_MEMORY:
                    self._memory_store = [
                        r for r in self._memory_store
                        if r.get("cluster") != cluster
                    ]
            else:
                self._memory_store.clear()
            
            return 0


class ClusterManager:
    """Manages multiple remote clusters."""
    
    def __init__(self):
        self._clusters: Dict[str, ClusterConfig] = {}
        self._active_cluster: Optional[str] = "local"
        self._storage_per_cluster: Dict[str, RemoteTrafficStorage] = {}
        self._lock = threading.Lock()
        self._init_default_clusters()
    
    def _init_default_clusters(self) -> None:
        """Initialize default cluster configurations."""
        self._clusters["local"] = ClusterConfig(
            name="local",
            cluster_type=ClusterType.LOCAL,
            api_endpoint="http://localhost:8000",
            ws_endpoint="ws://localhost:8765",
            storage_type=StorageTypeRemote.IN_MEMORY,
            connection_security=ConnectionSecurity.TLS,
        )
        
        self._clusters["staging"] = ClusterConfig(
            name="staging",
            cluster_type=ClusterType.STAGING,
            api_endpoint="https://api-staging.socialseed.io",
            ws_endpoint="wss://ws-staging.socialseed.io",
            storage_type=StorageTypeRemote.POSTGRESQL,
            connection_security=ConnectionSecurity.TLS,
        )
        
        self._clusters["production"] = ClusterConfig(
            name="production",
            cluster_type=ClusterType.PRODUCTION,
            api_endpoint="https://api.socialseed.io",
            ws_endpoint="wss://ws.socialseed.io",
            storage_type=StorageTypeRemote.POSTGRESQL,
            connection_security=ConnectionSecurity.MTLS,
        )
    
    def add_cluster(self, config: ClusterConfig) -> None:
        """Add a new cluster configuration."""
        with self._lock:
            self._clusters[config.name] = config
    
    def remove_cluster(self, name: str) -> bool:
        """Remove a cluster configuration."""
        with self._lock:
            if name in self._clusters:
                del self._clusters[name]
                if name in self._storage_per_cluster:
                    del self._storage_per_cluster[name]
                return True
            return False
    
    def get_cluster(self, name: str) -> Optional[ClusterConfig]:
        """Get cluster configuration."""
        return self._clusters.get(name)
    
    def list_clusters(self) -> List[Dict[str, Any]]:
        """List all clusters."""
        return [
            {
                "name": c.name,
                "type": c.cluster_type.value,
                "api_endpoint": c.api_endpoint,
                "is_active": c.is_active,
                "storage": c.storage_type.value,
            }
            for c in self._clusters.values()
        ]
    
    def set_active_cluster(self, name: str) -> bool:
        """Set the active cluster."""
        with self._lock:
            if name in self._clusters:
                self._active_cluster = name
                return True
            return False
    
    def get_active_cluster(self) -> Optional[ClusterConfig]:
        """Get the active cluster configuration."""
        return self._clusters.get(self._active_cluster)
    
    def get_storage(self, cluster_name: Optional[str] = None) -> RemoteTrafficStorage:
        """Get storage for a cluster."""
        name = cluster_name or self._active_cluster
        
        with self._lock:
            if name not in self._storage_per_cluster:
                cluster = self._clusters.get(name)
                if cluster:
                    self._storage_per_cluster[name] = RemoteTrafficStorage(
                        storage_type=cluster.storage_type,
                        database_url=cluster.database_url,
                        redis_url=cluster.redis_url,
                    )
                else:
                    self._storage_per_cluster[name] = RemoteTrafficStorage()
            
            return self._storage_per_cluster[name]
    
    def get_cluster_selector(self) -> ClusterSelector:
        """Get cluster selector for dashboard."""
        return ClusterSelector(
            clusters=list(self._clusters.values()),
            selected_cluster=self._active_cluster,
        )


_global_manager: Optional[ClusterManager] = None


def get_cluster_manager() -> ClusterManager:
    """Get global cluster manager."""
    global _global_manager
    if _global_manager is None:
        _global_manager = ClusterManager()
    return _global_manager
