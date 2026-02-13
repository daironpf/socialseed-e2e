"""API Relationship Mapper for comprehensive relationship mapping.

This module provides advanced mapping of API relationships including:
- Direct call relationships
- Data flow mapping
- Dependency graphs
- Impact analysis
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from socialseed_e2e.project_manifest.models import EndpointInfo, HttpMethod, ServiceInfo


class RelationshipCategory(str, Enum):
    """Categories of API relationships."""

    DIRECT_CALL = "direct_call"
    DATA_DEPENDENCY = "data_dependency"
    SEQUENTIAL = "sequential"
    ALTERNATIVE = "alternative"
    COMPOSITION = "composition"
    INHERITANCE = "inheritance"
    EVENT_DRIVEN = "event_driven"
    BATCH_PROCESSING = "batch_processing"


class DependencyStrength(str, Enum):
    """Strength of a dependency relationship."""

    STRONG = "strong"  # Hard dependency, cannot function without
    MODERATE = "moderate"  # Soft dependency, can work with degraded functionality
    WEAK = "weak"  # Optional dependency
    TEMPORAL = "temporal"  # Time-based dependency


@dataclass
class APIDependency:
    """Dependency between two endpoints."""

    source_endpoint: str
    target_endpoint: str
    category: RelationshipCategory
    strength: DependencyStrength
    confidence: float
    data_fields: List[str] = field(default_factory=list)
    call_frequency: Optional[str] = None  # always, often, sometimes, rarely
    description: str = ""
    bidirectional: bool = False


@dataclass
class DataFlow:
    """Data flow between endpoints."""

    source: str
    target: str
    data_type: str
    fields: List[str] = field(default_factory=list)
    transformation: Optional[str] = None
    volume: Optional[str] = None  # high, medium, low
    frequency: Optional[str] = None  # real-time, batch, scheduled


@dataclass
class APICluster:
    """Cluster of related endpoints."""

    name: str
    description: str
    endpoints: List[str] = field(default_factory=list)
    primary_entity: Optional[str] = None
    operations: List[str] = field(default_factory=list)
    related_clusters: List[str] = field(default_factory=list)


@dataclass
class ImpactAnalysis:
    """Analysis of impact for changes."""

    endpoint: str
    directly_affected: List[str] = field(default_factory=list)
    indirectly_affected: List[str] = field(default_factory=list)
    breaking_changes: List[str] = field(default_factory=list)
    risk_level: str = "low"  # low, medium, high, critical
    recommendations: List[str] = field(default_factory=list)


class APIRelationshipMapper:
    """Maps and analyzes relationships between APIs."""

    def __init__(self, services: List[ServiceInfo]):
        """Initialize the relationship mapper.

        Args:
            services: List of services to analyze
        """
        self.services = services
        self.endpoints: Dict[str, EndpointInfo] = {}
        self.dependencies: List[APIDependency] = []
        self.data_flows: List[DataFlow] = []
        self.clusters: List[APICluster] = []

        # Build endpoint index
        for service in services:
            for endpoint in service.endpoints:
                key = f"{service.name}.{endpoint.name}"
                self.endpoints[key] = endpoint

    def map_relationships(self) -> Dict[str, Any]:
        """Map all relationships between endpoints.

        Returns:
            Dictionary with all relationship information
        """
        self._detect_dependencies()
        self._map_data_flows()
        self._create_clusters()

        return {
            "dependencies": self.dependencies,
            "data_flows": self.data_flows,
            "clusters": self.clusters,
            "summary": self._generate_summary(),
        }

    def _detect_dependencies(self) -> None:
        """Detect all dependencies between endpoints."""
        endpoint_keys = list(self.endpoints.keys())

        for i, key1 in enumerate(endpoint_keys):
            for key2 in endpoint_keys[i + 1 :]:
                endpoint1 = self.endpoints[key1]
                endpoint2 = self.endpoints[key2]

                # Check for direct dependencies
                dep = self._check_direct_dependency(endpoint1, endpoint2, key1, key2)
                if dep:
                    self.dependencies.append(dep)

                # Check for data dependencies
                data_dep = self._check_data_dependency(endpoint1, endpoint2, key1, key2)
                if data_dep:
                    self.dependencies.append(data_dep)

                # Check for sequential dependencies
                seq_dep = self._check_sequential_dependency(
                    endpoint1, endpoint2, key1, key2
                )
                if seq_dep:
                    self.dependencies.append(seq_dep)

    def _check_direct_dependency(
        self, ep1: EndpointInfo, ep2: EndpointInfo, key1: str, key2: str
    ) -> Optional[APIDependency]:
        """Check for direct call dependency."""
        # Check if endpoint paths indicate a call relationship
        path1 = ep1.path.lower()
        path2 = ep2.path.lower()

        # Create → Read dependency
        if self._is_create_endpoint(ep1) and self._is_read_endpoint(ep2):
            if self._extract_entity(path1) == self._extract_entity(path2):
                return APIDependency(
                    source_endpoint=key1,
                    target_endpoint=key2,
                    category=RelationshipCategory.SEQUENTIAL,
                    strength=DependencyStrength.STRONG,
                    confidence=0.9,
                    description=f"Creating an entity typically precedes reading it",
                    data_fields=["id", f"{self._extract_entity(path1)}_id"],
                )

        # Read → Update dependency
        if self._is_read_endpoint(ep1) and self._is_update_endpoint(ep2):
            if self._extract_entity(path1) == self._extract_entity(path2):
                return APIDependency(
                    source_endpoint=key1,
                    target_endpoint=key2,
                    category=RelationshipCategory.SEQUENTIAL,
                    strength=DependencyStrength.MODERATE,
                    confidence=0.8,
                    description=f"Reading an entity often precedes updating it",
                    data_fields=["id"],
                )

        return None

    def _check_data_dependency(
        self, ep1: EndpointInfo, ep2: EndpointInfo, key1: str, key2: str
    ) -> Optional[APIDependency]:
        """Check for data dependency."""
        # Check if response DTO of one matches request DTO of another
        if ep1.response_dto and ep2.request_dto:
            if ep1.response_dto == ep2.request_dto:
                return APIDependency(
                    source_endpoint=key1,
                    target_endpoint=key2,
                    category=RelationshipCategory.DATA_DEPENDENCY,
                    strength=DependencyStrength.STRONG,
                    confidence=0.85,
                    description=f"Shared DTO dependency: {ep1.response_dto}",
                    data_fields=[ep1.response_dto],
                )

        # Check for path parameter overlap
        params1 = set(self._extract_path_params(ep1.path))
        params2 = set(self._extract_path_params(ep2.path))

        if params1 & params2:
            shared = params1 & params2
            return APIDependency(
                source_endpoint=key1,
                target_endpoint=key2,
                category=RelationshipCategory.DATA_DEPENDENCY,
                strength=DependencyStrength.MODERATE,
                confidence=0.7,
                description=f"Shared path parameters: {', '.join(shared)}",
                data_fields=list(shared),
            )

        return None

    def _check_sequential_dependency(
        self, ep1: EndpointInfo, ep2: EndpointInfo, key1: str, key2: str
    ) -> Optional[APIDependency]:
        """Check for sequential workflow dependency."""
        name1 = ep1.name.lower()
        name2 = ep2.name.lower()

        # Authentication flow
        if ("login" in name1 or "auth" in name1) and ep2.requires_auth:
            return APIDependency(
                source_endpoint=key1,
                target_endpoint=key2,
                category=RelationshipCategory.SEQUENTIAL,
                strength=DependencyStrength.STRONG,
                confidence=0.95,
                description="Authentication required before accessing protected endpoint",
                data_fields=["token", "session", "auth"],
            )

        # Registration flow
        if ("register" in name1 or "signup" in name1) and (
            "login" in name2 or "activate" in name2
        ):
            return APIDependency(
                source_endpoint=key1,
                target_endpoint=key2,
                category=RelationshipCategory.SEQUENTIAL,
                strength=DependencyStrength.MODERATE,
                confidence=0.85,
                description="Registration typically precedes login/activation",
                data_fields=["user_id", "email"],
            )

        return None

    def _map_data_flows(self) -> None:
        """Map data flows between endpoints."""
        for dep in self.dependencies:
            if dep.data_fields:
                flow = DataFlow(
                    source=dep.source_endpoint,
                    target=dep.target_endpoint,
                    data_type="dependency",
                    fields=dep.data_fields,
                    frequency="on_demand",
                )
                self.data_flows.append(flow)

        # Map DTO-based flows
        for key1, ep1 in self.endpoints.items():
            for key2, ep2 in self.endpoints.items():
                if key1 != key2:
                    if ep1.response_dto and ep1.response_dto == ep2.request_dto:
                        flow = DataFlow(
                            source=key1,
                            target=key2,
                            data_type="dto_transfer",
                            fields=[ep1.response_dto],
                            transformation="direct",
                            frequency="on_demand",
                        )
                        self.data_flows.append(flow)

    def _create_clusters(self) -> None:
        """Create clusters of related endpoints."""
        # Group by entity
        entity_groups: Dict[str, List[str]] = {}

        for key, endpoint in self.endpoints.items():
            entity = self._extract_entity(endpoint.path)
            if entity:
                if entity not in entity_groups:
                    entity_groups[entity] = []
                entity_groups[entity].append(key)

        # Create clusters for entities with multiple operations
        for entity, endpoint_keys in entity_groups.items():
            if len(endpoint_keys) >= 2:
                operations = []
                for key in endpoint_keys:
                    ep = self.endpoints[key]
                    if self._is_create_endpoint(ep):
                        operations.append("create")
                    elif self._is_read_endpoint(ep):
                        operations.append("read")
                    elif self._is_update_endpoint(ep):
                        operations.append("update")
                    elif self._is_delete_endpoint(ep):
                        operations.append("delete")

                cluster = APICluster(
                    name=f"{entity.title()} Operations",
                    description=f"CRUD operations for {entity} entity",
                    endpoints=endpoint_keys,
                    primary_entity=entity,
                    operations=list(set(operations)),
                )
                self.clusters.append(cluster)

        # Create functional clusters
        self._create_functional_clusters()

    def _create_functional_clusters(self) -> None:
        """Create clusters based on functional areas."""
        functional_patterns = {
            "authentication": [
                "login",
                "logout",
                "auth",
                "token",
                "refresh",
                "password",
            ],
            "user_management": ["user", "profile", "account", "permission", "role"],
            "payment": [
                "payment",
                "billing",
                "invoice",
                "charge",
                "refund",
                "subscription",
            ],
            "notification": ["notification", "email", "sms", "alert", "message"],
            "reporting": ["report", "analytics", "metric", "dashboard", "stats"],
        }

        for func_name, keywords in functional_patterns.items():
            matching_endpoints = []

            for key, endpoint in self.endpoints.items():
                name_lower = endpoint.name.lower()
                path_lower = endpoint.path.lower()

                if any(kw in name_lower or kw in path_lower for kw in keywords):
                    matching_endpoints.append(key)

            if len(matching_endpoints) >= 2:
                cluster = APICluster(
                    name=func_name.replace("_", " ").title(),
                    description=f"{func_name.replace('_', ' ').title()} related endpoints",
                    endpoints=matching_endpoints,
                )
                self.clusters.append(cluster)

    def _extract_entity(self, path: str) -> Optional[str]:
        """Extract entity name from path."""
        parts = path.strip("/").split("/")
        for part in parts:
            if part and not part.startswith("{"):
                return part.lower()
        return None

    def _extract_path_params(self, path: str) -> List[str]:
        """Extract path parameters from path."""
        return re.findall(r"\{(\w+)\}", path)

    def _is_create_endpoint(self, endpoint: EndpointInfo) -> bool:
        """Check if endpoint is a create operation."""
        return endpoint.method == HttpMethod.POST and any(
            kw in endpoint.name.lower() for kw in ["create", "add", "new", "post"]
        )

    def _is_read_endpoint(self, endpoint: EndpointInfo) -> bool:
        """Check if endpoint is a read operation."""
        return endpoint.method == HttpMethod.GET and any(
            kw in endpoint.name.lower()
            for kw in ["get", "list", "find", "fetch", "read"]
        )

    def _is_update_endpoint(self, endpoint: EndpointInfo) -> bool:
        """Check if endpoint is an update operation."""
        return endpoint.method in [HttpMethod.PUT, HttpMethod.PATCH] and any(
            kw in endpoint.name.lower()
            for kw in ["update", "edit", "modify", "put", "patch"]
        )

    def _is_delete_endpoint(self, endpoint: EndpointInfo) -> bool:
        """Check if endpoint is a delete operation."""
        return endpoint.method == HttpMethod.DELETE and any(
            kw in endpoint.name.lower() for kw in ["delete", "remove", "destroy"]
        )

    def analyze_impact(self, endpoint_name: str) -> ImpactAnalysis:
        """Analyze the impact of changing an endpoint.

        Args:
            endpoint_name: Name of the endpoint to analyze

        Returns:
            ImpactAnalysis with impact details
        """
        directly_affected = []
        indirectly_affected = []
        breaking_changes = []
        recommendations = []

        # Find all dependencies where this endpoint is the source
        for dep in self.dependencies:
            if dep.source_endpoint == endpoint_name:
                directly_affected.append(dep.target_endpoint)

                if dep.strength == DependencyStrength.STRONG:
                    breaking_changes.append(dep.target_endpoint)

            elif dep.target_endpoint == endpoint_name:
                indirectly_affected.append(dep.source_endpoint)

        # Calculate risk level
        if len(breaking_changes) > 5:
            risk_level = "critical"
        elif len(breaking_changes) > 2:
            risk_level = "high"
        elif len(breaking_changes) > 0:
            risk_level = "medium"
        else:
            risk_level = "low"

        # Generate recommendations
        if breaking_changes:
            recommendations.append(
                f"Consider backward compatibility for {len(breaking_changes)} dependent endpoints"
            )

        if len(directly_affected) > 10:
            recommendations.append(
                "This endpoint is highly coupled - consider refactoring"
            )

        if not breaking_changes:
            recommendations.append("Safe to modify - no strong dependencies detected")

        return ImpactAnalysis(
            endpoint=endpoint_name,
            directly_affected=directly_affected,
            indirectly_affected=indirectly_affected,
            breaking_changes=breaking_changes,
            risk_level=risk_level,
            recommendations=recommendations,
        )

    def get_dependency_graph(self) -> Dict[str, List[str]]:
        """Get a simple dependency graph.

        Returns:
            Dictionary mapping endpoints to their dependencies
        """
        graph = {}

        for key in self.endpoints.keys():
            graph[key] = []

        for dep in self.dependencies:
            if dep.source_endpoint in graph:
                graph[dep.source_endpoint].append(dep.target_endpoint)

        return graph

    def _generate_summary(self) -> Dict[str, Any]:
        """Generate summary of relationship mapping."""
        return {
            "total_endpoints": len(self.endpoints),
            "total_dependencies": len(self.dependencies),
            "total_data_flows": len(self.data_flows),
            "total_clusters": len(self.clusters),
            "dependency_categories": list(
                set(d.category.value for d in self.dependencies)
            ),
            "strong_dependencies": len(
                [
                    d
                    for d in self.dependencies
                    if d.strength == DependencyStrength.STRONG
                ]
            ),
            "clusters": [c.name for c in self.clusters[:10]],
        }

    def find_alternative_paths(self, source: str, target: str) -> List[List[str]]:
        """Find alternative paths between two endpoints.

        Args:
            source: Source endpoint
            target: Target endpoint

        Returns:
            List of alternative paths
        """
        graph = self.get_dependency_graph()
        paths = []
        visited = set()

        def dfs(current: str, path: List[str]):
            if current == target:
                paths.append(path[:])
                return

            if current in visited or len(path) > 5:  # Limit depth
                return

            visited.add(current)

            for neighbor in graph.get(current, []):
                if neighbor not in path:
                    path.append(neighbor)
                    dfs(neighbor, path)
                    path.pop()

            visited.remove(current)

        dfs(source, [source])

        return paths
