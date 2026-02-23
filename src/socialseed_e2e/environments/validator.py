"""
Configuration validation module for socialseed-e2e environments.
"""
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, ValidationError


class ServiceConfig(BaseModel):
    """Base configuration for a service."""

    host: Optional[str] = None
    port: Optional[int] = None
    enabled: bool = True
    config: Dict[str, Any] = Field(default_factory=dict)


class DatabaseConfig(ServiceConfig):
    """Database configuration."""

    engine: str = "postgresql"
    username: Optional[str] = None
    password: Optional[str] = None  # Should come from secrets
    database_name: str = "socialseed"


class SecretsConfig(BaseModel):
    """Secrets management configuration."""

    provider: str = Field("env", description="Secrets provider: env, vault, aws")
    env_var_prefix: str = "SOCIALSEED_"
    # Vault specific
    vault_url: Optional[str] = None
    vault_mount_point: Optional[str] = "secret"
    # AWS specific
    aws_region: Optional[str] = "us-east-1"
    aws_profile: Optional[str] = None


class EnvironmentConfig(BaseModel):
    """
    Main environment configuration schema.
    Validates the structure of environment implementation files.
    """

    environment: str = Field(..., description="Environment name (e.g., dev, staging, prod)")
    debug: bool = False
    log_level: str = "INFO"

    secrets: SecretsConfig = Field(default_factory=SecretsConfig)

    database: Optional[DatabaseConfig] = None
    redis: Optional[ServiceConfig] = None
    kafka: Optional[ServiceConfig] = None

    external_services: Dict[str, ServiceConfig] = Field(default_factory=dict)

    custom_settings: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        extra = "allow"  # Allow extra fields for flexibility


def validate_config(config_data: Dict[str, Any]) -> EnvironmentConfig:
    """
    Validates configuration data against the schema.
    Raises ValidationError if invalid.
    """
    try:
        return EnvironmentConfig(**config_data)
    except ValidationError as e:
        # Re-raise or handle
        raise e


def compare_environments(config_a: Dict[str, Any], config_b: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compares two environment configurations and returns the diff.
    """
    diff = {"added": [], "removed": [], "changed": {}}

    all_keys = set(config_a.keys()) | set(config_b.keys())

    for key in all_keys:
        if key not in config_a:
            diff["added"].append(key)
        elif key not in config_b:
            diff["removed"].append(key)
        else:
            if config_a[key] != config_b[key]:
                diff["changed"][key] = {"from": config_a[key], "to": config_b[key]}
    return diff
