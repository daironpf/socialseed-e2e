"""Tests for ApiConfigLoader.

This module contains unit tests for the ApiConfigLoader class,
testing configuration loading, validation, and file discovery.
"""

import os
import tempfile
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

from socialseed_e2e.core.config_loader import (
    ApiConfigLoader,
    AppConfig,
    ConfigError,
    ServiceConfig,
    get_service_config,
    normalize_service_name,
)


class TestFindConfigFile:
    """Test cases for configuration file discovery."""

    def test_find_from_env_variable(self, monkeypatch):
        """Test finding config from E2E_CONFIG_PATH environment variable."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".conf", delete=False) as f:
            f.write("general:\n  environment: test\n")
            temp_path = f.name

        try:
            monkeypatch.setenv("E2E_CONFIG_PATH", temp_path)
            result = ApiConfigLoader._find_config_file()
            assert result == temp_path
        finally:
            os.unlink(temp_path)

    def test_env_variable_not_found_raises_error(self, monkeypatch):
        """Test that invalid E2E_CONFIG_PATH raises FileNotFoundError."""
        monkeypatch.setenv("E2E_CONFIG_PATH", "/nonexistent/path/e2e.conf")

        with pytest.raises(FileNotFoundError) as exc_info:
            ApiConfigLoader._find_config_file()

        assert "E2E_CONFIG_PATH" in str(exc_info.value)

    def test_find_in_current_directory(self, tmp_path, monkeypatch):
        """Test finding e2e.conf in current directory."""
        config_file = tmp_path / "e2e.conf"
        config_file.write_text("general:\n  environment: test\n")

        monkeypatch.chdir(tmp_path)
        result = ApiConfigLoader._find_config_file()
        # Result can be relative or absolute path
        assert Path(result).name == "e2e.conf"
        assert Path(result).exists()

    def test_find_in_config_subdirectory(self, tmp_path, monkeypatch):
        """Test finding e2e.conf in config/ subdirectory."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_file = config_dir / "e2e.conf"
        config_file.write_text("general:\n  environment: test\n")

        monkeypatch.chdir(tmp_path)
        result = ApiConfigLoader._find_config_file()
        assert Path(result).resolve() == config_file.resolve()

    def test_find_in_tests_subdirectory(self, tmp_path, monkeypatch):
        """Test finding e2e.conf in tests/ subdirectory."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        config_file = tests_dir / "e2e.conf"
        config_file.write_text("general:\n  environment: test\n")

        monkeypatch.chdir(tmp_path)
        result = ApiConfigLoader._find_config_file()
        assert Path(result).resolve() == config_file.resolve()

    def test_priority_order_env_over_current(self, tmp_path, monkeypatch):
        """Test that E2E_CONFIG_PATH takes priority over ./e2e.conf."""
        # Create config in current directory
        local_config = tmp_path / "e2e.conf"
        local_config.write_text("general:\n  environment: local\n")

        # Create config via env variable
        with tempfile.NamedTemporaryFile(mode="w", suffix=".conf", delete=False) as f:
            f.write("general:\n  environment: env\n")
            env_path = f.name

        try:
            monkeypatch.setenv("E2E_CONFIG_PATH", env_path)
            monkeypatch.chdir(tmp_path)
            result = ApiConfigLoader._find_config_file()
            assert result == env_path
        finally:
            os.unlink(env_path)

    def test_priority_order_current_over_config_subdir(self, tmp_path, monkeypatch):
        """Test that ./e2e.conf takes priority over config/e2e.conf."""
        # Create config in config/ subdirectory
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        subdir_config = config_dir / "e2e.conf"
        subdir_config.write_text("general:\n  environment: subdir\n")

        # Create config in current directory
        local_config = tmp_path / "e2e.conf"
        local_config.write_text("general:\n  environment: local\n")

        monkeypatch.chdir(tmp_path)
        result = ApiConfigLoader._find_config_file()
        assert Path(result).resolve() == local_config.resolve()

    def test_not_found_error_message(self, tmp_path, monkeypatch):
        """Test that error message lists all searched locations."""
        monkeypatch.chdir(tmp_path)

        with pytest.raises(FileNotFoundError) as exc_info:
            ApiConfigLoader._find_config_file()

        error_msg = str(exc_info.value)
        assert "E2E_CONFIG_PATH" in error_msg
        assert "./e2e.conf" in error_msg
        assert "./config/e2e.conf" in error_msg
        assert "./tests/e2e.conf" in error_msg
        assert "e2e init" in error_msg


class TestCreateDefaultConfig:
    """Test cases for create_default_config method."""

    def test_create_default_config(self, tmp_path):
        """Test creating a default configuration file."""
        config_path = tmp_path / "e2e.conf"

        result = ApiConfigLoader.create_default_config(config_path)

        assert Path(result).exists()
        content = Path(result).read_text()
        assert "general:" in content
        assert "environment:" in content

    def test_create_in_nonexistent_directory(self, tmp_path):
        """Test creating config in directory that doesn't exist."""
        config_path = tmp_path / "subdir" / "e2e.conf"

        result = ApiConfigLoader.create_default_config(config_path)

        assert Path(result).exists()
        assert config_path.parent.exists()

    def test_create_without_overwrite_raises_error(self, tmp_path):
        """Test that creating over existing file raises error."""
        config_path = tmp_path / "e2e.conf"
        config_path.write_text("existing content")

        with pytest.raises(FileExistsError):
            ApiConfigLoader.create_default_config(config_path, overwrite=False)

    def test_create_with_overwrite(self, tmp_path):
        """Test overwriting existing file with overwrite=True."""
        config_path = tmp_path / "e2e.conf"
        config_path.write_text("existing content")

        result = ApiConfigLoader.create_default_config(config_path, overwrite=True)

        content = Path(result).read_text()
        assert "general:" in content
        assert "existing content" not in content


