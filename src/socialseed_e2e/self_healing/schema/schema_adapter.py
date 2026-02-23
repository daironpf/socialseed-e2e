"""
Schema adapter for self-healing tests.

Adapts tests to schema changes automatically.
"""

import uuid
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional

from ..models import (
    ChangeType,
    HealingSuggestion,
    HealingType,
    SchemaChange,
    TestFailure,
)


class SchemaAdapter:
    """Adapts tests to API schema changes.

    Detects schema changes and suggests adaptations:
    - Field renaming
    - Field removal
    - Type changes
    - Structure changes

    Example:
        adapter = SchemaAdapter()

        # Detect changes between schema versions
        changes = adapter.detect_changes(old_schema, new_schema)

        for change in changes:
            suggestion = adapter.generate_adaptation(change, test_file)
    """

    def __init__(self):
        """Initialize schema adapter."""
        self.schema_history: Dict[str, List[Dict[str, Any]]] = {}
        self.adaptation_history: List[HealingSuggestion] = []

    def detect_changes(
        self,
        old_schema: Dict[str, Any],
        new_schema: Dict[str, Any],
        schema_name: str = "api",
    ) -> List[SchemaChange]:
        """Detect changes between schema versions.

        Args:
            old_schema: Previous schema version
            new_schema: Current schema version
            schema_name: Name of the schema

        Returns:
            List of detected changes
        """
        changes = []

        # Flatten schemas for comparison
        old_fields = self._flatten_schema(old_schema)
        new_fields = self._flatten_schema(new_schema)

        old_keys = set(old_fields.keys())
        new_keys = set(new_fields.keys())

        # Detect removed fields
        for field in old_keys - new_keys:
            changes.append(
                SchemaChange(
                    change_type=ChangeType.FIELD_REMOVED,
                    field_path=field,
                    old_value=str(old_fields[field].get("type", "unknown")),
                    severity="high",
                    description=f"Field '{field}' was removed from schema",
                )
            )

        # Detect added fields
        for field in new_keys - old_keys:
            changes.append(
                SchemaChange(
                    change_type=ChangeType.FIELD_ADDED,
                    field_path=field,
                    new_value=str(new_fields[field].get("type", "unknown")),
                    severity="low",
                    description=f"Field '{field}' was added to schema",
                )
            )

        # Detect modified fields
        for field in old_keys & new_keys:
            old_type = old_fields[field].get("type")
            new_type = new_fields[field].get("type")

            if old_type != new_type:
                changes.append(
                    SchemaChange(
                        change_type=ChangeType.TYPE_CHANGED,
                        field_path=field,
                        old_value=str(old_type),
                        new_value=str(new_type),
                        severity="high",
                        description=f"Field '{field}' type changed from {old_type} to {new_type}",
                    )
                )

            # Check for renaming (same position, similar name)
            if self._might_be_renamed(
                field, old_keys, new_keys, old_fields, new_fields
            ):
                changes.append(
                    SchemaChange(
                        change_type=ChangeType.FIELD_RENAMED,
                        field_path=field,
                        old_value=field,
                        severity="medium",
                        description=f"Field '{field}' may have been renamed",
                    )
                )

        return changes

    def generate_adaptation(
        self,
        change: SchemaChange,
        test_file_content: str,
    ) -> Optional[HealingSuggestion]:
        """Generate adaptation suggestion for a schema change.

        Args:
            change: Schema change to adapt to
            test_file_content: Current test file content

        Returns:
            Healing suggestion or None
        """
        if change.change_type == ChangeType.FIELD_REMOVED:
            return self._adapt_field_removal(change, test_file_content)

        elif change.change_type == ChangeType.FIELD_ADDED:
            return self._adapt_field_addition(change, test_file_content)

        elif change.change_type == ChangeType.TYPE_CHANGED:
            return self._adapt_type_change(change, test_file_content)

        elif change.change_type == ChangeType.FIELD_RENAMED:
            return self._adapt_field_rename(change, test_file_content)

        return None

    def analyze_failure_for_schema_change(
        self,
        failure: TestFailure,
        schema_changes: List[SchemaChange],
    ) -> List[HealingSuggestion]:
        """Analyze test failure and suggest schema adaptations.

        Args:
            failure: Test failure information
            schema_changes: Detected schema changes

        Returns:
            List of healing suggestions
        """
        suggestions = []

        for change in schema_changes:
            # Check if error message references the changed field
            if self._is_field_in_error(failure.error_message, change.field_path):
                suggestion = self._generate_failure_adaptation(change, failure)
                if suggestion:
                    suggestions.append(suggestion)

        return suggestions

    def record_schema_version(
        self,
        schema_name: str,
        schema: Dict[str, Any],
    ):
        """Record a schema version for history tracking.

        Args:
            schema_name: Name of the schema
            schema: Schema definition
        """
        import hashlib
        import json

        schema_hash = hashlib.md5(
            json.dumps(schema, sort_keys=True).encode()
        ).hexdigest()

        if schema_name not in self.schema_history:
            self.schema_history[schema_name] = []

        history = self.schema_history[schema_name]

        # Only record if different from last version
        if not history or history[-1].get("hash") != schema_hash:
            history.append(
                {
                    "hash": schema_hash,
                    "schema": schema,
                    "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
                }
            )

    def _flatten_schema(
        self,
        schema: Dict[str, Any],
        prefix: str = "",
    ) -> Dict[str, Dict[str, Any]]:
        """Flatten nested schema structure.

        Args:
            schema: Schema to flatten
            prefix: Field path prefix

        Returns:
            Flattened field dictionary
        """
        result = {}

        properties = schema.get("properties", {})
        for name, prop in properties.items():
            path = f"{prefix}.{name}" if prefix else name
            result[path] = prop

            # Recurse into nested objects
            if "properties" in prop:
                result.update(self._flatten_schema(prop, path))

        return result

    def _might_be_renamed(
        self,
        field: str,
        old_keys: set,
        new_keys: set,
        old_fields: Dict,
        new_fields: Dict,
    ) -> bool:
        """Check if a field might have been renamed.

        Args:
            field: Field to check
            old_keys: Old schema keys
            new_keys: New schema keys
            old_fields: Old field definitions
            new_fields: New field definitions

        Returns:
            True if field might be renamed
        """
        # Simple heuristic: similar names with same type
        field_type = old_fields.get(field, {}).get("type")

        for new_key in new_keys - old_keys:
            new_type = new_fields.get(new_key, {}).get("type")
            if new_type == field_type:
                similarity = SequenceMatcher(None, field, new_key).ratio()
                if similarity > 0.6:
                    return True

        return False

    def _is_field_in_error(self, error_message: str, field_path: str) -> bool:
        """Check if field is referenced in error message.

        Args:
            error_message: Error message to check
            field_path: Field path to look for

        Returns:
            True if field is in error
        """
        field_name = field_path.split(".")[-1]
        return (
            field_name.lower() in error_message.lower()
            or field_path.lower() in error_message.lower()
        )

    def _adapt_field_removal(
        self,
        change: SchemaChange,
        test_file_content: str,
    ) -> Optional[HealingSuggestion]:
        """Generate adaptation for field removal.

        Args:
            change: Field removal change
            test_file_content: Test file content

        Returns:
            Healing suggestion or None
        """
        field_name = change.field_path.split(".")[-1]

        # Check if field is actually used in tests
        if field_name not in test_file_content:
            return None

        return HealingSuggestion(
            id=str(uuid.uuid4()),
            healing_type=HealingType.SCHEMA_ADAPTATION,
            change_type=ChangeType.FIELD_REMOVED,
            description=f"Remove references to deleted field '{change.field_path}'",
            code_patch=f"""# Schema Adaptation: Field Removed
# Field '{change.field_path}' was removed from API

# Option 1: Remove field references
# - Delete assertions for '{field_name}'
# - Remove field from test data

# Option 2: Use alternative field
# - Replace with equivalent field if available

# Before:
assert response["{field_name}"] == expected_value

# After:
# Field removed - update test accordingly
# assert response.get("{field_name}") is None  # Verify field is gone
""",
            confidence=0.9,
            affected_files=[],
            auto_applicable=False,  # Field removal needs manual review
        )

    def _adapt_field_addition(
        self,
        change: SchemaChange,
        test_file_content: str,
    ) -> Optional[HealingSuggestion]:
        """Generate adaptation for field addition.

        Args:
            change: Field addition change
            test_file_content: Test file content

        Returns:
            Healing suggestion or None
        """
        return HealingSuggestion(
            id=str(uuid.uuid4()),
            healing_type=HealingType.SCHEMA_ADAPTATION,
            change_type=ChangeType.FIELD_ADDED,
            description=f"Consider adding assertions for new field '{change.field_path}'",
            code_patch=f"""# Schema Adaptation: New Field
# Field '{change.field_path}' was added to API

# Consider adding test coverage:
# assert "{change.field_path.split(".")[-1]}" in response
# assert response["{change.field_path.split(".")[-1]}"] is not None
""",
            confidence=0.5,  # Low confidence - just informational
            affected_files=[],
            auto_applicable=False,
        )

    def _adapt_type_change(
        self,
        change: SchemaChange,
        test_file_content: str,
    ) -> Optional[HealingSuggestion]:
        """Generate adaptation for type change.

        Args:
            change: Type change
            test_file_content: Test file content

        Returns:
            Healing suggestion or None
        """
        field_name = change.field_path.split(".")[-1]

        return HealingSuggestion(
            id=str(uuid.uuid4()),
            healing_type=HealingType.SCHEMA_ADAPTATION,
            change_type=ChangeType.TYPE_CHANGED,
            description=f"Update assertions for type change: {change.old_value} -> {change.new_value}",
            code_patch=f"""# Schema Adaptation: Type Changed
# Field '{change.field_path}' type changed from {change.old_value} to {change.new_value}

# Update assertions to match new type:
# Old: assert isinstance(response["{field_name}"], {change.old_value})
# New: assert isinstance(response["{field_name}"], {change.new_value})

# May need to update test data as well
""",
            confidence=0.8,
            affected_files=[],
            auto_applicable=False,
        )

    def _adapt_field_rename(
        self,
        change: SchemaChange,
        test_file_content: str,
    ) -> Optional[HealingSuggestion]:
        """Generate adaptation for field rename.

        Args:
            change: Field rename change
            test_file_content: Test file content

        Returns:
            Healing suggestion or None
        """
        old_name = change.field_path.split(".")[-1]

        return HealingSuggestion(
            id=str(uuid.uuid4()),
            healing_type=HealingType.SCHEMA_ADAPTATION,
            change_type=ChangeType.FIELD_RENAMED,
            description=f"Field '{change.field_path}' may have been renamed - review and update",
            code_patch=f"""# Schema Adaptation: Possible Field Rename
# Field '{change.field_path}' appears to be renamed

# Review the API schema and update field references:
# - Find the new field name in the schema
# - Update all references from '{old_name}' to new_name

# Example:
# Old: response["{old_name}"]
# New: response["new_field_name"]
""",
            confidence=0.6,
            affected_files=[],
            auto_applicable=False,
        )

    def _generate_failure_adaptation(
        self,
        change: SchemaChange,
        failure: TestFailure,
    ) -> Optional[HealingSuggestion]:
        """Generate adaptation suggestion based on failure and change.

        Args:
            change: Schema change
            failure: Test failure

        Returns:
            Healing suggestion or None
        """
        # Delegate to specific adaptation method
        return self.generate_adaptation(change, "")
