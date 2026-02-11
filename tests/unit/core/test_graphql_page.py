"""Tests for GraphQL page support.

This module contains unit tests for the BaseGraphQLPage class,
GraphQLQueryBuilder, and GraphQLIntrospector.
"""

import json
import time
from unittest.mock import Mock, patch

import pytest

from socialseed_e2e.core.base_graphql_page import (
    BaseGraphQLPage,
    GraphQLError,
    GraphQLIntrospector,
    GraphQLQueryBuilder,
    GraphQLRequestLog,
    GraphQLRetryConfig,
    graphql_query,
)

pytestmark = pytest.mark.unit


class MockResponse:
    """Mock Playwright APIResponse for testing."""

    def __init__(
        self, status=200, body=None, headers=None, url="http://test.com/graphql"
    ):
        """Initialize mock response.

        Args:
            status: HTTP status code
            body: Response body
            headers: Response headers
            url: Request URL
        """
        self.status = status
        self._body = json.dumps(body).encode("utf-8") if body else b'{"data": {}}'
        self.headers = headers or {"content-type": "application/json"}
        self.url = url

    def body(self):
        """Return response body as bytes."""
        return self._body

    def text(self):
        """Return response body as string."""
        return self._body.decode("utf-8")

    def json(self):
        """Return response body as parsed JSON."""
        return json.loads(self._body)


class TestGraphQLRetryConfig:
    """Test cases for GraphQLRetryConfig dataclass."""

    def test_default_values(self):
        """Test default retry configuration."""
        config = GraphQLRetryConfig()

        assert config.max_retries == 3
        assert config.backoff_factor == 1.0
        assert config.max_backoff == 60.0
        assert 502 in config.retry_on
        assert 503 in config.retry_on
        assert 429 in config.retry_on

    def test_custom_values(self):
        """Test custom retry configuration."""
        config = GraphQLRetryConfig(
            max_retries=5,
            backoff_factor=2.0,
            max_backoff=120.0,
            retry_on=[500, 502, 503],
        )

        assert config.max_retries == 5
        assert config.backoff_factor == 2.0
        assert config.max_backoff == 120.0
        assert config.retry_on == [500, 502, 503]


class TestGraphQLQueryBuilder:
    """Test cases for GraphQLQueryBuilder."""

    def test_simple_query(self):
        """Test building a simple query."""
        builder = GraphQLQueryBuilder()
        query = (
            builder.query("GetUser")
            .field("user", id="123")
            .fields("name", "email")
            .build()
        )

        assert "query GetUser" in query
        assert 'user(id: "123")' in query
        assert "name" in query
        assert "email" in query

    def test_mutation(self):
        """Test building a mutation."""
        builder = GraphQLQueryBuilder()
        mutation = (
            builder.mutation("CreateUser")
            .field("createUser", user_name="John", email="john@example.com")
            .fields("id", "name")
            .build()
        )

        assert "mutation CreateUser" in mutation
        assert 'createUser(user_name: "John"' in mutation
        assert "id" in mutation
        assert "name" in mutation

    def test_subscription(self):
        """Test building a subscription."""
        builder = GraphQLQueryBuilder()
        subscription = (
            builder.subscription("OnUserCreated")
            .field("userCreated")
            .fields("id", "name")
            .build()
        )

        assert "subscription OnUserCreated" in subscription
        assert "userCreated" in subscription

    def test_variables(self):
        """Test query with variables."""
        builder = GraphQLQueryBuilder()
        query = (
            builder.query("GetUser")
            .variable("id", "ID!")
            .field("user", id="$id")
            .fields("name")
            .build()
        )

        assert "($id: ID!)" in query
        assert "user(id: $id)" in query

    def test_nested_fields(self):
        """Test query with nested fields."""
        builder = GraphQLQueryBuilder()
        query = (
            builder.query("GetUser")
            .field("user", id="123")
            .fields("name")
            .subfield("posts")
            .fields("title", "content")
            .end_field()
            .build()
        )

        assert "user" in query
        assert "posts" in query
        assert "title" in query
        assert "content" in query

    def test_fragments(self):
        """Test query with fragments."""
        builder = GraphQLQueryBuilder()
        query = (
            builder.query("GetUsers")
            .fragment("UserFields", "User", "id", "name", "email")
            .field("users")
            .subfield("...UserFields")
            .end_field()
            .build()
        )

        assert "fragment UserFields on User" in query
        assert "...UserFields" in query

    def test_alias(self):
        """Test field aliasing."""
        builder = GraphQLQueryBuilder()
        query = (
            builder.query("GetUsers")
            .field("users", alias="allUsers")
            .fields("id")
            .build()
        )

        assert "allUsers: users" in query

    def test_directives(self):
        """Test directives."""
        builder = GraphQLQueryBuilder()
        query = (
            builder.query("GetUser")
            .variable("id", "ID!")
            .variable("includeEmail", "Boolean!", False)
            .field("user", id="$id")
            .fields("id", "name")
            .subfield("email")
            .directive("include", **{"if": "$includeEmail"})
            .end_field()
            .build()
        )

        assert "@include" in query

    def test_default_values(self):
        """Test variables with default values."""
        builder = GraphQLQueryBuilder()
        query = (
            builder.query("GetUsers")
            .variable("limit", "Int", 10)
            .field("users", limit="$limit")
            .fields("id")
            .build()
        )

        assert "$limit: Int = 10" in query

    def test_format_value(self):
        """Test value formatting."""
        builder = GraphQLQueryBuilder()

        assert builder._format_value(None) == "null"
        assert builder._format_value(True) == "true"
        assert builder._format_value(False) == "false"
        assert builder._format_value(123) == "123"
        assert builder._format_value(3.14) == "3.14"
        assert builder._format_value("hello") == '"hello"'
        assert builder._format_value([1, 2, 3]) == "[1, 2, 3]"
        assert builder._format_value({"key": "value"}) == '{key: "value"}'


