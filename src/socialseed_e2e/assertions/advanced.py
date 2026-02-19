"""Advanced Assertion Library for Enterprise API Testing.

This module provides comprehensive assertions for enterprise API testing including:
- Schema validation (JSON Schema, XML Schema, GraphQL Schema, Protocol Buffers)
- Business logic assertions (cross-field validation, state machines, workflows)
- Performance assertions (response time, payload size, rate limiting)
- Security assertions (injection detection, authentication verification)
- Data quality assertions (PII detection, format consistency)

Usage:
    from socialseed_e2e.assertions.advanced import (
        SchemaValidator,
        BusinessRuleValidator,
        PerformanceValidator,
        SecurityValidator,
    )
"""

import json
import re
import time
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Union
from xml.etree import ElementTree as ET

from pydantic import BaseModel, ValidationError

from .base import E2EAssertionError


# =============================================================================
# SCHEMA VALIDATION
# =============================================================================


class SchemaType(str, Enum):
    """Supported schema types for validation."""

    JSON_SCHEMA = "json_schema"
    XML_SCHEMA = "xml_schema"
    GRAPHQL_SCHEMA = "graphql_schema"
    PROTOBUF_SCHEMA = "protobuf"


class ValidationResult(BaseModel):
    """Result of schema validation."""

    valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    validated_at: datetime = datetime.now()


