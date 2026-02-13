"""Tests for privacy_sanitizer module."""

import re
from datetime import datetime

import pytest

from socialseed_e2e.shadow_runner.privacy_sanitizer import (
    PII_PATTERNS,
    GDPRComplianceChecker,
    PrivacySanitizer,
    SanitizationRule,
)
from socialseed_e2e.shadow_runner.traffic_interceptor import (
    CapturedInteraction,
    CapturedRequest,
    CapturedResponse,
)


class TestPIIPatterns:
    """Test suite for PII patterns."""

    def test_email_pattern(self):
        """Test email pattern matching."""
        pattern = PII_PATTERNS["email"]
        assert pattern.search("user@example.com")
        assert pattern.search("test.user@company.co.uk")
        assert not pattern.search("not-an-email")

    def test_phone_pattern(self):
        """Test phone pattern matching."""
        pattern = PII_PATTERNS["phone"]
        assert pattern.search("555-123-4567")
        assert pattern.search("(555) 123-4567")
        assert pattern.search("555.123.4567")

    def test_ssn_pattern(self):
        """Test SSN pattern matching."""
        pattern = PII_PATTERNS["ssn"]
        assert pattern.search("123-45-6789")

    def test_credit_card_pattern(self):
        """Test credit card pattern matching."""
        pattern = PII_PATTERNS["credit_card"]
        assert pattern.search("4111-1111-1111-1111")
        assert pattern.search("4111 1111 1111 1111")
        assert pattern.search("4111111111111111")

    def test_ip_address_pattern(self):
        """Test IP address pattern matching."""
        pattern = PII_PATTERNS["ip_address"]
        assert pattern.search("192.168.1.1")
        assert pattern.search("10.0.0.1")


class TestPrivacySanitizer:
    """Test suite for PrivacySanitizer class."""

    def test_sanitizer_creation(self):
        """Test creating a PrivacySanitizer instance."""
        sanitizer = PrivacySanitizer()

        assert sanitizer.custom_rules == []
        assert sanitizer.enabled is True

    def test_sanitize_email(self):
        """Test sanitizing email addresses."""
        sanitizer = PrivacySanitizer()

        text = "Contact us at user@example.com for support"
        sanitized = sanitizer._sanitize_text(text)

        assert "user@example.com" not in sanitized
        assert "[REDACTED]" in sanitized or "[HASH:" in sanitized

    def test_sanitize_phone(self):
        """Test sanitizing phone numbers."""
        sanitizer = PrivacySanitizer()

        text = "Call us at 555-123-4567"
        sanitized = sanitizer._sanitize_text(text)

        assert "555-123-4567" not in sanitized

    def test_sanitize_ssn(self):
        """Test sanitizing SSN."""
        sanitizer = PrivacySanitizer()

        text = "SSN: 123-45-6789"
        sanitized = sanitizer._sanitize_text(text)

        assert "123-45-6789" not in sanitized

    def test_sanitize_credit_card(self):
        """Test sanitizing credit card numbers."""
        sanitizer = PrivacySanitizer()

        text = "Card: 4111-1111-1111-1111"
        sanitized = sanitizer._sanitize_text(text)

        assert "4111-1111-1111-1111" not in sanitized

    def test_sanitize_request(self):
        """Test sanitizing a CapturedRequest."""
        sanitizer = PrivacySanitizer()

        request = CapturedRequest(
            method="POST",
            path="/api/users",
            headers={
                "Authorization": "Bearer secret-token",
                "Content-Type": "application/json",
            },
            body='{"email": "user@example.com", "password": "secret123"}',
        )

        sanitized = sanitizer.sanitize_request(request)

        assert "user@example.com" not in sanitized.body
        assert "secret123" not in sanitized.body
        assert "secret-token" not in sanitized.headers.get("Authorization", "")

    def test_sanitize_response(self):
        """Test sanitizing a CapturedResponse."""
        sanitizer = PrivacySanitizer()

        response = CapturedResponse(
            status_code=200,
            body='{"user": {"email": "test@test.com", "phone": "555-1234"}}',
        )

        sanitized = sanitizer.sanitize_response(response)

        assert "test@test.com" not in sanitized.body
        assert "555-1234" not in sanitized.body

    def test_sanitize_interaction(self):
        """Test sanitizing a CapturedInteraction."""
        sanitizer = PrivacySanitizer()

        interaction = CapturedInteraction(
            request=CapturedRequest(
                method="POST",
                path="/api/login",
                body='{"email": "admin@company.com", "password": "admin123"}',
            ),
            response=CapturedResponse(
                status_code=200,
                body='{"token": "secret-jwt-token", "user": {"email": "admin@company.com"}}',
            ),
        )

        sanitized = sanitizer.sanitize_interaction(interaction)

        assert "admin@company.com" not in sanitized.request.body
        assert "admin123" not in sanitized.request.body
        assert "secret-jwt-token" not in sanitized.response.body

    def test_add_custom_rule(self):
        """Test adding a custom sanitization rule."""
        sanitizer = PrivacySanitizer()

        rule = SanitizationRule(
            name="employee_id",
            pattern=re.compile(r"EMP\d{6}"),
            replacement="[EMP_ID]",
            description="Employee ID pattern",
        )

        sanitizer.add_rule(rule)

        text = "Employee ID: EMP123456"
        sanitized = sanitizer._sanitize_text(text)

        assert "EMP123456" not in sanitized
        assert "[EMP_ID]" in sanitized

    def test_hash_value(self):
        """Test hashing sensitive values."""
        sanitizer = PrivacySanitizer()

        value = "secret-value"
        hashed = sanitizer._hash_value(value)

        assert hashed != value
        assert "[HASH:" in hashed

    def test_no_false_positives(self):
        """Test that normal text isn't affected."""
        sanitizer = PrivacySanitizer()

        text = "This is a normal sentence without any PII."
        sanitized = sanitizer._sanitize_text(text)

        assert sanitized == text


