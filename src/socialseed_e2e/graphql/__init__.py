"""Advanced GraphQL Testing Module.

This module provides comprehensive GraphQL testing capabilities including:
- Query complexity analysis and validation
- Introspection and schema analysis
- Subscription support (WebSocket)
- Federation testing
- Performance and load testing
- N+1 query detection

Usage:
    from socialseed_e2e.graphql import (
        GraphQLTestingSuite,
        SchemaAnalyzer,
        SubscriptionManager,
    )
"""

import json
import re
import time
import uuid
import websocket
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set
from enum import Enum

from pydantic import BaseModel


class OperationType(str, Enum):
    """GraphQL operation types."""

    QUERY = "query"
    MUTATION = "mutation"
    SUBSCRIPTION = "subscription"


class ComplexityLevel(str, Enum):
    """Query complexity levels."""

    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
    CRITICAL = "critical"


@dataclass
class GraphQLResponse:
    """Represents a GraphQL response."""

    data: Optional[Dict[str, Any]]
    errors: Optional[List[Dict[str, Any]]] = None
    extensions: Optional[Dict[str, Any]] = None
    duration_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def success(self) -> bool:
        """Check if the response is successful."""
        return self.errors is None or len(self.errors) == 0


@dataclass
class QueryComplexity:
    """Query complexity analysis result."""

    score: float
    level: ComplexityLevel
    depth: int
    fields_selected: int
    list_fields: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class SchemaType:
    """Represents a GraphQL type."""

    name: str
    kind: str
    fields: Dict[str, "SchemaField"] = field(default_factory=dict)
    interfaces: List[str] = field(default_factory=list)
    enum_values: List[str] = field(default_factory=list)
    input_fields: Dict[str, "SchemaField"] = field(default_factory=dict)


@dataclass
class SchemaField:
    """Represents a GraphQL field."""

    name: str
    type: str
    args: Dict[str, Any] = field(default_factory=dict)
    is_non_null: bool = False
    is_list: bool = False


