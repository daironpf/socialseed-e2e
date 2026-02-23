"""Test Template Marketplace.

This module provides functionality for managing and sharing test templates.
"""

import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from socialseed_e2e.community import (
    CommunityHub,
    ResourceType,
    TestTemplate,
)


@dataclass
class TemplateCategory:
    """Category for test templates."""

    name: str
    description: str
    icon: str = "📄"
    templates: List[str] = field(default_factory=list)


class TestTemplateMarketplace:
    """Marketplace for test templates."""

    # Predefined categories
    CATEGORIES = {
        "authentication": TemplateCategory(
            name="Authentication & Authorization",
            description="Login, logout, token management, permission tests",
            icon="🔐",
        ),
        "crud": TemplateCategory(
            name="CRUD Operations",
            description="Create, Read, Update, Delete test patterns",
            icon="📝",
        ),
        "api_testing": TemplateCategory(
            name="API Testing",
            description="REST API, GraphQL, gRPC test templates",
            icon="🌐",
        ),
        "database": TemplateCategory(
            name="Database Testing",
            description="SQL and NoSQL database tests",
            icon="🗄️",
        ),
        "security": TemplateCategory(
            name="Security Testing",
            description="Security fuzzing, vulnerability tests",
            icon="🔒",
        ),
        "performance": TemplateCategory(
            name="Performance Testing",
            description="Load tests, stress tests, benchmarks",
            icon="⚡",
        ),
        "integration": TemplateCategory(
            name="Integration Testing",
            description="Service integration, workflow tests",
            icon="🔗",
        ),
        "e2e_flows": TemplateCategory(
            name="End-to-End Flows",
            description="Complete user journey tests",
            icon="🎯",
        ),
    }

    def __init__(self, community_hub: Optional[CommunityHub] = None):
        """Initialize the template marketplace.

        Args:
            community_hub: Community hub instance
        """
        self.hub = community_hub or CommunityHub()
        self.templates_dir = self.hub.storage_path / "templates"
        self.templates_dir.mkdir(exist_ok=True)

    def create_template(
        self,
        name: str,
        description: str,
        author: str,
        category: str,
        framework: str,
        template_code: str,
        tags: Optional[List[str]] = None,
        example_usage: str = "",
    ) -> TestTemplate:
        """Create a new test template.

        Args:
            name: Template name
            description: Template description
            author: Author name
            category: Template category
            framework: Target framework (fastapi, flask, etc.)
            template_code: The template code
            tags: List of tags
            example_usage: Example usage code

        Returns:
            Created template
        """
        import uuid

        template_id = str(uuid.uuid4())

        # Save template code to file
        template_file = self.templates_dir / f"{template_id}.py"
        template_file.write_text(template_code)

        # Create template resource
        template = TestTemplate(
            id=template_id,
            name=name,
            description=description,
            author=author,
            version="1.0.0",
            tags=tags or [],
            file_path=template_file,
            framework=framework,
            example_usage=example_usage,
            metadata={"category": category},
        )

        return template

    def publish_template(self, template: TestTemplate) -> bool:
        """Publish a template to the marketplace.

        Args:
            template: Template to publish

        Returns:
            True if published successfully
        """
        return self.hub.publish_resource(template)

    def get_templates_by_category(self, category: str) -> List[TestTemplate]:
        """Get templates by category.

        Args:
            category: Category name

        Returns:
            List of templates
        """
        all_templates = self.hub.search_resources(
            resource_type=ResourceType.TEST_TEMPLATE
        )
        return [t for t in all_templates if t.metadata.get("category") == category]

    def search_templates(
        self,
        query: Optional[str] = None,
        framework: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> List[TestTemplate]:
        """Search for templates.

        Args:
            query: Search query
            framework: Filter by framework
            tags: Filter by tags

        Returns:
            List of matching templates
        """
        results = self.hub.search_resources(
            resource_type=ResourceType.TEST_TEMPLATE,
            tags=tags,
            query=query,
        )

        if framework:
            results = [t for t in results if t.framework.lower() == framework.lower()]

        return results

    def download_template(self, template_id: str, destination: Path) -> bool:
        """Download a template to a destination.

        Args:
            template_id: Template ID
            destination: Destination path

        Returns:
            True if downloaded successfully
        """
        template = self.hub.get_resource(template_id)
        if not template or not template.file_path:
            return False

        # Copy template file
        if template.file_path.exists():
            shutil.copy2(template.file_path, destination)
            self.hub.download_resource(template_id)
            return True

        return False

    def install_template(
        self, template_id: str, service_name: str, test_name: Optional[str] = None
    ) -> Optional[Path]:
        """Install a template into a service.

        Args:
            template_id: Template ID
            service_name: Target service name
            test_name: Custom test name

        Returns:
            Path to installed file or None
        """
        template = self.hub.get_resource(template_id)
        if not template:
            return None

        # Determine destination
        test_name = test_name or template.name.lower().replace(" ", "_")
        destination = Path("services") / service_name / "modules" / f"{test_name}.py"

        # Ensure directory exists
        destination.parent.mkdir(parents=True, exist_ok=True)

        # Download and install
        if self.download_template(template_id, destination):
            return destination

        return None

    def get_categories(self) -> Dict[str, TemplateCategory]:
        """Get all template categories with counts.

        Returns:
            Dictionary of categories
        """
        categories = dict(self.CATEGORIES)

        for template in self.hub.search_resources(
            resource_type=ResourceType.TEST_TEMPLATE
        ):
            category = template.metadata.get("category")
            if category and category in categories:
                categories[category].templates.append(template.id)

        return categories

    def get_featured_templates(self, limit: int = 5) -> List[TestTemplate]:
        """Get featured/popular templates.

        Args:
            limit: Maximum number to return

        Returns:
            List of featured templates
        """
        return self.hub.get_popular_resources(limit)

    def generate_template_from_service(
        self,
        service_name: str,
        author: str,
        template_name: Optional[str] = None,
    ) -> Optional[TestTemplate]:
        """Generate a template from an existing service.

        Args:
            service_name: Service to generate from
            author: Author name
            template_name: Custom template name

        Returns:
            Generated template or None
        """
        service_path = Path("services") / service_name
        if not service_path.exists():
            return None

        # Collect test files
        test_files = list((service_path / "modules").glob("*.py"))
        if not test_files:
            return None

        # Create template code
        template_code = self._generate_template_code(test_files, service_name)

        # Create template
        template_name = template_name or f"{service_name}_template"
        template = self.create_template(
            name=template_name,
            description=f"Test template generated from {service_name} service",
            author=author,
            category="e2e_flows",
            framework="generic",
            template_code=template_code,
            tags=[service_name, "generated", "template"],
        )

        return template

    def _generate_template_code(self, test_files: List[Path], service_name: str) -> str:
        """Generate template code from test files.

        Args:
            test_files: List of test files
            service_name: Service name

        Returns:
            Generated template code
        """
        code_parts = [
            f'"""Test template for {service_name} service.',
            "",
            "This template was automatically generated from existing tests.",
            '"""',
            "",
            "from socialseed_e2e.core.base_page import BasePage",
            "",
            "",
            f"class {service_name.title()}TestTemplate(BasePage):",
            '    """Test template for {service_name} service."""',
            "",
            "    def __init__(self):",
            '        super().__init__(base_url="http://localhost:8000")',
            "",
        ]

        # Add example methods
        code_parts.extend(
            [
                "    async def test_example_endpoint(self):",
                '        """Test example endpoint."""',
                '        response = await self.get("/api/example")',
                "        assert response.status == 200",
                "",
                "    async def test_create_resource(self):",
                '        """Test creating a resource."""',
                '        data = {"name": "test"}',
                '        response = await self.post("/api/resources", json=data)',
                "        assert response.status == 201",
                "",
            ]
        )

        return "\n".join(code_parts)

    def get_template_preview(self, template_id: str) -> Optional[str]:
        """Get a preview of template code.

        Args:
            template_id: Template ID

        Returns:
            Code preview or None
        """
        template = self.hub.get_resource(template_id)
        if not template or not template.file_path:
            return None

        try:
            code = template.file_path.read_text()
            # Return first 50 lines as preview
            lines = code.split("\n")[:50]
            return "\n".join(lines)
        except Exception:
            return None
