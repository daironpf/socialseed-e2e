"""Capability Registry for AI Agent Communication Protocol.

This module provides capability negotiation and registration for
AI agents communicating with the framework.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class CapabilityLevel(str, Enum):
    """Capability support levels."""

    FULL = "full"
    PARTIAL = "partial"
    EXPERIMENTAL = "experimental"
    NONE = "none"


class RequirementLevel(str, Enum):
    """Requirement levels."""

    REQUIRED = "required"
    OPTIONAL = "optional"
    PREFERRED = "preferred"


@dataclass
class Capability:
    """A capability that can be registered."""

    name: str
    description: str
    level: CapabilityLevel = CapabilityLevel.FULL
    version: str = "1.0.0"
    parameters: Dict[str, Any] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert capability to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "level": self.level.value,
            "version": self.version,
            "parameters": self.parameters,
            "constraints": self.constraints,
            "dependencies": self.dependencies,
            "examples": self.examples,
        }


@dataclass
class Requirement:
    """A requirement for capability negotiation."""

    name: str
    level: RequirementLevel
    description: str = ""
    min_version: Optional[str] = None
    max_version: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert requirement to dictionary."""
        return {
            "name": self.name,
            "level": self.level.value,
            "description": self.description,
            "min_version": self.min_version,
            "max_version": self.max_version,
        }


