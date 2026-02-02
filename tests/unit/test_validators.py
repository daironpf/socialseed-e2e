"""Tests for validators module.

This module contains unit tests for all validation functions in the validators module.
"""

import re

import pytest

pytestmark = pytest.mark.unit

from socialseed_e2e.utils.validators import (
    ValidationError,
    validate_base_url,
    validate_dict,
    validate_email,
    validate_integer,
    validate_json_response,
    validate_list,
    validate_pagination_response,
    validate_port,
    validate_service_name,
    validate_status_code,
    validate_string,
    validate_timeout,
    validate_url,
    validate_uuid,
)


class TestValidationError:
    """Test cases for ValidationError exception."""

    def test_basic_error(self):
        """Test basic ValidationError creation."""
        error = ValidationError("Something went wrong")
        assert str(error) == "Validation error: Something went wrong"
        assert error.message == "Something went wrong"
        assert error.field is None
        assert error.value is None

    def test_error_with_field(self):
        """Test ValidationError with field name."""
        error = ValidationError("Invalid value", field="username", value="abc")
        assert "username" in str(error)
        assert error.field == "username"
        assert error.value == "abc"


class TestValidateUrl:
    """Test cases for validate_url function."""

    def test_valid_https_url(self):
        """Test valid HTTPS URL."""
        result = validate_url("https://api.example.com")
        assert result == "https://api.example.com"

    def test_valid_http_url(self):
        """Test valid HTTP URL."""
        result = validate_url("http://localhost:8080")
        assert result == "http://localhost:8080"

    def test_valid_url_with_path(self):
        """Test valid URL with path."""
        result = validate_url("https://api.example.com/v1/users")
        assert result == "https://api.example.com/v1/users"

    def test_empty_url_raises_error(self):
        """Test that empty URL raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_url("")
        assert "non-empty string" in str(exc_info.value)

    def test_none_url_raises_error(self):
        """Test that None URL raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_url(None)
        assert "non-empty string" in str(exc_info.value)

    def test_url_without_scheme_raises_error(self):
        """Test that URL without scheme raises error when required."""
        with pytest.raises(ValidationError) as exc_info:
            validate_url("api.example.com")
        assert "scheme" in str(exc_info.value)

    def test_url_without_scheme_allowed(self):
        """Test that URL without scheme is allowed when not required."""
        result = validate_url("api.example.com", require_scheme=False)
        assert result == "api.example.com"

    def test_url_with_spaces_raises_error(self):
        """Test that URL with spaces raises error."""
        with pytest.raises(ValidationError) as exc_info:
            validate_url("https://api example.com")
        assert "spaces" in str(exc_info.value)

    def test_url_with_disallowed_scheme(self):
        """Test URL with disallowed scheme."""
        with pytest.raises(ValidationError) as exc_info:
            validate_url("ftp://files.example.com")
        assert "scheme" in str(exc_info.value)

    def test_url_with_custom_allowed_schemes(self):
        """Test URL with custom allowed schemes."""
        result = validate_url("ftp://files.example.com", allowed_schemes=["ftp", "sftp"])
        assert result == "ftp://files.example.com"

    def test_invalid_domain_format(self):
        """Test URL with invalid domain format."""
        with pytest.raises(ValidationError) as exc_info:
            validate_url("https://-invalid.com")
        assert "domain" in str(exc_info.value)


class TestValidateBaseUrl:
    """Test cases for validate_base_url function."""

    def test_valid_base_url(self):
        """Test valid base URL."""
        result = validate_base_url("https://api.example.com/")
        assert result == "https://api.example.com"  # Trailing slash removed

    def test_base_url_without_trailing_slash(self):
        """Test base URL without trailing slash."""
        result = validate_base_url("https://api.example.com")
        assert result == "https://api.example.com"


class TestValidatePort:
    """Test cases for validate_port function."""

    def test_valid_port(self):
        """Test valid port number."""
        result = validate_port(8080)
        assert result == 8080

    def test_valid_port_as_string(self):
        """Test valid port as string."""
        result = validate_port("443")
        assert result == 443

    def test_port_too_low_raises_error(self):
        """Test that port below 1 raises error."""
        with pytest.raises(ValidationError) as exc_info:
            validate_port(0)
        assert "between 1 and 65535" in str(exc_info.value)

    def test_port_too_high_raises_error(self):
        """Test that port above 65535 raises error."""
        with pytest.raises(ValidationError) as exc_info:
            validate_port(70000)
        assert "between 1 and 65535" in str(exc_info.value)

    def test_invalid_port_string_raises_error(self):
        """Test that invalid port string raises error."""
        with pytest.raises(ValidationError) as exc_info:
            validate_port("not-a-port")
        assert "valid integer" in str(exc_info.value)


