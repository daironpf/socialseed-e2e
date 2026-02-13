"""
Environment management module for socialseed-e2e.

Exposes:
- EnvironmentManager: Main entry point for managing environments.
- EnvironmentConfig: Configuration schema.
- SecretProvider: Abstract base class for secret providers.
"""

from .manager import EnvironmentManager
from .validator import EnvironmentConfig, validate_config, compare_environments
from .secrets import SecretProvider, EnvironmentVariableSecretProvider, VaultSecretProvider, AWSSecretManagerProvider

__all__ = [
    "EnvironmentManager",
    "EnvironmentConfig",
    "validate_config",
    "compare_environments", 
    "SecretProvider",
    "EnvironmentVariableSecretProvider",
    "VaultSecretProvider",
    "AWSSecretManagerProvider"
]
