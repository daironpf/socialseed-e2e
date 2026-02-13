"""Domain Model Understanding module.

This module provides deep understanding of the domain model including:
- Entity hierarchies and inheritance
- Value objects and aggregates
- Domain services and repositories
- Bounded contexts
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


class DomainElementType(str, Enum):
    """Types of domain elements."""

    ENTITY = "entity"
    VALUE_OBJECT = "value_object"
    AGGREGATE_ROOT = "aggregate_root"
    DOMAIN_SERVICE = "domain_service"
    REPOSITORY = "repository"
    FACTORY = "factory"
    DOMAIN_EVENT = "domain_event"
    VALUE = "value"


class RelationshipType(str, Enum):
    """Types of domain relationships."""

    INHERITANCE = "inheritance"
    COMPOSITION = "composition"
    ASSOCIATION = "association"
    DEPENDENCY = "dependency"
    REALIZATION = "realization"


@dataclass
class DomainAttribute:
    """Attribute of a domain element."""

    name: str
    type: str
    required: bool = True
    is_collection: bool = False
    description: Optional[str] = None
    constraints: List[str] = field(default_factory=list)


@dataclass
class DomainMethod:
    """Method of a domain element."""

    name: str
    parameters: List[Dict[str, str]] = field(default_factory=list)
    return_type: Optional[str] = None
    description: Optional[str] = None
    is_query: bool = False
    is_command: bool = False


@dataclass
class DomainElement:
    """A domain element (entity, value object, etc.)."""

    name: str
    element_type: DomainElementType
    description: str
    attributes: List[DomainAttribute] = field(default_factory=list)
    methods: List[DomainMethod] = field(default_factory=list)
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class DomainRelationship:
    """Relationship between domain elements."""

    source: str
    target: str
    relationship_type: RelationshipType
    cardinality: str = "1:1"  # 1:1, 1:N, N:M
    description: Optional[str] = None


@dataclass
class BoundedContext:
    """A bounded context in the domain."""

    name: str
    description: str
    elements: List[str] = field(default_factory=list)
    relationships: List[str] = field(default_factory=list)
    responsibilities: List[str] = field(default_factory=list)


@dataclass
class DomainModel:
    """Complete domain model."""

    elements: List[DomainElement] = field(default_factory=list)
    relationships: List[DomainRelationship] = field(default_factory=list)
    bounded_contexts: List[BoundedContext] = field(default_factory=list)
    terminology: Dict[str, str] = field(default_factory=dict)


class DomainModelUnderstanding:
    """Analyzer for domain model understanding."""

    # DDD pattern indicators
    ENTITY_INDICATORS = [
        r"class\s+\w+.*Entity",
        r"@Entity",
        r"@entity",
        r"@Document",
        r"extends\s+.*Entity",
        r"extends\s+.*Model",
    ]

    VALUE_OBJECT_INDICATORS = [
        r"class\s+\w+.*Value",
        r"@ValueObject",
        r"@Embedded",
        r"@embeddable",
    ]

    AGGREGATE_INDICATORS = [
        r"class\s+\w+.*Aggregate",
        r"@AggregateRoot",
        r"rootEntity",
    ]

    REPOSITORY_INDICATORS = [
        r"class\s+\w+.*Repository",
        r"interface\s+\w+.*Repository",
        r"@Repository",
        r"@repository",
        r"extends\s+JpaRepository",
        r"extends\s+MongoRepository",
    ]

    SERVICE_INDICATORS = [
        r"class\s+\w+.*Service",
        r"@Service",
        r"@service",
        r"class\s+\w+.*DomainService",
    ]

    DOMAIN_EVENT_INDICATORS = [
        r"class\s+\w+.*Event",
        r"@DomainEvent",
        r"class\s+\w+.*Occurred",
        r"class\s+\w+.*Happened",
    ]

    def __init__(self, project_root: Path):
        """Initialize the domain model analyzer.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root)
        self.model = DomainModel()

    def analyze(self) -> DomainModel:
        """Run complete domain model analysis.

        Returns:
            DomainModel with all detected elements
        """
        self._extract_domain_elements()
        self._extract_relationships()
        self._identify_bounded_contexts()
        self._build_terminology()

        return self.model

    def _extract_domain_elements(self) -> None:
        """Extract domain elements from code."""
        for file_path in self._get_source_files():
            try:
                content = file_path.read_text(encoding="utf-8")
                self._analyze_file(file_path, content)
            except Exception:
                continue

    def _get_source_files(self) -> List[Path]:
        """Get all source files."""
        source_files = []

        for pattern in ["**/*.py", "**/*.java", "**/*.kt", "**/*.cs"]:
            source_files.extend(self.project_root.glob(pattern))

        # Filter out test files
        filtered = []
        for f in source_files:
            path_str = str(f)
            if any(skip in path_str for skip in ["test", "__pycache__", ".git"]):
                continue
            filtered.append(f)

        return filtered

    def _analyze_file(self, file_path: Path, content: str) -> None:
        """Analyze a single file for domain elements."""
        lines = content.split("\n")

        for line_num, line in enumerate(lines, 1):
            # Check for entities
            element_type = self._detect_element_type(line)

            if element_type:
                class_name = self._extract_class_name(line)
                if class_name:
                    element = DomainElement(
                        name=class_name,
                        element_type=element_type,
                        description=f"Detected {element_type.value} from {file_path.name}",
                        file_path=str(file_path.relative_to(self.project_root)),
                        line_number=line_num,
                    )

                    # Extract attributes and methods
                    element.attributes = self._extract_attributes(content, class_name)
                    element.methods = self._extract_methods(content, class_name)

                    self.model.elements.append(element)

    def _detect_element_type(self, line: str) -> Optional[DomainElementType]:
        """Detect the type of domain element from a line."""
        for indicator in self.ENTITY_INDICATORS:
            if re.search(indicator, line, re.IGNORECASE):
                return DomainElementType.ENTITY

        for indicator in self.VALUE_OBJECT_INDICATORS:
            if re.search(indicator, line, re.IGNORECASE):
                return DomainElementType.VALUE_OBJECT

        for indicator in self.AGGREGATE_INDICATORS:
            if re.search(indicator, line, re.IGNORECASE):
                return DomainElementType.AGGREGATE_ROOT

        for indicator in self.REPOSITORY_INDICATORS:
            if re.search(indicator, line, re.IGNORECASE):
                return DomainElementType.REPOSITORY

        for indicator in self.SERVICE_INDICATORS:
            if re.search(indicator, line, re.IGNORECASE):
                return DomainElementType.DOMAIN_SERVICE

        for indicator in self.DOMAIN_EVENT_INDICATORS:
            if re.search(indicator, line, re.IGNORECASE):
                return DomainElementType.DOMAIN_EVENT

        return None

    def _extract_class_name(self, line: str) -> Optional[str]:
        """Extract class name from a line."""
        patterns = [
            r"class\s+(\w+)",
            r"interface\s+(\w+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                return match.group(1)

        return None

    def _extract_attributes(
        self, content: str, class_name: str
    ) -> List[DomainAttribute]:
        """Extract attributes from a class."""
        attrs = []

        # Find class section
        class_pattern = rf"class\s+{class_name}[^(]*\([^)]*\):"
        match = re.search(class_pattern, content)

        if match:
            start_pos = match.end()
            # Get next 50 lines
            section = content[start_pos : start_pos + 5000]

            # Python attributes
            attr_pattern = r"(?:self\.)?(\w+):\s*(\w+)"
            for match in re.finditer(attr_pattern, section):
                name, type_str = match.groups()
                if not name.startswith("_") and name not in ["cls", "self"]:
                    attrs.append(
                        DomainAttribute(
                            name=name,
                            type=type_str,
                            required=True,
                        )
                    )

        return attrs[:10]  # Limit to 10

    def _extract_methods(self, content: str, class_name: str) -> List[DomainMethod]:
        """Extract methods from a class."""
        methods = []

        # Python methods
        method_pattern = r"def\s+(\w+)\s*\(self[^)]*\)(?:\s*->\s*(\w+))?"
        for match in re.finditer(method_pattern, content):
            name, return_type = match.groups()
            if not name.startswith("_"):
                methods.append(
                    DomainMethod(
                        name=name,
                        return_type=return_type,
                        is_query=name.startswith("get")
                        or name.startswith("find")
                        or name.startswith("is"),
                        is_command=name.startswith("create")
                        or name.startswith("update")
                        or name.startswith("delete"),
                    )
                )

        return methods[:10]

    def _extract_relationships(self) -> None:
        """Extract relationships between domain elements."""
        for element in self.model.elements:
            # Find inheritance relationships
            self._find_inheritance(element)

            # Find composition relationships
            self._find_composition(element)

            # Find associations
            self._find_associations(element)

    def _find_inheritance(self, element: DomainElement) -> None:
        """Find inheritance relationships."""
        if not element.file_path:
            return

        try:
            file_path = self.project_root / element.file_path
            content = file_path.read_text(encoding="utf-8")

            # Look for class inheritance
            pattern = rf"class\s+{element.name}\([^)]*\)"
            match = re.search(pattern, content)

            if match:
                parent_classes = match.group(0).split("(")[1].rstrip(")").split(",")
                for parent in parent_classes:
                    parent = parent.strip()
                    # Check if parent is a known domain element
                    for other in self.model.elements:
                        if other.name == parent and other.name != element.name:
                            relationship = DomainRelationship(
                                source=element.name,
                                target=other.name,
                                relationship_type=RelationshipType.INHERITANCE,
                                description=f"{element.name} inherits from {other.name}",
                            )
                            self.model.relationships.append(relationship)

        except Exception:
            pass

    def _find_composition(self, element: DomainElement) -> None:
        """Find composition relationships."""
        for attr in element.attributes:
            # Check if attribute type is another domain element
            for other in self.model.elements:
                if (
                    other.name.lower() in attr.type.lower()
                    and other.name != element.name
                ):
                    cardinality = "1:N" if attr.is_collection else "1:1"
                    relationship = DomainRelationship(
                        source=element.name,
                        target=other.name,
                        relationship_type=RelationshipType.COMPOSITION,
                        cardinality=cardinality,
                        description=f"{element.name} contains {other.name}",
                    )
                    self.model.relationships.append(relationship)

    def _find_associations(self, element: DomainElement) -> None:
        """Find association relationships through method parameters."""
        for method in element.methods:
            for param in method.parameters:
                param_type = param.get("type", "")
                for other in self.model.elements:
                    if (
                        other.name.lower() in param_type.lower()
                        and other.name != element.name
                    ):
                        relationship = DomainRelationship(
                            source=element.name,
                            target=other.name,
                            relationship_type=RelationshipType.ASSOCIATION,
                            description=f"{element.name} uses {other.name} in {method.name}",
                        )
                        self.model.relationships.append(relationship)

    def _identify_bounded_contexts(self) -> None:
        """Identify bounded contexts in the domain."""
        # Group elements by directory structure
        context_groups: Dict[str, List[str]] = {}

        for element in self.model.elements:
            if element.file_path:
                # Use directory as context boundary
                parts = element.file_path.split("/")
                if len(parts) > 1:
                    context_name = parts[0]
                    if context_name not in context_groups:
                        context_groups[context_name] = []
                    context_groups[context_name].append(element.name)

        # Create bounded contexts for significant groups
        for context_name, elements in context_groups.items():
            if len(elements) >= 2:
                context = BoundedContext(
                    name=context_name.replace("_", " ").title(),
                    description=f"Domain context: {context_name}",
                    elements=elements,
                )
                self.model.bounded_contexts.append(context)

        # Add functional contexts
        self._add_functional_contexts()

    def _add_functional_contexts(self) -> None:
        """Add bounded contexts based on functional areas."""
        functional_areas = {
            "user_management": ["User", "Profile", "Account", "Role", "Permission"],
            "order_management": ["Order", "OrderItem", "Cart", "Checkout", "Payment"],
            "inventory": ["Product", "Stock", "Inventory", "Warehouse", "Category"],
            "notification": ["Notification", "Email", "SMS", "Message", "Alert"],
            "reporting": ["Report", "Analytics", "Dashboard", "Metric"],
        }

        for area_name, keywords in functional_areas.items():
            matching_elements = []

            for element in self.model.elements:
                if any(kw.lower() in element.name.lower() for kw in keywords):
                    matching_elements.append(element.name)

            if len(matching_elements) >= 2:
                context = BoundedContext(
                    name=area_name.replace("_", " ").title(),
                    description=f"Functional area: {area_name.replace('_', ' ')}",
                    elements=matching_elements,
                )
                self.model.bounded_contexts.append(context)

    def _build_terminology(self) -> None:
        """Build domain terminology dictionary."""
        terminology = {}

        for element in self.model.elements:
            # Add element name with description
            terminology[element.name] = element.description

            # Add method names
            for method in element.methods:
                terminology[f"{element.name}.{method.name}"] = (
                    method.description or f"Method of {element.name}"
                )

        self.model.terminology = terminology

    def get_entity_hierarchy(self) -> Dict[str, List[str]]:
        """Get the entity inheritance hierarchy.

        Returns:
            Dictionary mapping entities to their children
        """
        hierarchy = {}

        for rel in self.model.relationships:
            if rel.relationship_type == RelationshipType.INHERITANCE:
                if rel.target not in hierarchy:
                    hierarchy[rel.target] = []
                hierarchy[rel.target].append(rel.source)

        return hierarchy

    def get_aggregate_roots(self) -> List[DomainElement]:
        """Get all aggregate root elements.

        Returns:
            List of aggregate root elements
        """
        return [
            e
            for e in self.model.elements
            if e.element_type == DomainElementType.AGGREGATE_ROOT
        ]

    def get_repositories_for_entity(self, entity_name: str) -> List[DomainElement]:
        """Find repositories for a given entity.

        Args:
            entity_name: Name of the entity

        Returns:
            List of repositories
        """
        repositories = []

        for element in self.model.elements:
            if element.element_type == DomainElementType.REPOSITORY:
                if entity_name.lower() in element.name.lower():
                    repositories.append(element)

        return repositories

    def get_domain_summary(self) -> Dict[str, Any]:
        """Get a summary of the domain model.

        Returns:
            Dictionary with domain summary
        """
        return {
            "total_elements": len(self.model.elements),
            "total_relationships": len(self.model.relationships),
            "total_contexts": len(self.model.bounded_contexts),
            "element_types": {
                et.value: len([e for e in self.model.elements if e.element_type == et])
                for et in DomainElementType
            },
            "bounded_contexts": [c.name for c in self.model.bounded_contexts],
            "aggregate_roots": [e.name for e in self.get_aggregate_roots()],
        }
