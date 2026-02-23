"""Example projects module for socialseed-e2e.

This module provides pre-built example projects for different
industries and architectures.
"""

from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class ExampleType(str, Enum):
    """Types of example projects."""

    ECOMMERCE = "ecommerce"
    BANKING = "banking"
    HEALTHCARE = "healthcare"
    MICROSERVICES = "microservices"
    MONOLITHIC = "monolithic"
    SERVERLESS = "serverless"


class ExampleProject:
    """Represents an example project."""

    def __init__(
        self,
        name: str,
        description: str,
        example_type: ExampleType,
        services: List[str],
        features: List[str],
    ):
        """Initialize example project."""
        self.name = name
        self.description = description
        self.example_type = example_type
        self.services = services
        self.features = features


class ExampleProjectGenerator:
    """Generate example projects."""

    def __init__(self):
        """Initialize example project generator."""
        self._examples = self._load_examples()

    def _load_examples(self) -> Dict[str, ExampleProject]:
        """Load predefined examples."""
        return {
            "ecommerce-api": ExampleProject(
                name="E-commerce API",
                description="Complete e-commerce API with products, orders, cart, and payments",
                example_type=ExampleType.ECOMMERCE,
                services=["products", "orders", "cart", "payments", "users"],
                features=[
                    "CRUD operations",
                    "Authentication",
                    "Payment processing",
                    "Inventory management",
                ],
            ),
            "banking-api": ExampleProject(
                name="Banking API",
                description="Secure banking API with accounts, transactions, and transfers",
                example_type=ExampleType.BANKING,
                services=["accounts", "transactions", "transfers", "loans", "users"],
                features=[
                    "Account management",
                    "Fund transfers",
                    "Transaction history",
                    "Loan processing",
                ],
            ),
            "healthcare-api": ExampleProject(
                name="Healthcare API",
                description="HIPAA-compliant healthcare API with patient records and appointments",
                example_type=ExampleType.HEALTHCARE,
                services=[
                    "patients",
                    "appointments",
                    "medical-records",
                    "prescriptions",
                ],
                features=[
                    "Patient management",
                    "Appointment scheduling",
                    "Medical records",
                    "Prescription management",
                ],
            ),
            "social-media-api": ExampleProject(
                name="Social Media API",
                description="Social media platform API with posts, comments, and followers",
                example_type=ExampleType.MICROSERVICES,
                services=["posts", "comments", "users", "followers", "notifications"],
                features=[
                    "Post creation",
                    "Comments",
                    "Follow system",
                    "Notifications",
                ],
            ),
        }

    def list_examples(self) -> List[ExampleProject]:
        """List all available examples."""
        return list(self._examples.values())

    def get_example(self, name: str) -> Optional[ExampleProject]:
        """Get a specific example."""
        return self._examples.get(name)

    def get_by_type(self, example_type: ExampleType) -> List[ExampleProject]:
        """Get examples by type."""
        return [e for e in self._examples.values() if e.example_type == example_type]

    def generate_structure(self, example_name: str, output_path: str) -> bool:
        """Generate example project structure.

        Args:
            example_name: Name of example to generate
            output_path: Output directory path

        Returns:
            True if successful
        """
        example = self._examples.get(example_name)
        if not example:
            return False

        output = Path(output_path)
        output.mkdir(parents=True, exist_ok=True)

        for service in example.services:
            service_dir = output / "services" / service
            service_dir.mkdir(parents=True, exist_ok=True)
            (service_dir / "__init__.py").touch()

        (output / "tests").mkdir(exist_ok=True)
        (output / "e2e.conf").write_text(f"""# {example.name} Configuration
[default]
base_url = http://localhost:8080

[services]
""")

        return True


class TemplateLoader:
    """Load and manage project templates."""

    def __init__(self):
        """Initialize template loader."""
        self.templates: Dict[str, Dict[str, Any]] = {}

    def register_template(self, name: str, template: Dict[str, Any]):
        """Register a custom template.

        Args:
            name: Template name
            template: Template content
        """
        self.templates[name] = template

    def get_template(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a template by name."""
        return self.templates.get(name)

    def list_templates(self) -> List[str]:
        """List all available templates."""
        return list(self.templates.keys())


class BestPracticesGuide:
    """Generate best practices guides."""

    @staticmethod
    def generate_test_organization_guide() -> str:
        """Generate test organization best practices."""
        return """# Test Organization Best Practices

## Directory Structure
```
tests/
├── unit/           # Unit tests
├── integration/    # Integration tests
├── e2e/           # End-to-end tests
└── fixtures/      # Test fixtures
```

## Naming Conventions
- Use descriptive names: `test_user_can_login`
- Group related tests: `TestUserAuthentication`
- Use prefixes: `test_`, `Test`

## Test Isolation
- Each test should be independent
- Use fixtures for setup/teardown
- Clean up data after tests
"""

    @staticmethod
    def generate_assertion_guide() -> str:
        """Generate assertion best practices."""
        return """# Assertion Best Practices

## Use Descriptive Assertions
```python
# Bad
assert response.status_code == 200

# Good
assert response.status_code == 200, f"Expected 200, got {response.status_code}"
```

## Verify Important Data
- Check status codes
- Validate response structure
- Verify critical data fields
- Check error handling

## Avoid Hard-coded Values
- Use constants
- Generate test data dynamically
"""

    @staticmethod
    def generate_naming_guide() -> str:
        """Generate naming conventions guide."""
        return """# Naming Conventions

## Test Functions
- Use snake_case: `test_user_login_success`
- Start with `test_`: `test_create_user`
- Describe behavior: `test_returns_401_for_invalid_credentials`

## Test Classes
- Use PascalCase: `TestUserAuthentication`
- Group related tests: `TestPaymentFlow`

## Files
- snake_case: `test_auth_flow.py`
- Group by feature: `auth_tests/`
"""
