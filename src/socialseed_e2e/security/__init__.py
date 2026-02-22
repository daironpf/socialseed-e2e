"""
Security Testing Suite for socialseed-e2e.

This module provides comprehensive security testing capabilities:
- OWASP Top 10 vulnerability scanning
- Penetration testing automation
- Compliance testing (GDPR, PCI-DSS, HIPAA)
- Secret detection and PII scanning
- Security reporting and analysis
"""

from .models import (
    SecurityVulnerability,
    VulnerabilitySeverity,
    VulnerabilityCategory,
    SecurityScanResult,
    ComplianceStandard,
    ComplianceViolation,
    SecretFinding,
    SecretType,
    SecurityReport,
)
from .scanners.owasp_scanner import OWASPScanner
from .penetration.penetration_tester import PenetrationTester
from .compliance.compliance_validator import ComplianceValidator
from .detection.secret_detector import SecretDetector
from .reports.security_reporter import SecurityReporter
from .pii_detector import (
    PIIAnalyzer,
    PIIConfig,
    PIIDetection,
    PIIPattern,
    PIIType,
    SecurityComplianceReport,
    SecurityMiddleware,
    SeverityLevel,
)

__all__ = [
    "SecurityVulnerability",
    "VulnerabilitySeverity",
    "VulnerabilityCategory",
    "SecurityScanResult",
    "ComplianceStandard",
    "ComplianceViolation",
    "SecretFinding",
    "SecretType",
    "SecurityReport",
    "OWASPScanner",
    "PenetrationTester",
    "ComplianceValidator",
    "SecretDetector",
    "SecurityReporter",
    # PII Detection (Issue #3 - Phase 2)
    "PIIAnalyzer",
    "PIIConfig",
    "PIIDetection",
    "PIIPattern",
    "PIIType",
    "SecurityComplianceReport",
    "SecurityMiddleware",
    "SeverityLevel",
]