class TestGraphQLRequestLog:
    """Test cases for GraphQLRequestLog dataclass."""

    def test_creation(self):
        """Test log entry creation."""
        log = GraphQLRequestLog(
            operation_type="query",
            operation_name="GetUser",
            query="{ user { id } }",
            variables={"id": "123"},
            timestamp=time.time(),
            duration_ms=100.0,
            status=200,
        )

        assert log.operation_type == "query"
        assert log.operation_name == "GetUser"
        assert log.status == 200


class TestGraphQLError:
    """Test cases for GraphQLError exception."""

    def test_basic_error(self):
        """Test basic error creation."""
        error = GraphQLError("Test error")

        assert str(error) == "Test error"
        assert error.errors == []

    def test_error_with_details(self):
        """Test error with GraphQL details."""
        errors = [{"message": "Field not found"}, {"message": "Invalid argument"}]
        error = GraphQLError(
            "GraphQL errors",
            errors=errors,
            query="{ user { invalidField } }",
            url="http://test.com/graphql",
        )

        assert "GraphQL errors" in str(error)
        assert "http://test.com/graphql" in str(error)
        assert "Field not found" in str(error)

    def test_error_with_many_errors(self):
        """Test error formatting with many errors."""
        errors = [{"message": f"Error {i}"} for i in range(5)]
        error = GraphQLError("Multiple errors", errors=errors)

        # Should show only first 3 errors
        assert "Error 0" in str(error)
        assert "Error 2" in str(error)
        assert "and 2 more errors" in str(error)


