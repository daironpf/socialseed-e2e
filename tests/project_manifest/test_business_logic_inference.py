"""Tests for Business Logic Inference Engine."""

import pytest

from socialseed_e2e.project_manifest.business_logic_inference import (
    BusinessFlow,
    BusinessLogicInferenceEngine,
    FlowType,
    RelationshipType,
)
from socialseed_e2e.project_manifest.models import DtoField, DtoSchema, EndpointInfo, HttpMethod


class TestBusinessLogicInference:
    """Test suite for business logic inference."""

    def test_detect_registration_login_flow(self):
        """Test detection of registration → login flow."""
        # Create endpoints
        register_endpoint = EndpointInfo(
            name="registerUser",
            method=HttpMethod.POST,
            path="/auth/register",
            full_path="/auth/register",
            request_dto="RegisterRequest",
            file_path="test.py",
            line_number=1,
        )

        login_endpoint = EndpointInfo(
            name="loginUser",
            method=HttpMethod.POST,
            path="/auth/login",
            full_path="/auth/login",
            request_dto="LoginRequest",
            file_path="test.py",
            line_number=2,
        )

        profile_endpoint = EndpointInfo(
            name="getProfile",
            method=HttpMethod.GET,
            path="/auth/me",
            full_path="/auth/me",
            requires_auth=True,
            file_path="test.py",
            line_number=3,
        )

        # Run inference
        engine = BusinessLogicInferenceEngine(
            endpoints=[register_endpoint, login_endpoint, profile_endpoint], dtos=[]
        )
        result = engine.analyze()

        # Assertions
        assert len(result["flows"]) > 0

        # Check for auth flow
        auth_flow = next(
            (f for f in result["flows"] if f.flow_type == FlowType.AUTHENTICATION), None
        )
        assert auth_flow is not None
        assert len(auth_flow.steps) >= 2

    def test_detect_crud_flow(self):
        """Test detection of CRUD operations flow."""
        endpoints = [
            EndpointInfo(
                name="createUser",
                method=HttpMethod.POST,
                path="/users",
                full_path="/users",
                file_path="test.py",
                line_number=1,
            ),
            EndpointInfo(
                name="getUser",
                method=HttpMethod.GET,
                path="/users/{id}",
                full_path="/users/{id}",
                file_path="test.py",
                line_number=2,
            ),
            EndpointInfo(
                name="updateUser",
                method=HttpMethod.PUT,
                path="/users/{id}",
                full_path="/users/{id}",
                file_path="test.py",
                line_number=3,
            ),
            EndpointInfo(
                name="deleteUser",
                method=HttpMethod.DELETE,
                path="/users/{id}",
                full_path="/users/{id}",
                file_path="test.py",
                line_number=4,
            ),
        ]

        engine = BusinessLogicInferenceEngine(endpoints=endpoints, dtos=[])
        result = engine.analyze()

        # Check for CRUD flow
        crud_flow = next((f for f in result["flows"] if f.flow_type == FlowType.CRUD), None)
        assert crud_flow is not None
        assert "User" in crud_flow.entities_involved

    def test_detect_endpoint_relationships(self):
        """Test detection of relationships between endpoints."""
        register = EndpointInfo(
            name="register",
            method=HttpMethod.POST,
            path="/register",
            full_path="/register",
            file_path="test.py",
            line_number=1,
        )

        login = EndpointInfo(
            name="login",
            method=HttpMethod.POST,
            path="/login",
            full_path="/login",
            file_path="test.py",
            line_number=2,
        )

        engine = BusinessLogicInferenceEngine(endpoints=[register, login], dtos=[])
        result = engine.analyze()

        # Check for sequential relationship
        sequential = [
            r for r in result["relationships"] if r.relationship_type == RelationshipType.SEQUENTIAL
        ]
        assert len(sequential) > 0

    def test_extract_validation_criteria(self):
        """Test extraction of validation criteria from DTOs."""
        dto = DtoSchema(
            name="UserRequest",
            fields=[
                DtoField(
                    name="username",
                    type="str",
                    required=True,
                    validations=[
                        {"rule_type": "min_length", "value": 3},
                        {"rule_type": "max_length", "value": 50},
                    ],
                ),
                DtoField(name="email", type="EmailStr", required=True),
            ],
            file_path="test.py",
            line_number=1,
        )

        engine = BusinessLogicInferenceEngine(endpoints=[], dtos=[dto])
        result = engine.analyze()

        # Check validation criteria
        assert len(result["validation_criteria"]) > 0

        username_criteria = result["validation_criteria"].get("UserRequest.username")
        assert username_criteria is not None
        assert len(username_criteria.rules) == 2
        assert len(username_criteria.success_criteria) > 0
        assert len(username_criteria.failure_scenarios) > 0


