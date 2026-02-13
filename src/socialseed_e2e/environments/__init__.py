"""
Environment management module for socialseed-e2e.

Exposes:
- EnvironmentManager: Main entry point for managing environments.
- EnvironmentConfig: Configuration schema.
- SecretProvider: Abstract base class for secret providers.
"""

from .manager import EnvironmentManager
from .secrets import (
    AWSSecretManagerProvider,
    EnvironmentVariableSecretProvider,
    SecretProvider,
    VaultSecretProvider,
)
from .validator import EnvironmentConfig, compare_environments, validate_config

__all__ = [
    "EnvironmentManager",
    "EnvironmentConfig",
    "validate_config",
    "compare_environments",
    "SecretProvider",
    "EnvironmentVariableSecretProvider",
    "VaultSecretProvider",
    "AWSSecretManagerProvider",
]
