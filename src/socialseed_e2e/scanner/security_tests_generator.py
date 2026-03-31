"""Security tests generator for generating security test cases.

This module generates security tests for SQL injection, XSS, IDOR,
broken authentication, and other common vulnerabilities.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class SecurityTest:
    """Represents a security test case."""

    name: str
    category: str
    description: str
    test_code: str
    severity: str = "high"


@dataclass
class SecurityInfo:
    """Represents security test information."""

    tests: List[SecurityTest] = field(default_factory=list)
    vulnerabilities: List[Dict[str, str]] = field(default_factory=list)


class SecurityTestGenerator:
    """Generates security test cases."""

    SQL_INJECTION_PAYLOADS = [
        "' OR '1'='1",
        "' OR '1'='1' --",
        "admin'--",
        "' OR 1=1--",
        "' UNION SELECT NULL--",
        "' AND 1=1--",
        "'; DROP TABLE users--",
        "1' AND '1'='1",
        "' OR ''='",
    ]

    XSS_PAYLOADS = [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>",
        "<svg onload=alert('XSS')>",
        "javascript:alert('XSS')",
        "<body onload=alert('XSS')>",
        "<iframe src=javascript:alert('XSS')>",
    ]

    NOSQL_INJECTION_PAYLOADS = [
        "' || '1'=='1",
        "'; return 'a'=='a",
        "{\"$ne\": null}",
        "{\"$gt\": \"\"}",
        "admin' OR 1=1--",
    ]

    def __init__(self, project_root: Path, service_name: str = "service"):
        self.project_root = project_root
        self.service_name = service_name

    def generate(self) -> SecurityInfo:
        """Generate security tests."""
        info = SecurityInfo()

        self._generate_sql_injection_tests(info)
        self._generate_xss_tests(info)
        self._generate_nosql_injection_tests(info)
        self._generate_idor_tests(info)
        self._generate_auth_tests(info)

        return info

    def _generate_sql_injection_tests(self, info: SecurityInfo) -> None:
        """Generate SQL injection tests."""
        for payload in self.SQL_INJECTION_PAYLOADS[:3]:
            test = SecurityTest(
                name=f"test_sql_injection_{len(info.tests) + 1}",
                category="SQL Injection",
                description=f"Test SQL injection with payload: {payload}",
                severity="critical",
                test_code=f'''def test_sql_injection_{len(info.tests) + 1}(page):
    """Test SQL injection vulnerability"""
    payloads = ["{payload}"]
    
    for payload in payloads:
        response = page.post("/auth/login", data={{
            "email": payload,
            "password": "anything"
        }})
        # Should not reveal database errors
        assert response.status != 200 or "sql" not in response.text.lower()
        assert "syntax" not in response.text.lower()
        assert "mysql" not in response.text.lower()
        assert "postgres" not in response.text.lower()
''',
            )
            info.tests.append(test)

    def _generate_xss_tests(self, info: SecurityInfo) -> None:
        """Generate XSS tests."""
        for payload in self.XSS_PAYLOADS[:2]:
            test = SecurityTest(
                name=f"test_xss_{len(info.tests) + 1}",
                category="XSS",
                description=f"Test XSS vulnerability with payload: {payload}",
                severity="high",
                test_code=f'''def test_xss_{len(info.tests) + 1}(page):
    """Test XSS vulnerability"""
    payload = "{payload}"
    
    response = page.post("/users", data={{
        "username": payload,
        "email": "test@example.com",
        "password": "password"
    }})
    # Server should sanitize or reject
    assert response.status in [400, 201]
    
    # If created, check response doesn't contain raw payload
    if response.status == 201:
        assert payload not in response.text
''',
            )
            info.tests.append(test)

    def _generate_nosql_injection_tests(self, info: SecurityInfo) -> None:
        """Generate NoSQL injection tests."""
        for payload in self.NOSQL_INJECTION_PAYLOADS[:2]:
            test = SecurityTest(
                name=f"test_nosql_injection_{len(info.tests) + 1}",
                category="NoSQL Injection",
                description=f"Test NoSQL injection with payload: {payload}",
                severity="high",
                test_code=f'''def test_nosql_injection_{len(info.tests) + 1}(page):
    """Test NoSQL injection vulnerability"""
    payload = "{payload}"
    
    response = page.post("/auth/login", data={{
        "email": payload,
        "password": payload
    }})
    # Should not authenticate with injection
    assert response.status != 200 or response.json().get("data", {{}}).get("token") is None
''',
            )
            info.tests.append(test)

    def _generate_idor_tests(self, info: SecurityInfo) -> None:
        """Generate IDOR tests."""
        test = SecurityTest(
            name=f"test_idor_user_access",
            category="IDOR",
            description="Test Insecure Direct Object Reference - accessing other user data",
            severity="high",
            test_code='''def test_idor_user_access(page):
    """Test IDOR - accessing other user's data"""
    # Login as user A
    token_a = login("usera", "passwordA")
    
    # Get user B's ID
    user_b_id = "550e8400-e29b-41d4-a716-446655440000"
    
    # Try to access as user A
    response = page.get(
        f"/users/{{user_b_id}}",
        headers={"Authorization": f"Bearer {{token_a}}"}
    )
    # Should be 403 or 404, not 200
    assert response.status in [403, 404]
''',
        )
        info.tests.append(test)

    def _generate_auth_tests(self, info: SecurityInfo) -> None:
        """Generate authentication tests."""
        tests = [
            ("test_broken_auth_password_reset", "Broken Authentication",
             "Test password reset flow", "medium"),
            ("test_session_fixation", "Session Management",
             "Test session fixation protection", "medium"),
            ("test_weak_password_policy", "Password Policy",
             "Test weak password acceptance", "high"),
        ]

        for name, category, desc, severity in tests:
            test = SecurityTest(
                name=name,
                category=category,
                description=desc,
                severity=severity,
                test_code=f'''def {name}(page):
    """Test {desc}"""
    # TODO: Implement specific test based on the vulnerability
    pass
''',
            )
            info.tests.append(test)


def generate_security_tests_doc(project_root: Path, output_path: Optional[Path] = None) -> str:
    """Generate SECURITY_TESTS.md document."""
    generator = SecurityTestGenerator(project_root)
    info = generator.generate()

    doc = "# Tests de Seguridad\n\n"

    categories = {}
    for test in info.tests:
        if test.category not in categories:
            categories[test.category] = []
        categories[test.category].append(test)

    for category, tests in categories.items():
        doc += f"## {category}\n\n"
        severity_icons = {"critical": "🚨", "high": "⚠️", "medium": "⚡", "low": "🔹"}

        for test in tests:
            icon = severity_icons.get(test.severity, "")
            doc += f"### {icon} {test.name}\n\n"
            doc += f"{test.description}\n\n"
            doc += f"```python\n{test.test_code}\n```\n\n"

    doc += "---\n\n"
    doc += "## Ejecución de Tests de Seguridad\n\n"
    doc += "```bash\n"
    doc += "# Ejecutar todos los tests de seguridad\n"
    doc += "e2e run --service auth-service --tag security\n\n"
    doc += "# Ejecutar solo SQL Injection\n"
    doc += "e2e run --service auth-service --tag sql-injection\n\n"
    doc += "# Ejecutar solo XSS\n"
    doc += "e2e run --service auth-service --tag xss\n"
    doc += "```\n"

    if output_path:
        output_path.write_text(doc)

    return doc


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        project_root = Path(sys.argv[1])
        print(generate_security_tests_doc(project_root))
    else:
        print("Usage: python security_tests_generator.py <project_root>")
