"""Validation helpers for socialseed-e2e.

This module provides validation functions for common use cases including
URL validation, configuration validation, data type validation, and
response validation.
"""

import re
from typing import Any, Callable, Dict, List, Optional, Pattern, Union
from urllib.parse import urlparse


class ValidationError(Exception):
    """Exception raised when validation fails.

    Attributes:
        message: Explanation of the validation error
        field: Name of the field that failed validation (if applicable)
        value: The value that failed validation (if applicable)
    """

    def __init__(self, message: str, field: Optional[str] = None, value: Any = None):
        super().__init__(message)
        self.message = message
        self.field = field
        self.value = value

    def __str__(self) -> str:
        if self.field:
            return f"Validation error for '{self.field}': {self.message}"
        return f"Validation error: {self.message}"


# URL Validation


def validate_url(
    url: str,
    require_scheme: bool = True,
    allowed_schemes: Optional[List[str]] = None,
    field_name: str = "url",
) -> str:
    """Validate a URL string.

    Args:
        url: The URL to validate
        require_scheme: Whether the URL must have a scheme (http/https)
        allowed_schemes: List of allowed schemes (default: ['http', 'https'])
        field_name: Name of the field for error messages

    Returns:
        The validated URL string

    Raises:
        ValidationError: If URL is invalid

    Example:
        >>> validate_url("https://api.example.com")
        'https://api.example.com'
        >>> validate_url("not-a-url")
        ValidationError: Invalid URL format
    """
    if not url or not isinstance(url, str):
        raise ValidationError("URL must be a non-empty string", field_name, url)

    url = url.strip()

    # Check for spaces
    if " " in url:
        raise ValidationError("URL cannot contain spaces", field_name, url)

    try:
        parsed = urlparse(url)
    except Exception as e:
        raise ValidationError(f"Invalid URL format: {e}", field_name, url)

    # Check scheme
    if require_scheme:
        if not parsed.scheme:
            raise ValidationError("URL must include scheme (http/https)", field_name, url)

        allowed = allowed_schemes or ["http", "https"]
        if parsed.scheme not in allowed:
            raise ValidationError(
                f"URL scheme '{parsed.scheme}' not allowed. Allowed: {', '.join(allowed)}",
                field_name,
                url,
            )

    # Check netloc (domain)
    # If no netloc and no scheme, try parsing with a dummy scheme
    if not parsed.netloc and not parsed.scheme:
        parsed_with_scheme = urlparse("http://" + url)
        if parsed_with_scheme.netloc:
            parsed = parsed_with_scheme

    if not parsed.netloc:
        raise ValidationError("URL must include a domain", field_name, url)

    # Validate domain format
    domain = parsed.netloc.split(":")[0]  # Remove port if present
    if not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9.-]*[a-zA-Z0-9]$", domain):
        raise ValidationError(f"Invalid domain format: {domain}", field_name, url)

    return url


def validate_base_url(base_url: str, field_name: str = "base_url") -> str:
    """Validate a base URL for API services.

    Similar to validate_url but specifically for API base URLs,
    ensuring no trailing slash for consistent endpoint construction.

    Args:
        base_url: The base URL to validate
        field_name: Name of the field for error messages

    Returns:
        The validated base URL (without trailing slash)

    Raises:
        ValidationError: If base URL is invalid
    """
    url = validate_url(base_url, field_name=field_name)
    # Remove trailing slash for consistent endpoint construction
    return url.rstrip("/")


# Configuration Validation


def validate_port(port: Union[int, str], field_name: str = "port") -> int:
    """Validate a port number.

    Args:
        port: Port number to validate
        field_name: Name of the field for error messages

    Returns:
        Validated port number as integer

    Raises:
        ValidationError: If port is invalid
    """
    try:
        port_int = int(port)
    except (ValueError, TypeError):
        raise ValidationError(f"Port must be a valid integer, got: {port}", field_name, port)

    if port_int < 1 or port_int > 65535:
        raise ValidationError(
            f"Port must be between 1 and 65535, got: {port_int}", field_name, port
        )

    return port_int


def validate_timeout(timeout: Union[int, str], field_name: str = "timeout") -> int:
    """Validate a timeout value in milliseconds.

    Args:
        timeout: Timeout in milliseconds
        field_name: Name of the field for error messages

    Returns:
        Validated timeout as integer

    Raises:
        ValidationError: If timeout is invalid
    """
    try:
        timeout_int = int(timeout)
    except (ValueError, TypeError):
        raise ValidationError(
            f"Timeout must be a valid integer, got: {timeout}", field_name, timeout
        )

    if timeout_int <= 0:
        raise ValidationError(f"Timeout must be positive, got: {timeout_int}", field_name, timeout)

    if timeout_int < 100:
        # Warning for very short timeouts, but still valid
        pass  # Could log warning here

    return timeout_int


