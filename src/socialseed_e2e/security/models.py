"""
Models for security testing suite.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field


class VulnerabilitySeverity(str, Enum):
    """Severity levels for vulnerabilities."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class VulnerabilityCategory(str, Enum):
    """OWASP Top 10 vulnerability categories."""

    INJECTION = "injection"  # A01:2021
    BROKEN_AUTH = "broken_authentication"  # A02:2021
    SENSITIVE_DATA = "sensitive_data_exposure"  # A03:2021
    XXE = "xml_external_entities"  # A04:2021
    BROKEN_ACCESS = "broken_access_control"  # A05:2021
    SECURITY_MISCONFIG = "security_misconfiguration"  # A06:2021
    XSS = "cross_site_scripting"  # A07:2021
    INSECURE_DESERIALIZATION = "insecure_deserialization"  # A08:2021
    VULNERABLE_COMPONENTS = "vulnerable_components"  # A09:2021
    INSUFFICIENT_LOGGING = "insufficient_logging"  # A10:2021
    SSRF = "server_side_request_forgery"  # A11:2021


class SecretType(str, Enum):
    """Types of secrets that can be detected."""

    API_KEY = "api_key"
    AWS_KEY = "aws_access_key"
    DATABASE_URL = "database_url"
    PRIVATE_KEY = "private_key"
    PASSWORD = "password"
    TOKEN = "token"
    JWT = "jwt_token"
    OAUTH = "oauth_token"
    CREDIT_CARD = "credit_card"
    SSN = "social_security_number"
    EMAIL = "email_address"
    PHONE = "phone_number"


class ComplianceStandard(str, Enum):
    """Supported compliance standards."""

    GDPR = "gdpr"
    PCI_DSS = "pci_dss"
    HIPAA = "hipaa"
    SOC2 = "soc2"
    ISO27001 = "iso27001"


class SecurityVulnerability(BaseModel):
    """Represents a security vulnerability."""

    id: str = Field(..., description="Unique vulnerability ID")
    title: str = Field(..., description="Vulnerability title")
    description: str = Field(..., description="Detailed description")
    category: VulnerabilityCategory = Field(..., description="OWASP category")
    severity: VulnerabilitySeverity = Field(..., description="Severity level")
    cvss_score: Optional[float] = Field(default=None, description="CVSS score 0-10")

    # Location
    endpoint: str = Field(..., description="Affected endpoint")
    method: Optional[str] = Field(default=None, description="HTTP method")
    parameter: Optional[str] = Field(default=None, description="Vulnerable parameter")

    # Evidence
    request: Optional[str] = Field(
        default=None, description="Request that triggered vulnerability"
    )
    response: Optional[str] = Field(
        default=None, description="Response showing vulnerability"
    )
    evidence: Optional[str] = Field(default=None, description="Proof of vulnerability")

    # Remediation
    remediation: str = Field(..., description="How to fix")
    references: List[str] = Field(default_factory=list, description="Reference URLs")

    # Metadata
    discovered_at: datetime = Field(default_factory=datetime.utcnow)
    confidence: float = Field(
        default=0.8, ge=0.0, le=1.0, description="Confidence level"
    )

    model_config = {"populate_by_name": True}


class SecretFinding(BaseModel):
    """Represents a detected secret or PII."""

    id: str = Field(..., description="Unique finding ID")
    type: SecretType = Field(..., description="Type of secret")
    severity: VulnerabilitySeverity = Field(..., description="Severity level")

    # Location
    file_path: Optional[str] = Field(default=None, description="File containing secret")
    line_number: Optional[int] = Field(default=None, description="Line number")
    endpoint: Optional[str] = Field(default=None, description="API endpoint")

    # Content
    matched_content: str = Field(..., description="Matched content")
    masked_content: str = Field(..., description="Masked version for display")

    # Detection
    pattern_name: str = Field(..., description="Name of detection pattern")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)

    discovered_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"populate_by_name": True}


class ComplianceViolation(BaseModel):
    """Represents a compliance violation."""

    id: str = Field(..., description="Unique violation ID")
    standard: ComplianceStandard = Field(..., description="Compliance standard")
    requirement: str = Field(..., description="Requirement code/section")
    title: str = Field(..., description="Violation title")
    description: str = Field(..., description="Detailed description")
    severity: VulnerabilitySeverity = Field(..., description="Severity level")

    # Location
    endpoint: Optional[str] = Field(default=None)
    evidence: Optional[str] = Field(default=None)

    # Remediation
    remediation: str = Field(..., description="How to achieve compliance")

    discovered_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"populate_by_name": True}


class SecurityScanResult(BaseModel):
    """Results from a security scan."""

    scan_id: str = Field(..., description="Unique scan ID")
    target: str = Field(..., description="Scan target URL/endpoint")
    scan_type: str = Field(..., description="Type of scan performed")
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)

    # Findings
    vulnerabilities: List[SecurityVulnerability] = Field(default_factory=list)
    secrets: List[SecretFinding] = Field(default_factory=list)
    compliance_violations: List[ComplianceViolation] = Field(default_factory=list)

    # Summary
    total_findings: int = Field(default=0)
    critical_count: int = Field(default=0)
    high_count: int = Field(default=0)
    medium_count: int = Field(default=0)
    low_count: int = Field(default=0)
    info_count: int = Field(default=0)

    # Status
    status: str = Field(default="running")  # running, completed, failed
    error_message: Optional[str] = Field(default=None)

    model_config = {"populate_by_name": True}


class SecurityReport(BaseModel):
    """Comprehensive security report."""

    report_id: str = Field(..., description="Unique report ID")
    project_name: str = Field(..., description="Project name")
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    # Summary
    total_scans: int = Field(default=0)
    total_vulnerabilities: int = Field(default=0)
    total_secrets: int = Field(default=0)
    total_compliance_violations: int = Field(default=0)

    # Risk score
    risk_score: float = Field(
        default=0.0, ge=0.0, le=100.0, description="Overall risk score"
    )
    risk_level: str = Field(default="low")  # critical, high, medium, low

    # Findings by category
    owasp_findings: Dict[VulnerabilityCategory, List[SecurityVulnerability]] = Field(
        default_factory=dict
    )
    secrets_by_type: Dict[SecretType, List[SecretFinding]] = Field(default_factory=dict)
    compliance_by_standard: Dict[ComplianceStandard, List[ComplianceViolation]] = Field(
        default_factory=dict
    )

    # Detailed results
    scan_results: List[SecurityScanResult] = Field(default_factory=list)

    # Recommendations
    top_recommendations: List[str] = Field(default_factory=list)

    model_config = {"populate_by_name": True}
