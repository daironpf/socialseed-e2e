"""Configuration migration system for socialseed-e2e.

This module provides automatic configuration migration between framework versions,
ensuring backward compatibility and smooth upgrades.

Usage:
    from socialseed_e2e.core.config_migration import ConfigMigrator
    
    migrator = ConfigMigrator()
    migrated_config = migrator.migrate_if_needed(config_path)
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

logger = logging.getLogger(__name__)

CURRENT_VERSION = "1.0.0"
VERSION_FIELD = "_e2e_version"


@dataclass
class MigrationStep:
    """Represents a single migration step."""
    from_version: str
    to_version: str
    name: str
    migrate_func: Callable[[Dict[str, Any]], Dict[str, Any]]


class ConfigMigrationError(Exception):
    """Error during configuration migration."""
    pass


class ConfigMigrator:
    """
    Manages configuration file migrations between framework versions.
    
    The migrator detects the current config version and applies
    necessary transformations to upgrade to the latest version.
    
    Usage:
        migrator = ConfigMigrator()
        if migrator.needs_migration(config_path):
            migrator.migrate(config_path)
    """
    
    def __init__(self):
        self._migration_steps: List[MigrationStep] = []
        self._register_migrations()
    
    def _register_migrations(self) -> None:
        """Register all migration steps."""
        self._migration_steps = [
            MigrationStep(
                from_version="0.0.0",
                to_version="0.1.0",
                name="initial_version",
                migrate_func=self._migrate_0_0_0_to_0_1_0
            ),
            MigrationStep(
                from_version="0.1.0",
                to_version="0.2.0",
                name="add_reporting_config",
                migrate_func=self._migrate_0_1_0_to_0_2_0
            ),
            MigrationStep(
                from_version="0.2.0",
                to_version="0.3.0",
                name="add_parallel_config",
                migrate_func=self._migrate_0_2_0_to_0_3_0
            ),
            MigrationStep(
                from_version="0.3.0",
                to_version="0.4.0",
                name="add_security_config",
                migrate_func=self._migrate_0_3_0_to_0_4_0
            ),
            MigrationStep(
                from_version="0.4.0",
                to_version="0.5.0",
                name="add_health_defaults",
                migrate_func=self._migrate_0_4_0_to_0_5_0
            ),
            MigrationStep(
                from_version="0.5.0",
                to_version="1.0.0",
                name="restructure_to_sections",
                migrate_func=self._migrate_0_5_0_to_1_0_0
            ),
        ]
    
    def get_version(self, config_data: Dict[str, Any]) -> str:
        """Extract version from config data."""
        if VERSION_FIELD in config_data:
            return config_data[VERSION_FIELD]
        
        if "general" in config_data and "version" in config_data["general"]:
            return config_data["general"]["version"]
        
        if "settings" in config_data and "version" in config_data["settings"]:
            return config_data["settings"]["version"]
        
        return "0.0.0"
    
    def set_version(self, config_data: Dict[str, Any], version: str) -> Dict[str, Any]:
        """Set version in config data."""
        config_data[VERSION_FIELD] = version
        return config_data
    
    def needs_migration(self, config_path: Path) -> bool:
        """Check if config file needs migration."""
        try:
            config_data = self._load_config(config_path)
            current_version = self.get_version(config_data)
            return current_version != CURRENT_VERSION
        except Exception as e:
            logger.warning(f"Could not check migration status: {e}")
            return False
    
    def _load_config(self, config_path: Path) -> Dict[str, Any]:
        """Load config file as dict."""
        try:
            content = config_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            content = config_path.read_text(encoding='latin-1')
        
        try:
            import yaml
            return yaml.safe_load(content) or {}
        except ImportError:
            import json
            return json.loads(content)
    
    def _save_config(self, config_path: Path, config_data: Dict[str, Any]) -> None:
        """Save config dict to file."""
        try:
            content = config_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            content = config_path.read_text(encoding='latin-1')
        
        try:
            import yaml
            output = yaml.dump(config_data, default_flow_style=False, sort_keys=False)
        except ImportError:
            import json
            output = json.dumps(config_data, indent=2)
        
        try:
            config_path.write_text(output, encoding='utf-8')
        except UnicodeDecodeError:
            config_path.write_text(output, encoding='latin-1')
    
    def migrate(self, config_path: Path, dry_run: bool = False) -> Dict[str, Any]:
        """
        Migrate config file to current version.
        
        Args:
            config_path: Path to config file
            dry_run: If True, don't actually modify the file
            
        Returns:
            Migrated config data
            
        Raises:
            ConfigMigrationError: If migration fails
        """
        if not config_path.exists():
            raise ConfigMigrationError(f"Config file not found: {config_path}")
        
        try:
            config_data = self._load_config(config_path)
        except Exception as e:
            raise ConfigMigrationError(f"Failed to load config: {e}")
        
        current_version = self.get_version(config_data)
        
        if current_version == CURRENT_VERSION:
            logger.info("Config is already at current version")
            return config_data
        
        logger.info(f"Migrating config from {current_version} to {CURRENT_VERSION}")
        
        migration_chain = self._get_migration_chain(current_version, CURRENT_VERSION)
        
        if not migration_chain:
            logger.warning(f"No migration path from {current_version} to {CURRENT_VERSION}")
            return config_data
        
        for step in migration_chain:
            logger.info(f"Applying migration: {step.name} ({step.from_version} -> {step.to_version})")
            config_data = step.migrate_func(config_data)
            config_data = self.set_version(config_data, step.to_version)
        
        if not dry_run:
            self._save_config(config_path, config_data)
            logger.info(f"Config migrated to version {CURRENT_VERSION}")
        
        return config_data
    
    def _get_migration_chain(self, from_version: str, to_version: str) -> List[MigrationStep]:
        """Get ordered list of migrations to apply."""
        chain = []
        
        current = from_version
        while self._version_lt(current, to_version):
            next_step = None
            for step in self._migration_steps:
                if step.from_version == current:
                    next_step = step
                    break
            
            if next_step is None:
                break
                
            chain.append(next_step)
            current = next_step.to_version
        
        return chain
    
    def _version_gte(self, v1: str, v2: str) -> bool:
        """Check if v1 >= v2."""
        return self._compare_versions(v1, v2) >= 0
    
    def _version_lt(self, v1: str, v2: str) -> bool:
        """Check if v1 < v2."""
        return self._compare_versions(v1, v2) < 0
    
    def _compare_versions(self, v1: str, v2: str) -> int:
        """Compare two version strings."""
        parts1 = [int(p) for p in v1.split(".")]
        parts2 = [int(p) for p in v2.split(".")]
        
        max_len = max(len(parts1), len(parts2))
        parts1.extend([0] * (max_len - len(parts1)))
        parts2.extend([0] * (max_len - len(parts2)))
        
        for p1, p2 in zip(parts1, parts2):
            if p1 > p2:
                return 1
            elif p1 < p2:
                return -1
        return 0
    
    def _migrate_0_0_0_to_0_1_0(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Migration from 0.0.0 to 0.1.0 - Add initial version field."""
        if VERSION_FIELD not in config:
            config[VERSION_FIELD] = "0.1.0"
        
        if "timeout" in config and "general" not in config:
            config["general"] = {
                "timeout": config.pop("timeout", 30000),
                "environment": "dev"
            }
        
        return config
    
    def _migrate_0_1_0_to_0_2_0(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Migration from 0.1.0 to 0.2.0 - Add reporting config."""
        if "reporting" not in config:
            config["reporting"] = {
                "format": "console",
                "save_logs": True,
                "log_dir": "./logs"
            }
        
        return config
    
    def _migrate_0_2_0_to_0_3_0(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Migration from 0.2.0 to 0.3.0 - Add parallel config."""
        if "parallel" not in config:
            config["parallel"] = {
                "enabled": False,
                "max_workers": None,
                "mode": "service"
            }
        
        return config
    
    def _migrate_0_3_0_to_0_4_0(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Migration from 0.3.0 to 0.4.0 - Add security config."""
        if "security" not in config:
            config["security"] = {
                "verify_ssl": True
            }
        
        return config
    
    def _migrate_0_4_0_to_0_5_0(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Migration from 0.4.0 to 0.5.0 - Add health defaults to services."""
        services = config.get("services", {})
        
        for service_name, service_config in services.items():
            if isinstance(service_config, dict):
                if "health_endpoint" not in service_config:
                    service_config["health_endpoint"] = "/actuator/health"
                if "timeout" not in service_config:
                    service_config["timeout"] = 30000
                if "required" not in service_config:
                    service_config["required"] = True
        
        return config
    
    def _migrate_0_5_0_to_1_0_0(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Migration from 0.5.0 to 1.0.0 - Restructure to use general/settings sections."""
        if "general" not in config:
            general_keys = ["environment", "timeout", "user_agent", "verbose"]
            general = {}
            
            for key in general_keys:
                if key in config:
                    general[key] = config.pop(key)
            
            config["general"] = general
        
        if "settings" not in config:
            config["settings"] = {
                "verification_level": "strict",
                "project_version": "1.0.0"
            }
        
        if "services" in config:
            for name, svc in config["services"].items():
                if isinstance(svc, dict):
                    if "auto_start" not in svc:
                        svc["auto_start"] = False
        
        return config
    
    def get_migration_info(self, config_path: Path) -> Dict[str, Any]:
        """Get migration information for a config file."""
        try:
            config_data = self._load_config(config_path)
            current_version = self.get_version(config_data)
            
            return {
                "path": str(config_path),
                "current_version": current_version,
                "target_version": CURRENT_VERSION,
                "needs_migration": current_version != CURRENT_VERSION,
                "migration_path": [
                    {"from": s.from_version, "to": s.to_version, "name": s.name}
                    for s in self._get_migration_chain(current_version, CURRENT_VERSION)
                ]
            }
        except Exception as e:
            return {
                "path": str(config_path),
                "error": str(e),
                "needs_migration": True
            }


def migrate_config_if_needed(config_path: Optional[Path] = None) -> bool:
    """
    Convenience function to migrate config if needed.
    
    Args:
        config_path: Path to config file. If None, searches for e2e.conf
        
    Returns:
        True if migration was performed or not needed
    """
    if config_path is None:
        config_path = Path.cwd() / "e2e.conf"
    
    if not config_path.exists():
        logger.warning(f"Config file not found: {config_path}")
        return False
    
    migrator = ConfigMigrator()
    
    if not migrator.needs_migration(config_path):
        logger.info("Config is up to date")
        return False
    
    try:
        migrator.migrate(config_path)
        return True
    except ConfigMigrationError as e:
        logger.error(f"Migration failed: {e}")
        return False
