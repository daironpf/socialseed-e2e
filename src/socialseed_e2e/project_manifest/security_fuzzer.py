"""AI-Driven Intelligent Fuzzing and Security Testing Module.

This module provides intelligent fuzzing capabilities with:
- Malicious payload generation (SQL Injection, NoSQL Injection)
- Buffer overflow attempts and large blob attacks
- Logic-breaking type attacks
- Resilience monitoring and security reporting

Issue #189: Implement AI-Driven Intelligent Fuzzing and Security Testing
"""

import random
import string
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from socialseed_e2e.project_manifest.models import DtoField


class AttackType(str, Enum):
    """Types of security attacks to test."""

    SQL_INJECTION = "sql_injection"
    NOSQL_INJECTION = "nosql_injection"
    BUFFER_OVERFLOW = "buffer_overflow"
    TYPE_MANIPULATION = "type_manipulation"
    XSS = "xss"
    COMMAND_INJECTION = "command_injection"
    PATH_TRAVERSAL = "path_traversal"
    LOGIC_BYPASS = "logic_bypass"


class SeverityLevel(str, Enum):
    """Severity levels for vulnerabilities."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class SecurityPayload:
    """A security test payload with metadata."""

    value: Any
    attack_type: AttackType
    description: str
    expected_behavior: str  # "blocked", "crash", "bypass"
    field_target: Optional[str] = None
    severity: SeverityLevel = SeverityLevel.MEDIUM


@dataclass
class SecurityTestResult:
    """Result of a security test execution."""

    endpoint: str
    field_name: str
    payload: SecurityPayload
    response_status: int
    response_body: str
    test_passed: bool  # True if properly blocked, False if vulnerability found
    execution_time_ms: float
    timestamp: datetime
    vulnerability_found: bool = False
    severity: SeverityLevel = SeverityLevel.INFO
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FuzzingSession:
    """A complete fuzzing session with all results."""

    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    target_endpoints: List[str] = field(default_factory=list)
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    vulnerabilities_found: List[SecurityTestResult] = field(default_factory=list)
    resilience_score: float = 0.0  # 0.0 to 100.0


class MaliciousPayloadGenerator:
    """Generator for malicious security testing payloads."""

    # SQL Injection payloads
    SQL_INJECTION_PAYLOADS = [
        # Classic SQLi
        "' OR '1'='1",
        "' OR '1'='1' --",
        "' OR '1'='1' /*",
        "' OR 1=1 --",
        "' OR 1=1#",
        "' OR 1=1/*",
        "') OR ('1'='1",
        "') OR ('1'='1' --",
        # Union-based
        "' UNION SELECT NULL--",
        "' UNION SELECT NULL,NULL--",
        "' UNION SELECT username,password FROM users--",
        # Error-based
        "' AND 1=CONVERT(int, (SELECT @@version)) --",
        "' AND 1=(SELECT COUNT(*) FROM tablenames) --",
        # Time-based blind
        "'; WAITFOR DELAY '0:0:5'--",
        "' AND pg_sleep(5)--",
        "' AND (SELECT * FROM (SELECT(SLEEP(5)))a) --",
        # Boolean-based blind
        "' AND 1=1 --",
        "' AND 1=2 --",
        # Stacked queries
        "'; DROP TABLE users; --",
        "'; DELETE FROM users WHERE '1'='1",
        # NoSQL Injection
        "{'$gt': ''}",
        "{'$ne': null}",
        "{'$regex': '.*'}",
        "{'$where': 'this.password.length > 0'}",
    ]

    # NoSQL Injection payloads (MongoDB, etc.)
    NOSQL_INJECTION_PAYLOADS = [
        '{"$gt": ""}',
        '{"$ne": null}',
        '{"$exists": true}',
        '{"$regex": ".*"}',
        '{"$where": "this.password.length > 0"}',
        '{"username": {"$ne": null}}',
        '{"username": {"$gt": ""}}',
        '{"username": {"$regex": "admin"}}',
        '{"$or": [{"username": "admin"}, {"username": {"$ne": null}}]}',
    ]

    # XSS payloads
    XSS_PAYLOADS = [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>",
        "<svg onload=alert('XSS')>",
        "javascript:alert('XSS')",
        "<iframe src=javascript:alert('XSS')>",
        "<body onload=alert('XSS')>",
    ]

    # Command Injection payloads
    COMMAND_INJECTION_PAYLOADS = [
        "; cat /etc/passwd",
        "| whoami",
        "`whoami`",
        "$(whoami)",
        "; rm -rf /",
        "| dir",
        "& ping -c 4 127.0.0.1",
    ]

    # Path Traversal payloads
    PATH_TRAVERSAL_PAYLOADS = [
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32\\config\\sam",
        "....//....//....//etc/passwd",
        "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc/passwd",
        "..%252f..%252f..%252fetc/passwd",
    ]

    def __init__(self):
        self.payload_history: Set[str] = set()

    def generate_sql_injection_payloads(
        self, field_type: str = "string"
    ) -> List[SecurityPayload]:
        """Generate SQL injection payloads.

        Args:
            field_type: Type of field being targeted

        Returns:
            List of SQL injection payloads
        """
        payloads = []

        for sql_payload in self.SQL_INJECTION_PAYLOADS:
            payloads.append(
                SecurityPayload(
                    value=sql_payload,
                    attack_type=AttackType.SQL_INJECTION,
                    description=f"SQL Injection attempt: {sql_payload[:30]}...",
                    expected_behavior="blocked",
                    severity=SeverityLevel.CRITICAL,
                )
            )

        # Add field-specific variations
        if field_type.lower() in ["int", "integer", "float", "number"]:
            # Numeric SQLi
            numeric_payloads = [
                "1 OR 1=1",
                "1 AND 1=1",
                "1 UNION SELECT 1",
            ]
            for payload in numeric_payloads:
                payloads.append(
                    SecurityPayload(
                        value=payload,
                        attack_type=AttackType.SQL_INJECTION,
                        description=f"Numeric SQL Injection: {payload}",
                        expected_behavior="blocked",
                        severity=SeverityLevel.CRITICAL,
                    )
                )

        return payloads

    def generate_nosql_injection_payloads(self) -> List[SecurityPayload]:
        """Generate NoSQL injection payloads.

        Returns:
            List of NoSQL injection payloads
        """
        payloads = []

        for nosql_payload in self.NOSQL_INJECTION_PAYLOADS:
            payloads.append(
                SecurityPayload(
                    value=nosql_payload,
                    attack_type=AttackType.NOSQL_INJECTION,
                    description="NoSQL Injection attempt",
                    expected_behavior="blocked",
                    severity=SeverityLevel.CRITICAL,
                )
            )

        return payloads

    def generate_buffer_overflow_payloads(
        self, field_name: str = "", min_size: int = 1024, max_size: int = 100000
    ) -> List[SecurityPayload]:
        """Generate buffer overflow / large blob payloads.

        Args:
            field_name: Name of the field being targeted
            min_size: Minimum payload size
            max_size: Maximum payload size

        Returns:
            List of buffer overflow payloads
        """
        payloads = []

        # Various sizes for buffer overflow testing
        sizes = [
            1024,  # 1KB
            4096,  # 4KB
            8192,  # 8KB
            65536,  # 64KB
            1048576,  # 1MB
            10485760,  # 10MB
        ]

        for size in sizes:
            if min_size <= size <= max_size:
                # Generate random data
                random_data = "".join(
                    random.choices(
                        string.ascii_letters + string.digits,
                        k=min(size, 1000),  # Limit display size
                    )
                )

                payloads.append(
                    SecurityPayload(
                        value=random_data * (size // 1000)
                        if size > 1000
                        else random_data,
                        attack_type=AttackType.BUFFER_OVERFLOW,
                        description=f"Buffer overflow attempt: {size} bytes",
                        expected_behavior="blocked",
                        severity=SeverityLevel.HIGH,
                    )
                )

        # Add specific overflow patterns
        patterns = [
            "A" * 10000,  # Classic buffer overflow
            "%s" * 1000,  # Format string attack
            "\x00" * 1000,  # Null bytes
            "\xff" * 1000,  # High bytes
        ]

        for pattern in patterns:
            payloads.append(
                SecurityPayload(
                    value=pattern,
                    attack_type=AttackType.BUFFER_OVERFLOW,
                    description="Buffer overflow pattern attack",
                    expected_behavior="blocked",
                    severity=SeverityLevel.HIGH,
                )
            )

        return payloads

    def generate_type_manipulation_payloads(
        self, expected_type: str
    ) -> List[SecurityPayload]:
        """Generate logic-breaking type manipulation payloads.

        Args:
            expected_type: The expected data type

        Returns:
            List of type manipulation payloads
        """
        payloads = []

        if expected_type.lower() in ["int", "integer", "number"]:
            # Send strings where integers expected
            string_payloads = [
                "not_a_number",
                "123abc",
                "",
                "null",
                "undefined",
                "true",
                "false",
                "1e309",  # Infinity
                "-1e309",  # -Infinity
                "NaN",
                "123.456.789",
                "0x1G",  # Invalid hex
                "2.3.4",
                "--1",
                "++1",
            ]

            for payload in string_payloads:
                payloads.append(
                    SecurityPayload(
                        value=payload,
                        attack_type=AttackType.TYPE_MANIPULATION,
                        description=f"String in integer field: {payload}",
                        expected_behavior="blocked",
                        severity=SeverityLevel.MEDIUM,
                    )
                )

            # Extreme numeric values
            numeric_payloads = [
                9223372036854775807,  # Max int64
                -9223372036854775808,  # Min int64
                1.7976931348623157e308,  # Max double
                2.2250738585072014e-308,  # Min double
                float("inf"),
                float("-inf"),
            ]

            for payload in numeric_payloads:
                payloads.append(
                    SecurityPayload(
                        value=payload,
                        attack_type=AttackType.TYPE_MANIPULATION,
                        description=f"Extreme numeric value: {payload}",
                        expected_behavior="blocked",
                        severity=SeverityLevel.MEDIUM,
                    )
                )

        elif expected_type.lower() in ["str", "string", "text"]:
            # Send non-strings where strings expected
            non_string_payloads = [
                12345,
                True,
                False,
                None,
                [],
                {},
                {"key": "value"},
                [1, 2, 3],
            ]

            for payload in non_string_payloads:
                payloads.append(
                    SecurityPayload(
                        value=payload,
                        attack_type=AttackType.TYPE_MANIPULATION,
                        description=f"Non-string in string field: {type(payload).__name__}",
                        expected_behavior="blocked",
                        severity=SeverityLevel.LOW,
                    )
                )

        elif expected_type.lower() in ["bool", "boolean"]:
            # Send non-booleans where booleans expected
            non_bool_payloads = [
                "true",
                "false",
                "yes",
                "no",
                "1",
                "0",
                1,
                0,
                2,
                -1,
                None,
            ]

            for payload in non_bool_payloads:
                payloads.append(
                    SecurityPayload(
                        value=payload,
                        attack_type=AttackType.TYPE_MANIPULATION,
                        description=f"Non-boolean in boolean field: {payload}",
                        expected_behavior="blocked",
                        severity=SeverityLevel.LOW,
                    )
                )

        elif expected_type.lower() in ["list", "array"]:
            # Send non-arrays where arrays expected
            non_array_payloads = [
                "not_an_array",
                123,
                {"not": "array"},
                None,
            ]

            for payload in non_array_payloads:
                payloads.append(
                    SecurityPayload(
                        value=payload,
                        attack_type=AttackType.TYPE_MANIPULATION,
                        description=f"Non-array in array field: {type(payload).__name__}",
                        expected_behavior="blocked",
                        severity=SeverityLevel.LOW,
                    )
                )

        return payloads

    def generate_xss_payloads(self) -> List[SecurityPayload]:
        """Generate XSS payloads.

        Returns:
            List of XSS payloads
        """
        payloads = []

        for xss_payload in self.XSS_PAYLOADS:
            payloads.append(
                SecurityPayload(
                    value=xss_payload,
                    attack_type=AttackType.XSS,
                    description="XSS attempt",
                    expected_behavior="blocked",
                    severity=SeverityLevel.HIGH,
                )
            )

        return payloads

    def generate_command_injection_payloads(self) -> List[SecurityPayload]:
        """Generate command injection payloads.

        Returns:
            List of command injection payloads
        """
        payloads = []

        for cmd_payload in self.COMMAND_INJECTION_PAYLOADS:
            payloads.append(
                SecurityPayload(
                    value=cmd_payload,
                    attack_type=AttackType.COMMAND_INJECTION,
                    description="Command injection attempt",
                    expected_behavior="blocked",
                    severity=SeverityLevel.CRITICAL,
                )
            )

        return payloads

    def generate_path_traversal_payloads(self) -> List[SecurityPayload]:
        """Generate path traversal payloads.

        Returns:
            List of path traversal payloads
        """
        payloads = []

        for path_payload in self.PATH_TRAVERSAL_PAYLOADS:
            payloads.append(
                SecurityPayload(
                    value=path_payload,
                    attack_type=AttackType.PATH_TRAVERSAL,
                    description="Path traversal attempt",
                    expected_behavior="blocked",
                    severity=SeverityLevel.HIGH,
                )
            )

        return payloads

    def generate_all_payloads_for_field(
        self, field: DtoField, include_all_attack_types: bool = True
    ) -> List[SecurityPayload]:
        """Generate all applicable payloads for a field.

        Args:
            field: DTO field to generate payloads for
            include_all_attack_types: Whether to include all attack types

        Returns:
            List of security payloads
        """
        payloads = []

        # Always include type manipulation
        payloads.extend(self.generate_type_manipulation_payloads(field.type))

        if include_all_attack_types:
            # Include SQL injection for string fields
            if field.type.lower() in ["str", "string", "text", "email"]:
                payloads.extend(self.generate_sql_injection_payloads(field.type))
                payloads.extend(self.generate_nosql_injection_payloads())
                payloads.extend(self.generate_xss_payloads())
                payloads.extend(self.generate_path_traversal_payloads())

                # Buffer overflow for fields without max_length
                if not any(v.rule_type == "max_length" for v in field.validations):
                    payloads.extend(self.generate_buffer_overflow_payloads(field.name))

            # Command injection for fields that might execute commands
            if any(
                keyword in field.name.lower()
                for keyword in ["command", "exec", "shell", "cmd", "script", "eval"]
            ):
                payloads.extend(self.generate_command_injection_payloads())

        # Set field target for all payloads
        for payload in payloads:
            payload.field_target = field.name

        return payloads
