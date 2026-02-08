"""Pydantic models for AI Project Manifest (JSON Knowledge Base).

These models define the structure of project_knowledge.json which stores
all detected information about the user's project for AI token optimization.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class HttpMethod(str, Enum):
    """HTTP methods supported."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class ValidationRule(BaseModel):
    """Validation rule for a DTO field."""

    rule_type: str = Field(
        ...,
        description="Type of validation: min_length, max_length, regex, gt, lt, etc.",
    )
    value: Any = Field(..., description="Validation value")
    error_message: Optional[str] = Field(None, description="Custom error message")


class DtoField(BaseModel):
    """Field definition in a DTO."""

    name: str = Field(..., description="Field name")
    type: str = Field(..., description="Field type (Python type annotation)")
    required: bool = Field(True, description="Whether the field is required")
    default_value: Optional[Any] = Field(None, description="Default value if not required")
    validations: List[ValidationRule] = Field(default_factory=list, description="Validation rules")
    description: Optional[str] = Field(None, description="Field description")
    alias: Optional[str] = Field(None, description="Serialization alias")


class DtoSchema(BaseModel):
    """DTO schema definition."""

    name: str = Field(..., description="DTO class name")
    fields: List[DtoField] = Field(default_factory=list, description="DTO fields")
    file_path: str = Field(..., description="Source file path")
    line_number: Optional[int] = Field(None, description="Line number in source file")
    description: Optional[str] = Field(None, description="DTO description")
    base_classes: List[str] = Field(default_factory=list, description="Base classes")


class EndpointParameter(BaseModel):
    """Parameter for an endpoint."""

    name: str = Field(..., description="Parameter name")
    param_type: str = Field(..., description="Parameter type")
    location: str = Field(..., description="Parameter location: path, query, body, header")
    required: bool = Field(True, description="Whether parameter is required")
    dto_schema: Optional[str] = Field(None, description="Reference to DTO schema if applicable")


class EndpointInfo(BaseModel):
    """REST endpoint information."""

    name: str = Field(..., description="Endpoint handler name")
    method: HttpMethod = Field(..., description="HTTP method")
    path: str = Field(..., description="Endpoint path")
    full_path: str = Field(..., description="Full path including base path")
    parameters: List[EndpointParameter] = Field(
        default_factory=list, description="Endpoint parameters"
    )
    request_dto: Optional[str] = Field(None, description="Request DTO name")
    response_dto: Optional[str] = Field(None, description="Response DTO name")
    requires_auth: bool = Field(False, description="Whether authentication is required")
    auth_roles: List[str] = Field(default_factory=list, description="Required roles if applicable")
    file_path: str = Field(..., description="Source file path")
    line_number: Optional[int] = Field(None, description="Line number in source file")
    description: Optional[str] = Field(None, description="Endpoint description")
    tags: List[str] = Field(default_factory=list, description="Tags/categories")


class EnvironmentVariable(BaseModel):
    """Environment variable configuration."""

    name: str = Field(..., description="Variable name")
    default_value: Optional[str] = Field(None, description="Default value")
    required: bool = Field(True, description="Whether the variable is required")
    description: Optional[str] = Field(None, description="Variable description")
    example: Optional[str] = Field(None, description="Example value")


class PortConfig(BaseModel):
    """Port configuration."""

    port: int = Field(..., description="Port number")
    protocol: str = Field("http", description="Protocol: http, https, grpc, tcp")
    description: Optional[str] = Field(None, description="Port purpose")
    exposed: bool = Field(True, description="Whether port is exposed externally")


class ServiceDependency(BaseModel):
    """Dependency on another service."""

    service_name: str = Field(..., description="Name of the dependent service")
    endpoint: Optional[str] = Field(None, description="Endpoint being called")
    method: Optional[HttpMethod] = Field(None, description="HTTP method used")
    description: Optional[str] = Field(None, description="Description of the relationship")


class ServiceInfo(BaseModel):
    """Information about a service in the project."""

    name: str = Field(..., description="Service name")
    language: str = Field(..., description="Programming language: python, java, node, csharp, go")
    framework: Optional[str] = Field(
        None, description="Framework: spring, flask, fastapi, express, etc."
    )
    root_path: str = Field(..., description="Service root directory")
    endpoints: List[EndpointInfo] = Field(default_factory=list, description="Service endpoints")
    dto_schemas: List[DtoSchema] = Field(default_factory=list, description="Service DTOs")
    ports: List[PortConfig] = Field(default_factory=list, description="Service ports")
    environment_vars: List[EnvironmentVariable] = Field(
        default_factory=list, description="Environment variables"
    )
    dependencies: List[ServiceDependency] = Field(
        default_factory=list, description="Service dependencies"
    )
    file_paths: List[str] = Field(default_factory=list, description="Key source files")
    config_files: List[str] = Field(default_factory=list, description="Configuration files")


class FileMetadata(BaseModel):
    """Metadata for a tracked file."""

    path: str = Field(..., description="File path")
    checksum: str = Field(..., description="File checksum for change detection")
    last_modified: datetime = Field(..., description="Last modification time")
    language: Optional[str] = Field(None, description="Detected language")
    scanned_at: datetime = Field(
        default_factory=datetime.utcnow, description="When file was last scanned"
    )


class ProjectKnowledge(BaseModel):
    """Root model for project knowledge manifest."""

    version: str = Field("1.0.0", description="Manifest version")
    project_name: str = Field(..., description="Project name")
    project_root: str = Field(..., description="Project root directory")
    generated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Generation timestamp"
    )
    last_updated: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )
    services: List[ServiceInfo] = Field(
        default_factory=list, description="All services in the project"
    )
    file_metadata: Dict[str, FileMetadata] = Field(
        default_factory=dict, description="Tracked files metadata"
    )
    global_env_vars: List[EnvironmentVariable] = Field(
        default_factory=list, description="Global environment variables"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    def get_service(self, name: str) -> Optional[ServiceInfo]:
        """Get a service by name."""
        for service in self.services:
            if service.name == name:
                return service
        return None

    def get_endpoint(
        self, path: str, method: Optional[HttpMethod] = None
    ) -> Optional[EndpointInfo]:
        """Get an endpoint by path and optional method."""
        for service in self.services:
            for endpoint in service.endpoints:
                if endpoint.path == path or endpoint.full_path == path:
                    if method is None or endpoint.method == method:
                        return endpoint
        return None

    def get_dto(self, name: str) -> Optional[DtoSchema]:
        """Get a DTO by name."""
        for service in self.services:
            for dto in service.dto_schemas:
                if dto.name == name:
                    return dto
        return None

    def update_timestamp(self) -> None:
        """Update the last_updated timestamp."""
        self.last_updated = datetime.utcnow()