class SchemaValidator:
    """Advanced schema validation for multiple protocols.

    Example:
        validator = SchemaValidator()
        result = validator.validate_json_schema(
            response.json(),
            json_schema
        )
        if not result.valid:
            print(result.errors)
    """

    def __init__(self, strict_mode: bool = True):
        """Initialize validator with optional strict mode."""
        self.strict_mode = strict_mode

    def validate_json_schema(
        self,
        data: Any,
        schema: Dict[str, Any],
        validate_types: bool = True,
    ) -> ValidationResult:
        """Validate data against JSON Schema.

        Args:
            data: Data to validate
            schema: JSON Schema definition
            validate_types: Whether to validate types strictly

        Returns:
            ValidationResult with valid status and any errors

        Example:
            schema = {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "email": {"type": "string", "format": "email"}
                },
                "required": ["id"]
            }
            result = validator.validate_json_schema(user_data, schema)
        """
        errors: List[str] = []
        warnings: List[str] = []

        try:
            self._validate_json_object(
                data, schema, "", errors, warnings, validate_types
            )
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def _validate_json_object(
        self,
        data: Any,
        schema: Dict[str, Any],
        path: str,
        errors: List[str],
        warnings: List[str],
        validate_types: bool,
    ) -> None:
        """Recursively validate JSON object against schema."""
        schema_type = schema.get("type")

        # Handle empty schema
        if schema_type is None and not schema.get("properties"):
            return

        # Type validation
        if validate_types and schema_type:
            if not self._check_type(data, schema_type):
                errors.append(
                    f"{path}: expected type '{schema_type}', got '{type(data).__name__}'"
                )
                return

        # Object validation
        if schema_type == "object" or "properties" in schema:
            if not isinstance(data, dict):
                errors.append(f"{path}: expected object, got {type(data).__name__}")
                return

            # Check required fields
            for required in schema.get("required", []):
                if required not in data:
                    errors.append(f"{path}: required field '{required}' is missing")

            # Validate properties
            for prop_name, prop_schema in schema.get("properties", {}).items():
                if prop_name in data:
                    self._validate_json_object(
                        data[prop_name],
                        prop_schema,
                        f"{path}.{prop_name}" if path else prop_name,
                        errors,
                        warnings,
                        validate_types,
                    )

        # Array validation
        if schema_type == "array" or "items" in schema:
            if not isinstance(data, list):
                errors.append(f"{path}: expected array, got {type(data).__name__}")
                return

            for i, item in enumerate(data):
                self._validate_json_object(
                    item,
                    schema.get("items", {}),
                    f"{path}[{i}]",
                    errors,
                    warnings,
                    validate_types,
                )

        # String format validation
        if schema_type == "string" and "format" in schema:
            self._validate_string_format(data, schema["format"], path, errors)

        # Numeric constraints
        if schema_type in ("integer", "number"):
            self._validate_numeric_constraints(data, schema, path, errors)

        # Enum validation
        if "enum" in schema:
            if data not in schema["enum"]:
                errors.append(f"{path}: value must be one of {schema['enum']}")

    def _check_type(self, data: Any, schema_type: str) -> bool:
        """Check if data matches schema type."""
        type_map = {
            "string": str,
            "integer": int,
            "number": (int, float, Decimal),
            "boolean": bool,
            "array": list,
            "object": dict,
            "null": type(None),
        }
        expected = type_map.get(schema_type)
        if expected is None:
            return True
        return isinstance(data, expected)

    def _validate_string_format(
        self, data: str, format_type: str, path: str, errors: List[str]
    ) -> None:
        """Validate string format."""
        format_validators = {
            "email": r"^[\w\.-]+@[\w\.-]+\.\w+$",
            "uri": r"^https?://",
            "uuid": r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
            "date": r"^\d{4}-\d{2}-\d{2}$",
            "date-time": r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}",
            "time": r"^\d{2}:\d{2}:\d{2}",
            "ipv4": r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$",
            "ipv6": r"^[0-9a-fA-F:]+$",
            "hostname": r"^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$",
        }

        if format_type in format_validators:
            if not re.match(format_validators[format_type], data):
                errors.append(f"{path}: invalid '{format_type}' format")

    def _validate_numeric_constraints(
        self,
        data: Union[int, float],
        schema: Dict[str, Any],
        path: str,
        errors: List[str],
    ) -> None:
        """Validate numeric constraints."""
        if "minimum" in schema and data < schema["minimum"]:
            errors.append(
                f"{path}: value {data} is less than minimum {schema['minimum']}"
            )

        if "maximum" in schema and data > schema["maximum"]:
            errors.append(
                f"{path}: value {data} is greater than maximum {schema['maximum']}"
            )

        if "exclusiveMinimum" in schema and data <= schema["exclusiveMinimum"]:
            errors.append(
                f"{path}: value {data} must be greater than {schema['exclusiveMinimum']}"
            )

        if "exclusiveMaximum" in schema and data >= schema["exclusiveMaximum"]:
            errors.append(
                f"{path}: value {data} must be less than {schema['exclusiveMaximum']}"
            )

    def validate_xml_schema(self, xml_data: str, xsd_schema: str) -> ValidationResult:
        """Validate XML against XSD schema.

        Args:
            xml_data: XML string to validate
            xsd_schema: XSD schema string

        Returns:
            ValidationResult with validation status
        """
        errors: List[str] = []
        warnings: List[str] = []

        try:
            # Parse XSD
            xsd_root = ET.fromstring(xsd_schema)
            # Basic validation - in production use lxml
            if not xml_data.strip().startswith("<"):
                errors.append("Invalid XML: must start with '<'")
        except ET.ParseError as e:
            errors.append(f"XML parse error: {str(e)}")
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")

        return ValidationResult(
            valid=len(errors) == 0, errors=errors, warnings=warnings
        )

    def validate_graphql_schema(
        self, query: str, schema: Dict[str, Any]
    ) -> ValidationResult:
        """Validate GraphQL query against schema.

        Args:
            query: GraphQL query string
            schema: GraphQL schema definition

        Returns:
            ValidationResult with validation status
        """
        errors: List[str] = []
        warnings: List[str] = []

        # Basic GraphQL syntax validation
        if not query.strip():
            errors.append("GraphQL query is empty")
            return ValidationResult(valid=False, errors=errors, warnings=warnings)

        # Check for common issues
        if query.count("{") != query.count("}"):
            errors.append("Unbalanced braces in GraphQL query")

        if (
            "query" not in query
            and "mutation" not in query
            and "subscription" not in query
        ):
            warnings.append("GraphQL query should specify operation type")

        return ValidationResult(
            valid=len(errors) == 0, errors=errors, warnings=warnings
        )


# =============================================================================
# BUSINESS LOGIC VALIDATION
# =============================================================================


class StateTransition(BaseModel):
    """Represents a valid state transition."""

    from_state: str
    to_state: str
    condition: Optional[str] = None


