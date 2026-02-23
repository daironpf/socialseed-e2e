"""Multi-Protocol Contract Testing Support.

This module extends contract testing to support multiple protocols:
- REST API contracts
- GraphQL contracts
- gRPC contracts

Example:
    >>> from socialseed_e2e.contract_testing import MultiProtocolContractBuilder
    >>> builder = MultiProtocolContractBuilder()
    >>> contract = builder.build_graphql_contract(schema, operations)
"""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ProtocolType(Enum):
    """Supported protocol types."""

    REST = "rest"
    GRAPHQL = "graphql"
    GRPC = "grpc"
    WEBSOCKET = "websocket"


@dataclass
class FieldDefinition:
    """Definition of a field in a schema."""

    name: str
    field_type: str
    required: bool = True
    description: str = ""
    default_value: Any = None
    constraints: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RESTEndpoint:
    """REST API endpoint definition."""

    path: str
    method: str  # GET, POST, PUT, DELETE, etc.
    description: str = ""
    path_parameters: List[FieldDefinition] = field(default_factory=list)
    query_parameters: List[FieldDefinition] = field(default_factory=list)
    request_headers: Dict[str, str] = field(default_factory=dict)
    request_body: Optional[Dict[str, Any]] = None
    response_statuses: Dict[int, Dict[str, Any]] = field(default_factory=dict)

    def to_contract_interaction(self) -> Dict[str, Any]:
        """Convert to standard contract interaction format."""
        return {
            "description": f"{self.method} {self.path}",
            "provider_state": "",
            "request": {
                "method": self.method,
                "path": self.path,
                "headers": self.request_headers,
                "body": self.request_body,
            },
            "response": {
                "status": list(self.response_statuses.keys())[0]
                if self.response_statuses
                else 200,
                "body": list(self.response_statuses.values())[0]
                if self.response_statuses
                else None,
            },
        }


@dataclass
class GraphQLOperation:
    """GraphQL operation definition."""

    name: str
    operation_type: str  # query, mutation, subscription
    description: str = ""
    arguments: List[FieldDefinition] = field(default_factory=list)
    return_type: str = ""
    return_fields: List[str] = field(default_factory=list)

    def to_contract_interaction(self) -> Dict[str, Any]:
        """Convert to standard contract interaction format."""
        query = self._build_query()

        return {
            "description": f"GraphQL {self.operation_type}: {self.name}",
            "provider_state": "",
            "request": {
                "method": "POST",
                "path": "/graphql",
                "headers": {"Content-Type": "application/json"},
                "body": {
                    "query": query,
                    "variables": {},
                    "operationName": self.name,
                },
            },
            "response": {
                "status": 200,
                "body": {"data": {self.name: self._build_response_shape()}},
            },
        }

    def _build_query(self) -> str:
        """Build GraphQL query string."""
        args_str = ""
        if self.arguments:
            args = [f"${arg.name}: {arg.field_type}" for arg in self.arguments]
            args_str = f"({', '.join(args)})"

        fields_str = "\n    ".join(self.return_fields) if self.return_fields else ""

        return f"""
{self.operation_type} {self.name}{args_str} {{
    {self.name}{args_str} {{
        {fields_str}
    }}
}}
""".strip()

    def _build_response_shape(self) -> Any:
        """Build expected response shape."""
        if not self.return_fields:
            return {}

        # Build nested structure based on field paths
        result = {}
        for field_path in self.return_fields:
            parts = field_path.split(".")
            current = result
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            current[parts[-1]] = f"<{self.return_type}>"

        return result


@dataclass
class GRPCMethod:
    """gRPC method definition."""

    name: str
    service: str
    package: str = ""
    description: str = ""
    input_type: str = ""
    output_type: str = ""
    input_fields: List[FieldDefinition] = field(default_factory=list)
    output_fields: List[FieldDefinition] = field(default_factory=list)
    streaming_input: bool = False
    streaming_output: bool = False

    def to_contract_interaction(self) -> Dict[str, Any]:
        """Convert to standard contract interaction format."""
        full_service_name = (
            f"{self.package}.{self.service}" if self.package else self.service
        )

        return {
            "description": f"gRPC {full_service_name}/{self.name}",
            "provider_state": "",
            "request": {
                "method": "GRPC",
                "path": f"/{full_service_name}/{self.name}",
                "headers": {
                    "Content-Type": "application/grpc",
                },
                "body": self._build_request_shape(),
            },
            "response": {
                "status": 0,  # gRPC status codes
                "body": self._build_response_shape(),
            },
        }

    def _build_request_shape(self) -> Dict[str, Any]:
        """Build request message shape."""
        return {field.name: f"<{field.field_type}>" for field in self.input_fields}

    def _build_response_shape(self) -> Dict[str, Any]:
        """Build response message shape."""
        return {field.name: f"<{field.field_type}>" for field in self.output_fields}