class SchemaAnalyzer:
    """Analyzes GraphQL schemas and queries.

    Example:
        analyzer = SchemaAnalyzer()
        await analyzer.load_from_introspection(endpoint)

        # Analyze query complexity
        complexity = analyzer.analyze_query_complexity(query)
        print(f"Complexity: {complexity.score}")

        # Get type information
        user_type = analyzer.get_type("User")
    """

    def __init__(self):
        """Initialize the schema analyzer."""
        self.types: Dict[str, SchemaType] = {}
        self.query_type: Optional[str] = None
        self.mutation_type: Optional[str] = None
        self.subscription_type: Optional[str] = None

    def load_from_introspection(self, introspection_result: Dict[str, Any]) -> None:
        """Load schema from introspection result.

        Args:
            introspection_result: Result from GraphQL introspection query
        """
        schema = introspection_result.get("data", {}).get("__schema", {})

        # Load types
        for type_def in schema.get("types", []):
            if type_def["name"].startswith("__"):
                continue

            schema_type = SchemaType(
                name=type_def["name"],
                kind=type_def.get("kind", "object"),
                interfaces=type_def.get("interfaces", []),
                enum_values=[e["name"] for e in type_def.get("enumValues", [])],
            )

            # Load fields
            for field_def in type_def.get("fields", []):
                field_obj = SchemaField(
                    name=field_def["name"],
                    type=field_def["type"]["name"],
                    args={a["name"]: a for a in field_def.get("args", [])},
                    is_non_null=field_def["type"].get("nonNull", False),
                    is_list=field_def["type"].get("kind") == "LIST",
                )
                schema_type.fields[field_def["name"]] = field_obj

            self.types[type_def["name"]] = schema_type

        # Store root types
        self.query_type = schema.get("queryType", {}).get("name")
        self.mutation_type = schema.get("mutationType", {}).get("name")
        self.subscription_type = schema.get("subscriptionType", {}).get("name")

    def get_type(self, type_name: str) -> Optional[SchemaType]:
        """Get type information by name.

        Args:
            type_name: Name of the type

        Returns:
            SchemaType or None if not found
        """
        return self.types.get(type_name)

    def analyze_query_complexity(self, query: str) -> QueryComplexity:
        """Analyze query complexity.

        Args:
            query: GraphQL query string

        Returns:
            QueryComplexity with analysis results
        """
        # Parse query (simplified - in production use graphql-core)
        depth = self._calculate_depth(query)
        fields = self._extract_fields(query)
        list_fields = [f for f in fields if self._is_list_field(f)]

        # Calculate complexity score
        score = self._calculate_score(depth, fields, list_fields)

        # Determine level
        if score < 10:
            level = ComplexityLevel.SIMPLE
        elif score < 50:
            level = ComplexityLevel.MEDIUM
        elif score < 100:
            level = ComplexityLevel.COMPLEX
        else:
            level = ComplexityLevel.CRITICAL

        # Generate warnings
        warnings = []
        if depth > 5:
            warnings.append(f"Query depth of {depth} may impact performance")
        if len(list_fields) > 3:
            warnings.append(
                f"Multiple list fields ({len(list_fields)}) may cause N+1 queries"
            )
        if score > 100:
            warnings.append(f"High complexity score ({score}) - consider simplifying")

        return QueryComplexity(
            score=score,
            level=level,
            depth=depth,
            fields_selected=len(fields),
            list_fields=list_fields,
            warnings=warnings,
        )

    def _calculate_depth(self, query: str) -> int:
        """Calculate maximum query depth."""
        max_depth = 0
        current_depth = 0

        for char in query:
            if char == "{":
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char == "}":
                current_depth -= 1

        return max_depth

    def _extract_fields(self, query: str) -> List[str]:
        """Extract field names from query."""
        fields = []
        pattern = r"(\w+)\s*(?:\(|:|\{|$)"
        matches = re.findall(pattern, query)
        for match in matches:
            if match[0] not in ["query", "mutation", "subscription", "fragment", "on"]:
                fields.append(match[0])
        return fields

    def _is_list_field(self, field_name: str) -> bool:
        """Check if field returns a list."""
        for schema_type in self.types.values():
            if field_name in schema_type.fields:
                return schema_type.fields[field_name].is_list
        return False

    def _calculate_score(
        self, depth: int, fields: List[str], list_fields: List[str]
    ) -> float:
        """Calculate complexity score."""
        score = depth * 10  # Depth contributes significantly
        score += len(fields) * 2  # Each field adds to complexity
        score += len(list_fields) * 15  # List fields are expensive
        return score

    def get_field_coverage(self, query: str) -> Dict[str, float]:
        """Calculate field coverage for a type.

        Args:
            query: GraphQL query

        Returns:
            Dict mapping type names to coverage percentage
        """
        # Simplified implementation
        queried_types = set()

        # Extract type names from query
        for type_name in self.types:
            if type_name in query:
                queried_types.add(type_name)

        coverage = {}
        for type_name in self.types:
            type_obj = self.types[type_name]
            if type_obj.fields:
                queried_fields = [f for f in type_obj.fields if f in query]
                coverage[type_name] = len(queried_fields) / len(type_obj.fields) * 100
            else:
                coverage[type_name] = 100.0

        return coverage