class TestGDPRComplianceChecker:
    """Test suite for GDPRComplianceChecker class."""

    def test_checker_creation(self):
        """Test creating a GDPRComplianceChecker instance."""
        checker = GDPRComplianceChecker()

        assert checker.violations == []
        assert checker.checked_interactions == 0

    def test_check_email_in_request(self):
        """Test detecting email in request body."""
        checker = GDPRComplianceChecker()

        interaction = CapturedInteraction(
            request=CapturedRequest(
                method="POST",
                path="/api/users",
                body='{"email": "user@example.com"}',
            ),
            response=CapturedResponse(status_code=201),
        )

        violations = checker.check_interaction(interaction)

        assert len(violations) > 0
        assert any("email" in v.lower() for v in violations)

    def test_compliant_interaction(self):
        """Test that compliant interaction has no violations."""
        checker = GDPRComplianceChecker()

        interaction = CapturedInteraction(
            request=CapturedRequest(
                method="GET",
                path="/api/users",
            ),
            response=CapturedResponse(
                status_code=200,
                body='{"users": [{"id": 1}]}',
            ),
        )

        violations = checker.check_interaction(interaction)

        assert len(violations) == 0

    def test_check_session(self):
        """Test checking an entire session."""
        checker = GDPRComplianceChecker()

        from socialseed_e2e.shadow_runner.session_recorder import UserSession

        session = UserSession(
            session_id="test-session",
            user_id="user-1",
            interactions=[
                CapturedInteraction(
                    request=CapturedRequest(
                        method="POST",
                        path="/api/login",
                        body='{"email": "test@test.com"}',
                    ),
                    response=CapturedResponse(status_code=200),
                ),
            ],
        )

        report = checker.check_session(session)

        assert report["session_id"] == "test-session"
        assert report["total_interactions_checked"] == 1
        assert len(report["violations_found"]) > 0


class TestPrivacyIntegration:
    """Integration tests for privacy sanitization."""

    def test_full_sanitization_flow(self):
        """Test complete sanitization flow with multiple PII types."""
        sanitizer = PrivacySanitizer()

        interaction = CapturedInteraction(
            request=CapturedRequest(
                method="POST",
                path="/api/register",
                headers={"Authorization": "Bearer token123"},
                body="""{
                    "name": "John Doe",
                    "email": "john.doe@example.com",
                    "phone": "555-123-4567",
                    "password": "secretpass123"
                }""",
            ),
            response=CapturedResponse(
                status_code=201,
                body="""{
                    "id": 1,
                    "email": "john.doe@example.com",
                    "token": "jwt-token-here"
                }""",
            ),
        )

        sanitized = sanitizer.sanitize_interaction(interaction)

        # Verify all PII is removed
        assert "john.doe@example.com" not in sanitized.request.body
        assert "john.doe@example.com" not in sanitized.response.body
        assert "555-123-4567" not in sanitized.request.body
        assert "secretpass123" not in sanitized.request.body
        assert "token123" not in sanitized.request.headers.get("Authorization", "")
        assert "jwt-token-here" not in sanitized.response.body
