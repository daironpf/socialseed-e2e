"""Semantic Codebase Analyzer for deep understanding of project structure.

This module provides semantic analysis of the codebase to understand:
- Code patterns and conventions
- Domain concepts and terminology
- Business rules embedded in code
- Entity relationships and hierarchies
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


class SemanticPatternType(str, Enum):
    """Types of semantic patterns that can be detected."""

    DOMAIN_ENTITY = "domain_entity"
    BUSINESS_RULE = "business_rule"
    VALIDATION_RULE = "validation_rule"
    STATE_TRANSITION = "state_transition"
    WORKFLOW_PATTERN = "workflow_pattern"
    SECURITY_PATTERN = "security_pattern"
    DATA_ACCESS_PATTERN = "data_access_pattern"
    INTEGRATION_PATTERN = "integration_pattern"


@dataclass
class DomainConcept:
    """A domain concept detected in the codebase."""

    name: str
    concept_type: str  # entity, value_object, aggregate, service, etc.
    description: str
    attributes: List[str] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    relationships: List[Dict[str, Any]] = field(default_factory=list)
    file_path: Optional[str] = None
    confidence: float = 0.8


@dataclass
class BusinessRule:
    """A business rule extracted from code."""

    description: str
    rule_type: str  # validation, constraint, calculation, etc.
    source_file: str
    line_number: int
    entities_involved: List[str] = field(default_factory=list)
    conditions: List[str] = field(default_factory=list)
    actions: List[str] = field(default_factory=list)
    priority: str = "normal"  # high, normal, low


@dataclass
class CodePattern:
    """A detected code pattern."""

    pattern_type: SemanticPatternType
    description: str
    confidence: float
    source_files: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    related_entities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SemanticContext:
    """Complete semantic context of the codebase."""

    domain_concepts: List[DomainConcept] = field(default_factory=list)
    business_rules: List[BusinessRule] = field(default_factory=list)
    patterns: List[CodePattern] = field(default_factory=list)
    terminology: Dict[str, List[str]] = field(default_factory=dict)
    entity_hierarchies: Dict[str, List[str]] = field(default_factory=dict)


class SemanticCodebaseAnalyzer:
    """Analyzer for deep semantic understanding of codebase."""

    # Domain-related keywords to look for
    DOMAIN_KEYWORDS = [
        "user",
        "customer",
        "account",
        "profile",
        "order",
        "payment",
        "product",
        "item",
        "cart",
        "invoice",
        "transaction",
        "subscription",
        "organization",
        "team",
        "member",
        "role",
        "permission",
        "notification",
        "message",
        "email",
        "sms",
        "file",
        "document",
        "image",
        "video",
        "media",
        "category",
        "tag",
        "label",
        "metadata",
        "audit",
        "log",
        "history",
        "activity",
        "config",
        "setting",
        "preference",
        "workflow",
        "process",
        "task",
        "job",
        "queue",
        "report",
        "analytics",
        "metric",
        "dashboard",
    ]

    # Business rule indicators
    RULE_INDICATORS = [
        r"if\s+.*:\s*raise",
        r"if\s+.*:\s*return\s+False",
        r"if\s+.*:\s*raise\s+.*Error",
        r"if\s+.*:\s*raise\s+.*Exception",
        r"assert\s+",
        r"must\s+be",
        r"should\s+be",
        r"cannot\s+",
        r"must\s+not",
        r"is\s+required",
        r"@validator",
        r"@validate",
        r"validate_",
    ]

    # State transition keywords
    STATE_KEYWORDS = [
        "status",
        "state",
        "phase",
        "stage",
        "step",
        "pending",
        "active",
        "inactive",
        "completed",
        "cancelled",
        "draft",
        "published",
        "archived",
        "deleted",
        "approved",
        "rejected",
        "reviewing",
        "processing",
        "shipped",
        "delivered",
    ]

    def __init__(self, project_root: Path):
        """Initialize the semantic analyzer.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root)
        self.context = SemanticContext()
        self._domain_terms: Set[str] = set()

    def analyze(self) -> SemanticContext:
        """Run complete semantic analysis.

        Returns:
            SemanticContext with all detected information
        """
        self._extract_domain_concepts()
        self._extract_business_rules()
        self._detect_patterns()
        self._build_terminology()
        self._analyze_entity_hierarchies()

        return self.context

    def _extract_domain_concepts(self) -> None:
        """Extract domain concepts from code files."""
        for file_path in self._get_source_files():
            try:
                content = file_path.read_text(encoding="utf-8")
                self._analyze_file_for_concepts(file_path, content)
            except Exception:
                continue

    def _get_source_files(self) -> List[Path]:
        """Get all source files to analyze."""
        source_files = []

        for pattern in ["**/*.py", "**/*.java", "**/*.js", "**/*.ts"]:
            source_files.extend(self.project_root.glob(pattern))

        # Filter out test files and common directories
        filtered = []
        for f in source_files:
            path_str = str(f)
            if any(
                skip in path_str
                for skip in ["test", "__pycache__", "node_modules", ".git"]
            ):
                continue
            filtered.append(f)

        return filtered

    def _analyze_file_for_concepts(self, file_path: Path, content: str) -> None:
        """Analyze a single file for domain concepts."""
        # Look for class definitions
        class_pattern = r"(?:class|interface)\s+(\w+)"
        classes = re.findall(class_pattern, content)

        for class_name in classes:
            # Check if class name contains domain keywords
            is_domain = any(
                keyword in class_name.lower() for keyword in self.DOMAIN_KEYWORDS
            )

            if is_domain:
                # Extract attributes and methods
                attrs = self._extract_class_attributes(content, class_name)
                methods = self._extract_class_methods(content, class_name)

                concept = DomainConcept(
                    name=class_name,
                    concept_type="entity",
                    description=f"Domain entity detected from {file_path.name}",
                    attributes=attrs,
                    methods=methods,
                    file_path=str(file_path.relative_to(self.project_root)),
                    confidence=0.75 if is_domain else 0.5,
                )

                self.context.domain_concepts.append(concept)
                self._domain_terms.add(class_name.lower())

    def _extract_class_attributes(self, content: str, class_name: str) -> List[str]:
        """Extract attribute names from a class definition."""
        attrs = []

        # Python-style attributes
        attr_pattern = r"self\.(\w+)\s*="
        attrs.extend(re.findall(attr_pattern, content))

        # Pydantic/dataclass fields
        field_pattern = r"(\w+):\s*\w+(?:\s*=\s*Field"
        attrs.extend(re.findall(field_pattern, content))

        # Java-style attributes
        java_attr_pattern = r"(?:private|public|protected)\s+\w+\s+(\w+)\s*;"
        attrs.extend(re.findall(java_attr_pattern, content))

        return list(set(attrs))[:10]  # Limit to 10 attributes

    def _extract_class_methods(self, content: str, class_name: str) -> List[str]:
        """Extract method names from a class definition."""
        methods = []

        # Python methods
        method_pattern = r"def\s+(\w+)\s*\(self"
        methods.extend(re.findall(method_pattern, content))

        # Java methods
        java_method_pattern = (
            r"(?:public|private|protected)\s+(?:\w+|void)\s+(\w+)\s*\("
        )
        methods.extend(re.findall(java_method_pattern, content))

        return list(set(methods))[:10]  # Limit to 10 methods

    def _extract_business_rules(self) -> None:
        """Extract business rules from code."""
        for file_path in self._get_source_files():
            try:
                content = file_path.read_text(encoding="utf-8")
                lines = content.split("\n")

                for line_num, line in enumerate(lines, 1):
                    for indicator in self.RULE_INDICATORS:
                        if re.search(indicator, line, re.IGNORECASE):
                            # Extract surrounding context
                            context_start = max(0, line_num - 3)
                            context_end = min(len(lines), line_num + 2)
                            context = "\n".join(lines[context_start:context_end])

                            # Find entities mentioned
                            entities = self._extract_entities_from_line(line)

                            rule = BusinessRule(
                                description=self._describe_rule(line, context),
                                rule_type="validation"
                                if "valid" in line.lower()
                                else "constraint",
                                source_file=str(
                                    file_path.relative_to(self.project_root)
                                ),
                                line_number=line_num,
                                entities_involved=entities,
                                conditions=[line.strip()],
                            )

                            self.context.business_rules.append(rule)
                            break

            except Exception:
                continue

    def _extract_entities_from_line(self, line: str) -> List[str]:
        """Extract entity names from a line of code."""
        entities = []

        for concept in self.context.domain_concepts:
            if concept.name.lower() in line.lower():
                entities.append(concept.name)

        return entities

    def _describe_rule(self, line: str, context: str) -> str:
        """Generate a human-readable description of a rule."""
        line_clean = line.strip()

        if "raise" in line_clean:
            return "Validation rule: throws exception when condition met"
        elif "assert" in line_clean:
            return "Assertion: condition must be true"
        elif "required" in line_clean.lower():
            return "Field is mandatory"
        else:
            return f"Business rule detected: {line_clean[:50]}"

    def _detect_patterns(self) -> None:
        """Detect semantic patterns in the codebase."""
        patterns = []

        # Detect state machine patterns
        state_pattern = self._detect_state_machine_pattern()
        if state_pattern:
            patterns.append(state_pattern)

        # Detect repository pattern
        repo_pattern = self._detect_repository_pattern()
        if repo_pattern:
            patterns.append(repo_pattern)

        # Detect service layer pattern
        service_pattern = self._detect_service_pattern()
        if service_pattern:
            patterns.append(service_pattern)

        # Detect validation patterns
        validation_pattern = self._detect_validation_pattern()
        if validation_pattern:
            patterns.append(validation_pattern)

        self.context.patterns = patterns

    def _detect_state_machine_pattern(self) -> Optional[CodePattern]:
        """Detect state machine patterns in the code."""
        state_files = []

        for file_path in self._get_source_files():
            try:
                content = file_path.read_text(encoding="utf-8")

                # Look for state-related code
                state_indicators = [
                    r"class\s+\w+State",
                    r"status\s*=\s*[\"\'][\w]+[\"\']",
                    r"state\s*=\s*[\"\'][\w]+[\"\']",
                    r"Enum.*Status",
                    r"Enum.*State",
                ]

                for indicator in state_indicators:
                    if re.search(indicator, content, re.IGNORECASE):
                        state_files.append(
                            str(file_path.relative_to(self.project_root))
                        )
                        break

            except Exception:
                continue

        if state_files:
            return CodePattern(
                pattern_type=SemanticPatternType.STATE_TRANSITION,
                description="State machine pattern detected - entity status/state management",
                confidence=0.8,
                source_files=state_files[:5],
                examples=["Status enum", "State transitions", "Status field updates"],
            )

        return None

    def _detect_repository_pattern(self) -> Optional[CodePattern]:
        """Detect repository/data access patterns."""
        repo_files = []

        for file_path in self._get_source_files():
            try:
                content = file_path.read_text(encoding="utf-8")

                repo_indicators = [
                    r"class\s+\w+Repository",
                    r"class\s+\w+DAO",
                    r"def\s+find_by",
                    r"def\s+save\(",
                    r"def\s+delete\(",
                    r"@repository",
                ]

                for indicator in repo_indicators:
                    if re.search(indicator, content, re.IGNORECASE):
                        repo_files.append(str(file_path.relative_to(self.project_root)))
                        break

            except Exception:
                continue

        if repo_files:
            return CodePattern(
                pattern_type=SemanticPatternType.DATA_ACCESS_PATTERN,
                description="Repository pattern detected - data access abstraction layer",
                confidence=0.85,
                source_files=repo_files[:5],
                examples=[
                    "Repository classes",
                    "DAO pattern",
                    "Database access methods",
                ],
            )

        return None

    def _detect_service_pattern(self) -> Optional[CodePattern]:
        """Detect service layer patterns."""
        service_files = []

        for file_path in self._get_source_files():
            try:
                content = file_path.read_text(encoding="utf-8")

                service_indicators = [
                    r"class\s+\w+Service",
                    r"@service",
                    r"@Service",
                ]

                for indicator in service_indicators:
                    if re.search(indicator, content, re.IGNORECASE):
                        service_files.append(
                            str(file_path.relative_to(self.project_root))
                        )
                        break

            except Exception:
                continue

        if service_files:
            return CodePattern(
                pattern_type=SemanticPatternType.BUSINESS_RULE,
                description="Service layer pattern detected - business logic encapsulation",
                confidence=0.8,
                source_files=service_files[:5],
                examples=["Service classes", "Business operations"],
            )

        return None

    def _detect_validation_pattern(self) -> Optional[CodePattern]:
        """Detect validation patterns."""
        validation_files = []

        for file_path in self._get_source_files():
            try:
                content = file_path.read_text(encoding="utf-8")

                validation_indicators = [
                    r"@validator",
                    r"@validate",
                    r"validate_",
                    r"class\s+\w+Validator",
                    r"@Validation",
                ]

                for indicator in validation_indicators:
                    if re.search(indicator, content, re.IGNORECASE):
                        validation_files.append(
                            str(file_path.relative_to(self.project_root))
                        )
                        break

            except Exception:
                continue

        if validation_files:
            return CodePattern(
                pattern_type=SemanticPatternType.VALIDATION_RULE,
                description="Validation pattern detected - input/data validation",
                confidence=0.85,
                source_files=validation_files[:5],
                examples=["Validators", "Validation decorators", "Validation methods"],
            )

        return None

    def _build_terminology(self) -> None:
        """Build domain terminology dictionary."""
        terminology = {
            "entities": [],
            "actions": [],
            "attributes": [],
            "relationships": [],
        }

        for concept in self.context.domain_concepts:
            terminology["entities"].append(concept.name)
            terminology["attributes"].extend(concept.attributes)

        for rule in self.context.business_rules:
            words = rule.description.split()
            for word in words:
                if word.lower() in [
                    "create",
                    "update",
                    "delete",
                    "get",
                    "validate",
                    "process",
                ]:
                    terminology["actions"].append(word.lower())

        # Remove duplicates
        for key in terminology:
            terminology[key] = list(set(terminology[key]))[:20]

        self.context.terminology = terminology

    def _analyze_entity_hierarchies(self) -> None:
        """Analyze and build entity hierarchies."""
        hierarchies = {}

        for concept in self.context.domain_concepts:
            parent = self._find_parent_entity(concept)
            if parent:
                if parent not in hierarchies:
                    hierarchies[parent] = []
                hierarchies[parent].append(concept.name)

        self.context.entity_hierarchies = hierarchies

    def _find_parent_entity(self, concept: DomainConcept) -> Optional[str]:
        """Find parent entity for a concept based on naming."""
        name_lower = concept.name.lower()

        for other in self.context.domain_concepts:
            if other.name != concept.name:
                other_lower = other.name.lower()
                # Check if one contains the other
                if name_lower.startswith(other_lower) and len(name_lower) > len(
                    other_lower
                ):
                    return other.name

        return None

    def get_domain_summary(self) -> Dict[str, Any]:
        """Get a summary of the domain understanding."""
        return {
            "total_concepts": len(self.context.domain_concepts),
            "total_business_rules": len(self.context.business_rules),
            "total_patterns": len(self.context.patterns),
            "domain_entities": [c.name for c in self.context.domain_concepts[:10]],
            "key_business_rules": [
                r.description for r in self.context.business_rules[:5]
            ],
            "detected_patterns": [p.pattern_type.value for p in self.context.patterns],
            "terminology_categories": list(self.context.terminology.keys()),
        }

    def find_related_concepts(self, concept_name: str) -> List[DomainConcept]:
        """Find concepts related to a given concept."""
        related = []

        target = None
        for concept in self.context.domain_concepts:
            if concept.name.lower() == concept_name.lower():
                target = concept
                break

        if not target:
            return related

        for concept in self.context.domain_concepts:
            if concept.name != target.name:
                # Check for shared attributes
                shared_attrs = set(target.attributes) & set(concept.attributes)
                if shared_attrs:
                    related.append(concept)
                    continue

                # Check for name similarity
                if target.name.lower() in concept.name.lower():
                    related.append(concept)

        return related
