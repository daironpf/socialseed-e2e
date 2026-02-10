"""Auto-fixer for Interactive Doctor.

This module applies automatic fixes based on suggestions.
"""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from socialseed_e2e.core.interactive_doctor.models import (
    AppliedFix,
    DiagnosisResult,
    FixStrategy,
    FixSuggestion,
)


class AutoFixer:
    """Applies automatic fixes to code.

        This class applies fix suggestions to test files or source code,
    creating backups before modifications.

        Example:
            >>> fixer = AutoFixer("/path/to/project")
            >>> result = fixer.apply_fix(diagnosis, suggestion)
            >>> if result.success:
            ...     print(f"Fixed applied to {result.files_modified}")
    """

    def __init__(self, project_root: str, backup_dir: Optional[str] = None):
        """Initialize the auto-fixer.

        Args:
            project_root: Root directory of the project
            backup_dir: Directory for backups (default: .e2e/backups)
        """
        self.project_root = Path(project_root)
        self.backup_dir = (
            Path(backup_dir) if backup_dir else self.project_root / ".e2e" / "backups"
        )
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def apply_fix(
        self, diagnosis: DiagnosisResult, suggestion: FixSuggestion
    ) -> AppliedFix:
        """Apply a fix suggestion.

        Args:
            diagnosis: The diagnosis result
            suggestion: The fix suggestion to apply

        Returns:
            AppliedFix result
        """
        fix_id = f"fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        try:
            if suggestion.strategy == FixStrategy.UPDATE_TEST_DATA:
                result = self._apply_test_data_fix(diagnosis, suggestion)
            elif suggestion.strategy == FixStrategy.ADD_MISSING_FIELD:
                result = self._apply_add_field_fix(diagnosis, suggestion)
            elif suggestion.strategy == FixStrategy.UPDATE_VALIDATION:
                result = self._apply_validation_fix(diagnosis, suggestion)
            elif suggestion.strategy == FixStrategy.CONVERT_TYPE:
                result = self._apply_type_conversion_fix(diagnosis, suggestion)
            else:
                return AppliedFix(
                    fix_id=fix_id,
                    strategy=suggestion.strategy,
                    description=suggestion.description,
                    success=False,
                    error_message="Fix strategy not supported for automatic application",
                )

            result.fix_id = fix_id
            return result

        except Exception as e:
            return AppliedFix(
                fix_id=fix_id,
                strategy=suggestion.strategy,
                description=suggestion.description,
                success=False,
                error_message=str(e),
            )

    def _apply_test_data_fix(
        self, diagnosis: DiagnosisResult, suggestion: FixSuggestion
    ) -> AppliedFix:
        """Apply fix to test data.

        Args:
            diagnosis: Diagnosis
            suggestion: Suggestion

        Returns:
            AppliedFix result
        """
        files_modified = []
        backup_paths = []

        # Find test file
        test_file = self._find_test_file(diagnosis.context.test_name)

        if not test_file:
            return AppliedFix(
                fix_id="",
                strategy=FixStrategy.UPDATE_TEST_DATA,
                description=suggestion.description,
                success=False,
                error_message=f"Could not find test file for {diagnosis.context.test_name}",
            )

        # Create backup
        backup_path = self._create_backup(test_file)
        backup_paths.append(str(backup_path))

        # Read file
        content = test_file.read_text()

        # Apply changes based on change type
        for change in suggestion.code_changes:
            if change.get("change_type") == "type_conversion":
                content = self._apply_type_conversion(
                    content, change["field"], change["from_type"], change["to_type"]
                )
            elif change.get("change_type") == "adjust_value":
                content = self._apply_value_adjustment(
                    content,
                    change["field"],
                    change.get("validation_rule"),
                    change.get("constraint"),
                )

        # Write modified content
        test_file.write_text(content)
        files_modified.append(str(test_file))

        return AppliedFix(
            fix_id="",
            strategy=FixStrategy.UPDATE_TEST_DATA,
            description=suggestion.description,
            files_modified=files_modified,
            backup_paths=backup_paths,
            success=True,
        )

    def _apply_add_field_fix(
        self, diagnosis: DiagnosisResult, suggestion: FixSuggestion
    ) -> AppliedFix:
        """Apply fix to add missing field.

        Args:
            diagnosis: Diagnosis
            suggestion: Suggestion

        Returns:
            AppliedFix result
        """
        files_modified = []
        backup_paths = []

        # Find test file
        test_file = self._find_test_file(diagnosis.context.test_name)

        if not test_file:
            return AppliedFix(
                fix_id="",
                strategy=FixStrategy.ADD_MISSING_FIELD,
                description=suggestion.description,
                success=False,
                error_message=f"Could not find test file for {diagnosis.context.test_name}",
            )

        # Create backup
        backup_path = self._create_backup(test_file)
        backup_paths.append(str(backup_path))

        # Read file
        content = test_file.read_text()

        # Add field to test data
        for change in suggestion.code_changes:
            if change.get("change_type") == "add_field":
                content = self._apply_add_field(
                    content, change["field"], change.get("default_value")
                )

        # Write modified content
        test_file.write_text(content)
        files_modified.append(str(test_file))

        return AppliedFix(
            fix_id="",
            strategy=FixStrategy.ADD_MISSING_FIELD,
            description=suggestion.description,
            files_modified=files_modified,
            backup_paths=backup_paths,
            success=True,
        )

    def _apply_validation_fix(
        self, diagnosis: DiagnosisResult, suggestion: FixSuggestion
    ) -> AppliedFix:
        """Apply validation fix.

        Args:
            diagnosis: Diagnosis
            suggestion: Suggestion

        Returns:
            AppliedFix result
        """
        # Validation fixes typically require manual intervention
        return AppliedFix(
            fix_id="",
            strategy=FixStrategy.UPDATE_VALIDATION,
            description=suggestion.description,
            success=False,
            error_message="Validation fixes require manual review and implementation",
        )

    def _apply_type_conversion_fix(
        self, diagnosis: DiagnosisResult, suggestion: FixSuggestion
    ) -> AppliedFix:
        """Apply type conversion fix.

        Args:
            diagnosis: Diagnosis
            suggestion: Suggestion

        Returns:
            AppliedFix result
        """
        # Type conversion is handled as part of UPDATE_TEST_DATA
        return self._apply_test_data_fix(diagnosis, suggestion)

    def _find_test_file(self, test_name: str) -> Optional[Path]:
        """Find test file by test name.

        Args:
            test_name: Name of the test

        Returns:
            Path to test file or None
        """
        # Search in common test directories
        search_dirs = [
            self.project_root / "services",
            self.project_root / "tests",
            self.project_root / "verify_services",
        ]

        for search_dir in search_dirs:
            if not search_dir.exists():
                continue

            for py_file in search_dir.rglob("*.py"):
                if (
                    test_name in py_file.name
                    or test_name.replace("test_", "") in py_file.name
                ):
                    return py_file

                # Also check file content for test function
                try:
                    content = py_file.read_text()
                    if (
                        f"def {test_name}(" in content
                        or f"def test_{test_name}(" in content
                    ):
                        return py_file
                except Exception:
                    continue

        return None

    def _create_backup(self, file_path: Path) -> Path:
        """Create backup of a file.

        Args:
            file_path: Path to file

        Returns:
            Path to backup file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
        backup_path = self.backup_dir / backup_name

        shutil.copy2(file_path, backup_path)
        return backup_path

    def _apply_type_conversion(
        self, content: str, field: str, from_type: str, to_type: str
    ) -> str:
        """Apply type conversion in file content.

        Args:
            content: File content
            field: Field name
            from_type: Current type
            to_type: Target type

        Returns:
            Modified content
        """
        import re

        # Pattern to find field assignments in test data
        # Matches: field_name: value, "field_name": value, 'field_name': value
        patterns = [
            rf'["\']?{field}["\']?\s*:\s*([^,\n]+)',
            rf"{field}\s*=\s*([^,\n]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                current_value = match.group(1).strip()

                # Convert value
                if to_type.lower() in ("int", "integer"):
                    try:
                        # Try to convert
                        converted = int(float(current_value.strip("\"'")))
                        content = content.replace(
                            match.group(0), f"{field}: {converted}"
                        )
                    except ValueError:
                        pass

                elif to_type.lower() in ("str", "string"):
                    if not (
                        current_value.startswith('"') or current_value.startswith("'")
                    ):
                        content = content.replace(
                            match.group(0), f'{field}: "{current_value}"'
                        )

        return content

    def _apply_value_adjustment(
        self, content: str, field: str, validation_rule: Optional[str], constraint: Any
    ) -> str:
        """Apply value adjustment in file content.

        Args:
            content: File content
            field: Field name
            validation_rule: Validation rule
            constraint: Constraint value

        Returns:
            Modified content
        """
        import re

        # Pattern to find field assignments
        patterns = [
            rf'["\']?{field}["\']?\s*:\s*([^,\n]+)',
            rf"{field}\s*=\s*([^,\n]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                current_value = match.group(1).strip()

                # Adjust based on validation rule
                if validation_rule == "min" and constraint is not None:
                    try:
                        new_value = max(int(current_value), int(constraint) + 1)
                        content = content.replace(
                            match.group(0), f"{field}: {new_value}"
                        )
                    except ValueError:
                        pass

                elif validation_rule == "max" and constraint is not None:
                    try:
                        new_value = min(int(current_value), int(constraint) - 1)
                        content = content.replace(
                            match.group(0), f"{field}: {new_value}"
                        )
                    except ValueError:
                        pass

        return content

    def _apply_add_field(self, content: str, field: str, default_value: Any) -> str:
        """Apply add field in file content.

        Args:
            content: File content
            field: Field name
            default_value: Default value

        Returns:
            Modified content
        """
        import re

        # Find dictionary definitions in the content
        # Look for patterns like: {key: value, key: value}
        dict_pattern = r"\{[^}]+\}"

        for match in re.finditer(dict_pattern, content):
            dict_content = match.group(0)

            # Check if this dict contains request data indicators
            data_indicators = ["username", "email", "name", "data", "json"]
            if any(ind in dict_content.lower() for ind in data_indicators):
                # Add field before closing brace
                if isinstance(default_value, str):
                    field_line = f'"{field}": "{default_value}"'
                elif isinstance(default_value, bool):
                    field_line = f'"{field}": {str(default_value).lower()}'
                else:
                    field_line = f'"{field}": {default_value}'

                # Add comma if needed
                if not dict_content.rstrip().endswith(","):
                    field_line = ", " + field_line
                else:
                    field_line = " " + field_line

                new_dict = dict_content[:-1] + field_line + "}"
                content = content.replace(dict_content, new_dict)
                break

        return content

    def restore_backup(self, backup_path: str) -> bool:
        """Restore a file from backup.

        Args:
            backup_path: Path to backup file

        Returns:
            True if restored successfully
        """
        try:
            backup_file = Path(backup_path)
            if not backup_file.exists():
                return False

            # Extract original filename from backup name
            # Format: filename_timestamp.ext
            original_name = "_".join(backup_file.stem.split("_")[:-1])
            original_ext = backup_file.suffix
            original_file = backup_file.parent.parent / f"{original_name}{original_ext}"

            shutil.copy2(backup_file, original_file)
            return True

        except Exception:
            return False

    def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backups.

        Returns:
            List of backup information
        """
        backups = []

        if not self.backup_dir.exists():
            return backups

        for backup_file in self.backup_dir.iterdir():
            if backup_file.is_file():
                backups.append(
                    {
                        "path": str(backup_file),
                        "filename": backup_file.name,
                        "created": datetime.fromtimestamp(backup_file.stat().st_mtime),
                    }
                )

        return backups
