"""Tests for Advanced Assertion Library.

This module tests the advanced assertion features including:
- Schema validation
- Business logic validation
- Performance validation
- Security validation
- Data quality validation
"""

import pytest

from socialseed_e2e.assertions.advanced import (
    BusinessRuleValidator,
    DataQualityValidator,
    PerformanceValidator,
    SchemaValidator,
    SecurityValidator,
    StateTransition,
    assert_no_pii,
    assert_no_sql_injection,
    assert_response_time,
    assert_valid_json_schema,
)


class TestSchemaValidator:
    """Tests for SchemaValidator."""

    def test_valid_json_schema(self):
        """Test valid JSON schema validation."""
        validator = SchemaValidator()
        schema = {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "email": {"type": "string", "format": "email"},
            },
            "required": ["id"],
        }
        data = {"id": 1, "email": "test@example.com"}
        result = validator.validate_json_schema(data, schema)
        assert result.valid

    def test_invalid_type(self):
        """Test type validation failure."""
        validator = SchemaValidator()
        schema = {"type": "object", "properties": {"id": {"type": "integer"}}}
        data = {"id": "not_an_integer"}
        result = validator.validate_json_schema(data, schema)
        assert not result.valid
        assert any("expected type" in err for err in result.errors)

    def test_missing_required_field(self):
        """Test missing required field."""
        validator = SchemaValidator()
        schema = {"type": "object", "required": ["id"]}
        data = {}
        result = validator.validate_json_schema(data, schema)
        assert not result.valid
        assert any("required field" in err for err in result.errors)

    def test_string_format_email(self):
        """Test email format validation."""
        validator = SchemaValidator()
        result = validator.validate_json_schema(
            "invalid-email", {"type": "string", "format": "email"}
        )
        assert not result.valid


class TestBusinessRuleValidator:
    """Tests for BusinessRuleValidator."""

    def test_cross_field_validation(self):
        """Test cross-field business rules."""
        validator = BusinessRuleValidator()
        data = {"start_date": "2024-01-01", "end_date": "2024-01-15"}
        rules = [("end_date", ">", "start_date")]
        result = validator.validate_cross_field(data, rules)
        assert result.valid

    def test_cross_field_failure(self):
        """Test cross-field validation failure."""
        validator = BusinessRuleValidator()
        data = {"start_date": "2024-01-15", "end_date": "2024-01-01"}
        rules = [("end_date", ">", "start_date")]
        result = validator.validate_cross_field(data, rules)
        assert not result.valid

    def test_state_transition_valid(self):
        """Test valid state transition."""
        validator = BusinessRuleValidator()
        transitions = [
            StateTransition(from_state="pending", to_state="approved"),
            StateTransition(from_state="pending", to_state="rejected"),
        ]
        result = validator.validate_state_transition(
            "pending", transitions, ["approved"]
        )
        assert result.valid

    def test_state_transition_invalid(self):
        """Test invalid state transition."""
        validator = BusinessRuleValidator()
        transitions = [
            StateTransition(from_state="pending", to_state="approved"),
        ]
        result = validator.validate_state_transition(
            "pending", transitions, ["rejected"]
        )
        assert not result.valid


class TestPerformanceValidator:
    """Tests for PerformanceValidator."""

    def test_response_time_within_sla(self):
        """Test response time within SLA."""
        validator = PerformanceValidator()
        result = validator.validate_response_time(150, 200)
        assert result.valid

    def test_response_time_exceeds_sla(self):
        """Test response time exceeds SLA."""
        validator = PerformanceValidator()
        result = validator.validate_response_time(250, 200)
        assert not result.valid

    def test_payload_size_within_limit(self):
        """Test payload size within limit."""
        validator = PerformanceValidator()
        result = validator.validate_payload_size("x" * 1024, 2)  # 1KB
        assert result.valid

    def test_payload_size_exceeds_limit(self):
        """Test payload size exceeds limit."""
        validator = PerformanceValidator()
        result = validator.validate_payload_size("x" * 3072, 2)  # 3KB
        assert not result.valid

    def test_rate_limit_valid(self):
        """Test rate limit valid."""
        validator = PerformanceValidator()
        result = validator.validate_rate_limit(remaining=50, limit=100)
        assert result.valid

    def test_rate_limit_exceeded(self):
        """Test rate limit exceeded."""
        validator = PerformanceValidator()
        result = validator.validate_rate_limit(remaining=0, limit=100)
        assert not result.valid


class TestSecurityValidator:
    """Tests for SecurityValidator."""

    def test_no_sql_injection_clean(self):
        """Test clean input passes SQL injection check."""
        validator = SecurityValidator()
        result = validator.validate_no_sql_injection("John Doe")
        assert result.valid

    def test_sql_injection_detected(self):
        """Test SQL injection detection."""
        validator = SecurityValidator()
        result = validator.validate_no_sql_injection("'; DROP TABLE users;--")
        assert not result.valid

    def test_no_xss_clean(self):
        """Test clean input passes XSS check."""
        validator = SecurityValidator()
        result = validator.validate_no_xss("Hello World")
        assert result.valid

    def test_xss_detected(self):
        """Test XSS detection."""
        validator = SecurityValidator()
        result = validator.validate_no_xss("<script>alert('xss')</script>")
        assert not result.valid

    def test_no_pii_clean(self):
        """Test clean response passes PII check."""
        validator = SecurityValidator()
        result = validator.validate_no_pii_in_response({"name": "John", "age": 30})
        assert result.valid

    def test_pii_detected(self):
        """Test PII detection in response."""
        validator = SecurityValidator()
        result = validator.validate_no_pii_in_response(
            {"email": "test@example.com", "ssn": "123-45-6789"}
        )
        assert not result.valid


class TestConvenienceFunctions:
    """Tests for convenience assertion functions."""

    def test_assert_response_time_passes(self):
        """Test assert_response_time passes."""
        assert_response_time(100, 200)

    def test_assert_response_time_fails(self):
        """Test assert_response_time fails."""
        with pytest.raises(Exception):
            assert_response_time(300, 200)

    def test_assert_no_sql_injection_passes(self):
        """Test assert_no_sql_injection passes."""
        assert_no_sql_injection("normal input")

    def test_assert_no_sql_injection_fails(self):
        """Test assert_no_sql_injection fails."""
        with pytest.raises(Exception):
            assert_no_sql_injection("'; DROP TABLE users;--")

    def test_assert_no_pii_passes(self):
        """Test assert_no_pii passes."""
        assert_no_pii({"name": "John"})

    def test_assert_no_pii_fails(self):
        """Test assert_no_pii fails."""
        with pytest.raises(Exception):
            assert_no_pii({"email": "test@example.com"})