class SubscriptionManager:
    """Manages GraphQL subscriptions over WebSocket.

    Example:
        manager = SubscriptionManager("ws://localhost:4000/graphql")

        # Subscribe to events
        def on_user_created(user):
            print(f"User created: {user}")

        sub_id = manager.subscribe(
            "subscription { userCreated { id name email } }",
            on_user_created
        )

        # Cleanup
        manager.unsubscribe(sub_id)
    """

    def __init__(self, ws_url: str, headers: Optional[Dict[str, str]] = None):
        """Initialize subscription manager.

        Args:
            ws_url: WebSocket URL for GraphQL subscriptions
            headers: Optional headers for authentication
        """
        self.ws_url = ws_url
        self.headers = headers or {}
        self.ws: Optional[websocket.WebSocket] = None
        self.subscriptions: Dict[str, Callable] = {}
        self.connection_init: Dict[str, Any] = {}

    def connect(self) -> bool:
        """Establish WebSocket connection.

        Returns:
            True if connected successfully
        """
        try:
            self.ws = websocket.create_connection(
                self.ws_url,
                header=self.headers,
            )

            # Send connection init
            self._send({"type": "connection_init", **self.connection_init})

            # Wait for connection ack
            response = self._receive()
            if response.get("type") == "connection_ack":
                return True

            return False
        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    def disconnect(self) -> None:
        """Close WebSocket connection."""
        if self.ws:
            self._send({"type": "connection_terminate"})
            self.ws.close()
            self.ws = None

    def subscribe(
        self,
        query: str,
        callback: Callable[[Dict[str, Any]], None],
        variables: Optional[Dict[str, Any]] = None,
        operation_name: Optional[str] = None,
    ) -> str:
        """Subscribe to a GraphQL subscription.

        Args:
            query: GraphQL subscription query
            callback: Function to call when data arrives
            variables: Optional query variables
            operation_name: Optional operation name

        Returns:
            Subscription ID
        """
        if not self.ws:
            raise RuntimeError("Not connected. Call connect() first.")

        sub_id = str(uuid.uuid4())

        payload = {
            "id": sub_id,
            "type": "start",
            "payload": {
                "query": query,
                "variables": variables or {},
                "operationName": operation_name,
            },
        }

        self._send(payload)
        self.subscriptions[sub_id] = callback

        return sub_id

    def unsubscribe(self, subscription_id: str) -> None:
        """Unsubscribe from a subscription.

        Args:
            subscription_id: ID returned from subscribe()
        """
        if subscription_id in self.subscriptions:
            self._send({"type": "stop", "id": subscription_id})
            del self.subscriptions[subscription_id]

    def listen(self, timeout: Optional[float] = None) -> None:
        """Listen for subscription events.

        Args:
            timeout: Optional timeout in seconds
        """
        import select

        if not self.ws:
            raise RuntimeError("Not connected")

        end_time = time.time() + timeout if timeout else None

        while self.subscriptions:
            # Check timeout
            if end_time and time.time() > end_time:
                break

            # Check if there's data to read
            if select.select([self.ws.sock], [], [], 0.1)[0]:
                response = self._receive()

                if response.get("type") == "data":
                    sub_id = response.get("id")
                    if sub_id in self.subscriptions:
                        payload = response.get("payload", {})
                        data = payload.get("data")
                        errors = payload.get("errors")
                        self.subscriptions[sub_id](data, errors)

                elif response.get("type") == "error":
                    sub_id = response.get("id")
                    if sub_id in self.subscriptions:
                        self.subscriptions[sub_id](None, [response.get("payload")])

    def _send(self, message: Dict[str, Any]) -> None:
        """Send message over WebSocket."""
        if self.ws:
            self.ws.send(json.dumps(message))

    def _receive(self) -> Dict[str, Any]:
        """Receive message from WebSocket."""
        if self.ws:
            data = self.ws.recv()
            return json.loads(data)
        return {}