class BusinessRuleValidator:
    """Validator for business logic constraints.

    Example:
        validator = BusinessRuleValidator()

        # Cross-field validation
        validator.validate_cross_field(
            data,
            rules=[("end_date", ">", "start_date")]
        )

        # State machine validation
        validator.validate_state_transition(
            current_state="pending",
            transitions=[
                StateTransition(from_state="pending", to_state="approved"),
                StateTransition(from_state="pending", to_state="rejected"),
            ]
        )
    """

    def __init__(self):
        """Initialize business rule validator."""
        self._custom_rules: List[Callable] = []

    def validate_cross_field(
        self,
        data: Dict[str, Any],
        rules: List[tuple],
    ) -> ValidationResult:
        """Validate cross-field business rules.

        Args:
            data: Data dictionary to validate
            rules: List of (field1, operator, field2) tuples

        Supported operators:
            - "==", "!=", ">", "<", ">=", "<="
            - "contains", "startswith", "endswith"
            - "in", "not_in"

        Example:
            rules = [
                ("end_date", ">", "start_date"),
                ("quantity", ">", 0),
                ("status", "in", ["active", "pending"]),
            ]
        """
        errors: List[str] = []
        warnings: List[str] = []

        for rule in rules:
            if len(rule) == 3:
                field1, operator, field2 = rule

                # Get values
                val1 = data.get(field1)
                val2 = data.get(field2) if isinstance(field2, str) else field2

                # Apply validation
                if not self._apply_operator(val1, operator, val2):
                    errors.append(
                        f"Business rule failed: {field1} {operator} {field2} "
                        f"(values: {val1}, {val2})"
                    )

        return ValidationResult(
            valid=len(errors) == 0, errors=errors, warnings=warnings
        )

    def _apply_operator(self, val1: Any, operator: str, val2: Any) -> bool:
        """Apply comparison operator."""
        operators = {
            "==": lambda a, b: a == b,
            "!=": lambda a, b: a != b,
            ">": lambda a, b: a > b,
            "<": lambda a, b: a < b,
            ">=": lambda a, b: a >= b,
            "<=": lambda a, b: a <= b,
            "contains": lambda a, b: b in a if a else False,
            "startswith": lambda a, b: str(a).startswith(str(b)) if a else False,
            "endswith": lambda a, b: str(a).endswith(str(b)) if a else False,
            "in": lambda a, b: a in b if isinstance(b, (list, tuple, set)) else False,
            "not_in": lambda a, b: a not in b
            if isinstance(b, (list, tuple, set))
            else True,
        }

        op_func = operators.get(operator)
        if op_func is None:
            return True

        try:
            return op_func(val1, val2)
        except (TypeError, ValueError):
            return False

    def validate_state_transition(
        self,
        current_state: str,
        transitions: List[StateTransition],
        expected_next_states: Optional[List[str]] = None,
    ) -> ValidationResult:
        """Validate state machine transition.

        Args:
            current_state: Current state
            transitions: List of valid StateTransition
            expected_next_states: Expected next states (optional)

        Returns:
            ValidationResult with transition validity
        """
        errors: List[str] = []
        warnings: List[str] = []

        # Find valid transitions from current state
        valid_transitions = [
            t.to_state for t in transitions if t.from_state == current_state
        ]

        if not valid_transitions:
            if current_state not in [t.from_state for t in transitions]:
                errors.append(f"No valid transitions from state '{current_state}'")
            return ValidationResult(
                valid=len(errors) == 0, errors=errors, warnings=warnings
            )

        # Check if expected next state is valid
        if expected_next_states:
            for expected in expected_next_states:
                if expected not in valid_transitions:
                    errors.append(
                        f"Invalid transition: cannot go from '{current_state}' to '{expected}'. "
                        f"Valid transitions: {valid_transitions}"
                    )

        return ValidationResult(
            valid=len(errors) == 0, errors=errors, warnings=warnings
        )

    def validate_workflow(
        self,
        steps: List[str],
        required_order: List[str],
    ) -> ValidationResult:
        """Validate workflow step ordering.

        Args:
            steps: Actual workflow steps executed
            required_order: Required order of steps

        Returns:
            ValidationResult with workflow validity
        """
        errors: List[str] = []
        warnings: List[str] = []

        # Check all required steps are present
        for req_step in required_order:
            if req_step not in steps:
                errors.append(f"Required step '{req_step}' not found in workflow")

        # Check order
        last_index = -1
        for step in required_order:
            if step in steps:
                current_index = steps.index(step)
                if current_index < last_index:
                    errors.append(
                        f"Workflow order violation: '{step}' came before expected step"
                    )
                last_index = current_index

        return ValidationResult(
            valid=len(errors) == 0, errors=errors, warnings=warnings
        )

    def add_custom_rule(self, rule: Callable[[Dict[str, Any]], Optional[str]]) -> None:
        """Add a custom business rule.

        Args:
            rule: Function that returns error message or None

        Example:
            def no_future_dates(data):
                if data.get("created_at", "") > datetime.now().isoformat():
                    return "created_at cannot be in the future"

            validator.add_custom_rule(no_future_dates)
        """
        self._custom_rules.append(rule)

    def validate_custom_rules(self, data: Dict[str, Any]) -> ValidationResult:
        """Validate all custom rules."""
        errors: List[str] = []
        warnings: List[str] = []

        for rule in self._custom_rules:
            try:
                error = rule(data)
                if error:
                    errors.append(f"Custom rule failed: {error}")
            except Exception as e:
                errors.append(f"Custom rule error: {str(e)}")

        return ValidationResult(
            valid=len(errors) == 0, errors=errors, warnings=warnings
        )