def validate_service_name(name: str, field_name: str = "service_name") -> str:
    """Validate a service name.

    Service names should be:
    - Alphanumeric with hyphens and underscores
    - Start with letter
    - Between 1 and 50 characters

    Args:
        name: Service name to validate
        field_name: Name of the field for error messages

    Returns:
        Validated service name

    Raises:
        ValidationError: If name is invalid
    """
    if not name or not isinstance(name, str):
        raise ValidationError("Service name must be a non-empty string", field_name, name)

    name = name.strip()

    if len(name) < 1 or len(name) > 50:
        raise ValidationError(
            f"Service name must be between 1 and 50 characters, got: {len(name)}", field_name, name
        )

    if not re.match(r"^[a-zA-Z][a-zA-Z0-9_-]*$", name):
        raise ValidationError(
            "Service name must start with letter and contain only letters, numbers, hyphens, and underscores",
            field_name,
            name,
        )

    return name


# Data Type Validation


def validate_string(
    value: Any,
    field_name: str = "value",
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    pattern: Optional[Union[str, Pattern]] = None,
    allow_blank: bool = True,
) -> str:
    """Validate a string value.

    Args:
        value: Value to validate
        field_name: Name of the field for error messages
        min_length: Minimum string length (optional)
        max_length: Maximum string length (optional)
        pattern: Regex pattern to match (optional)
        allow_blank: Whether empty strings are allowed

    Returns:
        Validated string

    Raises:
        ValidationError: If value is invalid
    """
    if not isinstance(value, str):
        raise ValidationError(f"Expected string, got {type(value).__name__}", field_name, value)

    if not allow_blank and not value.strip():
        raise ValidationError("String cannot be blank", field_name, value)

    if min_length is not None and len(value) < min_length:
        raise ValidationError(
            f"String must be at least {min_length} characters, got: {len(value)}", field_name, value
        )

    if max_length is not None and len(value) > max_length:
        raise ValidationError(
            f"String must be at most {max_length} characters, got: {len(value)}", field_name, value
        )

    if pattern is not None:
        if isinstance(pattern, str):
            pattern = re.compile(pattern)
        if not pattern.match(value):
            raise ValidationError(
                f"String does not match required pattern: {pattern.pattern}", field_name, value
            )

    return value


def validate_integer(
    value: Any,
    field_name: str = "value",
    min_value: Optional[int] = None,
    max_value: Optional[int] = None,
) -> int:
    """Validate an integer value.

    Args:
        value: Value to validate
        field_name: Name of the field for error messages
        min_value: Minimum allowed value (optional)
        max_value: Maximum allowed value (optional)

    Returns:
        Validated integer

    Raises:
        ValidationError: If value is invalid
    """
    try:
        int_value = int(value)
    except (ValueError, TypeError):
        raise ValidationError(
            f"Expected integer, got {type(value).__name__}: {value}", field_name, value
        )

    if min_value is not None and int_value < min_value:
        raise ValidationError(
            f"Value must be at least {min_value}, got: {int_value}", field_name, value
        )

    if max_value is not None and int_value > max_value:
        raise ValidationError(
            f"Value must be at most {max_value}, got: {int_value}", field_name, value
        )

    return int_value


def validate_email(email: str, field_name: str = "email") -> str:
    """Validate an email address.

    Args:
        email: Email address to validate
        field_name: Name of the field for error messages

    Returns:
        Validated email address

    Raises:
        ValidationError: If email is invalid
    """
    if not email or not isinstance(email, str):
        raise ValidationError("Email must be a non-empty string", field_name, email)

    email = email.strip()

    # Basic email pattern
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, email):
        raise ValidationError("Invalid email format", field_name, email)

    return email.lower()


def validate_uuid(uuid_str: str, field_name: str = "uuid") -> str:
    """Validate a UUID string.

    Args:
        uuid_str: UUID string to validate
        field_name: Name of the field for error messages

    Returns:
        Validated UUID string

    Raises:
        ValidationError: If UUID is invalid
    """
    if not uuid_str or not isinstance(uuid_str, str):
        raise ValidationError("UUID must be a non-empty string", field_name, uuid_str)

    uuid_str = uuid_str.strip()

    # UUID pattern (accepts both with and without hyphens)
    pattern = r"^[0-9a-fA-F]{8}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{12}$"
    if not re.match(pattern, uuid_str):
        raise ValidationError("Invalid UUID format", field_name, uuid_str)

    return uuid_str


# Response Validation


def validate_status_code(
    status: int, expected: Union[int, List[int]], field_name: str = "status_code"
) -> int:
    """Validate an HTTP status code.

    Args:
        status: Actual status code
        expected: Expected status code(s)
        field_name: Name of the field for error messages

    Returns:
        Validated status code

    Raises:
        ValidationError: If status doesn't match expected
    """
    if isinstance(expected, int):
        expected = [expected]

    if status not in expected:
        raise ValidationError(f"Expected status code {expected}, got: {status}", field_name, status)

    return status


