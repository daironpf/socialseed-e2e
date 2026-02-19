"""
Secret and PII detection module.

Detects exposed secrets, credentials, API keys, and personally identifiable information.
"""

import hashlib
import re
import uuid
from typing import Any, Dict, List, Optional

from ..models import (
    SecretFinding,
    SecretType,
    VulnerabilitySeverity,
)


class SecretDetector:
    """Detects exposed secrets and PII in code and API responses.

    Scans for:
    - API keys and tokens
    - Database credentials
    - Private keys
    - Passwords
    - PII (emails, phone numbers, SSN, credit cards)

    Example:
        detector = SecretDetector()

        # Scan text content
        findings = detector.scan_text("api_key=sk_live_123456789")

        # Scan file
        findings = detector.scan_file("/path/to/config.py")
    """

    # Detection patterns for different secret types
    PATTERNS = {
        SecretType.API_KEY: [
            (r"(?i)(api[_-]?key|apikey)\s*[=:]\s*['\"]?([a-zA-Z0-9_\-]{20,})['\"]?", 2),
            (r"(?i)(api[_-]?key|apikey)\s+['\"]?([a-zA-Z0-9_\-]{16,})['\"]?", 2),
            (r"(?i)x-api-key:\s*([a-zA-Z0-9_\-]{16,})", 1),
            (r"(?i)sk-[a-zA-Z0-9]{48}", 0),  # OpenAI
        ],
        SecretType.AWS_KEY: [
            (r"(?i)AKIA[0-9A-Z]{16}", 0),  # AWS Access Key ID
            (
                r"(?i)aws[_-]?(access[_-]?key|secret)[\s]*[=:]\s*['\"]?([A-Za-z0-9/+=]{40})['\"]?",
                2,
            ),
        ],
        SecretType.DATABASE_URL: [
            (r"(postgres|mysql|mongodb)://[^\s\"']+", 0),
            (r"(?i)database[_-]?url\s*[=:]\s*['\"]?([^\s\"']+)['\"]?", 1),
            (
                r"(?i)(db[_-]?host|db[_-]?password|db[_-]?user)\s*[=:]\s*['\"]?([^\s\"']+)['\"]?",
                2,
            ),
        ],
        SecretType.PRIVATE_KEY: [
            (r"-----BEGIN (RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----", 0),
            (
                r"-----BEGIN (RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----[\s\S]+?-----END",
                0,
            ),
        ],
        SecretType.PASSWORD: [
            (r"(?i)(password|passwd|pwd)\s*[=:]\s*['\"]?([^\s\"']{8,})['\"]?", 2),
            (r"(?i)(pass|password)\s+['\"]?([^\s\"']{8,})['\"]?", 2),
        ],
        SecretType.TOKEN: [
            (
                r"(?i)(auth[_-]?token|access[_-]?token)\s*[=:]\s*['\"]?([a-zA-Z0-9_\-]{20,})['\"]?",
                2,
            ),
            (r"(?i)bearer\s+([a-zA-Z0-9_\-\.]{20,})", 1),
        ],
        SecretType.JWT: [
            (r"eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*", 0),
        ],
        SecretType.OAUTH: [
            (
                r"(?i)oauth[_-]?(token|secret)\s*[=:]\s*['\"]?([a-zA-Z0-9_\-]{20,})['\"]?",
                2,
            ),
        ],
        SecretType.CREDIT_CARD: [
            (r"\b4\d{3}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b", 0),  # Visa
            (r"\b5[1-5]\d{2}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b", 0),  # MasterCard
            (r"\b3[47]\d{2}[\s-]?\d{6}[\s-]?\d{5}\b", 0),  # Amex
            (r"\b6(?:011|5\d{2})[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b", 0),  # Discover
        ],
        SecretType.SSN: [
            (r"\b\d{3}-\d{2}-\d{4}\b", 0),
            (r"\b\d{3}\.\d{2}\.\d{4}\b", 0),
            (r"\b\d{3}\s\d{2}\s\d{4}\b", 0),
        ],
        SecretType.EMAIL: [
            (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", 0),
        ],
        SecretType.PHONE: [
            (r"\b\d{3}-\d{3}-\d{4}\b", 0),  # US format
            (r"\(\d{3}\)\s?\d{3}-\d{4}", 0),  # US format with parens
            (r"\+\d[\d\s-]{8,}\d", 0),  # International
        ],
    }

    def __init__(self):
        """Initialize secret detector."""
        self.findings: List[SecretFinding] = []

    def scan_text(
        self,
        text: str,
        source: Optional[str] = None,
        include_pii: bool = True,
    ) -> List[SecretFinding]:
        """Scan text content for secrets and PII.

        Args:
            text: Text content to scan
            source: Source identifier (e.g., filename)
            include_pii: Whether to include PII detection

        Returns:
            List of secret findings
        """
        self.findings = []

        # Determine which patterns to use
        patterns_to_check = dict(self.PATTERNS)
        if not include_pii:
            pii_types = [
                SecretType.EMAIL,
                SecretType.PHONE,
                SecretType.SSN,
                SecretType.CREDIT_CARD,
            ]
            for pii_type in pii_types:
                patterns_to_check.pop(pii_type, None)

        # Scan for each pattern
        for secret_type, patterns in patterns_to_check.items():
            for pattern, group in patterns:
                for match in re.finditer(pattern, text):
                    matched_content = (
                        match.group(group) if group > 0 else match.group(0)
                    )

                    # Create masked version
                    masked_content = self._mask_content(matched_content)

                    # Determine severity
                    severity = self._get_severity(secret_type)

                    finding = SecretFinding(
                        id=str(uuid.uuid4()),
                        type=secret_type,
                        severity=severity,
                        matched_content=matched_content,
                        masked_content=masked_content,
                        pattern_name=f"{secret_type.value}_pattern",
                        file_path=source,
                    )

                    self.findings.append(finding)

        return self.findings

    def scan_file(self, filepath: str, include_pii: bool = True) -> List[SecretFinding]:
        """Scan a file for secrets and PII.

        Args:
            filepath: Path to file to scan
            include_pii: Whether to include PII detection

        Returns:
            List of secret findings
        """
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            findings = self.scan_text(content, source=filepath, include_pii=include_pii)

            # Add line numbers
            lines = content.split("\n")
            for finding in findings:
                for i, line in enumerate(lines, 1):
                    if finding.matched_content in line:
                        finding.line_number = i
                        break

            return findings
        except Exception as e:
            return []

    def scan_api_response(
        self,
        response: str,
        endpoint: str,
        include_pii: bool = True,
    ) -> List[SecretFinding]:
        """Scan API response for exposed secrets.

        Args:
            response: API response body
            endpoint: API endpoint URL
            include_pii: Whether to include PII detection

        Returns:
            List of secret findings
        """
        findings = self.scan_text(response, source=endpoint, include_pii=include_pii)

        # Update findings with endpoint
        for finding in findings:
            finding.endpoint = endpoint

        return findings

    def scan_directory(
        self,
        directory: str,
        file_extensions: Optional[List[str]] = None,
        include_pii: bool = True,
    ) -> List[SecretFinding]:
        """Scan all files in a directory.

        Args:
            directory: Directory path to scan
            file_extensions: List of file extensions to scan (e.g., ['.py', '.js'])
            include_pii: Whether to include PII detection

        Returns:
            List of secret findings
        """
        import os

        all_findings = []

        if file_extensions is None:
            file_extensions = [
                ".py",
                ".js",
                ".ts",
                ".java",
                ".go",
                ".rb",
                ".php",
                ".yml",
                ".yaml",
                ".json",
                ".xml",
                ".env",
                ".config",
            ]

        for root, dirs, files in os.walk(directory):
            # Skip hidden directories and common non-source directories
            dirs[:] = [
                d
                for d in dirs
                if not d.startswith(".")
                and d not in ["node_modules", "__pycache__", "venv", ".git"]
            ]

            for file in files:
                if any(file.endswith(ext) for ext in file_extensions):
                    filepath = os.path.join(root, file)
                    findings = self.scan_file(filepath, include_pii=include_pii)
                    all_findings.extend(findings)

        return all_findings

    def generate_report(self) -> Dict[str, Any]:
        """Generate summary report of findings.

        Returns:
            Dictionary with findings summary
        """
        by_type = {}
        by_severity = {
            VulnerabilitySeverity.CRITICAL.value: 0,
            VulnerabilitySeverity.HIGH.value: 0,
            VulnerabilitySeverity.MEDIUM.value: 0,
            VulnerabilitySeverity.LOW.value: 0,
        }

        for finding in self.findings:
            # Count by type
            type_key = finding.type.value
            by_type[type_key] = by_type.get(type_key, 0) + 1

            # Count by severity
            severity_key = finding.severity.value
            by_severity[severity_key] = by_severity.get(severity_key, 0) + 1

        return {
            "total_findings": len(self.findings),
            "by_type": by_type,
            "by_severity": by_severity,
        }

    def _mask_content(self, content: str, visible_chars: int = 4) -> str:
        """Mask sensitive content for display.

        Args:
            content: Content to mask
            visible_chars: Number of characters to keep visible at start/end

        Returns:
            Masked content
        """
        if len(content) <= visible_chars * 2:
            return "*" * len(content)

        return (
            content[:visible_chars]
            + "*" * (len(content) - visible_chars * 2)
            + content[-visible_chars:]
        )

    def _get_severity(self, secret_type: SecretType) -> VulnerabilitySeverity:
        """Get severity level for secret type.

        Args:
            secret_type: Type of secret

        Returns:
            Severity level
        """
        severity_map = {
            SecretType.AWS_KEY: VulnerabilitySeverity.CRITICAL,
            SecretType.PRIVATE_KEY: VulnerabilitySeverity.CRITICAL,
            SecretType.DATABASE_URL: VulnerabilitySeverity.CRITICAL,
            SecretType.API_KEY: VulnerabilitySeverity.HIGH,
            SecretType.PASSWORD: VulnerabilitySeverity.HIGH,
            SecretType.JWT: VulnerabilitySeverity.HIGH,
            SecretType.OAUTH: VulnerabilitySeverity.HIGH,
            SecretType.TOKEN: VulnerabilitySeverity.HIGH,
            SecretType.CREDIT_CARD: VulnerabilitySeverity.CRITICAL,
            SecretType.SSN: VulnerabilitySeverity.CRITICAL,
            SecretType.EMAIL: VulnerabilitySeverity.LOW,
            SecretType.PHONE: VulnerabilitySeverity.LOW,
        }

        return severity_map.get(secret_type, VulnerabilitySeverity.MEDIUM)