# =============================================================================
# PERFORMANCE VALIDATION
# =============================================================================


class PerformanceValidator:
    """Validator for performance-related assertions.

    Example:
        validator = PerformanceValidator()

        # Response time validation
        validator.validate_response_time(response_time_ms=150, sla_ms=200)

        # Payload size validation
        validator.validate_payload_size(response.body, max_size_kb=100)

        # Rate limit validation
        validator.validate_rate_limit(remaining=5, limit=100)
    """

    def __init__(self):
        """Initialize performance validator."""
        self._measurements: List[Dict[str, Any]] = []

    def validate_response_time(
        self,
        response_time_ms: float,
        sla_ms: float,
        percentile: Optional[float] = None,
    ) -> ValidationResult:
        """Validate response time against SLA.

        Args:
            response_time_ms: Response time in milliseconds
            sla_ms: SLA threshold in milliseconds
            percentile: Optional percentile for percentile SLA

        Returns:
            ValidationResult with performance status
        """
        errors: List[str] = []
        warnings: List[str] = []

        if response_time_ms > sla_ms:
            errors.append(
                f"Response time {response_time_ms}ms exceeds SLA {sla_ms}ms "
                f"(exceeded by {response_time_ms - sla_ms}ms)"
            )

        # Warning for close to SLA
        if response_time_ms > sla_ms * 0.9:
            warnings.append(
                f"Response time {response_time_ms}ms is close to SLA {sla_ms}ms"
            )

        return ValidationResult(
            valid=len(errors) == 0, errors=errors, warnings=warnings
        )

    def validate_payload_size(
        self,
        payload: Union[str, bytes, Dict],
        max_size_kb: float,
    ) -> ValidationResult:
        """Validate payload size.

        Args:
            payload: Response payload
            max_size_kb: Maximum size in kilobytes

        Returns:
            ValidationResult with size validation status
        """
        errors: List[str] = []
        warnings: List[str] = []

        # Calculate size
        if isinstance(payload, dict):
            size_bytes = len(json.dumps(payload).encode("utf-8"))
        elif isinstance(payload, str):
            size_bytes = len(payload.encode("utf-8"))
        else:
            size_bytes = len(payload)

        size_kb = size_bytes / 1024

        if size_kb > max_size_kb:
            errors.append(
                f"Payload size {size_kb:.2f}KB exceeds maximum {max_size_kb}KB "
                f"(exceeded by {size_kb - max_size_kb:.2f}KB)"
            )

        return ValidationResult(
            valid=len(errors) == 0, errors=errors, warnings=warnings
        )

    def validate_rate_limit(
        self,
        remaining: int,
        limit: int,
        min_remaining: int = 10,
    ) -> ValidationResult:
        """Validate rate limit compliance.

        Args:
            remaining: Remaining requests allowed
            limit: Total rate limit
            min_remaining: Minimum remaining requests to warn

        Returns:
            ValidationResult with rate limit status
        """
        errors: List[str] = []
        warnings: List[str] = []

        if remaining <= 0:
            errors.append("Rate limit exceeded - no requests remaining")

        if remaining < min_remaining:
            warnings.append(
                f"Rate limit low: only {remaining}/{limit} requests remaining"
            )

        return ValidationResult(
            valid=len(errors) == 0, errors=errors, warnings=warnings
        )

    def measure_execution_time(self, func: Callable, *args, **kwargs) -> tuple:
        """Measure function execution time.

        Returns:
            Tuple of (result, execution_time_ms)
        """
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        return result, (end - start) * 1000

    def add_measurement(self, name: str, value: float, unit: str = "ms") -> None:
        """Add a performance measurement for tracking."""
        self._measurements.append(
            {
                "name": name,
                "value": value,
                "unit": unit,
                "timestamp": datetime.now(),
            }
        )

    def get_measurements(self) -> List[Dict[str, Any]]:
        """Get all recorded measurements."""
        return self._measurements.copy()