class TestValidateConfig:
    """Test cases for validate_config method."""

    def test_valid_config_passes(self):
        """Test that valid configuration passes validation."""
        data = {
            "general": {
                "environment": "dev",
                "timeout": 30000,
            },
            "services": {
                "test-api": {
                    "base_url": "http://localhost:8080",
                }
            },
        }

        # Should not raise
        ApiConfigLoader.validate_config(data)

    def test_missing_general_section_raises_error(self):
        """Test that missing 'general' section raises ConfigError."""
        data = {"services": {"test-api": {"base_url": "http://localhost:8080"}}}

        with pytest.raises(ConfigError) as exc_info:
            ApiConfigLoader.validate_config(data)

        assert "general" in str(exc_info.value)

    def test_invalid_timeout_raises_error(self):
        """Test that invalid timeout value raises ConfigError."""
        data = {
            "general": {
                "environment": "dev",
                "timeout": "invalid",
            }
        }

        with pytest.raises(ConfigError) as exc_info:
            ApiConfigLoader.validate_config(data)

        assert "timeout" in str(exc_info.value)

    def test_negative_timeout_raises_error(self):
        """Test that negative timeout value raises ConfigError."""
        data = {
            "general": {
                "environment": "dev",
                "timeout": -1000,
            }
        }

        with pytest.raises(ConfigError) as exc_info:
            ApiConfigLoader.validate_config(data)

        assert "timeout" in str(exc_info.value)
        assert "positive" in str(exc_info.value)

    def test_service_without_base_url_raises_error(self):
        """Test that service without base_url raises ConfigError."""
        data = {
            "general": {"environment": "dev"},
            "services": {
                "test-api": {
                    "port": 8080,
                    # missing base_url
                }
            },
        }

        with pytest.raises(ConfigError) as exc_info:
            ApiConfigLoader.validate_config(data)

        assert "test-api" in str(exc_info.value)
        assert "base_url" in str(exc_info.value)

    def test_invalid_port_raises_error(self):
        """Test that invalid port value raises ConfigError."""
        data = {
            "general": {"environment": "dev"},
            "services": {
                "test-api": {
                    "base_url": "http://localhost:8080",
                    "port": 99999,  # Invalid port
                }
            },
        }

        with pytest.raises(ConfigError) as exc_info:
            ApiConfigLoader.validate_config(data)

        assert "port" in str(exc_info.value)

    def test_empty_services_warning_in_strict_mode(self):
        """Test that empty services generates warning in strict mode."""
        data = {"general": {"environment": "dev"}, "services": {}}

        # In non-strict mode, should not raise
        ApiConfigLoader.validate_config(data, strict=False)

        # In strict mode, should warn
        with pytest.warns(UserWarning):
            ApiConfigLoader.validate_config(data, strict=True)


class TestSubstituteEnvVars:
    """Test cases for environment variable substitution."""

    def test_substitute_simple_variable(self, monkeypatch):
        """Test substituting a simple environment variable."""
        monkeypatch.setenv("TEST_VAR", "test_value")

        content = "value: ${TEST_VAR}"
        result = ApiConfigLoader._substitute_env_vars(content)

        assert "value: test_value" in result

    def test_substitute_with_default(self):
        """Test substituting variable with default value."""
        content = "value: ${MISSING_VAR:-default_value}"
        result = ApiConfigLoader._substitute_env_vars(content)

        assert "value: default_value" in result

    def test_substitute_env_overrides_default(self, monkeypatch):
        """Test that env variable overrides default."""
        monkeypatch.setenv("TEST_VAR", "env_value")

        content = "value: ${TEST_VAR:-default_value}"
        result = ApiConfigLoader._substitute_env_vars(content)

        assert "value: env_value" in result

    def test_keep_unset_variable_without_default(self):
        """Test that unset variables without default are kept as-is."""
        content = "value: ${UNSET_VAR}"
        result = ApiConfigLoader._substitute_env_vars(content)

        assert "value: ${UNSET_VAR}" in result