class GraphQLTestingSuite:
    """Comprehensive GraphQL testing suite.

    Example:
        suite = GraphQLTestingSuite("http://localhost:4000/graphql")

        # Test a query
        response = suite.execute_query("{ users { id name } }")

        # Analyze complexity
        complexity = suite.analyze_query_complexity(query)

        # Test mutation with variables
        response = suite.execute_mutation(
            "mutation CreateUser($input: UserInput!) { createUser(input: $input) { id } }",
            variables={"input": {"name": "John", "email": "john@example.com"}}
        )
    """

    def __init__(
        self,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 30.0,
    ):
        """Initialize GraphQL testing suite.

        Args:
            endpoint: GraphQL endpoint URL
            headers: Optional headers
            timeout: Request timeout in seconds
        """
        self.endpoint = endpoint
        self.headers = headers or {"Content-Type": "application/json"}
        self.timeout = timeout
        self.schema_analyzer = SchemaAnalyzer()
        self.request_history: List[GraphQLResponse] = []

    def execute_query(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        operation_name: Optional[str] = None,
    ) -> GraphQLResponse:
        """Execute a GraphQL query.

        Args:
            query: GraphQL query string
            variables: Optional variables
            operation_name: Optional operation name

        Returns:
            GraphQLResponse with data and errors
        """
        import requests

        payload = {
            "query": query,
            "variables": variables or {},
            "operationName": operation_name,
        }

        start_time = time.perf_counter()

        try:
            response = requests.post(
                self.endpoint,
                json=payload,
                headers=self.headers,
                timeout=self.timeout,
            )

            duration_ms = (time.perf_counter() - start_time) * 1000
            data = response.json()

            result = GraphQLResponse(
                data=data.get("data"),
                errors=data.get("errors"),
                extensions=data.get("extensions"),
                duration_ms=duration_ms,
            )

            self.request_history.append(result)
            return result

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            return GraphQLResponse(
                data=None,
                errors=[{"message": str(e)}],
                duration_ms=duration_ms,
            )

    def execute_mutation(
        self,
        mutation: str,
        variables: Optional[Dict[str, Any]] = None,
        operation_name: Optional[str] = None,
    ) -> GraphQLResponse:
        """Execute a GraphQL mutation.

        Args:
            mutation: GraphQL mutation string
            variables: Optional variables
            operation_name: Optional operation name

        Returns:
            GraphQLResponse with data and errors
        """
        return self.execute_query(mutation, variables, operation_name)

    def execute_subscription(
        self,
        subscription: str,
        callback: Callable[[Dict[str, Any]], None],
        variables: Optional[Dict[str, Any]] = None,
    ) -> SubscriptionManager:
        """Execute a GraphQL subscription.

        Args:
            subscription: GraphQL subscription string
            callback: Function to call on each event
            variables: Optional variables

        Returns:
            SubscriptionManager instance
        """
        ws_url = self.endpoint.replace("http", "ws")
        manager = SubscriptionManager(ws_url, self.headers)

        if manager.connect():
            manager.subscribe(subscription, callback, variables)
            return manager

        raise RuntimeError("Failed to connect to subscription endpoint")

    def load_schema(self, introspection_query: Optional[str] = None) -> None:
        """Load schema from introspection.

        Args:
            introspection_query: Custom introspection query (optional)
        """
        default_introspection = """
        query IntrospectionQuery {
          __schema {
            queryType { name }
            mutationType { name }
            subscriptionType { name }
            types {
              ...FullType
            }
          }
        }
        fragment FullType on __Type {
          kind
          name
          fields(includeDeprecated: true) {
            name
            args {
              ...InputValue
            }
            type {
              ...TypeRef
            }
            isDeprecated
            deprecationReason
          }
          inputFields {
            ...InputValue
          }
          interfaces {
            ...TypeRef
          }
          enumValues(includeDeprecated: true) {
            name
            isDeprecated
            deprecationReason
          }
          possibleTypes {
            ...TypeRef
          }
        }
        fragment InputValue on __InputValue {
          name
          type {
            ...TypeRef
          }
          defaultValue
        }
        fragment TypeRef on __Type {
          kind
          name
          ofType {
            kind
            name
            ofType {
              kind
              name
              ofType {
                kind
                name
                ofType {
                  kind
                  name
                  ofType {
                    kind
                    name
                    ofType {
                      kind
                      name
                      ofType {
                        kind
                        name
                      }
                    }
                  }
                }
              }
            }
          }
        }
        """

        response = self.execute_query(introspection_query or default_introspection)
        if response.success and response.data:
            self.schema_analyzer.load_from_introspection(response.data)

    def analyze_query_complexity(self, query: str) -> QueryComplexity:
        """Analyze query complexity.

        Args:
            query: GraphQL query

        Returns:
            QueryComplexity analysis
        """
        return self.schema_analyzer.analyze_query_complexity(query)

    def detect_n_plus_one(self, queries: List[str]) -> List[Dict[str, Any]]:
        """Detect potential N+1 query issues.

        Args:
            queries: List of GraphQL queries to analyze

        Returns:
            List of potential N+1 issues
        """
        issues = []

        for query in queries:
            complexity = self.analyze_query_complexity(query)

            # Check for list fields that could cause N+1
            for list_field in complexity.list_fields:
                # Check if the field resolver might cause N+1
                field_type = self.schema_analyzer.get_field(complexity.level)
                if field_type and field_type.fields:
                    issues.append(
                        {
                            "query": query[:100],
                            "list_field": list_field,
                            "severity": "high" if complexity.score > 50 else "medium",
                            "recommendation": f"Consider using DataLoader for {list_field}",
                        }
                    )

        return issues

    def validate_schema(self) -> Dict[str, Any]:
        """Validate the loaded schema.

        Returns:
            Validation results
        """
        issues = []

        # Check for required root types
        if not self.schema_analyzer.query_type:
            issues.append({"type": "missing_root", "field": "query"})

        # Check for deprecated types in use
        for type_name, schema_type in self.schema_analyzer.types.items():
            if schema_type.enum_values:
                for enum_val in schema_type.enum_values:
                    if enum_val.isupper():
                        issues.append(
                            {
                                "type": "naming_convention",
                                "field": f"{type_name}.{enum_val}",
                                "message": "Enum values should use PascalCase",
                            }
                        )

        return {"valid": len(issues) == 0, "issues": issues}


