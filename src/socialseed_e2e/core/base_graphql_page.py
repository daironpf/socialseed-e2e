"""Base GraphQL page for testing GraphQL APIs.

This module provides a BaseGraphQLPage class for testing GraphQL services,
offering a similar interface to BasePage but adapted for GraphQL protocol.
It includes query building, introspection support, and convenient methods
for common GraphQL operations.
"""

import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from playwright.sync_api import APIRequestContext, Playwright

from socialseed_e2e.core.headers import DEFAULT_BROWSER_HEADERS, DEFAULT_JSON_HEADERS
from socialseed_e2e.utils.state_management import DynamicStateMixin

logger = logging.getLogger(__name__)

# GraphQL support is always available (no optional dependencies)
GRAPHQL_AVAILABLE = True


@dataclass
class GraphQLRetryConfig:
    """Configuration for GraphQL retry mechanism.

    Attributes:
        max_retries: Maximum number of retry attempts (default: 3)
        backoff_factor: Exponential backoff multiplier (default: 1.0)
        max_backoff: Maximum backoff time in seconds (default: 60)
        retry_on: List of HTTP status codes to retry on (default: [502, 503, 504, 429])
    """

    max_retries: int = 3
    backoff_factor: float = 1.0
    max_backoff: float = 60.0
    retry_on: Optional[List[int]] = None

    def __post_init__(self):
        """Initialize default retry configuration values."""
        if self.retry_on is None:
            self.retry_on = [502, 503, 504, 429]


@dataclass
class GraphQLRequestLog:
    """Log entry for a single GraphQL request.

    Attributes:
        operation_type: Type of operation (query, mutation, subscription)
        operation_name: Name of the operation (if provided)
        query: The GraphQL query/mutation string
        variables: Variables passed to the operation
        timestamp: When the request was made
        duration_ms: Request duration in milliseconds
        status: HTTP status code
        response_data: Response data (if successful)
        errors: GraphQL errors (if any)
    """

    operation_type: str
    operation_name: Optional[str]
    query: str
    variables: Optional[Dict[str, Any]]
    timestamp: float
    duration_ms: float = 0.0
    status: Optional[int] = None
    response_data: Optional[Dict[str, Any]] = None
    errors: Optional[List[Dict[str, Any]]] = None


class GraphQLError(Exception):
    """Exception for GraphQL errors."""

    def __init__(
        self,
        message: str,
        errors: Optional[List[Dict[str, Any]]] = None,
        query: Optional[str] = None,
        url: Optional[str] = None,
    ):
        """Initialize exception with GraphQL error details.

        Args:
            message: Error message
            errors: List of GraphQL errors from the response
            query: The GraphQL query that caused the error
            url: The URL of the GraphQL endpoint
        """
        super().__init__(message)
        self.errors = errors or []
        self.query = query
        self.url = url

    def __str__(self) -> str:
        """Return formatted error message with context."""
        parts = [super().__str__()]
        if self.url:
            parts.append(f"URL: {self.url}")
        if self.query:
            query_preview = self.query[:200] + "..." if len(self.query) > 200 else self.query
            parts.append(f"Query: {query_preview}")
        if self.errors:
            parts.append(f"GraphQL Errors: {len(self.errors)}")
            for i, error in enumerate(self.errors[:3]):  # Show first 3 errors
                parts.append(f"  {i + 1}. {error.get('message', 'Unknown error')}")
            if len(self.errors) > 3:
                parts.append(f"  ... and {len(self.errors) - 3} more errors")
        return "\n  ".join(parts)