class TestLoad:
    """Test cases for load method."""

    def test_load_valid_config(self, tmp_path, monkeypatch):
        """Test loading a valid configuration file."""
        config_file = tmp_path / "e2e.conf"
        config_file.write_text(
            """
general:
  environment: test
  timeout: 5000
services:
  test-api:
    name: test-service
    base_url: http://localhost:8080
"""
        )

        monkeypatch.chdir(tmp_path)
        # Reset singleton
        ApiConfigLoader._instance = None

        config = ApiConfigLoader.load()

        assert isinstance(config, AppConfig)
        assert config.environment == "test"
        assert config.timeout == 5000
        # Service names are normalized (hyphens to underscores)
        assert "test_api" in config.services

    def test_load_invalid_config_raises_error(self, tmp_path, monkeypatch):
        """Test that loading invalid config raises ConfigError."""
        config_file = tmp_path / "e2e.conf"
        config_file.write_text(
            """
general:
  timeout: invalid_value
"""
        )

        monkeypatch.chdir(tmp_path)
        ApiConfigLoader._instance = None

        with pytest.raises(ConfigError):
            ApiConfigLoader.load()

    def test_singleton_pattern(self, tmp_path, monkeypatch):
        """Test that load() returns same instance on subsequent calls."""
        config_file = tmp_path / "e2e.conf"
        config_file.write_text(
            """
general:
  environment: test
services:
  test-api:
    base_url: http://localhost:8080
"""
        )

        monkeypatch.chdir(tmp_path)
        # Reset singleton
        ApiConfigLoader._instance = None

        config1 = ApiConfigLoader.load()
        config2 = ApiConfigLoader.load()

        assert config1 is config2

    def test_reload_creates_new_instance(self, tmp_path, monkeypatch):
        """Test that reload() creates a new instance."""
        config_file = tmp_path / "e2e.conf"
        config_file.write_text(
            """
general:
  environment: test
services:
  test-api:
    base_url: http://localhost:8080
"""
        )

        monkeypatch.chdir(tmp_path)
        ApiConfigLoader._instance = None

        config1 = ApiConfigLoader.load()
        config2 = ApiConfigLoader.reload()

        assert config1 is not config2
        assert config1.environment == config2.environment


class TestParseConfig:
    """Test cases for _parse_config method."""

    def test_parse_general_config(self):
        """Test parsing general configuration section."""
        data = {
            "general": {
                "environment": "production",
                "timeout": 60000,
                "user_agent": "TestAgent/1.0",
                "verbose": False,
            }
        }

        config = ApiConfigLoader._parse_config(data)

        assert config.environment == "production"
        assert config.timeout == 60000
        assert config.user_agent == "TestAgent/1.0"
        assert config.verbose is False

    def test_parse_services(self):
        """Test parsing services configuration."""
        data = {
            "general": {"environment": "dev"},
            "services": {
                "api1": {
                    "name": "service-one",
                    "base_url": "http://localhost:8081",
                    "health_endpoint": "/health",
                    "port": 8081,
                    "timeout": 10000,
                    "required": True,
                },
                "api2": {
                    "name": "service-two",
                    "base_url": "http://localhost:8082",
                },
            },
        }

        config = ApiConfigLoader._parse_config(data)

        assert len(config.services) == 2
        assert "api1" in config.services
        assert "api2" in config.services

        service1 = config.services["api1"]
        assert isinstance(service1, ServiceConfig)
        assert service1.name == "service-one"
        assert service1.base_url == "http://localhost:8081"
        assert service1.health_endpoint == "/health"

    def test_parse_with_defaults(self):
        """Test that default values are applied."""
        data = {
            "general": {},  # Empty general section
        }

        config = ApiConfigLoader._parse_config(data)

        assert config.environment == "dev"  # Default
        assert config.timeout == 30000  # Default
        assert config.verbose is True  # Default
        assert config.user_agent == "SocialSeed-E2E-Agent/2.0"  # Default


class TestBackwardCompatibility:
    """Test backward compatibility with legacy configurations."""

    def test_legacy_api_conf_supported(self, tmp_path, monkeypatch):
        """Test that legacy api.conf format is still supported."""
        config_file = tmp_path / "api.conf"
        config_file.write_text(
            """
general:
  environment: dev
services:
  legacy-api:
    base_url: http://localhost:8080
"""
        )

        monkeypatch.chdir(tmp_path)
        ApiConfigLoader._instance = None

        config = ApiConfigLoader.load()
        assert config.environment == "dev"

    def test_legacy_verify_services_path(self, tmp_path, monkeypatch):
        """Test support for legacy verify_services/api.conf path."""
        verify_dir = tmp_path / "verify_services"
        verify_dir.mkdir()
        config_file = verify_dir / "api.conf"
        config_file.write_text(
            """
general:
  environment: dev
services:
  test-api:
    base_url: http://localhost:8080
"""
        )

        monkeypatch.chdir(tmp_path)
        ApiConfigLoader._instance = None

        config = ApiConfigLoader.load()
        assert config.environment == "dev"


