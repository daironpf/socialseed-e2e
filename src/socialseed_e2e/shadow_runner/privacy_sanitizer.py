"""Privacy Sanitizer for Shadow Runner.

Anonymizes sensitive data (PII, passwords, tokens) from captured traffic.
"""

import hashlib
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Pattern

from socialseed_e2e.shadow_runner.traffic_interceptor import (
    CapturedInteraction,
    CapturedRequest,
    CapturedResponse,
)


# Common PII patterns
PII_PATTERNS = {
    "email": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    "phone": re.compile(r"(\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}"),
    "ssn": re.compile(r"\d{3}-\d{2}-\d{4}"),
    "credit_card": re.compile(r"\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}"),
    "ip_address": re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"),
}

# Sensitive headers to sanitize
SENSITIVE_HEADERS = {
    "authorization",
    "x-api-key",
    "x-auth-token",
    "cookie",
    "set-cookie",
    "x-csrf-token",
    "x-xsrf-token",
}

# Sensitive JSON fields
SENSITIVE_FIELDS = {
    "password",
    "passwd",
    "pwd",
    "secret",
    "token",
    "api_key",
    "apikey",
    "access_token",
    "refresh_token",
    "credit_card",
    "cvv",
    "ssn",
    "social_security",
    "dob",
    "date_of_birth",
    "phone",
    "email",
    "address",
    "name",
}


@dataclass
class SanitizationRule:
    """A rule for sanitizing data."""

    name: str
    pattern: Pattern
    replacement: str
    description: str = ""