class TestFlowDetection:
    """Test flow detection capabilities."""

    def test_entity_name_extraction(self):
        """Test extraction of entity names from paths."""
        engine = BusinessLogicInferenceEngine(endpoints=[], dtos=[])

        # Test various path patterns
        test_cases = [
            ("/users", "users"),
            ("/users/{id}", "users"),
            ("/api/v1/products", "products"),
            ("/auth/login", "auth"),
        ]

        for path, expected in test_cases:
            endpoint = EndpointInfo(
                name="test",
                method=HttpMethod.GET,
                path=path,
                full_path=path,
                file_path="test.py",
                line_number=1,
            )
            entity = engine._extract_entity_name(endpoint)
            assert entity == expected, f"Failed for path: {path}"

    def test_is_crud_operation(self):
        """Test CRUD operation detection."""
        engine = BusinessLogicInferenceEngine(endpoints=[], dtos=[])

        # Test CREATE
        create_ep = EndpointInfo(
            name="createUser",
            method=HttpMethod.POST,
            path="/users",
            full_path="/users",
            file_path="test.py",
            line_number=1,
        )
        assert engine._is_crud_operation(create_ep, "create")

        # Test READ
        read_ep = EndpointInfo(
            name="getUser",
            method=HttpMethod.GET,
            path="/users/{id}",
            full_path="/users/{id}",
            file_path="test.py",
            line_number=1,
        )
        assert engine._is_crud_operation(read_ep, "read")

        # Test UPDATE
        update_ep = EndpointInfo(
            name="updateUser",
            method=HttpMethod.PUT,
            path="/users/{id}",
            full_path="/users/{id}",
            file_path="test.py",
            line_number=1,
        )
        assert engine._is_crud_operation(update_ep, "update")

        # Test DELETE
        delete_ep = EndpointInfo(
            name="deleteUser",
            method=HttpMethod.DELETE,
            path="/users/{id}",
            full_path="/users/{id}",
            file_path="test.py",
            line_number=1,
        )
        assert engine._is_crud_operation(delete_ep, "delete")


class TestScenarioGeneration:
    """Test test scenario generation."""

    def test_suggest_test_scenarios(self):
        """Test generation of test scenarios."""
        # Create a simple flow
        endpoint = EndpointInfo(
            name="createUser",
            method=HttpMethod.POST,
            path="/users",
            full_path="/users",
            request_dto="UserRequest",
            file_path="test.py",
            line_number=1,
        )

        flow = BusinessFlow(
            name="User Creation",
            flow_type=FlowType.CRUD,
            description="Create user flow",
            steps=[],  # Simplified for test
        )

        dto = DtoSchema(
            name="UserRequest",
            fields=[
                DtoField(
                    name="username",
                    type="str",
                    required=True,
                    validations=[{"rule_type": "min_length", "value": 3}],
                ),
            ],
            file_path="test.py",
            line_number=1,
        )

        engine = BusinessLogicInferenceEngine(endpoints=[endpoint], dtos=[dto])
        engine.flows = [flow]
        scenarios = engine.suggest_test_scenarios()

        # Should generate success, failure, and chaos scenarios
        assert len(scenarios) > 0

        # Check for different scenario types
        types = {s["type"] for s in scenarios}
        assert "success" in types
        assert "chaos" in types
