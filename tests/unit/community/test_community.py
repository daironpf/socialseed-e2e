"""Tests for Community Hub and Test Marketplace (Issue #129)."""

import tempfile
from pathlib import Path

import pytest

from socialseed_e2e.community import (
    CommunityHub,
    CommunityResource,
    PluginResource,
    ResourceStatus,
    ResourceType,
    TestTemplate,
)
from socialseed_e2e.community.plugin_repository import (
    PluginManifest,
    PluginRepository,
)
from socialseed_e2e.community.template_marketplace import TestTemplateMarketplace


class TestCommunityHub:
    """Tests for CommunityHub."""

    @pytest.fixture
    def temp_storage(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def hub(self, temp_storage):
        return CommunityHub(temp_storage)

    def test_initialization(self, temp_storage, hub):
        """Test hub initialization."""
        assert hub.storage_path == temp_storage
        assert isinstance(hub.resources, dict)

    def test_publish_resource(self, hub):
        """Test publishing a resource."""
        resource = CommunityResource(
            id="test-123",
            name="Test Resource",
            description="A test resource",
            resource_type=ResourceType.BEST_PRACTICE,
            author="Test Author",
            version="1.0.0",
        )

        result = hub.publish_resource(resource)

        assert result is True
        assert "test-123" in hub.resources

    def test_publish_duplicate_resource(self, hub):
        """Test publishing duplicate resource fails."""
        resource = CommunityResource(
            id="test-123",
            name="Test Resource",
            description="A test resource",
            resource_type=ResourceType.BEST_PRACTICE,
            author="Test Author",
            version="1.0.0",
        )

        hub.publish_resource(resource)
        result = hub.publish_resource(resource)

        assert result is False

    def test_get_resource(self, hub):
        """Test getting a resource by ID."""
        resource = CommunityResource(
            id="test-456",
            name="Another Resource",
            description="Another test resource",
            resource_type=ResourceType.BEST_PRACTICE,
            author="Test Author",
            version="1.0.0",
        )

        hub.publish_resource(resource)
        retrieved = hub.get_resource("test-456")

        assert retrieved is not None
        assert retrieved.name == "Another Resource"

    def test_get_nonexistent_resource(self, hub):
        """Test getting nonexistent resource returns None."""
        result = hub.get_resource("nonexistent-id")
        assert result is None

    def test_search_resources_by_type(self, hub):
        """Test searching by resource type."""
        # Add test template
        template = TestTemplate(
            id="template-1",
            name="Auth Template",
            description="Auth test template",
            author="Author",
            version="1.0.0",
            framework="fastapi",
            status=ResourceStatus.APPROVED,
        )
        hub.publish_resource(template)

        # Add best practice
        practice = CommunityResource(
            id="practice-1",
            name="Best Practice",
            description="A best practice",
            resource_type=ResourceType.BEST_PRACTICE,
            author="Author",
            version="1.0.0",
            status=ResourceStatus.APPROVED,
        )
        hub.publish_resource(practice)

        # Search for templates
        results = hub.search_resources(resource_type=ResourceType.TEST_TEMPLATE)

        assert len(results) == 1
        assert results[0].id == "template-1"

    def test_search_resources_by_query(self, hub):
        """Test searching by query string."""
        resource1 = CommunityResource(
            id="res-1",
            name="Authentication Guide",
            description="Guide for auth",
            resource_type=ResourceType.BEST_PRACTICE,
            author="Author",
            version="1.0.0",
            status=ResourceStatus.APPROVED,
        )
        resource2 = CommunityResource(
            id="res-2",
            name="Payment Flow",
            description="Payment processing",
            resource_type=ResourceType.BEST_PRACTICE,
            author="Author",
            version="1.0.0",
            status=ResourceStatus.APPROVED,
        )

        hub.publish_resource(resource1)
        hub.publish_resource(resource2)

        results = hub.search_resources(query="auth")

        assert len(results) == 1
        assert results[0].id == "res-1"

    def test_update_resource(self, hub):
        """Test updating a resource."""
        resource = CommunityResource(
            id="update-test",
            name="Original Name",
            description="Original description",
            resource_type=ResourceType.BEST_PRACTICE,
            author="Author",
            version="1.0.0",
        )

        hub.publish_resource(resource)

        # Update
        result = hub.update_resource("update-test", {"name": "Updated Name"})

        assert result is True
        assert hub.resources["update-test"].name == "Updated Name"

    def test_rate_resource(self, hub):
        """Test rating a resource."""
        resource = CommunityResource(
            id="rate-test",
            name="Rateable Resource",
            description="Test rating",
            resource_type=ResourceType.BEST_PRACTICE,
            author="Author",
            version="1.0.0",
        )

        hub.publish_resource(resource)

        # Rate
        result = hub.rate_resource("rate-test", 4.5)

        assert result is True
        assert hub.resources["rate-test"].rating == 4.5
        assert hub.resources["rate-test"].rating_count == 1

        # Rate again
        hub.rate_resource("rate-test", 5.0)

        # Check average
        assert hub.resources["rate-test"].rating == 4.75  # (4.5 + 5.0) / 2
        assert hub.resources["rate-test"].rating_count == 2

    def test_get_popular_resources(self, hub):
        """Test getting popular resources."""
        # Add resources with different download counts
        for i in range(5):
            resource = CommunityResource(
                id=f"pop-{i}",
                name=f"Resource {i}",
                description=f"Resource {i}",
                resource_type=ResourceType.BEST_PRACTICE,
                author="Author",
                version="1.0.0",
                downloads=i * 10,
                status=ResourceStatus.APPROVED,
            )
            hub.publish_resource(resource)

        popular = hub.get_popular_resources(3)

        assert len(popular) == 3
        # Should be sorted by downloads descending
        assert popular[0].downloads >= popular[1].downloads

    def test_get_statistics(self, hub):
        """Test getting marketplace statistics."""
        # Add various resources
        template = TestTemplate(
            id="stat-template",
            name="Stat Template",
            description="Template",
            author="Author",
            version="1.0.0",
            framework="fastapi",
            status=ResourceStatus.APPROVED,
        )
        hub.publish_resource(template)

        practice = CommunityResource(
            id="stat-practice",
            name="Stat Practice",
            description="Practice",
            resource_type=ResourceType.BEST_PRACTICE,
            author="Author",
            version="1.0.0",
            status=ResourceStatus.APPROVED,
        )
        hub.publish_resource(practice)

        stats = hub.get_statistics()

        assert stats["total_resources"] == 2
        assert stats["by_type"]["test_template"] == 1
        assert stats["by_type"]["best_practice"] == 1


class TestTestTemplateMarketplace:
    """Tests for TestTemplateMarketplace."""

    @pytest.fixture
    def temp_storage(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def marketplace(self, temp_storage):
        hub = CommunityHub(temp_storage)
        return TestTemplateMarketplace(hub)

    def test_create_template(self, marketplace):
        """Test creating a template."""
        template = marketplace.create_template(
            name="Auth Tests",
            description="Authentication test suite",
            author="Test Author",
            category="authentication",
            framework="fastapi",
            template_code="# Test code here",
            tags=["auth", "security"],
        )

        assert isinstance(template, TestTemplate)
        assert template.name == "Auth Tests"
        assert template.framework == "fastapi"
        assert template.metadata["category"] == "authentication"
        assert template.file_path.exists()

    def test_publish_template(self, marketplace):
        """Test publishing a template."""
        template = marketplace.create_template(
            name="Test Template",
            description="Test",
            author="Author",
            category="crud",
            framework="flask",
            template_code="# Code",
        )

        result = marketplace.publish_template(template)

        assert result is True

    def test_get_templates_by_category(self, marketplace):
        """Test getting templates by category."""
        from socialseed_e2e.community import ResourceStatus

        # Create templates in different categories
        for category in ["authentication", "authentication", "crud"]:
            template = marketplace.create_template(
                name=f"{category} Template",
                description=f"{category} tests",
                author="Author",
                category=category,
                framework="fastapi",
                template_code="# Code",
            )
            template.status = ResourceStatus.APPROVED
            marketplace.publish_template(template)

        auth_templates = marketplace.get_templates_by_category("authentication")

        assert len(auth_templates) == 2

    def test_search_templates(self, marketplace):
        """Test searching templates."""
        from socialseed_e2e.community import ResourceStatus

        # Create templates
        for name, framework in [("FastAPI Auth", "fastapi"), ("Flask CRUD", "flask")]:
            template = marketplace.create_template(
                name=name,
                description=f"{name} tests",
                author="Author",
                category="general",
                framework=framework,
                template_code="# Code",
            )
            template.status = ResourceStatus.APPROVED
            marketplace.publish_template(template)

        # Search by framework
        results = marketplace.search_templates(framework="fastapi")

        assert len(results) == 1
        assert results[0].name == "FastAPI Auth"

    def test_get_categories(self, marketplace):
        """Test getting template categories."""
        categories = marketplace.get_categories()

        assert "authentication" in categories
        assert "crud" in categories
        assert categories["authentication"].icon == "🔐"


class TestPluginRepository:
    """Tests for PluginRepository."""

    @pytest.fixture
    def temp_storage(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def repo(self, temp_storage):
        hub = CommunityHub(temp_storage)
        return PluginRepository(hub)

    def test_create_plugin_package(self, repo, temp_storage):
        """Test creating a plugin package."""
        manifest = PluginManifest(
            name="test-plugin",
            version="1.0.0",
            description="A test plugin",
            author="Test Author",
            entry_point="test_plugin.main",
            hooks=["before_test"],
        )

        package_path = repo.create_plugin_package(
            manifest=manifest,
            plugin_code="# Plugin code",
        )

        assert package_path.exists()
        assert package_path.suffix == ".zip"

    def test_validate_valid_plugin(self, repo, temp_storage):
        """Test validating a valid plugin package."""
        manifest = PluginManifest(
            name="valid-plugin",
            version="1.0.0",
            description="Valid plugin",
            author="Author",
            entry_point="valid_plugin.main",
        )

        package_path = repo.create_plugin_package(
            manifest=manifest,
            plugin_code="# Valid code",
        )

        is_valid, errors = repo.validate_plugin(package_path)

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_invalid_plugin(self, repo, temp_storage):
        """Test validating an invalid plugin package."""
        # Create invalid package (no manifest)
        invalid_package = temp_storage / "invalid.zip"
        import zipfile

        with zipfile.ZipFile(invalid_package, "w") as zf:
            zf.writestr("some_file.txt", "content")

        is_valid, errors = repo.validate_plugin(invalid_package)

        assert is_valid is False
        assert len(errors) > 0

    def test_list_installed_plugins_empty(self, repo):
        """Test listing plugins when none installed."""
        plugins = repo.list_installed_plugins()

        assert isinstance(plugins, list)

    def test_plugin_manifest_to_dict(self):
        """Test converting manifest to dictionary."""
        manifest = PluginManifest(
            name="test-plugin",
            version="1.0.0",
            description="Test",
            author="Author",
            entry_point="test.main",
            hooks=["hook1", "hook2"],
        )

        data = manifest.to_dict()

        assert data["name"] == "test-plugin"
        assert data["hooks"] == ["hook1", "hook2"]

    def test_plugin_manifest_from_dict(self):
        """Test creating manifest from dictionary."""
        data = {
            "name": "from-dict",
            "version": "2.0.0",
            "description": "From dict",
            "author": "Author",
            "entry_point": "main.entry",
            "hooks": ["hook1"],
            "dependencies": ["dep1"],
        }

        manifest = PluginManifest.from_dict(data)

        assert manifest.name == "from-dict"
        assert manifest.version == "2.0.0"
        assert manifest.hooks == ["hook1"]


class TestResourceTypes:
    """Tests for resource type enums."""

    def test_resource_type_values(self):
        """Test resource type enum values."""
        assert ResourceType.TEST_TEMPLATE.value == "test_template"
        assert ResourceType.PLUGIN.value == "plugin"
        assert ResourceType.BEST_PRACTICE.value == "best_practice"

    def test_resource_status_values(self):
        """Test resource status enum values."""
        assert ResourceStatus.DRAFT.value == "draft"
        assert ResourceStatus.APPROVED.value == "approved"
        assert ResourceStatus.REJECTED.value == "rejected"


class TestCommunityResource:
    """Tests for CommunityResource dataclass."""

    def test_resource_to_dict(self):
        """Test converting resource to dictionary."""
        resource = CommunityResource(
            id="test-id",
            name="Test Resource",
            description="Test",
            resource_type=ResourceType.BEST_PRACTICE,
            author="Author",
            version="1.0.0",
            downloads=10,
            rating=4.5,
        )

        data = resource.to_dict()

        assert data["id"] == "test-id"
        assert data["name"] == "Test Resource"
        assert data["downloads"] == 10
        assert data["rating"] == 4.5
        assert data["resource_type"] == "best_practice"

    def test_resource_from_dict(self):
        """Test creating resource from dictionary."""
        data = {
            "id": "from-dict",
            "name": "From Dict",
            "description": "Test",
            "resource_type": "test_template",
            "author": "Author",
            "version": "1.0.0",
            "downloads": 5,
            "rating": 3.5,
            "rating_count": 2,
            "status": "approved",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
            "file_path": None,
            "dependencies": [],
            "metadata": {},
        }

        resource = CommunityResource.from_dict(data)

        assert resource.id == "from-dict"
        assert resource.resource_type == ResourceType.TEST_TEMPLATE
        assert resource.status == ResourceStatus.APPROVED
