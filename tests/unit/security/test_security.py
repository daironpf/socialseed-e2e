"""
Unit tests for security testing suite.
"""

import pytest
from datetime import datetime

from socialseed_e2e.security import (
    OWASPScanner,
    PenetrationTester,
    ComplianceValidator,
    SecretDetector,
    SecurityReporter,
)
from socialseed_e2e.security.models import (
    SecurityVulnerability,
    SecretFinding,
    ComplianceViolation,
    VulnerabilitySeverity,
    VulnerabilityCategory,
    SecretType,
    ComplianceStandard,
)


class TestOWASPScanner:
    """Test OWASP Top 10 scanner."""

    def test_scanner_initialization(self):
        scanner = OWASPScanner()
        assert scanner is not None
        assert scanner.vulnerabilities == []

    def test_scan_endpoint_basic(self):
        scanner = OWASPScanner()
        result = scanner.scan_endpoint("https://example.com/api/users")

        assert result.scan_id is not None
        assert result.target == "https://example.com/api/users"
        assert result.scan_type == "owasp_top10"
        assert result.status in ["completed", "failed"]

    def test_scan_endpoint_with_sql_injection(self):
        scanner = OWASPScanner()
        result = scanner.scan_endpoint(
            "https://example.com/api/users", params={"id": "1' OR '1'='1"}
        )

        # Should detect SQL injection
        sql_injection_vulns = [
            v
            for v in result.vulnerabilities
            if v.category == VulnerabilityCategory.INJECTION and "SQL" in v.title
        ]
        assert len(sql_injection_vulns) > 0

    def test_scan_endpoint_with_xss(self):
        scanner = OWASPScanner()
        result = scanner.scan_endpoint(
            "https://example.com/api/users",
            params={"name": "<script>alert('xss')</script>"},
        )

        # Should detect XSS
        xss_vulns = [
            v for v in result.vulnerabilities if v.category == VulnerabilityCategory.XSS
        ]
        assert len(xss_vulns) > 0

    def test_scan_api_multiple_endpoints(self):
        scanner = OWASPScanner()
        results = scanner.scan_api("https://example.com")

        assert len(results) > 0
        for result in results:
            assert result.scan_id is not None
            assert result.target is not None


class TestPenetrationTester:
    """Test penetration testing module."""

    def test_tester_initialization(self):
        tester = PenetrationTester()
        assert tester is not None
        assert tester.vulnerabilities == []

    def test_authentication_bypass_test(self):
        tester = PenetrationTester()
        result = tester.test_authentication_bypass(
            login_endpoint="https://example.com/login",
            protected_endpoint="https://example.com/admin",
        )

        assert result.scan_id is not None
        assert result.scan_type == "authentication_bypass"
        assert result.status in ["completed", "failed"]

    def test_privilege_escalation_test(self):
        tester = PenetrationTester()
        result = tester.test_privilege_escalation(
            base_endpoint="https://example.com",
            user_endpoints=["/api/users/1"],
            admin_endpoints=["/api/admin"],
        )

        assert result.scan_id is not None
        assert result.scan_type == "privilege_escalation"

    def test_session_management_test(self):
        tester = PenetrationTester()
        result = tester.test_session_management("https://example.com/api")

        assert result.scan_id is not None
        assert result.scan_type == "session_management"

    def test_idor_test(self):
        tester = PenetrationTester()
        result = tester.test_idor("/api/users/{id}", id_range=range(1, 5))

        assert result.scan_id is not None
        assert result.scan_type == "idor"