class TestValidateTimeout:
    """Test cases for validate_timeout function."""

    def test_valid_timeout(self):
        """Test valid timeout."""
        result = validate_timeout(5000)
        assert result == 5000

    def test_valid_timeout_as_string(self):
        """Test valid timeout as string."""
        result = validate_timeout("30000")
        assert result == 30000

    def test_zero_timeout_raises_error(self):
        """Test that zero timeout raises error."""
        with pytest.raises(ValidationError) as exc_info:
            validate_timeout(0)
        assert "positive" in str(exc_info.value)

    def test_negative_timeout_raises_error(self):
        """Test that negative timeout raises error."""
        with pytest.raises(ValidationError) as exc_info:
            validate_timeout(-1000)
        assert "positive" in str(exc_info.value)

    def test_invalid_timeout_string_raises_error(self):
        """Test that invalid timeout string raises error."""
        with pytest.raises(ValidationError) as exc_info:
            validate_timeout("fast")
        assert "valid integer" in str(exc_info.value)


class TestValidateServiceName:
    """Test cases for validate_service_name function."""

    def test_valid_service_name(self):
        """Test valid service name."""
        result = validate_service_name("users-api")
        assert result == "users-api"

    def test_valid_service_name_with_underscore(self):
        """Test valid service name with underscore."""
        result = validate_service_name("users_api")
        assert result == "users_api"

    def test_empty_name_raises_error(self):
        """Test that empty name raises error."""
        with pytest.raises(ValidationError) as exc_info:
            validate_service_name("")
        assert "non-empty string" in str(exc_info.value)

    def test_name_starting_with_number_raises_error(self):
        """Test that name starting with number raises error."""
        with pytest.raises(ValidationError) as exc_info:
            validate_service_name("123service")
        assert "start with letter" in str(exc_info.value)

    def test_name_too_long_raises_error(self):
        """Test that name exceeding 50 chars raises error."""
        with pytest.raises(ValidationError) as exc_info:
            validate_service_name("a" * 51)
        assert "between 1 and 50" in str(exc_info.value)

    def test_name_with_special_chars_raises_error(self):
        """Test that name with special chars raises error."""
        with pytest.raises(ValidationError) as exc_info:
            validate_service_name("user@api")
        assert "letters, numbers, hyphens, and underscores" in str(exc_info.value)


class TestValidateString:
    """Test cases for validate_string function."""

    def test_valid_string(self):
        """Test valid string."""
        result = validate_string("hello")
        assert result == "hello"

    def test_string_min_length(self):
        """Test string minimum length validation."""
        with pytest.raises(ValidationError) as exc_info:
            validate_string("ab", min_length=3)
        assert "at least 3 characters" in str(exc_info.value)

    def test_string_max_length(self):
        """Test string maximum length validation."""
        with pytest.raises(ValidationError) as exc_info:
            validate_string("hello world", max_length=5)
        assert "at most 5 characters" in str(exc_info.value)

    def test_string_pattern(self):
        """Test string pattern validation."""
        result = validate_string("abc123", pattern=r"^[a-z0-9]+$")
        assert result == "abc123"

    def test_string_pattern_failure(self):
        """Test string pattern validation failure."""
        with pytest.raises(ValidationError) as exc_info:
            validate_string("ABC", pattern=r"^[a-z]+$")
        assert "pattern" in str(exc_info.value)

    def test_string_not_blank(self):
        """Test that blank string is rejected when not allowed."""
        with pytest.raises(ValidationError) as exc_info:
            validate_string("   ", allow_blank=False)
        assert "cannot be blank" in str(exc_info.value)

    def test_non_string_raises_error(self):
        """Test that non-string raises error."""
        with pytest.raises(ValidationError) as exc_info:
            validate_string(123)
        assert "Expected string" in str(exc_info.value)


class TestValidateInteger:
    """Test cases for validate_integer function."""

    def test_valid_integer(self):
        """Test valid integer."""
        result = validate_integer(42)
        assert result == 42

    def test_integer_from_string(self):
        """Test integer from string."""
        result = validate_integer("100")
        assert result == 100

    def test_integer_min_value(self):
        """Test integer minimum value."""
        with pytest.raises(ValidationError) as exc_info:
            validate_integer(5, min_value=10)
        assert "at least 10" in str(exc_info.value)

    def test_integer_max_value(self):
        """Test integer maximum value."""
        with pytest.raises(ValidationError) as exc_info:
            validate_integer(100, max_value=50)
        assert "at most 50" in str(exc_info.value)

    def test_invalid_integer_raises_error(self):
        """Test that invalid integer raises error."""
        with pytest.raises(ValidationError) as exc_info:
            validate_integer("not-a-number")
        assert "Expected integer" in str(exc_info.value)