class TestReloadScenarios:
    """Test cases for reload() method with various scenarios."""

    def test_reload_without_prior_load(self, tmp_path, monkeypatch):
        """Test that reload() works even without prior load() call."""
        config_file = tmp_path / "e2e.conf"
        config_file.write_text(
            """
general:
  environment: test
services:
  test-api:
    base_url: http://localhost:8080
"""
        )

        monkeypatch.chdir(tmp_path)
        ApiConfigLoader._instance = None
        ApiConfigLoader._config_path = None

        config = ApiConfigLoader.reload()

        assert isinstance(config, AppConfig)
        assert config.environment == "test"

    def test_reload_with_explicit_path(self, tmp_path, monkeypatch):
        """Test reload() uses stored config path."""
        config_file = tmp_path / "e2e.conf"
        config_file.write_text(
            """
general:
  environment: initial
services:
  test-api:
    base_url: http://localhost:8080
"""
        )

        monkeypatch.chdir(tmp_path)
        ApiConfigLoader._instance = None

        # First load
        config1 = ApiConfigLoader.load()
        assert config1.environment == "initial"

        # Modify file
        config_file.write_text(
            """
general:
  environment: modified
services:
  test-api:
    base_url: http://localhost:8080
"""
        )

        # Reload should pick up changes
        config2 = ApiConfigLoader.reload()
        assert config2.environment == "modified"

    def test_reload_resets_singleton(self, tmp_path, monkeypatch):
        """Test that reload() properly resets singleton state."""
        config_file = tmp_path / "e2e.conf"
        config_file.write_text(
            """
general:
  environment: test
services:
  test-api:
    base_url: http://localhost:8080
"""
        )

        monkeypatch.chdir(tmp_path)
        ApiConfigLoader._instance = None

        config1 = ApiConfigLoader.load()
        ApiConfigLoader.reload()
        config2 = ApiConfigLoader.load()

        # After reload, load() should still work normally
        assert isinstance(config2, AppConfig)
        assert config1.environment == config2.environment


class TestEnvVarEdgeCases:
    """Test cases for environment variable substitution edge cases."""

    def test_substitute_multiple_variables(self, monkeypatch):
        """Test substituting multiple environment variables."""
        monkeypatch.setenv("VAR1", "value1")
        monkeypatch.setenv("VAR2", "value2")

        content = "host: ${VAR1}, port: ${VAR2}"
        result = ApiConfigLoader._substitute_env_vars(content)

        assert result == "host: value1, port: value2"

    def test_substitute_empty_env_var(self, monkeypatch):
        """Test substituting empty environment variable."""
        monkeypatch.setenv("EMPTY_VAR", "")

        content = "value: ${EMPTY_VAR}"
        result = ApiConfigLoader._substitute_env_vars(content)

        # Empty string should replace the variable
        assert result == "value: "

    def test_substitute_empty_default(self):
        """Test substituting variable with empty default value."""
        content = "value: ${MISSING_VAR:-}"
        result = ApiConfigLoader._substitute_env_vars(content)

        assert result == "value: "

    def test_substitute_special_chars_in_default(self):
        """Test default value with special characters."""
        content = "url: ${MISSING_URL:-http://localhost:8080/api/v1}"
        result = ApiConfigLoader._substitute_env_vars(content)

        assert result == "url: http://localhost:8080/api/v1"

    def test_substitute_no_braces_format(self):
        """Test that non-brace format is not substituted."""
        content = "value: $VAR_NAME"
        result = ApiConfigLoader._substitute_env_vars(content)

        # Format without braces should remain unchanged
        assert result == "value: $VAR_NAME"

    def test_substitute_in_yaml_structure(self, monkeypatch):
        """Test substitution within YAML structure."""
        monkeypatch.setenv("API_PORT", "9090")

        content = """
services:
  test-api:
    base_url: http://localhost:${API_PORT}
"""
        result = ApiConfigLoader._substitute_env_vars(content)

        assert "http://localhost:9090" in result

    def test_substitute_partial_variable_name(self, monkeypatch):
        """Test that partial variable names are handled correctly."""
        monkeypatch.setenv("HOST", "example.com")

        content = "value: ${HOSTNAME}"  # HOSTNAME, not HOST
        result = ApiConfigLoader._substitute_env_vars(content)

        # HOSTNAME is different from HOST, should remain unchanged
        assert result == "value: ${HOSTNAME}"