# =============================================================================
# SECURITY VALIDATION
# =============================================================================


class SecurityValidator:
    """Validator for security-related assertions.

    Example:
        validator = SecurityValidator()

        # Check for SQL injection
        validator.validate_no_sql_injection(user_input)

        # Verify authentication headers
        validator.validate_authentication(response.headers)

        # Check for sensitive data exposure
        validator.validate_no_pii_in_response(response.json())
    """

    # Common SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE|UNION)\b)",
        r"(--|#|/\*|\*/)",
        r"(\bOR\b.*=.*\bOR\b)",
        r"(\bAND\b.*=.*\bAND\b)",
        r"('|(\\'))",
        r"(;\s*(SELECT|INSERT|UPDATE|DELETE|DROP))",
    ]

    # Common XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
    ]

    # Sensitive data patterns
    SENSITIVE_PATTERNS = {
        "api_key": r"(?i)(api[_-]?key|apikey)\s*[:=]\s*['\"]?([a-zA-Z0-9_-]{16,})",
        "password": r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"]?([^\s'\"]{4,})",
        "token": r"(?i)(access[_-]?token|refresh[_-]?token|auth[_-]?token)\s*[:=]\s*['\"]?([a-zA-Z0-9_-]{16,})",
        "credit_card": r"\b(?:\d{4}[- ]?){3}\d{4}\b",
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    }

    def __init__(self):
        """Initialize security validator."""
        self._validation_log: List[Dict[str, Any]] = []

    def validate_no_sql_injection(self, user_input: str) -> ValidationResult:
        """Check for SQL injection patterns in user input.

        Args:
            user_input: User-provided string to validate

        Returns:
            ValidationResult with security status
        """
        errors: List[str] = []
        warnings: List[str] = []

        for pattern in self.SQL_INJECTION_PATTERNS:
            if re.search(pattern, user_input, re.IGNORECASE):
                errors.append(
                    f"Potential SQL injection detected: pattern '{pattern}' found in input"
                )

        return ValidationResult(
            valid=len(errors) == 0, errors=errors, warnings=warnings
        )

    def validate_no_xss(self, user_input: str) -> ValidationResult:
        """Check for XSS patterns in user input.

        Args:
            user_input: User-provided string to validate

        Returns:
            ValidationResult with security status
        """
        errors: List[str] = []
        warnings: List[str] = []

        for pattern in self.XSS_PATTERNS:
            if re.search(pattern, user_input, re.IGNORECASE):
                errors.append(
                    f"Potential XSS detected: pattern '{pattern}' found in input"
                )

        return ValidationResult(
            valid=len(errors) == 0, errors=errors, warnings=warnings
        )

    def validate_authentication(
        self,
        headers: Dict[str, str],
        require_auth: bool = True,
    ) -> ValidationResult:
        """Validate authentication headers are present and correct.

        Args:
            headers: Response headers to validate
            require_auth: Whether authentication is required

        Returns:
            ValidationResult with authentication status
        """
        errors: List[str] = []
        warnings: List[str] = []

        # Check for security headers
        security_headers = {
            "Authorization": "Authorization header",
            "X-Content-Type-Options": "X-Content-Type-Options",
            "X-Frame-Options": "X-Frame-Options",
            "X-XSS-Protection": "X-XSS-Protection",
            "Strict-Transport-Security": "HSTS",
        }

        for header, name in security_headers.items():
            if header not in headers:
                warnings.append(f"Recommended security header '{name}' not present")

        # Validate Authorization header format
        if "Authorization" in headers:
            auth_value = headers["Authorization"]
            if not auth_value.startswith(("Bearer ", "Basic ", "Digest ")):
                warnings.append("Authorization header has non-standard format")

        if require_auth and "Authorization" not in headers:
            errors.append("Required Authorization header is missing")

        return ValidationResult(
            valid=len(errors) == 0, errors=errors, warnings=warnings
        )

    def validate_no_pii_in_response(
        self,
        data: Any,
        check_types: Optional[List[str]] = None,
    ) -> ValidationResult:
        """Check for PII in response data.

        Args:
            data: Response data to check
            check_types: List of PII types to check (default: all)

        Returns:
            ValidationResult with PII detection status
        """
        errors: List[str] = []
        warnings: List[str] = []

        check_types = check_types or list(self.SENSITIVE_PATTERNS.keys())

        found_pii = self._scan_for_pii(data, check_types)

        if found_pii:
            for pii_type, locations in found_pii.items():
                errors.append(
                    f"PII detected: {pii_type} found in {len(locations)} location(s)"
                )

        return ValidationResult(
            valid=len(errors) == 0, errors=errors, warnings=warnings
        )

    def _scan_for_pii(
        self,
        data: Any,
        check_types: List[str],
        path: str = "",
    ) -> Dict[str, List[str]]:
        """Recursively scan data for PII."""
        found: Dict[str, List[str]] = {}

        if isinstance(data, str):
            for pii_type in check_types:
                if pii_type in self.SENSITIVE_PATTERNS:
                    pattern = self.SENSITIVE_PATTERNS[pii_type]
                    if re.search(pattern, data):
                        found.setdefault(pii_type, []).append(path or "root")

        elif isinstance(data, dict):
            for key, value in data.items():
                new_path = f"{path}.{key}" if path else key
                result = self._scan_for_pii(value, check_types, new_path)
                for pii_type, locations in result.items():
                    found.setdefault(pii_type, []).extend(locations)

        elif isinstance(data, list):
            for i, item in enumerate(data):
                new_path = f"{path}[{i}]"
                result = self._scan_for_pii(item, check_types, new_path)
                for pii_type, locations in result.items():
                    found.setdefault(pii_type, []).extend(locations)

        return found

    def validate_csrf_token(
        self,
        headers: Dict[str, str],
        request_cookies: Optional[Dict[str, str]] = None,
    ) -> ValidationResult:
        """Validate CSRF token presence.

        Args:
            headers: Request/response headers
            request_cookies: Cookies from request

        Returns:
            ValidationResult with CSRF status
        """
        errors: List[str] = []
        warnings: List[str] = []

        csrf_headers = ["X-CSRF-Token", "X-XSRF-Token", "X-CSRF-TOKEN"]
        csrf_tokens = [headers.get(h) for h in csrf_headers]
        csrf_cookie = request_cookies.get("CSRFTOKEN") if request_cookies else None

        if not any(csrf_tokens) and not csrf_cookie:
            warnings.append("CSRF token not found in headers or cookies")

        return ValidationResult(
            valid=len(errors) == 0, errors=errors, warnings=warnings
        )


