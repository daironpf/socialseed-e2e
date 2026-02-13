"""
Environment Manager for socialseed-e2e.
Handles loading, validation, merging, and secrets injection for environment configurations.
"""
import os
import yaml
import json
import logging
import copy
from typing import Dict, Any, Optional, List, Union
from pathlib import Path

from .secrets import SecretProvider, get_secrets_provider
from .validator import validate_config, compare_environments, EnvironmentConfig

logger = logging.getLogger(__name__)

class EnvironmentManager:
    """
    Manages environment configurations, secrets, and validation.
    """
    
    def __init__(self, config_dir: Union[str, Path]):
        self.config_dir = Path(config_dir)
        self.base_config = self._load_yaml("base.yaml")
        self.current_env = None
        self.config = {}
        self.secrets_provider = None

    def _load_yaml(self, filename: str) -> Dict[str, Any]:
        """Load a YAML file from the config directory."""
        file_path = self.config_dir / filename
        if not file_path.exists():
            logger.warning(f"Config file {filename} not found in {self.config_dir}")
            return {}
        try:
            with open(file_path, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Error loading {filename}: {e}")
            return {}

    def load_environment(self, env_name: str) -> Dict[str, Any]:
        """
        Loads the environment configuration by merging base config with environment-specific config.
        Initializes the secrets provider.
        """
        self.current_env = env_name
        env_config = self._load_yaml(f"{env_name}.yaml")
        
        # Merge base with environment
        self.config = self._merge_configs(self.base_config, env_config)
        
        # Inject environment name if missing
        if "environment" not in self.config:
            self.config["environment"] = env_name

        # Validate configuration structure
        try:
            validated_model = validate_config(self.config)
            # Update config with defaults from model (Pydantic v2)
            self.config = validated_model.model_dump()
        except Exception as e:
            logger.error(f"Configuration validation failed for {env_name}: {e}")
            # Depending on severity, we might want to raise, but let's just log for now to allow partial loading
            raise e

        # Initialize secrets
        self._initialize_secrets()
        
        # Inject secrets into configuration placeholders
        self.config = self._inject_secrets(self.config)
        
        return self.config

    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Recursive deep merge of two dictionaries."""
        result = copy.deepcopy(base)
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = copy.deepcopy(value)
        return result

    def _initialize_secrets(self):
        """Initializes the secrets provider based on loaded configuration."""
        secrets_config = self.config.get("secrets", {})
        # Flatten structure if secrets config is nested under a 'secrets' key that was merged
        # The schema in validator.py expects 'secrets' key with provider info.
        
        # We need to construct a config dict that get_secrets_provider understands
        provider_config = {}
        if isinstance(secrets_config, dict):
            provider_config["env_var_prefix"] = secrets_config.get("env_var_prefix", "SOCIALSEED_")
            
            if secrets_config.get("provider") == "vault":
                provider_config["vault"] = {
                    "enabled": True,
                    "url": secrets_config.get("vault_url"),
                    "token": os.environ.get("VAULT_TOKEN"), # Security: Don't put token in config file usually
                    "mount_point": secrets_config.get("vault_mount_point", "secret")
                }
            
            if secrets_config.get("provider") == "aws":
                provider_config["aws_secrets"] = {
                    "enabled": True,
                    "region": secrets_config.get("aws_region", "us-east-1"),
                    "profile": secrets_config.get("aws_profile")
                }
        
        self.secrets_provider = get_secrets_provider(provider_config)

    def _inject_secrets(self, config_fragment: Any) -> Any:
        """
        Recursively replaces placeholders like 'SECRET:key' with actual secret values.
        Also supports '{{ secret.key }}' syntax if we wanted, but let's stick to a prefix or schema.
        Let's use a convention: explicit strings starting with 'SECRET:'.
        """
        if isinstance(config_fragment, dict):
            return {k: self._inject_secrets(v) for k, v in config_fragment.items()}
        elif isinstance(config_fragment, list):
            return [self._inject_secrets(i) for i in config_fragment]
        elif isinstance(config_fragment, str):
            if config_fragment.startswith("SECRET:"):
                secret_key = config_fragment[7:]
                secret_value = self.secrets_provider.get_secret(secret_key)
                if secret_value is None:
                    logger.warning(f"Secret '{secret_key}' not found.")
                    return config_fragment # Return original if not found? Or None?
                return secret_value
        return config_fragment

    def compare_envs(self, env_name_a: str, env_name_b: str) -> Dict[str, Any]:
        """Compares two environment configurations."""
        # Load implicitly without modifying current state if possible, or save/restore state.
        # Simple approach: Create temporary managers or just load raw dicts.
        # We need merged dicts.
        
        # Helper to load merged without state side effects
        def load_merged(name):
            base = self._load_yaml("base.yaml")
            env = self._load_yaml(f"{name}.yaml")
            return self._merge_configs(base, env)
            
        config_a = load_merged(env_name_a)
        config_b = load_merged(env_name_b)
        
        return compare_environments(config_a, config_b)

    def promote_environment(self, source_env: str, target_env: str, dry_run: bool = False):
        """
        Promotes configuration from source to target.
        Effectively copies source_env.yaml content to target_env.yaml, 
        potentially preserving target-specific overrides if logic was more complex.
        For now, a simple overwrite or safe merge promotion logic.
        
        A true promotion usually means: "Take the Artifact/Config version from Source and deploy to Target".
        Here we probably just want to validate that Source is valid, and then update Target config to match specific compatible settings.
        
        Let's implement a safe copy: config that is environment-agnostic is copied.
        """
        if dry_run:
            logger.info(f"[Dry Run] Promoting {source_env} to {target_env}")
            diff = self.compare_envs(source_env, target_env)
            return diff
            
        source_config = self._load_yaml(f"{source_env}.yaml")
        target_config_path = self.config_dir / f"{target_env}.yaml"
        
        # We probably want to keep the target environment's specific "identifiers" (like explicit environment name)
        # but update feature flags, service versions, etc.
        
        # For simplicity in this implementation, we overwrite the target file with source content
        # BUT we ensure the 'environment' key is updated to target_env.
        
        new_target_config = copy.deepcopy(source_config)
        new_target_config["environment"] = target_env
        
        with open(target_config_path, 'w') as f:
            yaml.dump(new_target_config, f)
            
        logger.info(f"Promoted {source_env} to {target_env}")

    def detect_drift(self, external_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compares current loaded config against an external state (e.g. from a live query).
        Returns the diff.
        """
        if not self.config:
            logger.warning("No configuration loaded. Cannot detect drift.")
            return {}
            
        return compare_environments(self.config, external_state)