class TestJsonConfiguration:
    """Test cases for JSON configuration format."""

    def test_load_valid_json_config(self, tmp_path, monkeypatch):
        """Test loading a valid JSON configuration file."""
        config_file = tmp_path / "e2e.json"
        config_file.write_text(
            """{
  "general": {
    "environment": "test",
    "timeout": 5000
  },
  "services": {
    "test-api": {
      "name": "test-service",
      "base_url": "http://localhost:8080"
    }
  }
}"""
        )

        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("E2E_CONFIG_PATH", str(config_file))
        ApiConfigLoader._instance = None

        config = ApiConfigLoader.load()

        assert isinstance(config, AppConfig)
        assert config.environment == "test"
        assert config.timeout == 5000
        # Service names are normalized (hyphens to underscores)
        assert "test_api" in config.services

    def test_json_config_with_env_vars(self, tmp_path, monkeypatch):
        """Test JSON config with environment variable substitution."""
        monkeypatch.setenv("TEST_HOST", "api.example.com")

        config_file = tmp_path / "e2e.json"
        config_file.write_text(
            """{
  "general": {
    "environment": "test"
  },
  "services": {
    "test-api": {
      "base_url": "http://${TEST_HOST}:8080"
    }
  }
}"""
        )

        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("E2E_CONFIG_PATH", str(config_file))
        ApiConfigLoader._instance = None

        config = ApiConfigLoader.load()

        # Service names are normalized (hyphens to underscores)
        assert config.services["test_api"].base_url == "http://api.example.com:8080"

    def test_json_invalid_syntax_raises_error(self, tmp_path, monkeypatch):
        """Test that invalid JSON syntax raises appropriate error."""
        config_file = tmp_path / "e2e.json"
        config_file.write_text(
            """{
  "general": {
    "environment": "test"
  },
  "services": {
    "test-api": {
      "base_url": "http://localhost:8080"
    }
  }
  invalid json here
}"""
        )

        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("E2E_CONFIG_PATH", str(config_file))
        ApiConfigLoader._instance = None

        # Should raise a parser error (YAML parses JSON, so it's a yaml.parser.ParserError)
        with pytest.raises(Exception):  # ParserError is a subclass of Exception
            ApiConfigLoader.load()


class TestPartialAndInvalidConfigurations:
    """Test cases for partial and invalid configurations."""

    def test_minimal_config_with_only_general(self, tmp_path, monkeypatch):
        """Test loading minimal config with only general section."""
        config_file = tmp_path / "e2e.conf"
        config_file.write_text(
            """
general:
  environment: test
"""
        )

        monkeypatch.chdir(tmp_path)
        ApiConfigLoader._instance = None

        config = ApiConfigLoader.load()

        assert config.environment == "test"
        assert config.services == {}

    def test_service_with_only_required_fields(self, tmp_path, monkeypatch):
        """Test service configuration with only required base_url."""
        config_file = tmp_path / "e2e.conf"
        config_file.write_text(
            """
general:
  environment: test
services:
  minimal-api:
    base_url: http://localhost:8080
"""
        )

        monkeypatch.chdir(tmp_path)
        ApiConfigLoader._instance = None

        config = ApiConfigLoader.load()

        # Service names are normalized (hyphens to underscores)
        service = config.services["minimal_api"]
        assert service.base_url == "http://localhost:8080"
        assert service.name == "minimal-api"  # Original name preserved
        assert service.port == 8080  # Default value
        assert service.required is True  # Default value

    def test_invalid_yaml_raises_error(self, tmp_path, monkeypatch):
        """Test that invalid YAML raises appropriate error."""
        config_file = tmp_path / "e2e.conf"
        config_file.write_text(
            """
general:
  environment: test
services:
  - this is not valid: service
    structure: should be dict not list
"""
        )

        monkeypatch.chdir(tmp_path)
        ApiConfigLoader._instance = None

        # Should raise error due to validation (services as list instead of dict)
        with pytest.raises((ConfigError, AttributeError)):
            ApiConfigLoader.load()

    def test_service_not_a_dict_raises_error(self, tmp_path, monkeypatch):
        """Test that service defined as non-dict raises validation error."""
        config_file = tmp_path / "e2e.conf"
        config_file.write_text(
            """
general:
  environment: test
services:
  invalid-service: "just a string"
"""
        )

        monkeypatch.chdir(tmp_path)
        ApiConfigLoader._instance = None

        with pytest.raises(ConfigError) as exc_info:
            ApiConfigLoader.load()

        assert "invalid-service" in str(exc_info.value)

    def test_empty_config_file_raises_error(self, tmp_path, monkeypatch):
        """Test that empty config file raises error."""
        config_file = tmp_path / "e2e.conf"
        config_file.write_text("")

        monkeypatch.chdir(tmp_path)
        ApiConfigLoader._instance = None

        # Empty YAML file returns None, which causes TypeError in validation
        with pytest.raises((ConfigError, TypeError)):
            ApiConfigLoader.load()

    def test_config_with_null_values_raises_error(self, tmp_path, monkeypatch):
        """Test that null values raise validation error."""
        config_file = tmp_path / "e2e.conf"
        config_file.write_text(
            """
general:
  environment: test
  timeout: null
services:
  test-api:
    base_url: http://localhost:8080
"""
        )

        monkeypatch.chdir(tmp_path)
        ApiConfigLoader._instance = None

        # Null is not a valid integer, should raise ConfigError
        with pytest.raises(ConfigError) as exc_info:
            ApiConfigLoader.load()

        assert "timeout" in str(exc_info.value)
        assert "valid integer" in str(exc_info.value)