class ProtocolContractBuilder(ABC):
    """Abstract base class for protocol-specific contract builders."""

    @abstractmethod
    def build_contract(
        self,
        consumer: str,
        provider: str,
        endpoints: List[Any],
    ) -> str:
        """Build contract for the specific protocol."""
        pass


class RESTContractBuilder(ProtocolContractBuilder):
    """Builder for REST API contracts."""

    def build_contract(
        self,
        consumer: str,
        provider: str,
        endpoints: List[RESTEndpoint],
    ) -> str:
        """Build REST API contract.

        Args:
            consumer: Consumer application name
            provider: Provider application name
            endpoints: List of REST endpoint definitions

        Returns:
            Contract JSON string
        """
        contract = {
            "consumer": consumer,
            "provider": provider,
            "protocol": ProtocolType.REST.value,
            "interactions": [
                endpoint.to_contract_interaction() for endpoint in endpoints
            ],
            "metadata": {
                "pactSpecification": {"version": "3.0.0"},
            },
        }

        return json.dumps(contract, indent=2)

    def from_openapi_spec(
        self,
        consumer: str,
        provider: str,
        openapi_spec: Dict[str, Any],
    ) -> str:
        """Build contract from OpenAPI specification.

        Args:
            consumer: Consumer application name
            provider: Provider application name
            openapi_spec: OpenAPI specification dictionary

        Returns:
            Contract JSON string
        """
        endpoints = []

        paths = openapi_spec.get("paths", {})
        for path, methods in paths.items():
            for method, spec in methods.items():
                if method.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                    endpoint = self._parse_openapi_endpoint(path, method.upper(), spec)
                    endpoints.append(endpoint)

        return self.build_contract(consumer, provider, endpoints)

    def _parse_openapi_endpoint(
        self, path: str, method: str, spec: Dict[str, Any]
    ) -> RESTEndpoint:
        """Parse OpenAPI path item into RESTEndpoint."""
        # Extract path parameters
        path_params = []
        parameters = spec.get("parameters", [])
        for param in parameters:
            if param.get("in") == "path":
                path_params.append(
                    FieldDefinition(
                        name=param["name"],
                        field_type=param.get("schema", {}).get("type", "string"),
                        required=param.get("required", True),
                        description=param.get("description", ""),
                    )
                )

        # Extract request body
        request_body = None
        if "requestBody" in spec:
            content = spec["requestBody"].get("content", {})
            if "application/json" in content:
                schema = content["application/json"].get("schema", {})
                request_body = self._schema_to_example(schema)

        # Extract responses
        responses = {}
        for status_code, response_spec in spec.get("responses", {}).items():
            if status_code.isdigit():
                content = response_spec.get("content", {})
                if "application/json" in content:
                    schema = content["application/json"].get("schema", {})
                    responses[int(status_code)] = self._schema_to_example(schema)

        return RESTEndpoint(
            path=path,
            method=method,
            description=spec.get("summary", ""),
            path_parameters=path_params,
            request_body=request_body,
            response_statuses=responses,
        )

    def _schema_to_example(self, schema: Dict[str, Any]) -> Any:
        """Convert JSON schema to example value."""
        schema_type = schema.get("type")

        if schema_type == "object":
            example = {}
            properties = schema.get("properties", {})
            for prop_name, prop_schema in properties.items():
                example[prop_name] = self._schema_to_example(prop_schema)
            return example

        elif schema_type == "array":
            items = schema.get("items", {})
            return [self._schema_to_example(items)]

        elif schema_type == "string":
            return "<string>"

        elif schema_type == "integer":
            return 0

        elif schema_type == "number":
            return 0.0

        elif schema_type == "boolean":
            return True

        return None


