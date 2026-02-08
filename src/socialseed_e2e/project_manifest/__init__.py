"""AI Project Manifest (JSON Knowledge Base) for token optimization.

This package provides functionality to generate, maintain, and query
a project knowledge manifest that stores:
- All detected endpoints and their HTTP methods
- DTO schemas and field validation rules
- Port configurations and environment variables
- Relationships between services

Example:
    >>> from socialseed_e2e.project_manifest import ManifestGenerator, ManifestAPI
    >>>
    >>> # Generate manifest
    >>> generator = ManifestGenerator("/path/to/project")
    >>> manifest = generator.generate()
    >>>
    >>> # Query manifest
    >>> api = ManifestAPI("/path/to/project")
    >>> endpoints = api.get_endpoints(method=HttpMethod.GET)
    >>> user_dto = api.get_dto("UserRequest")
"""

from socialseed_e2e.project_manifest.api import ManifestAPI, TokenOptimizedQuery
from socialseed_e2e.project_manifest.file_watcher import FileWatcher, SmartSyncManager
from socialseed_e2e.project_manifest.generator import ManifestGenerator
from socialseed_e2e.project_manifest.models import (
    DtoField,
    DtoSchema,
    EndpointInfo,
    EndpointParameter,
    EnvironmentVariable,
    FileMetadata,
    HttpMethod,
    PortConfig,
    ProjectKnowledge,
    ServiceDependency,
    ServiceInfo,
    ValidationRule,
)
from socialseed_e2e.project_manifest.parsers import (
    BaseParser,
    JavaParser,
    NodeParser,
    ParseResult,
    PythonParser,
    parser_registry,
)

__all__ = [
    # Main classes
    "ManifestGenerator",
    "ManifestAPI",
    "TokenOptimizedQuery",
    "FileWatcher",
    "SmartSyncManager",
    # Models
    "ProjectKnowledge",
    "ServiceInfo",
    "EndpointInfo",
    "EndpointParameter",
    "DtoSchema",
    "DtoField",
    "ValidationRule",
    "PortConfig",
    "EnvironmentVariable",
    "ServiceDependency",
    "FileMetadata",
    "HttpMethod",
    # Parsers
    "BaseParser",
    "PythonParser",
    "JavaParser",
    "NodeParser",
    "ParseResult",
    "parser_registry",
]