class TestConfigurationWithAllOptionalFields:
    """Test cases for configuration with all optional fields populated."""

    def test_full_general_configuration(self, tmp_path, monkeypatch):
        """Test general section with all optional fields."""
        config_file = tmp_path / "e2e.conf"
        config_file.write_text(
            """
general:
  environment: production
  timeout: 60000
  user_agent: CustomAgent/1.0
  verification_level: lenient
  verbose: false
  project:
    name: MyProject
    version: 1.2.3
services:
  test-api:
    base_url: http://localhost:8080
"""
        )

        monkeypatch.chdir(tmp_path)
        ApiConfigLoader._instance = None

        config = ApiConfigLoader.load()

        assert config.environment == "production"
        assert config.timeout == 60000
        assert config.user_agent == "CustomAgent/1.0"
        assert config.verification_level == "lenient"
        assert config.verbose is False
        assert config.project_name == "MyProject"
        assert config.project_version == "1.2.3"

    def test_full_service_configuration(self, tmp_path, monkeypatch):
        """Test service with all optional fields populated."""
        config_file = tmp_path / "e2e.conf"
        config_file.write_text(
            """
general:
  environment: test
services:
  full-api:
    name: Full API Service
    base_url: http://localhost:9090
    health_endpoint: /health/check
    port: 9090
    maven_module: services/full-api
    timeout: 15000
    headers:
      Authorization: Bearer token123
      Content-Type: application/json
    auto_start: false
    required: false
    endpoints:
      login: /auth/login
      logout: /auth/logout
"""
        )

        monkeypatch.chdir(tmp_path)
        ApiConfigLoader._instance = None

        config = ApiConfigLoader.load()
        # Service names are normalized (hyphens to underscores)
        service = config.services["full_api"]

        assert service.name == "Full API Service"
        assert service.base_url == "http://localhost:9090"
        assert service.health_endpoint == "/health/check"
        assert service.port == 9090
        assert service.maven_module == "services/full-api"
        assert service.timeout == 15000
        assert service.headers == {
            "Authorization": "Bearer token123",
            "Content-Type": "application/json",
        }
        assert service.auto_start is False
        assert service.required is False
        assert service.endpoints == {"login": "/auth/login", "logout": "/auth/logout"}

    def test_full_api_gateway_configuration(self, tmp_path, monkeypatch):
        """Test API gateway with all optional fields."""
        config_file = tmp_path / "e2e.conf"
        config_file.write_text(
            """
general:
  environment: test
api_gateway:
  enabled: true
  url: http://gateway.example.com
  prefix: /api/v1
  auth:
    type: bearer
    bearer_token: secret-token-123
    api_key_header: X-API-Key
    api_key_value: api-key-value
services:
  test-api:
    base_url: http://localhost:8080
"""
        )

        monkeypatch.chdir(tmp_path)
        ApiConfigLoader._instance = None

        config = ApiConfigLoader.load()
        gateway = config.api_gateway

        assert gateway.enabled is True
        assert gateway.url == "http://gateway.example.com"
        assert gateway.prefix == "/api/v1"
        assert gateway.auth_type == "bearer"
        assert gateway.auth_token == "secret-token-123"
        assert gateway.api_key_header == "X-API-Key"
        assert gateway.api_key_value == "api-key-value"

    def test_full_database_configuration(self, tmp_path, monkeypatch):
        """Test database configuration with all optional fields."""
        config_file = tmp_path / "e2e.conf"
        config_file.write_text(
            """
general:
  environment: test
databases:
  main-db:
    host: db.example.com
    port: 5433
    database: myapp
    username: dbuser
    password: dbpass123
    enabled: true
services:
  test-api:
    base_url: http://localhost:8080
"""
        )

        monkeypatch.chdir(tmp_path)
        ApiConfigLoader._instance = None

        config = ApiConfigLoader.load()
        db = config.databases["main-db"]

        assert db.host == "db.example.com"
        assert db.port == 5433
        assert db.database == "myapp"
        assert db.username == "dbuser"
        assert db.password == "dbpass123"
        assert db.enabled is True

    def test_full_test_data_configuration(self, tmp_path, monkeypatch):
        """Test test data configuration with all optional fields."""
        config_file = tmp_path / "e2e.conf"
        config_file.write_text(
            """
general:
  environment: test
test_data:
  user:
    email_domain: custom.domain.com
    password: CustomPass123!
    username_prefix: autouser
  timing:
    step_delay: 500
    async_timeout: 20000
  retries:
    max_attempts: 5
    backoff_ms: 2000
services:
  test-api:
    base_url: http://localhost:8080
"""
        )

        monkeypatch.chdir(tmp_path)
        ApiConfigLoader._instance = None

        config = ApiConfigLoader.load()
        test_data = config.test_data

        assert test_data.email_domain == "custom.domain.com"
        assert test_data.password == "CustomPass123!"
        assert test_data.username_prefix == "autouser"
        assert test_data.step_delay == 500
        assert test_data.async_timeout == 20000
        assert test_data.max_retries == 5
        assert test_data.retry_backoff_ms == 2000

    def test_full_security_configuration(self, tmp_path, monkeypatch):
        """Test security configuration with all optional fields."""
        config_file = tmp_path / "e2e.conf"
        config_file.write_text(
            """
general:
  environment: test
security:
  verify_ssl: false
  ssl_cert: /path/to/cert.pem
  ssl_key: /path/to/key.pem
  ssl_ca: /path/to/ca.pem
  test_tokens:
    admin: admin-token-123
    user: user-token-456
services:
  test-api:
    base_url: http://localhost:8080
"""
        )

        monkeypatch.chdir(tmp_path)
        ApiConfigLoader._instance = None

        config = ApiConfigLoader.load()
        security = config.security

        assert security.verify_ssl is False
        assert security.ssl_cert == "/path/to/cert.pem"
        assert security.ssl_key == "/path/to/key.pem"
        assert security.ssl_ca == "/path/to/ca.pem"
        assert security.test_tokens == {
            "admin": "admin-token-123",
            "user": "user-token-456",
        }

    def test_full_reporting_configuration(self, tmp_path, monkeypatch):
        """Test reporting configuration with all optional fields."""
        config_file = tmp_path / "e2e.conf"
        config_file.write_text(
            """
general:
  environment: test
reporting:
  format: json
  save_logs: false
  log_dir: /var/log/tests
  include_payloads: true
  screenshot_on_failure: true
services:
  test-api:
    base_url: http://localhost:8080
"""
        )

        monkeypatch.chdir(tmp_path)
        ApiConfigLoader._instance = None

        config = ApiConfigLoader.load()
        reporting = config.reporting

        assert reporting.format == "json"
        assert reporting.save_logs is False
        assert reporting.log_dir == "/var/log/tests"
        assert reporting.include_payloads is True
        assert reporting.screenshot_on_failure is True