class TestGraphQLIntrospector:
    """Test cases for GraphQLIntrospector."""

    @pytest.fixture
    def mock_page(self):
        """Create a mock GraphQL page."""
        return Mock(spec=BaseGraphQLPage)

    @pytest.fixture
    def sample_schema(self):
        """Sample introspection schema for testing."""
        return {
            "queryType": {"name": "Query"},
            "mutationType": {"name": "Mutation"},
            "subscriptionType": None,
            "types": [
                {
                    "kind": "OBJECT",
                    "name": "Query",
                    "fields": [
                        {"name": "user", "type": {"name": "User"}},
                        {"name": "users", "type": {"name": "[User]"}},
                    ],
                },
                {
                    "kind": "OBJECT",
                    "name": "Mutation",
                    "fields": [
                        {"name": "createUser", "type": {"name": "User"}},
                    ],
                },
                {
                    "kind": "OBJECT",
                    "name": "User",
                    "fields": [
                        {"name": "id", "type": {"name": "ID"}},
                        {"name": "name", "type": {"name": "String"}},
                    ],
                },
                {
                    "kind": "ENUM",
                    "name": "Status",
                    "enumValues": [
                        {"name": "ACTIVE"},
                        {"name": "INACTIVE"},
                    ],
                },
            ],
            "directives": [],
        }

    def test_introspect(self, mock_page, sample_schema):
        """Test schema introspection."""
        mock_page.query.return_value = {"data": {"__schema": sample_schema}}

        introspector = GraphQLIntrospector(mock_page)
        schema = introspector.introspect()

        assert schema == sample_schema
        mock_page.query.assert_called_once()

    def test_introspect_with_errors(self, mock_page):
        """Test introspection with errors."""
        mock_page.query.return_value = {
            "data": None,
            "errors": [{"message": "Introspection not allowed"}],
        }

        introspector = GraphQLIntrospector(mock_page)

        with pytest.raises(GraphQLError) as exc_info:
            introspector.introspect()

        assert "Introspection query failed" in str(exc_info.value)

    def test_get_types(self, mock_page, sample_schema):
        """Test getting all types."""
        mock_page.query.return_value = {"data": {"__schema": sample_schema}}

        introspector = GraphQLIntrospector(mock_page)
        types = introspector.get_types()

        assert len(types) == 4
        type_names = [t["name"] for t in types]
        assert "Query" in type_names
        assert "User" in type_names

    def test_get_types_filtered(self, mock_page, sample_schema):
        """Test getting types with kind filter."""
        mock_page.query.return_value = {"data": {"__schema": sample_schema}}

        introspector = GraphQLIntrospector(mock_page)
        types = introspector.get_types(kind="ENUM")

        assert len(types) == 1
        assert types[0]["name"] == "Status"

    def test_get_type(self, mock_page, sample_schema):
        """Test getting a specific type."""
        mock_page.query.return_value = {"data": {"__schema": sample_schema}}

        introspector = GraphQLIntrospector(mock_page)
        user_type = introspector.get_type("User")

        assert user_type is not None
        assert user_type["name"] == "User"
        assert user_type["kind"] == "OBJECT"

    def test_get_type_not_found(self, mock_page, sample_schema):
        """Test getting a non-existent type."""
        mock_page.query.return_value = {"data": {"__schema": sample_schema}}

        introspector = GraphQLIntrospector(mock_page)
        result = introspector.get_type("NonExistent")

        assert result is None

    def test_get_queries(self, mock_page, sample_schema):
        """Test getting available queries."""
        mock_page.query.return_value = {"data": {"__schema": sample_schema}}

        introspector = GraphQLIntrospector(mock_page)
        queries = introspector.get_queries()

        assert len(queries) == 2
        query_names = [q["name"] for q in queries]
        assert "user" in query_names
        assert "users" in query_names

    def test_get_mutations(self, mock_page, sample_schema):
        """Test getting available mutations."""
        mock_page.query.return_value = {"data": {"__schema": sample_schema}}

        introspector = GraphQLIntrospector(mock_page)
        mutations = introspector.get_mutations()

        assert len(mutations) == 1
        assert mutations[0]["name"] == "createUser"

    def test_get_subscriptions_none(self, mock_page, sample_schema):
        """Test getting subscriptions when none exist."""
        mock_page.query.return_value = {"data": {"__schema": sample_schema}}

        introspector = GraphQLIntrospector(mock_page)
        subscriptions = introspector.get_subscriptions()

        assert subscriptions == []

    def test_get_query(self, mock_page, sample_schema):
        """Test getting a specific query."""
        mock_page.query.return_value = {"data": {"__schema": sample_schema}}

        introspector = GraphQLIntrospector(mock_page)
        query = introspector.get_query("user")

        assert query is not None
        assert query["name"] == "user"

    def test_get_enum_values(self, mock_page, sample_schema):
        """Test getting enum values."""
        mock_page.query.return_value = {"data": {"__schema": sample_schema}}

        introspector = GraphQLIntrospector(mock_page)
        values = introspector.get_enum_values("Status")

        assert values == ["ACTIVE", "INACTIVE"]

    def test_clear_cache(self, mock_page, sample_schema):
        """Test clearing the schema cache."""
        mock_page.query.return_value = {"data": {"__schema": sample_schema}}

        introspector = GraphQLIntrospector(mock_page)
        introspector.introspect()

        assert introspector._schema_cache is not None

        introspector.clear_cache()
        assert introspector._schema_cache is None

    def test_cache_reuse(self, mock_page, sample_schema):
        """Test that introspection result is cached."""
        mock_page.query.return_value = {"data": {"__schema": sample_schema}}

        introspector = GraphQLIntrospector(mock_page)
        schema1 = introspector.introspect()
        schema2 = introspector.introspect()

        # Should only call query once
        mock_page.query.assert_called_once()
        assert schema1 == schema2

    def test_force_refresh(self, mock_page, sample_schema):
        """Test force refresh bypasses cache."""
        mock_page.query.return_value = {"data": {"__schema": sample_schema}}

        introspector = GraphQLIntrospector(mock_page)
        introspector.introspect()
        introspector.introspect(force_refresh=True)

        # Should call query twice
        assert mock_page.query.call_count == 2


