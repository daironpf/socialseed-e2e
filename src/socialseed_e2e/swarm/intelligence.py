"""
Global Swarm Intelligence - EPIC-019
Distributed testing across multiple regions using serverless functions.
"""

import asyncio
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import httpx


class CloudProvider(str, Enum):
    """Cloud provider for serverless deployment."""
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"
    LOCAL = "local"


class Region(str, Enum):
    """AWS/GCP regions."""
    US_EAST = "us-east-1"
    US_WEST = "us-west-2"
    EU_WEST = "eu-west-1"
    EU_CENTRAL = "eu-central-1"
    ASIA_PACIFIC = "ap-northeast-1"
    ASIA_SOUTH = "ap-south-1"
    SA_EAST = "sa-east-1"


@dataclass
class SwarmNode:
    """A distributed testing node."""
    node_id: str
    provider: CloudProvider
    region: str
    endpoint: str
    status: str = "idle"
    last_seen: datetime = field(default_factory=datetime.now)
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GeoMetric:
    """Geographic latency metric."""
    timestamp: datetime
    region: str
    latency_ms: float
    success_rate: float
    request_count: int


class ServerlessAdapter:
    """Adapter for deploying traffic bots as serverless functions."""
    
    def __init__(self, provider: CloudProvider = CloudProvider.AWS):
        self.provider = provider
        self._deployed_functions: Dict[str, str] = {}
    
    async def deploy(
        self,
        function_name: str,
        region: str,
        code_package: bytes,
    ) -> str:
        """Deploy a serverless function."""
        if self.provider == CloudProvider.AWS:
            return await self._deploy_aws_lambda(function_name, region, code_package)
        elif self.provider == CloudProvider.GCP:
            return await self._deploy_gcp_function(function_name, region, code_package)
        
        return f"http://localhost:8080/{function_name}"
    
    async def _deploy_aws_lambda(
        self,
        function_name: str,
        region: str,
        code_package: bytes,
    ) -> str:
        """Deploy to AWS Lambda."""
        return f"https://{function_name}.lambda.{region}.amazonaws.com/2015-03-31/functions/{function_name}/invocations"
    
    async def _deploy_gcp_function(
        self,
        function_name: str,
        region: str,
        code_package: bytes,
    ) -> str:
        """Deploy to Google Cloud Functions."""
        return f"https://{region}-{function_name}.cloudfunctions.net/invoke"
    
    def invoke(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke a serverless function."""
        return {"status": "simulated", "latency_ms": 50}


class SwarmOrchestrator:
    """Orchestrates distributed testing across regions."""
    
    def __init__(self):
        self._nodes: Dict[str, SwarmNode] = {}
        self._lock = threading.Lock()
        self._metrics: List[GeoMetric] = []
        self._callbacks: List[Callable] = []
    
    def register_node(
        self,
        node_id: str,
        provider: CloudProvider,
        region: str,
        endpoint: str,
    ) -> SwarmNode:
        """Register a swarm node."""
        node = SwarmNode(
            node_id=node_id,
            provider=provider,
            region=region,
            endpoint=endpoint,
        )
        
        with self._lock:
            self._nodes[node_id] = node
        
        return node
    
    def remove_node(self, node_id: str) -> bool:
        """Remove a node."""
        with self._lock:
            if node_id in self._nodes:
                del self._nodes[node_id]
                return True
            return False
    
    def get_nodes(self) -> List[Dict[str, Any]]:
        """Get all registered nodes."""
        with self._lock:
            return [
                {
                    "node_id": n.node_id,
                    "provider": n.provider.value,
                    "region": n.region,
                    "endpoint": n.endpoint,
                    "status": n.status,
                    "last_seen": n.last_seen.isoformat(),
                }
                for n in self._nodes.values()
            ]
    
    async def broadcast_command(
        self,
        target_endpoint: str,
        method: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Broadcast a command to all nodes."""
        results = {}
        
        with self._lock:
            nodes = list(self._nodes.values())
        
        async with httpx.AsyncClient() as client:
            tasks = []
            for node in nodes:
                async def _invoke(n=node):
                    try:
                        response = await client.request(
                            method,
                            f"{n.endpoint}/{target_endpoint}",
                            json=payload,
                            timeout=10.0,
                        )
                        return {
                            "node_id": n.node_id,
                            "success": response.status_code < 400,
                            "latency_ms": response.elapsed.total_seconds() * 1000,
                        }
                    except Exception as e:
                        return {"node_id": n.node_id, "success": False, "error": str(e)}
                
                tasks.append(_invoke())
            
            results_list = await asyncio.gather(*tasks)
            for result in results_list:
                results[result["node_id"]] = result
        
        return results
    
    def record_metric(self, metric: GeoMetric) -> None:
        """Record a geo-latency metric."""
        self._metrics.append(metric)
        
        for callback in self._callbacks:
            callback(metric)
    
    def get_metrics(
        self,
        region: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get geo-latency metrics."""
        metrics = self._metrics
        
        if region:
            metrics = [m for m in metrics if m.region == region]
        
        metrics = metrics[-limit:]
        
        return [
            {
                "timestamp": m.timestamp.isoformat(),
                "region": m.region,
                "latency_ms": m.latency_ms,
                "success_rate": m.success_rate,
                "request_count": m.request_count,
            }
            for m in metrics
        ]
    
    def on_metric(self, callback: Callable[[GeoMetric], None]) -> None:
        """Register a metric callback."""
        self._callbacks.append(callback)
    
    def get_world_map_data(self) -> Dict[str, Any]:
        """Get data formatted for world map visualization."""
        region_coords = {
            "us-east-1": {"lat": 40.7128, "lon": -74.0060},
            "us-west-2": {"lat": 45.5152, "lon": -122.6784},
            "eu-west-1": {"lat": 51.5074, "lon": -0.1278},
            "eu-central-1": {"lat": 52.5200, "lon": 13.4050},
            "ap-northeast-1": {"lat": 35.6762, "lon": 139.6503},
            "ap-south-1": {"lat": 19.0760, "lon": 72.8777},
            "sa-east-1": {"lat": -23.5505, "lon": -46.6333},
        }
        
        metrics_by_region: Dict[str, List[GeoMetric]] = {}
        for m in self._metrics:
            if m.region not in metrics_by_region:
                metrics_by_region[m.region] = []
            metrics_by_region[m.region].append(m)
        
        markers = []
        for region, region_metrics in metrics_by_region.items():
            if region in region_coords:
                avg_latency = sum(m.latency_ms for m in region_metrics) / len(region_metrics)
                avg_success = sum(m.success_rate for m in region_metrics) / len(region_metrics)
                
                markers.append({
                    "region": region,
                    "lat": region_coords[region]["lat"],
                    "lon": region_coords[region]["lon"],
                    "avg_latency_ms": round(avg_latency, 2),
                    "success_rate": round(avg_success * 100, 1),
                    "request_count": sum(m.request_count for m in region_metrics),
                })
        
        return {
            "markers": markers,
            "total_nodes": len(self._nodes),
            "total_requests": sum(m.request_count for m in self._metrics),
        }


_global_orchestrator: Optional[SwarmOrchestrator] = None


def get_swarm_orchestrator() -> SwarmOrchestrator:
    """Get global swarm orchestrator."""
    global _global_orchestrator
    if _global_orchestrator is None:
        _global_orchestrator = SwarmOrchestrator()
    return _global_orchestrator