@dataclass
class CapabilityNegotiation:
    """Result of capability negotiation."""

    success: bool
    agreed_capabilities: List[str] = field(default_factory=list)
    rejected_capabilities: List[str] = field(default_factory=list)
    missing_requirements: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    negotiated_parameters: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert negotiation result to dictionary."""
        return {
            "success": self.success,
            "agreed_capabilities": self.agreed_capabilities,
            "rejected_capabilities": self.rejected_capabilities,
            "missing_requirements": self.missing_requirements,
            "warnings": self.warnings,
            "negotiated_parameters": self.negotiated_parameters,
        }


class CapabilityRegistry:
    """Registry for framework and agent capabilities."""

    def __init__(self):
        """Initialize the capability registry."""
        self.framework_capabilities: Dict[str, Capability] = {}
        self.agent_capabilities: Dict[str, Capability] = {}
        self.framework_requirements: List[Requirement] = []
        self.agent_requirements: List[Requirement] = []

        # Register default framework capabilities
        self._register_default_capabilities()

    def _register_default_capabilities(self) -> None:
        """Register default framework capabilities."""
        defaults = [
            Capability(
                name="test_generation",
                description="Generate automated tests from API specifications",
                level=CapabilityLevel.FULL,
                parameters={
                    "supported_formats": ["python", "javascript", "java"],
                    "max_tests_per_request": 100,
                },
            ),
            Capability(
                name="test_execution",
                description="Execute E2E tests with reporting",
                level=CapabilityLevel.FULL,
                parameters={
                    "parallel_execution": True,
                    "max_parallel_workers": 10,
                    "supported_protocols": ["http", "https", "grpc"],
                },
            ),
            Capability(
                name="manifest_generation",
                description="Generate AI Project Manifest from codebase",
                level=CapabilityLevel.FULL,
                parameters={
                    "supported_languages": [
                        "python",
                        "java",
                        "javascript",
                        "typescript",
                        "csharp",
                    ],
                    "smart_sync": True,
                },
            ),
            Capability(
                name="deep_context_analysis",
                description="Deep context awareness and semantic analysis",
                level=CapabilityLevel.FULL,
            ),
            Capability(
                name="business_logic_inference",
                description="Infer business logic from endpoints",
                level=CapabilityLevel.FULL,
            ),
            Capability(
                name="semantic_search",
                description="Vector-based semantic search on manifest",
                level=CapabilityLevel.EXPERIMENTAL,
            ),
            Capability(
                name="code_fixing",
                description="Automatically fix failing tests",
                level=CapabilityLevel.PARTIAL,
                parameters={
                    "auto_apply": False,
                    "requires_approval": True,
                },
            ),
            Capability(
                name="security_testing",
                description="Security fuzzing and vulnerability testing",
                level=CapabilityLevel.EXPERIMENTAL,
            ),
        ]

        for cap in defaults:
            self.register_framework_capability(cap)

    def register_framework_capability(self, capability: Capability) -> None:
        """Register a framework capability.

        Args:
            capability: Capability to register
        """
        self.framework_capabilities[capability.name] = capability

    def register_agent_capability(self, capability: Capability) -> None:
        """Register an agent capability.

        Args:
            capability: Capability to register
        """
        self.agent_capabilities[capability.name] = capability

    def add_framework_requirement(self, requirement: Requirement) -> None:
        """Add a framework requirement.

        Args:
            requirement: Requirement to add
        """
        self.framework_requirements.append(requirement)

    def add_agent_requirement(self, requirement: Requirement) -> None:
        """Add an agent requirement.

        Args:
            requirement: Requirement to add
        """
        self.agent_requirements.append(requirement)

    def get_framework_capability(self, name: str) -> Optional[Capability]:
        """Get a framework capability by name.

        Args:
            name: Capability name

        Returns:
            Capability or None
        """
        return self.framework_capabilities.get(name)

    def get_agent_capability(self, name: str) -> Optional[Capability]:
        """Get an agent capability by name.

        Args:
            name: Capability name

        Returns:
            Capability or None
        """
        return self.agent_capabilities.get(name)

    def list_framework_capabilities(self) -> List[Capability]:
        """List all framework capabilities.

        Returns:
            List of capabilities
        """
        return list(self.framework_capabilities.values())

    def list_agent_capabilities(self) -> List[Capability]:
        """List all agent capabilities.

        Returns:
            List of capabilities
        """
        return list(self.agent_capabilities.values())

    def negotiate_capabilities(
        self, agent_offered: List[str], agent_requirements: List[Requirement] = None
    ) -> CapabilityNegotiation:
        """Negotiate capabilities between framework and agent.

        Args:
            agent_offered: Capabilities the agent offers
            agent_requirements: Requirements the agent has

        Returns:
            Negotiation result
        """
        agreed = []
        rejected = []
        missing = []
        warnings = []
        parameters = {}

        # Check what framework requires vs what agent offers
        for req in self.framework_requirements:
            if req.name in agent_offered:
                if req.level == RequirementLevel.REQUIRED:
                    agreed.append(req.name)
                else:
                    agreed.append(req.name)
            elif req.level == RequirementLevel.REQUIRED:
                missing.append(req.name)
            elif req.level == RequirementLevel.PREFERRED:
                warnings.append(
                    f"Preferred capability '{req.name}' not offered by agent"
                )

        # Check what agent requires vs what framework has
        if agent_requirements:
            for req in agent_requirements:
                if req.name in self.framework_capabilities:
                    cap = self.framework_capabilities[req.name]
                    # Check version compatibility
                    if (
                        req.min_version
                        and self._version_compare(cap.version, req.min_version) < 0
                    ):
                        rejected.append(f"{req.name} (version too old)")
                    elif (
                        req.max_version
                        and self._version_compare(cap.version, req.max_version) > 0
                    ):
                        rejected.append(f"{req.name} (version too new)")
                    else:
                        agreed.append(req.name)
                        # Include capability parameters
                        parameters[req.name] = cap.parameters
                elif req.level == RequirementLevel.REQUIRED:
                    missing.append(req.name)
                else:
                    warnings.append(
                        f"Agent requirement '{req.name}' not supported by framework"
                    )

        # Check offered capabilities that aren't required
        for cap_name in agent_offered:
            if cap_name not in agreed and cap_name in self.framework_capabilities:
                agreed.append(cap_name)

        # Determine success
        success = len(missing) == 0

        return CapabilityNegotiation(
            success=success,
            agreed_capabilities=agreed,
            rejected_capabilities=rejected,
            missing_requirements=missing,
            warnings=warnings,
            negotiated_parameters=parameters,
        )

    def _version_compare(self, v1: str, v2: str) -> int:
        """Compare two version strings.

        Args:
            v1: First version
            v2: Second version

        Returns:
            -1 if v1 < v2, 0 if equal, 1 if v1 > v2
        """
        parts1 = [int(x) for x in v1.split(".")]
        parts2 = [int(x) for x in v2.split(".")]

        for p1, p2 in zip(parts1, parts2):
            if p1 < p2:
                return -1
            if p1 > p2:
                return 1

        if len(parts1) < len(parts2):
            return -1
        if len(parts1) > len(parts2):
            return 1

        return 0

    def check_capability_compatibility(
        self, capability_name: str, parameters: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """Check if parameters are compatible with a capability.

        Args:
            capability_name: Name of the capability
            parameters: Parameters to check

        Returns:
            Tuple of (is_compatible, error_messages)
        """
        cap = self.framework_capabilities.get(capability_name)
        if not cap:
            return False, [f"Capability '{capability_name}' not found"]

        errors = []

        # Check constraints
        for key, constraint in cap.constraints.items():
            if key in parameters:
                value = parameters[key]
                if not self._validate_constraint(value, constraint):
                    errors.append(
                        f"Parameter '{key}' violates constraint: {constraint}"
                    )

        return len(errors) == 0, errors

    def _validate_constraint(self, value: Any, constraint: Any) -> bool:
        """Validate a value against a constraint.

        Args:
            value: Value to validate
            constraint: Constraint to check against

        Returns:
            True if valid
        """
        if isinstance(constraint, list):
            return value in constraint
        if isinstance(constraint, dict):
            if "min" in constraint and value < constraint["min"]:
                return False
            if "max" in constraint and value > constraint["max"]:
                return False
            if "type" in constraint and not isinstance(value, eval(constraint["type"])):
                return False
        return True

    def get_capability_matrix(self) -> Dict[str, Any]:
        """Get a matrix of all capabilities.

        Returns:
            Capability matrix
        """
        return {
            "framework": {
                name: cap.to_dict() for name, cap in self.framework_capabilities.items()
            },
            "agent": {
                name: cap.to_dict() for name, cap in self.agent_capabilities.items()
            },
            "framework_requirements": [
                r.to_dict() for r in self.framework_requirements
            ],
            "agent_requirements": [r.to_dict() for r in self.agent_requirements],
        }

    def has_capability(self, name: str) -> bool:
        """Check if framework has a capability.

        Args:
            name: Capability name

        Returns:
            True if capability exists
        """
        return name in self.framework_capabilities

    def get_capability_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a capability.

        Args:
            name: Capability name

        Returns:
            Capability info or None
        """
        cap = self.framework_capabilities.get(name)
        if cap:
            return {
                **cap.to_dict(),
                "available": True,
                "level_description": self._get_level_description(cap.level),
            }
        return None

    def _get_level_description(self, level: CapabilityLevel) -> str:
        """Get human-readable description of capability level."""
        descriptions = {
            CapabilityLevel.FULL: "Fully supported and production-ready",
            CapabilityLevel.PARTIAL: "Partially supported with some limitations",
            CapabilityLevel.EXPERIMENTAL: "Experimental feature, may have issues",
            CapabilityLevel.NONE: "Not supported",
        }
        return descriptions.get(level, "Unknown")
