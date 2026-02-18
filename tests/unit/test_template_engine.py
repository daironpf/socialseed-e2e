"""Tests for TemplateEngine.

This module contains unit tests for the TemplateEngine class and
helper functions.
"""

import tempfile
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

from socialseed_e2e.utils.template_engine import (
    TemplateEngine,
    to_camel_case,
    to_class_name,
    to_snake_case,
)


class TestTemplateEngine:
    """Test cases for TemplateEngine class."""

    def test_init_default_template_dir(self):
        """Test that TemplateEngine initializes with default template directory."""
        engine = TemplateEngine()
        assert engine.template_dir.exists()
        assert (engine.template_dir / "e2e.conf.template").exists()

    def test_init_custom_template_dir(self):
        """Test that TemplateEngine initializes with custom template directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = TemplateEngine(tmpdir)
            assert engine.template_dir == Path(tmpdir)

    def test_list_templates(self):
        """Test listing available templates."""
        engine = TemplateEngine()
        templates = engine.list_templates()

        # Should find all template files
        assert "e2e.conf.template" in templates
        assert "service_page.py.template" in templates
        assert "test_module.py.template" in templates
        assert "data_schema.py.template" in templates
        assert "config.py.template" in templates

    def test_load_template_success(self):
        """Test loading an existing template."""
        engine = TemplateEngine()
        template = engine.load_template("e2e.conf")

        assert template is not None
        assert "${environment}" in template.template

    def test_load_template_not_found(self):
        """Test loading a non-existent template raises FileNotFoundError."""
        engine = TemplateEngine()

        with pytest.raises(FileNotFoundError) as exc_info:
            engine.load_template("nonexistent")

        assert "Template not found" in str(exc_info.value)

    def test_render_with_variables(self):
        """Test rendering a template with variables."""
        engine = TemplateEngine()

        result = engine.render(
            "e2e.conf",
            {
                "environment": "test",
                "timeout": "5000",
                "user_agent": "test-agent",
                "verbose": "false",
                "services_config": "# no services",
            },
        )

        assert "environment: test" in result
        assert "timeout: 5000" in result
        assert "test-agent" in result
        assert "verbose: false" in result

    def test_render_missing_variables_uses_placeholder(self):
        """Test that missing variables are left as placeholders."""
        engine = TemplateEngine()

        result = engine.render(
            "e2e.conf",
            {
                "environment": "test"
                # Other variables missing
            },
        )

        # Missing variables should remain as ${variable}
        assert "environment: test" in result
        assert "${timeout}" in result  # Should remain as placeholder

    def test_render_to_file_success(self):
        """Test rendering and writing to file."""
        engine = TemplateEngine()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.conf"

            result_path = engine.render_to_file(
                "e2e.conf",
                {
                    "environment": "dev",
                    "timeout": "30000",
                    "user_agent": "agent",
                    "verbose": "true",
                    "services_config": "",
                },
                output_path,
            )

            assert result_path.exists()
            content = result_path.read_text()
            assert "environment: dev" in content

    def test_render_to_file_overwrite(self):
        """Test overwrite behavior in render_to_file."""
        engine = TemplateEngine()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.conf"
            output_path.write_text("original content")

            # Should raise FileExistsError without overwrite=True
            with pytest.raises(FileExistsError):
                engine.render_to_file(
                    "e2e.conf",
                    {
                        "environment": "dev",
                        "timeout": "30000",
                        "user_agent": "agent",
                        "verbose": "true",
                        "services_config": "",
                    },
                    output_path,
                )

            # Should succeed with overwrite=True
            engine.render_to_file(
                "e2e.conf",
                {
                    "environment": "prod",
                    "timeout": "10000",
                    "user_agent": "agent2",
                    "verbose": "false",
                    "services_config": "",
                },
                output_path,
                overwrite=True,
            )

            content = output_path.read_text()
            assert "environment: prod" in content

    def test_get_template_variables(self):
        """Test extracting variable names from template."""
        engine = TemplateEngine()

        variables = engine.get_template_variables("e2e.conf")

        assert "environment" in variables
        assert "timeout" in variables
        assert "user_agent" in variables
        assert "verbose" in variables
        assert "services_config" in variables

    def test_validate_variables(self):
        """Test variable validation."""
        engine = TemplateEngine()

        missing, extra = engine.validate_variables(
            "e2e.conf", {"environment": "test", "timeout": "5000", "extra_var": "value"}
        )

        # Should report missing variables
        assert "user_agent" in missing
        assert "verbose" in missing
        assert "services_config" in missing

        # Should report extra variables
        assert "extra_var" in extra


class TestHelperFunctions:
    """Test cases for helper functions."""

    def test_to_class_name_with_hyphens(self):
        """Test converting hyphenated names to class names."""
        assert to_class_name("users-api") == "UsersApi"
        assert to_class_name("my-service") == "MyService"

    def test_to_class_name_with_underscores(self):
        """Test converting snake_case names to class names."""
        assert to_class_name("users_api") == "UsersApi"
        assert to_class_name("my_service") == "MyService"

    def test_to_class_name_mixed(self):
        """Test converting mixed names to class names."""
        assert to_class_name("my-api_service") == "MyApiService"

    def test_to_snake_case_with_hyphens(self):
        """Test converting hyphenated names to snake_case."""
        assert to_snake_case("users-api") == "users_api"
        assert to_snake_case("My-Service") == "my_service"

    def test_to_snake_case_already_snake(self):
        """Test converting already snake_case names."""
        assert to_snake_case("users_api") == "users_api"

    def test_to_camel_case_with_hyphens(self):
        """Test converting hyphenated names to camelCase."""
        assert to_camel_case("users-api") == "usersApi"
        assert to_camel_case("my-service") == "myService"

    def test_to_camel_case_with_underscores(self):
        """Test converting snake_case names to camelCase."""
        assert to_camel_case("users_api") == "usersApi"
        assert to_camel_case("my_service") == "myService"


class TestServicePageTemplate:
    """Test cases for service_page.py.template."""

    def test_service_page_template_rendering(self):
        """Test rendering service_page.py.template with variables."""
        engine = TemplateEngine()

        result = engine.render(
            "service_page.py",
            {
                "service_name": "users-api",
                "class_name": "UsersApi",
                "snake_case_name": "users_api",
                "endpoint_prefix": "users",
            },
        )

        assert "class UsersApiPage(BasePage):" in result
        assert "users-api" in result
        assert "ENDPOINTS" in result
        assert "access_token" in result


class TestTestModuleTemplate:
    """Test cases for test_module.py.template."""

    def test_test_module_template_rendering(self):
        """Test rendering test_module.py.template with variables."""
        engine = TemplateEngine()

        result = engine.render(
            "test_module.py",
            {
                "service_name": "users-api",
                "class_name": "UsersApi",
                "snake_case_name": "users_api",
                "test_name": "login",
                "test_description": "User login flow",
            },
        )

        assert "def run(users_api" in result
        assert "UsersApiPage" in result
        assert "login" in result
        assert "User login flow" in result


class TestDataSchemaTemplate:
    """Test cases for data_schema.py.template."""

    def test_data_schema_template_rendering(self):
        """Test rendering data_schema.py.template with variables."""
        engine = TemplateEngine()

        result = engine.render(
            "data_schema.py",
            {
                "service_name": "users-api",
                "class_name": "UsersApi",
                "constants": "# Custom constants here",
            },
        )

        assert "class UsersApiDTO(BaseModel):" in result
        assert "UsersApiCreateDTO" in result
        assert "UsersApiUpdateDTO" in result
        assert "TEST_ENTITY" in result


class TestConfigTemplate:
    """Test cases for config.py.template."""

    def test_config_template_rendering(self):
        """Test rendering config.py.template with variables."""
        engine = TemplateEngine()

        result = engine.render(
            "config.py", {"service_name": "users-api", "snake_case_name": "users_api"}
        )

        assert "get_users_api_config" in result
        assert 'config.services["users-api"]' in result
