"""Contract Validator for verifying requests and responses against schemas.

This module validates that requests to mock servers and their responses
conform to the expected contract, ensuring air-gapped testing integrity.
"""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


@dataclass
class ValidationError:
    """Represents a validation error."""

    field: str
    message: str
    expected: Any = None
    actual: Any = None
    severity: str = "error"  # error, warning


@dataclass
class ValidationResult:
    """Result of contract validation."""

    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)

    def add_error(
        self, field: str, message: str, expected: Any = None, actual: Any = None
    ) -> None:
        """Add an error to the result."""
        self.errors.append(
            ValidationError(
                field=field,
                message=message,
                expected=expected,
                actual=actual,
                severity="error",
            )
        )
        self.is_valid = False

    def add_warning(
        self, field: str, message: str, expected: Any = None, actual: Any = None
    ) -> None:
        """Add a warning to the result."""
        self.warnings.append(
            ValidationError(
                field=field,
                message=message,
                expected=expected,
                actual=actual,
                severity="warning",
            )
        )

    def merge(self, other: "ValidationResult") -> "ValidationResult":
        """Merge another validation result into this one."""
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        if not other.is_valid:
            self.is_valid = False
        return self


class ContractValidator:
    """Validates requests and responses against JSON schemas."""

    def __init__(self):
        """Initialize the validator."""
        self._schemas: Dict[str, Dict[str, Any]] = {}

    def validate_request(
        self,
        request_body: Dict[str, Any],
        schema: Dict[str, Any],
        path: str = "",
    ) -> ValidationResult:
        """Validate a request body against a schema.

        Args:
            request_body: The request body to validate
            schema: JSON schema to validate against
            path: Current path for nested validation

        Returns:
            ValidationResult with errors if any
        """
        result = ValidationResult(is_valid=True)

        if not schema:
            return result

        # Check type
        schema_type = schema.get("type")
        if schema_type and not self._check_type(request_body, schema_type):
            result.add_error(
                field=path or "root",
                message=f"Expected type '{schema_type}', got '{type(request_body).__name__}'",
                expected=schema_type,
                actual=type(request_body).__name__,
            )
            return result

        # Validate object properties
        if schema_type == "object" and isinstance(request_body, dict):
            result.merge(self._validate_object(request_body, schema, path))

        # Validate array items
        elif schema_type == "array" and isinstance(request_body, list):
            result.merge(self._validate_array(request_body, schema, path))

        # Validate string format
        elif schema_type == "string" and isinstance(request_body, str):
            result.merge(self._validate_string_format(request_body, schema, path))

        # Validate number constraints
        elif schema_type in ("number", "integer") and isinstance(
            request_body, (int, float)
        ):
            result.merge(self._validate_number_constraints(request_body, schema, path))

        # Check enum
        if "enum" in schema:
            if request_body not in schema["enum"]:
                result.add_error(
                    field=path or "root",
                    message=f"Value must be one of {schema['enum']}",
                    expected=schema["enum"],
                    actual=request_body,
                )

        return result

    def validate_response(
        self,
        response_body: Dict[str, Any],
        schema: Dict[str, Any],
        expected_status: int = 200,
        actual_status: int = 200,
    ) -> ValidationResult:
        """Validate a response body and status code.

        Args:
            response_body: The response body to validate
            schema: JSON schema to validate against
            expected_status: Expected HTTP status code
            actual_status: Actual HTTP status code

        Returns:
            ValidationResult with errors if any
        """
        result = ValidationResult(is_valid=True)

        # Check status code
        if expected_status != actual_status:
            result.add_error(
                field="status_code",
                message=f"Expected status {expected_status}, got {actual_status}",
                expected=expected_status,
                actual=actual_status,
            )

        # Validate response body
        if schema:
            result.merge(self.validate_request(response_body, schema))

        return result

    def validate_url_path(
        self,
        actual_path: str,
        pattern_path: str,
    ) -> ValidationResult:
        """Validate that a URL path matches a pattern.

        Args:
            actual_path: Actual request path
            pattern_path: Expected path pattern (may contain {params})

        Returns:
            ValidationResult
        """
        result = ValidationResult(is_valid=True)

        # Convert pattern to regex
        pattern = re.escape(pattern_path)
        pattern = pattern.replace(r"\{", "{")
        pattern = pattern.replace(r"\}", "}")
        pattern = re.sub(r"\{(\w+)\}", r"(?P<\1>[^/]+)", pattern)
        pattern = f"^{pattern}$"

        if not re.match(pattern, actual_path):
            result.add_error(
                field="path",
                message=f"Path '{actual_path}' does not match pattern '{pattern_path}'",
                expected=pattern_path,
                actual=actual_path,
            )

        return result

    def validate_headers(
        self,
        actual_headers: Dict[str, str],
        required_headers: List[str],
        header_schema: Optional[Dict[str, Any]] = None,
    ) -> ValidationResult:
        """Validate request/response headers.

        Args:
            actual_headers: Actual headers
            required_headers: List of required header names
            header_schema: Optional schema for header validation

        Returns:
            ValidationResult
        """
        result = ValidationResult(is_valid=True)

        # Check required headers
        actual_keys_lower = {k.lower(): k for k in actual_headers.keys()}

        for required in required_headers:
            if required.lower() not in actual_keys_lower:
                result.add_error(
                    field=f"header.{required}",
                    message=f"Required header '{required}' is missing",
                    expected=required,
                    actual=None,
                )

        # Validate header values if schema provided
        if header_schema and "properties" in header_schema:
            for header_name, header_schema_def in header_schema["properties"].items():
                actual_key = actual_keys_lower.get(header_name.lower())
                if actual_key:
                    header_value = actual_headers[actual_key]
                    # Simple type checking for headers
                    expected_type = header_schema_def.get("type")
                    if expected_type == "string" and not isinstance(header_value, str):
                        result.add_error(
                            field=f"header.{header_name}",
                            message="Header should be string",
                            expected="string",
                            actual=type(header_value).__name__,
                        )

        return result

    def _validate_object(
        self,
        obj: Dict[str, Any],
        schema: Dict[str, Any],
        path: str,
    ) -> ValidationResult:
        """Validate an object against a schema."""
        result = ValidationResult(is_valid=True)

        properties = schema.get("properties", {})
        required = schema.get("required", [])

        # Check required properties
        for prop_name in required:
            if prop_name not in obj:
                result.add_error(
                    field=f"{path}.{prop_name}" if path else prop_name,
                    message=f"Required property '{prop_name}' is missing",
                    expected=prop_name,
                    actual=None,
                )

        # Validate each property
        for prop_name, prop_value in obj.items():
            prop_path = f"{path}.{prop_name}" if path else prop_name

            if prop_name in properties:
                prop_schema = properties[prop_name]
                result.merge(self.validate_request(prop_value, prop_schema, prop_path))
            elif schema.get("additionalProperties") is False:
                result.add_warning(
                    field=prop_path,
                    message=f"Additional property '{prop_name}' not allowed by schema",
                )

        return result

    def _validate_array(
        self,
        arr: List[Any],
        schema: Dict[str, Any],
        path: str,
    ) -> ValidationResult:
        """Validate an array against a schema."""
        result = ValidationResult(is_valid=True)

        items_schema = schema.get("items")

        if items_schema:
            for i, item in enumerate(arr):
                item_path = f"{path}[{i}]"
                result.merge(self.validate_request(item, items_schema, item_path))

        # Check minItems
        if "minItems" in schema:
            if len(arr) < schema["minItems"]:
                result.add_error(
                    field=path,
                    message=f"Array must have at least {schema['minItems']} items",
                    expected=f">= {schema['minItems']} items",
                    actual=f"{len(arr)} items",
                )

        # Check maxItems
        if "maxItems" in schema:
            if len(arr) > schema["maxItems"]:
                result.add_error(
                    field=path,
                    message=f"Array must have at most {schema['maxItems']} items",
                    expected=f"<= {schema['maxItems']} items",
                    actual=f"{len(arr)} items",
                )

        return result

    def _validate_string_format(
        self,
        value: str,
        schema: Dict[str, Any],
        path: str,
    ) -> ValidationResult:
        """Validate string format constraints."""
        result = ValidationResult(is_valid=True)

        # Check minLength
        if "minLength" in schema:
            if len(value) < schema["minLength"]:
                result.add_error(
                    field=path,
                    message=f"String must be at least {schema['minLength']} characters",
                    expected=f">= {schema['minLength']} chars",
                    actual=f"{len(value)} chars",
                )

        # Check maxLength
        if "maxLength" in schema:
            if len(value) > schema["maxLength"]:
                result.add_error(
                    field=path,
                    message=f"String must be at most {schema['maxLength']} characters",
                    expected=f"<= {schema['maxLength']} chars",
                    actual=f"{len(value)} chars",
                )

        # Check pattern
        if "pattern" in schema:
            if not re.match(schema["pattern"], value):
                result.add_error(
                    field=path,
                    message=f"String does not match pattern '{schema['pattern']}'",
                    expected=schema["pattern"],
                    actual=value,
                )

        # Check format
        if "format" in schema:
            format_validators = {
                "email": self._validate_email,
                "uri": self._validate_uri,
                "date": self._validate_date,
                "date-time": self._validate_datetime,
                "uuid": self._validate_uuid,
            }
            validator = format_validators.get(schema["format"])
            if validator:
                format_result = validator(value)
                if not format_result.is_valid:
                    result.merge(format_result)

        return result

    def _validate_number_constraints(
        self,
        value: Union[int, float],
        schema: Dict[str, Any],
        path: str,
    ) -> ValidationResult:
        """Validate number constraints."""
        result = ValidationResult(is_valid=True)

        # Check minimum
        if "minimum" in schema:
            if value < schema["minimum"]:
                result.add_error(
                    field=path,
                    message=f"Value must be >= {schema['minimum']}",
                    expected=f">= {schema['minimum']}",
                    actual=value,
                )

        # Check maximum
        if "maximum" in schema:
            if value > schema["maximum"]:
                result.add_error(
                    field=path,
                    message=f"Value must be <= {schema['maximum']}",
                    expected=f"<= {schema['maximum']}",
                    actual=value,
                )

        # Check exclusiveMinimum
        if "exclusiveMinimum" in schema:
            if value <= schema["exclusiveMinimum"]:
                result.add_error(
                    field=path,
                    message=f"Value must be > {schema['exclusiveMinimum']}",
                    expected=f"> {schema['exclusiveMinimum']}",
                    actual=value,
                )

        # Check exclusiveMaximum
        if "exclusiveMaximum" in schema:
            if value >= schema["exclusiveMaximum"]:
                result.add_error(
                    field=path,
                    message=f"Value must be < {schema['exclusiveMaximum']}",
                    expected=f"< {schema['exclusiveMaximum']}",
                    actual=value,
                )

        return result

    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Check if a value matches the expected type."""
        type_mapping = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict,
            "null": type(None),
        }

        expected = type_mapping.get(expected_type)
        if expected is None:
            return True

        if isinstance(expected, tuple):
            return isinstance(value, expected)
        return isinstance(value, expected)

    def _validate_email(self, value: str) -> ValidationResult:
        """Validate email format."""
        result = ValidationResult(is_valid=True)
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, value):
            result.add_error(
                field="email",
                message="Invalid email format",
                expected="valid email",
                actual=value,
            )
        return result

    def _validate_uri(self, value: str) -> ValidationResult:
        """Validate URI format."""
        result = ValidationResult(is_valid=True)
        pattern = r"^https?://[^\s/$.?#].[^\s]*$"
        if not re.match(pattern, value):
            result.add_error(
                field="uri",
                message="Invalid URI format",
                expected="valid URI",
                actual=value,
            )
        return result

    def _validate_date(self, value: str) -> ValidationResult:
        """Validate date format (YYYY-MM-DD)."""
        result = ValidationResult(is_valid=True)
        pattern = r"^\d{4}-\d{2}-\d{2}$"
        if not re.match(pattern, value):
            result.add_error(
                field="date",
                message="Invalid date format, expected YYYY-MM-DD",
                expected="YYYY-MM-DD",
                actual=value,
            )
        return result

    def _validate_datetime(self, value: str) -> ValidationResult:
        """Validate datetime format (ISO 8601)."""
        result = ValidationResult(is_valid=True)
        pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?$"
        if not re.match(pattern, value):
            result.add_error(
                field="datetime",
                message="Invalid datetime format, expected ISO 8601",
                expected="ISO 8601 datetime",
                actual=value,
            )
        return result

    def _validate_uuid(self, value: str) -> ValidationResult:
        """Validate UUID format."""
        result = ValidationResult(is_valid=True)
        pattern = r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
        if not re.match(pattern, value):
            result.add_error(
                field="uuid",
                message="Invalid UUID format",
                expected="valid UUID",
                actual=value,
            )
        return result

    def load_schema(self, schema_path: Union[str, Path]) -> Dict[str, Any]:
        """Load a JSON schema from a file.

        Args:
            schema_path: Path to schema file

        Returns:
            Loaded schema
        """
        with open(schema_path, "r") as f:
            return json.load(f)

    def validate_contract_file(
        self,
        contract_path: Union[str, Path],
    ) -> Dict[str, ValidationResult]:
        """Validate an entire contract file.

        Args:
            contract_path: Path to contract file (JSON with request/response pairs)

        Returns:
            Dictionary mapping test names to validation results
        """
        results = {}

        with open(contract_path, "r") as f:
            contract = json.load(f)

        for test_name, test_case in contract.items():
            request = test_case.get("request", {})
            expected_response = test_case.get("expected_response", {})
            schema = test_case.get("schema", {})

            result = ValidationResult(is_valid=True)

            # Validate request if schema provided
            if schema.get("request"):
                result.merge(self.validate_request(request, schema["request"]))

            # Validate expected response
            if schema.get("response"):
                result.merge(
                    self.validate_request(expected_response, schema["response"])
                )

            results[test_name] = result

        return results


def validate_request_contract(
    request_body: Dict[str, Any],
    schema: Dict[str, Any],
) -> ValidationResult:
    """Convenience function to validate a request.

    Args:
        request_body: Request body to validate
        schema: JSON schema

    Returns:
        ValidationResult
    """
    validator = ContractValidator()
    return validator.validate_request(request_body, schema)


def validate_response_contract(
    response_body: Dict[str, Any],
    schema: Dict[str, Any],
    expected_status: int = 200,
    actual_status: int = 200,
) -> ValidationResult:
    """Convenience function to validate a response.

    Args:
        response_body: Response body to validate
        schema: JSON schema
        expected_status: Expected HTTP status
        actual_status: Actual HTTP status

    Returns:
        ValidationResult
    """
    validator = ContractValidator()
    return validator.validate_response(
        response_body, schema, expected_status, actual_status
    )
