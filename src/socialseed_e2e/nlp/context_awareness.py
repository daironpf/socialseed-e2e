"""Context Awareness for NLP-based test generation.

This module provides context understanding by analyzing project structure,
existing APIs, and test patterns to generate more accurate test code.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from socialseed_e2e.nlp.models import (
    ActionType,
    EntityType,
    NaturalLanguageTest,
    ParsedAction,
    ParsedEntity,
    TranslationContext,
)
from socialseed_e2e.project_manifest.api import ManifestAPI
from socialseed_e2e.project_manifest.models import (
    DtoSchema,
    EndpointInfo,
    HttpMethod,
    ServiceInfo,
)


class ProjectContextAnalyzer:
    """Analyzes project context for better test generation."""

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.manifest_api = ManifestAPI(project_path)
        self._cache: Dict[str, Any] = {}

    def get_service(self, name: str) -> Optional[ServiceInfo]:
        """Get service by name.

        Args:
            name: Service name

        Returns:
            Service info or None
        """
        return self.manifest_api.get_service(name)

    def find_endpoint(
        self,
        action: ActionType,
        entity: Optional[ParsedEntity] = None,
        keywords: Optional[List[str]] = None,
    ) -> Optional[EndpointInfo]:
        """Find endpoint matching action and entity.

        Args:
            action: Action type
            entity: Entity (optional)
            keywords: Additional keywords

        Returns:
            Matching endpoint or None
        """
        keywords = keywords or []

        # Map actions to HTTP methods
        method_mapping = {
            ActionType.CREATE: [HttpMethod.POST],
            ActionType.READ: [HttpMethod.GET],
            ActionType.UPDATE: [HttpMethod.PUT, HttpMethod.PATCH],
            ActionType.DELETE: [HttpMethod.DELETE],
            ActionType.LOGIN: [HttpMethod.POST],
            ActionType.LOGOUT: [HttpMethod.POST],
            ActionType.SEARCH: [HttpMethod.GET],
        }

        expected_methods = method_mapping.get(action, [])

        # Search endpoints
        for service in self.manifest_api.get_services():
            for endpoint in service.endpoints:
                # Check method match
                if expected_methods and endpoint.method not in expected_methods:
                    continue

                # Check name/path match
                searchable = f"{endpoint.name} {endpoint.path}".lower()

                # Match entity name
                if entity:
                    entity_name = entity.name.lower()
                    if entity_name in searchable:
                        return endpoint

                # Match keywords
                for keyword in keywords:
                    if keyword.lower() in searchable:
                        return endpoint

        return None

    def get_dto_for_endpoint(
        self, endpoint: EndpointInfo, direction: str = "request"
    ) -> Optional[DtoSchema]:
        """Get DTO schema for an endpoint.

        Args:
            endpoint: Endpoint info
            direction: 'request' or 'response'

        Returns:
            DTO schema or None
        """
        if direction == "request" and endpoint.request_dto:
            return self.manifest_api.get_dto(endpoint.request_dto)
        elif direction == "response" and endpoint.response_dto:
            return self.manifest_api.get_dto(endpoint.response_dto)

        return None

    def suggest_payload(
        self, dto: DtoSchema, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Suggest test payload for a DTO.

        Args:
            dto: DTO schema
            context: Optional context values

        Returns:
            Suggested payload
        """
        payload = {}
        context = context or {}

        for field in dto.fields:
            # Use context value if available
            if field.name in context:
                payload[field.name] = context[field.name]
            elif field.alias and field.alias in context:
                payload[field.alias] = context[field.alias]
            # Use default value if not required
            elif not field.required and field.default_value is not None:
                payload[field.name] = field.default_value
            # Generate test value based on type
            else:
                payload[field.name] = self._generate_test_value(field.type, field.name)

        return payload

    def _generate_test_value(self, field_type: str, field_name: str) -> Any:
        """Generate a test value based on field type.

        Args:
            field_type: Field type
            field_name: Field name

        Returns:
            Generated test value
        """
        field_type = field_type.lower()
        field_lower = field_name.lower()

        # Email
        if "email" in field_lower:
            return "test@example.com"

        # Username/User
        if any(word in field_lower for word in ["username", "user"]):
            return "testuser"

        # Password
        if "password" in field_lower:
            return "Test123!"

        # Name
        if field_lower == "name":
            return "Test Name"

        # ID
        if field_lower.endswith("id"):
            return "12345"

        # Type mappings
        if "str" in field_type:
            return "test string"
        elif "int" in field_type:
            return 42
        elif "float" in field_type:
            return 3.14
        elif "bool" in field_type:
            return True
        elif "list" in field_type or "array" in field_type:
            return []
        elif "dict" in field_type or "object" in field_type:
            return {}
        elif "datetime" in field_type:
            return "2024-01-01T00:00:00Z"

        return "test value"

    def get_auth_requirements(self, endpoint: EndpointInfo) -> Dict[str, Any]:
        """Get authentication requirements for an endpoint.

        Args:
            endpoint: Endpoint info

        Returns:
            Auth requirements
        """
        return {
            "requires_auth": endpoint.requires_auth,
            "roles": endpoint.auth_roles,
            "suggested_headers": (
                {"Authorization": "Bearer ${token}"} if endpoint.requires_auth else {}
            ),
        }


