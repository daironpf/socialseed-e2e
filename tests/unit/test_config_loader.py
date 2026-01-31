"""Tests for ApiConfigLoader.

This module contains unit tests for the ApiConfigLoader class,
testing configuration loading, validation, and file discovery.
"""

import os
import tempfile
from pathlib import Path

import pytest

from socialseed_e2e.core.config_loader import (
    ApiConfigLoader,
    AppConfig,
    ServiceConfig,
    ConfigError,
)


class TestFindConfigFile:
    """Test cases for configuration file discovery."""

    def test_find_from_env_variable(self, monkeypatch):
        """Test finding config from E2E_CONFIG_PATH environment variable."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as f:
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
        with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as f:
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
            }
        }
        
        # Should not raise
        ApiConfigLoader.validate_config(data)

    def test_missing_general_section_raises_error(self):
        """Test that missing 'general' section raises ConfigError."""
        data = {
            "services": {
                "test-api": {"base_url": "http://localhost:8080"}
            }
        }
        
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
            }
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
            }
        }
        
        with pytest.raises(ConfigError) as exc_info:
            ApiConfigLoader.validate_config(data)
        
        assert "port" in str(exc_info.value)

    def test_empty_services_warning_in_strict_mode(self):
        """Test that empty services generates warning in strict mode."""
        data = {
            "general": {"environment": "dev"},
            "services": {}
        }
        
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
        config_file.write_text("""
general:
  environment: test
  timeout: 5000
services:
  test-api:
    name: test-service
    base_url: http://localhost:8080
""")
        
        monkeypatch.chdir(tmp_path)
        # Reset singleton
        ApiConfigLoader._instance = None
        
        config = ApiConfigLoader.load()
        
        assert isinstance(config, AppConfig)
        assert config.environment == "test"
        assert config.timeout == 5000
        assert "test-api" in config.services

    def test_load_invalid_config_raises_error(self, tmp_path, monkeypatch):
        """Test that loading invalid config raises ConfigError."""
        config_file = tmp_path / "e2e.conf"
        config_file.write_text("""
general:
  timeout: invalid_value
""")
        
        monkeypatch.chdir(tmp_path)
        ApiConfigLoader._instance = None
        
        with pytest.raises(ConfigError):
            ApiConfigLoader.load()

    def test_singleton_pattern(self, tmp_path, monkeypatch):
        """Test that load() returns same instance on subsequent calls."""
        config_file = tmp_path / "e2e.conf"
        config_file.write_text("""
general:
  environment: test
services:
  test-api:
    base_url: http://localhost:8080
""")
        
        monkeypatch.chdir(tmp_path)
        # Reset singleton
        ApiConfigLoader._instance = None
        
        config1 = ApiConfigLoader.load()
        config2 = ApiConfigLoader.load()
        
        assert config1 is config2

    def test_reload_creates_new_instance(self, tmp_path, monkeypatch):
        """Test that reload() creates a new instance."""
        config_file = tmp_path / "e2e.conf"
        config_file.write_text("""
general:
  environment: test
services:
  test-api:
    base_url: http://localhost:8080
""")
        
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
                }
            }
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
        config_file.write_text("""
general:
  environment: dev
services:
  legacy-api:
    base_url: http://localhost:8080
""")
        
        monkeypatch.chdir(tmp_path)
        ApiConfigLoader._instance = None
        
        config = ApiConfigLoader.load()
        assert config.environment == "dev"

    def test_legacy_verify_services_path(self, tmp_path, monkeypatch):
        """Test support for legacy verify_services/api.conf path."""
        verify_dir = tmp_path / "verify_services"
        verify_dir.mkdir()
        config_file = verify_dir / "api.conf"
        config_file.write_text("""
general:
  environment: dev
services:
  test-api:
    base_url: http://localhost:8080
""")
        
        monkeypatch.chdir(tmp_path)
        ApiConfigLoader._instance = None
        
        config = ApiConfigLoader.load()
        assert config.environment == "dev"