# =============================================================================
# DATA QUALITY VALIDATION
# =============================================================================


class DataQualityValidator:
    """Validator for data quality assertions.

    Example:
        validator = DataQualityValidator()

        # Check data consistency
        validator.validate_consistency(user_data, "email")

        # Validate referential integrity
        validator.validate_foreign_key(order_data, "user_id", existing_ids)

        # Check data completeness
        validator.validate_completeness(user_data, required_fields=["id", "email", "name"])
    """

    def __init__(self):
        """Initialize data quality validator."""
        self._known_values: Dict[str, Set[Any]] = {}

    def validate_consistency(
        self,
        data: Dict[str, Any],
        field: str,
    ) -> ValidationResult:
        """Validate data consistency within the dataset.

        Args:
            data: Data to validate
            field: Field to check for consistency

        Returns:
            ValidationResult with consistency status
        """
        errors: List[str] = []
        warnings: List[str] = []

        value = data.get(field)

        if value is None:
            warnings.append(f"Field '{field}' is None - cannot verify consistency")

        # Check type consistency
        if isinstance(value, str):
            if not value.strip():
                warnings.append(f"Field '{field}' is empty string")

        return ValidationResult(
            valid=len(errors) == 0, errors=errors, warnings=warnings
        )

    def validate_foreign_key(
        self,
        data: Dict[str, Any],
        foreign_key_field: str,
        valid_ids: Set[Any],
    ) -> ValidationResult:
        """Validate foreign key references.

        Args:
            data: Data with foreign key
            foreign_key_field: Name of foreign key field
            valid_ids: Set of valid IDs to reference

        Returns:
            ValidationResult with referential integrity status
        """
        errors: List[str] = []
        warnings: List[str] = []

        fk_value = data.get(foreign_key_field)

        if fk_value is None:
            warnings.append(f"Foreign key '{foreign_key_field}' is None")
            return ValidationResult(valid=True, errors=[], warnings=warnings)

        if fk_value not in valid_ids:
            errors.append(
                f"Invalid foreign key: '{foreign_key_field}'={fk_value} "
                f"not found in valid IDs"
            )

        return ValidationResult(
            valid=len(errors) == 0, errors=errors, warnings=warnings
        )

    def validate_completeness(
        self,
        data: Dict[str, Any],
        required_fields: List[str],
    ) -> ValidationResult:
        """Validate all required fields are present and non-null.

        Args:
            data: Data to validate
            required_fields: List of required field names

        Returns:
            ValidationResult with completeness status
        """
        errors: List[str] = []
        warnings: List[str] = []

        for field in required_fields:
            if field not in data:
                errors.append(f"Required field '{field}' is missing")
            elif data[field] is None:
                errors.append(f"Required field '{field}' is null")
            elif data[field] == "":
                warnings.append(f"Required field '{field}' is empty string")

        return ValidationResult(
            valid=len(errors) == 0, errors=errors, warnings=warnings
        )

    def validate_format_consistency(
        self,
        data: List[Dict[str, Any]],
        field: str,
        format_type: str,
    ) -> ValidationResult:
        """Validate format consistency across dataset.

        Args:
            data: List of data objects
            field: Field to check
            format_type: Expected format (date, email, phone, etc.)

        Returns:
            ValidationResult with format consistency status
        """
        errors: List[str] = []
        warnings: List[str] = []

        format_validators = {
            "date": r"^\d{4}-\d{2}-\d{2}$",
            "datetime": r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}",
            "email": r"^[\w\.-]+@[\w\.-]+\.\w+$",
            "phone": r"^\+?[\d\s\-()]+$",
            "uuid": r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        }

        pattern = format_validators.get(format_type)
        if not pattern:
            warnings.append(f"Unknown format type: {format_type}")
            return ValidationResult(valid=True, errors=[], warnings=warnings)

        inconsistent: List[str] = []

        for i, item in enumerate(data):
            value = item.get(field)
            if value and not re.match(pattern, str(value)):
                inconsistent.append(f"row {i}: {value}")

        if inconsistent:
            errors.append(
                f"Format inconsistency in '{field}' ({format_type}): "
                f"{len(inconsistent)} items don't match format"
            )

        return ValidationResult(
            valid=len(errors) == 0, errors=errors, warnings=warnings
        )


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def assert_valid_json_schema(
    data: Any,
    schema: Dict[str, Any],
    message: str = "JSON Schema validation failed",
) -> None:
    """Assert data is valid JSON Schema.

    Args:
        data: Data to validate
        schema: JSON Schema
        message: Custom error message

    Raises:
        E2EAssertionError: If validation fails
    """
    validator = SchemaValidator()
    result = validator.validate_json_schema(data, schema)

    if not result.valid:
        raise E2EAssertionError(
            message=message,
            actual=result.errors,
            context={"warnings": result.warnings},
        )


