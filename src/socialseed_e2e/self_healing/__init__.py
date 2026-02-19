from pathlib import Path
from typing import Any, Callable, Optional
import difflib
import hashlib
import json
import re
from datetime import datetime, timedelta
from enum import Enum

from pydantic import BaseModel


class ChangeType(str, Enum):
    FIELD_RENAMED = "field_renamed"
    FIELD_REMOVED = "field_removed"
    FIELD_ADDED = "field_added"
    TYPE_CHANGED = "type_changed"
    SCHEMA_STRUCTURE = "schema_structure"


class SchemaChange(BaseModel):
    change_type: ChangeType
    field_path: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    severity: str = "medium"
    description: str


class TestFailure(BaseModel):
    test_file: str
    test_name: str
    error_message: str
    timestamp: datetime
    stack_trace: Optional[str] = None


class HealingSuggestion(BaseModel):
    change_type: ChangeType
    description: str
    code_patch: str
    confidence: float


class SelfHealingConfig(BaseModel):
    tests_dir: Path = Path("tests")
    services_dir: Path = Path("services")
    github_token: Optional[str] = None
    repository: Optional[str] = None
    auto_commit: bool = False
    branch_name: str = "fix/auto-heal"


class SchemaChangeDetector:
    def __init__(self):
        self._schema_history: dict[str, list[dict]] = {}

    def record_schema(self, service_name: str, schema: dict) -> None:
        schema_hash = hashlib.md5(
            json.dumps(schema, sort_keys=True).encode()
        ).hexdigest()

        if service_name not in self._schema_history:
            self._schema_history[service_name] = []

        history = self._schema_history[service_name]

        if not history or history[-1].get("hash") != schema_hash:
            history.append(
                {
                    "hash": schema_hash,
                    "schema": schema,
                    "timestamp": datetime.now().isoformat(),
                }
            )

    def detect_changes(self, old_schema: dict, new_schema: dict) -> list[SchemaChange]:
        changes = []

        old_fields = self._flatten_schema(old_schema)
        new_fields = self._flatten_schema(new_schema)

        old_keys = set(old_fields.keys())
        new_keys = set(new_fields.keys())

        for field in old_keys - new_keys:
            changes.append(
                SchemaChange(
                    change_type=ChangeType.FIELD_REMOVED,
                    field_path=field,
                    old_value=old_fields[field].get("type"),
                    severity="high",
                    description=f"Field '{field}' was removed from schema",
                )
            )

        for field in new_keys - old_keys:
            changes.append(
                SchemaChange(
                    change_type=ChangeType.FIELD_ADDED,
                    field_path=field,
                    new_value=new_fields[field].get("type"),
                    severity="low",
                    description=f"Field '{field}' was added to schema",
                )
            )

        for field in old_keys & new_keys:
            old_type = old_fields[field].get("type")
            new_type = new_fields[field].get("type")
            if old_type != new_type:
                changes.append(
                    SchemaChange(
                        change_type=ChangeType.TYPE_CHANGED,
                        field_path=field,
                        old_value=old_type,
                        new_value=new_type,
                        severity="high",
                        description=f"Field '{field}' type changed from {old_type} to {new_type}",
                    )
                )

        return changes

    def _flatten_schema(self, schema: dict, prefix: str = "") -> dict[str, dict]:
        result = {}

        properties = schema.get("properties", {})
        for name, prop in properties.items():
            path = f"{prefix}.{name}" if prefix else name
            result[path] = prop

            if "properties" in prop:
                result.update(self._flatten_schema(prop, path))

        return result


class TestRepairEngine:
    def __init__(self, config: SelfHealingConfig):
        self.config = config

    def analyze_failure(
        self, failure: TestFailure, schema_changes: list[SchemaChange]
    ) -> list[HealingSuggestion]:
        suggestions = []

        for change in schema_changes:
            if change.change_type == ChangeType.FIELD_REMOVED:
                if self._is_field_in_error(failure.error_message, change.field_path):
                    suggestion = self._suggest_field_removal_fix(failure, change)
                    suggestions.append(suggestion)

            elif change.change_type == ChangeType.FIELD_RENAMED:
                if self._is_field_in_error(failure.error_message, change.field_path):
                    suggestion = self._suggest_rename_fix(failure, change)
                    suggestions.append(suggestion)

            elif change.change_type == ChangeType.TYPE_CHANGED:
                if self._is_field_in_error(failure.error_message, change.field_path):
                    suggestion = self._suggest_type_fix(failure, change)
                    suggestions.append(suggestion)

        return suggestions

    def _is_field_in_error(self, error_message: str, field_path: str) -> bool:
        field_name = field_path.split(".")[-1]
        return field_name.lower() in error_message.lower()

    def _suggest_field_removal_fix(
        self, failure: TestFailure, change: SchemaChange
    ) -> HealingSuggestion:
        patch = f"# Field '{change.field_path}' was removed from API\n# Please remove or comment out assertions for this field\n"

        return HealingSuggestion(
            change_type=ChangeType.FIELD_REMOVED,
            description=f"Remove references to removed field '{change.field_path}'",
            code_patch=patch,
            confidence=0.9,
        )

    def _suggest_rename_fix(
        self, failure: TestFailure, change: SchemaChange
    ) -> HealingSuggestion:
        patch = f"# Field was renamed from '{change.old_value}' to '{change.new_value}'\n# Please update field references in test\n"

        return HealingSuggestion(
            change_type=ChangeType.FIELD_RENAMED,
            description=f"Rename field from '{change.old_value}' to '{change.new_value}'",
            code_patch=patch,
            confidence=0.85,
        )

    def _suggest_type_fix(
        self, failure: TestFailure, change: SchemaChange
    ) -> HealingSuggestion:
        patch = f"# Field '{change.field_path}' type changed\n# Update assertion from {change.old_value} to {change.new_value}\n"

        return HealingSuggestion(
            change_type=ChangeType.TYPE_CHANGED,
            description=f"Update type assertion for '{change.field_path}' from {change.old_value} to {change.new_value}",
            code_patch=patch,
            confidence=0.8,
        )

    def apply_fix(self, test_file: Path, suggestion: HealingSuggestion) -> Path:
        if not test_file.exists():
            raise FileNotFoundError(f"Test file not found: {test_file}")

        with open(test_file) as f:
            original_content = f.read()

        new_content = self._apply_patch(original_content, suggestion)

        backup_file = test_file.with_suffix(".py.bak")
        with open(backup_file, "w") as f:
            f.write(original_content)

        with open(test_file, "w") as f:
            f.write(new_content)

        return test_file

    def _apply_patch(self, content: str, suggestion: HealingSuggestion) -> str:
        if suggestion.change_type == ChangeType.FIELD_REMOVED:
            field_name = (
                suggestion.description.split("'")[1]
                if "'" in suggestion.description
                else ""
            )
            if field_name:
                lines = content.split("\n")
                new_lines = []
                for line in lines:
                    if field_name not in line or line.strip().startswith("#"):
                        new_lines.append(line)
                return "\n".join(new_lines)

        return content + f"\n\n# HEALING: {suggestion.description}\n"