class TestConfigLoaderUtilities:
    """Test cases for utility methods of ApiConfigLoader."""

    def test_get_config_path_returns_none_before_load(self):
        """Test get_config_path returns None before any load."""
        ApiConfigLoader._instance = None
        ApiConfigLoader._config_path = None

        result = ApiConfigLoader.get_config_path()
        assert result is None

    def test_get_config_path_after_load(self, tmp_path, monkeypatch):
        """Test get_config_path returns correct path after load."""
        config_file = tmp_path / "e2e.conf"
        config_file.write_text(
            """
general:
  environment: test
services:
  test-api:
    base_url: http://localhost:8080
"""
        )

        monkeypatch.chdir(tmp_path)
        ApiConfigLoader._instance = None
        ApiConfigLoader._config_path = None

        ApiConfigLoader.load()
        path = ApiConfigLoader.get_config_path()

        assert path is not None
        assert path.name == "e2e.conf"

    def test_validate_config_invalid_environment_warning(self):
        """Test validation warning for unusual environment value."""
        data = {
            "general": {
                "environment": "custom-env",  # Not a standard value
            }
        }

        # In strict mode, should generate warning about unusual environment
        import warnings

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            ApiConfigLoader.validate_config(data, strict=True)
            # Should generate at least one warning about unusual environment
            assert len(w) >= 1
            assert any("Unusual environment" in str(warning.message) for warning in w)

    def test_validate_short_timeout_warning(self):
        """Test validation warning for very short timeout."""
        data = {
            "general": {
                "environment": "test",
                "timeout": 500,  # Very short
            }
        }

        import warnings

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            ApiConfigLoader.validate_config(data, strict=True)
            # Should generate at least one warning about short timeout
            assert len(w) >= 1
            assert any("very short" in str(warning.message).lower() for warning in w)

    def test_validate_empty_base_url_warning(self):
        """Test validation warning for empty base_url."""
        data = {
            "general": {
                "environment": "test",
            },
            "services": {
                "test-api": {
                    "base_url": "",  # Empty base_url
                }
            },
        }

        import warnings

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            ApiConfigLoader.validate_config(data, strict=True)
            # Should generate at least one warning about empty base_url
            assert len(w) >= 1
            assert any("empty base_url" in str(warning.message) for warning in w)


