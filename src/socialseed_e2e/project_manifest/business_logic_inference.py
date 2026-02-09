"""Business Logic Inference Engine for detecting endpoint relationships and flows.

This module analyzes endpoints to understand business logic relationships,
such as register → login flows, CRUD operations, and entity lifecycle patterns.
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from socialseed_e2e.project_manifest.models import DtoSchema, EndpointInfo, HttpMethod


class FlowType(str, Enum):
    """Types of business flows that can be detected."""

    AUTHENTICATION = "authentication"
    REGISTRATION = "registration"
    CRUD = "crud"
    LIFECYCLE = "lifecycle"
    WORKFLOW = "workflow"
    DATA_IMPORT = "data_import"
    DATA_EXPORT = "data_export"
    NOTIFICATION = "notification"
    CUSTOM = "custom"


class RelationshipType(str, Enum):
    """Types of relationships between endpoints."""

    SEQUENTIAL = "sequential"  # Must happen in order (register → login)
    DEPENDENT = "dependent"  # Requires previous endpoint (delete requires create)
    ALTERNATIVE = "alternative"  # Different ways to achieve same goal
    COMPLEMENTARY = "complementary"  # Work together (create + get)
    CONFLICTING = "conflicting"  # Mutually exclusive operations


@dataclass
class EndpointRelationship:
    """Relationship between two endpoints."""

    source_endpoint: str
    target_endpoint: str
    relationship_type: RelationshipType
    confidence: float  # 0.0 to 1.0
    reason: str
    data_flow: Optional[List[str]] = None  # Fields passed between endpoints


@dataclass
class FlowStep:
    """A step in a business flow."""

    endpoint: EndpointInfo
    step_number: int
    description: str
    required_data_from_previous: List[str] = field(default_factory=list)
    output_data_for_next: List[str] = field(default_factory=list)
    optional: bool = False
    alternatives: List[EndpointInfo] = field(default_factory=list)


@dataclass
class BusinessFlow:
    """A complete business flow composed of multiple steps."""

    name: str
    flow_type: FlowType
    description: str
    steps: List[FlowStep]
    entry_points: List[EndpointInfo] = field(default_factory=list)
    exit_points: List[EndpointInfo] = field(default_factory=list)
    entities_involved: List[str] = field(default_factory=list)
    estimated_duration_ms: Optional[int] = None  # Estimated execution time

    def get_required_dtos(self) -> Set[str]:
        """Get all DTOs required for this flow."""
        dtos = set()
        for step in self.steps:
            if step.endpoint.request_dto:
                dtos.add(step.endpoint.request_dto)
            if step.endpoint.response_dto:
                dtos.add(step.endpoint.response_dto)
        return dtos


@dataclass
class ValidationCriteria:
    """Validation criteria detected from code."""

    field_name: str
    rules: List[Dict[str, Any]]
    error_messages: List[str]
    success_criteria: List[str]
    failure_scenarios: List[str]
    chaos_test_ideas: List[str]


class BusinessLogicInferenceEngine:
    """Engine to infer business logic from endpoints and relationships."""

    # Keywords that indicate authentication flows
    AUTH_KEYWORDS = [
        "login",
        "authenticate",
        "auth",
        "signin",
        "sign-in",
        "token",
        "refresh",
        "logout",
        "signout",
        "session",
        "oauth",
        "jwt",
    ]

    # Keywords that indicate registration flows
    REGISTRATION_KEYWORDS = [
        "register",
        "signup",
        "sign-up",
        "create.*account",
        "create.*user",
        "verify.*email",
        "confirm.*email",
        "activate",
    ]

    # Keywords that indicate CRUD operations
    CRUD_KEYWORDS = {
        "create": ["create", "add", "new", "insert", "post"],
        "read": ["get", "fetch", "retrieve", "find", "list", "search"],
        "update": ["update", "edit", "modify", "patch", "put"],
        "delete": ["delete", "remove", "destroy", "trash"],
    }

    # Entity lifecycle patterns
    LIFECYCLE_PATTERNS = [
        ("create", "activate", "deactivate", "delete"),
        ("draft", "publish", "unpublish", "archive"),
        ("pending", "approve", "reject"),
        ("init", "process", "complete", "cleanup"),
    ]

    def __init__(self, endpoints: List[EndpointInfo], dtos: List[DtoSchema]):
        """Initialize the inference engine.

        Args:
            endpoints: List of all endpoints in the service
            dtos: List of all DTO schemas
        """
        self.endpoints = endpoints
        self.dtos = {dto.name: dto for dto in dtos}
        self.relationships: List[EndpointRelationship] = []
        self.flows: List[BusinessFlow] = []
        self.validation_criteria: Dict[str, ValidationCriteria] = {}

    def analyze(self) -> Dict[str, Any]:
        """Run complete analysis and return all inferred information.

        Returns:
            Dictionary containing relationships, flows, and validation criteria
        """
        self._detect_relationships()
        self._detect_flows()
        self._extract_validation_criteria()

        return {
            "relationships": self.relationships,
            "flows": self.flows,
            "validation_criteria": self.validation_criteria,
            "summary": self._generate_summary(),
        }

    def _detect_relationships(self) -> None:
        """Detect relationships between endpoints."""
        for i, ep1 in enumerate(self.endpoints):
            for ep2 in self.endpoints[i + 1 :]:
                relationship = self._analyze_endpoint_pair(ep1, ep2)
                if relationship:
                    self.relationships.append(relationship)

    def _analyze_endpoint_pair(
        self, ep1: EndpointInfo, ep2: EndpointInfo
    ) -> Optional[EndpointRelationship]:
        """Analyze a pair of endpoints for relationships.

        Args:
            ep1: First endpoint
            ep2: Second endpoint

        Returns:
            EndpointRelationship if a relationship is detected, None otherwise
        """
        # Check for registration → login flow
        if self._is_registration_endpoint(ep1) and self._is_login_endpoint(ep2):
            return EndpointRelationship(
                source_endpoint=ep1.name,
                target_endpoint=ep2.name,
                relationship_type=RelationshipType.SEQUENTIAL,
                confidence=0.95,
                reason="Registration typically precedes login",
                data_flow=["username", "email", "user_id"],
            )

        # Check for login → authenticated operation flow
        if self._is_login_endpoint(ep1) and ep2.requires_auth:
            return EndpointRelationship(
                source_endpoint=ep1.name,
                target_endpoint=ep2.name,
                relationship_type=RelationshipType.DEPENDENT,
                confidence=0.90,
                reason="Login provides authentication token for subsequent operations",
                data_flow=["access_token", "refresh_token"],
            )

        # Check for CRUD relationships
        crud_relation = self._detect_crud_relationship(ep1, ep2)
        if crud_relation:
            return crud_relation

        # Check for entity lifecycle patterns
        lifecycle_relation = self._detect_lifecycle_relationship(ep1, ep2)
        if lifecycle_relation:
            return lifecycle_relation

        # Check for DTO data flow
        dto_relation = self._detect_dto_data_flow(ep1, ep2)
        if dto_relation:
            return dto_relation

        return None

    def _is_registration_endpoint(self, endpoint: EndpointInfo) -> bool:
        """Check if endpoint is a registration endpoint."""
        name_lower = endpoint.name.lower()
        path_lower = endpoint.path.lower()

        for keyword in self.REGISTRATION_KEYWORDS:
            if re.search(keyword, name_lower) or re.search(keyword, path_lower):
                return endpoint.method == HttpMethod.POST
        return False

    def _is_login_endpoint(self, endpoint: EndpointInfo) -> bool:
        """Check if endpoint is a login/authentication endpoint."""
        name_lower = endpoint.name.lower()
        path_lower = endpoint.path.lower()

        for keyword in self.AUTH_KEYWORDS:
            if keyword in name_lower or keyword in path_lower:
                return endpoint.method in [HttpMethod.POST, HttpMethod.GET]
        return False

    def _detect_crud_relationship(
        self, ep1: EndpointInfo, ep2: EndpointInfo
    ) -> Optional[EndpointRelationship]:
        """Detect CRUD relationships between endpoints."""
        # Extract entity names from paths
        ep1_entity = self._extract_entity_name(ep1)
        ep2_entity = self._extract_entity_name(ep2)

        if ep1_entity != ep2_entity:
            return None

        # Create → Read relationship
        if self._is_crud_operation(ep1, "create") and self._is_crud_operation(ep2, "read"):
            return EndpointRelationship(
                source_endpoint=ep1.name,
                target_endpoint=ep2.name,
                relationship_type=RelationshipType.COMPLEMENTARY,
                confidence=0.85,
                reason=f"Create and Read operations on same entity: {ep1_entity}",
                data_flow=["id", f"{ep1_entity}_id"],
            )

        # Read → Update relationship
        if self._is_crud_operation(ep1, "read") and self._is_crud_operation(ep2, "update"):
            return EndpointRelationship(
                source_endpoint=ep1.name,
                target_endpoint=ep2.name,
                relationship_type=RelationshipType.SEQUENTIAL,
                confidence=0.80,
                reason=f"Read before Update on entity: {ep1_entity}",
                data_flow=["id"],
            )

        # Create → Delete relationship
        if self._is_crud_operation(ep1, "create") and self._is_crud_operation(ep2, "delete"):
            return EndpointRelationship(
                source_endpoint=ep1.name,
                target_endpoint=ep2.name,
                relationship_type=RelationshipType.COMPLEMENTARY,
                confidence=0.75,
                reason=f"Create and Delete operations on same entity: {ep1_entity}",
                data_flow=["id"],
            )

        return None

    def _extract_entity_name(self, endpoint: EndpointInfo) -> Optional[str]:
        """Extract entity name from endpoint path or name."""
        # Try to extract from path
        path_parts = endpoint.path.strip("/").split("/")
        for part in path_parts:
            if part and not part.startswith("{"):
                return part.lower()

        # Try to extract from name
        name_lower = endpoint.name.lower()
        for op in ["create", "get", "update", "delete", "list", "find"]:
            if name_lower.startswith(op):
                return name_lower[len(op) :].strip("_").lower()

        return None

    def _is_crud_operation(self, endpoint: EndpointInfo, operation: str) -> bool:
        """Check if endpoint performs a specific CRUD operation."""
        name_lower = endpoint.name.lower()
        keywords = self.CRUD_KEYWORDS.get(operation, [])

        for keyword in keywords:
            if keyword in name_lower:
                # Verify HTTP method matches
                if operation == "create" and endpoint.method == HttpMethod.POST:
                    return True
                elif operation == "read" and endpoint.method == HttpMethod.GET:
                    return True
                elif operation == "update" and endpoint.method in [
                    HttpMethod.PUT,
                    HttpMethod.PATCH,
                ]:
                    return True
                elif operation == "delete" and endpoint.method == HttpMethod.DELETE:
                    return True

        return False

    def _detect_lifecycle_relationship(
        self, ep1: EndpointInfo, ep2: EndpointInfo
    ) -> Optional[EndpointRelationship]:
        """Detect entity lifecycle relationships."""
        name1 = ep1.name.lower()
        name2 = ep2.name.lower()

        for pattern in self.LIFECYCLE_PATTERNS:
            for i, state1 in enumerate(pattern[:-1]):
                for state2 in pattern[i + 1 :]:
                    if state1 in name1 and state2 in name2:
                        return EndpointRelationship(
                            source_endpoint=ep1.name,
                            target_endpoint=ep2.name,
                            relationship_type=RelationshipType.SEQUENTIAL,
                            confidence=0.70,
                            reason=f"Entity lifecycle: {state1} → {state2}",
                            data_flow=["id", "status"],
                        )

        return None

    def _detect_dto_data_flow(
        self, ep1: EndpointInfo, ep2: EndpointInfo
    ) -> Optional[EndpointRelationship]:
        """Detect data flow through shared DTOs."""
        # Check if response DTO of ep1 matches request DTO of ep2
        if ep1.response_dto and ep2.request_dto:
            if ep1.response_dto == ep2.request_dto:
                return EndpointRelationship(
                    source_endpoint=ep1.name,
                    target_endpoint=ep2.name,
                    relationship_type=RelationshipType.SEQUENTIAL,
                    confidence=0.80,
                    reason=f"Shared DTO: {ep1.response_dto}",
                    data_flow=[ep1.response_dto],
                )

        # Check for field overlap in DTOs
        if ep1.response_dto and ep2.request_dto:
            dto1 = self.dtos.get(ep1.response_dto)
            dto2 = self.dtos.get(ep2.request_dto)

            if dto1 and dto2:
                fields1 = {f.name for f in dto1.fields}
                fields2 = {f.name for f in dto2.fields}
                overlap = fields1 & fields2

                if len(overlap) >= 2:  # At least 2 common fields
                    return EndpointRelationship(
                        source_endpoint=ep1.name,
                        target_endpoint=ep2.name,
                        relationship_type=RelationshipType.COMPLEMENTARY,
                        confidence=0.65,
                        reason=f"Shared fields: {', '.join(overlap)}",
                        data_flow=list(overlap),
                    )

        return None

    def _detect_flows(self) -> None:
        """Detect complete business flows from relationships."""
        # Group relationships by type
        sequential = [
            r for r in self.relationships if r.relationship_type == RelationshipType.SEQUENTIAL
        ]
        dependent = [
            r for r in self.relationships if r.relationship_type == RelationshipType.DEPENDENT
        ]

        # Detect authentication flows
        auth_flow = self._build_auth_flow(sequential)
        if auth_flow:
            self.flows.append(auth_flow)

        # Detect CRUD flows
        crud_flows = self._build_crud_flows(dependent)
        self.flows.extend(crud_flows)

        # Detect custom workflows
        custom_flows = self._build_custom_workflows()
        self.flows.extend(custom_flows)

    def _build_auth_flow(self, sequential: List[EndpointRelationship]) -> Optional[BusinessFlow]:
        """Build authentication flow from sequential relationships."""
        steps = []

        # Find registration endpoint
        reg_endpoint = None
        for ep in self.endpoints:
            if self._is_registration_endpoint(ep):
                reg_endpoint = ep
                break

        # Find login endpoint
        login_endpoint = None
        for ep in self.endpoints:
            if self._is_login_endpoint(ep):
                login_endpoint = ep
                break

        if reg_endpoint and login_endpoint:
            steps.append(
                FlowStep(
                    endpoint=reg_endpoint,
                    step_number=1,
                    description="Register new user account",
                    output_data_for_next=["user_id", "email"],
                )
            )

            steps.append(
                FlowStep(
                    endpoint=login_endpoint,
                    step_number=2,
                    description="Login with registered credentials",
                    required_data_from_previous=["email", "password"],
                    output_data_for_next=["access_token", "refresh_token"],
                )
            )

            # Add authenticated endpoints as optional steps
            auth_required = [ep for ep in self.endpoints if ep.requires_auth]
            if auth_required:
                steps.append(
                    FlowStep(
                        endpoint=auth_required[0],
                        step_number=3,
                        description=f"Access protected resource: {auth_required[0].name}",
                        required_data_from_previous=["access_token"],
                        alternatives=auth_required[1:] if len(auth_required) > 1 else [],
                    )
                )

            return BusinessFlow(
                name="User Authentication Flow",
                flow_type=FlowType.AUTHENTICATION,
                description="Complete user registration and login flow",
                steps=steps,
                entry_points=[reg_endpoint],
                exit_points=[login_endpoint] if not auth_required else [auth_required[0]],
                entities_involved=["User"],
            )

        return None

    def _build_crud_flows(self, dependent: List[EndpointRelationship]) -> List[BusinessFlow]:
        """Build CRUD flows for each entity."""
        flows = []

        # Group endpoints by entity
        entity_endpoints: Dict[str, List[EndpointInfo]] = {}
        for ep in self.endpoints:
            entity = self._extract_entity_name(ep)
            if entity:
                if entity not in entity_endpoints:
                    entity_endpoints[entity] = []
                entity_endpoints[entity].append(ep)

        # Build flow for each entity with multiple operations
        for entity, endpoints in entity_endpoints.items():
            if len(endpoints) >= 2:
                steps = []
                step_num = 1

                # Sort endpoints: create → read → update → delete
                sorted_eps = sorted(endpoints, key=lambda e: self._get_crud_priority(e))

                for ep in sorted_eps:
                    desc = self._get_crud_description(ep, entity)
                    steps.append(FlowStep(endpoint=ep, step_number=step_num, description=desc))
                    step_num += 1

                flows.append(
                    BusinessFlow(
                        name=f"{entity.title()} CRUD Operations",
                        flow_type=FlowType.CRUD,
                        description=f"Complete CRUD lifecycle for {entity}",
                        steps=steps,
                        entities_involved=[entity],
                    )
                )

        return flows

    def _get_crud_priority(self, endpoint: EndpointInfo) -> int:
        """Get priority for CRUD ordering."""
        name_lower = endpoint.name.lower()

        if self._is_crud_operation(endpoint, "create"):
            return 1
        elif self._is_crud_operation(endpoint, "read"):
            return 2
        elif self._is_crud_operation(endpoint, "update"):
            return 3
        elif self._is_crud_operation(endpoint, "delete"):
            return 4
        return 5

    def _get_crud_description(self, endpoint: EndpointInfo, entity: str) -> str:
        """Get human-readable description for CRUD operation."""
        if self._is_crud_operation(endpoint, "create"):
            return f"Create new {entity}"
        elif self._is_crud_operation(endpoint, "read"):
            return f"Retrieve {entity} information"
        elif self._is_crud_operation(endpoint, "update"):
            return f"Update {entity} details"
        elif self._is_crud_operation(endpoint, "delete"):
            return f"Delete {entity}"
        return f"Perform operation on {entity}"

    def _build_custom_workflows(self) -> List[BusinessFlow]:
        """Build custom workflows based on path patterns."""
        flows = []

        # Look for workflow patterns in paths
        workflow_patterns = [
            (r"/checkout", r"/payment", r"/confirm"),
            (r"/upload", r"/process", r"/download"),
            (r"/import", r"/validate", r"/save"),
        ]

        for pattern in workflow_patterns:
            workflow_eps = []
            for path_pattern in pattern:
                for ep in self.endpoints:
                    if re.search(path_pattern, ep.path, re.IGNORECASE):
                        workflow_eps.append(ep)

            if len(workflow_eps) >= 2:
                steps = [
                    FlowStep(
                        endpoint=ep,
                        step_number=i + 1,
                        description=f"Step {i + 1}: {ep.name}",
                    )
                    for i, ep in enumerate(workflow_eps)
                ]

                flows.append(
                    BusinessFlow(
                        name=f"Workflow: {pattern[0].strip('/')}",
                        flow_type=FlowType.WORKFLOW,
                        description=f"Automated workflow detection for {pattern[0]}",
                        steps=steps,
                    )
                )

        return flows

    def _extract_validation_criteria(self) -> None:
        """Extract validation criteria from DTOs."""
        for dto_name, dto in self.dtos.items():
            for field in dto.fields:
                criteria = self._analyze_field_validations(field)
                key = f"{dto_name}.{field.name}"
                self.validation_criteria[key] = criteria

    def _analyze_field_validations(self, field) -> ValidationCriteria:
        """Analyze validation rules for a field and generate test scenarios."""
        rules = []
        error_messages = []
        success_criteria = []
        failure_scenarios = []
        chaos_test_ideas = []

        for validation in field.validations:
            rule_info = {
                "type": validation.rule_type,
                "value": validation.value,
                "error_message": validation.error_message,
            }
            rules.append(rule_info)

            # Generate test scenarios based on validation type
            if validation.rule_type == "min_length":
                min_val = validation.value
                success_criteria.append(f"Value with length >= {min_val}")
                failure_scenarios.append(f"Value with length < {min_val}")
                chaos_test_ideas.append(f"Boundary test: exactly {min_val} characters")
                chaos_test_ideas.append(f"Boundary test: {min_val - 1} characters (should fail)")

            elif validation.rule_type == "max_length":
                max_val = validation.value
                success_criteria.append(f"Value with length <= {max_val}")
                failure_scenarios.append(f"Value with length > {max_val}")
                chaos_test_ideas.append(f"Boundary test: exactly {max_val} characters")
                chaos_test_ideas.append(f"Boundary test: {max_val + 1} characters (should fail)")

            elif validation.rule_type == "regex":
                pattern = validation.value
                success_criteria.append(f"Value matching pattern: {pattern}")
                failure_scenarios.append(f"Value not matching pattern: {pattern}")
                chaos_test_ideas.append(f"Edge case: empty string against pattern")
                chaos_test_ideas.append(f"Edge case: special characters in pattern")

            elif validation.rule_type in ["gt", "ge"]:
                success_criteria.append(f"Value > {validation.value}")
                failure_scenarios.append(f"Value <= {validation.value}")

            elif validation.rule_type in ["lt", "le"]:
                success_criteria.append(f"Value < {validation.value}")
                failure_scenarios.append(f"Value >= {validation.value}")

        # If no validations, still add basic criteria
        if not rules:
            if field.required:
                success_criteria.append("Non-null value")
                failure_scenarios.append("Null value")
                chaos_test_ideas.append("Empty value test")
            else:
                success_criteria.append("Any value or null")

        return ValidationCriteria(
            field_name=field.name,
            rules=rules,
            error_messages=error_messages,
            success_criteria=success_criteria,
            failure_scenarios=failure_scenarios,
            chaos_test_ideas=chaos_test_ideas,
        )

    def _generate_summary(self) -> Dict[str, Any]:
        """Generate analysis summary."""
        return {
            "total_endpoints": len(self.endpoints),
            "total_relationships": len(self.relationships),
            "total_flows": len(self.flows),
            "flow_types": {flow.flow_type.value for flow in self.flows},
            "entities_involved": list(
                set(entity for flow in self.flows for entity in flow.entities_involved)
            ),
            "validation_fields_analyzed": len(self.validation_criteria),
        }

    def get_flow_for_entity(self, entity_name: str) -> Optional[BusinessFlow]:
        """Get the flow for a specific entity."""
        for flow in self.flows:
            if entity_name in flow.entities_involved:
                return flow
        return None

    def get_related_endpoints(self, endpoint_name: str) -> List[EndpointRelationship]:
        """Get all relationships for a specific endpoint."""
        return [
            r
            for r in self.relationships
            if r.source_endpoint == endpoint_name or r.target_endpoint == endpoint_name
        ]

    def suggest_test_scenarios(self) -> List[Dict[str, Any]]:
        """Suggest test scenarios based on analysis."""
        scenarios = []

        for flow in self.flows:
            # Success scenario
            scenarios.append(
                {
                    "name": f"{flow.name} - Success",
                    "flow": flow,
                    "type": "success",
                    "description": f"Complete {flow.flow_type.value} flow with valid data",
                }
            )

            # Failure scenarios for each step
            for step in flow.steps:
                if step.endpoint.request_dto:
                    dto_key = step.endpoint.request_dto
                    for field_key, criteria in self.validation_criteria.items():
                        if field_key.startswith(dto_key):
                            for failure in criteria.failure_scenarios:
                                scenarios.append(
                                    {
                                        "name": f"{flow.name} - {step.endpoint.name} Validation Failure",
                                        "flow": flow,
                                        "step": step,
                                        "type": "failure",
                                        "field": field_key,
                                        "failure": failure,
                                        "description": f"Test validation failure: {failure}",
                                    }
                                )

            # Chaos test scenarios
            scenarios.append(
                {
                    "name": f"{flow.name} - Chaos Test",
                    "flow": flow,
                    "type": "chaos",
                    "description": f"Random invalid data and edge cases for {flow.name}",
                }
            )

        return scenarios