class GraphQLBatchTester:
    """Tests for GraphQL batch operations.

    Example:
        tester = GraphQLBatchTester(endpoint)

        # Test batch mutation
        results = tester.test_batch_mutation(
            "mutation CreateUsers($users: [UserInput!]!) { createUsers(users: $users) { id } }",
            [
                {"name": "User1", "email": "user1@example.com"},
                {"name": "User2", "email": "user2@example.com"},
            ]
        )
    """

    def __init__(self, endpoint: str):
        """Initialize batch tester.

        Args:
            endpoint: GraphQL endpoint
        """
        self.endpoint = endpoint
        self.suite = GraphQLTestingSuite(endpoint)

    def test_batch_mutation(
        self,
        mutation: str,
        items: List[Dict[str, Any]],
    ) -> List[GraphQLResponse]:
        """Test batch mutation with multiple items.

        Args:
            mutation: GraphQL mutation
            items: List of items to process

        Returns:
            List of responses for each item
        """
        responses = []

        for item in items:
            response = self.suite.execute_mutation(
                mutation,
                variables={"users": [item] if "$users" in mutation else item},
            )
            responses.append(response)

        return responses

    def test_batch_mutation_efficiency(
        self,
        mutation: str,
        items: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Test batch mutation efficiency.

        Args:
            mutation: GraphQL mutation
            items: List of items

        Returns:
            Efficiency metrics
        """
        start = time.perf_counter()

        responses = self.test_batch_mutation(mutation, items)

        total_time = time.perf_counter() - start
        success_count = sum(1 for r in responses if r.success)

        return {
            "total_items": len(items),
            "successful": success_count,
            "failed": len(items) - success_count,
            "total_time_ms": total_time * 1000,
            "avg_time_ms": (total_time / len(items)) * 1000 if items else 0,
        }