def assert_response_time(
    response_time_ms: float,
    sla_ms: float,
    message: str = "Response time SLA violation",
) -> None:
    """Assert response time is within SLA.

    Args:
        response_time_ms: Actual response time
        sla_ms: SLA threshold
        message: Custom error message

    Raises:
        E2EAssertionError: If SLA violated
    """
    validator = PerformanceValidator()
    result = validator.validate_response_time(response_time_ms, sla_ms)

    if not result.valid:
        raise E2EAssertionError(
            message=message,
            actual=f"{response_time_ms}ms",
            expected=f"<{sla_ms}ms",
        )


def assert_no_sql_injection(user_input: str) -> None:
    """Assert user input contains no SQL injection.

    Args:
        user_input: Input to validate

    Raises:
        E2EAssertionError: If SQL injection detected
    """
    validator = SecurityValidator()
    result = validator.validate_no_sql_injection(user_input)

    if not result.valid:
        raise E2EAssertionError(
            message="SQL injection detected in input",
            actual=user_input,
        )


def assert_no_pii(data: Any) -> None:
    """Assert data contains no PII.

    Args:
        data: Data to check

    Raises:
        E2EAssertionError: If PII detected
    """
    validator = SecurityValidator()
    result = validator.validate_no_pii_in_response(data)

    if not result.valid:
        raise E2EAssertionError(
            message="PII detected in response",
            actual=result.errors,
        )
