"""Tests for Contract Testing Module.

This module tests the enhanced contract testing features including
Pact Broker integration, migration analysis, and multi-protocol support.
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from socialseed_e2e.contract_testing import (
    ConsumerContract,
    ContractChange,
    ContractMigrationAnalyzer,
    ChangeSeverity,
    ChangeType,
    DeprecationNotice,
    FieldDefinition,
    GRPCMethod,
    GraphQLContractBuilder,
    GraphQLOperation,
    GRPCContractBuilder,
    LocalContractRegistry,
    MigrationAnalysisResult,
    MigrationPath,
    MultiProtocolContractBuilder,
    ProtocolType,
    ProviderVerifier,
    RESTContractBuilder,
    RESTEndpoint,
)


# Check if Pact Broker is available
try:
    from socialseed_e2e.contract_testing import (
        PactBrokerClient,
        PactBrokerConfig,
        CompatibilityResult,
        VerificationResult,
    )

    _PACT_BROKER_AVAILABLE = True
except ImportError:
    _PACT_BROKER_AVAILABLE = False


class TestConsumerContract:
    """Tests for ConsumerContract."""

    def test_create_contract(self):
        """Test creating a consumer contract."""
        contract = ConsumerContract("order-service", "payment-service")

        assert contract.contract.consumer == "order-service"
        assert contract.contract.provider == "payment-service"
        assert len(contract.contract.interactions) == 0

    def test_add_interaction(self):
        """Test adding an interaction to contract."""
        contract = ConsumerContract("order-service", "payment-service")

        contract.given("order exists").upon_receiving("process payment").with_request(
            "POST",
            "/payments",
            headers={"Content-Type": "application/json"},
            body={"order_id": "123"},
        ).will_respond_with(201, body={"payment_id": "pay_456"})

        assert len(contract.contract.interactions) == 1
        interaction = contract.contract.interactions[0]
        assert interaction.description == "process payment"
        assert interaction.provider_state == "order exists"
        assert interaction.request["method"] == "POST"
        assert interaction.request["path"] == "/payments"
        assert interaction.response["status"] == 201

    def test_contract_to_json(self):
        """Test exporting contract to JSON."""
        contract = ConsumerContract("order-service", "payment-service")
        contract.given("state").upon_receiving("desc").with_request(
            "GET", "/test"
        ).will_respond_with(200)

        json_str = contract.to_json()
        data = json.loads(json_str)

        assert data["consumer"] == "order-service"
        assert data["provider"] == "payment-service"
        assert len(data["interactions"]) == 1

    def test_save_contract(self, tmp_path):
        """Test saving contract to file."""
        contract = ConsumerContract("order-service", "payment-service")
        contract.given("state").upon_receiving("desc").with_request(
            "GET", "/test"
        ).will_respond_with(200)

        contract.save(str(tmp_path))

        expected_file = tmp_path / "order-service-payment-service.json"
        assert expected_file.exists()

        data = json.loads(expected_file.read_text())
        assert data["consumer"] == "order-service"


class TestLocalContractRegistry:
    """Tests for LocalContractRegistry."""

    def test_publish_contract(self, tmp_path):
        """Test publishing contract to registry."""
        registry = LocalContractRegistry(str(tmp_path))

        contract_json = json.dumps({"consumer": "order", "provider": "payment"})
        registry.publish(contract_json, "order", "payment", "1.0.0")

        # Check file was created
        contract_file = tmp_path / "payment" / "order" / "1.0.0.json"
        assert contract_file.exists()

    def test_get_contract(self, tmp_path):
        """Test retrieving contract from registry."""
        registry = LocalContractRegistry(str(tmp_path))

        contract_json = json.dumps({"test": "data"})
        registry.publish(contract_json, "consumer", "provider", "1.0.0")

        retrieved = registry.get_contract("consumer", "provider", "1.0.0")
        assert retrieved is not None
        assert json.loads(retrieved)["test"] == "data"

    def test_get_nonexistent_contract(self, tmp_path):
        """Test retrieving non-existent contract."""
        registry = LocalContractRegistry(str(tmp_path))

        result = registry.get_contract("none", "none", "1.0.0")
        assert result is None

    def test_detect_breaking_changes_endpoint_removed(self, tmp_path):
        """Test detecting breaking change when endpoint removed."""
        registry = LocalContractRegistry(str(tmp_path))

        old_contract = json.dumps(
            {
                "consumer": "order",
                "provider": "payment",
                "interactions": [
                    {
                        "description": "old endpoint",
                        "request": {"method": "GET", "path": "/old"},
                        "response": {"status": 200},
                    }
                ],
            }
        )

        new_contract = json.dumps(
            {"consumer": "order", "provider": "payment", "interactions": []}
        )

        registry.publish(old_contract, "order", "payment", "latest")

        changes = registry.detect_breaking_changes(new_contract, "order", "payment")
        assert len(changes) == 1
        assert "old endpoint" in changes[0]

    def test_detect_breaking_changes_status_changed(self, tmp_path):
        """Test detecting breaking change when status code changes."""
        registry = LocalContractRegistry(str(tmp_path))

        old_contract = json.dumps(
            {
                "consumer": "order",
                "provider": "payment",
                "interactions": [
                    {
                        "description": "test endpoint",
                        "request": {"method": "GET", "path": "/test"},
                        "response": {"status": 200},
                    }
                ],
            }
        )

        new_contract = json.dumps(
            {
                "consumer": "order",
                "provider": "payment",
                "interactions": [
                    {
                        "description": "test endpoint",
                        "request": {"method": "GET", "path": "/test"},
                        "response": {"status": 201},
                    }
                ],
            }
        )

        registry.publish(old_contract, "order", "payment", "latest")

        changes = registry.detect_breaking_changes(new_contract, "order", "payment")
        assert len(changes) == 1
        assert "200" in changes[0]
        assert "201" in changes[0]


class TestContractMigrationAnalyzer:
    """Tests for ContractMigrationAnalyzer."""

    def test_analyze_no_changes(self):
        """Test analysis with identical contracts."""
        analyzer = ContractMigrationAnalyzer()

        contract = {
            "consumer": "order",
            "provider": "payment",
            "interactions": [
                {
                    "description": "test",
                    "request": {"method": "GET", "path": "/test"},
                    "response": {"status": 200},
                }
            ],
        }

        result = analyzer.analyze_migration(contract, contract, "1.0.0", "1.0.0")

        assert len(result.changes) == 0
        assert len(result.breaking_changes) == 0
        assert result.compatibility_score == 1.0

    def test_detect_endpoint_removed(self):
        """Test detecting removed endpoint."""
        analyzer = ContractMigrationAnalyzer()

        old_contract = {
            "consumer": "order",
            "provider": "payment",
            "interactions": [
                {
                    "description": "old endpoint",
                    "request": {"method": "GET", "path": "/old"},
                    "response": {"status": 200},
                }
            ],
        }

        new_contract = {"consumer": "order", "provider": "payment", "interactions": []}

        result = analyzer.analyze_migration(
            old_contract, new_contract, "1.0.0", "2.0.0"
        )

        assert result.has_breaking_changes()
        assert len(result.breaking_changes) == 1
        assert result.breaking_changes[0].change_type == ChangeType.ENDPOINT_REMOVED

    def test_detect_endpoint_added(self):
        """Test detecting added endpoint."""
        analyzer = ContractMigrationAnalyzer()

        old_contract = {"consumer": "order", "provider": "payment", "interactions": []}

        new_contract = {
            "consumer": "order",
            "provider": "payment",
            "interactions": [
                {
                    "description": "new endpoint",
                    "request": {"method": "GET", "path": "/new"},
                    "response": {"status": 200},
                }
            ],
        }

        result = analyzer.analyze_migration(
            old_contract, new_contract, "1.0.0", "1.1.0"
        )

        assert not result.has_breaking_changes()
        changes = result.get_changes_by_type(ChangeType.ENDPOINT_ADDED)
        assert len(changes) == 1
        assert changes[0].severity == ChangeSeverity.INFO

    def test_detect_response_field_removed(self):
        """Test detecting removed response field."""
        analyzer = ContractMigrationAnalyzer()

        old_contract = {
            "consumer": "order",
            "provider": "payment",
            "interactions": [
                {
                    "description": "test",
                    "request": {"method": "GET", "path": "/test"},
                    "response": {"status": 200, "body": {"id": 1, "name": "test"}},
                }
            ],
        }

        new_contract = {
            "consumer": "order",
            "provider": "payment",
            "interactions": [
                {
                    "description": "test",
                    "request": {"method": "GET", "path": "/test"},
                    "response": {"status": 200, "body": {"id": 1}},
                }
            ],
        }

        result = analyzer.analyze_migration(
            old_contract, new_contract, "1.0.0", "2.0.0"
        )

        assert result.has_breaking_changes()
        changes = result.get_changes_by_type(ChangeType.RESPONSE_FIELD_REMOVED)
        assert len(changes) == 1
        assert changes[0].severity == ChangeSeverity.BREAKING

    def test_detect_request_field_added(self):
        """Test detecting added request field."""
        analyzer = ContractMigrationAnalyzer()

        old_contract = {
            "consumer": "order",
            "provider": "payment",
            "interactions": [
                {
                    "description": "test",
                    "request": {"method": "POST", "path": "/test", "body": {"id": 1}},
                    "response": {"status": 200},
                }
            ],
        }

        new_contract = {
            "consumer": "order",
            "provider": "payment",
            "interactions": [
                {
                    "description": "test",
                    "request": {
                        "method": "POST",
                        "path": "/test",
                        "body": {"id": 1, "name": "required"},
                    },
                    "response": {"status": 200},
                }
            ],
        }

        result = analyzer.analyze_migration(
            old_contract, new_contract, "1.0.0", "2.0.0"
        )

        assert result.has_breaking_changes()
        changes = result.get_changes_by_type(ChangeType.REQUEST_FIELD_ADDED)
        assert len(changes) == 1
        assert changes[0].severity == ChangeSeverity.BREAKING

    def test_detect_status_code_change(self):
        """Test detecting response status code change."""
        analyzer = ContractMigrationAnalyzer()

        old_contract = {
            "consumer": "order",
            "provider": "payment",
            "interactions": [
                {
                    "description": "test",
                    "request": {"method": "GET", "path": "/test"},
                    "response": {"status": 200},
                }
            ],
        }

        new_contract = {
            "consumer": "order",
            "provider": "payment",
            "interactions": [
                {
                    "description": "test",
                    "request": {"method": "GET", "path": "/test"},
                    "response": {"status": 201},
                }
            ],
        }

        result = analyzer.analyze_migration(
            old_contract, new_contract, "1.0.0", "2.0.0"
        )

        changes = result.get_changes_by_type(ChangeType.RESPONSE_STATUS_CHANGED)
        assert len(changes) == 1

    def test_generate_migration_guide(self):
        """Test generating migration guide."""
        analyzer = ContractMigrationAnalyzer()

        old_contract = {
            "consumer": "order",
            "provider": "payment",
            "interactions": [
                {
                    "description": "test",
                    "request": {"method": "GET", "path": "/test"},
                    "response": {"status": 200, "body": {"id": 1}},
                }
            ],
        }

        new_contract = {
            "consumer": "order",
            "provider": "payment",
            "interactions": [
                {
                    "description": "test",
                    "request": {"method": "GET", "path": "/test"},
                    "response": {"status": 200, "body": {}},
                }
            ],
        }

        result = analyzer.analyze_migration(
            old_contract, new_contract, "1.0.0", "2.0.0"
        )
        guide = analyzer.generate_migration_guide(result, format="markdown")

        assert "Migration Guide" in guide
        assert "1.0.0 → 2.0.0" in guide
        assert "BREAKING CHANGES" in guide or "Breaking Changes" in guide

    def test_compatibility_score(self):
        """Test compatibility score calculation."""
        analyzer = ContractMigrationAnalyzer()

        # Multiple breaking changes should reduce score significantly
        old_contract = {
            "consumer": "order",
            "provider": "payment",
            "interactions": [
                {
                    "description": "ep1",
                    "request": {"method": "GET", "path": "/ep1"},
                    "response": {"status": 200},
                },
                {
                    "description": "ep2",
                    "request": {"method": "GET", "path": "/ep2"},
                    "response": {"status": 200},
                },
            ],
        }

        new_contract = {"consumer": "order", "provider": "payment", "interactions": []}

        result = analyzer.analyze_migration(
            old_contract, new_contract, "1.0.0", "2.0.0"
        )

        assert result.compatibility_score < 1.0
        assert result.compatibility_score >= 0.0


class TestRESTContractBuilder:
    """Tests for RESTContractBuilder."""

    def test_build_rest_contract(self):
        """Test building REST contract."""
        builder = RESTContractBuilder()

        endpoints = [
            RESTEndpoint(
                path="/users",
                method="GET",
                description="List users",
                response_statuses={200: [{"id": 1, "name": "John"}]},
            ),
            RESTEndpoint(
                path="/users/{id}",
                method="GET",
                description="Get user by ID",
                path_parameters=[
                    FieldDefinition(name="id", field_type="integer", required=True)
                ],
                response_statuses={200: {"id": 1, "name": "John"}, 404: None},
            ),
        ]

        contract_json = builder.build_contract("web-app", "user-api", endpoints)
        contract = json.loads(contract_json)

        assert contract["consumer"] == "web-app"
        assert contract["provider"] == "user-api"
        assert contract["protocol"] == ProtocolType.REST.value
        assert len(contract["interactions"]) == 2

    def test_from_openapi_spec(self):
        """Test building contract from OpenAPI spec."""
        builder = RESTContractBuilder()

        openapi_spec = {
            "openapi": "3.0.0",
            "paths": {
                "/users": {
                    "get": {
                        "summary": "List users",
                        "responses": {
                            "200": {
                                "description": "List of users",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "array",
                                            "items": {"type": "object"},
                                        }
                                    }
                                },
                            }
                        },
                    }
                }
            },
        }

        contract_json = builder.from_openapi_spec("client", "api", openapi_spec)
        contract = json.loads(contract_json)

        assert len(contract["interactions"]) == 1
        # Description is generated as "GET /users" from the path and method
        assert contract["interactions"][0]["description"] == "GET /users"


class TestGraphQLContractBuilder:
    """Tests for GraphQLContractBuilder."""

    def test_build_graphql_contract(self):
        """Test building GraphQL contract."""
        builder = GraphQLContractBuilder()

        operations = [
            GraphQLOperation(
                name="getUser",
                operation_type="query",
                description="Get user by ID",
                arguments=[FieldDefinition(name="id", field_type="ID", required=True)],
                return_type="User",
                return_fields=["id", "name", "email"],
            ),
        ]

        contract_json = builder.build_contract("mobile-app", "graphql-api", operations)
        contract = json.loads(contract_json)

        assert contract["consumer"] == "mobile-app"
        assert contract["provider"] == "graphql-api"
        assert contract["protocol"] == ProtocolType.GRAPHQL.value
        assert len(contract["interactions"]) == 1

        # Check GraphQL query format
        request_body = contract["interactions"][0]["request"]["body"]
        assert "query" in request_body
        assert "getUser" in request_body["query"]

    def test_from_graphql_schema(self):
        """Test building contract from GraphQL introspection schema."""
        builder = GraphQLContractBuilder()

        schema = {
            "data": {
                "__schema": {
                    "queryType": {
                        "fields": [
                            {
                                "name": "getUser",
                                "description": "Get user",
                                "args": [
                                    {
                                        "name": "id",
                                        "type": {
                                            "kind": "NON_NULL",
                                            "ofType": {"name": "ID", "kind": "SCALAR"},
                                        },
                                    }
                                ],
                                "type": {
                                    "kind": "OBJECT",
                                    "name": "User",
                                    "fields": [{"name": "id"}, {"name": "name"}],
                                },
                            }
                        ]
                    }
                }
            }
        }

        contract_json = builder.from_graphql_schema("client", "api", schema)
        contract = json.loads(contract_json)

        assert len(contract["interactions"]) == 1
        assert "getUser" in contract["interactions"][0]["description"]


class TestGRPCContractBuilder:
    """Tests for GRPCContractBuilder."""

    def test_build_grpc_contract(self):
        """Test building gRPC contract."""
        builder = GRPCContractBuilder()

        methods = [
            GRPCMethod(
                name="GetUser",
                service="UserService",
                package="com.example.users",
                input_type="GetUserRequest",
                output_type="User",
                input_fields=[FieldDefinition(name="id", field_type="string")],
                output_fields=[
                    FieldDefinition(name="id", field_type="string"),
                    FieldDefinition(name="name", field_type="string"),
                ],
            ),
        ]

        contract_json = builder.build_contract("client", "grpc-service", methods)
        contract = json.loads(contract_json)

        assert contract["consumer"] == "client"
        assert contract["provider"] == "grpc-service"
        assert contract["protocol"] == ProtocolType.GRPC.value
        assert len(contract["interactions"]) == 1

        # Check gRPC-specific path format
        request_path = contract["interactions"][0]["request"]["path"]
        assert "UserService" in request_path
        assert "GetUser" in request_path


class TestMultiProtocolContractBuilder:
    """Tests for MultiProtocolContractBuilder."""

    def test_build_rest_contract(self):
        """Test building REST contract via multi-protocol builder."""
        builder = MultiProtocolContractBuilder()

        endpoints = [
            RESTEndpoint(path="/test", method="GET", response_statuses={200: {}})
        ]

        contract_json = builder.build_rest_contract("client", "api", endpoints)
        contract = json.loads(contract_json)

        assert contract["protocol"] == ProtocolType.REST.value

    def test_build_graphql_contract(self):
        """Test building GraphQL contract via multi-protocol builder."""
        builder = MultiProtocolContractBuilder()

        operations = [
            GraphQLOperation(name="test", operation_type="query", return_type="String")
        ]

        contract_json = builder.build_graphql_contract("client", "api", operations)
        contract = json.loads(contract_json)

        assert contract["protocol"] == ProtocolType.GRAPHQL.value

    def test_build_grpc_contract(self):
        """Test building gRPC contract via multi-protocol builder."""
        builder = MultiProtocolContractBuilder()

        methods = [
            GRPCMethod(
                name="Test",
                service="TestService",
                input_type="Request",
                output_type="Response",
            )
        ]

        contract_json = builder.build_grpc_contract("client", "api", methods)
        contract = json.loads(contract_json)

        assert contract["protocol"] == ProtocolType.GRPC.value


@pytest.mark.skipif(not _PACT_BROKER_AVAILABLE, reason="Pact Broker not available")
class TestPactBrokerClient:
    """Tests for PactBrokerClient."""

    def test_broker_config_basic_auth(self):
        """Test PactBrokerConfig with basic auth."""
        config = PactBrokerConfig(
            base_url="https://broker.example.com", username="user", password="pass"
        )

        assert config.base_url == "https://broker.example.com"
        auth = config.get_auth()
        assert auth is not None

    def test_broker_config_token_auth(self):
        """Test PactBrokerConfig with token auth."""
        config = PactBrokerConfig(
            base_url="https://broker.example.com", token="my-token"
        )

        auth = config.get_auth()
        assert isinstance(auth, dict)
        assert "Authorization" in auth

    @patch("socialseed_e2e.contract_testing.pact_broker.requests.Session")
    def test_publish_contract(self, mock_session_class):
        """Test publishing contract to broker."""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_session.request = Mock(return_value=mock_response)
        mock_session_class.return_value = mock_session

        config = PactBrokerConfig(base_url="https://broker.example.com")
        client = PactBrokerClient(config)

        contract = json.dumps({"consumer": "order", "provider": "payment"})
        result = client.publish_contract(
            contract, "order-service", "payment-service", "1.0.0", tags=["prod"]
        )

        assert result is True
        mock_session.request.assert_called()

    @patch("socialseed_e2e.contract_testing.pact_broker.requests.Session")
    def test_get_contract(self, mock_session_class):
        """Test retrieving contract from broker."""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.text = json.dumps({"test": "data"})
        mock_response.raise_for_status = Mock()
        mock_session.request = Mock(return_value=mock_response)
        mock_session_class.return_value = mock_session

        config = PactBrokerConfig(base_url="https://broker.example.com")
        client = PactBrokerClient(config)

        result = client.get_contract("consumer", "provider", "1.0.0")

        assert result is not None
        assert json.loads(result)["test"] == "data"


class TestChangeSeverity:
    """Tests for ChangeSeverity enum."""

    def test_severity_levels(self):
        """Test change severity levels."""
        assert ChangeSeverity.INFO.value == "info"
        assert ChangeSeverity.WARNING.value == "warning"
        assert ChangeSeverity.BREAKING.value == "breaking"
        assert ChangeSeverity.CRITICAL.value == "critical"


class TestChangeType:
    """Tests for ChangeType enum."""

    def test_change_types(self):
        """Test change type values."""
        assert ChangeType.ENDPOINT_ADDED.value == "endpoint_added"
        assert ChangeType.ENDPOINT_REMOVED.value == "endpoint_removed"
        assert ChangeType.RESPONSE_FIELD_REMOVED.value == "response_field_removed"


class TestFieldDefinition:
    """Tests for FieldDefinition."""

    def test_field_creation(self):
        """Test creating field definition."""
        field = FieldDefinition(
            name="userId",
            field_type="string",
            required=True,
            description="User identifier",
            constraints={"minLength": 1, "maxLength": 100},
        )

        assert field.name == "userId"
        assert field.field_type == "string"
        assert field.required is True
        assert field.constraints["minLength"] == 1


class TestRESTEndpoint:
    """Tests for RESTEndpoint."""

    def test_to_contract_interaction(self):
        """Test converting RESTEndpoint to contract format."""
        endpoint = RESTEndpoint(
            path="/users/{id}",
            method="GET",
            description="Get user",
            path_parameters=[FieldDefinition(name="id", field_type="integer")],
            response_statuses={200: {"id": 1}},
        )

        interaction = endpoint.to_contract_interaction()

        assert interaction["request"]["method"] == "GET"
        assert interaction["request"]["path"] == "/users/{id}"
        assert interaction["response"]["status"] == 200


class TestGraphQLOperation:
    """Tests for GraphQLOperation."""

    def test_to_contract_interaction(self):
        """Test converting GraphQL operation to contract format."""
        operation = GraphQLOperation(
            name="getUser",
            operation_type="query",
            arguments=[FieldDefinition(name="id", field_type="ID")],
            return_fields=["id", "name"],
        )

        interaction = operation.to_contract_interaction()

        assert interaction["request"]["method"] == "POST"
        assert interaction["request"]["path"] == "/graphql"
        assert "query" in interaction["request"]["body"]
        assert "getUser" in interaction["request"]["body"]["query"]


class TestGRPCMethod:
    """Tests for GRPCMethod."""

    def test_to_contract_interaction(self):
        """Test converting gRPC method to contract format."""
        method = GRPCMethod(
            name="GetUser",
            service="UserService",
            package="com.example",
            input_fields=[FieldDefinition(name="id", field_type="string")],
            output_fields=[FieldDefinition(name="name", field_type="string")],
        )

        interaction = method.to_contract_interaction()

        assert interaction["request"]["method"] == "GRPC"
        assert "UserService" in interaction["request"]["path"]
        assert "GetUser" in interaction["request"]["path"]


class TestMigrationAnalysisResult:
    """Tests for MigrationAnalysisResult."""

    def test_has_breaking_changes(self):
        """Test checking for breaking changes."""
        result = MigrationAnalysisResult(
            old_version="1.0.0",
            new_version="2.0.0",
            breaking_changes=[
                ContractChange(
                    change_type=ChangeType.ENDPOINT_REMOVED,
                    severity=ChangeSeverity.BREAKING,
                    path="test",
                    description="Test",
                )
            ],
        )

        assert result.has_breaking_changes() is True

    def test_get_changes_by_severity(self):
        """Test filtering changes by severity."""
        result = MigrationAnalysisResult(
            old_version="1.0.0",
            new_version="2.0.0",
            changes=[
                ContractChange(
                    change_type=ChangeType.ENDPOINT_ADDED,
                    severity=ChangeSeverity.INFO,
                    path="test1",
                    description="Test1",
                ),
                ContractChange(
                    change_type=ChangeType.ENDPOINT_REMOVED,
                    severity=ChangeSeverity.BREAKING,
                    path="test2",
                    description="Test2",
                ),
            ],
        )

        info_changes = result.get_changes_by_severity(ChangeSeverity.INFO)
        breaking_changes = result.get_changes_by_severity(ChangeSeverity.BREAKING)

        assert len(info_changes) == 1
        assert len(breaking_changes) == 1

    def test_get_changes_by_type(self):
        """Test filtering changes by type."""
        result = MigrationAnalysisResult(
            old_version="1.0.0",
            new_version="2.0.0",
            changes=[
                ContractChange(
                    change_type=ChangeType.ENDPOINT_ADDED,
                    severity=ChangeSeverity.INFO,
                    path="test1",
                    description="Test1",
                ),
                ContractChange(
                    change_type=ChangeType.ENDPOINT_REMOVED,
                    severity=ChangeSeverity.BREAKING,
                    path="test2",
                    description="Test2",
                ),
            ],
        )

        added = result.get_changes_by_type(ChangeType.ENDPOINT_ADDED)
        removed = result.get_changes_by_type(ChangeType.ENDPOINT_REMOVED)

        assert len(added) == 1
        assert len(removed) == 1