class TestValidateEmail:
    """Test cases for validate_email function."""

    def test_valid_email(self):
        """Test valid email."""
        result = validate_email("user@example.com")
        assert result == "user@example.com"

    def test_email_converted_to_lowercase(self):
        """Test that email is converted to lowercase."""
        result = validate_email("USER@EXAMPLE.COM")
        assert result == "user@example.com"

    def test_email_with_dots_and_plus(self):
        """Test email with dots and plus."""
        result = validate_email("user.name+tag@example.co.uk")
        assert result == "user.name+tag@example.co.uk"

    def test_empty_email_raises_error(self):
        """Test that empty email raises error."""
        with pytest.raises(ValidationError) as exc_info:
            validate_email("")
        assert "non-empty string" in str(exc_info.value)

    def test_invalid_email_format(self):
        """Test invalid email format."""
        with pytest.raises(ValidationError) as exc_info:
            validate_email("not-an-email")
        assert "Invalid email" in str(exc_info.value)

    def test_email_without_at_symbol(self):
        """Test email without @ symbol."""
        with pytest.raises(ValidationError) as exc_info:
            validate_email("user.example.com")
        assert "Invalid email" in str(exc_info.value)


class TestValidateUuid:
    """Test cases for validate_uuid function."""

    def test_valid_uuid_with_hyphens(self):
        """Test valid UUID with hyphens."""
        result = validate_uuid("550e8400-e29b-41d4-a716-446655440000")
        assert result == "550e8400-e29b-41d4-a716-446655440000"

    def test_valid_uuid_without_hyphens(self):
        """Test valid UUID without hyphens."""
        result = validate_uuid("550e8400e29b41d4a716446655440000")
        assert result == "550e8400e29b41d4a716446655440000"

    def test_empty_uuid_raises_error(self):
        """Test that empty UUID raises error."""
        with pytest.raises(ValidationError) as exc_info:
            validate_uuid("")
        assert "non-empty string" in str(exc_info.value)

    def test_invalid_uuid_format(self):
        """Test invalid UUID format."""
        with pytest.raises(ValidationError) as exc_info:
            validate_uuid("not-a-uuid")
        assert "Invalid UUID" in str(exc_info.value)

    def test_uuid_wrong_length(self):
        """Test UUID with wrong length."""
        with pytest.raises(ValidationError) as exc_info:
            validate_uuid("550e8400-e29b-41d4")
        assert "Invalid UUID" in str(exc_info.value)


class TestValidateStatusCode:
    """Test cases for validate_status_code function."""

    def test_single_expected_status(self):
        """Test single expected status code."""
        result = validate_status_code(200, 200)
        assert result == 200

    def test_multiple_expected_statuses(self):
        """Test multiple expected status codes."""
        result = validate_status_code(201, [200, 201, 202])
        assert result == 201

    def test_unexpected_status_raises_error(self):
        """Test that unexpected status raises error."""
        with pytest.raises(ValidationError) as exc_info:
            validate_status_code(404, 200)
        assert "Expected status code [200]" in str(exc_info.value)
        assert "404" in str(exc_info.value)


class TestValidateJsonResponse:
    """Test cases for validate_json_response function."""

    def test_valid_json_object(self):
        """Test valid JSON object."""
        data = {"id": 1, "name": "Test"}
        result = validate_json_response(data)
        assert result == data

    def test_required_fields_present(self):
        """Test that required fields are present."""
        data = {"id": 1, "name": "Test", "email": "test@example.com"}
        result = validate_json_response(data, required_fields=["id", "name"])
        assert result == data

    def test_missing_required_field_raises_error(self):
        """Test that missing required field raises error."""
        data = {"id": 1}
        with pytest.raises(ValidationError) as exc_info:
            validate_json_response(data, required_fields=["id", "name"])
        assert "Missing required fields" in str(exc_info.value)
        assert "name" in str(exc_info.value)

    def test_field_types(self):
        """Test field type validation."""
        data = {"id": 1, "name": "Test"}
        result = validate_json_response(data, field_types={"id": int, "name": str})
        assert result == data

    def test_field_type_mismatch_raises_error(self):
        """Test that field type mismatch raises error."""
        data = {"id": "1", "name": "Test"}
        with pytest.raises(ValidationError) as exc_info:
            validate_json_response(data, field_types={"id": int})
        assert "Field 'id' must be int" in str(exc_info.value)

    def test_non_dict_raises_error(self):
        """Test that non-dict raises error."""
        with pytest.raises(ValidationError) as exc_info:
            validate_json_response("not a dict")
        assert "Expected JSON object" in str(exc_info.value)