class GraphQLContractBuilder(ProtocolContractBuilder):
    """Builder for GraphQL contracts."""

    def build_contract(
        self,
        consumer: str,
        provider: str,
        operations: List[GraphQLOperation],
    ) -> str:
        """Build GraphQL contract.

        Args:
            consumer: Consumer application name
            provider: Provider application name
            operations: List of GraphQL operation definitions

        Returns:
            Contract JSON string
        """
        contract = {
            "consumer": consumer,
            "provider": provider,
            "protocol": ProtocolType.GRAPHQL.value,
            "interactions": [op.to_contract_interaction() for op in operations],
            "metadata": {
                "pactSpecification": {"version": "3.0.0"},
            },
        }

        return json.dumps(contract, indent=2)

    def from_graphql_schema(
        self,
        consumer: str,
        provider: str,
        schema: Dict[str, Any],
        operations: Optional[List[str]] = None,
    ) -> str:
        """Build contract from GraphQL introspection schema.

        Args:
            consumer: Consumer application name
            provider: Provider application name
            schema: GraphQL introspection schema
            operations: Optional list of operation names to include

        Returns:
            Contract JSON string
        """
        graphql_ops = []

        # Parse queries
        query_type = schema.get("data", {}).get("__schema", {}).get("queryType", {})
        if query_type:
            fields = query_type.get("fields", [])
            for field in fields:
                if operations and field["name"] not in operations:
                    continue

                op = self._parse_graphql_field(field, "query")
                graphql_ops.append(op)

        # Parse mutations
        mutation_type = (
            schema.get("data", {}).get("__schema", {}).get("mutationType", {})
        )
        if mutation_type:
            fields = mutation_type.get("fields", [])
            for field in fields:
                if operations and field["name"] not in operations:
                    continue

                op = self._parse_graphql_field(field, "mutation")
                graphql_ops.append(op)

        return self.build_contract(consumer, provider, graphql_ops)

    def _parse_graphql_field(
        self, field: Dict[str, Any], operation_type: str
    ) -> GraphQLOperation:
        """Parse GraphQL field into operation."""
        args = []
        for arg in field.get("args", []):
            args.append(
                FieldDefinition(
                    name=arg["name"],
                    field_type=self._graphql_type_to_string(arg.get("type", {})),
                    required=arg.get("type", {}).get("kind") == "NON_NULL",
                )
            )

        # Extract return fields from type
        return_fields = self._extract_return_fields(field.get("type", {}))

        return GraphQLOperation(
            name=field["name"],
            operation_type=operation_type,
            description=field.get("description", ""),
            arguments=args,
            return_type=self._graphql_type_to_string(field.get("type", {})),
            return_fields=return_fields,
        )

    def _graphql_type_to_string(self, type_def: Dict[str, Any]) -> str:
        """Convert GraphQL type definition to string."""
        kind = type_def.get("kind")

        if kind == "NON_NULL":
            of_type = type_def.get("ofType", {})
            return self._graphql_type_to_string(of_type)

        elif kind == "LIST":
            of_type = type_def.get("ofType", {})
            return f"[{self._graphql_type_to_string(of_type)}]"

        elif kind == "SCALAR":
            return type_def.get("name", "String")

        elif kind == "OBJECT":
            return type_def.get("name", "Object")

        return "String"

    def _extract_return_fields(self, type_def: Dict[str, Any]) -> List[str]:
        """Extract field names from GraphQL type."""
        fields = []

        # Unwrap non-null and list types
        while type_def.get("kind") in ["NON_NULL", "LIST"]:
            type_def = type_def.get("ofType", {})

        # Get fields from object type
        if type_def.get("kind") == "OBJECT":
            for field in type_def.get("fields", []):
                fields.append(field["name"])

        return fields