class ContextEnricher:
    """Enrich parsed natural language with project context."""

    def __init__(self, project_path: str):
        self.analyzer = ProjectContextAnalyzer(project_path)

    def enrich(
        self, parsed_test: NaturalLanguageTest, context: TranslationContext
    ) -> NaturalLanguageTest:
        """Enrich parsed test with context.

        Args:
            parsed_test: Parsed test
            context: Translation context

        Returns:
            Enriched test
        """
        # Enrich entities
        enriched_entities = self._enrich_entities(parsed_test.entities)

        # Enrich actions with endpoint info
        enriched_actions = self._enrich_actions(parsed_test.actions, enriched_entities)

        # Build complete context
        if not context.service and enriched_actions:
            context.service = self._infer_service(enriched_actions)

        if not context.endpoint and enriched_actions:
            context.endpoint = self._infer_endpoint(enriched_actions)

        if not context.http_method and enriched_actions:
            context.http_method = self._infer_http_method(enriched_actions)

        # Update parsed test
        parsed_test.entities = enriched_entities
        parsed_test.actions = enriched_actions

        return parsed_test

    def _enrich_entities(self, entities: List[ParsedEntity]) -> List[ParsedEntity]:
        """Enrich entities with additional info.

        Args:
            entities: Parsed entities

        Returns:
            Enriched entities
        """
        enriched = []

        for entity in entities:
            # Add attributes based on entity type
            if entity.entity_type == EntityType.USER:
                entity.attributes["role"] = "user"
                entity.attributes["test_credentials"] = {
                    "username": "testuser",
                    "password": "Test123!",
                }

            elif entity.entity_type == EntityType.ADMIN:
                entity.attributes["role"] = "admin"
                entity.attributes["test_credentials"] = {
                    "username": "admin",
                    "password": "Admin123!",
                }

            elif entity.entity_type == EntityType.ENDPOINT:
                # Try to find matching endpoint
                endpoint = self.analyzer.find_endpoint(
                    ActionType.READ, entity, [entity.name]
                )
                if endpoint:
                    entity.attributes["endpoint_info"] = {
                        "path": endpoint.path,
                        "method": endpoint.method.value,
                        "full_path": endpoint.full_path,
                    }

            enriched.append(entity)

        return enriched

    def _enrich_actions(
        self,
        actions: List[ParsedAction],
        entities: List[ParsedEntity],
    ) -> List[ParsedAction]:
        """Enrich actions with endpoint info.

        Args:
            actions: Parsed actions
            entities: Enriched entities

        Returns:
            Enriched actions
        """
        enriched = []

        for action in actions:
            # Find matching endpoint
            entity = next((e for e in entities if e.position > action.position), None)

            keywords = []
            if action.target:
                keywords.append(action.target)

            endpoint = self.analyzer.find_endpoint(action.action_type, entity, keywords)

            if endpoint:
                action.parameters["endpoint"] = {
                    "path": endpoint.path,
                    "method": endpoint.method.value,
                    "full_path": endpoint.full_path,
                    "requires_auth": endpoint.requires_auth,
                }

                # Add request/response DTO info
                if endpoint.request_dto:
                    dto = self.analyzer.get_dto_for_endpoint(endpoint, "request")
                    if dto:
                        action.parameters["request_dto"] = dto.name
                        action.parameters["suggested_payload"] = (
                            self.analyzer.suggest_payload(dto)
                        )

                if endpoint.response_dto:
                    dto = self.analyzer.get_dto_for_endpoint(endpoint, "response")
                    if dto:
                        action.parameters["response_dto"] = dto.name

            enriched.append(action)

        return enriched

    def _infer_service(self, actions: List[ParsedAction]) -> Optional[str]:
        """Infer service from actions.

        Args:
            actions: Enriched actions

        Returns:
            Service name or None
        """
        for action in actions:
            if "endpoint" in action.parameters:
                # Extract service from endpoint path
                path = action.parameters["endpoint"].get("path", "")
                parts = path.strip("/").split("/")
                if parts:
                    return parts[0]
        return None

    def _infer_endpoint(self, actions: List[ParsedAction]) -> Optional[str]:
        """Infer endpoint from actions.

        Args:
            actions: Enriched actions

        Returns:
            Endpoint path or None
        """
        for action in actions:
            if "endpoint" in action.parameters:
                return action.parameters["endpoint"].get("path")
        return None

    def _infer_http_method(self, actions: List[ParsedAction]) -> Optional[str]:
        """Infer HTTP method from actions.

        Args:
            actions: Enriched actions

        Returns:
            HTTP method or None
        """
        for action in actions:
            if "endpoint" in action.parameters:
                return action.parameters["endpoint"].get("method")
        return None


