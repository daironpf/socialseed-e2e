"""Security Test Executor and Resilience Monitor.

This module executes security tests and monitors backend resilience,
detecting crashes (500 errors) vs proper validation (400/422).

Issue #189: Implement AI-Driven Intelligent Fuzzing and Security Testing
"""

import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable

from playwright.sync_api import APIResponse

from socialseed_e2e.project_manifest.models import EndpointInfo, ServiceInfo
from socialseed_e2e.project_manifest.security_fuzzer import (
    AttackType,
    MaliciousPayloadGenerator,
    SecurityPayload,
    SecurityTestResult,
    FuzzingSession,
    SeverityLevel,
)


class ResilienceMonitor:
    """Monitors backend resilience during security testing."""

    # Status codes that indicate proper validation
    VALIDATION_SUCCESS_CODES = [400, 401, 403, 404, 422, 429]

    # Status codes that indicate server crash/vulnerability
    SERVER_ERROR_CODES = [500, 501, 502, 503, 504]

    # Status codes that might indicate unexpected behavior
    SUSPICIOUS_CODES = [200, 201, 202, 204]  # Success on attack = potential bypass

    def __init__(self):
        self.crash_count = 0
        self.blocked_count = 0
        self.bypass_count = 0
        self.response_times: List[float] = []

    def analyze_response(
        self, response: APIResponse, payload: SecurityPayload, execution_time_ms: float
    ) -> SecurityTestResult:
        """Analyze API response to determine if vulnerability exists.

        Args:
            response: API response from playwright
            payload: The security payload that was sent
            execution_time_ms: Time taken for request

        Returns:
            SecurityTestResult with analysis
        """
        status = response.status

        # Track response time
        self.response_times.append(execution_time_ms)

        # Determine if test passed (properly blocked) or failed (vulnerability)
        test_passed = True
        vulnerability_found = False
        severity = SeverityLevel.INFO

        if status in self.SERVER_ERROR_CODES:
            # Server crash - vulnerability!
            test_passed = False
            vulnerability_found = True
            severity = self._determine_severity(payload, "crash")
            self.crash_count += 1

        elif status in self.SUSPICIOUS_CODES:
            # Success status on attack - potential bypass!
            test_passed = False
            vulnerability_found = True
            severity = self._determine_severity(payload, "bypass")
            self.bypass_count += 1

        elif status in self.VALIDATION_SUCCESS_CODES:
            # Properly blocked
            test_passed = True
            self.blocked_count += 1

        else:
            # Unexpected status
            test_passed = False
            severity = SeverityLevel.LOW

        return SecurityTestResult(
            endpoint="",  # Will be set by executor
            field_name=payload.field_target or "unknown",
            payload=payload,
            response_status=status,
            response_body=response.text()[:500],  # Limit body size
            test_passed=test_passed,
            execution_time_ms=execution_time_ms,
            timestamp=datetime.now(),
            vulnerability_found=vulnerability_found,
            severity=severity,
            details={
                "response_headers": dict(response.headers),
                "attack_type": payload.attack_type.value,
            },
        )

    def _determine_severity(
        self, payload: SecurityPayload, issue_type: str
    ) -> SeverityLevel:
        """Determine severity level based on payload and issue type.

        Args:
            payload: The payload that caused the issue
            issue_type: Type of issue ("crash" or "bypass")

        Returns:
            Severity level
        """
        if issue_type == "crash":
            # Server crashes are critical
            if payload.attack_type in [
                AttackType.SQL_INJECTION,
                AttackType.NOSQL_INJECTION,
            ]:
                return SeverityLevel.CRITICAL
            elif payload.attack_type == AttackType.BUFFER_OVERFLOW:
                return SeverityLevel.HIGH
            else:
                return SeverityLevel.MEDIUM
        elif issue_type == "bypass":
            # Successful bypasses are high severity
            if payload.attack_type in [
                AttackType.SQL_INJECTION,
                AttackType.NOSQL_INJECTION,
            ]:
                return SeverityLevel.CRITICAL
            elif payload.attack_type == AttackType.COMMAND_INJECTION:
                return SeverityLevel.CRITICAL
            else:
                return SeverityLevel.HIGH

        return SeverityLevel.LOW

    def get_resilience_score(self) -> float:
        """Calculate resilience score (0.0 to 100.0).

        Returns:
            Resilience score percentage
        """
        total = self.blocked_count + self.crash_count + self.bypass_count
        if total == 0:
            return 100.0

        # Weight: blocked = 100%, crash = 0%, bypass = 0%
        score = (self.blocked_count / total) * 100.0
        return round(score, 2)

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of monitoring results.

        Returns:
            Dictionary with summary statistics
        """
        total = self.blocked_count + self.crash_count + self.bypass_count

        avg_response_time = 0.0
        if self.response_times:
            avg_response_time = sum(self.response_times) / len(self.response_times)

        return {
            "total_tests": total,
            "blocked": self.blocked_count,
            "crashes": self.crash_count,
            "bypasses": self.bypass_count,
            "resilience_score": self.get_resilience_score(),
            "avg_response_time_ms": round(avg_response_time, 2),
        }


class SecurityTestExecutor:
    """Executes security tests against API endpoints."""

    def __init__(self, base_url: str, service_page: Any):
        """Initialize the security test executor.

        Args:
            base_url: Base URL of the API
            service_page: Service page instance for making requests
        """
        self.base_url = base_url
        self.service_page = service_page
        self.payload_generator = MaliciousPayloadGenerator()
        self.monitor = ResilienceMonitor()
        self.session: Optional[FuzzingSession] = None

    def start_session(self, target_endpoints: List[str]) -> FuzzingSession:
        """Start a new fuzzing session.

        Args:
            target_endpoints: List of endpoints to target

        Returns:
            New fuzzing session
        """
        self.session = FuzzingSession(
            session_id=str(uuid.uuid4()),
            start_time=datetime.now(),
            target_endpoints=target_endpoints,
        )
        return self.session

    def execute_security_tests(
        self, endpoint: EndpointInfo, dto: Any, max_payloads_per_field: int = 10
    ) -> List[SecurityTestResult]:
        """Execute security tests for an endpoint.

        Args:
            endpoint: Endpoint to test
            dto: DTO schema for the endpoint
            max_payloads_per_field: Maximum payloads to test per field

        Returns:
            List of test results
        """
        results = []

        if not dto or not hasattr(dto, "fields"):
            return results

        # Generate payloads for each field
        for field in dto.fields:
            payloads = self.payload_generator.generate_all_payloads_for_field(field)

            # Limit payloads
            if len(payloads) > max_payloads_per_field:
                # Prioritize critical/high severity payloads
                critical = [p for p in payloads if p.severity == SeverityLevel.CRITICAL]
                high = [p for p in payloads if p.severity == SeverityLevel.HIGH]
                medium = [p for p in payloads if p.severity == SeverityLevel.MEDIUM]

                payloads = (
                    critical
                    + high
                    + medium[: max_payloads_per_field - len(critical) - len(high)]
                )

            # Execute each payload
            for payload in payloads:
                result = self._execute_single_payload(endpoint, field.name, payload)
                results.append(result)

                # Update session stats
                if self.session:
                    self.session.total_tests += 1
                    if result.test_passed:
                        self.session.passed_tests += 1
                    else:
                        self.session.failed_tests += 1
                        if result.vulnerability_found:
                            self.session.vulnerabilities_found.append(result)

        return results

    def _execute_single_payload(
        self, endpoint: EndpointInfo, field_name: str, payload: SecurityPayload
    ) -> SecurityTestResult:
        """Execute a single security payload.

        Args:
            endpoint: Target endpoint
            field_name: Field being tested
            payload: Security payload to send

        Returns:
            SecurityTestResult
        """
        start_time = time.time()

        try:
            # Prepare request data
            request_data = self._prepare_request_data(endpoint, field_name, payload)

            # Make request based on method
            method = endpoint.method.value.upper()
            url = f"{self.base_url}{endpoint.path}"

            if method == "GET":
                response = self.service_page.get(url, params=request_data)
            elif method == "POST":
                response = self.service_page.post(url, data=request_data)
            elif method == "PUT":
                response = self.service_page.put(url, data=request_data)
            elif method == "PATCH":
                response = self.service_page.patch(url, data=request_data)
            elif method == "DELETE":
                response = self.service_page.delete(url, data=request_data)
            else:
                response = self.service_page.request(method, url, data=request_data)

            execution_time = (time.time() - start_time) * 1000

            # Analyze response
            result = self.monitor.analyze_response(response, payload, execution_time)
            result.endpoint = endpoint.name

            return result

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000

            # Request failed - might indicate crash or timeout
            return SecurityTestResult(
                endpoint=endpoint.name,
                field_name=field_name,
                payload=payload,
                response_status=0,
                response_body=str(e)[:500],
                test_passed=False,
                execution_time_ms=execution_time,
                timestamp=datetime.now(),
                vulnerability_found=True,
                severity=SeverityLevel.HIGH,
                details={"error": str(e), "error_type": type(e).__name__},
            )

    def _prepare_request_data(
        self, endpoint: EndpointInfo, field_name: str, payload: SecurityPayload
    ) -> Dict[str, Any]:
        """Prepare request data with payload.

        Args:
            endpoint: Endpoint info
            field_name: Target field
            payload: Payload to inject

        Returns:
            Request data dictionary
        """
        # Start with base valid data
        request_data = {}

        # Inject payload into target field
        request_data[field_name] = payload.value

        return request_data

    def end_session(self) -> FuzzingSession:
        """End the current fuzzing session.

        Returns:
            Completed session with results
        """
        if self.session:
            self.session.end_time = datetime.now()
            self.session.resilience_score = self.monitor.get_resilience_score()

        return self.session


class SecurityReportGenerator:
    """Generates security test reports."""

    def __init__(self, session: FuzzingSession):
        """Initialize report generator.

        Args:
            session: Fuzzing session with results
        """
        self.session = session

    def generate_report(self) -> str:
        """Generate markdown security report.

        Returns:
            Markdown formatted report
        """
        lines = [
            "# 🔒 Security Fuzzing Report",
            "",
            f"**Session ID:** `{self.session.session_id}`",
            f"**Start Time:** {self.session.start_time.strftime('%Y-%m-%d %H:%M:%S')}",
        ]

        if self.session.end_time:
            lines.append(
                f"**End Time:** {self.session.end_time.strftime('%Y-%m-%d %H:%M:%S')}"
            )

        lines.extend(
            [
                "",
                "---",
                "",
                "## 📊 Executive Summary",
                "",
            ]
        )

        # Summary statistics
        lines.extend(
            [
                f"**Total Tests Executed:** {self.session.total_tests}",
                f"**Tests Passed (Blocked):** {self.session.passed_tests}",
                f"**Tests Failed:** {self.session.failed_tests}",
                f"**Vulnerabilities Found:** {len(self.session.vulnerabilities_found)}",
                f"**Resilience Score:** {self.session.resilience_score}%",
                "",
            ]
        )

        # Resilience score interpretation
        score = self.session.resilience_score
        if score >= 90:
            lines.append(
                "🟢 **Resilience Level:** Excellent - API properly validates and blocks attacks"
            )
        elif score >= 70:
            lines.append(
                "🟡 **Resilience Level:** Good - Most attacks blocked, minor issues found"
            )
        elif score >= 50:
            lines.append(
                "🟠 **Resilience Level:** Moderate - Several vulnerabilities need attention"
            )
        else:
            lines.append(
                "🔴 **Resilience Level:** Poor - Critical vulnerabilities found, immediate action required"
            )

        lines.append("")

        # Vulnerabilities by severity
        if self.session.vulnerabilities_found:
            lines.extend(
                [
                    "",
                    "## 🚨 Vulnerabilities Found",
                    "",
                ]
            )

            # Group by severity
            critical = [
                v
                for v in self.session.vulnerabilities_found
                if v.severity == SeverityLevel.CRITICAL
            ]
            high = [
                v
                for v in self.session.vulnerabilities_found
                if v.severity == SeverityLevel.HIGH
            ]
            medium = [
                v
                for v in self.session.vulnerabilities_found
                if v.severity == SeverityLevel.MEDIUM
            ]
            low = [
                v
                for v in self.session.vulnerabilities_found
                if v.severity == SeverityLevel.LOW
            ]

            if critical:
                lines.extend(["### 🔴 Critical", ""])
                for vuln in critical:
                    lines.extend(self._format_vulnerability(vuln))

            if high:
                lines.extend(["### 🟠 High", ""])
                for vuln in high:
                    lines.extend(self._format_vulnerability(vuln))

            if medium:
                lines.extend(["### 🟡 Medium", ""])
                for vuln in medium:
                    lines.extend(self._format_vulnerability(vuln))

            if low:
                lines.extend(["### 🟢 Low", ""])
                for vuln in low:
                    lines.extend(self._format_vulnerability(vuln))

        # Attack type breakdown
        lines.extend(
            [
                "",
                "## 📈 Attack Type Breakdown",
                "",
            ]
        )

        attack_types = {}
        for vuln in self.session.vulnerabilities_found:
            attack_type = vuln.payload.attack_type.value
            if attack_type not in attack_types:
                attack_types[attack_type] = 0
            attack_types[attack_type] += 1

        if attack_types:
            lines.append("| Attack Type | Count |")
            lines.append("|-------------|-------|")
            for attack_type, count in sorted(
                attack_types.items(), key=lambda x: x[1], reverse=True
            ):
                lines.append(f"| {attack_type} | {count} |")
        else:
            lines.append("No vulnerabilities found by attack type.")

        lines.extend(
            [
                "",
                "## 🎯 Recommendations",
                "",
                "Based on the security testing results:",
                "",
            ]
        )

        if score < 50:
            lines.extend(
                [
                    "🔴 **Critical Priority:**",
                    "- Implement comprehensive input validation on all endpoints",
                    "- Add parameterized queries to prevent SQL/NoSQL injection",
                    "- Set up request size limits to prevent buffer overflow",
                    "- Review and strengthen error handling to prevent information leakage",
                    "",
                ]
            )

        if critical or high:
            lines.extend(
                [
                    "⚠️ **High Priority Issues:**",
                    "- Review all fields accepting user input for proper sanitization",
                    "- Implement strict type validation before processing requests",
                    "- Add rate limiting to prevent brute force attacks",
                    "",
                ]
            )

        lines.extend(
            [
                "✅ **General Best Practices:**",
                "- Implement Web Application Firewall (WAF)",
                "- Regular security testing with updated payload databases",
                "- Monitor logs for suspicious activity patterns",
                "- Keep dependencies updated to patch known vulnerabilities",
                "",
            ]
        )

        lines.extend(
            [
                "---",
                "",
                "*This report was generated by socialseed-e2e AI Security Fuzzer*",
            ]
        )

        return "\n".join(lines)

    def _format_vulnerability(self, vuln: SecurityTestResult) -> List[str]:
        """Format a single vulnerability for the report.

        Args:
            vuln: Vulnerability to format

        Returns:
            List of markdown lines
        """
        lines = [
            f"**Endpoint:** `{vuln.endpoint}`",
            f"**Field:** `{vuln.field_name}`",
            f"**Attack Type:** {vuln.payload.attack_type.value}",
            f"**Status Code:** {vuln.response_status}",
            f"**Payload:** `{str(vuln.payload.value)[:100]}`",
            "",
        ]

        if vuln.response_body:
            lines.append(f"**Response Preview:** `{vuln.response_body[:200]}`")
            lines.append("")

        lines.append("---")
        lines.append("")

        return lines

    def save_report(self, output_path: str) -> None:
        """Save report to file.

        Args:
            output_path: Path to save the report
        """
        report = self.generate_report()
        with open(output_path, "w") as f:
            f.write(report)


def run_security_fuzzing(
    service_page: Any, service_info: ServiceInfo, max_payloads_per_field: int = 10
) -> FuzzingSession:
    """Convenience function to run security fuzzing on a service.

    Args:
        service_page: Service page instance
        service_info: Service information
        max_payloads_per_field: Max payloads per field

    Returns:
        Completed fuzzing session
    """
    executor = SecurityTestExecutor(
        base_url=service_page.base_url, service_page=service_page
    )

    # Start session
    endpoints = [ep.name for ep in service_info.endpoints]
    session = executor.start_session(endpoints)

    # Execute tests for each endpoint
    for endpoint in service_info.endpoints:
        if endpoint.request_dto:
            # Find DTO
            dto = next(
                (d for d in service_info.dto_schemas if d.name == endpoint.request_dto),
                None,
            )

            if dto:
                executor.execute_security_tests(endpoint, dto, max_payloads_per_field)

    # End session
    executor.end_session()

    return session
