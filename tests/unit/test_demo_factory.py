"""Tests for demo_factory module."""

import pytest
import tempfile
from pathlib import Path

from socialseed_e2e.demo_factory import (
    DemoFactory,
    DemoConfig,
    GenericDemoFactory,
    create_demo_factory,
)


class TestDemoConfig:
    """Tests for DemoConfig dataclass."""

    def test_default_config(self):
        """Test default config values."""
        config = DemoConfig(
            name="test", port=5000, title="Test API", description="Test API"
        )
        assert config.name == "test"
        assert config.port == 5000
        assert config.title == "Test API"
        assert config.entities == []
        assert config.features == []

    def test_config_with_entities(self):
        """Test config with entities."""
        config = DemoConfig(
            name="blog",
            port=5001,
            title="Blog API",
            description="A blog API",
            entities=["post", "comment"],
            features=["CRUD", "Search"],
        )
        assert config.entities == ["post", "comment"]
        assert config.features == ["CRUD", "Search"]


class TestGenericDemoFactory:
    """Tests for GenericDemoFactory."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_factory_creation(self, temp_dir):
        """Test factory is created correctly."""
        factory = GenericDemoFactory(temp_dir, "testapi", 5000)
        assert factory.demo_name == "testapi"
        assert factory.port == 5000
        assert factory.service_name == "testapi-demo"

    def test_get_config(self, temp_dir):
        """Test config generation."""
        factory = GenericDemoFactory(temp_dir, "myapi", 5001)
        config = factory.get_config()
        assert config.name == "myapi"
        assert config.port == 5001
        assert config.title == "Myapi Demo API"

    def test_template_vars(self, temp_dir):
        """Test template variables are generated."""
        factory = GenericDemoFactory(temp_dir, "blog", 5002)
        config = factory.get_config()
        vars = factory._get_template_vars(config)

        assert vars["demo_name"] == "blog"
        assert vars["port"] == 5002
        assert vars["service_name"] == "blog-demo"

    def test_create_all(self, temp_dir):
        """Test creating all demo components."""
        factory = GenericDemoFactory(temp_dir, "testapi", 5003)
        results = factory.create_all()

        # Check results structure
        assert "api" in results
        assert "service_page" in results
        assert "data_schema" in results
        assert "config" in results
        assert "tests" in results

    def test_service_directory_created(self, temp_dir):
        """Test service directory is created."""
        factory = GenericDemoFactory(temp_dir, "testapi", 5004)
        factory.create_all()

        service_path = temp_dir / "services" / "testapi-demo"
        assert service_path.exists()
        assert (service_path / "modules").exists()

    def test_demo_directory_created(self, temp_dir):
        """Test demo directory is created."""
        factory = GenericDemoFactory(temp_dir, "testapi", 5005)
        factory.create_all()

        demo_path = temp_dir / "demos" / "testapi"
        assert demo_path.exists()


class TestCreateDemoFactory:
    """Tests for create_demo_factory function."""

    def test_create_generic_factory(self, temp_dir=None):
        """Test generic factory creation."""
        if temp_dir is None:
            with tempfile.TemporaryDirectory() as tmpdir:
                temp_dir = Path(tmpdir)

        factory = create_demo_factory("testapi", 5006, temp_dir)
        assert isinstance(factory, GenericDemoFactory)
        assert factory.demo_name == "testapi"
        assert factory.port == 5006