class TestBaseGraphQLPage:
    """Test cases for BaseGraphQLPage."""

    @pytest.fixture
    def mock_playwright(self):
        """Fixture to mock playwright for initialization tests."""
        with patch("playwright.sync_api.sync_playwright") as mock_playwright:
            mock_instance = Mock()
            mock_playwright.return_value = mock_instance
            mock_instance.__enter__ = Mock(return_value=Mock())
            mock_instance.__exit__ = Mock(return_value=False)
            yield mock_playwright

    @pytest.fixture
    def page(self, mock_playwright):
        """Create a BaseGraphQLPage instance for testing."""
        return BaseGraphQLPage("http://test.com/graphql")

    def test_init_with_endpoint(self, mock_playwright):
        """Test initialization with endpoint."""
        page = BaseGraphQLPage("http://test.com/graphql")

        assert page.endpoint == "http://test.com/graphql"
        assert page.enable_logging is True

    def test_init_with_custom_headers(self, mock_playwright):
        """Test initialization with custom headers."""
        headers = {"Authorization": "Bearer token123"}
        page = BaseGraphQLPage("http://test.com/graphql", headers=headers)

        assert "Authorization" in page.headers
        assert page.headers["Authorization"] == "Bearer token123"

    def test_init_with_retry_config(self, mock_playwright):
        """Test initialization with retry configuration."""
        retry_config = GraphQLRetryConfig(max_retries=5, backoff_factor=2.0)
        page = BaseGraphQLPage("http://test.com/graphql", retry_config=retry_config)

        assert page.retry_config.max_retries == 5
        assert page.retry_config.backoff_factor == 2.0

    def test_builder(self, mock_playwright):
        """Test getting a query builder."""
        page = BaseGraphQLPage("http://test.com/graphql")
        builder = page.builder()

        assert isinstance(builder, GraphQLQueryBuilder)

    def test_introspector(self, mock_playwright):
        """Test getting an introspector."""
        page = BaseGraphQLPage("http://test.com/graphql")
        introspector = page.introspector()

        assert isinstance(introspector, GraphQLIntrospector)
        assert page._introspector is introspector

    def test_introspector_cached(self, mock_playwright):
        """Test that introspector is cached."""
        page = BaseGraphQLPage("http://test.com/graphql")
        introspector1 = page.introspector()
        introspector2 = page.introspector()

        assert introspector1 is introspector2