class PrivacySanitizer:
    """Sanitizes sensitive data from captured traffic."""

    def __init__(self):
        """Initialize the privacy sanitizer."""
        self.custom_rules: List[SanitizationRule] = []
        self.hash_salt = "shadow_runner_salt"  # In production, use a secure random salt
        self.enabled = True

    def sanitize_interaction(
        self, interaction: CapturedInteraction
    ) -> CapturedInteraction:
        """Sanitize an interaction.

        Args:
            interaction: Interaction to sanitize

        Returns:
            Sanitized interaction
        """
        if not self.enabled:
            return interaction

        # Sanitize request
        sanitized_request = self.sanitize_request(interaction.request)

        # Sanitize response
        sanitized_response = None
        if interaction.response:
            sanitized_response = self.sanitize_response(interaction.response)

        # Create new interaction with sanitized data
        return CapturedInteraction(
            id=interaction.id,
            request=sanitized_request,
            response=sanitized_response,
            session_id=interaction.session_id,
            sequence_number=interaction.sequence_number,
            tags=interaction.tags + ["sanitized"],
        )

    def sanitize_request(self, request: CapturedRequest) -> CapturedRequest:
        """Sanitize a request.

        Args:
            request: Request to sanitize

        Returns:
            Sanitized request
        """
        # Sanitize headers
        sanitized_headers = self._sanitize_headers(request.headers)

        # Sanitize body
        sanitized_body = self._sanitize_body(request.body)

        # Sanitize query params
        sanitized_params = self._sanitize_query_params(request.query_params)

        return CapturedRequest(
            id=request.id,
            timestamp=request.timestamp,
            protocol=request.protocol,
            method=request.method,
            url=self._sanitize_url(request.url),
            path=request.path,
            headers=sanitized_headers,
            body=sanitized_body,
            query_params=sanitized_params,
            metadata={**request.metadata, "sanitized": True},
        )

    def sanitize_response(self, response: CapturedResponse) -> CapturedResponse:
        """Sanitize a response.

        Args:
            response: Response to sanitize

        Returns:
            Sanitized response
        """
        # Sanitize headers
        sanitized_headers = self._sanitize_headers(response.headers)

        # Sanitize body
        sanitized_body = self._sanitize_body(response.body)

        return CapturedResponse(
            id=response.id,
            request_id=response.request_id,
            timestamp=response.timestamp,
            status_code=response.status_code,
            headers=sanitized_headers,
            body=sanitized_body,
            latency_ms=response.latency_ms,
            metadata={**response.metadata, "sanitized": True},
        )

    def _sanitize_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Sanitize headers.

        Args:
            headers: Headers to sanitize

        Returns:
            Sanitized headers
        """
        sanitized = {}

        for key, value in headers.items():
            key_lower = key.lower()

            if key_lower in SENSITIVE_HEADERS:
                # Hash the sensitive value
                sanitized[key] = self._hash_value(value)
            elif "token" in key_lower or "key" in key_lower or "secret" in key_lower:
                sanitized[key] = self._hash_value(value)
            else:
                sanitized[key] = value

        return sanitized

    def _sanitize_body(self, body: Optional[str]) -> Optional[str]:
        """Sanitize request/response body.

        Args:
            body: Body to sanitize

        Returns:
            Sanitized body
        """
        if not body:
            return body

        # Try to parse as JSON
        try:
            import json

            data = json.loads(body)
            sanitized_data = self._sanitize_json(data)
            return json.dumps(sanitized_data)
        except json.JSONDecodeError:
            # Not JSON, try to sanitize as text
            return self._sanitize_text(body)

    def _sanitize_json(self, data: Any) -> Any:
        """Sanitize JSON data.

        Args:
            data: JSON data

        Returns:
            Sanitized data
        """
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                key_lower = key.lower()

                if key_lower in SENSITIVE_FIELDS:
                    # Sanitize sensitive field
                    sanitized[key] = self._mask_value(value)
                elif isinstance(value, (dict, list)):
                    sanitized[key] = self._sanitize_json(value)
                elif isinstance(value, str):
                    sanitized[key] = self._sanitize_pii_in_text(value)
                else:
                    sanitized[key] = value

            return sanitized

        elif isinstance(data, list):
            return [self._sanitize_json(item) for item in data]

        elif isinstance(data, str):
            return self._sanitize_pii_in_text(data)

        return data

    def _sanitize_query_params(self, params: Dict[str, str]) -> Dict[str, str]:
        """Sanitize query parameters.

        Args:
            params: Query parameters

        Returns:
            Sanitized parameters
        """
        sanitized = {}

        for key, value in params.items():
            key_lower = key.lower()

            if key_lower in SENSITIVE_FIELDS or "token" in key_lower:
                sanitized[key] = self._hash_value(value)
            else:
                sanitized[key] = value

        return sanitized

    def _sanitize_url(self, url: str) -> str:
        """Sanitize URL.

        Args:
            url: URL to sanitize

        Returns:
            Sanitized URL
        """
        # Remove credentials from URL
        import re

        # Pattern: protocol://user:pass@host
        url = re.sub(r"(https?://)[^@]+@", r"\1***@", url)

        return url

    def _sanitize_text(self, text: str) -> str:
        """Sanitize plain text.

        Args:
            text: Text to sanitize

        Returns:
            Sanitized text
        """
        # Apply PII patterns
        for pii_type, pattern in PII_PATTERNS.items():
            text = pattern.sub("[REDACTED]", text)

        # Apply custom rules
        for rule in self.custom_rules:
            text = rule.pattern.sub(rule.replacement, text)

        return text

    def _sanitize_pii_in_text(self, text: str) -> str:
        """Sanitize PII in text.

        Args:
            text: Text to sanitize

        Returns:
            Sanitized text
        """
        # Apply PII patterns
        for pii_type, pattern in PII_PATTERNS.items():
            text = pattern.sub(f"[{pii_type}_REDACTED]", text)

        return text

    def add_rule(self, rule: SanitizationRule) -> None:
        """Add a custom sanitization rule.

        Args:
            rule: Sanitization rule to add
        """
        self.custom_rules.append(rule)

    def _hash_value(self, value: str) -> str:
        """Hash a sensitive value.

        Args:
            value: Value to hash

        Returns:
            Hashed value
        """
        if not value:
            return value

        # Create hash
        hasher = hashlib.sha256()
        hasher.update(self.hash_salt.encode())
        hasher.update(value.encode())
        return f"[HASH:{hasher.hexdigest()[:16]}]"

        # Return shortened hash for readability
        return f"hash_{hasher.hexdigest()[:16]}"

    def _mask_value(self, value: Any) -> str:
        """Mask a sensitive value.

        Args:
            value: Value to mask

        Returns:
            Masked value
        """
        if value is None:
            return ""

        value_str = str(value)

        if len(value_str) <= 4:
            return "****"

        # Show first and last 2 characters
        return f"{value_str[:2]}****{value_str[-2:]}"

    def add_custom_rule(
        self, name: str, pattern: str, replacement: str, description: str = ""
    ) -> None:
        """Add a custom sanitization rule.

        Args:
            name: Rule name
            pattern: Regex pattern
            replacement: Replacement string
            description: Rule description
        """
        rule = SanitizationRule(
            name=name,
            pattern=re.compile(pattern),
            replacement=replacement,
            description=description,
        )
        self.custom_rules.append(rule)

    def remove_custom_rule(self, name: str) -> bool:
        """Remove a custom rule.

        Args:
            name: Rule name

        Returns:
            True if removed
        """
        for i, rule in enumerate(self.custom_rules):
            if rule.name == name:
                self.custom_rules.pop(i)
                return True
        return False

    def enable(self) -> None:
        """Enable sanitization."""
        self.enabled = True

    def disable(self) -> None:
        """Disable sanitization."""
        self.enabled = False

    def get_sanitization_report(
        self, interactions: List[CapturedInteraction]
    ) -> Dict[str, Any]:
        """Get a report of what would be sanitized.

        Args:
            interactions: List of interactions

        Returns:
            Sanitization report
        """
        report = {
            "total_interactions": len(interactions),
            "fields_sanitized": 0,
            "headers_sanitized": 0,
            "bodies_sanitized": 0,
            "pii_detected": {key: 0 for key in PII_PATTERNS.keys()},
        }

        for interaction in interactions:
            # Check request
            request = interaction.request

            # Check headers
            for header in request.headers:
                if header.lower() in SENSITIVE_HEADERS:
                    report["headers_sanitized"] += 1

            # Check body for PII
            if request.body:
                for pii_type, pattern in PII_PATTERNS.items():
                    matches = pattern.findall(request.body)
                    report["pii_detected"][pii_type] += len(matches)

            # Check response
            if interaction.response:
                response = interaction.response

                for header in response.headers:
                    if header.lower() in SENSITIVE_HEADERS:
                        report["headers_sanitized"] += 1

                if response.body:
                    for pii_type, pattern in PII_PATTERNS.items():
                        matches = pattern.findall(response.body)
                        report["pii_detected"][pii_type] += len(matches)

        return report


class GDPRComplianceChecker:
    """Checks GDPR compliance of captured data."""

    GDPR_SENSITIVE_FIELDS = {
        "race",
        "ethnicity",
        "political_opinions",
        "religious_beliefs",
        "trade_union_membership",
        "health",
        "sex_life",
        "sexual_orientation",
        "genetic_data",
        "biometric_data",
    }

    def __init__(self):
        """Initialize GDPR checker."""
        self.violations: List[str] = []
        self.checked_interactions = 0

    def check_interaction(self, interaction: CapturedInteraction) -> List[str]:
        """Check an interaction for GDPR compliance.

        Args:
            interaction: Interaction to check

        Returns:
            List of violation messages
        """
        self.checked_interactions += 1
        violations = []

        # Check request body for PII
        if interaction.request.body:
            if PII_PATTERNS["email"].search(interaction.request.body):
                violations.append("Email detected in request body")
            if PII_PATTERNS["phone"].search(interaction.request.body):
                violations.append("Phone number detected in request body")
            if PII_PATTERNS["ssn"].search(interaction.request.body):
                violations.append("SSN detected in request body")

        # Check response body for PII
        if interaction.response and interaction.response.body:
            if PII_PATTERNS["email"].search(interaction.response.body):
                violations.append("Email detected in response body")
            if PII_PATTERNS["phone"].search(interaction.response.body):
                violations.append("Phone number detected in response body")
            if PII_PATTERNS["ssn"].search(interaction.response.body):
                violations.append("SSN detected in response body")

        # Check for GDPR sensitive fields
        if interaction.request.body:
            body_violations = self._check_body(interaction.request.body)
            for v in body_violations:
                violations.append(v["message"])

        if interaction.response and interaction.response.body:
            body_violations = self._check_body(interaction.response.body)
            for v in body_violations:
                violations.append(v["message"])

        return violations

    def _contains_pii(self, text: str) -> bool:
        """Check if text contains PII.

        Args:
            text: Text to check

        Returns:
            True if PII detected
        """
        # Check for email addresses
        if PII_PATTERNS["email"].search(text):
            return True
        # Check for phone numbers
        if PII_PATTERNS["phone"].search(text):
            return True
        # Check for SSN
        if PII_PATTERNS["ssn"].search(text):
            return True
        return False

    def check_session(self, session) -> Dict[str, Any]:
        """Check an entire session for GDPR compliance.

        Args:
            session: UserSession to check

        Returns:
            Compliance report dictionary
        """
        all_violations = []

        for interaction in session.interactions:
            violations = self.check_interaction(interaction)
            all_violations.extend(violations)

        return {
            "session_id": session.id,
            "total_interactions_checked": len(session.interactions),
            "violations_found": all_violations,
        }

    def _check_body(self, body: str) -> List[Dict[str, Any]]:
        """Check body for GDPR sensitive data.

        Args:
            body: Body to check

        Returns:
            List of violations
        """
        violations = []

        try:
            import json

            data = json.loads(body)

            if isinstance(data, dict):
                for key in data.keys():
                    key_lower = key.lower().replace(" ", "_")
                    if key_lower in self.GDPR_SENSITIVE_FIELDS:
                        violations.append(
                            {
                                "type": "gdpr_sensitive_field",
                                "field": key,
                                "severity": "high",
                                "message": f"GDPR sensitive field detected: {key}",
                            }
                        )
        except json.JSONDecodeError:
            pass

        return violations

    def get_compliance_report(self) -> Dict[str, Any]:
        """Get compliance report.

        Returns:
            Compliance report
        """
        return {
            "total_violations": len(self.violations),
            "violations_by_type": self._categorize_violations(),
            "recommendations": self._generate_recommendations(),
        }

    def _categorize_violations(self) -> Dict[str, int]:
        """Categorize violations by type."""
        categories = {}
        for v in self.violations:
            vtype = v.get("type", "unknown")
            categories[vtype] = categories.get(vtype, 0) + 1
        return categories

    def _generate_recommendations(self) -> List[str]:
        """Generate compliance recommendations."""
        recommendations = []

        if any(v.get("type") == "gdpr_sensitive_field" for v in self.violations):
            recommendations.append(
                "Consider implementing data minimization - only capture necessary fields"
            )
            recommendations.append(
                "Ensure explicit consent is obtained before capturing sensitive data"
            )

        return recommendations
