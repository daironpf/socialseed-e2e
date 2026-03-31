"""
Kubernetes Auto-Scaling Recommender - EPIC-022
Predictive scaling recommendations based on metrics.
"""

from .recommender import (
    KubernetesRecommender,
    ResourceMetrics,
    ScalingRecommendation,
    get_k8s_recommender,
)

__all__ = [
    "KubernetesRecommender",
    "ResourceMetrics",
    "ScalingRecommendation",
    "get_k8s_recommender",
]