class TestBaseGraphQLPageRequests:
    """Test cases for BaseGraphQLPage request methods."""

    @pytest.fixture
    def mock_api_context(self):
        """Create a mock API context."""
        return Mock()

    @pytest.fixture
    def page(self, mock_api_context):
        """Create a page with mocked API context."""
        with patch("playwright.sync_api.sync_playwright") as mock_pw:
            mock_instance = Mock()
            mock_pw.return_value = mock_instance
            mock_instance.__enter__ = Mock(
                return_value=Mock(
                    request=Mock(new_context=Mock(return_value=mock_api_context))
                )
            )
            mock_instance.__exit__ = Mock(return_value=False)

            page = BaseGraphQLPage("http://test.com/graphql")
            page.setup()
            return page

    def test_query_success(self, page, mock_api_context):
        """Test successful query execution."""
        mock_api_context.post.return_value = MockResponse(
            status=200,
            body={"data": {"user": {"id": "1", "name": "John"}}},
        )

        result = page.query("{ user { id name } }")

        assert result["data"]["user"]["id"] == "1"
        assert result["data"]["user"]["name"] == "John"
        mock_api_context.post.assert_called_once()

    def test_query_with_variables(self, page, mock_api_context):
        """Test query with variables."""
        mock_api_context.post.return_value = MockResponse(
            status=200,
            body={"data": {"user": {"id": "123", "name": "John"}}},
        )

        result = page.query(
            "query GetUser($id: ID!) { user(id: $id) { name } }",
            variables={"id": "123"},
        )

        assert result["data"]["user"]["name"] == "John"

        # Check the payload sent
        call_args = mock_api_context.post.call_args
        payload = call_args[1]["data"]
        assert payload["variables"] == {"id": "123"}

    def test_query_with_operation_name(self, page, mock_api_context):
        """Test query with operation name."""
        mock_api_context.post.return_value = MockResponse(
            status=200,
            body={"data": {"user": {"name": "John"}}},
        )

        result = page.query(
            "query GetUser { user { name } }",
            operation_name="GetUser",
        )

        call_args = mock_api_context.post.call_args
        payload = call_args[1]["data"]
        assert payload["operationName"] == "GetUser"

    def test_mutation(self, page, mock_api_context):
        """Test mutation execution."""
        mock_api_context.post.return_value = MockResponse(
            status=200,
            body={"data": {"createUser": {"id": "1", "name": "John"}}},
        )

        result = page.mutation(
            'mutation { createUser(name: "John") { id name } }',
        )

        assert result["data"]["createUser"]["id"] == "1"

    def test_execute(self, page, mock_api_context):
        """Test generic execute method."""
        mock_api_context.post.return_value = MockResponse(
            status=200,
            body={"data": {"test": "value"}},
        )

        result = page.execute("{ test }")

        assert result["data"]["test"] == "value"

    def test_query_graphql_errors(self, page, mock_api_context):
        """Test handling of GraphQL errors."""
        mock_api_context.post.return_value = MockResponse(
            status=200,
            body={
                "data": None,
                "errors": [{"message": "Field not found"}],
            },
        )

        with pytest.raises(GraphQLError) as exc_info:
            page.query("{ invalidField }")

        assert "GraphQL operation returned errors" in str(exc_info.value)
        assert exc_info.value.errors == [{"message": "Field not found"}]

    def test_query_http_error(self, page, mock_api_context):
        """Test handling of HTTP errors."""
        mock_api_context.post.return_value = MockResponse(status=500)

        with pytest.raises(GraphQLError) as exc_info:
            page.query("{ user { id } }")

        assert "GraphQL request failed: HTTP 500" in str(exc_info.value)

    def test_query_retry_on_502(self, page, mock_api_context):
        """Test retry on 502 error."""
        # First call returns 502, second succeeds
        mock_api_context.post.side_effect = [
            MockResponse(status=502),
            MockResponse(status=200, body={"data": {"user": {"id": "1"}}}),
        ]

        result = page.query("{ user { id } }")

        assert result["data"]["user"]["id"] == "1"
        assert mock_api_context.post.call_count == 2

    def test_query_retry_exhausted(self, page, mock_api_context):
        """Test retry exhaustion."""
        # All calls return 502
        mock_api_context.post.return_value = MockResponse(status=502)
        page.retry_config.max_retries = 2

        with pytest.raises(GraphQLError) as exc_info:
            page.query("{ user { id } }")

        assert "HTTP 502" in str(exc_info.value)
        assert mock_api_context.post.call_count == 3  # Initial + 2 retries

    def test_query_json_parse_error(self, page, mock_api_context):
        """Test handling of JSON parse errors."""
        response = Mock()
        response.status = 200
        response.json.side_effect = json.JSONDecodeError("test", "invalid", 0)
        mock_api_context.post.return_value = response

        with pytest.raises(GraphQLError) as exc_info:
            page.query("{ user { id } }")

        assert "Failed to parse GraphQL response" in str(exc_info.value)