class TestComplianceValidator:
    """Test compliance validation module."""

    def test_validator_initialization(self):
        validator = ComplianceValidator()
        assert validator is not None

    def test_gdpr_validation_no_pii(self):
        validator = ComplianceValidator()
        violations = validator.validate_gdpr(
            "https://example.com/api", collects_pii=False
        )

        assert len(violations) == 0

    def test_gdpr_validation_with_pii(self):
        validator = ComplianceValidator()
        violations = validator.validate_gdpr(
            "https://example.com/api",
            collects_pii=True,
            has_consent_mechanism=False,
            encrypts_data=False,
        )

        assert len(violations) > 0

        # Check for specific GDPR violations
        consent_violations = [v for v in violations if "consent" in v.title.lower()]
        encryption_violations = [v for v in violations if "encrypt" in v.title.lower()]

        assert len(consent_violations) > 0
        assert len(encryption_violations) > 0

    def test_gdpr_pii_detection_in_response(self):
        validator = ComplianceValidator()
        response_content = "User email: test@example.com and SSN: 123-45-6789"

        violations = validator.validate_gdpr(
            "https://example.com/api",
            collects_pii=True,
            response_content=response_content,
        )

        # Should detect PII exposure
        pii_violations = [
            v for v in violations if "PII" in v.title or "email" in v.title.lower()
        ]
        assert len(pii_violations) > 0

    def test_pci_dss_validation(self):
        validator = ComplianceValidator()
        violations = validator.validate_pci_dss(
            "http://example.com/payment",  # HTTP instead of HTTPS
            processes_payments=True,
            encrypts_cardholder_data=False,
        )

        assert len(violations) > 0

        # Should detect insecure transmission
        insecure_violations = [
            v
            for v in violations
            if "transmission" in v.title.lower() or "encrypt" in v.title.lower()
        ]
        assert len(insecure_violations) > 0

    def test_hipaa_validation(self):
        validator = ComplianceValidator()
        violations = validator.validate_hipaa(
            "https://example.com/patient",
            handles_phi=True,
            has_baa=False,
            encrypts_phi=False,
        )

        assert len(violations) > 0

        # Check for BAA violation
        baa_violations = [
            v for v in violations if "BAA" in v.title or "Business Associate" in v.title
        ]
        assert len(baa_violations) > 0


class TestSecretDetector:
    """Test secret and PII detection."""

    def test_detector_initialization(self):
        detector = SecretDetector()
        assert detector is not None

    def test_scan_text_api_key(self):
        detector = SecretDetector()
        text = "api_key=sk_live_abcdef123456789"
        findings = detector.scan_text(text)

        assert len(findings) > 0
        api_key_findings = [f for f in findings if f.type == SecretType.API_KEY]
        assert len(api_key_findings) > 0

    def test_scan_text_aws_key(self):
        detector = SecretDetector()
        text = "AWS Access Key: AKIAIOSFODNN7EXAMPLE"
        findings = detector.scan_text(text)

        aws_findings = [f for f in findings if f.type == SecretType.AWS_KEY]
        assert len(aws_findings) > 0

    def test_scan_text_private_key(self):
        detector = SecretDetector()
        text = "-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA..."
        findings = detector.scan_text(text)

        key_findings = [f for f in findings if f.type == SecretType.PRIVATE_KEY]
        assert len(key_findings) > 0

    def test_scan_text_credit_card(self):
        detector = SecretDetector()
        text = "Card number: 4532-1234-5678-9012"
        findings = detector.scan_text(text)

        cc_findings = [f for f in findings if f.type == SecretType.CREDIT_CARD]
        assert len(cc_findings) > 0

    def test_scan_text_ssn(self):
        detector = SecretDetector()
        text = "SSN: 123-45-6789"
        findings = detector.scan_text(text)

        ssn_findings = [f for f in findings if f.type == SecretType.SSN]
        assert len(ssn_findings) > 0

    def test_scan_text_email(self):
        detector = SecretDetector()
        text = "Contact: user@example.com"
        findings = detector.scan_text(text)

        email_findings = [f for f in findings if f.type == SecretType.EMAIL]
        assert len(email_findings) > 0

    def test_scan_text_without_pii(self):
        detector = SecretDetector()
        text = "Contact: user@example.com"
        findings = detector.scan_text(text, include_pii=False)

        email_findings = [f for f in findings if f.type == SecretType.EMAIL]
        assert len(email_findings) == 0

    def test_mask_content(self):
        detector = SecretDetector()
        masked = detector._mask_content("secret_api_key_12345")

        assert "****" in masked
        assert len(masked) < len("secret_api_key_12345")

    def test_get_severity(self):
        detector = SecretDetector()

        assert (
            detector._get_severity(SecretType.AWS_KEY) == VulnerabilitySeverity.CRITICAL
        )
        assert (
            detector._get_severity(SecretType.PRIVATE_KEY)
            == VulnerabilitySeverity.CRITICAL
        )
        assert detector._get_severity(SecretType.API_KEY) == VulnerabilitySeverity.HIGH
        assert detector._get_severity(SecretType.EMAIL) == VulnerabilitySeverity.LOW


