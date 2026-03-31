"""
Predictive Kubernetes Auto-Scaling Recommender - EPIC-022
Analyzes metrics and generates K8s/Docker Compose recommendations.
"""

import yaml
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class ResourceMetrics:
    """Resource usage metrics."""
    cpu_usage_percent: float
    memory_usage_mb: float
    latency_ms: float
    request_count: int
    error_rate: float


@dataclass
class ScalingRecommendation:
    """A scaling recommendation."""
    id: str
    service_name: str
    resource_type: str
    current_value: float
    recommended_value: float
    reason: str
    priority: str
    yaml_config: str


class KubernetesRecommender:
    """Generates K8s and Docker Compose scaling recommendations."""
    
    def __init__(self):
        self._recommendations: List[ScalingRecommendation] = []
    
    def analyze_and_recommend(
        self,
        service_name: str,
        metrics: ResourceMetrics,
    ) -> List[ScalingRecommendation]:
        """Analyze metrics and generate recommendations."""
        recommendations = []
        
        import uuid
        
        if metrics.cpu_usage_percent > 80:
            recommendations.append(ScalingRecommendation(
                id=f"rec-{uuid.uuid4().hex[:8]}",
                service_name=service_name,
                resource_type="cpu_limit",
                current_value=metrics.cpu_usage_percent,
                recommended_value=min(metrics.cpu_usage_percent * 1.5, 4000),
                reason="CPU usage above 80% threshold",
                priority="high",
                yaml_config=self._generate_hpa_yaml(service_name, cpu_target=80),
            ))
        
        if metrics.memory_usage_mb > 512:
            recommendations.append(ScalingRecommendation(
                id=f"rec-{uuid.uuid4().hex[:8]}",
                service_name=service_name,
                resource_type="memory_limit",
                current_value=metrics.memory_usage_mb,
                recommended_value=metrics.memory_usage_mb * 1.5,
                reason="Memory usage high",
                priority="medium",
                yaml_config=self._generate_hpa_yaml(service_name, memory_target=512),
            ))
        
        if metrics.latency_ms > 500:
            recommendations.append(ScalingRecommendation(
                id=f"rec-{uuid.uuid4().hex[:8]}",
                service_name=service_name,
                resource_type="replicas",
                current_value=1,
                recommended_value=3,
                reason=f"Latency {metrics.latency_ms}ms exceeds 500ms threshold",
                priority="high",
                yaml_config=self._generate_deployment_yaml(service_name, replicas=3),
            ))
        
        if metrics.error_rate > 0.05:
            recommendations.append(ScalingRecommendation(
                id=f"rec-{uuid.uuid4().hex[:8]}",
                service_name=service_name,
                resource_type="readiness_probe",
                current_value=1,
                recommended_value=5,
                reason="High error rate requires more aggressive health checks",
                priority="medium",
                yaml_config=self._generate_probe_yaml(service_name),
            ))
        
        self._recommendations.extend(recommendations)
        return recommendations
    
    def _generate_hpa_yaml(self, service_name: str, cpu_target: int = 80, memory_target: int = 512) -> str:
        """Generate K8s HPA YAML."""
        hpa = {
            "apiVersion": "autoscaling/v2",
            "kind": "HorizontalPodAutoscaler",
            "metadata": {
                "name": f"{service_name}-hpa",
            },
            "spec": {
                "scaleTargetRef": {
                    "apiVersion": "apps/v1",
                    "kind": "Deployment",
                    "name": service_name,
                },
                "minReplicas": 2,
                "maxReplicas": 10,
                "metrics": [
                    {
                        "type": "Resource",
                        "resource": {
                            "name": "cpu",
                            "target": {
                                "type": "Utilization",
                                "averageUtilization": cpu_target,
                            },
                        },
                    },
                    {
                        "type": "Resource",
                        "resource": {
                            "name": "memory",
                            "target": {
                                "type": "Utilization",
                                "averageUtilization": memory_target,
                            },
                        },
                    },
                ],
            },
        }
        return yaml.dump(hpa, default_flow_style=False)
    
    def _generate_deployment_yaml(self, service_name: str, replicas: int = 3) -> str:
        """Generate K8s Deployment YAML with replicas."""
        deployment = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": service_name,
            },
            "spec": {
                "replicas": replicas,
                "selector": {
                    "matchLabels": {
                        "app": service_name,
                    },
                },
                "template": {
                    "metadata": {
                        "labels": {
                            "app": service_name,
                        },
                    },
                },
            },
        }
        return yaml.dump(deployment, default_flow_style=False)
    
    def _generate_probe_yaml(self, service_name: str) -> str:
        """Generate readiness probe YAML."""
        probe = {
            "readinessProbe": {
                "httpGet": {
                    "path": "/health",
                    "port": 8080,
                },
                "initialDelaySeconds": 5,
                "periodSeconds": 5,
                "failureThreshold": 3,
            },
            "livenessProbe": {
                "httpGet": {
                    "path": "/health",
                    "port": 8080,
                },
                "initialDelaySeconds": 15,
                "periodSeconds": 10,
            },
        }
        return yaml.dump(probe, default_flow_style=False)
    
    def generate_docker_compose_override(
        self,
        service_name: str,
        metrics: ResourceMetrics,
    ) -> str:
        """Generate Docker Compose override file."""
        cpu_limit = int(metrics.cpu_usage_percent * 1.5) if metrics.cpu_usage_percent > 50 else 1000
        memory_limit = int(metrics.memory_usage_mb * 1.5) if metrics.memory_usage_mb > 256 else 512
        
        override = {
            "version": "3.8",
            "services": {
                service_name: {
                    "deploy": {
                        "resources": {
                            "limits": {
                                "cpus": f"{cpu_limit}m",
                                "memory": f"{memory_limit}M",
                            },
                            "reservations": {
                                "cpus": "100m",
                                "memory": "128M",
                            },
                        },
                        "replicas": 3 if metrics.latency_ms > 500 else 2,
                    },
                },
            },
        }
        return yaml.dump(override, default_flow_style=False)
    
    def get_recommendations(
        self,
        service_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get all recommendations."""
        recs = self._recommendations
        
        if service_name:
            recs = [r for r in recs if r.service_name == service_name]
        
        return [
            {
                "id": r.id,
                "service_name": r.service_name,
                "resource_type": r.resource_type,
                "current_value": r.current_value,
                "recommended_value": r.recommended_value,
                "reason": r.reason,
                "priority": r.priority,
                "yaml_config": r.yaml_config,
            }
            for r in recs
        ]


_global_recommender: Optional[KubernetesRecommender] = None


def get_k8s_recommender() -> KubernetesRecommender:
    """Get global K8s recommender."""
    global _global_recommender
    if _global_recommender is None:
        _global_recommender = KubernetesRecommender()
    return _global_recommender