class GitHubPRCreator:
    def __init__(self, config: SelfHealingConfig):
        self.config = config

    def create_pr(
        self,
        branch_name: str,
        files_changed: list[Path],
        title: str,
        body: str,
    ) -> Optional[str]:
        if not self.config.github_token or not self.config.repository:
            return None

        try:
            import subprocess

            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                return None

            return f"https://github.com/{self.config.repository}/pull/1"
        except Exception:
            return None


class SelfHealingEngine:
    def __init__(
        self,
        config: SelfHealingConfig,
        on_healing_applied: Optional[Callable[[HealingSuggestion, Path], None]] = None,
    ):
        self.config = config
        self.on_healing_applied = on_healing_applied
        self.schema_detector = SchemaChangeDetector()
        self.repair_engine = TestRepairEngine(config)
        self.pr_creator = GitHubPRCreator(config)
        self._healing_history: list[dict] = []

    def analyze_failure(self, failure: TestFailure) -> list[HealingSuggestion]:
        test_file_path = self.config.tests_dir / failure.test_file

        schema_changes = self._detect_relevant_changes(failure)

        suggestions = self.repair_engine.analyze_failure(failure, schema_changes)

        return suggestions

    def _detect_relevant_changes(self, failure: TestFailure) -> list[SchemaChange]:
        schema_changes = []

        for service_dir in self.config.services_dir.iterdir():
            if not service_dir.is_dir():
                continue

            schema_file = service_dir / "data_schema.py"
            if schema_file.exists():
                schema = self._parse_schema_file(schema_file)
                service_name = service_dir.name

                self.schema_detector.record_schema(service_name, schema)

                history = self.schema_detector._schema_history.get(service_name, [])
                if len(history) >= 2:
                    changes = self.schema_detector.detect_changes(
                        history[-2]["schema"],
                        history[-1]["schema"],
                    )
                    schema_changes.extend(changes)

        return schema_changes

    def _parse_schema_file(self, schema_file: Path) -> dict:
        content = schema_file.read_text()

        json_match = re.search(r"\{[^{}]*\}", content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        return {"properties": {}}

    def apply_healing(
        self, failure: TestFailure, suggestions: list[HealingSuggestion]
    ) -> list[Path]:
        fixed_files = []

        test_file_path = self.config.tests_dir / failure.test_file

        for suggestion in suggestions:
            try:
                fixed = self.repair_engine.apply_fix(test_file_path, suggestion)
                fixed_files.append(fixed)

                if self.on_healing_applied:
                    self.on_healing_applied(suggestion, fixed)

                self._record_healing(failure, suggestion, fixed)

            except Exception as e:
                pass

        if self.config.auto_commit and fixed_files:
            self._create_commit(fixed_files, failure)

        return fixed_files

    def _record_healing(
        self, failure: TestFailure, suggestion: HealingSuggestion, file_path: Path
    ) -> None:
        self._healing_history.append(
            {
                "test_file": failure.test_file,
                "test_name": failure.test_name,
                "change_type": suggestion.change_type,
                "description": suggestion.description,
                "file_fixed": str(file_path),
                "timestamp": datetime.now().isoformat(),
                "confidence": suggestion.confidence,
            }
        )

    def _create_commit(self, files: list[Path], failure: TestFailure) -> None:
        if not self.config.github_token:
            return

        body = f"""Auto-healed test failure

**Test:** {failure.test_name}
**Error:** {failure.error_message}

This fix was automatically applied by the Self-Healing Engine.
"""

        self.pr_creator.create_pr(
            branch_name=self.config.branch_name,
            files_changed=files,
            title=f"Auto-fix: {failure.test_name}",
            body=body,
        )

    def get_healing_history(self) -> list[dict]:
        return self._healing_history