class TestBaseGraphQLPageAssertions:
    """Test cases for BaseGraphQLPage assertion methods."""

    @pytest.fixture
    def page(self):
        """Create a page with mocked Playwright."""
        with patch("playwright.sync_api.sync_playwright") as mock_pw:
            mock_instance = Mock()
            mock_pw.return_value = mock_instance
            mock_instance.__enter__ = Mock(return_value=Mock())
            mock_instance.__exit__ = Mock(return_value=False)

            page = BaseGraphQLPage("http://test.com/graphql")
            yield page

    def test_assert_no_errors_success(self, page):
        """Test assert_no_errors with no errors."""
        response = {"data": {"user": {"id": "1"}}}

        result = page.assert_no_errors(response)
        assert result == response

    def test_assert_no_errors_failure(self, page):
        """Test assert_no_errors with errors."""
        response = {"data": None, "errors": [{"message": "Error"}]}

        with pytest.raises(GraphQLError) as exc_info:
            page.assert_no_errors(response)

        assert "GraphQL response contains errors" in str(exc_info.value)

    def test_assert_has_data_success(self, page):
        """Test assert_has_data with data present."""
        response = {"data": {"user": {"id": "1"}}}

        result = page.assert_has_data(response)
        assert result == response

    def test_assert_has_data_failure(self, page):
        """Test assert_has_data without data."""
        response = {"errors": [{"message": "Error"}]}

        with pytest.raises(AssertionError) as exc_info:
            page.assert_has_data(response)

        assert "GraphQL response has no data field" in str(exc_info.value)

    def test_get_data_full(self, page):
        """Test get_data returning full data."""
        response = {"data": {"user": {"id": "1", "name": "John"}}}

        data = page.get_data(response)
        assert data == {"user": {"id": "1", "name": "John"}}

    def test_get_data_with_path(self, page):
        """Test get_data with path."""
        response = {"data": {"user": {"id": "1", "name": "John"}}}

        user_id = page.get_data(response, "user.id")
        assert user_id == "1"

        user_name = page.get_data(response, "user.name")
        assert user_name == "John"

    def test_get_data_invalid_path(self, page):
        """Test get_data with invalid path."""
        response = {"data": {"user": {"id": "1"}}}

        result = page.get_data(response, "user.nonexistent")
        assert result is None

    def test_get_data_no_data(self, page):
        """Test get_data when no data exists."""
        response = {}

        data = page.get_data(response)
        assert data is None

    def test_get_errors_with_errors(self, page):
        """Test get_errors when errors exist."""
        response = {"errors": [{"message": "Error 1"}, {"message": "Error 2"}]}

        errors = page.get_errors(response)
        assert len(errors) == 2

    def test_get_errors_no_errors(self, page):
        """Test get_errors when no errors exist."""
        response = {"data": {"user": {"id": "1"}}}

        errors = page.get_errors(response)
        assert errors == []


