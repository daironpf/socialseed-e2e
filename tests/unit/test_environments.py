import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from socialseed_e2e.environments.manager import EnvironmentManager
from socialseed_e2e.environments.secrets import EnvironmentVariableSecretProvider


@pytest.fixture
def config_dir(tmp_path):
    """Creates a temporary configuration directory with sample config files."""
    base_config = {
        "debug": False,
        "logging": {"level": "INFO"},
        "secrets": {"provider": "env", "env_var_prefix": "TEST_APP_"},
        "database": {"host": "localhost", "port": 5432},
    }

    dev_config = {
        "environment": "development",
        "debug": True,
        "database": {"password": "SECRET:DB_PASSWORD"},
    }

    prod_config = {
        "environment": "production",
        "logging": {"level": "WARNING"},
        "secrets": {"provider": "aws", "aws_region": "us-west-2"},
    }

    with open(tmp_path / "base.yaml", "w") as f:
        yaml.dump(base_config, f)

    with open(tmp_path / "development.yaml", "w") as f:
        yaml.dump(dev_config, f)

    with open(tmp_path / "production.yaml", "w") as f:
        yaml.dump(prod_config, f)

    return tmp_path


def test_load_environment_merge_and_validate(config_dir):
    manager = EnvironmentManager(config_dir)

    # Mock secrets to avoid looking up real env vars or AWS
    with patch.dict(os.environ, {"TEST_APP_DB_PASSWORD": "mysecretpassword"}):
        config = manager.load_environment("development")

    assert config["environment"] == "development"
    assert config["debug"] is True
    assert config["logging"]["level"] == "INFO"  # From base
    assert config["database"]["host"] == "localhost"  # From base
    assert config["database"]["password"] == "mysecretpassword"  # Secret injected


def test_compare_environments(config_dir):
    manager = EnvironmentManager(config_dir)

    # Mock validation pass
    with patch("socialseed_e2e.environments.manager.validate_config") as mock_validate:
        diff = manager.compare_envs("development", "production")

    # Check diff structure
    # development has debug=True, production inherits debug=False (from base)?
    # Wait, base debug=False. dev overrides to True. prod inherits base=False.
    # So "debug" key should be in changed.

    assert "debug" in diff["changed"]
    assert diff["changed"]["debug"]["from"] is True
    assert diff["changed"]["debug"]["to"] is False


def test_secrets_provider_setup(config_dir):
    manager = EnvironmentManager(config_dir)

    # Force use of environment variable provider
    # Mocking get_secrets_provider to inspect calls is better, but let's trust logic for now
    # or use direct assertion if possible.

    # No patching, let it run (configures env provider)
    manager.load_environment("development")

    assert manager.secrets_provider is not None
    # We can check if it's a CompositeSecretProvider
    # But for this test, we care that it works as validated in previous test.


def test_drift_detection(config_dir):
    manager = EnvironmentManager(config_dir)
    with patch.dict(os.environ, {"TEST_APP_DB_PASSWORD": "secret"}):
        config = manager.load_environment("development")

    # Simulate external state that differs
    external_state = config.copy()
    external_state["debug"] = False  # Drift: Config says True, State says False

    drift = manager.detect_drift(external_state)
    assert "debug" in drift["changed"]
    assert drift["changed"]["debug"]["from"] is True
    assert drift["changed"]["debug"]["to"] is False