class GraphQLQueryBuilder:
    """Builder for constructing GraphQL queries and mutations.

    This class provides a fluent interface for building GraphQL queries
    with proper formatting and argument handling.

    Example:
        >>> builder = GraphQLQueryBuilder()
        >>> query = builder.query("GetUser")\
        ...     .field("user", id="123")\
        ...     .fields("name", "email", "posts")\
        ...     .field("posts")\
        ...     .fields("title", "content")\
        ...     .build()
        >>> print(query)
        query GetUser {
          user(id: "123") {
            name
            email
            posts {
              title
              content
            }
          }
        }
    """

    def __init__(self, operation_type: str = "query"):
        """Initialize the query builder.

        Args:
            operation_type: Type of operation (query, mutation, subscription)
        """
        self._operation_type = operation_type
        self._operation_name: Optional[str] = None
        self._fields: List[Union[str, Dict[str, Any]]] = []
        self._fragments: Dict[str, str] = {}
        self._variables: Dict[str, Dict[str, Any]] = {}  # name -> {type, value}
        self._directives: List[str] = []
        self._current_field: Optional[Dict[str, Any]] = None

    def query(self, name: Optional[str] = None) -> "GraphQLQueryBuilder":
        """Start building a query.

        Args:
            name: Optional operation name

        Returns:
            Self for method chaining
        """
        self._operation_type = "query"
        self._operation_name = name
        return self

    def mutation(self, name: Optional[str] = None) -> "GraphQLQueryBuilder":
        """Start building a mutation.

        Args:
            name: Optional operation name

        Returns:
            Self for method chaining
        """
        self._operation_type = "mutation"
        self._operation_name = name
        return self

    def subscription(self, name: Optional[str] = None) -> "GraphQLQueryBuilder":
        """Start building a subscription.

        Args:
            name: Optional operation name

        Returns:
            Self for method chaining
        """
        self._operation_type = "subscription"
        self._operation_name = name
        return self

    def field(
        self,
        field_name: str,
        alias: Optional[str] = None,
        **arguments: Any,
    ) -> "GraphQLQueryBuilder":
        """Add a field to the query.

        Args:
            field_name: Field name
            alias: Optional field alias
            **arguments: Field arguments

        Returns:
            Self for method chaining
        """
        field_def = {
            "name": field_name,
            "alias": alias,
            "args": arguments,
            "fields": [],
        }
        self._fields.append(field_def)
        self._current_field = field_def
        return self

    def fields(self, *names: str) -> "GraphQLQueryBuilder":
        """Add scalar fields to the current field or root.

        Args:
            *names: Field names to add

        Returns:
            Self for method chaining
        """
        target = self._current_field if self._current_field else self
        if isinstance(target, dict):
            target["fields"].extend(names)
        else:
            self._fields.extend(names)
        return self

    def subfield(
        self,
        name: str,
        alias: Optional[str] = None,
        **arguments: Any,
    ) -> "GraphQLQueryBuilder":
        """Add a subfield to the current field.

        Args:
            name: Subfield name
            alias: Optional alias
            **arguments: Subfield arguments

        Returns:
            Self for method chaining
        """
        if not self._current_field:
            raise ValueError("No parent field selected. Call field() first.")

        subfield_def = {"name": name, "alias": alias, "args": arguments, "fields": []}
        self._current_field["fields"].append(subfield_def)
        return self

    def subfields(self, *names: str) -> "GraphQLQueryBuilder":
        """Add scalar subfields to the current field.

        Args:
            *names: Field names to add

        Returns:
            Self for method chaining
        """
        if not self._current_field:
            raise ValueError("No parent field selected. Call field() first.")

        self._current_field["fields"].extend(names)
        return self

    def end_field(self) -> "GraphQLQueryBuilder":
        """End the current field and return to root level.

        Returns:
            Self for method chaining
        """
        self._current_field = None
        return self

    def variable(self, name: str, var_type: str, default: Any = None) -> "GraphQLQueryBuilder":
        """Declare a variable for the operation.

        Args:
            name: Variable name (without $)
            var_type: GraphQL type (e.g., "ID!", "String", "Int")
            default: Optional default value

        Returns:
            Self for method chaining
        """
        self._variables[name] = {"type": var_type, "default": default}
        return self

    def directive(self, name: str, **arguments: Any) -> "GraphQLQueryBuilder":
        """Add a directive to the current field.

        Args:
            name: Directive name (e.g., "include", "skip")
            **arguments: Directive arguments

        Returns:
            Self for method chaining
        """
        directive_str = f"@{name}"
        if arguments:
            args_str = ", ".join(f"{k}: {self._format_value(v)}" for k, v in arguments.items())
            directive_str += f"({args_str})"
        self._directives.append(directive_str)
        return self

    def fragment(self, name: str, on_type: str, *fields: str) -> "GraphQLQueryBuilder":
        """Define a fragment.

        Args:
            name: Fragment name
            on_type: Type the fragment applies to
            *fields: Fields in the fragment

        Returns:
            Self for method chaining
        """
        fields_str = "\n    ".join(fields)
        self._fragments[name] = f"fragment {name} on {on_type} {{\n    {fields_str}\n  }}"
        return self

    def _format_value(self, value: Any) -> str:
        """Format a value for GraphQL syntax.

        Args:
            value: Value to format

        Returns:
            GraphQL-formatted value string
        """
        if value is None:
            return "null"
        elif isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, str):
            return json.dumps(value)
        elif isinstance(value, list):
            items = ", ".join(self._format_value(item) for item in value)
            return f"[{items}]"
        elif isinstance(value, dict):
            pairs = ", ".join(f"{k}: {self._format_value(v)}" for k, v in value.items())
            return f"{{{pairs}}}"
        else:
            return json.dumps(str(value))

    def _format_arguments(self, args: Dict[str, Any]) -> str:
        """Format arguments for a field.

        Args:
            args: Arguments dictionary

        Returns:
            Formatted arguments string
        """
        if not args:
            return ""

        formatted = []
        for key, value in args.items():
            # Check if value is a variable reference
            if isinstance(value, str) and value.startswith("$"):
                formatted.append(f"{key}: {value}")
            else:
                formatted.append(f"{key}: {self._format_value(value)}")

        return f"({', '.join(formatted)})"

    def _build_field(self, field_def: Union[str, Dict[str, Any]], indent: int = 2) -> str:
        """Build a field string from its definition.

        Args:
            field_def: Field definition (string or dict)
            indent: Indentation level

        Returns:
            GraphQL field string
        """
        if isinstance(field_def, str):
            return " " * indent + field_def

        name = field_def["name"]
        alias = field_def.get("alias")
        args = self._format_arguments(field_def.get("args", {}))
        subfields = field_def.get("fields", [])

        field_str = " " * indent
        if alias:
            field_str += f"{alias}: "
        field_str += f"{name}{args}"

        if subfields:
            subfield_strs = [self._build_field(sf, indent + 2) for sf in subfields]
            if any(isinstance(sf, str) and not isinstance(sf, dict) for sf in subfields):
                # Mixed scalar and complex subfields
                field_str += " {\n" + "\n".join(subfield_strs) + "\n" + " " * indent + "}"
            else:
                field_str += " {\n" + "\n".join(subfield_strs) + "\n" + " " * indent + "}"

        return field_str

    def build(self) -> str:
        """Build the GraphQL query string.

        Returns:
            Complete GraphQL query string
        """
        lines = []

        # Add fragment definitions
        for fragment in self._fragments.values():
            lines.append(fragment)

        if self._fragments:
            lines.append("")

        # Build operation signature
        op_parts = [self._operation_type]
        if self._operation_name:
            op_parts.append(self._operation_name)

        # Add variable definitions
        if self._variables:
            var_defs = []
            for name, spec in self._variables.items():
                var_def = f"${name}: {spec['type']}"
                if spec.get("default") is not None:
                    var_def += f" = {self._format_value(spec['default'])}"
                var_defs.append(var_def)
            op_parts.append(f"({', '.join(var_defs)})")

        # Add directives
        if self._directives:
            op_parts.extend(self._directives)

        # Build field selections
        field_strs = [self._build_field(f) for f in self._fields]

        # Combine everything
        operation = " ".join(op_parts) + " {\n" + "\n".join(field_strs) + "\n}"
        lines.append(operation)

        return "\n".join(lines)

    def __str__(self) -> str:
        """Return the built query string."""
        return self.build()