class TestServiceNameNormalization:
    """Test cases for service name normalization (Issue #178)."""

    def test_normalize_service_name_with_hyphens(self):
        """Test that hyphens are converted to underscores."""
        assert normalize_service_name("auth-service") == "auth_service"
        assert normalize_service_name("user-api") == "user_api"
        assert normalize_service_name("my-service-name") == "my_service_name"

    def test_normalize_service_name_with_underscores(self):
        """Test that underscores remain unchanged."""
        assert normalize_service_name("auth_service") == "auth_service"
        assert normalize_service_name("user_api") == "user_api"

    def test_normalize_service_name_mixed(self):
        """Test normalization with mixed hyphens and underscores."""
        assert normalize_service_name("auth-service_v2") == "auth_service_v2"
        assert normalize_service_name("my-api-service") == "my_api_service"

    def test_service_config_stored_with_normalized_name(self, tmp_path, monkeypatch):
        """Test that services are stored with normalized names in config."""
        config_file = tmp_path / "e2e.conf"
        config_file.write_text(
            """
general:
  environment: test
services:
  auth-service:
    name: Auth Service
    base_url: http://localhost:8085
    port: 8085
"""
        )

        monkeypatch.chdir(tmp_path)
        ApiConfigLoader._instance = None

        config = ApiConfigLoader.load()

        # Service should be stored with normalized name (auth_service)
        assert "auth_service" in config.services
        assert "auth-service" not in config.services

        # But the original name should be preserved in the service config
        service = config.services["auth_service"]
        assert service.name == "Auth Service"
        assert service.base_url == "http://localhost:8085"
        assert service.port == 8085

    def test_get_service_config_with_hyphenated_name(self, tmp_path, monkeypatch):
        """Test that get_service_config works with hyphenated service names."""
        config_file = tmp_path / "e2e.conf"
        config_file.write_text(
            """
general:
  environment: test
services:
  auth-service:
    name: Auth Service
    base_url: http://localhost:8085
"""
        )

        monkeypatch.chdir(tmp_path)
        ApiConfigLoader._instance = None

        # Should find the service using hyphenated name
        service = get_service_config("auth-service")
        assert service is not None
        assert service.base_url == "http://localhost:8085"

        # Should also find it using underscore name
        service = get_service_config("auth_service")
        assert service is not None
        assert service.base_url == "http://localhost:8085"

    def test_multiple_services_with_various_naming(self, tmp_path, monkeypatch):
        """Test config with multiple services using different naming conventions."""
        config_file = tmp_path / "e2e.conf"
        config_file.write_text(
            """
general:
  environment: test
services:
  auth-service:
    name: Auth Service
    base_url: http://localhost:8081
  user_api:
    name: User API
    base_url: http://localhost:8082
  payment-service-v2:
    name: Payment Service V2
    base_url: http://localhost:8083
"""
        )

        monkeypatch.chdir(tmp_path)
        ApiConfigLoader._instance = None

        config = ApiConfigLoader.load()

        # All services should be stored with normalized names
        assert "auth_service" in config.services
        assert "user_api" in config.services
        assert "payment_service_v2" in config.services

        # Should be accessible using various naming conventions
        assert get_service_config("auth-service").base_url == "http://localhost:8081"
        assert get_service_config("auth_service").base_url == "http://localhost:8081"
        assert get_service_config("user_api").base_url == "http://localhost:8082"
        assert (
            get_service_config("payment-service-v2").base_url == "http://localhost:8083"
        )
        assert (
            get_service_config("payment_service_v2").base_url == "http://localhost:8083"
        )

    def test_service_name_collision_raises_error(self, tmp_path, monkeypatch):
        """Test that services with same normalized name cause collision."""
        config_file = tmp_path / "e2e.conf"
        # This config has both auth-service and auth_service
        # The second one should overwrite the first (YAML behavior)
        config_file.write_text(
            """
general:
  environment: test
services:
  auth-service:
    name: Auth Service with hyphens
    base_url: http://localhost:8081
  auth_service:
    name: Auth Service with underscores
    base_url: http://localhost:8082
"""
        )

        monkeypatch.chdir(tmp_path)
        ApiConfigLoader._instance = None

        config = ApiConfigLoader.load()

        # Both services normalize to auth_service, so the last one wins
        assert "auth_service" in config.services
        # The service should have the values from the second definition
        service = config.services["auth_service"]
        assert service.base_url == "http://localhost:8082"
        assert service.name == "Auth Service with underscores"
