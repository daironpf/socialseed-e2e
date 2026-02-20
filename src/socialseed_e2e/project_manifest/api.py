"""Internal API for querying the AI Project Manifest.

This module provides a programmatic interface for other agents and components
to query the project_knowledge.json without parsing raw source code.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, TypeVar, Union

from socialseed_e2e.project_manifest.models import (
    DtoField,
    DtoSchema,
    EndpointInfo,
    EnvironmentVariable,
    HttpMethod,
    PortConfig,
    ProjectKnowledge,
    ServiceDependency,
    ServiceInfo,
)

T = TypeVar("T")


class ManifestAPI:
    """API for querying project knowledge manifest.

    This class provides methods to query the project_knowledge.json
    without having to parse the raw source code, optimizing token usage
    for AI agents.

    Example:
        >>> api = ManifestAPI("/path/to/project")
        >>> endpoints = api.get_endpoints(method=HttpMethod.GET)
        >>> user_dto = api.get_dto("UserRequest")
        >>> auth_endpoints = api.search_endpoints(tags=["auth"])
    """

    def __init__(
        self, project_root: Union[str, Path], manifest_path: Optional[Path] = None
    ):
        """Initialize the Manifest API.

        Args:
            project_root: Root directory of the project
            manifest_path: Optional custom path to manifest file
        """
        import socialseed_e2e
        import inspect

        self.project_root = Path(project_root).resolve()

        # If manifest_path is not provided, search in multiple locations:
        # 1. Framework manifests folder: <framework_root>/manifests/<service_name>/
        # 2. Project root: <project_root>/project_knowledge.json
        if manifest_path is None:
            # Try to find the manifest in the framework's manifests folder
            framework_root = Path(inspect.getfile(socialseed_e2e)).parent.parent
            service_name = self.project_root.name

            # Check framework manifests folder first
            framework_manifest_path = (
                framework_root / "manifests" / service_name / "project_knowledge.json"
            )
            if framework_manifest_path.exists():
                self.manifest_path = framework_manifest_path
            else:
                # Fall back to project root
                self.manifest_path = self.project_root / "project_knowledge.json"
        else:
            self.manifest_path = manifest_path

        self._manifest: Optional[ProjectKnowledge] = None
        self._load_manifest()

    def _load_manifest(self) -> None:
        """Load manifest from disk."""
        if not self.manifest_path.exists():
            raise FileNotFoundError(
                f"Manifest not found at {self.manifest_path}. "
                "Run ManifestGenerator first to create the manifest."
            )

        content = self.manifest_path.read_text(encoding="utf-8")
        data = json.loads(content)
        self._manifest = ProjectKnowledge.model_validate(data)

    def reload(self) -> None:
        """Reload manifest from disk (useful if manifest was updated)."""
        self._load_manifest()

    @property
    def manifest(self) -> ProjectKnowledge:
        """Get the loaded manifest.

        Returns:
            ProjectKnowledge object

        Raises:
            RuntimeError: If manifest is not loaded
        """
        if self._manifest is None:
            raise RuntimeError("Manifest not loaded")
        return self._manifest

    # ==========================================================================
    # Service Queries
    # ==========================================================================

    def get_services(self) -> List[ServiceInfo]:
        """Get all services in the project.

        Returns:
            List of ServiceInfo objects
        """
        return self.manifest.services

    def get_service(self, name: str) -> Optional[ServiceInfo]:
        """Get a service by name.

        Args:
            name: Service name

        Returns:
            ServiceInfo if found, None otherwise
        """
        return self.manifest.get_service(name)

    def get_services_by_language(self, language: str) -> List[ServiceInfo]:
        """Get all services using a specific language.

        Args:
            language: Programming language (python, java, javascript, etc.)

        Returns:
            List of ServiceInfo objects
        """
        return [
            s for s in self.manifest.services if s.language.lower() == language.lower()
        ]

    def get_services_by_framework(self, framework: str) -> List[ServiceInfo]:
        """Get all services using a specific framework.

        Args:
            framework: Framework name (fastapi, flask, spring, express, etc.)

        Returns:
            List of ServiceInfo objects
        """
        return [
            s
            for s in self.manifest.services
            if s.framework and s.framework.lower() == framework.lower()
        ]

    # ==========================================================================
    # Endpoint Queries
    # ==========================================================================

    def get_endpoints(
        self,
        service_name: Optional[str] = None,
        method: Optional[HttpMethod] = None,
        requires_auth: Optional[bool] = None,
    ) -> List[EndpointInfo]:
        """Get endpoints with optional filtering.

        Args:
            service_name: Filter by service name
            method: Filter by HTTP method
            requires_auth: Filter by authentication requirement

        Returns:
            List of EndpointInfo objects
        """
        endpoints = []

        services = self.manifest.services
        if service_name:
            service = self.get_service(service_name)
            services = [service] if service else []

        for service in services:
            for endpoint in service.endpoints:
                if method and endpoint.method != method:
                    continue
                if (
                    requires_auth is not None
                    and endpoint.requires_auth != requires_auth
                ):
                    continue
                endpoints.append(endpoint)

        return endpoints

    def get_endpoint(
        self, path: str, method: Optional[HttpMethod] = None
    ) -> Optional[EndpointInfo]:
        """Get a specific endpoint by path.

        Args:
            path: Endpoint path (e.g., "/api/users")
            method: Optional HTTP method to match

        Returns:
            EndpointInfo if found, None otherwise
        """
        return self.manifest.get_endpoint(path, method)

    def search_endpoints(
        self,
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        path_prefix: Optional[str] = None,
    ) -> List[EndpointInfo]:
        """Search endpoints by query, tags, or path prefix.

        Args:
            query: Search string to match in name, path, or description
            tags: List of tags to match
            path_prefix: Path prefix to match

        Returns:
            List of matching EndpointInfo objects
        """
        matches = []

        for service in self.manifest.services:
            for endpoint in service.endpoints:
                match = True

                if query:
                    query_lower = query.lower()
                    searchable = " ".join(
                        [
                            endpoint.name,
                            endpoint.path,
                            endpoint.description or "",
                        ]
                    ).lower()
                    if query_lower not in searchable:
                        match = False

                if tags:
                    if not any(tag in endpoint.tags for tag in tags):
                        match = False

                if path_prefix:
                    if not (
                        endpoint.path.startswith(path_prefix)
                        or endpoint.full_path.startswith(path_prefix)
                    ):
                        match = False

                if match:
                    matches.append(endpoint)

        return matches

    def get_endpoints_by_dto(
        self, dto_name: str, dto_type: str = "request"
    ) -> List[EndpointInfo]:
        """Get endpoints that use a specific DTO.

        Args:
            dto_name: Name of the DTO
            dto_type: Type of DTO to match: "request", "response", or "both"

        Returns:
            List of EndpointInfo objects
        """
        endpoints = []

        for service in self.manifest.services:
            for endpoint in service.endpoints:
                match_request = (
                    dto_type in ("request", "both") and endpoint.request_dto == dto_name
                )
                match_response = (
                    dto_type in ("response", "both")
                    and endpoint.response_dto == dto_name
                )

                if match_request or match_response:
                    endpoints.append(endpoint)

        return endpoints

    # ==========================================================================
    # DTO Queries
    # ==========================================================================

    def get_dtos(self, service_name: Optional[str] = None) -> List[DtoSchema]:
        """Get all DTOs with optional service filter.

        Args:
            service_name: Optional service name to filter by

        Returns:
            List of DtoSchema objects
        """
        dtos = []

        services = self.manifest.services
        if service_name:
            service = self.get_service(service_name)
            services = [service] if service else []

        for service in services:
            dtos.extend(service.dto_schemas)

        return dtos

    def get_dto(self, name: str) -> Optional[DtoSchema]:
        """Get a DTO by name.

        Args:
            name: DTO name

        Returns:
            DtoSchema if found, None otherwise
        """
        return self.manifest.get_dto(name)

    def search_dtos(self, query: str) -> List[DtoSchema]:
        """Search DTOs by name or field names.

        Args:
            query: Search string

        Returns:
            List of matching DtoSchema objects
        """
        matches = []
        query_lower = query.lower()

        for service in self.manifest.services:
            for dto in service.dto_schemas:
                # Match by name
                if query_lower in dto.name.lower():
                    matches.append(dto)
                    continue

                # Match by field names
                for field in dto.fields:
                    if query_lower in field.name.lower():
                        matches.append(dto)
                        break

        return matches

    def get_dto_fields(
        self, dto_name: str, include_validations: bool = True
    ) -> List[DtoField]:
        """Get fields of a specific DTO.

        Args:
            dto_name: Name of the DTO
            include_validations: Whether to include validation rules

        Returns:
            List of DtoField objects
        """
        dto = self.get_dto(dto_name)
        if not dto:
            return []

        if include_validations:
            return dto.fields
        else:
            # Return fields without validations for token optimization
            return [
                DtoField(
                    name=f.name,
                    type=f.type,
                    required=f.required,
                    default_value=f.default_value,
                    alias=f.alias,
                )
                for f in dto.fields
            ]

    def get_dto_hierarchy(self, dto_name: str) -> Dict[str, Any]:
        """Get the hierarchy and relationships of a DTO.

        Args:
            dto_name: Name of the DTO

        Returns:
            Dictionary with DTO info and related endpoints
        """
        dto = self.get_dto(dto_name)
        if not dto:
            return {}

        # Find endpoints that use this DTO
        request_endpoints = self.get_endpoints_by_dto(dto_name, "request")
        response_endpoints = self.get_endpoints_by_dto(dto_name, "response")

        return {
            "dto": dto,
            "used_as_request_by": request_endpoints,
            "used_as_response_by": response_endpoints,
        }

    # ==========================================================================
    # Environment & Configuration Queries
    # ==========================================================================

    def get_environment_variables(
        self,
        service_name: Optional[str] = None,
        include_global: bool = True,
    ) -> List[EnvironmentVariable]:
        """Get environment variables.

        Args:
            service_name: Optional service name to filter by
            include_global: Whether to include global environment variables

        Returns:
            List of EnvironmentVariable objects
        """
        env_vars = []

        if include_global:
            env_vars.extend(self.manifest.global_env_vars)

        if service_name:
            service = self.get_service(service_name)
            if service:
                env_vars.extend(service.environment_vars)
        else:
            for service in self.manifest.services:
                env_vars.extend(service.environment_vars)

        # Remove duplicates
        seen = set()
        unique_vars = []
        for var in env_vars:
            if var.name not in seen:
                seen.add(var.name)
                unique_vars.append(var)

        return unique_vars

    def get_ports(self, service_name: Optional[str] = None) -> List[PortConfig]:
        """Get port configurations.

        Args:
            service_name: Optional service name to filter by

        Returns:
            List of PortConfig objects
        """
        ports = []

        if service_name:
            service = self.get_service(service_name)
            if service:
                ports.extend(service.ports)
        else:
            for service in self.manifest.services:
                ports.extend(service.ports)

        return ports

    # ==========================================================================
    # Dependency Queries
    # ==========================================================================

    def get_dependencies(
        self, service_name: Optional[str] = None
    ) -> List[ServiceDependency]:
        """Get service dependencies.

        Args:
            service_name: Optional service name to filter by

        Returns:
            List of ServiceDependency objects
        """
        dependencies = []

        if service_name:
            service = self.get_service(service_name)
            if service:
                dependencies.extend(service.dependencies)
        else:
            for service in self.manifest.services:
                dependencies.extend(service.dependencies)

        return dependencies

    def get_service_graph(self) -> Dict[str, List[str]]:
        """Get a graph of service dependencies.

        Returns:
            Dictionary mapping service names to list of dependent service names
        """
        graph = {}

        for service in self.manifest.services:
            graph[service.name] = []
            for dep in service.dependencies:
                if dep.service_name not in graph[service.name]:
                    graph[service.name].append(dep.service_name)

        return graph

    def find_circular_dependencies(self) -> List[List[str]]:
        """Find circular dependencies in the service graph.

        Returns:
            List of circular dependency chains
        """
        graph = self.get_service_graph()
        circles = []
        visited = set()

        def dfs(node: str, path: List[str]) -> None:
            if node in path:
                # Found a cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                circles.append(cycle)
                return

            if node in visited:
                return

            visited.add(node)
            path.append(node)

            for neighbor in graph.get(node, []):
                dfs(neighbor, path)

            path.pop()

        for service in graph:
            visited.clear()
            dfs(service, [])

        return circles

    # ==========================================================================
    # Summary & Statistics
    # ==========================================================================

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the project.

        Returns:
            Dictionary with project summary statistics
        """
        total_services = len(self.manifest.services)
        total_endpoints = sum(len(s.endpoints) for s in self.manifest.services)
        total_dtos = sum(len(s.dto_schemas) for s in self.manifest.services)
        total_env_vars = len(self.manifest.global_env_vars)

        languages = {}
        frameworks = {}

        for service in self.manifest.services:
            lang = service.language
            languages[lang] = languages.get(lang, 0) + 1

            if service.framework:
                fw = service.framework
                frameworks[fw] = frameworks.get(fw, 0) + 1

        return {
            "project_name": self.manifest.project_name,
            "version": self.manifest.version,
            "last_updated": self.manifest.last_updated,
            "statistics": {
                "services": total_services,
                "endpoints": total_endpoints,
                "dtos": total_dtos,
                "global_env_vars": total_env_vars,
            },
            "languages": languages,
            "frameworks": frameworks,
        }

    def export_summary(self, format: str = "json") -> str:
        """Export project summary in various formats.

        Args:
            format: Export format ("json", "markdown", "yaml")

        Returns:
            Formatted string
        """
        summary = self.get_summary()

        if format == "json":
            return json.dumps(summary, indent=2, default=str)

        elif format == "markdown":
            lines = [
                f"# {summary['project_name']} - Project Summary",
                "",
                f"**Version:** {summary['version']}",
                f"**Last Updated:** {summary['last_updated']}",
                "",
                "## Statistics",
                "",
                f"- **Services:** {summary['statistics']['services']}",
                f"- **Endpoints:** {summary['statistics']['endpoints']}",
                f"- **DTOs:** {summary['statistics']['dtos']}",
                f"- **Global Environment Variables:** {summary['statistics']['global_env_vars']}",
                "",
                "## Languages",
                "",
            ]

            for lang, count in summary["languages"].items():
                lines.append(f"- {lang}: {count} service(s)")

            if summary["frameworks"]:
                lines.extend(["", "## Frameworks", ""])
                for fw, count in summary["frameworks"].items():
                    lines.append(f"- {fw}: {count} service(s)")

            return "\n".join(lines)

        elif format == "yaml":
            try:
                import yaml

                return yaml.dump(summary, default_flow_style=False)
            except ImportError:
                raise ImportError(
                    "PyYAML is required for YAML export. Install with: pip install pyyaml"
                )

        else:
            raise ValueError(f"Unsupported format: {format}")