class TestPatternMatcher:
    """Match natural language to existing test patterns."""

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.patterns: Dict[str, Any] = {}
        self._load_patterns()

    def _load_patterns(self) -> None:
        """Load existing test patterns."""
        patterns_file = self.project_path / ".e2e" / "nlp_patterns.json"

        if patterns_file.exists():
            with open(patterns_file, "r") as f:
                self.patterns = json.load(f)

    def find_similar_tests(
        self, description: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Find tests similar to description.

        Args:
            description: Test description
            limit: Maximum number of results

        Returns:
            List of similar tests
        """
        similar = []
        description_lower = description.lower()

        for pattern_name, pattern_data in self.patterns.items():
            similarity = self._calculate_similarity(
                description_lower, pattern_data.get("description", "").lower()
            )

            if similarity > 0.5:  # Threshold
                similar.append(
                    {
                        "name": pattern_name,
                        "similarity": similarity,
                        "data": pattern_data,
                    }
                )

        # Sort by similarity
        similar.sort(key=lambda x: x["similarity"], reverse=True)

        return similar[:limit]

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score (0.0 to 1.0)
        """
        # Simple word overlap similarity
        words1 = set(text1.split())
        words2 = set(text2.split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union)

    def save_pattern(self, name: str, description: str, code: str) -> None:
        """Save a test pattern.

        Args:
            name: Pattern name
            description: Natural language description
            code: Generated code
        """
        self.patterns[name] = {
            "description": description,
            "code": code,
            "usage_count": 0,
        }

        self._save_patterns()

    def _save_patterns(self) -> None:
        """Save patterns to file."""
        patterns_file = self.project_path / ".e2e"
        patterns_file.mkdir(parents=True, exist_ok=True)
        patterns_file = patterns_file / "nlp_patterns.json"

        with open(patterns_file, "w") as f:
            json.dump(self.patterns, f, indent=2)


class RequirementsTracer:
    """Trace requirements to generated tests."""

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.requirements: Dict[str, Any] = {}

    def link_to_requirement(
        self, test_name: str, requirement_id: str, description: str
    ) -> Dict[str, Any]:
        """Link a test to a requirement.

        Args:
            test_name: Test name
            requirement_id: Requirement ID
            description: Requirement description

        Returns:
            Traceability link
        """
        link = {
            "test_name": test_name,
            "requirement_id": requirement_id,
            "requirement_description": description,
            "created_at": str(Path().stat().st_mtime),
        }

        if requirement_id not in self.requirements:
            self.requirements[requirement_id] = {
                "description": description,
                "tests": [],
            }

        self.requirements[requirement_id]["tests"].append(test_name)

        return link

    def get_test_requirements(self, test_name: str) -> List[Dict[str, Any]]:
        """Get requirements linked to a test.

        Args:
            test_name: Test name

        Returns:
            List of requirements
        """
        linked_requirements = []

        for req_id, req_data in self.requirements.items():
            if test_name in req_data.get("tests", []):
                linked_requirements.append(
                    {
                        "id": req_id,
                        "description": req_data["description"],
                    }
                )

        return linked_requirements

    def generate_traceability_matrix(self) -> Dict[str, Any]:
        """Generate traceability matrix.

        Returns:
            Traceability matrix
        """
        return {
            "total_requirements": len(self.requirements),
            "requirements_with_tests": sum(
                1 for req in self.requirements.values() if req.get("tests")
            ),
            "matrix": self.requirements,
        }
