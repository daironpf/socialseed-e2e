"""Contract Migration and Breaking Change Detection.

This module provides tools for detecting breaking changes between contract
versions, generating migration paths, and handling deprecations.

Example:
    >>> from socialseed_e2e.contract_testing import ContractMigrationAnalyzer
    >>> analyzer = ContractMigrationAnalyzer()
    >>> result = analyzer.analyze_migration(old_contract, new_contract)
    >>> print(result.breaking_changes)
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class ChangeSeverity(Enum):
    """Severity levels for contract changes."""

    INFO = "info"  # No impact, informational only
    WARNING = "warning"  # Potential concern, review recommended
    BREAKING = "breaking"  # Breaking change, requires consumer update
    CRITICAL = "critical"  # Critical breaking change, immediate action needed


class ChangeType(Enum):
    """Types of contract changes."""

    # Endpoint changes
    ENDPOINT_ADDED = "endpoint_added"
    ENDPOINT_REMOVED = "endpoint_removed"
    ENDPOINT_MODIFIED = "endpoint_modified"

    # Request changes
    REQUEST_FIELD_ADDED = "request_field_added"
    REQUEST_FIELD_REMOVED = "request_field_removed"
    REQUEST_FIELD_MODIFIED = "request_field_modified"
    REQUEST_BODY_CHANGED = "request_body_changed"

    # Response changes
    RESPONSE_FIELD_ADDED = "response_field_added"
    RESPONSE_FIELD_REMOVED = "response_field_removed"
    RESPONSE_FIELD_MODIFIED = "response_field_modified"
    RESPONSE_STATUS_CHANGED = "response_status_changed"
    RESPONSE_BODY_CHANGED = "response_body_changed"

    # Schema changes
    TYPE_CHANGED = "type_changed"
    REQUIRED_FIELD_ADDED = "required_field_added"
    REQUIRED_FIELD_REMOVED = "required_field_removed"
    CONSTRAINT_CHANGED = "constraint_changed"

    # Metadata changes
    VERSION_CHANGED = "version_changed"
    DESCRIPTION_CHANGED = "description_changed"
    DEPRECATION_ADDED = "deprecation_added"


@dataclass
class ContractChange:
    """Represents a single change between contract versions."""

    change_type: ChangeType
    severity: ChangeSeverity
    path: str  # JSON path to the changed element
    description: str
    old_value: Any = None
    new_value: Any = None
    suggestion: str = ""
    affected_consumers: List[str] = field(default_factory=list)


@dataclass
class MigrationPath:
    """Represents a migration path for a breaking change."""

    change: ContractChange
    steps: List[str]  # Ordered list of migration steps
    code_example: str = ""  # Code example for migration
    timeline: str = ""  # Suggested migration timeline
    automated_fix_available: bool = False


@dataclass
class DeprecationNotice:
    """Represents a deprecation notice for a contract element."""

    path: str
    element_type: str  # endpoint, field, parameter, etc.
    description: str
    deprecated_since: datetime
    removal_date: Optional[datetime] = None
    replacement: Optional[str] = None
    migration_guide: str = ""


@dataclass
class MigrationAnalysisResult:
    """Complete result of contract migration analysis."""

    old_version: str
    new_version: str
    changes: List[ContractChange] = field(default_factory=list)
    breaking_changes: List[ContractChange] = field(default_factory=list)
    migration_paths: List[MigrationPath] = field(default_factory=list)
    deprecations: List[DeprecationNotice] = field(default_factory=list)
    summary: str = ""
    compatibility_score: float = 1.0  # 0.0 to 1.0

    def has_breaking_changes(self) -> bool:
        """Check if there are any breaking changes."""
        return len(self.breaking_changes) > 0

    def get_changes_by_severity(self, severity: ChangeSeverity) -> List[ContractChange]:
        """Get all changes of a specific severity."""
        return [c for c in self.changes if c.severity == severity]

    def get_changes_by_type(self, change_type: ChangeType) -> List[ContractChange]:
        """Get all changes of a specific type."""
        return [c for c in self.changes if c.change_type == change_type]


class ContractMigrationAnalyzer:
    """Analyzes contract migrations and detects breaking changes.

    Provides comprehensive analysis of contract changes including:
    - Breaking change detection
    - Migration path generation
    - Deprecation tracking
    - Compatibility scoring

    Example:
        >>> analyzer = ContractMigrationAnalyzer()
        >>> result = analyzer.analyze_migration(
        ...     old_contract={...},
        ...     new_contract={...},
        ...     old_version="1.0.0",
        ...     new_version="2.0.0"
        ... )
        >>> if result.has_breaking_changes():
        ...     for change in result.breaking_changes:
        ...         print(f"BREAKING: {change.description}")
    """

    def __init__(self):
        """Initialize the migration analyzer."""
        self._change_detectors = [
            self._detect_endpoint_changes,
            self._detect_request_changes,
            self._detect_response_changes,
            self._detect_schema_changes,
            self._detect_metadata_changes,
        ]

    def analyze_migration(
        self,
        old_contract: Union[str, Dict[str, Any]],
        new_contract: Union[str, Dict[str, Any]],
        old_version: str = "unknown",
        new_version: str = "unknown",
    ) -> MigrationAnalysisResult:
        """Analyze migration between two contract versions.

        Args:
            old_contract: Old contract content (JSON string or dict)
            new_contract: New contract content (JSON string or dict)
            old_version: Old contract version
            new_version: New contract version

        Returns:
            MigrationAnalysisResult with all changes and recommendations
        """
        # Parse contracts
        old = self._parse_contract(old_contract)
        new = self._parse_contract(new_contract)

        # Detect all changes
        all_changes = []
        for detector in self._change_detectors:
            changes = detector(old, new)
            all_changes.extend(changes)

        # Separate breaking changes
        breaking_changes = [
            c
            for c in all_changes
            if c.severity in (ChangeSeverity.BREAKING, ChangeSeverity.CRITICAL)
        ]

        # Generate migration paths for breaking changes
        migration_paths = [
            self._generate_migration_path(change) for change in breaking_changes
        ]

        # Detect deprecations
        deprecations = self._detect_deprecations(old, new)

        # Calculate compatibility score
        compatibility_score = self._calculate_compatibility_score(all_changes)

        # Generate summary
        summary = self._generate_summary(
            old_version, new_version, all_changes, breaking_changes
        )

        return MigrationAnalysisResult(
            old_version=old_version,
            new_version=new_version,
            changes=all_changes,
            breaking_changes=breaking_changes,
            migration_paths=migration_paths,
            deprecations=deprecations,
            summary=summary,
            compatibility_score=compatibility_score,
        )

    def _parse_contract(self, contract: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Parse contract from string or dict."""
        if isinstance(contract, str):
            return json.loads(contract)
        return contract

    def _detect_endpoint_changes(
        self, old: Dict[str, Any], new: Dict[str, Any]
    ) -> List[ContractChange]:
        """Detect changes in API endpoints."""
        changes = []

        old_interactions = {
            i.get("description", ""): i for i in old.get("interactions", [])
        }
        new_interactions = {
            i.get("description", ""): i for i in new.get("interactions", [])
        }

        # Check for removed endpoints (breaking)
        for desc, interaction in old_interactions.items():
            if desc not in new_interactions:
                changes.append(
                    ContractChange(
                        change_type=ChangeType.ENDPOINT_REMOVED,
                        severity=ChangeSeverity.BREAKING,
                        path=f"interactions[{desc}]",
                        description=f"Endpoint '{desc}' was removed",
                        old_value=interaction.get("request", {}).get("path"),
                        suggestion="Consumers must stop using this endpoint or migrate to replacement",
                    )
                )

        # Check for added endpoints (info)
        for desc, interaction in new_interactions.items():
            if desc not in old_interactions:
                changes.append(
                    ContractChange(
                        change_type=ChangeType.ENDPOINT_ADDED,
                        severity=ChangeSeverity.INFO,
                        path=f"interactions[{desc}]",
                        description=f"New endpoint '{desc}' was added",
                        new_value=interaction.get("request", {}).get("path"),
                        suggestion="Consumers can optionally use this new endpoint",
                    )
                )

        return changes

    def _detect_request_changes(
        self, old: Dict[str, Any], new: Dict[str, Any]
    ) -> List[ContractChange]:
        """Detect changes in request specifications."""
        changes = []

        old_interactions = {
            i.get("description", ""): i for i in old.get("interactions", [])
        }
        new_interactions = {
            i.get("description", ""): i for i in new.get("interactions", [])
        }

        for desc in old_interactions:
            if desc not in new_interactions:
                continue

            old_req = old_interactions[desc].get("request", {})
            new_req = new_interactions[desc].get("request", {})

            # Check method changes
            if old_req.get("method") != new_req.get("method"):
                changes.append(
                    ContractChange(
                        change_type=ChangeType.ENDPOINT_MODIFIED,
                        severity=ChangeSeverity.BREAKING,
                        path=f"interactions[{desc}].request.method",
                        description=f"HTTP method changed for '{desc}'",
                        old_value=old_req.get("method"),
                        new_value=new_req.get("method"),
                        suggestion="Update client code to use new HTTP method",
                    )
                )

            # Check path changes
            if old_req.get("path") != new_req.get("path"):
                changes.append(
                    ContractChange(
                        change_type=ChangeType.ENDPOINT_MODIFIED,
                        severity=ChangeSeverity.BREAKING,
                        path=f"interactions[{desc}].request.path",
                        description=f"Path changed for '{desc}'",
                        old_value=old_req.get("path"),
                        new_value=new_req.get("path"),
                        suggestion="Update all references to this endpoint path",
                    )
                )

            # Check body changes
            if old_req.get("body") != new_req.get("body"):
                body_changes = self._analyze_body_changes(
                    old_req.get("body"),
                    new_req.get("body"),
                    f"interactions[{desc}].request.body",
                )
                changes.extend(body_changes)

        return changes

    def _detect_response_changes(
        self, old: Dict[str, Any], new: Dict[str, Any]
    ) -> List[ContractChange]:
        """Detect changes in response specifications."""
        changes = []

        old_interactions = {
            i.get("description", ""): i for i in old.get("interactions", [])
        }
        new_interactions = {
            i.get("description", ""): i for i in new.get("interactions", [])
        }

        for desc in old_interactions:
            if desc not in new_interactions:
                continue

            old_res = old_interactions[desc].get("response", {})
            new_res = new_interactions[desc].get("response", {})

            # Check status code changes
            if old_res.get("status") != new_res.get("status"):
                severity = ChangeSeverity.BREAKING
                # Status code changes are usually breaking unless it's adding new success codes
                if old_res.get("status") in [200, 201] and new_res.get("status") in [
                    200,
                    201,
                ]:
                    severity = ChangeSeverity.WARNING

                changes.append(
                    ContractChange(
                        change_type=ChangeType.RESPONSE_STATUS_CHANGED,
                        severity=severity,
                        path=f"interactions[{desc}].response.status",
                        description=f"Response status code changed for '{desc}'",
                        old_value=old_res.get("status"),
                        new_value=new_res.get("status"),
                        suggestion="Update client code to handle new status code",
                    )
                )

            # Check body changes
            if old_res.get("body") != new_res.get("body"):
                body_changes = self._analyze_body_changes(
                    old_res.get("body"),
                    new_res.get("body"),
                    f"interactions[{desc}].response.body",
                    is_response=True,
                )
                changes.extend(body_changes)

        return changes

    def _detect_schema_changes(
        self, old: Dict[str, Any], new: Dict[str, Any]
    ) -> List[ContractChange]:
        """Detect changes in data schemas."""
        changes = []

        # This would require JSON Schema analysis
        # For now, we'll focus on the interaction-level changes
        # which cover most practical cases

        return changes

    def _detect_metadata_changes(
        self, old: Dict[str, Any], new: Dict[str, Any]
    ) -> List[ContractChange]:
        """Detect changes in contract metadata."""
        changes = []

        old_meta = old.get("metadata", {})
        new_meta = new.get("metadata", {})

        # Version change
        if old_meta.get("version") != new_meta.get("version"):
            changes.append(
                ContractChange(
                    change_type=ChangeType.VERSION_CHANGED,
                    severity=ChangeSeverity.INFO,
                    path="metadata.version",
                    description="Contract version updated",
                    old_value=old_meta.get("version"),
                    new_value=new_meta.get("version"),
                )
            )

        return changes

    def _analyze_body_changes(
        self, old_body: Any, new_body: Any, path: str, is_response: bool = False
    ) -> List[ContractChange]:
        """Analyze changes in request/response bodies."""
        changes = []

        if not isinstance(old_body, dict) or not isinstance(new_body, dict):
            if old_body != new_body:
                change_type = (
                    ChangeType.RESPONSE_BODY_CHANGED
                    if is_response
                    else ChangeType.REQUEST_BODY_CHANGED
                )
                changes.append(
                    ContractChange(
                        change_type=change_type,
                        severity=ChangeSeverity.WARNING,
                        path=path,
                        description=f"Body structure changed at {path}",
                        suggestion="Review and update body handling code",
                    )
                )
            return changes

        # Check for removed fields
        for key in old_body:
            if key not in new_body:
                severity = (
                    ChangeSeverity.BREAKING if is_response else ChangeSeverity.WARNING
                )
                change_type = (
                    ChangeType.RESPONSE_FIELD_REMOVED
                    if is_response
                    else ChangeType.REQUEST_FIELD_REMOVED
                )
                changes.append(
                    ContractChange(
                        change_type=change_type,
                        severity=severity,
                        path=f"{path}.{key}",
                        description=f"Field '{key}' was removed from {'response' if is_response else 'request'}",
                        old_value=old_body[key],
                        suggestion=f"Remove dependency on field '{key}' from consumer code"
                        if is_response
                        else f"Stop sending field '{key}'",
                    )
                )

        # Check for added fields
        for key in new_body:
            if key not in old_body:
                severity = (
                    ChangeSeverity.INFO if is_response else ChangeSeverity.BREAKING
                )
                change_type = (
                    ChangeType.RESPONSE_FIELD_ADDED
                    if is_response
                    else ChangeType.REQUEST_FIELD_ADDED
                )
                changes.append(
                    ContractChange(
                        change_type=change_type,
                        severity=severity,
                        path=f"{path}.{key}",
                        description=f"New field '{key}' added to {'response' if is_response else 'request'}",
                        new_value=new_body[key],
                        suggestion=f"Can start using field '{key}'"
                        if is_response
                        else f"Must update to provide field '{key}'",
                    )
                )

        # Check for modified fields
        for key in old_body:
            if key in new_body and old_body[key] != new_body[key]:
                change_type = (
                    ChangeType.RESPONSE_FIELD_MODIFIED
                    if is_response
                    else ChangeType.REQUEST_FIELD_MODIFIED
                )
                changes.append(
                    ContractChange(
                        change_type=change_type,
                        severity=ChangeSeverity.WARNING,
                        path=f"{path}.{key}",
                        description=f"Field '{key}' modified in {'response' if is_response else 'request'}",
                        old_value=old_body[key],
                        new_value=new_body[key],
                        suggestion=f"Review usage of field '{key}'",
                    )
                )

        return changes

    def _detect_deprecations(
        self, old: Dict[str, Any], new: Dict[str, Any]
    ) -> List[DeprecationNotice]:
        """Detect deprecation notices in the contract."""
        deprecations = []

        # Check for deprecation annotations in metadata
        new_meta = new.get("metadata", {})
        if "deprecations" in new_meta:
            for dep in new_meta["deprecations"]:
                deprecations.append(
                    DeprecationNotice(
                        path=dep.get("path", ""),
                        element_type=dep.get("type", "unknown"),
                        description=dep.get("description", ""),
                        deprecated_since=datetime.fromisoformat(
                            dep.get("since", datetime.utcnow().isoformat())
                        ),
                        removal_date=datetime.fromisoformat(dep["removal"])
                        if "removal" in dep
                        else None,
                        replacement=dep.get("replacement"),
                        migration_guide=dep.get("migration_guide", ""),
                    )
                )

        return deprecations

    def _generate_migration_path(self, change: ContractChange) -> MigrationPath:
        """Generate migration path for a breaking change."""
        steps = []
        code_example = ""
        timeline = "Immediate action required"
        automated = False

        if change.change_type == ChangeType.ENDPOINT_REMOVED:
            steps = [
                "Identify all usages of the removed endpoint",
                "Find replacement endpoint or functionality",
                "Update client code to use replacement",
                "Test thoroughly before deploying",
            ]
            code_example = f"""
# Old code
response = requests.get("{change.old_value}")

# New code
response = requests.get("<replacement_endpoint>")
"""

        elif change.change_type == ChangeType.RESPONSE_FIELD_REMOVED:
            field_name = change.path.split(".")[-1]
            steps = [
                f"Remove all references to field '{field_name}'",
                "Update data models and validation logic",
                "Test to ensure no runtime errors",
            ]
            code_example = f"""
# Remove field access
data = response.json()
# OLD: value = data.get("{field_name}")
# NEW: Use alternative field or remove logic
"""

        elif change.change_type == ChangeType.REQUEST_FIELD_ADDED:
            field_name = change.path.split(".")[-1]
            steps = [
                f"Add required field '{field_name}' to all requests",
                "Update request builders and validators",
                "Test with provider to ensure compatibility",
            ]
            code_example = f"""
# Add required field
payload = {{
    # ... existing fields
    "{field_name}": <value>,  # NEW: Required field
}}
"""

        return MigrationPath(
            change=change,
            steps=steps,
            code_example=code_example,
            timeline=timeline,
            automated_fix_available=automated,
        )

    def _calculate_compatibility_score(self, changes: List[ContractChange]) -> float:
        """Calculate compatibility score based on changes."""
        if not changes:
            return 1.0

        # Weight by severity
        weights = {
            ChangeSeverity.INFO: 0.0,
            ChangeSeverity.WARNING: 0.1,
            ChangeSeverity.BREAKING: 0.5,
            ChangeSeverity.CRITICAL: 1.0,
        }

        total_weight = sum(weights.get(c.severity, 0.1) for c in changes)
        score = max(0.0, 1.0 - (total_weight / len(changes)))

        return round(score, 2)

    def _generate_summary(
        self,
        old_version: str,
        new_version: str,
        all_changes: List[ContractChange],
        breaking_changes: List[ContractChange],
    ) -> str:
        """Generate human-readable summary of migration."""
        lines = [
            f"Contract Migration Analysis: {old_version} → {new_version}",
            "",
            f"Total changes: {len(all_changes)}",
            f"Breaking changes: {len(breaking_changes)}",
            "",
        ]

        if breaking_changes:
            lines.append("⚠️  BREAKING CHANGES DETECTED")
            lines.append("")
            for change in breaking_changes[:5]:  # Show first 5
                lines.append(f"  • {change.description}")
            if len(breaking_changes) > 5:
                lines.append(f"  ... and {len(breaking_changes) - 5} more")
        else:
            lines.append("✅ No breaking changes detected")

        return "\n".join(lines)

    def generate_migration_guide(
        self, result: MigrationAnalysisResult, format: str = "markdown"
    ) -> str:
        """Generate a comprehensive migration guide.

        Args:
            result: Migration analysis result
            format: Output format (markdown, html, json)

        Returns:
            Formatted migration guide
        """
        if format == "markdown":
            return self._generate_markdown_guide(result)
        elif format == "json":
            return json.dumps(
                {
                    "old_version": result.old_version,
                    "new_version": result.new_version,
                    "compatibility_score": result.compatibility_score,
                    "breaking_changes": [
                        {
                            "type": c.change_type.value,
                            "severity": c.severity.value,
                            "description": c.description,
                            "suggestion": c.suggestion,
                        }
                        for c in result.breaking_changes
                    ],
                    "migration_paths": [
                        {
                            "change": mp.change.description,
                            "steps": mp.steps,
                            "code_example": mp.code_example,
                        }
                        for mp in result.migration_paths
                    ],
                },
                indent=2,
            )
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _generate_markdown_guide(self, result: MigrationAnalysisResult) -> str:
        """Generate markdown migration guide."""
        lines = [
            f"# Migration Guide: {result.old_version} → {result.new_version}",
            "",
            f"**Compatibility Score:** {result.compatibility_score * 100:.0f}%",
            "",
            "## Summary",
            "",
            result.summary,
            "",
        ]

        if result.breaking_changes:
            lines.extend(
                [
                    "## Breaking Changes",
                    "",
                ]
            )
            for change in result.breaking_changes:
                lines.extend(
                    [
                        f"### {change.description}",
                        "",
                        f"**Severity:** {change.severity.value}",
                        f"**Path:** `{change.path}`",
                        "",
                        f"**Suggestion:** {change.suggestion}",
                        "",
                    ]
                )

            lines.extend(
                [
                    "## Migration Steps",
                    "",
                ]
            )
            for path in result.migration_paths:
                lines.extend(
                    [
                        f"### {path.change.description}",
                        "",
                        "**Steps:**",
                        "",
                    ]
                )
                for i, step in enumerate(path.steps, 1):
                    lines.append(f"{i}. {step}")
                lines.append("")

                if path.code_example:
                    lines.extend(
                        [
                            "**Code Example:**",
                            "",
                            "```python",
                            path.code_example,
                            "```",
                            "",
                        ]
                    )

        if result.deprecations:
            lines.extend(
                [
                    "## Deprecations",
                    "",
                ]
            )
            for dep in result.deprecations:
                lines.extend(
                    [
                        f"### {dep.element_type}: `{dep.path}`",
                        "",
                        dep.description,
                        "",
                        f"**Deprecated since:** {dep.deprecated_since.isoformat()}",
                    ]
                )
                if dep.removal_date:
                    lines.append(
                        f"**Scheduled removal:** {dep.removal_date.isoformat()}"
                    )
                if dep.replacement:
                    lines.append(f"**Replacement:** {dep.replacement}")
                lines.append("")

        return "\n".join(lines)
