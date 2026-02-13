"""
Secrets management module for socialseed-e2e environments.
Supports multiple secret providers: Environment Variables, HashiCorp Vault, and AWS Secrets Manager.
"""
import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

class SecretProvider(ABC):
    """Abstract base class for secret providers."""

    @abstractmethod
    def get_secret(self, key: str) -> Optional[str]:
        """Retrieve a single secret value by key."""
        pass

    @abstractmethod
    def get_all_secrets(self, path: Optional[str] = None) -> Dict[str, Any]:
        """Retrieve all secrets from a given path or context."""
        pass

class EnvironmentVariableSecretProvider(SecretProvider):
    """Provider that retrieves secrets from environment variables."""

    def __init__(self, prefix: str = "SOCIALSEED_"):
        self.prefix = prefix

    def get_secret(self, key: str) -> Optional[str]:
        env_key = f"{self.prefix}{key.upper()}"
        return os.environ.get(env_key)

    def get_all_secrets(self, path: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns all environment variables starting with the prefix.
        The path argument is ignored.
        """
        secrets = {}
        for k, v in os.environ.items():
            if k.startswith(self.prefix):
                # Remove prefix and convert to lowercase for the key
                clean_key = k[len(self.prefix):].lower()
                secrets[clean_key] = v
        return secrets

class VaultSecretProvider(SecretProvider):
    """Provider that retrieves secrets from HashiCorp Vault."""
    
    def __init__(self, url: str, token: str, mount_point: str = "secret"):
        try:
            import hvac # type: ignore
        except ImportError:
            raise ImportError("hvac library is required for VaultSecretProvider. Install with pip install hvac")
        
        self.client = hvac.Client(url=url, token=token)
        self.mount_point = mount_point
        if not self.client.is_authenticated():
            logger.warning("Vault client is not authenticated.")

    def get_secret(self, key: str) -> Optional[str]:
        # This implementation assumes a specific path structure like secret/socialseed/key is not feasible for single key lookup
        # unless 'key' is a path. Let's assume key is a path to a secret engine entry.
        # Alternatively, we can assume a default path and key is a key within that path.
        # For simplicity, we'll try to read from a default path defined in constructor if available?
        # Actually, let's treat 'key' as 'path/to/secret:key_inside' or just 'path/to/secret'
        
        # Simply implement reading a specific path
        try:
            if ":" in key:
                path, specific_key = key.split(":", 1)
                response = self.client.secrets.kv.v2.read_secret_version(path=path, mount_point=self.mount_point)
                return response['data']['data'].get(specific_key)
            else:
                # Return the whole JSON string if just path provided? Or None?
                # Better: Assume key is just the name of the secret at a base path context?
                # Let's stick to explicit path:key for get_secret
                return None
        except Exception as e:
            logger.error(f"Error reading secret from Vault: {e}")
            return None

    def get_all_secrets(self, path: Optional[str] = None) -> Dict[str, Any]:
        if not path:
            return {}
        try:
            response = self.client.secrets.kv.v2.read_secret_version(path=path, mount_point=self.mount_point)
            return response['data']['data']
        except Exception as e:
            logger.error(f"Error reading secrets from Vault path {path}: {e}")
            return {}

class AWSSecretManagerProvider(SecretProvider):
    """Provider that retrieves secrets from AWS Secrets Manager."""

    def __init__(self, region_name: str = "us-east-1", profile_name: Optional[str] = None):
        try:
            import boto3 # type: ignore
            from botocore.exceptions import ClientError # type: ignore
        except ImportError:
            raise ImportError("boto3 library is required for AWSSecretManagerProvider. Install with pip install boto3")
        
        session = boto3.Session(profile_name=profile_name)
        self.client = session.client(service_name='secretsmanager', region_name=region_name)

    def get_secret(self, key: str) -> Optional[str]:
        """
        Retrieves a secret value. 
        If strict key match fails, it tries to parse the value as JSON and return a specific key if requested.
        """
        try:
            # Check if key implies a JSON lookup like "secret_name:json_key"
            secret_name = key
            json_key = None
            if ":" in key:
                secret_name, json_key = key.split(":", 1)

            get_secret_value_response = self.client.get_secret_value(SecretId=secret_name)
            
            if 'SecretString' in get_secret_value_response:
                secret = get_secret_value_response['SecretString']
                if json_key:
                    try:
                        secret_dict = json.loads(secret)
                        return secret_dict.get(json_key)
                    except json.JSONDecodeError:
                        logger.warning(f"Secret {secret_name} is not valid JSON, cannot extract {json_key}")
                        return None
                return secret
            return None
        except Exception as e:
            logger.error(f"Error retrieving secret {key} from AWS Secrets Manager: {e}")
            return None

    def get_all_secrets(self, path: Optional[str] = None) -> Dict[str, Any]:
        """
        For AWS, 'path' is interpreted as the SecretId.
        Returns the parsed JSON dictionary of the secret.
        """
        if not path:
            return {}
        try:
            val = self.get_secret(path)
            if val:
                try:
                    return json.loads(val)
                except json.JSONDecodeError:
                    return {"value": val}
            return {}
        except Exception:
            return {}

class CompositeSecretProvider(SecretProvider):
    """
    Chains multiple providers. Returns the first found secret.
    """
    def __init__(self, providers: List[SecretProvider]):
        self.providers = providers

    def get_secret(self, key: str) -> Optional[str]:
        for provider in self.providers:
            val = provider.get_secret(key)
            if val is not None:
                return val
        return None

    def get_all_secrets(self, path: Optional[str] = None) -> Dict[str, Any]:
        """
        Merges secrets from all providers. 
        Providers later in the list overwrite earlier ones (or preserve earlier? Standard is "priority first").
        Actually, usually first provider is highest priority.
        So we should iterate in reverse if we are 'merging' into a dict, so that the first provider (last loaded) wins.
        """
        combined_secrets = {}
        # Iterate in reverse order so that higher priority (earlier in list) updates/overwrites lower priority
        for provider in reversed(self.providers):
            combined_secrets.update(provider.get_all_secrets(path))
        return combined_secrets

def get_secrets_provider(config: Dict[str, Any]) -> SecretProvider:
    """Factory to create a secret provider based on configuration."""
    providers = []
    
    # Always include Env Vars (Highest priority? or lowest? usually highest override)
    # Let's say Env Vars are highest priority for local overrides.
    providers.append(EnvironmentVariableSecretProvider(prefix=config.get("env_var_prefix", "SOCIALSEED_")))
    
    vault_config = config.get("vault")
    if vault_config and vault_config.get("enabled"):
        try:
            providers.append(VaultSecretProvider(
                url=vault_config.get("url"),
                token=vault_config.get("token"), # Should be passed safely
                mount_point=vault_config.get("mount_point", "secret")
            ))
        except ImportError:
            logger.warning("Vault provider enabled but hvac not installed.")

    aws_config = config.get("aws_secrets")
    if aws_config and aws_config.get("enabled"):
        try:
            providers.append(AWSSecretManagerProvider(
                region_name=aws_config.get("region", "us-east-1"),
                profile_name=aws_config.get("profile")
            ))
        except ImportError:
            logger.warning("AWS Secrets Manager provider enabled but boto3 not installed.")
            
    return CompositeSecretProvider(providers)
