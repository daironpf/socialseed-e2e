"""Test Strategy Planner for AI-driven test planning.

This module analyzes codebases and generates comprehensive testing strategies
based on code analysis, business impact, and risk assessment.
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from socialseed_e2e.ai_orchestrator.models import (
    RiskFactor,
    TestCase,
    TestPriority,
    TestStrategy,
    TestType,
)
from socialseed_e2e.project_manifest.api import ManifestAPI
from socialseed_e2e.project_manifest.models import EndpointInfo, ProjectKnowledge, ServiceInfo

logger = logging.getLogger(__name__)


class CodeAnalyzer:
    """Analyzes code to determine test requirements."""

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.manifest_api = ManifestAPI(project_path)

    def analyze_complexity(self, endpoint: EndpointInfo) -> float:
        """Analyze endpoint complexity score (0.0 to 1.0).

        Args:
            endpoint: Endpoint to analyze

        Returns:
            Complexity score between 0.0 and 1.0
        """
        score = 0.0

        # Factor: Number of parameters
        param_count = len(endpoint.parameters)
        if param_count > 5:
            score += 0.3
        elif param_count > 3:
            score += 0.2
        elif param_count > 0:
            score += 0.1

        # Factor: Authentication required
        if endpoint.requires_auth:
            score += 0.15

        # Factor: Multiple roles
        if len(endpoint.auth_roles) > 1:
            score += 0.1

        # Factor: Has request/response DTOs (more complex data handling)
        if endpoint.request_dto and endpoint.response_dto:
            score += 0.2
        elif endpoint.request_dto or endpoint.response_dto:
            score += 0.1

        # Factor: Path complexity (path parameters)
        path_param_count = endpoint.path.count("{") + endpoint.path.count("<")
        score += path_param_count * 0.05

        return min(score, 1.0)

    def analyze_business_impact(self, endpoint: EndpointInfo) -> float:
        """Analyze business impact score (0.0 to 1.0).

        Args:
            endpoint: Endpoint to analyze

        Returns:
            Impact score between 0.0 and 1.0
        """
        score = 0.0

        # Critical operations
        critical_patterns = [
            "payment",
            "billing",
            "auth",
            "login",
            "register",
            "order",
            "purchase",
            "checkout",
            "delete",
            "admin",
        ]

        endpoint_lower = f"{endpoint.path} {endpoint.name}".lower()

        for pattern in critical_patterns:
            if pattern in endpoint_lower:
                score += 0.25
                break

        # Write operations have higher impact
        if endpoint.method in ["POST", "PUT", "DELETE", "PATCH"]:
            score += 0.2

        # Public endpoints (no auth) may have wider impact
        if not endpoint.requires_auth and endpoint.method != "GET":
            score += 0.15

        return min(score, 1.0)

    def analyze_change_frequency(self, endpoint: EndpointInfo) -> float:
        """Analyze how frequently an endpoint changes (0.0 to 1.0).

        Uses git history if available, otherwise uses heuristics.

        Args:
            endpoint: Endpoint to analyze

        Returns:
            Change frequency score between 0.0 and 1.0
        """
        # This is a simplified implementation
        # In production, this would use git history analysis

        score = 0.0

        # Newer endpoints (based on naming conventions) may change more
        if any(word in endpoint.name.lower() for word in ["v2", "new", "beta", "experimental"]):
            score += 0.3

        # Complex endpoints tend to change more
        if len(endpoint.parameters) > 3:
            score += 0.2

        return min(score, 1.0)


class StrategyPlanner:
    """Plans comprehensive testing strategies based on codebase analysis."""

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.analyzer = CodeAnalyzer(project_path)
        self.manifest_api = ManifestAPI(project_path)

    def generate_strategy(
        self,
        name: str,
        description: str,
        target_services: Optional[List[str]] = None,
        test_types: Optional[List[TestType]] = None,
    ) -> TestStrategy:
        """Generate a complete testing strategy.

        Args:
            name: Strategy name
            description: Strategy description
            target_services: Specific services to include (None = all)
            test_types: Types of tests to include (None = all)

        Returns:
            Complete test strategy
        """
        logger.info(f"Generating test strategy: {name}")

        test_types = test_types or list(TestType)

        # Get project knowledge
        knowledge = self.manifest_api.manifest

        # Filter services
        services = knowledge.services
        if target_services:
            services = [s for s in services if s.name in target_services]

        # Generate test cases
        test_cases: List[TestCase] = []
        for service in services:
            service_tests = self._generate_service_tests(service, test_types)
            test_cases.extend(service_tests)

        # Prioritize and order tests
        prioritized_tests = self._prioritize_tests(test_cases)

        # Create parallelization groups
        parallel_groups = self._create_parallelization_groups(prioritized_tests)

        # Calculate total estimated duration
        total_duration = sum(tc.estimated_duration_ms for tc in prioritized_tests)

        # Generate strategy ID
        strategy_id = self._generate_strategy_id(name, target_services)

        strategy = TestStrategy(
            id=strategy_id,
            name=name,
            description=description,
            target_services=[s.name for s in services],
            test_cases=prioritized_tests,
            execution_order=[tc.id for tc in prioritized_tests],
            parallelization_groups=parallel_groups,
            total_estimated_duration_ms=total_duration,
            coverage_targets=self._calculate_coverage_targets(services),
        )

        logger.info(f"Generated strategy with {len(test_cases)} test cases")
        return strategy

    def _generate_service_tests(
        self, service: ServiceInfo, test_types: List[TestType]
    ) -> List[TestCase]:
        """Generate test cases for a service.

        Args:
            service: Service to generate tests for
            test_types: Types of tests to generate

        Returns:
            List of test cases
        """
        test_cases: List[TestCase] = []

        for endpoint in service.endpoints:
            # Generate E2E tests for each endpoint
            if TestType.E2E in test_types:
                e2e_tests = self._generate_endpoint_e2e_tests(service, endpoint)
                test_cases.extend(e2e_tests)

            # Generate integration tests
            if TestType.INTEGRATION in test_types:
                integration_tests = self._generate_integration_tests(service, endpoint)
                test_cases.extend(integration_tests)

            # Generate security tests
            if TestType.SECURITY in test_types:
                security_tests = self._generate_security_tests(service, endpoint)
                test_cases.extend(security_tests)

        return test_cases

    def _generate_endpoint_e2e_tests(
        self, service: ServiceInfo, endpoint: EndpointInfo
    ) -> List[TestCase]:
        """Generate E2E test cases for an endpoint.

        Args:
            service: Service containing the endpoint
            endpoint: Endpoint to generate tests for

        Returns:
            List of E2E test cases
        """
        test_cases: List[TestCase] = []

        # Happy path test
        test_id = f"{service.name}_{endpoint.method}_{endpoint.name}_happy"
        complexity = self.analyzer.analyze_complexity(endpoint)
        impact = self.analyzer.analyze_business_impact(endpoint)
        change_freq = self.analyzer.analyze_change_frequency(endpoint)

        risk_factors = [
            RiskFactor(
                factor_type="complexity",
                score=complexity,
                description=f"Endpoint complexity score based on {len(endpoint.parameters)} parameters",
            ),
            RiskFactor(
                factor_type="business_impact",
                score=impact,
                description="Business impact based on endpoint purpose",
            ),
            RiskFactor(
                factor_type="change_frequency",
                score=change_freq,
                description="Estimated change frequency",
            ),
        ]

        # Calculate priority based on risk factors
        avg_risk = sum(rf.score for rf in risk_factors) / len(risk_factors)
        if avg_risk > 0.7:
            priority = TestPriority.CRITICAL
        elif avg_risk > 0.5:
            priority = TestPriority.HIGH
        elif avg_risk > 0.3:
            priority = TestPriority.MEDIUM
        else:
            priority = TestPriority.LOW

        happy_test = TestCase(
            id=test_id,
            name=f"{endpoint.name} - Happy Path",
            description=f"Valid {endpoint.method} request to {endpoint.path}",
            test_type=TestType.E2E,
            priority=priority,
            service=service.name,
            module=f"services/{service.name}/modules/e2e/{endpoint.name}.py",
            endpoint=endpoint.path,
            http_method=endpoint.method.value,
            risk_factors=risk_factors,
            estimated_duration_ms=int(1000 + complexity * 2000),
            tags=["e2e", "happy-path", service.name],
        )
        test_cases.append(happy_test)

        # Error handling tests
        if endpoint.parameters:
            error_test = TestCase(
                id=f"{service.name}_{endpoint.method}_{endpoint.name}_validation",
                name=f"{endpoint.name} - Validation Errors",
                description=f"Invalid inputs for {endpoint.method} {endpoint.path}",
                test_type=TestType.E2E,
                priority=TestPriority.HIGH if impact > 0.5 else TestPriority.MEDIUM,
                service=service.name,
                module=f"services/{service.name}/modules/e2e/{endpoint.name}_validation.py",
                endpoint=endpoint.path,
                http_method=endpoint.method.value,
                risk_factors=risk_factors,
                estimated_duration_ms=1500,
                tags=["e2e", "validation", service.name],
            )
            test_cases.append(error_test)

        # Authentication test (if auth required)
        if endpoint.requires_auth:
            auth_test = TestCase(
                id=f"{service.name}_{endpoint.method}_{endpoint.name}_auth",
                name=f"{endpoint.name} - Authentication",
                description=f"Unauthorized access to {endpoint.method} {endpoint.path}",
                test_type=TestType.E2E,
                priority=TestPriority.HIGH,
                service=service.name,
                module=f"services/{service.name}/modules/e2e/{endpoint.name}_auth.py",
                endpoint=endpoint.path,
                http_method=endpoint.method.value,
                risk_factors=risk_factors,
                estimated_duration_ms=1000,
                tags=["e2e", "security", "auth", service.name],
            )
            test_cases.append(auth_test)

        return test_cases

    def _generate_integration_tests(
        self, service: ServiceInfo, endpoint: EndpointInfo
    ) -> List[TestCase]:
        """Generate integration test cases.

        Args:
            service: Service containing the endpoint
            endpoint: Endpoint to generate tests for

        Returns:
            List of integration test cases
        """
        test_cases: List[TestCase] = []

        # Only generate integration tests for services with dependencies
        if service.dependencies:
            test_id = f"{service.name}_{endpoint.method}_{endpoint.name}_integration"

            test = TestCase(
                id=test_id,
                name=f"{endpoint.name} - Integration",
                description=f"Integration test for {endpoint.method} {endpoint.path}",
                test_type=TestType.INTEGRATION,
                priority=TestPriority.MEDIUM,
                service=service.name,
                module=f"services/{service.name}/modules/integration/{endpoint.name}.py",
                endpoint=endpoint.path,
                http_method=endpoint.method.value,
                estimated_duration_ms=2000,
                tags=["integration", service.name],
            )
            test_cases.append(test)

        return test_cases

    def _generate_security_tests(
        self, service: ServiceInfo, endpoint: EndpointInfo
    ) -> List[TestCase]:
        """Generate security test cases.

        Args:
            service: Service containing the endpoint
            endpoint: Endpoint to generate tests for

        Returns:
            List of security test cases
        """
        test_cases: List[TestCase] = []

        # Security tests for write operations
        if endpoint.method in ["POST", "PUT", "DELETE", "PATCH"]:
            test_id = f"{service.name}_{endpoint.method}_{endpoint.name}_security"

            test = TestCase(
                id=test_id,
                name=f"{endpoint.name} - Security",
                description=f"Security tests for {endpoint.method} {endpoint.path}",
                test_type=TestType.SECURITY,
                priority=TestPriority.HIGH,
                service=service.name,
                module=f"services/{service.name}/modules/security/{endpoint.name}.py",
                endpoint=endpoint.path,
                http_method=endpoint.method.value,
                estimated_duration_ms=1500,
                tags=["security", service.name],
            )
            test_cases.append(test)

        return test_cases

    def _prioritize_tests(self, test_cases: List[TestCase]) -> List[TestCase]:
        """Prioritize test cases based on risk factors.

        Args:
            test_cases: List of test cases to prioritize

        Returns:
            Prioritized list of test cases
        """

        def get_priority_score(test: TestCase) -> float:
            """Calculate priority score for a test."""
            priority_scores = {
                TestPriority.CRITICAL: 4.0,
                TestPriority.HIGH: 3.0,
                TestPriority.MEDIUM: 2.0,
                TestPriority.LOW: 1.0,
            }

            base_score = priority_scores[test.priority]

            # Add risk factor scores
            risk_bonus = sum(rf.score for rf in test.risk_factors) * 0.5

            # Prefer faster tests for earlier execution
            duration_penalty = test.estimated_duration_ms / 5000.0

            return base_score + risk_bonus - duration_penalty

        # Sort by priority score (descending)
        return sorted(test_cases, key=get_priority_score, reverse=True)

    def _create_parallelization_groups(self, test_cases: List[TestCase]) -> List[List[str]]:
        """Create groups of tests that can run in parallel.

        Args:
            test_cases: List of test cases

        Returns:
            List of groups (each group is a list of test IDs)
        """
        # Group tests by service (tests within same service may have dependencies)
        service_groups: Dict[str, List[str]] = {}

        for test in test_cases:
            if test.service not in service_groups:
                service_groups[test.service] = []
            service_groups[test.service].append(test.id)

        # Create parallel groups
        # Tests from different services can run in parallel
        parallel_groups: List[List[str]] = []

        for service, test_ids in service_groups.items():
            # For now, put all tests from same service in one group
            # More sophisticated dependency analysis could split further
            parallel_groups.append(test_ids)

        return parallel_groups

    def _calculate_coverage_targets(self, services: List[ServiceInfo]) -> Dict[str, float]:
        """Calculate coverage targets based on service analysis.

        Args:
            services: List of services

        Returns:
            Dictionary of coverage targets by category
        """
        total_endpoints = sum(len(s.endpoints) for s in services)

        targets = {
            "endpoint_coverage": 90.0,  # Target: 90% of endpoints tested
            "e2e_coverage": 80.0,  # Target: 80% E2E test coverage
            "integration_coverage": 70.0,  # Target: 70% integration coverage
            "security_coverage": 100.0,  # Target: 100% of write operations
        }

        if total_endpoints > 50:
            # For large projects, adjust targets
            targets["e2e_coverage"] = 70.0
            targets["integration_coverage"] = 60.0

        return targets

    def _generate_strategy_id(self, name: str, target_services: Optional[List[str]]) -> str:
        """Generate a unique strategy ID.

        Args:
            name: Strategy name
            target_services: Target services

        Returns:
            Unique strategy ID
        """
        content = f"{name}_{json.dumps(target_services, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def save_strategy(self, strategy: TestStrategy, output_path: Optional[Path] = None) -> str:
        """Save a strategy to a file.

        Args:
            strategy: Strategy to save
            output_path: Optional output path (default: .e2e/strategies/)

        Returns:
            Path to saved strategy file
        """
        if output_path is None:
            output_path = self.project_path / ".e2e" / "strategies"

        output_path.mkdir(parents=True, exist_ok=True)

        file_path = output_path / f"{strategy.id}.json"

        with open(file_path, "w") as f:
            f.write(strategy.model_dump_json(indent=2))

        logger.info(f"Strategy saved to {file_path}")
        return str(file_path)

    def load_strategy(
        self, strategy_id: str, strategies_path: Optional[Path] = None
    ) -> TestStrategy:
        """Load a strategy from file.

        Args:
            strategy_id: Strategy ID
            strategies_path: Optional path to strategies directory

        Returns:
            Loaded test strategy
        """
        if strategies_path is None:
            strategies_path = self.project_path / ".e2e" / "strategies"

        file_path = strategies_path / f"{strategy_id}.json"

        with open(file_path, "r") as f:
            data = json.load(f)

        return TestStrategy.model_validate(data)