class TokenOptimizedQuery:
    """Token-optimized queries that return minimal information.

    This class provides methods that return only essential information
    to minimize token usage when querying the manifest.
    """

    def __init__(self, api: ManifestAPI):
        """Initialize with a ManifestAPI instance.

        Args:
            api: ManifestAPI instance
        """
        self.api = api

    def get_endpoint_signature(
        self, path: str, method: HttpMethod
    ) -> Optional[Dict[str, Any]]:
        """Get minimal endpoint signature for token optimization.

        Args:
            path: Endpoint path
            method: HTTP method

        Returns:
            Minimal endpoint information
        """
        endpoint = self.api.get_endpoint(path, method)
        if not endpoint:
            return None

        return {
            "method": endpoint.method,
            "path": endpoint.path,
            "auth": endpoint.requires_auth,
            "request": endpoint.request_dto,
            "response": endpoint.response_dto,
        }

    def get_dto_signature(self, dto_name: str) -> Optional[Dict[str, Any]]:
        """Get minimal DTO signature for token optimization.

        Args:
            dto_name: DTO name

        Returns:
            Minimal DTO information
        """
        dto = self.api.get_dto(dto_name)
        if not dto:
            return None

        return {
            "name": dto.name,
            "fields": [
                {
                    "name": f.name,
                    "type": f.type,
                    "required": f.required,
                }
                for f in dto.fields
            ],
        }

    def get_service_overview(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get minimal service overview for token optimization.

        Args:
            service_name: Service name

        Returns:
            Minimal service information
        """
        service = self.api.get_service(service_name)
        if not service:
            return None

        return {
            "name": service.name,
            "language": service.language,
            "framework": service.framework,
            "endpoints": len(service.endpoints),
            "dtos": len(service.dto_schemas),
            "ports": [p.port for p in service.ports],
        }

    def list_all_endpoints_compact(self) -> List[Dict[str, str]]:
        """Get compact list of all endpoints.

        Returns:
            List of minimal endpoint dictionaries
        """
        return [
            {
                "method": ep.method.value,
                "path": ep.full_path or ep.path,
                "dto": ep.request_dto or "",
            }
            for service in self.api.manifest.services
            for ep in service.endpoints
        ]

    def list_all_dtos_compact(self) -> List[Dict[str, Any]]:
        """Get compact list of all DTOs.

        Returns:
            List of minimal DTO dictionaries
        """
        return [
            {
                "name": dto.name,
                "fields": len(dto.fields),
                "service": service.name,
            }
            for service in self.api.manifest.services
            for dto in service.dto_schemas
        ]