class TestSecurityReporter:
    """Test security reporting module."""

    def test_reporter_initialization(self):
        reporter = SecurityReporter(project_name="Test Project")
        assert reporter is not None
        assert reporter.project_name == "Test Project"

    def test_generate_report(self):
        reporter = SecurityReporter(project_name="Test API")

        report = reporter.generate_report()

        assert report.report_id is not None
        assert report.project_name == "Test API"
        assert report.risk_score >= 0
        assert report.risk_score <= 100
        assert report.risk_level in ["critical", "high", "medium", "low", "minimal"]

    def test_calculate_risk_score(self):
        reporter = SecurityReporter()

        # Empty should be 0
        assert reporter._calculate_risk_score() == 0.0

        # Add vulnerabilities
        vuln = SecurityVulnerability(
            id="test1",
            title="Test Vuln",
            description="Test",
            category=VulnerabilityCategory.INJECTION,
            severity=VulnerabilitySeverity.CRITICAL,
            endpoint="/test",
            remediation="Fix it",
        )
        reporter.add_vulnerabilities([vuln])

        score = reporter._calculate_risk_score()
        assert score > 0
        assert score <= 100

    def test_get_risk_level(self):
        reporter = SecurityReporter()

        assert reporter._get_risk_level(90) == "critical"
        assert reporter._get_risk_level(70) == "high"
        assert reporter._get_risk_level(50) == "medium"
        assert reporter._get_risk_level(30) == "low"
        assert reporter._get_risk_level(10) == "minimal"

    def test_generate_recommendations(self):
        reporter = SecurityReporter()

        # Default recommendation
        recs = reporter._generate_recommendations()
        assert len(recs) > 0
        assert "Continue regular security testing" in recs[0]

        # Add critical vulnerability
        vuln = SecurityVulnerability(
            id="test1",
            title="Test",
            description="Test",
            category=VulnerabilityCategory.INJECTION,
            severity=VulnerabilitySeverity.CRITICAL,
            endpoint="/test",
            remediation="Fix",
        )
        reporter.add_vulnerabilities([vuln])

        recs = reporter._generate_recommendations()
        assert any("URGENT" in r for r in recs)

    def test_export_json(self, tmp_path):
        reporter = SecurityReporter(project_name="Test")
        output_file = tmp_path / "report.json"

        result = reporter.export_json(str(output_file))

        assert result == str(output_file)
        assert output_file.exists()

    def test_generate_summary(self):
        reporter = SecurityReporter(project_name="Test API")

        summary = reporter.generate_summary()

        assert summary["project"] == "Test API"
        assert "generated_at" in summary
        assert "total_vulnerabilities" in summary
        assert "risk_score" in summary
        assert "risk_level" in summary


class TestSecurityModels:
    """Test security data models."""

    def test_vulnerability_creation(self):
        vuln = SecurityVulnerability(
            id="vuln-001",
            title="SQL Injection",
            description="SQL injection vulnerability",
            category=VulnerabilityCategory.INJECTION,
            severity=VulnerabilitySeverity.CRITICAL,
            cvss_score=9.8,
            endpoint="/api/users",
            remediation="Use parameterized queries",
        )

        assert vuln.id == "vuln-001"
        assert vuln.title == "SQL Injection"
        assert vuln.cvss_score == 9.8
        assert vuln.category == VulnerabilityCategory.INJECTION

    def test_secret_finding_creation(self):
        finding = SecretFinding(
            id="secret-001",
            type=SecretType.API_KEY,
            severity=VulnerabilitySeverity.HIGH,
            matched_content="sk_live_12345",
            masked_content="sk_****2345",
            pattern_name="api_key_pattern",
        )

        assert finding.id == "secret-001"
        assert finding.type == SecretType.API_KEY
        assert finding.masked_content == "sk_****2345"

    def test_compliance_violation_creation(self):
        violation = ComplianceViolation(
            id="comp-001",
            standard=ComplianceStandard.GDPR,
            requirement="Article 32",
            title="Unencrypted Data",
            description="PII not encrypted",
            severity=VulnerabilitySeverity.CRITICAL,
            remediation="Enable encryption",
        )

        assert violation.standard == ComplianceStandard.GDPR
        assert violation.requirement == "Article 32"


class TestSecurityIntegration:
    """Integration tests for security suite."""

    def test_full_security_workflow(self):
        """Test complete security testing workflow."""
        target = "https://example.com/api"

        # OWASP Scan
        scanner = OWASPScanner()
        scan_result = scanner.scan_endpoint(target)

        # Secret Detection
        detector = SecretDetector()
        secrets = detector.scan_text("api_key=sk_live_test")

        # Compliance Check
        validator = ComplianceValidator()
        violations = validator.validate_gdpr(target, collects_pii=True)

        # Generate Report
        reporter = SecurityReporter(project_name="Integration Test")
        reporter.add_scan_result(scan_result)
        reporter.add_secrets(secrets)
        reporter.add_compliance_violations(violations)

        report = reporter.generate_report()

        assert report.total_scans >= 1
        assert report.total_secrets >= 1
        assert report.risk_score is not None
