"""
Compliance testing validators for GDPR, PCI-DSS, HIPAA, SOC2, and ISO27001.

Validates APIs against compliance standards and regulations.
"""

import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..models import (
    ComplianceStandard,
    ComplianceViolation,
    VulnerabilitySeverity,
)


class ComplianceValidator:
    """Validates APIs against compliance standards.

    Supports GDPR, PCI-DSS, HIPAA, SOC2, and ISO27001 compliance checks.

    Example:
        validator = ComplianceValidator()

        # Validate against GDPR
        violations = validator.validate_gdpr(
            endpoint="https://api.example.com/users",
            collects_pii=True,
            has_consent_mechanism=True
        )
    """

    # GDPR PII patterns
    GDPR_PII_PATTERNS = [
        (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "email_address"),
        (r"\b\d{3}-\d{2}-\d{4}\b", "ssn"),
        (r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b", "credit_card"),
        (r"\b[A-Z]{2}\d{2}\s?\d[A-Z]{2}\b", "postal_code"),
        (r"\b\d{3}-\d{3}-\d{4}\b", "phone_number"),
        (r"(password|passwd|pwd)\s*[=:]\s*\S+", "password"),
        (r"(ip_address|ip)\s*[=:]\s*\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", "ip_address"),
    ]

    # PCI-DSS patterns
    PCI_PATTERNS = [
        (r"\b4\d{3}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b", "visa_card"),
        (r"\b5[1-5]\d{2}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b", "mastercard"),
        (r"\b3[47]\d{2}[\s-]?\d{6}[\s-]?\d{5}\b", "amex_card"),
        (r"cvv[\s]*[=:]\s*\d{3,4}", "cvv"),
        (r"(track1|track2)[\s]*[=:]\s*[^\s]+", "card_track_data"),
    ]

    # HIPAA PHI patterns (Protected Health Information)
    HIPAA_PHI_PATTERNS = [
        (r"\b\d{3}-\d{2}-\d{4}\b", "ssn"),
        (r"(mrn|patient_id|medical_record)[\s]*[=:]\s*\d+", "medical_record_number"),
        (r"(diagnosis|condition|treatment)[\s]*[=:]\s*[^\s]+", "health_condition"),
        (r"(prescription|medication|drug)[\s]*[=:]\s*[^\s]+", "prescription_info"),
    ]

    def __init__(self):
        """Initialize compliance validator."""
        self.violations: List[ComplianceViolation] = []

    def validate_gdpr(
        self,
        endpoint: str,
        collects_pii: bool = False,
        has_consent_mechanism: bool = False,
        has_data_retention_policy: bool = False,
        has_right_to_deletion: bool = False,
        has_data_portability: bool = False,
        encrypts_data: bool = False,
        response_content: Optional[str] = None,
    ) -> List[ComplianceViolation]:
        """Validate GDPR compliance.

        Args:
            endpoint: API endpoint URL
            collects_pii: Whether the endpoint collects PII
            has_consent_mechanism: Whether explicit consent is obtained
            has_data_retention_policy: Whether data retention policy exists
            has_right_to_deletion: Whether right to deletion is supported
            has_data_portability: Whether data portability is supported
            encrypts_data: Whether data is encrypted
            response_content: Optional response content to analyze

        Returns:
            List of compliance violations
        """
        self.violations = []

        # Check for PII in response
        if response_content:
            self._check_gdpr_pii(endpoint, response_content)

        # Check consent mechanism
        if collects_pii and not has_consent_mechanism:
            self._add_violation(
                standard=ComplianceStandard.GDPR,
                requirement="Article 6 - Lawfulness of Processing",
                title="Missing Consent Mechanism",
                description="API collects PII without explicit consent mechanism",
                severity=VulnerabilitySeverity.HIGH,
                endpoint=endpoint,
                remediation="Implement explicit consent collection with clear opt-in mechanism. Maintain audit trail of consent.",
            )

        # Check data encryption
        if collects_pii and not encrypts_data:
            self._add_violation(
                standard=ComplianceStandard.GDPR,
                requirement="Article 32 - Security of Processing",
                title="PII Not Encrypted",
                description="PII is collected without encryption",
                severity=VulnerabilitySeverity.CRITICAL,
                endpoint=endpoint,
                remediation="Encrypt all PII at rest and in transit using strong encryption (AES-256, TLS 1.2+).",
            )

        # Check data retention
        if collects_pii and not has_data_retention_policy:
            self._add_violation(
                standard=ComplianceStandard.GDPR,
                requirement="Article 5 - Principles of Processing",
                title="No Data Retention Policy",
                description="No data retention policy defined for PII",
                severity=VulnerabilitySeverity.MEDIUM,
                endpoint=endpoint,
                remediation="Define and implement data retention policies. Automatically delete data after retention period.",
            )

        # Check right to deletion
        if collects_pii and not has_right_to_deletion:
            self._add_violation(
                standard=ComplianceStandard.GDPR,
                requirement="Article 17 - Right to Erasure",
                title="Right to Deletion Not Implemented",
                description="Users cannot delete their data",
                severity=VulnerabilitySeverity.HIGH,
                endpoint=endpoint,
                remediation="Implement data deletion endpoint. Ensure complete removal including backups and logs.",
            )

        # Check data portability
        if collects_pii and not has_data_portability:
            self._add_violation(
                standard=ComplianceStandard.GDPR,
                requirement="Article 20 - Right to Data Portability",
                title="Data Portability Not Supported",
                description="Users cannot export their data in machine-readable format",
                severity=VulnerabilitySeverity.MEDIUM,
                endpoint=endpoint,
                remediation="Implement data export functionality supporting JSON, CSV, or XML formats.",
            )

        return self.violations

    def validate_pci_dss(
        self,
        endpoint: str,
        processes_payments: bool = False,
        encrypts_cardholder_data: bool = False,
        uses_tokenization: bool = False,
        has_access_controls: bool = False,
        has_monitoring: bool = False,
        response_content: Optional[str] = None,
    ) -> List[ComplianceViolation]:
        """Validate PCI-DSS compliance.

        Args:
            endpoint: API endpoint URL
            processes_payments: Whether endpoint processes payments
            encrypts_cardholder_data: Whether cardholder data is encrypted
            uses_tokenization: Whether tokenization is used
            has_access_controls: Whether access controls are implemented
            has_monitoring: Whether monitoring/logging is enabled
            response_content: Optional response content to analyze

        Returns:
            List of compliance violations
        """
        self.violations = []

        # Check for cardholder data in response
        if response_content:
            self._check_pci_data(endpoint, response_content)

        if not processes_payments:
            return self.violations

        # Requirement 3: Protect stored cardholder data
        if not encrypts_cardholder_data and not uses_tokenization:
            self._add_violation(
                standard=ComplianceStandard.PCI_DSS,
                requirement="Requirement 3 - Protect Stored Cardholder Data",
                title="Unencrypted Cardholder Data",
                description="Cardholder data is stored without encryption or tokenization",
                severity=VulnerabilitySeverity.CRITICAL,
                endpoint=endpoint,
                remediation="Use strong cryptography (AES-256) or tokenization to protect stored cardholder data.",
            )

        # Requirement 7: Restrict access
        if not has_access_controls:
            self._add_violation(
                standard=ComplianceStandard.PCI_DSS,
                requirement="Requirement 7 - Restrict Access",
                title="Missing Access Controls",
                description="Access controls for cardholder data not implemented",
                severity=VulnerabilitySeverity.HIGH,
                endpoint=endpoint,
                remediation="Implement need-to-know access controls. Use role-based access control (RBAC).",
            )

        # Requirement 10: Monitor networks
        if not has_monitoring:
            self._add_violation(
                standard=ComplianceStandard.PCI_DSS,
                requirement="Requirement 10 - Monitor Networks",
                title="Insufficient Logging",
                description="Payment processing not properly monitored",
                severity=VulnerabilitySeverity.HIGH,
                endpoint=endpoint,
                remediation="Implement comprehensive logging for all payment transactions. Monitor for suspicious activity.",
            )

        # Requirement 4: Encrypt transmission
        if not endpoint.startswith("https://"):
            self._add_violation(
                standard=ComplianceStandard.PCI_DSS,
                requirement="Requirement 4 - Encrypt Transmission",
                title="Insecure Transmission",
                description="Cardholder data transmitted over unencrypted channel",
                severity=VulnerabilitySeverity.CRITICAL,
                endpoint=endpoint,
                remediation="Use TLS 1.2 or higher for all cardholder data transmission.",
            )

        return self.violations

    def validate_hipaa(
        self,
        endpoint: str,
        handles_phi: bool = False,
        has_baa: bool = False,
        encrypts_phi: bool = False,
        has_access_audit: bool = False,
        has_minimum_necessary: bool = False,
        response_content: Optional[str] = None,
    ) -> List[ComplianceViolation]:
        """Validate HIPAA compliance.

        Args:
            endpoint: API endpoint URL
            handles_phi: Whether endpoint handles Protected Health Information
            has_baa: Whether Business Associate Agreement exists
            encrypts_phi: Whether PHI is encrypted
            has_access_audit: Whether access is audited
            has_minimum_necessary: Whether minimum necessary rule is implemented
            response_content: Optional response content to analyze

        Returns:
            List of compliance violations
        """
        self.violations = []

        # Check for PHI in response
        if response_content:
            self._check_hipaa_phi(endpoint, response_content)

        if not handles_phi:
            return self.violations

        # Check Business Associate Agreement
        if not has_baa:
            self._add_violation(
                standard=ComplianceStandard.HIPAA,
                requirement="164.504(e) - Business Associate Contracts",
                title="Missing Business Associate Agreement",
                description="No Business Associate Agreement (BAA) in place",
                severity=VulnerabilitySeverity.HIGH,
                endpoint=endpoint,
                remediation="Establish Business Associate Agreement with all vendors handling PHI.",
            )

        # Check encryption (Addressable under Security Rule)
        if not encrypts_phi:
            self._add_violation(
                standard=ComplianceStandard.HIPAA,
                requirement="164.312(a)(2)(iv) - Encryption",
                title="PHI Not Encrypted",
                description="Protected Health Information is not encrypted",
                severity=VulnerabilitySeverity.CRITICAL,
                endpoint=endpoint,
                remediation="Implement encryption for PHI at rest (AES-256) and in transit (TLS 1.2+).",
            )

        # Check access audit
        if not has_access_audit:
            self._add_violation(
                standard=ComplianceStandard.HIPAA,
                requirement="164.312(b) - Audit Controls",
                title="Missing Audit Controls",
                description="Access to PHI is not audited",
                severity=VulnerabilitySeverity.HIGH,
                endpoint=endpoint,
                remediation="Implement audit logging for all PHI access. Regularly review audit logs.",
            )

        # Check minimum necessary rule
        if not has_minimum_necessary:
            self._add_violation(
                standard=ComplianceStandard.HIPAA,
                requirement="164.502(b) - Minimum Necessary",
                title="Minimum Necessary Rule Not Implemented",
                description="PHI disclosure not limited to minimum necessary",
                severity=VulnerabilitySeverity.MEDIUM,
                endpoint=endpoint,
                remediation="Implement minimum necessary rule. Limit PHI access to what is required for specific purpose.",
            )

        return self.violations

    def validate_all(
        self, endpoint: str, standards: List[ComplianceStandard], **kwargs
    ) -> Dict[ComplianceStandard, List[ComplianceViolation]]:
        """Validate against multiple compliance standards.

        Args:
            endpoint: API endpoint URL
            standards: List of standards to validate
            **kwargs: Additional validation parameters

        Returns:
            Dictionary mapping standards to violations
        """
        results = {}

        for standard in standards:
            if standard == ComplianceStandard.GDPR:
                results[standard] = self.validate_gdpr(endpoint, **kwargs)
            elif standard == ComplianceStandard.PCI_DSS:
                results[standard] = self.validate_pci_dss(endpoint, **kwargs)
            elif standard == ComplianceStandard.HIPAA:
                results[standard] = self.validate_hipaa(endpoint, **kwargs)

        return results

    def _check_gdpr_pii(self, endpoint: str, content: str):
        """Check for PII in content (GDPR)."""
        for pattern, pii_type in self.GDPR_PII_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                self._add_violation(
                    standard=ComplianceStandard.GDPR,
                    requirement="Article 5 - Data Minimization",
                    title=f"PII Exposed in Response - {pii_type}",
                    description=f"API response contains {pii_type} in plaintext",
                    severity=VulnerabilitySeverity.CRITICAL,
                    endpoint=endpoint,
                    evidence=f"Pattern matched: {pattern[:30]}...",
                    remediation="Remove unnecessary PII from API responses. Mask or tokenize required data.",
                )

    def _check_pci_data(self, endpoint: str, content: str):
        """Check for cardholder data in content (PCI-DSS)."""
        for pattern, data_type in self.PCI_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                self._add_violation(
                    standard=ComplianceStandard.PCI_DSS,
                    requirement="Requirement 3 - Protect Stored Cardholder Data",
                    title=f"Cardholder Data Exposed - {data_type}",
                    description=f"API response contains {data_type} in plaintext",
                    severity=VulnerabilitySeverity.CRITICAL,
                    endpoint=endpoint,
                    evidence=f"Pattern matched: {pattern[:30]}...",
                    remediation="Never return full card numbers, CVV, or track data. Use tokenization.",
                )

    def _check_hipaa_phi(self, endpoint: str, content: str):
        """Check for PHI in content (HIPAA)."""
        for pattern, phi_type in self.HIPAA_PHI_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                self._add_violation(
                    standard=ComplianceStandard.HIPAA,
                    requirement="164.502 - Uses and Disclosures",
                    title=f"PHI Exposed in Response - {phi_type}",
                    description=f"API response contains {phi_type} without proper authorization",
                    severity=VulnerabilitySeverity.CRITICAL,
                    endpoint=endpoint,
                    evidence=f"Pattern matched: {pattern[:30]}...",
                    remediation="Limit PHI in responses. Implement de-identification where possible.",
                )

    def _add_violation(
        self,
        standard: ComplianceStandard,
        requirement: str,
        title: str,
        description: str,
        severity: VulnerabilitySeverity,
        remediation: str,
        endpoint: Optional[str] = None,
        evidence: Optional[str] = None,
    ):
        """Add a compliance violation."""
        violation = ComplianceViolation(
            id=str(uuid.uuid4()),
            standard=standard,
            requirement=requirement,
            title=title,
            description=description,
            severity=severity,
            endpoint=endpoint,
            evidence=evidence,
            remediation=remediation,
        )

        self.violations.append(violation)
