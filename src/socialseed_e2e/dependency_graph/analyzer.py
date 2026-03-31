"""
Dependency Graph Analyzer - EPIC-010
Analyzes captured traffic to build interactive topology maps of microservices.
"""

import json
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set

from pydantic import BaseModel


class NodeStatus(Enum):
    """Health status of a node."""
    HEALTHY = "healthy"
    SLOW = "slow"
    ERROR = "error"
    UNKNOWN = "unknown"


class ConnectionStatus(Enum):
    """Health status of a connection."""
    OK = "ok"
    SLOW = "slow"
    ERROR = "error"


@dataclass
class ServiceNode:
    """Represents a microservice node in the topology."""
    name: str
    status: NodeStatus = NodeStatus.UNKNOWN
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_duration_ms: float = 0.0
    avg_duration_ms: float = 0.0
    last_seen: Optional[datetime] = None
    endpoints: Set[str] = field(default_factory=set)


@dataclass
class ServiceConnection:
    """Represents a connection between two services."""
    source: str
    target: str
    status: ConnectionStatus = ConnectionStatus.OK
    request_count: int = 0
    total_duration_ms: float = 0.0
    avg_duration_ms: float = 0.0
    error_count: int = 0


class TopologyGraph:
    """Builds and maintains a topology graph from captured traffic."""
    
    def __init__(self):
        self.nodes: Dict[str, ServiceNode] = {}
        self.connections: Dict[str, ServiceConnection] = {}
        self._lock = threading.Lock()
        self._request_id_to_service: Dict[str, str] = {}
        self._correlation_tracking: Dict[str, List[str]] = {}
    
    def _get_connection_key(self, source: str, target: str) -> str:
        """Generate unique key for a connection."""
        return f"{source}->{target}"
    
    def _infer_service_from_url(self, url: str) -> str:
        """Infer service name from URL."""
        if not url:
            return "unknown"
        
        try:
            from urllib.parse import urlparse
            host = urlparse(url).netloc
            if ":" in host:
                host = host.split(":")[0]
            
            parts = host.split(".")
            if len(parts) > 1:
                return parts[0]
            return host
        except Exception:
            return "unknown"
    
    def _infer_service_from_path(self, path: str) -> str:
        """Infer service name from API path patterns."""
        if not path:
            return "unknown"
        
        path_lower = path.lower()
        
        if "/auth" in path_lower or "/login" in path_lower:
            return "auth"
        if "/user" in path_lower:
            return "socialuser"
        if "/post" in path_lower or "/feed" in path_lower:
            return "post"
        if "/comment" in path_lower:
            return "comment"
        if "/notification" in path_lower:
            return "notification"
        if "/analytics" in path_lower:
            return "analytics"
        
        return path.split("/")[1] if len(path.split("/")) > 1 else "unknown"
    
    def _infer_target_service(
        self,
        request_body: Optional[dict] = None,
        response_body: Optional[dict] = None,
        headers: Optional[dict] = None
    ) -> Optional[str]:
        """Infer target service from request/response data."""
        if headers:
            header_str = json.dumps(headers).lower()
            
            if "authorization" in header_str or "token" in header_str:
                return "auth"
        
        if request_body:
            body_str = json.dumps(request_body).lower()
            
            if "username" in body_str or "password" in body_str:
                return "auth"
            if "user_id" in body_str or "email" in body_str:
                return "socialuser"
        
        if response_body:
            resp_str = json.dumps(response_body).lower()
            
            if "token" in resp_str and "access" in resp_str:
                return "auth"
            if "user" in resp_str and "profile" in resp_str:
                return "socialuser"
        
        return None
    
    def analyze_request(
        self,
        method: str,
        path: str,
        url: str,
        status_code: int,
        duration_ms: float,
        request_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        request_body: Optional[dict] = None,
        response_body: Optional[dict] = None,
        request_headers: Optional[dict] = None,
    ) -> None:
        """Analyze a single request and update the topology."""
        with self._lock:
            target_service = self._infer_service_from_url(url)
            if target_service == "unknown":
                target_service = self._infer_service_from_path(path)
            
            source_service = "client"
            if request_headers:
                if "X-Forwarded-Service" in request_headers:
                    source_service = request_headers["X-Forwarded-Service"]
                elif "X-Source-Service" in request_headers:
                    source_service = request_headers["X-Source-Service"]
            
            if target_service not in self.nodes:
                self.nodes[target_service] = ServiceNode(name=target_service)
            
            node = self.nodes[target_service]
            node.total_requests += 1
            node.total_duration_ms += duration_ms
            node.last_seen = datetime.now()
            node.endpoints.add(f"{method} {path}")
            
            if 200 <= status_code < 300:
                node.successful_requests += 1
                node.status = NodeStatus.HEALTHY
            elif status_code >= 500:
                node.failed_requests += 1
                node.status = NodeStatus.ERROR
            elif status_code >= 400:
                node.failed_requests += 1
            
            if node.total_requests > 0:
                node.avg_duration_ms = node.total_duration_ms / node.total_requests
            
            if node.avg_duration_ms > 1000:
                node.status = NodeStatus.SLOW
            
            if source_service != "client":
                conn_key = self._get_connection_key(source_service, target_service)
                if conn_key not in self.connections:
                    self.connections[conn_key] = ServiceConnection(
                        source=source_service,
                        target=target_service
                    )
                
                conn = self.connections[conn_key]
                conn.request_count += 1
                conn.total_duration_ms += duration_ms
                conn.avg_duration_ms = conn.total_duration_ms / conn.request_count
                
                if status_code >= 500:
                    conn.error_count += 1
                    conn.status = ConnectionStatus.ERROR
                elif conn.avg_duration_ms > 1000:
                    conn.status = ConnectionStatus.SLOW
            
            if request_id:
                self._request_id_to_service[request_id] = target_service
            
            if correlation_id:
                if correlation_id not in self._correlation_tracking:
                    self._correlation_tracking[correlation_id] = []
                self._correlation_tracking[correlation_id].append(target_service)
    
    def get_topology_json(self) -> dict:
        """Export topology as JSON for visualization."""
        with self._lock:
            nodes = []
            for name, node in self.nodes.items():
                status_color = {
                    NodeStatus.HEALTHY: "#22c55e",
                    NodeStatus.SLOW: "#eab308",
                    NodeStatus.ERROR: "#ef4444",
                    NodeStatus.UNKNOWN: "#6b7280"
                }.get(node.status, "#6b7280")
                
                nodes.append({
                    "id": name,
                    "label": name,
                    "status": node.status.value,
                    "statusColor": status_color,
                    "requests": node.total_requests,
                    "avgDuration": round(node.avg_duration_ms, 2),
                    "endpoints": list(node.endpoints)[:10]
                })
            
            links = []
            for conn in self.connections.values():
                status_color = {
                    ConnectionStatus.OK: "#22c55e",
                    ConnectionStatus.SLOW: "#eab308",
                    ConnectionStatus.ERROR: "#ef4444"
                }.get(conn.status, "#6b7280")
                
                links.append({
                    "source": conn.source,
                    "target": conn.target,
                    "status": conn.status.value,
                    "statusColor": status_color,
                    "requests": conn.request_count,
                    "avgDuration": round(conn.avg_duration_ms, 2)
                })
            
            return {
                "nodes": nodes,
                "links": links,
                "timestamp": datetime.now().isoformat()
            }
    
    def reset(self) -> None:
        """Reset the topology graph."""
        with self._lock:
            self.nodes.clear()
            self.connections.clear()
            self._request_id_to_service.clear()
            self._correlation_tracking.clear()


