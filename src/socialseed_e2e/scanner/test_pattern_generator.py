"""Test pattern generator for generating test templates.

This module generates test patterns and CRUD templates based on
detected endpoints and schemas.
"""

from typing import Any, Dict, List


class TestPatternGenerator:
    """Generates test patterns and CRUD templates."""

    # Common test patterns
    TEST_PATTERNS = {
        "happy_path": """## {name} - Happy Path

```python
def test_{name}_{action}():
    \"\"\"Test: {description}\"\"\"
    # Arrange
    data = {data}
    
    # Act
    response = page.{method}("{endpoint}", data=data)
    
    # Assert
    assert response.status == {expected_status}
    assert response.json()["status"] == {expected_status}
""",
        "not_found": """## {name} - Not Found

```python
def test_{name}_not_found():
    \"\"\"Test: {description}\"\"\"
    # Act
    response = page.{method}("{endpoint}")
    
    # Assert
    assert response.status == 404
""",
        "unauthorized": """## {name} - Unauthorized

```python
def test_{name}_unauthorized():
    \"\"\"Test: {description}\"\"\"
    # Act
    response = page.{method}("{endpoint}")
    
    # Assert
    assert response.status == 401
""",
        "validation_error": """## {name} - Validation Error

```python
def test_{name}_validation_error():
    \"\"\"Test: {description}\"\"\"
    # Arrange
    data = {data}
    
    # Act
    response = page.{method}("{endpoint}", data=data)
    
    # Assert
    assert response.status == 400
    assert "error" in response.json() or "message" in response.json()
""",
    }

    def __init__(self, endpoints: List[Any], schemas: List[Any]):
        self.endpoints = endpoints
        self.schemas = schemas

    def generate_crud_tests(self) -> str:
        """Generate CRUD test patterns based on detected endpoints."""

        # Find CRUD endpoints
        resources = {}
        for ep in self.endpoints:
            # Extract resource name from path
            parts = ep.path.strip("/").split("/")
            if len(parts) >= 1:
                resource = parts[0]
                if resource not in resources:
                    resources[resource] = {
                        "GET": [],
                        "POST": [],
                        "PUT": [],
                        "DELETE": [],
                        "PATCH": [],
                    }
                if ep.method in resources[resource]:
                    resources[resource][ep.method].append(ep)

        md = "# CRUD Test Templates\n\n"
        md += "This document contains test templates for each detected resource.\n\n"

        for resource, methods in resources.items():
            md += f"## {resource.title()} CRUD\n\n"

            # Create
            if methods.get("POST"):
                md += "### Create\n\n"
                ep = methods["POST"][0]
                md += f"**Endpoint:** `{ep.method} {ep.path}`\n\n"
                md += f"**Auth Required:** {'Yes' if ep.auth_required else 'No'}\n\n"
                md += self.TEST_PATTERNS["happy_path"].format(
                    name=resource,
                    action="create",
                    description=f"Create a new {resource}",
                    data="{" + f'"{resource[:-1]}_name": "test"' + "}",
                    method="post",
                    endpoint=ep.path,
                    expected_status="201",
                )
                md += "\n"

            # Read All
            if methods.get("GET") and len(methods["GET"]) == 1:
                md += "### List All\n\n"
                ep = methods["GET"][0]
                md += f"**Endpoint:** `{ep.method} {ep.path}`\n\n"
                md += f"**Auth Required:** {'Yes' if ep.auth_required else 'No'}\n\n"
                md += self.TEST_PATTERNS["happy_path"].format(
                    name=resource,
                    action="list",
                    description=f"List all {resource}",
                    data="{}",
                    method="get",
                    endpoint=ep.path,
                    expected_status="200",
                )
                md += "\n"

            # Read One
            get_by_id = [
                ep for ep in methods.get("GET", []) if "{id}" in ep.path or "/{" in ep.path
            ]
            if get_by_id:
                md += "### Get by ID\n\n"
                ep = get_by_id[0]
                md += f"**Endpoint:** `{ep.method} {ep.path}`\n\n"
                md += f"**Auth Required:** {'Yes' if ep.auth_required else 'No'}\n\n"
                md += self.TEST_PATTERNS["happy_path"].format(
                    name=resource,
                    action="get_by_id",
                    description=f"Get {resource} by ID",
                    data="{}",
                    method="get",
                    endpoint=ep.path.replace("{id}", "test-id-123"),
                    expected_status="200",
                )
                md += "\n"
                md += self.TEST_PATTERNS["not_found"].format(
                    name=resource,
                    action="get_by_id_not_found",
                    description=f"Get {resource} with non-existent ID",
                    method="get",
                    endpoint=ep.path.replace("{id}", "non-existent-id"),
                )
                md += "\n"

            # Update
            if methods.get("PUT") or methods.get("PATCH"):
                md += "### Update\n\n"
                ep = methods.get("PUT") or methods.get("PATCH")
                if ep:
                    ep = ep[0]
                    md += f"**Endpoint:** `{ep.method} {ep.path}`\n\n"
                    md += f"**Auth Required:** {'Yes' if ep.auth_required else 'No'}\n\n"
                    md += self.TEST_PATTERNS["happy_path"].format(
                        name=resource,
                        action="update",
                        description=f"Update {resource}",
                        data="{" + f'"{resource[:-1]}_name": "updated"' + "}",
                        method="put" if methods.get("PUT") else "patch",
                        endpoint=ep.path.replace("{id}", "test-id-123"),
                        expected_status="200",
                    )
                    md += "\n"

            # Delete
            if methods.get("DELETE"):
                md += "### Delete\n\n"
                ep = methods["DELETE"][0]
                md += f"**Endpoint:** `{ep.method} {ep.path}`\n\n"
                md += f"**Auth Required:** {'Yes' if ep.auth_required else 'No'}\n\n"
                md += self.TEST_PATTERNS["happy_path"].format(
                    name=resource,
                    action="delete",
                    description=f"Delete {resource}",
                    data="{}",
                    method="delete",
                    endpoint=ep.path.replace("{id}", "test-id-123"),
                    expected_status="204",
                )
                md += "\n"

            md += "---\n\n"

        return md

    def generate_security_tests(self) -> str:
        """Generate security test patterns."""

        md = "# Security Test Templates\n\n"
        md += "This document contains security test templates.\n\n"

        # Find auth endpoints
        auth_endpoints = [ep for ep in self.endpoints if ep.auth_required]

        md += "## Authentication Tests\n\n"

        md += "### Unauthorized Access\n\n"
        md += """```python
def test_unauthorized_access():
    \"\"\"Test: Access protected endpoint without token\"\"\"
    # Act
    response = page.get("/protected/endpoint")
    
    # Assert
    assert response.status == 401
```
"""

        md += "### Invalid Token\n\n"
        md += """```python
def test_invalid_token():
    \"\"\"Test: Access with invalid token\"\"\"
    # Act
    response = page.get(
        "/protected/endpoint",
        headers={"Authorization": "Bearer invalid-token"}
    )
    
    # Assert
    assert response.status == 401
```
"""

        md += "## SQL Injection Tests\n\n"
        md += """```python
SQL_PAYLOADS = [
    "' OR '1'='1",
    "' OR '1'='1' --",
    "admin'--",
    "1' AND '1'='1",
]

def test_sql_injection():
    \"\"\"Test: SQL Injection in query parameters\"\"\"
    for payload in SQL_PAYLOADS:
        response = page.get(f"/users?username={payload}")
        # Should not reveal database errors
        assert "sql" not in response.text.lower()
        assert response.status != 500
```
"""

        md += "## XSS Tests\n\n"
        md += """```python
XSS_PAYLOADS = [
    "<script>alert('XSS')</script>",
    "<img src=x onerror=alert(1)>",
    "javascript:alert(1)",
]

def test_xss_in_input():
    \"\"\"Test: XSS in input fields\"\"\"
    for payload in XSS_PAYLOADS:
        response = page.post("/users", data={"username": payload})
        # Server should sanitize or reject
        assert response.status in [200, 201, 400]
```
"""

        md += "## IDOR Tests\n\n"
        md += """```python
def test_idor_access():
    \"\"\"Test: Insecure Direct Object Reference\"\"\"
    # Login as user A
    token_a = login("user_a")
    
    # Try to access user B's data
    response = page.get(
        f"/users/user-b-id",
        headers={"Authorization": f"Bearer {token_a}"}
    )
    
    # Should be 403 or 404, not 200
    assert response.status in [403, 404]
```
"""

        md += "## Rate Limiting Tests\n\n"
        md += """```python
def test_rate_limiting():
    \"\"\"Test: Rate limiting on endpoint\"\"\"
    responses = []
    for _ in range(100):
        response = page.get("/api/data")
        responses.append(response.status)
    
    # Should get rate limited eventually
    assert 429 in responses
```
"""

        return md

    def generate_patterns_doc(self) -> str:
        """Generate complete patterns documentation."""

        md = "# Test Patterns\n\n"
        md += f"**Total endpoints:** {len(self.endpoints)}\n"
        md += f"**Total schemas:** {len(self.schemas)}\n\n"

        md += "## Common Test Patterns\n\n"

        md += "### Arrange-Act-Assert\n\n"
        md += """```python
def test_example():
    # Arrange - setup data
    data = {"field": "value"}
    
    # Act - perform action
    response = page.post("/endpoint", data=data)
    
    # Assert - verify result
    assert response.status == 200
    assert response.json()["data"]["field"] == "value"
```
"""

        md += "### Given-When-Then\n\n"
        md += """```python
def test_example():
    # Given - precondition
    user = create_test_user()
    token = login(user)
    
    # When - action
    response = page.get(
        "/protected",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Then - assertion
    assert response.status == 200
```
"""

        md += "### Error Handling\n\n"
        md += """```python
def test_validation_error():
    # Send invalid data
    response = page.post("/users", data={"email": "not-an-email"})
    
    # Verify error response
    assert response.status == 400
    errors = response.json()
    assert "email" in str(errors).lower()
```
"""

        return md


def generate_test_patterns(endpoints: List[Any], schemas: List[Any]) -> str:
    """Convenience function to generate test patterns documentation."""
    generator = TestPatternGenerator(endpoints, schemas)
    doc = generator.generate_patterns_doc()
    doc += "\n\n" + generator.generate_crud_tests()
    doc += "\n\n" + generator.generate_security_tests()
    return doc