class TestValidatePaginationResponse:
    """Test cases for validate_pagination_response function."""

    def test_valid_pagination(self):
        """Test valid pagination response."""
        data = {"items": [{"id": 1}, {"id": 2}], "total": 2, "page": 1}
        result = validate_pagination_response(data)
        assert result == data

    def test_missing_items_field_raises_error(self):
        """Test that missing items field raises error."""
        data = {"total": 0, "page": 1}
        with pytest.raises(ValidationError) as exc_info:
            validate_pagination_response(data)
        assert "Missing 'items' field" in str(exc_info.value)

    def test_items_not_list_raises_error(self):
        """Test that items not being a list raises error."""
        data = {"items": "not a list", "total": 0}
        with pytest.raises(ValidationError) as exc_info:
            validate_pagination_response(data)
        assert "must be a list" in str(exc_info.value)

    def test_invalid_total_raises_error(self):
        """Test that invalid total raises error."""
        data = {"items": [], "total": -1}
        with pytest.raises(ValidationError) as exc_info:
            validate_pagination_response(data)
        assert "at least 0" in str(exc_info.value)

    def test_invalid_page_raises_error(self):
        """Test that invalid page raises error."""
        data = {"items": [], "total": 0, "page": 0}
        with pytest.raises(ValidationError) as exc_info:
            validate_pagination_response(data)
        assert "at least 1" in str(exc_info.value)


class TestValidateList:
    """Test cases for validate_list function."""

    def test_valid_list(self):
        """Test valid list."""
        result = validate_list([1, 2, 3])
        assert result == [1, 2, 3]

    def test_list_min_length(self):
        """Test list minimum length."""
        with pytest.raises(ValidationError) as exc_info:
            validate_list([1], min_length=2)
        assert "at least 2 items" in str(exc_info.value)

    def test_list_max_length(self):
        """Test list maximum length."""
        with pytest.raises(ValidationError) as exc_info:
            validate_list([1, 2, 3, 4, 5], max_length=3)
        assert "at most 3 items" in str(exc_info.value)

    def test_list_item_validator(self):
        """Test list with item validator."""
        result = validate_list(["hello", "world"], item_validator=lambda x: validate_string(x))
        assert result == ["hello", "world"]

    def test_list_item_validator_failure(self):
        """Test list with item validator failure."""
        with pytest.raises(ValidationError) as exc_info:
            validate_list(["hello", 123], item_validator=lambda x: validate_string(x))
        assert "Invalid item at index 1" in str(exc_info.value)

    def test_non_list_raises_error(self):
        """Test that non-list raises error."""
        with pytest.raises(ValidationError) as exc_info:
            validate_list("not a list")
        assert "Expected list" in str(exc_info.value)


class TestValidateDict:
    """Test cases for validate_dict function."""

    def test_valid_dict(self):
        """Test valid dict."""
        result = validate_dict({"key": "value"})
        assert result == {"key": "value"}

    def test_required_keys(self):
        """Test required keys validation."""
        data = {"id": 1, "name": "Test"}
        result = validate_dict(data, required_keys=["id", "name"])
        assert result == data

    def test_missing_required_key_raises_error(self):
        """Test that missing required key raises error."""
        data = {"id": 1}
        with pytest.raises(ValidationError) as exc_info:
            validate_dict(data, required_keys=["id", "name"])
        assert "Missing required keys" in str(exc_info.value)
        assert "name" in str(exc_info.value)

    def test_value_types(self):
        """Test value types validation."""
        data = {"count": 10, "active": True}
        result = validate_dict(data, value_types={"count": int, "active": bool})
        assert result == data

    def test_value_type_mismatch_raises_error(self):
        """Test that value type mismatch raises error."""
        data = {"count": "ten"}
        with pytest.raises(ValidationError) as exc_info:
            validate_dict(data, value_types={"count": int})
        assert "must be int" in str(exc_info.value)

    def test_non_dict_raises_error(self):
        """Test that non-dict raises error."""
        with pytest.raises(ValidationError) as exc_info:
            validate_dict("not a dict")
        assert "Expected dict" in str(exc_info.value)
