"""Error analyzer for Interactive Doctor.

This module analyzes test errors and consults the Project Manifest
to provide intelligent diagnosis.
"""

import json
import re
from typing import Any, Dict, List, Optional

from socialseed_e2e.core.interactive_doctor.models import (
    DiagnosisResult,
    ErrorContext,
    ErrorType,
    MissingFieldDetails,
    TypeMismatchDetails,
    ValidationErrorDetails,
)


class ErrorAnalyzer:
    """Analyzes test errors using Project Manifest information.

        This class parses error messages and consults the project manifest
    to identify the root cause of test failures.

        Example:
            >>> analyzer = ErrorAnalyzer("/path/to/project")
            >>> context = ErrorContext(
            ...     test_name="test_create_user",
            ...     service_name="user-service",
            ...     error_message="Validation error: age must be integer",
            ...     endpoint_path="/users",
            ...     http_method="POST"
            ... )
            >>> diagnosis = analyzer.analyze(context)
            >>> print(diagnosis.error_type)
            ErrorType.TYPE_MISMATCH
    """

    def __init__(self, project_root: str):
        """Initialize the error analyzer.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root
        self._manifest_api = None

    def _get_manifest_api(self):
        """Lazy load manifest API."""
        if self._manifest_api is None:
            try:
                from socialseed_e2e.project_manifest.api import ManifestAPI

                self._manifest_api = ManifestAPI(self.project_root)
            except Exception:
                self._manifest_api = None
        return self._manifest_api

    def analyze(self, context: ErrorContext) -> DiagnosisResult:
        """Analyze an error and provide diagnosis.

        Args:
            context: Error context with all relevant information

        Returns:
            DiagnosisResult with identified error type and details
        """
        # Try to identify error type from message
        error_type = self._identify_error_type(context.error_message)

        # Get manifest insights
        manifest_insights = self._get_manifest_insights(context)

        # Analyze based on error type
        if error_type == ErrorType.TYPE_MISMATCH:
            details = self._analyze_type_mismatch(context, manifest_insights)
        elif error_type == ErrorType.MISSING_FIELD:
            details = self._analyze_missing_field(context, manifest_insights)
        elif error_type == ErrorType.VALIDATION_ERROR:
            details = self._analyze_validation_error(context, manifest_insights)
        else:
            details = None

        # Build diagnosis description
        description = self._build_description(error_type, details, context)

        # Determine confidence based on available information
        confidence = self._calculate_confidence(error_type, manifest_insights, details)

        return DiagnosisResult(
            error_type=error_type,
            confidence=confidence,
            description=description,
            context=context,
            details=details,
            affected_files=self._get_affected_files(context, manifest_insights),
            manifest_insights=manifest_insights,
        )

    def _identify_error_type(self, error_message: str) -> ErrorType:
        """Identify error type from error message.

        Args:
            error_message: The error message text

        Returns:
            Identified ErrorType
        """
        message_lower = error_message.lower()

        # Type mismatch patterns
        type_patterns = [
            r"expected.*integer.*got.*string",
            r"expected.*string.*got.*integer",
            r"expected.*bool.*got.*",
            r"type.*mismatch",
            r"invalid.*type",
            r"must be.*integer",
            r"must be.*string",
            r"must be.*boolean",
            r"validation.*error",
        ]

        for pattern in type_patterns:
            if re.search(pattern, message_lower):
                return ErrorType.TYPE_MISMATCH

        # Missing field patterns
        missing_patterns = [
            r"missing.*field",
            r"field.*required",
            r"is required",
            r"cannot be null",
            r"does not exist",
        ]

        for pattern in missing_patterns:
            if re.search(pattern, message_lower):
                return ErrorType.MISSING_FIELD

        # Auth patterns
        auth_patterns = [
            r"unauthorized",
            r"authentication.*failed",
            r"forbidden",
            r"access.*denied",
        ]

        for pattern in auth_patterns:
            if re.search(pattern, message_lower):
                return ErrorType.AUTH_ERROR

        # Not found patterns
        not_found_patterns = [
            r"not found",
            r"404",
            r"does not exist",
        ]

        for pattern in not_found_patterns:
            if re.search(pattern, message_lower):
                return ErrorType.NOT_FOUND

        # Server error patterns
        server_patterns = [
            r"500",
            r"internal.*error",
            r"server.*error",
        ]

        for pattern in server_patterns:
            if re.search(pattern, message_lower):
                return ErrorType.SERVER_ERROR

        # Assertion patterns
        assertion_patterns = [
            r"assertion.*failed",
            r"expected.*got",
            r"assert.*error",
        ]

        for pattern in assertion_patterns:
            if re.search(pattern, message_lower):
                return ErrorType.ASSERTION_FAILURE

        return ErrorType.UNKNOWN

    def _get_manifest_insights(self, context: ErrorContext) -> Dict[str, Any]:
        """Get relevant information from project manifest.

        Args:
            context: Error context

        Returns:
            Dictionary with manifest insights
        """
        insights = {
            "endpoint_found": False,
            "dto_found": False,
            "endpoint_info": None,
            "dto_info": None,
        }

        api = self._get_manifest_api()
        if not api:
            return insights

        # Try to find endpoint
        if context.endpoint_path and context.http_method:
            try:
                endpoints = api.get_endpoints(service_name=context.service_name)
                for endpoint in endpoints:
                    if (
                        endpoint.path == context.endpoint_path
                        and endpoint.method.value.upper() == context.http_method.upper()
                    ):
                        insights["endpoint_found"] = True
                        insights["endpoint_info"] = endpoint

                        # Get DTO info if available
                        if endpoint.request_dto:
                            dto = api.get_dto(endpoint.request_dto)
                            if dto:
                                insights["dto_found"] = True
                                insights["dto_info"] = dto
                        break
            except Exception:
                pass

        return insights

    def _analyze_type_mismatch(
        self, context: ErrorContext, insights: Dict[str, Any]
    ) -> Optional[TypeMismatchDetails]:
        """Analyze type mismatch error.

        Args:
            context: Error context
            insights: Manifest insights

        Returns:
            TypeMismatchDetails or None
        """
        # Extract field name from error message
        field_match = re.search(
            r"['\"](\w+)['\"].*expected|field ['\"](\w+)['\"]", context.error_message
        )
        field_name = field_match.group(1) if field_match else None

        if not field_name and context.request_data:
            # Try to find field in request data
            for key in context.request_data.keys():
                if key.lower() in context.error_message.lower():
                    field_name = key
                    break

        # Determine expected and actual types
        expected_type = "unknown"
        actual_type = "unknown"

        # Check DTO info from manifest
        if insights.get("dto_info") and field_name:
            dto = insights["dto_info"]
            for field in dto.fields:
                if field.name == field_name or field.alias == field_name:
                    expected_type = field.type
                    break

        # Parse from error message
        type_match = re.search(
            r"expected ['\"]?(\w+)['\"]?.*got ['\"]?(\w+)['\"]?",
            context.error_message.lower(),
        )
        if type_match:
            expected_type = type_match.group(1)
            actual_type = type_match.group(2)

        # Get actual value from request
        actual_value = None
        if context.request_data and field_name:
            actual_value = context.request_data.get(field_name)
            if actual_value is not None:
                actual_type = type(actual_value).__name__

        return TypeMismatchDetails(
            field_name=field_name or "unknown",
            expected_type=expected_type,
            actual_type=actual_type,
            actual_value=actual_value,
            dto_name=insights.get("endpoint_info", {}).request_dto
            if insights.get("endpoint_info")
            else None,
        )

    def _analyze_missing_field(
        self, context: ErrorContext, insights: Dict[str, Any]
    ) -> Optional[MissingFieldDetails]:
        """Analyze missing field error.

        Args:
            context: Error context
            insights: Manifest insights

        Returns:
            MissingFieldDetails or None
        """
        # Extract field name
        field_match = re.search(
            r"['\"](\w+)['\"].*required|missing.*['\"](\w+)['\"]|field ['\"](\w+)['\"]",
            context.error_message,
        )

        field_name = None
        if field_match:
            for group in field_match.groups():
                if group:
                    field_name = group
                    break

        # Check DTO for field info
        is_required = True
        default_value = None

        if insights.get("dto_info") and field_name:
            dto = insights["dto_info"]
            for field in dto.fields:
                if field.name == field_name:
                    is_required = field.required
                    default_value = field.default_value
                    break

        return MissingFieldDetails(
            field_name=field_name or "unknown",
            dto_name=insights.get("endpoint_info", {}).request_dto
            if insights.get("endpoint_info")
            else None,
            is_required=is_required,
            default_value=default_value,
        )

    def _analyze_validation_error(
        self, context: ErrorContext, insights: Dict[str, Any]
    ) -> Optional[ValidationErrorDetails]:
        """Analyze validation error.

        Args:
            context: Error context
            insights: Manifest insights

        Returns:
            ValidationErrorDetails or None
        """
        # Extract field name and validation rule
        field_match = re.search(r"['\"](\w+)['\"]", context.error_message)
        field_name = field_match.group(1) if field_match else "unknown"

        validation_rule = "unknown"
        constraint_value = None

        # Identify validation type
        if (
            "minimum" in context.error_message.lower()
            or "min" in context.error_message.lower()
        ):
            validation_rule = "min"
            match = re.search(r"(\d+)", context.error_message)
            if match:
                constraint_value = int(match.group(1))
        elif (
            "maximum" in context.error_message.lower()
            or "max" in context.error_message.lower()
        ):
            validation_rule = "max"
            match = re.search(r"(\d+)", context.error_message)
            if match:
                constraint_value = int(match.group(1))
        elif "length" in context.error_message.lower():
            validation_rule = "length"
        elif (
            "pattern" in context.error_message.lower()
            or "regex" in context.error_message.lower()
        ):
            validation_rule = "regex"

        actual_value = None
        if context.request_data and field_name in context.request_data:
            actual_value = context.request_data[field_name]

        return ValidationErrorDetails(
            field_name=field_name,
            validation_rule=validation_rule,
            constraint_value=constraint_value,
            actual_value=actual_value,
            error_message=context.error_message,
        )

    def _build_description(
        self, error_type: ErrorType, details: Any, context: ErrorContext
    ) -> str:
        """Build human-readable diagnosis description.

        Args:
            error_type: Identified error type
            details: Error details
            context: Error context

        Returns:
            Description string
        """
        if error_type == ErrorType.TYPE_MISMATCH and isinstance(
            details, TypeMismatchDetails
        ):
            return (
                f"Type mismatch in field '{details.field_name}': "
                f"expected {details.expected_type}, got {details.actual_type}"
            )
        elif error_type == ErrorType.MISSING_FIELD and isinstance(
            details, MissingFieldDetails
        ):
            return f"Missing required field: {details.field_name}"
        elif error_type == ErrorType.VALIDATION_ERROR and isinstance(
            details, ValidationErrorDetails
        ):
            return f"Validation failed for field '{details.field_name}': {details.error_message}"
        elif error_type == ErrorType.AUTH_ERROR:
            return "Authentication/authorization error"
        elif error_type == ErrorType.NOT_FOUND:
            return f"Resource not found: {context.endpoint_path}"
        elif error_type == ErrorType.SERVER_ERROR:
            return "Server error occurred"
        else:
            return f"Error occurred: {context.error_message[:100]}"

    def _calculate_confidence(
        self, error_type: ErrorType, insights: Dict[str, Any], details: Any
    ) -> float:
        """Calculate confidence level of diagnosis.

        Args:
            error_type: Error type
            insights: Manifest insights
            details: Error details

        Returns:
            Confidence score (0.0 to 1.0)
        """
        confidence = 0.5  # Base confidence

        # Increase confidence if we found endpoint in manifest
        if insights.get("endpoint_found"):
            confidence += 0.2

        # Increase confidence if we found DTO
        if insights.get("dto_found"):
            confidence += 0.2

        # Increase confidence if we have specific details
        if (
            details
            and hasattr(details, "field_name")
            and details.field_name != "unknown"
        ):
            confidence += 0.1

        # Decrease confidence for unknown errors
        if error_type == ErrorType.UNKNOWN:
            confidence -= 0.3

        return max(0.0, min(1.0, confidence))

    def _get_affected_files(
        self, context: ErrorContext, insights: Dict[str, Any]
    ) -> List[str]:
        """Get list of files affected by this error.

        Args:
            context: Error context
            insights: Manifest insights

        Returns:
            List of file paths
        """
        files = []

        if insights.get("endpoint_info"):
            endpoint = insights["endpoint_info"]
            if hasattr(endpoint, "file_path"):
                files.append(endpoint.file_path)

        if insights.get("dto_info"):
            dto = insights["dto_info"]
            if hasattr(dto, "file_path"):
                files.append(dto.file_path)

        return files