def validate_json_response(
    data: Any,
    required_fields: Optional[List[str]] = None,
    field_types: Optional[Dict[str, type]] = None,
    field_name: str = "response",
) -> Dict[str, Any]:
    """Validate a JSON response structure.

    Args:
        data: JSON data to validate
        required_fields: List of required field names
        field_types: Dictionary of field names to expected types
        field_name: Name of the field for error messages

    Returns:
        Validated data as dictionary

    Raises:
        ValidationError: If data structure is invalid
    """
    if not isinstance(data, dict):
        raise ValidationError(
            f"Expected JSON object (dict), got {type(data).__name__}", field_name, data
        )

    # Check required fields
    if required_fields:
        missing = [f for f in required_fields if f not in data]
        if missing:
            raise ValidationError(
                f"Missing required fields: {', '.join(missing)}", field_name, data
            )

    # Validate field types
    if field_types:
        for field, expected_type in field_types.items():
            if field in data:
                actual_value = data[field]
                if actual_value is not None and not isinstance(actual_value, expected_type):
                    raise ValidationError(
                        f"Field '{field}' must be {expected_type.__name__}, "
                        f"got {type(actual_value).__name__}",
                        field_name,
                        data,
                    )

    return data


def validate_pagination_response(
    data: Dict[str, Any],
    items_field: str = "items",
    total_field: str = "total",
    page_field: str = "page",
    field_name: str = "pagination",
) -> Dict[str, Any]:
    """Validate a paginated response structure.

    Args:
        data: Response data to validate
        items_field: Name of the items field
        total_field: Name of the total count field
        page_field: Name of the page field
        field_name: Name of the field for error messages

    Returns:
        Validated data

    Raises:
        ValidationError: If pagination structure is invalid
    """
    if not isinstance(data, dict):
        raise ValidationError("Pagination response must be a JSON object", field_name, data)

    # Validate items field
    if items_field not in data:
        raise ValidationError(
            f"Missing '{items_field}' field in pagination response", field_name, data
        )

    if not isinstance(data[items_field], list):
        raise ValidationError(f"'{items_field}' must be a list", field_name, data)

    # Validate total field
    if total_field in data:
        try:
            validate_integer(data[total_field], total_field, min_value=0)
        except ValidationError as e:
            raise ValidationError(str(e), field_name, data)

    # Validate page field
    if page_field in data:
        try:
            validate_integer(data[page_field], page_field, min_value=1)
        except ValidationError as e:
            raise ValidationError(str(e), field_name, data)

    return data


# Utility Validators


def validate_list(
    value: Any,
    field_name: str = "value",
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    item_validator: Optional[Callable[[Any], None]] = None,
) -> List[Any]:
    """Validate a list value.

    Args:
        value: Value to validate
        field_name: Name of the field for error messages
        min_length: Minimum list length (optional)
        max_length: Maximum list length (optional)
        item_validator: Optional function to validate each item

    Returns:
        Validated list

    Raises:
        ValidationError: If value is invalid
    """
    if not isinstance(value, list):
        raise ValidationError(f"Expected list, got {type(value).__name__}", field_name, value)

    if min_length is not None and len(value) < min_length:
        raise ValidationError(
            f"List must have at least {min_length} items, got: {len(value)}", field_name, value
        )

    if max_length is not None and len(value) > max_length:
        raise ValidationError(
            f"List must have at most {max_length} items, got: {len(value)}", field_name, value
        )

    if item_validator:
        for i, item in enumerate(value):
            try:
                item_validator(item)
            except ValidationError as e:
                raise ValidationError(f"Invalid item at index {i}: {e.message}", field_name, value)

    return value


def validate_dict(
    value: Any,
    field_name: str = "value",
    required_keys: Optional[List[str]] = None,
    value_types: Optional[Dict[str, type]] = None,
) -> Dict[str, Any]:
    """Validate a dictionary value.

    Args:
        value: Value to validate
        field_name: Name of the field for error messages
        required_keys: List of required keys
        value_types: Dictionary of keys to expected value types

    Returns:
        Validated dictionary

    Raises:
        ValidationError: If value is invalid
    """
    if not isinstance(value, dict):
        raise ValidationError(f"Expected dict, got {type(value).__name__}", field_name, value)

    if required_keys:
        missing = [k for k in required_keys if k not in value]
        if missing:
            raise ValidationError(f"Missing required keys: {', '.join(missing)}", field_name, value)

    if value_types:
        for key, expected_type in value_types.items():
            if key in value:
                actual_value = value[key]
                if actual_value is not None and not isinstance(actual_value, expected_type):
                    raise ValidationError(
                        f"Value for key '{key}' must be {expected_type.__name__}, "
                        f"got {type(actual_value).__name__}",
                        field_name,
                        value,
                    )

    return value