class TestBaseGraphQLPageLogging:
    """Test cases for BaseGraphQLPage logging."""

    def test_request_logging(self):
        """Test that requests are logged."""
        with patch("playwright.sync_api.sync_playwright") as mock_pw:
            mock_instance = Mock()
            mock_pw.return_value = mock_instance
            mock_instance.__enter__ = Mock(return_value=Mock())
            mock_instance.__exit__ = Mock(return_value=False)

            page = BaseGraphQLPage("http://test.com/graphql", enable_logging=True)

            # Create a mock log entry
            log_entry = GraphQLRequestLog(
                operation_type="query",
                operation_name="GetUser",
                query="{ user { id } }",
                variables=None,
                timestamp=time.time(),
                duration_ms=100.0,
                status=200,
            )

            page._log_request(log_entry)

            assert len(page.request_logs) == 1
            assert page.request_logs[0].operation_name == "GetUser"

    def test_log_size_limit(self):
        """Test that log size is limited."""
        with patch("playwright.sync_api.sync_playwright") as mock_pw:
            mock_instance = Mock()
            mock_pw.return_value = mock_instance
            mock_instance.__enter__ = Mock(return_value=Mock())
            mock_instance.__exit__ = Mock(return_value=False)

            page = BaseGraphQLPage("http://test.com/graphql")
            page._max_log_size = 5

            # Add more than max logs
            for i in range(10):
                log_entry = GraphQLRequestLog(
                    operation_type="query",
                    operation_name=f"Query{i}",
                    query="{ test }",
                    variables=None,
                    timestamp=time.time(),
                )
                page._log_request(log_entry)

            assert len(page.request_logs) == 5
            # Oldest entries should be removed
            assert page.request_logs[0].operation_name == "Query5"

    def test_get_request_logs(self):
        """Test getting request logs."""
        with patch("playwright.sync_api.sync_playwright") as mock_pw:
            mock_instance = Mock()
            mock_pw.return_value = mock_instance
            mock_instance.__enter__ = Mock(return_value=Mock())
            mock_instance.__exit__ = Mock(return_value=False)

            page = BaseGraphQLPage("http://test.com/graphql")

            log_entry = GraphQLRequestLog(
                operation_type="query",
                operation_name="GetUser",
                query="{ user { id } }",
                variables=None,
                timestamp=time.time(),
            )
            page._log_request(log_entry)

            logs = page.get_request_logs()
            assert len(logs) == 1

            # Should return a copy
            logs.clear()
            assert len(page.request_logs) == 1

    def test_clear_logs(self):
        """Test clearing logs."""
        with patch("playwright.sync_api.sync_playwright") as mock_pw:
            mock_instance = Mock()
            mock_pw.return_value = mock_instance
            mock_instance.__enter__ = Mock(return_value=Mock())
            mock_instance.__exit__ = Mock(return_value=False)

            page = BaseGraphQLPage("http://test.com/graphql")

            log_entry = GraphQLRequestLog(
                operation_type="query",
                operation_name="GetUser",
                query="{ user { id } }",
                variables=None,
                timestamp=time.time(),
            )
            page._log_request(log_entry)

            page.clear_logs()
            assert len(page.request_logs) == 0


class TestGraphQLQueryConvenienceFunction:
    """Test cases for the graphql_query convenience function."""

    @patch("socialseed_e2e.core.base_graphql_page.BaseGraphQLPage")
    def test_graphql_query(self, mock_page_class):
        """Test the graphql_query convenience function."""
        mock_page = Mock()
        mock_page_class.return_value = mock_page
        mock_page.query.return_value = {"data": {"user": {"id": "1"}}}

        result = graphql_query(
            "http://test.com/graphql",
            "{ user { id } }",
            variables={"id": "123"},
        )

        assert result == {"data": {"user": {"id": "1"}}}
        mock_page.setup.assert_called_once()
        mock_page.teardown.assert_called_once()
        mock_page.query.assert_called_once_with("{ user { id } }", {"id": "123"})

    @patch("socialseed_e2e.core.base_graphql_page.BaseGraphQLPage")
    def test_graphql_query_with_error(self, mock_page_class):
        """Test graphql_query with error handling."""
        mock_page = Mock()
        mock_page_class.return_value = mock_page
        mock_page.query.side_effect = GraphQLError("Test error")

        with pytest.raises(GraphQLError):
            graphql_query("http://test.com/graphql", "{ test }")

        # Teardown should still be called
        mock_page.teardown.assert_called_once()


class TestBaseGraphQLPageContextManager:
    """Test cases for BaseGraphQLPage context manager."""

    def test_context_manager(self):
        """Test using page as context manager."""
        with patch("playwright.sync_api.sync_playwright") as mock_pw:
            mock_instance = Mock()
            mock_pw.return_value = mock_instance
            mock_instance.__enter__ = Mock(return_value=Mock())
            mock_instance.__exit__ = Mock(return_value=False)

            mock_api_context = Mock()
            mock_instance.__enter__().request.new_context.return_value = (
                mock_api_context
            )

            with BaseGraphQLPage("http://test.com/graphql") as page:
                assert page.api_context is not None

            # After exiting, api_context should be None
            assert page.api_context is None