class GraphQLIntrospector:
    """Introspection utility for GraphQL schemas.

    This class provides methods to introspect a GraphQL API and
    retrieve information about its schema, types, queries, and mutations.

    Example:
        >>> page = BaseGraphQLPage("https://api.example.com/graphql")
        >>> page.setup()
        >>> introspector = GraphQLIntrospector(page)
        >>>
        >>> # Get full schema
        >>> schema = introspector.introspect()
        >>>
        >>> # Get available queries
        >>> queries = introspector.get_queries()
        >>>
        >>> # Get type information
        >>> user_type = introspector.get_type("User")
    """

    # Introspection query for full schema
    FULL_SCHEMA_QUERY = """
    query IntrospectionQuery {
      __schema {
        queryType { name }
        mutationType { name }
        subscriptionType { name }
        types {
          ...FullType
        }
        directives {
          name
          description
          locations
          args {
            ...InputValue
          }
        }
      }
    }

    fragment FullType on __Type {
      kind
      name
      description
      fields(includeDeprecated: true) {
        name
        description
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
        description
        isDeprecated
        deprecationReason
      }
      possibleTypes {
        ...TypeRef
      }
    }

    fragment InputValue on __InputValue {
      name
      description
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

    def __init__(self, page: "BaseGraphQLPage"):
        """Initialize the introspector.

        Args:
            page: BaseGraphQLPage instance to use for requests
        """
        self._page = page
        self._schema_cache: Optional[Dict[str, Any]] = None

    def introspect(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get the full GraphQL schema through introspection.

        Args:
            force_refresh: Whether to bypass cache and fetch fresh data

        Returns:
            Full introspection result containing the schema
        """
        if self._schema_cache is not None and not force_refresh:
            return self._schema_cache

        response = self._page.query(self.FULL_SCHEMA_QUERY)

        if response.get("errors"):
            raise GraphQLError(
                "Introspection query failed",
                errors=response.get("errors"),
            )

        schema = response.get("data", {}).get("__schema", {})
        self._schema_cache = schema
        return schema

    def get_types(self, kind: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all types from the schema.

        Args:
            kind: Filter by type kind (e.g., "OBJECT", "SCALAR", "ENUM")

        Returns:
            List of type definitions
        """
        schema = self.introspect()
        types = schema.get("types", [])

        if kind:
            types = [t for t in types if t.get("kind") == kind]

        return types

    def get_type(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific type by name.

        Args:
            name: Type name

        Returns:
            Type definition or None if not found
        """
        types = self.get_types()
        for t in types:
            if t.get("name") == name:
                return t
        return None

    def get_queries(self) -> List[Dict[str, Any]]:
        """Get all available query fields.

        Returns:
            List of query field definitions
        """
        schema = self.introspect()
        query_type_name = schema.get("queryType", {}).get("name")

        if not query_type_name:
            return []

        query_type = self.get_type(query_type_name)
        return query_type.get("fields", []) if query_type else []

    def get_mutations(self) -> List[Dict[str, Any]]:
        """Get all available mutation fields.

        Returns:
            List of mutation field definitions
        """
        schema = self.introspect()
        mutation_type_name = schema.get("mutationType", {}).get("name")

        if not mutation_type_name:
            return []

        mutation_type = self.get_type(mutation_type_name)
        return mutation_type.get("fields", []) if mutation_type else []

    def get_subscriptions(self) -> List[Dict[str, Any]]:
        """Get all available subscription fields.

        Returns:
            List of subscription field definitions
        """
        schema = self.introspect()
        subscription_type = schema.get("subscriptionType")

        if subscription_type is None:
            return []

        subscription_type_name = subscription_type.get("name")
        if not subscription_type_name:
            return []

        subscription_type_info = self.get_type(subscription_type_name)
        return subscription_type_info.get("fields", []) if subscription_type_info else []

    def get_query(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific query field by name.

        Args:
            name: Query name

        Returns:
            Query field definition or None
        """
        queries = self.get_queries()
        for q in queries:
            if q.get("name") == name:
                return q
        return None

    def get_mutation(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific mutation field by name.

        Args:
            name: Mutation name

        Returns:
            Mutation field definition or None
        """
        mutations = self.get_mutations()
        for m in mutations:
            if m.get("name") == name:
                return m
        return None

    def get_enum_values(self, enum_name: str) -> List[str]:
        """Get all values for an enum type.

        Args:
            enum_name: Name of the enum type

        Returns:
            List of enum value names
        """
        enum_type = self.get_type(enum_name)
        if not enum_type or enum_type.get("kind") != "ENUM":
            return []

        values = enum_type.get("enumValues", [])
        return [v.get("name") for v in values]

    def clear_cache(self) -> None:
        """Clear the schema cache."""
        self._schema_cache = None


class BaseGraphQLPage(DynamicStateMixin):
    """Base page for testing GraphQL APIs.

    This class provides a foundation for creating GraphQL service pages,
    with support for query building, introspection, and convenient
    methods for common GraphQL operations.

    Example:
        >>> page = BaseGraphQLPage("https://api.example.com/graphql")
        >>> page.setup()
        >>>
        >>> # Simple query
        >>> result = page.query("{ users { id name } }")
        >>>
        >>> # Query with variables
        >>> result = page.query(
        ...     "query GetUser($id: ID!) { user(id: $id) { name } }",
        ...     variables={"id": "123"}
        ... )
        >>>
        >>> # Using the query builder
        >>> builder = page.builder()
        >>> query = builder.query("GetUser").field("user", id="123").fields("name", "email").build()
        >>> result = page.query(query)
        >>>
        >>> page.teardown()

    Attributes:
        endpoint: The GraphQL endpoint URL
        headers: Default headers for all requests
        retry_config: Configuration for automatic retries
        request_logs: List of GraphQL request logs
    """

    def __init__(
        self,
        endpoint: str,
        playwright: Optional[Playwright] = None,
        headers: Optional[Dict[str, str]] = None,
        retry_config: Optional[GraphQLRetryConfig] = None,
        enable_logging: bool = True,
    ):
        """Initialize the GraphQL page.

        Args:
            endpoint: GraphQL endpoint URL
            playwright: Optional Playwright instance (created if not provided)
            headers: Default headers for all requests
            retry_config: Configuration for automatic retries
            enable_logging: Whether to log requests and responses
        """
        self.endpoint = endpoint
        self.headers = {
            **DEFAULT_JSON_HEADERS,
            **DEFAULT_BROWSER_HEADERS,
            "Accept": "application/json",
            **(headers or {}),
        }
        self.retry_config = retry_config or GraphQLRetryConfig()
        self.enable_logging = enable_logging

        # Initialize Playwright
        self.playwright_manager: Optional[Any] = None
        self.playwright: Optional[Playwright] = None

        if playwright:
            self.playwright = playwright
        else:
            self.playwright_manager = __import__("playwright").sync_api.sync_playwright()
            self.playwright = self.playwright_manager.__enter__()

        self.api_context: Optional[APIRequestContext] = None
        self.request_logs: List[GraphQLRequestLog] = []
        self._max_log_size = 100

        # Initialize introspector
        self._introspector: Optional[GraphQLIntrospector] = None

        # Initialize state management
        self.init_dynamic_state()

        logger.info(f"BaseGraphQLPage initialized for {self.endpoint}")

    def setup(self) -> "BaseGraphQLPage":
        """Set up the API context.

        Returns:
            Self for method chaining
        """
        if not self.api_context:
            assert self.playwright is not None
            self.api_context = self.playwright.request.new_context()
            logger.debug("GraphQL API context initialized")
        return self

    def teardown(self) -> None:
        """Clean up resources."""
        if self.api_context:
            self.api_context.dispose()
            self.api_context = None
            logger.debug("GraphQL API context disposed")

        if self.playwright_manager:
            self.playwright_manager.__exit__(None, None, None)
            self.playwright_manager = None
            self.playwright = None
            logger.debug("Playwright manager cleaned up")

        logger.info("BaseGraphQLPage teardown complete")

    def _ensure_setup(self) -> None:
        """Ensure API context is set up."""
        if not self.api_context:
            self.setup()

    def builder(self) -> GraphQLQueryBuilder:
        """Get a new query builder instance.

        Returns:
            GraphQLQueryBuilder instance
        """
        return GraphQLQueryBuilder()

    def introspector(self) -> GraphQLIntrospector:
        """Get the introspector instance.

        Returns:
            GraphQLIntrospector instance
        """
        if self._introspector is None:
            self._introspector = GraphQLIntrospector(self)
        return self._introspector

    def _execute(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        operation_name: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Execute a GraphQL operation with retry logic.

        Args:
            query: GraphQL query/mutation string
            variables: Optional variables
            operation_name: Optional operation name
            headers: Optional request-specific headers

        Returns:
            Parsed JSON response

        Raises:
            GraphQLError: If the request fails or GraphQL returns errors
        """
        self._ensure_setup()
        assert self.api_context is not None

        # Prepare request payload
        payload: Dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = variables
        if operation_name:
            payload["operationName"] = operation_name

        # Prepare headers
        request_headers = self.headers.copy()
        if headers:
            request_headers.update(headers)

        # Determine operation type for logging
        operation_type = "query"
        if query.strip().startswith("mutation"):
            operation_type = "mutation"
        elif query.strip().startswith("subscription"):
            operation_type = "subscription"

        # Initialize log entry
        log_entry = GraphQLRequestLog(
            operation_type=operation_type,
            operation_name=operation_name,
            query=query,
            variables=variables,
            timestamp=time.time(),
        )

        for attempt in range(self.retry_config.max_retries + 1):
            start_time = time.time()

            try:
                response = self.api_context.post(
                    self.endpoint,
                    data=payload,
                    headers=request_headers,
                )

                log_entry.duration_ms = (time.time() - start_time) * 1000
                log_entry.status = response.status

                # Check HTTP status
                if response.status >= 400:
                    log_entry.errors = [{"message": f"HTTP {response.status}"}]
                    self._log_request(log_entry)

                    if attempt < self.retry_config.max_retries:
                        retry_codes = self.retry_config.retry_on or []
                        if response.status in retry_codes:
                            backoff = min(
                                self.retry_config.backoff_factor * (2**attempt),
                                self.retry_config.max_backoff,
                            )
                            logger.warning(
                                f"GraphQL request failed with HTTP {response.status}, "
                                f"retrying {attempt + 1}/{self.retry_config.max_retries} "
                                f"after {backoff:.1f}s"
                            )
                            time.sleep(backoff)
                            continue

                    raise GraphQLError(
                        f"GraphQL request failed: HTTP {response.status}",
                        query=query,
                        url=self.endpoint,
                    )

                # Parse response
                try:
                    result = response.json()
                except Exception as e:
                    raise GraphQLError(
                        f"Failed to parse GraphQL response: {e}",
                        query=query,
                        url=self.endpoint,
                    ) from e

                log_entry.response_data = result.get("data")
                log_entry.errors = result.get("errors")
                self._log_request(log_entry)

                # Check for GraphQL errors
                if result.get("errors"):
                    raise GraphQLError(
                        "GraphQL operation returned errors",
                        errors=result.get("errors"),
                        query=query,
                        url=self.endpoint,
                    )

                return result

            except GraphQLError:
                raise

            except Exception as e:
                log_entry.errors = [{"message": str(e)}]

                if attempt < self.retry_config.max_retries:
                    backoff = min(
                        self.retry_config.backoff_factor * (2**attempt),
                        self.retry_config.max_backoff,
                    )
                    logger.warning(
                        f"GraphQL request failed: {e}, "
                        f"retrying {attempt + 1}/{self.retry_config.max_retries} "
                        f"after {backoff:.1f}s"
                    )
                    time.sleep(backoff)
                else:
                    self._log_request(log_entry)
                    raise GraphQLError(
                        f"GraphQL request failed after "
                        f"{self.retry_config.max_retries + 1} attempts: {e}",
                        query=query,
                        url=self.endpoint,
                    ) from e

        # Should not reach here
        self._log_request(log_entry)
        raise GraphQLError(
            "GraphQL request failed",
            query=query,
            url=self.endpoint,
        )

    def _log_request(self, log_entry: GraphQLRequestLog) -> None:
        """Add a request to the log.

        Args:
            log_entry: Request log entry
        """
        self.request_logs.append(log_entry)

        if len(self.request_logs) > self._max_log_size:
            self.request_logs.pop(0)

        if self.enable_logging:
            if log_entry.errors:
                logger.error(
                    f"GraphQL {log_entry.operation_type} failed - "
                    f"{len(log_entry.errors)} error(s) "
                    f"({log_entry.duration_ms:.0f}ms)"
                )
            else:
                logger.info(
                    f"GraphQL {log_entry.operation_type} succeeded "
                    f"({log_entry.duration_ms:.0f}ms)"
                )

    def query(
        self,
        query_string: str,
        variables: Optional[Dict[str, Any]] = None,
        operation_name: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Execute a GraphQL query.

        Args:
            query_string: GraphQL query string
            variables: Optional variables
            operation_name: Optional operation name
            headers: Optional request-specific headers

        Returns:
            Full GraphQL response dictionary
        """
        return self._execute(query_string, variables, operation_name, headers)

    def mutation(
        self,
        mutation_string: str,
        variables: Optional[Dict[str, Any]] = None,
        operation_name: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Execute a GraphQL mutation.

        Args:
            mutation_string: GraphQL mutation string
            variables: Optional variables
            operation_name: Optional operation name
            headers: Optional request-specific headers

        Returns:
            Full GraphQL response dictionary
        """
        return self._execute(mutation_string, variables, operation_name, headers)

    def execute(
        self,
        operation: str,
        variables: Optional[Dict[str, Any]] = None,
        operation_name: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Execute a GraphQL operation (query or mutation).

        Args:
            operation: GraphQL operation string
            variables: Optional variables
            operation_name: Optional operation name
            headers: Optional request-specific headers

        Returns:
            Full GraphQL response dictionary
        """
        return self._execute(operation, variables, operation_name, headers)

    def assert_no_errors(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Assert that a GraphQL response has no errors.

        Args:
            response: GraphQL response dictionary

        Returns:
            The response (for chaining)

        Raises:
            GraphQLError: If the response contains errors
        """
        if response.get("errors"):
            raise GraphQLError(
                "GraphQL response contains errors",
                errors=response.get("errors"),
            )
        return response

    def assert_has_data(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Assert that a GraphQL response has data.

        Args:
            response: GraphQL response dictionary

        Returns:
            The response (for chaining)

        Raises:
            AssertionError: If the response has no data
        """
        if "data" not in response:
            raise AssertionError("GraphQL response has no data field")
        return response

    def get_data(self, response: Dict[str, Any], path: Optional[str] = None) -> Any:
        """Extract data from a GraphQL response.

        Args:
            response: GraphQL response dictionary
            path: Optional dot-separated path to extract (e.g., "user.name")

        Returns:
            Data at the specified path or all data
        """
        data = response.get("data")

        if path and data:
            keys = path.split(".")
            value = data
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return None
            return value

        return data

    def get_errors(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get errors from a GraphQL response.

        Args:
            response: GraphQL response dictionary

        Returns:
            List of GraphQL errors (empty if no errors)
        """
        return response.get("errors", [])

    def get_request_logs(self) -> List[GraphQLRequestLog]:
        """Get all request logs.

        Returns:
            List of request log entries
        """
        return self.request_logs.copy()

    def clear_logs(self) -> None:
        """Clear all request logs."""
        self.request_logs.clear()

    def __enter__(self) -> "BaseGraphQLPage":
        """Context manager entry."""
        self.setup()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.teardown()


# Convenience function for quick queries
def graphql_query(
    endpoint: str,
    query: str,
    variables: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Execute a GraphQL query without creating a persistent page.

    This is a convenience function for simple, one-off GraphQL queries.

    Args:
        endpoint: GraphQL endpoint URL
        query: GraphQL query string
        variables: Optional variables
        headers: Optional headers

    Returns:
        GraphQL response dictionary

    Example:
        >>> result = graphql_query(
        ...     "https://api.example.com/graphql",
        ...     "{ users { id name } }"
        ... )
        >>> print(result["data"]["users"])
    """
    page = BaseGraphQLPage(endpoint, headers=headers)
    try:
        page.setup()
        return page.query(query, variables)
    finally:
        page.teardown()