class GRPCContractBuilder(ProtocolContractBuilder):
    """Builder for gRPC contracts."""

    def build_contract(
        self,
        consumer: str,
        provider: str,
        methods: List[GRPCMethod],
    ) -> str:
        """Build gRPC contract.

        Args:
            consumer: Consumer application name
            provider: Provider application name
            methods: List of gRPC method definitions

        Returns:
            Contract JSON string
        """
        contract = {
            "consumer": consumer,
            "provider": provider,
            "protocol": ProtocolType.GRPC.value,
            "interactions": [method.to_contract_interaction() for method in methods],
            "metadata": {
                "pactSpecification": {"version": "3.0.0"},
            },
        }

        return json.dumps(contract, indent=2)

    def from_proto_file(
        self,
        consumer: str,
        provider: str,
        proto_content: str,
        package: str = "",
    ) -> str:
        """Build contract from Protocol Buffer definition.

        Args:
            consumer: Consumer application name
            provider: Provider application name
            proto_content: Proto file content
            package: Package name

        Returns:
            Contract JSON string
        """
        methods = self._parse_proto(proto_content, package)
        return self.build_contract(consumer, provider, methods)

    def _parse_proto(self, proto_content: str, package: str) -> List[GRPCMethod]:
        """Parse proto file content to extract methods."""
        methods = []

        # Simple regex-based parsing for demonstration
        # In production, use proper protobuf parsing library

        # Find service definitions
        service_pattern = r"service\s+(\w+)\s*\{([^}]+)\}"
        method_pattern = (
            r"rpc\s+(\w+)\s*\(\s*(\??)\s*(\w+)\s*\)\s+returns\s*\(\s*(\??)\s*(\w+)\s*\)"
        )

        import re

        for service_match in re.finditer(service_pattern, proto_content):
            service_name = service_match.group(1)
            service_body = service_match.group(2)

            for method_match in re.finditer(method_pattern, service_body):
                method_name = method_match.group(1)
                streaming_input = method_match.group(2) == "stream"
                input_type = method_match.group(3)
                streaming_output = method_match.group(4) == "stream"
                output_type = method_match.group(5)

                method = GRPCMethod(
                    name=method_name,
                    service=service_name,
                    package=package,
                    input_type=input_type,
                    output_type=output_type,
                    streaming_input=streaming_input,
                    streaming_output=streaming_output,
                )
                methods.append(method)

        return methods


class MultiProtocolContractBuilder:
    """Unified builder for multi-protocol contracts.

    Provides a single interface for building contracts across
    different protocols.

    Example:
        >>> builder = MultiProtocolContractBuilder()
        >>>
        >>> # REST contract
        >>> rest_contract = builder.build_rest_contract(
        ...     consumer="web-app",
        ...     provider="api-service",
        ...     endpoints=[...]
        ... )
        >>>
        >>> # GraphQL contract
        >>> graphql_contract = builder.build_graphql_contract(
        ...     consumer="mobile-app",
        ...     provider="graphql-api",
        ...     operations=[...]
        ... )
    """

    def __init__(self):
        """Initialize the multi-protocol builder."""
        self._rest_builder = RESTContractBuilder()
        self._graphql_builder = GraphQLContractBuilder()
        self._grpc_builder = GRPCContractBuilder()

    def build_rest_contract(
        self,
        consumer: str,
        provider: str,
        endpoints: List[RESTEndpoint],
    ) -> str:
        """Build REST API contract."""
        return self._rest_builder.build_contract(consumer, provider, endpoints)

    def build_rest_from_openapi(
        self,
        consumer: str,
        provider: str,
        openapi_spec: Dict[str, Any],
    ) -> str:
        """Build REST contract from OpenAPI spec."""
        return self._rest_builder.from_openapi_spec(consumer, provider, openapi_spec)

    def build_graphql_contract(
        self,
        consumer: str,
        provider: str,
        operations: List[GraphQLOperation],
    ) -> str:
        """Build GraphQL contract."""
        return self._graphql_builder.build_contract(consumer, provider, operations)

    def build_graphql_from_schema(
        self,
        consumer: str,
        provider: str,
        schema: Dict[str, Any],
        operations: Optional[List[str]] = None,
    ) -> str:
        """Build GraphQL contract from schema."""
        return self._graphql_builder.from_graphql_schema(
            consumer, provider, schema, operations
        )

    def build_grpc_contract(
        self,
        consumer: str,
        provider: str,
        methods: List[GRPCMethod],
    ) -> str:
        """Build gRPC contract."""
        return self._grpc_builder.build_contract(consumer, provider, methods)

    def build_grpc_from_proto(
        self,
        consumer: str,
        provider: str,
        proto_content: str,
        package: str = "",
    ) -> str:
        """Build gRPC contract from proto file."""
        return self._grpc_builder.from_proto_file(
            consumer, provider, proto_content, package
        )