class DependencyGraphAnalyzer:
    """Main analyzer class for microservices dependency mapping."""
    
    def __init__(self):
        self.graph = TopologyGraph()
        self._traffic_buffer: List[dict] = []
        self._buffer_lock = threading.Lock()
    
    def add_traffic_sample(self, traffic: dict) -> None:
        """Add a traffic sample for analysis."""
        with self._buffer_lock:
            self._traffic_buffer.append(traffic)
            
            if len(self._traffic_buffer) >= 10:
                self._process_buffer()
    
    def _process_buffer(self) -> None:
        """Process buffered traffic samples."""
        with self._buffer_lock:
            samples = self._traffic_buffer.copy()
            self._traffic_buffer.clear()
        
        for sample in samples:
            self.graph.analyze_request(
                method=sample.get("method", "GET"),
                path=sample.get("path", "/"),
                url=sample.get("url", ""),
                status_code=sample.get("status_code", 200),
                duration_ms=sample.get("duration_ms", 0),
                request_id=sample.get("request_id"),
                correlation_id=sample.get("correlation_id"),
                request_body=sample.get("request_body"),
                response_body=sample.get("response_body"),
                request_headers=sample.get("request_headers"),
            )
    
    def get_topology(self) -> dict:
        """Get current topology graph."""
        self._process_buffer()
        return self.graph.get_topology_json()
    
    def get_health_summary(self) -> dict:
        """Get health summary of all services."""
        topology = self.get_topology()
        
        total_nodes = len(topology["nodes"])
        healthy_nodes = sum(1 for n in topology["nodes"] if n["status"] == "healthy")
        slow_nodes = sum(1 for n in topology["nodes"] if n["status"] == "slow")
        error_nodes = sum(1 for n in topology["nodes"] if n["status"] == "error")
        
        total_links = len(topology["links"])
        healthy_links = sum(1 for l in topology["links"] if l["status"] == "ok")
        error_links = sum(1 for l in topology["links"] if l["status"] == "error")
        
        return {
            "nodes": {
                "total": total_nodes,
                "healthy": healthy_nodes,
                "slow": slow_nodes,
                "error": error_nodes
            },
            "links": {
                "total": total_links,
                "ok": healthy_links,
                "error": error_links
            },
            "overall_health": "healthy" if error_nodes == 0 else "degraded" if error_nodes <= total_nodes // 3 else "critical"
        }


_global_analyzer: Optional[DependencyGraphAnalyzer] = None


def get_analyzer() -> DependencyGraphAnalyzer:
    """Get global dependency graph analyzer instance."""
    global _global_analyzer
    if _global_analyzer is None:
        _global_analyzer = DependencyGraphAnalyzer()
    return _global_analyzer
