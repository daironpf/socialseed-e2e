"""
OWASP Top 10 vulnerability scanner.

Detects vulnerabilities according to OWASP Top 10 2021:
- A01:2021 – Broken Access Control
- A02:2021 – Cryptographic Failures
- A03:2021 – Injection
- A04:2021 – Insecure Design
- A05:2021 – Security Misconfiguration
- A06:2021 – Vulnerable and Outdated Components
- A07:2021 – Identification and Authentication Failures
- A08:2021 – Software and Data Integrity Failures
- A09:2021 – Security Logging and Monitoring Failures
- A10:2021 – Server-Side Request Forgery (SSRF)
"""

import re
import uuid
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

from ..models import (
    SecurityVulnerability,
    VulnerabilitySeverity,
    VulnerabilityCategory,
    SecurityScanResult,
)


class OWASPScanner:
    """Scanner for OWASP Top 10 vulnerabilities.

    Detects common web application security vulnerabilities according to
    the OWASP Top 10 2021 standard.

    Example:
        scanner = OWASPScanner()
        result = scanner.scan_endpoint("https://api.example.com/users", method="GET")

        for vuln in result.vulnerabilities:
            print(f"{vuln.severity}: {vuln.title}")
    """

    # SQL Injection patterns
    SQLI_PATTERNS = [
        r"(\%27)|(\')|(\-\-)|(\%23)|(#)",  # Basic SQL meta-characters
        r"((\%3D)|(=))[^\n]*((\%27)|(\')|(\-\-)|(\%3B)|(;))",  # '=' with meta-chars
        r"\w*((\%27)|(\'))((\%6F)|o|(\%4F))((\%72)|r|(\%52))",  # ' OR variants
        r"((\%27)|(\'))union",  # UNION operator
        r"exec(\s|\+)\(s\)pxp_cmdshell",  # Stored procedures
        r"UNION\s+SELECT",  # Union select
        r"INSERT\s+INTO",  # Insert statement
        r"DELETE\s+FROM",  # Delete statement
        r"DROP\s+TABLE",  # Drop table
    ]

    # XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>[\s\S]*?</script>",  # Script tags
        r"javascript:",  # JavaScript protocol
        r"on\w+\s*=",  # Event handlers (onclick, onload, etc.)
        r"<iframe",  # Iframe tags
        r"<object",  # Object tags
        r"<embed",  # Embed tags
        r"expression\s*\(",  # CSS expressions
        r"eval\s*\(",  # JavaScript eval
    ]

    # Path traversal patterns
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",  # Unix traversal
        r"\.\.\\",  # Windows traversal
        r"%2e%2e%2f",  # URL encoded traversal
        r"%252e%252e%252f",  # Double encoded
        r"..%2f",  # Mixed encoding
        r"%2e%2e/",  # Mixed encoding 2
        r"\.\.//",  # Double slash
    ]

    # Command injection patterns
    CMD_INJECTION_PATTERNS = [
        r"[;&|`]\s*\w+",  # Command separators
        r"\$\(\s*\w+",  # Command substitution
        r"`\s*\w+",  # Backtick execution
        r"\|\s*\w+",  # Pipe operator
        r";\s*\w+",  # Semicolon separator
    ]

    # Information disclosure patterns
    INFO_DISCLOSURE_PATTERNS = [
        r"(Password|pwd|passwd)\s*[=:]\s*\S+",
        r"(Secret|secret[_-]?key)\s*[=:]\s*\S+",
        r"(AWS|azure|gcp)[_-]?(access[_-]?key|secret)\s*[=:]\s*\S+",
        r"(database|db)[_-]?(url|password|pwd)\s*[=:]\s*\S+",
        r"Stack trace:",
        r"Exception in thread",
        r"Traceback \(most recent call last\)",
    ]

    # Insecure direct object reference patterns
    IDOR_PATTERNS = [
        r"/api/users/\d+",  # Sequential user IDs
        r"/api/orders/\d+",  # Sequential order IDs
        r"user_id=\d+",  # User ID parameter
        r"order_id=\d+",  # Order ID parameter
    ]

    # SSRF patterns
    SSRF_PATTERNS = [
        r"http://localhost",
        r"http://127\.0\.0\.1",
        r"http://0\.0\.0\.0",
        r"http://10\.\d+\.\d+\.\d+",
        r"http://172\.1[6-9]\.\d+\.\d+",
        r"http://172\.2[0-9]\.\d+\.\d+",
        r"http://172\.3[0-1]\.\d+\.\d+",
        r"http://192\.168\.\d+\.\d+",
        r"file://",
        r"ftp://",
        r"dict://",
        r"ldap://",
        r"gopher://",
    ]

    def __init__(self):
        """Initialize OWASP scanner."""
        self.vulnerabilities: List[SecurityVulnerability] = []

    def scan_endpoint(
        self,
        endpoint: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> SecurityScanResult:
        """Scan a single endpoint for OWASP vulnerabilities.

        Args:
            endpoint: Target endpoint URL
            method: HTTP method
            headers: Request headers
            params: Query parameters
            data: Request body data

        Returns:
            SecurityScanResult with vulnerabilities found
        """
        scan_id = str(uuid.uuid4())
        result = SecurityScanResult(
            scan_id=scan_id,
            target=endpoint,
            scan_type="owasp_top10",
        )

        try:
            # Check for injection vulnerabilities
            self._check_injection(endpoint, method, params, data)

            # Check for broken authentication
            self._check_broken_auth(endpoint, headers)

            # Check for sensitive data exposure
            self._check_sensitive_data(endpoint, headers)

            # Check for XXE
            self._check_xxe(endpoint, headers, data)

            # Check for broken access control
            self._check_access_control(endpoint)

            # Check for security misconfiguration
            self._check_security_misconfig(endpoint, headers)

            # Check for XSS
            self._check_xss(endpoint, params, data)

            # Check for insecure deserialization
            self._check_insecure_deserialization(endpoint, headers, data)

            # Check for vulnerable components
            self._check_vulnerable_components(headers)

            # Check for insufficient logging
            self._check_insufficient_logging(endpoint, headers)

            # Check for SSRF
            self._check_ssrf(endpoint, params, data)

            # Update result
            result.vulnerabilities = self.vulnerabilities
            result.total_findings = len(self.vulnerabilities)
            result.critical_count = sum(
                1
                for v in self.vulnerabilities
                if v.severity == VulnerabilitySeverity.CRITICAL
            )
            result.high_count = sum(
                1
                for v in self.vulnerabilities
                if v.severity == VulnerabilitySeverity.HIGH
            )
            result.medium_count = sum(
                1
                for v in self.vulnerabilities
                if v.severity == VulnerabilitySeverity.MEDIUM
            )
            result.low_count = sum(
                1
                for v in self.vulnerabilities
                if v.severity == VulnerabilitySeverity.LOW
            )
            result.status = "completed"

        except Exception as e:
            result.status = "failed"
            result.error_message = str(e)

        return result

    def scan_api(
        self,
        base_url: str,
        endpoints: Optional[List[Dict[str, Any]]] = None,
    ) -> List[SecurityScanResult]:
        """Scan multiple API endpoints.

        Args:
            base_url: Base API URL
            endpoints: List of endpoint configurations

        Returns:
            List of SecurityScanResult
        """
        results = []

        if endpoints is None:
            # Default common endpoints to scan
            endpoints = [
                {"path": "/", "method": "GET"},
                {"path": "/api", "method": "GET"},
                {"path": "/api/users", "method": "GET"},
                {"path": "/api/login", "method": "POST"},
                {"path": "/api/register", "method": "POST"},
            ]

        for endpoint_config in endpoints:
            path = endpoint_config.get("path", "/")
            method = endpoint_config.get("method", "GET")
            full_url = urljoin(base_url, path)

            result = self.scan_endpoint(
                endpoint=full_url,
                method=method,
                headers=endpoint_config.get("headers"),
                params=endpoint_config.get("params"),
                data=endpoint_config.get("data"),
            )
            results.append(result)

            # Reset vulnerabilities for next scan
            self.vulnerabilities = []

        return results

    def _check_injection(
        self,
        endpoint: str,
        method: str,
        params: Optional[Dict[str, Any]],
        data: Optional[Dict[str, Any]],
    ):
        """Check for injection vulnerabilities (SQLi, Command Injection, etc.)."""
        inputs_to_check = []

        if params:
            inputs_to_check.extend(str(v) for v in params.values())
        if data:
            inputs_to_check.extend(str(v) for v in data.values())

        for user_input in inputs_to_check:
            # Check SQL Injection
            for pattern in self.SQLI_PATTERNS:
                if re.search(pattern, user_input, re.IGNORECASE):
                    self._add_vulnerability(
                        title="SQL Injection",
                        description=f"Potential SQL injection detected in input: {user_input[:50]}...",
                        category=VulnerabilityCategory.INJECTION,
                        severity=VulnerabilitySeverity.CRITICAL,
                        endpoint=endpoint,
                        method=method,
                        evidence=f"Pattern matched: {pattern[:50]}",
                        remediation="Use parameterized queries/prepared statements. Validate and sanitize all user inputs.",
                        references=[
                            "https://owasp.org/www-project-top-ten/2017/A1_2017-Injection",
                            "https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html",
                        ],
                    )
                    break

            # Check Command Injection
            for pattern in self.CMD_INJECTION_PATTERNS:
                if re.search(pattern, user_input, re.IGNORECASE):
                    self._add_vulnerability(
                        title="Command Injection",
                        description=f"Potential command injection detected in input",
                        category=VulnerabilityCategory.INJECTION,
                        severity=VulnerabilitySeverity.CRITICAL,
                        endpoint=endpoint,
                        method=method,
                        evidence=f"Pattern matched: {pattern}",
                        remediation="Avoid passing user input to system commands. Use parameterized APIs if necessary.",
                        references=[
                            "https://owasp.org/www-community/attacks/Command_Injection",
                        ],
                    )
                    break

    def _check_broken_auth(self, endpoint: str, headers: Optional[Dict[str, str]]):
        """Check for broken authentication vulnerabilities."""
        if headers:
            auth_header = headers.get("Authorization", "")

            # Check for weak authentication schemes
            if auth_header.startswith("Basic "):
                self._add_vulnerability(
                    title="Basic Authentication Detected",
                    description="API is using Basic Authentication which transmits credentials in base64 encoding",
                    category=VulnerabilityCategory.BROKEN_AUTH,
                    severity=VulnerabilitySeverity.HIGH,
                    endpoint=endpoint,
                    evidence="Authorization: Basic ...",
                    remediation="Use OAuth 2.0, JWT, or other modern authentication mechanisms. Ensure HTTPS is enforced.",
                    references=[
                        "https://owasp.org/www-project-top-ten/2017/A2_2017-Broken_Authentication",
                    ],
                )

            # Check for missing security headers related to auth
            if "X-Frame-Options" not in str(headers):
                self._add_vulnerability(
                    title="Missing X-Frame-Options Header",
                    description="X-Frame-Options header is missing, potentially allowing clickjacking attacks",
                    category=VulnerabilityCategory.BROKEN_AUTH,
                    severity=VulnerabilitySeverity.MEDIUM,
                    endpoint=endpoint,
                    remediation="Add X-Frame-Options: DENY or SAMEORIGIN header to prevent clickjacking",
                    references=[
                        "https://owasp.org/www-community/attacks/Clickjacking",
                    ],
                )

    def _check_sensitive_data(self, endpoint: str, headers: Optional[Dict[str, str]]):
        """Check for sensitive data exposure."""
        if headers:
            # Check for missing HTTPS
            if not endpoint.startswith("https://"):
                self._add_vulnerability(
                    title="Insecure Protocol - HTTP",
                    description="Endpoint is using HTTP instead of HTTPS, exposing data in transit",
                    category=VulnerabilityCategory.SENSITIVE_DATA,
                    severity=VulnerabilitySeverity.CRITICAL,
                    endpoint=endpoint,
                    evidence=f"Protocol: {endpoint.split('://')[0]}",
                    remediation="Enforce HTTPS for all endpoints. Redirect HTTP to HTTPS.",
                    references=[
                        "https://owasp.org/www-project-top-ten/2017/A3_2017-Sensitive_Data_Exposure",
                    ],
                )

            # Check for sensitive headers
            sensitive_headers = ["X-Powered-By", "Server", "X-AspNet-Version"]
            for header in sensitive_headers:
                if header in str(headers):
                    self._add_vulnerability(
                        title=f"Information Disclosure - {header}",
                        description=f"{header} header reveals technology stack information",
                        category=VulnerabilityCategory.SENSITIVE_DATA,
                        severity=VulnerabilitySeverity.LOW,
                        endpoint=endpoint,
                        evidence=f"{header} header present",
                        remediation=f"Remove {header} header from responses",
                        references=[
                            "https://owasp.org/www-project-top-ten/2017/A3_2017-Sensitive_Data_Exposure",
                        ],
                    )

    def _check_xxe(
        self,
        endpoint: str,
        headers: Optional[Dict[str, str]],
        data: Optional[Dict[str, Any]],
    ):
        """Check for XML External Entity vulnerabilities."""
        if data and any(
            "xml" in str(k).lower() or "<!DOCTYPE" in str(v) for k, v in data.items()
        ):
            content_type = headers.get("Content-Type", "") if headers else ""
            if "xml" in content_type.lower() or any(
                "<!DOCTYPE" in str(v) for v in data.values()
            ):
                self._add_vulnerability(
                    title="Potential XML External Entity (XXE)",
                    description="Endpoint accepts XML input without proper XXE protection",
                    category=VulnerabilityCategory.XXE,
                    severity=VulnerabilitySeverity.HIGH,
                    endpoint=endpoint,
                    evidence="XML content detected in request",
                    remediation="Disable DTDs and external entities. Use JSON instead of XML when possible.",
                    references=[
                        "https://owasp.org/www-project-top-ten/2017/A4_2017-XML_External_Entities_(XXE)",
                        "https://cheatsheetseries.owasp.org/cheatsheets/XML_External_Entity_Prevention_Cheat_Sheet.html",
                    ],
                )

    def _check_access_control(self, endpoint: str):
        """Check for broken access control vulnerabilities."""
        # Check for IDOR patterns
        for pattern in self.IDOR_PATTERNS:
            if re.search(pattern, endpoint):
                self._add_vulnerability(
                    title="Insecure Direct Object Reference (IDOR)",
                    description="Sequential ID pattern detected in endpoint, potential IDOR vulnerability",
                    category=VulnerabilityCategory.BROKEN_ACCESS,
                    severity=VulnerabilitySeverity.HIGH,
                    endpoint=endpoint,
                    evidence=f"Pattern matched: {pattern}",
                    remediation="Implement proper access controls. Use UUIDs instead of sequential IDs. Verify user permissions.",
                    references=[
                        "https://owasp.org/www-project-top-ten/2017/A5_2017-Broken_Access_Control",
                        "https://cheatsheetseries.owasp.org/cheatsheets/Insecure_Direct_Object_Reference_Prevention_Cheat_Sheet.html",
                    ],
                )
                break

        # Check for path traversal
        for pattern in self.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, endpoint):
                self._add_vulnerability(
                    title="Path Traversal",
                    description="Path traversal pattern detected in endpoint",
                    category=VulnerabilityCategory.BROKEN_ACCESS,
                    severity=VulnerabilitySeverity.HIGH,
                    endpoint=endpoint,
                    evidence=f"Pattern matched: {pattern}",
                    remediation="Validate and sanitize file paths. Use allowlists for acceptable paths.",
                    references=[
                        "https://owasp.org/www-community/attacks/Path_Traversal",
                    ],
                )
                break

    def _check_security_misconfig(
        self, endpoint: str, headers: Optional[Dict[str, str]]
    ):
        """Check for security misconfiguration."""
        if headers:
            # Check for security headers
            security_headers = {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": ["DENY", "SAMEORIGIN"],
                "Content-Security-Policy": None,
                "Strict-Transport-Security": None,
                "X-XSS-Protection": "1; mode=block",
            }

            for header, expected_value in security_headers.items():
                if header not in headers:
                    self._add_vulnerability(
                        title=f"Missing Security Header - {header}",
                        description=f"{header} security header is not set",
                        category=VulnerabilityCategory.SECURITY_MISCONFIG,
                        severity=VulnerabilitySeverity.MEDIUM,
                        endpoint=endpoint,
                        remediation=f"Add {header} header to all responses",
                        references=[
                            "https://owasp.org/www-project-top-ten/2017/A6_2017-Security_Misconfiguration",
                            "https://owasp.org/www-project-secure-headers/",
                        ],
                    )

    def _check_xss(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]],
        data: Optional[Dict[str, Any]],
    ):
        """Check for Cross-Site Scripting vulnerabilities."""
        inputs_to_check = []

        if params:
            inputs_to_check.extend(str(v) for v in params.values())
        if data:
            inputs_to_check.extend(str(v) for v in data.values())

        for user_input in inputs_to_check:
            for pattern in self.XSS_PATTERNS:
                if re.search(pattern, user_input, re.IGNORECASE):
                    self._add_vulnerability(
                        title="Cross-Site Scripting (XSS)",
                        description=f"Potential XSS vulnerability detected in user input",
                        category=VulnerabilityCategory.XSS,
                        severity=VulnerabilitySeverity.HIGH,
                        endpoint=endpoint,
                        evidence=f"Pattern matched: {pattern[:50]}",
                        remediation="Encode all user input before rendering. Implement Content Security Policy.",
                        references=[
                            "https://owasp.org/www-project-top-ten/2017/A7_2017-Cross-Site_Scripting_(XSS)",
                            "https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html",
                        ],
                    )
                    break

    def _check_insecure_deserialization(
        self,
        endpoint: str,
        headers: Optional[Dict[str, str]],
        data: Optional[Dict[str, Any]],
    ):
        """Check for insecure deserialization."""
        if headers:
            content_type = headers.get("Content-Type", "")

            # Check for serialized data formats
            if "application/x-java-serialized-object" in content_type:
                self._add_vulnerability(
                    title="Insecure Deserialization - Java",
                    description="Java serialized objects detected, potential deserialization vulnerability",
                    category=VulnerabilityCategory.INSECURE_DESERIALIZATION,
                    severity=VulnerabilitySeverity.CRITICAL,
                    endpoint=endpoint,
                    evidence="Content-Type: application/x-java-serialized-object",
                    remediation="Avoid deserializing untrusted data. Use JSON or XML with schema validation.",
                    references=[
                        "https://owasp.org/www-project-top-ten/2017/A8_2017-Insecure_Deserialization",
                        "https://cheatsheetseries.owasp.org/cheatsheets/Deserialization_Cheat_Sheet.html",
                    ],
                )

            if data and any(
                "pickle" in str(v).lower() or "yaml.load" in str(v).lower()
                for v in data.values()
            ):
                self._add_vulnerability(
                    title="Insecure Deserialization - Python",
                    description="Python pickle/YAML detected, potential deserialization vulnerability",
                    category=VulnerabilityCategory.INSECURE_DESERIALIZATION,
                    severity=VulnerabilitySeverity.CRITICAL,
                    endpoint=endpoint,
                    evidence="Pickle/YAML content detected",
                    remediation="Use json.loads() instead of pickle.loads(). Use yaml.safe_load() instead of yaml.load()",
                    references=[
                        "https://owasp.org/www-project-top-ten/2017/A8_2017-Insecure_Deserialization",
                    ],
                )

    def _check_vulnerable_components(self, headers: Optional[Dict[str, str]]):
        """Check for vulnerable and outdated components."""
        if headers:
            # Check for outdated server software
            server = headers.get("Server", "")
            powered_by = headers.get("X-Powered-By", "")

            # This is a basic check - in production, you'd compare against CVE database
            outdated_patterns = [
                (r"Apache/2\.2", "Apache 2.2.x is outdated"),
                (r"nginx/1\.[0-9]", "Old nginx version detected"),
                (r"PHP/5\.", "PHP 5.x is outdated and unsupported"),
                (r"Python/2\.", "Python 2.x is outdated and unsupported"),
            ]

            for header_value in [server, powered_by]:
                for pattern, message in outdated_patterns:
                    if re.search(pattern, header_value, re.IGNORECASE):
                        self._add_vulnerability(
                            title="Vulnerable Component Detected",
                            description=message,
                            category=VulnerabilityCategory.VULNERABLE_COMPONENTS,
                            severity=VulnerabilitySeverity.MEDIUM,
                            evidence=f"Header: {header_value}",
                            remediation="Update to the latest stable version. Regularly patch dependencies.",
                            references=[
                                "https://owasp.org/www-project-top-ten/2017/A9_2017-Using_Components_with_Known_Vulnerabilities",
                            ],
                        )

    def _check_insufficient_logging(
        self, endpoint: str, headers: Optional[Dict[str, str]]
    ):
        """Check for insufficient logging and monitoring."""
        # Check for sensitive endpoints that should have enhanced logging
        sensitive_endpoints = ["/login", "/admin", "/api/auth", "/password", "/reset"]

        for sensitive in sensitive_endpoints:
            if sensitive in endpoint.lower():
                # In a real implementation, you'd check actual logging configuration
                self._add_vulnerability(
                    title="Sensitive Endpoint - Verify Logging",
                    description=f"Endpoint {endpoint} handles sensitive operations and should have comprehensive logging",
                    category=VulnerabilityCategory.INSUFFICIENT_LOGGING,
                    severity=VulnerabilitySeverity.MEDIUM,
                    endpoint=endpoint,
                    evidence=f"Sensitive pattern: {sensitive}",
                    remediation="Implement comprehensive logging for authentication, authorization, and sensitive operations. Monitor for suspicious activity.",
                    references=[
                        "https://owasp.org/www-project-top-ten/2017/A10_2017-Insufficient_Logging%26Monitoring",
                    ],
                )
                break

    def _check_ssrf(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]],
        data: Optional[Dict[str, Any]],
    ):
        """Check for Server-Side Request Forgery."""
        # Look for URL parameters that might be vulnerable to SSRF
        url_params = ["url", "uri", "endpoint", "path", "redirect", "callback"]

        inputs_to_check = {}
        if params:
            inputs_to_check.update(params)
        if data:
            inputs_to_check.update(data)

        for key, value in inputs_to_check.items():
            if any(param in str(key).lower() for param in url_params):
                value_str = str(value)

                # Check for internal URLs
                for pattern in self.SSRF_PATTERNS:
                    if re.search(pattern, value_str, re.IGNORECASE):
                        self._add_vulnerability(
                            title="Server-Side Request Forgery (SSRF)",
                            description=f"Potential SSRF vulnerability in parameter '{key}'",
                            category=VulnerabilityCategory.SSRF,
                            severity=VulnerabilitySeverity.HIGH,
                            endpoint=endpoint,
                            evidence=f"Internal URL pattern detected: {value_str[:100]}",
                            remediation="Validate and sanitize all URL inputs. Use allowlists for acceptable destinations. Disable unnecessary URL schemas.",
                            references=[
                                "https://owasp.org/www-community/attacks/Server_Side_Request_Forgery",
                                "https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html",
                            ],
                        )
                        break

    def _add_vulnerability(
        self,
        title: str,
        description: str,
        category: VulnerabilityCategory,
        severity: VulnerabilitySeverity,
        endpoint: str,
        remediation: str,
        evidence: Optional[str] = None,
        method: Optional[str] = None,
        parameter: Optional[str] = None,
        request: Optional[str] = None,
        response: Optional[str] = None,
        references: Optional[List[str]] = None,
        cvss_score: Optional[float] = None,
    ):
        """Add a vulnerability to the list."""
        vulnerability = SecurityVulnerability(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            category=category,
            severity=severity,
            cvss_score=cvss_score or self._severity_to_cvss(severity),
            endpoint=endpoint,
            method=method,
            parameter=parameter,
            evidence=evidence,
            request=request,
            response=response,
            remediation=remediation,
            references=references or [],
        )

        self.vulnerabilities.append(vulnerability)

    def _severity_to_cvss(self, severity: VulnerabilitySeverity) -> float:
        """Convert severity to CVSS score."""
        mapping = {
            VulnerabilitySeverity.CRITICAL: 9.5,
            VulnerabilitySeverity.HIGH: 7.5,
            VulnerabilitySeverity.MEDIUM: 5.5,
            VulnerabilitySeverity.LOW: 3.5,
            VulnerabilitySeverity.INFO: 0.0,
        }
        return mapping.get(severity, 5.0)
