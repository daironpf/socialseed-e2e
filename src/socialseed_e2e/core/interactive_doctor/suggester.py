"""Fix suggester for Interactive Doctor.

This module generates fix suggestions based on error diagnosis.
"""

from typing import Any, Dict, List

from socialseed_e2e.core.interactive_doctor.models import (
    DiagnosisResult,
    ErrorType,
    FixStrategy,
    FixSuggestion,
    MissingFieldDetails,
    TypeMismatchDetails,
    ValidationErrorDetails,
)


class FixSuggester:
    """Generates fix suggestions based on diagnosis.

        This class analyzes diagnosis results and suggests appropriate
    fixes that can be applied automatically or manually.

        Example:
            >>> suggester = FixSuggester()
            >>> suggestions = suggester.suggest_fixes(diagnosis)
            >>> for suggestion in suggestions:
            ...     print(f"{suggestion.strategy}: {suggestion.description}")
    """

    def suggest_fixes(self, diagnosis: DiagnosisResult) -> List[FixSuggestion]:
        """Generate fix suggestions for a diagnosis.

        Args:
            diagnosis: The diagnosis result

        Returns:
            List of fix suggestions
        """
        suggestions = []

        if diagnosis.error_type == ErrorType.TYPE_MISMATCH:
            suggestions.extend(self._suggest_type_mismatch_fixes(diagnosis))
        elif diagnosis.error_type == ErrorType.MISSING_FIELD:
            suggestions.extend(self._suggest_missing_field_fixes(diagnosis))
        elif diagnosis.error_type == ErrorType.VALIDATION_ERROR:
            suggestions.extend(self._suggest_validation_fixes(diagnosis))
        elif diagnosis.error_type == ErrorType.AUTH_ERROR:
            suggestions.extend(self._suggest_auth_fixes(diagnosis))
        elif diagnosis.error_type == ErrorType.NOT_FOUND:
            suggestions.extend(self._suggest_not_found_fixes(diagnosis))

        # Always add manual fix option
        suggestions.append(self._create_manual_fix_suggestion(diagnosis))

        # Always add ignore option
        suggestions.append(self._create_ignore_suggestion(diagnosis))

        return suggestions

    def _suggest_type_mismatch_fixes(
        self, diagnosis: DiagnosisResult
    ) -> List[FixSuggestion]:
        """Suggest fixes for type mismatch errors.

        Args:
            diagnosis: Diagnosis with TypeMismatchDetails

        Returns:
            List of suggestions
        """
        suggestions = []
        details = diagnosis.details

        if not isinstance(details, TypeMismatchDetails):
            return suggestions

        # Suggestion 1: Update test data
        if diagnosis.context.request_data:
            preview = self._generate_type_conversion_preview(
                diagnosis.context.request_data,
                details.field_name,
                details.expected_type,
            )

            suggestions.append(
                FixSuggestion(
                    strategy=FixStrategy.UPDATE_TEST_DATA,
                    title="Fix Test Data",
                    description=(
                        f"Convert '{details.field_name}' from {details.actual_type} "
                        f"to {details.expected_type} in test data"
                    ),
                    automatic=True,
                    preview=preview,
                    code_changes=[
                        {
                            "file_type": "test",
                            "change_type": "type_conversion",
                            "field": details.field_name,
                            "from_type": details.actual_type,
                            "to_type": details.expected_type,
                        }
                    ],
                    risks=["May affect other tests using same data"],
                )
            )

        # Suggestion 2: Update DTO logic
        if diagnosis.manifest_insights.get("dto_info"):
            dto_info = diagnosis.manifest_insights["dto_info"]
            suggestions.append(
                FixSuggestion(
                    strategy=FixStrategy.UPDATE_DTO_LOGIC,
                    title="Update DTO Logic",
                    description=(
                        f"Modify DTO '{dto_info.name}' to accept {details.actual_type} "
                        f"instead of {details.expected_type} for field '{details.field_name}'"
                    ),
                    automatic=False,  # Requires manual review
                    preview=f"# In {dto_info.file_path}\n# Change field type from {details.expected_type} to {details.actual_type}",
                    code_changes=[
                        {
                            "file_type": "dto",
                            "change_type": "type_change",
                            "file_path": dto_info.file_path,
                            "field": details.field_name,
                            "from_type": details.expected_type,
                            "to_type": details.actual_type,
                        }
                    ],
                    risks=[
                        "May break API contract",
                        "Could affect other endpoints using same DTO",
                        "Database schema may need migration",
                    ],
                )
            )

        return suggestions

    def _suggest_missing_field_fixes(
        self, diagnosis: DiagnosisResult
    ) -> List[FixSuggestion]:
        """Suggest fixes for missing field errors.

        Args:
            diagnosis: Diagnosis with MissingFieldDetails

        Returns:
            List of suggestions
        """
        suggestions = []
        details = diagnosis.details

        if not isinstance(details, MissingFieldDetails):
            return suggestions

        # Suggestion 1: Add field to test data
        if diagnosis.context.request_data is not None:
            default_value = self._generate_default_value(details)
            preview = self._generate_add_field_preview(
                diagnosis.context.request_data, details.field_name, default_value
            )

            suggestions.append(
                FixSuggestion(
                    strategy=FixStrategy.ADD_MISSING_FIELD,
                    title="Add Missing Field to Test",
                    description=(
                        f"Add required field '{details.field_name}' to test data "
                        f"with appropriate value"
                    ),
                    automatic=True,
                    preview=preview,
                    code_changes=[
                        {
                            "file_type": "test",
                            "change_type": "add_field",
                            "field": details.field_name,
                            "default_value": default_value,
                        }
                    ],
                    risks=[],
                )
            )

        # Suggestion 2: Make field optional in DTO
        if diagnosis.manifest_insights.get("dto_info") and not details.is_required:
            suggestions.append(
                FixSuggestion(
                    strategy=FixStrategy.UPDATE_DTO_LOGIC,
                    title="Make Field Optional in DTO",
                    description=(
                        f"Modify DTO to make '{details.field_name}' optional "
                        f"with default value"
                    ),
                    automatic=False,
                    preview=f"# Set {details.field_name} as Optional with default",
                    code_changes=[
                        {
                            "file_type": "dto",
                            "change_type": "make_optional",
                            "field": details.field_name,
                            "default_value": details.default_value,
                        }
                    ],
                    risks=["May break validation logic elsewhere"],
                )
            )

        return suggestions

    def _suggest_validation_fixes(
        self, diagnosis: DiagnosisResult
    ) -> List[FixSuggestion]:
        """Suggest fixes for validation errors.

        Args:
            diagnosis: Diagnosis with ValidationErrorDetails

        Returns:
            List of suggestions
        """
        suggestions = []
        details = diagnosis.details

        if not isinstance(details, ValidationErrorDetails):
            return suggestions

        # Suggestion 1: Update test data to meet validation
        suggestions.append(
            FixSuggestion(
                strategy=FixStrategy.UPDATE_TEST_DATA,
                title="Adjust Test Data for Validation",
                description=(
                    f"Update '{details.field_name}' to satisfy validation rule: "
                    f"{details.validation_rule}"
                ),
                automatic=True,
                preview=f"# Adjust value to meet {details.validation_rule} constraint",
                code_changes=[
                    {
                        "file_type": "test",
                        "change_type": "adjust_value",
                        "field": details.field_name,
                        "validation_rule": details.validation_rule,
                        "constraint": details.constraint_value,
                    }
                ],
                risks=[],
            )
        )

        # Suggestion 2: Update validation rules
        suggestions.append(
            FixSuggestion(
                strategy=FixStrategy.UPDATE_VALIDATION,
                title="Relax Validation Rules",
                description=(
                    f"Modify validation for '{details.field_name}' to allow "
                    f"current value"
                ),
                automatic=False,
                preview="# Update validation constraint in DTO/Model",
                code_changes=[
                    {
                        "file_type": "dto",
                        "change_type": "update_validation",
                        "field": details.field_name,
                        "validation_rule": details.validation_rule,
                    }
                ],
                risks=["May reduce data quality", "Could allow invalid data"],
            )
        )

        return suggestions

    def _suggest_auth_fixes(self, diagnosis: DiagnosisResult) -> List[FixSuggestion]:
        """Suggest fixes for authentication errors.

        Args:
            diagnosis: Diagnosis

        Returns:
            List of suggestions
        """
        return [
            FixSuggestion(
                strategy=FixStrategy.MANUAL_FIX,
                title="Check Authentication",
                description="Verify authentication tokens and credentials",
                automatic=False,
                preview="# Check auth headers and tokens in test setup",
                code_changes=[
                    {
                        "file_type": "test",
                        "change_type": "update_auth",
                        "description": "Update authentication in test",
                    }
                ],
                risks=[],
            )
        ]

    def _suggest_not_found_fixes(
        self, diagnosis: DiagnosisResult
    ) -> List[FixSuggestion]:
        """Suggest fixes for not found errors.

        Args:
            diagnosis: Diagnosis

        Returns:
            List of suggestions
        """
        suggestions = []

        # Check if endpoint exists in manifest
        if not diagnosis.manifest_insights.get("endpoint_found"):
            suggestions.append(
                FixSuggestion(
                    strategy=FixStrategy.MANUAL_FIX,
                    title="Endpoint Not Found in Manifest",
                    description=(
                        f"Endpoint '{diagnosis.context.endpoint_path}' not found "
                        f"in Project Manifest. May need to regenerate manifest."
                    ),
                    automatic=False,
                    preview="# Run: e2e manifest --force",
                    code_changes=[],
                    risks=[],
                )
            )
        else:
            suggestions.append(
                FixSuggestion(
                    strategy=FixStrategy.UPDATE_TEST_DATA,
                    title="Update Resource ID",
                    description="Use valid resource ID that exists in database",
                    automatic=False,
                    preview="# Update ID in test data to valid value",
                    code_changes=[
                        {
                            "file_type": "test",
                            "change_type": "update_id",
                            "description": "Use valid resource identifier",
                        }
                    ],
                    risks=[],
                )
            )

        return suggestions

    def _create_manual_fix_suggestion(
        self, diagnosis: DiagnosisResult
    ) -> FixSuggestion:
        """Create manual fix suggestion.

        Args:
            diagnosis: Diagnosis

        Returns:
            Manual fix suggestion
        """
        return FixSuggestion(
            strategy=FixStrategy.MANUAL_FIX,
            title="Manual Fix",
            description="Fix the issue manually in your code",
            automatic=False,
            preview=f"# Manual fix required for: {diagnosis.description}",
            code_changes=[],
            risks=[],
        )

    def _create_ignore_suggestion(self, diagnosis: DiagnosisResult) -> FixSuggestion:
        """Create ignore suggestion.

        Args:
            diagnosis: Diagnosis

        Returns:
            Ignore suggestion
        """
        return FixSuggestion(
            strategy=FixStrategy.IGNORE,
            title="Ignore for Now",
            description="Skip this error and continue with other tests",
            automatic=True,
            preview="# Error will be logged but not fixed",
            code_changes=[],
            risks=["Test may continue to fail"],
        )

    def _generate_type_conversion_preview(
        self, request_data: Dict[str, Any], field_name: str, expected_type: str
    ) -> str:
        """Generate preview of type conversion.

        Args:
            request_data: Current request data
            field_name: Field to convert
            expected_type: Target type

        Returns:
            Preview string
        """
        current_value = request_data.get(field_name)

        if current_value is None:
            return f"# Add {field_name}: <{expected_type}_value>"

        if expected_type.lower() in ("int", "integer"):
            try:
                converted = int(current_value)
                return f"# {field_name}: {current_value} -> {converted}"
            except (ValueError, TypeError):
                return f"# {field_name}: '{current_value}' -> <valid_integer>"

        elif expected_type.lower() in ("str", "string"):
            return f"# {field_name}: {current_value} -> '{current_value}'"

        elif expected_type.lower() in ("bool", "boolean"):
            return f"# {field_name}: {current_value} -> {bool(current_value)}"

        return f"# {field_name}: convert to {expected_type}"

    def _generate_add_field_preview(
        self, request_data: Dict[str, Any], field_name: str, default_value: Any
    ) -> str:
        """Generate preview of adding a field.

        Args:
            request_data: Current request data
            field_name: Field to add
            default_value: Default value for field

        Returns:
            Preview string
        """
        data_preview = dict(request_data)
        data_preview[field_name] = default_value

        import json

        return json.dumps(data_preview, indent=2)

    def _generate_default_value(self, details: MissingFieldDetails) -> Any:
        """Generate appropriate default value for a field.

        Args:
            details: Missing field details

        Returns:
            Default value
        """
        if details.default_value is not None:
            return details.default_value

        # Generate based on field name patterns
        field_lower = details.field_name.lower()

        if "id" in field_lower:
            return 1
        elif "name" in field_lower:
            return "test_name"
        elif "email" in field_lower:
            return "test@example.com"
        elif "age" in field_lower:
            return 25
        elif "count" in field_lower or "number" in field_lower:
            return 0
        elif "enabled" in field_lower or "active" in field_lower:
            return True
        elif "date" in field_lower:
            return "2024-01-01"

        return "test_value"
