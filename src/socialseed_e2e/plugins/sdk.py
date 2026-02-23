"""Plugin SDK for creating custom plugins.

This module provides the SDK for creating plugins including
lifecycle management, configuration handling, and utilities.
"""

import json
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .interfaces import IPlugin, PluginContext, PluginMetadata


class PluginLifecycle(str, Enum):
    """Plugin lifecycle states."""

    DISCOVERED = "discovered"
    LOADED = "loaded"
    INITIALIZED = "initialized"
    ACTIVE = "active"
    FAILED = "failed"
    DISABLED = "disabled"


class PluginConfig:
    """Plugin configuration handler."""

    def __init__(self, plugin_id: str, config_path: Optional[str] = None):
        """Initialize plugin config.

        Args:
            plugin_id: Unique plugin identifier
            config_path: Path to config file
        """
        self.plugin_id = plugin_id
        self.config_path = config_path
        self._config: Dict[str, Any] = {}

    def load(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if self.config_path and Path(self.config_path).exists():
            self._config = json.loads(Path(self.config_path).read_text())
        return self._config

    def save(self, config: Dict[str, Any]):
        """Save configuration to file."""
        self._config = config
        if self.config_path:
            Path(self.config_path).write_text(json.dumps(config, indent=2))

    def get(self, key: str, default: Any = None) -> Any:
        """Get config value."""
        return self._config.get(key, default)

    def set(self, key: str, value: Any):
        """Set config value."""
        self._config[key] = value


class PluginSDK:
    """SDK for creating plugins."""

    def __init__(self):
        """Initialize plugin SDK."""
        self._hooks: Dict[str, List[Callable]] = {}
        self._assertions: Dict[str, Callable] = {}
        self._reporters: Dict[str, Any] = {}

    def register_hook(self, event: str, callback: Callable):
        """Register a hook callback.

        Args:
            event: Event name
            callback: Callback function
        """
        if event not in self._hooks:
            self._hooks[event] = []
        self._hooks[event].append(callback)

    def register_assertion(self, name: str, assertion_fn: Callable):
        """Register a custom assertion.

        Args:
            name: Assertion name
            assertion_fn: Assertion function
        """
        self._assertions[name] = assertion_fn

    def register_reporter(self, name: str, reporter_class: Any):
        """Register a custom reporter.

        Args:
            name: Reporter name
            reporter_class: Reporter class
        """
        self._reporters[name] = reporter_class

    def emit_hook(self, event: str, *args, **kwargs):
        """Emit a hook event.

        Args:
            event: Event name
            *args: Positional arguments
            **kwargs: Keyword arguments
        """
        if event in self._hooks:
            for callback in self._hooks[event]:
                callback(*args, **kwargs)

    def get_assertions(self) -> Dict[str, Callable]:
        """Get all registered assertions."""
        return self._assertions

    def get_reporters(self) -> Dict[str, Any]:
        """Get all registered reporters."""
        return self._reporters


class BasePlugin(IPlugin):
    """Base class for plugins with common functionality."""

    def __init__(self):
        """Initialize base plugin."""
        self._config: Optional[PluginConfig] = None
        self._sdk: Optional[PluginSDK] = None
        self._state: PluginLifecycle = PluginLifecycle.DISCOVERED

    @property
    def name(self) -> str:
        """Plugin name."""
        return self.__class__.__name__.lower()

    @property
    def version(self) -> str:
        """Plugin version."""
        return "1.0.0"

    @property
    def description(self) -> str:
        """Plugin description."""
        return "A custom plugin"

    @property
    def author(self) -> str:
        """Plugin author."""
        return "Unknown"

    @property
    def metadata(self) -> PluginMetadata:
        """Plugin metadata."""
        return PluginMetadata(
            name=self.name,
            version=self.version,
            description=self.description,
            author=self.author,
            hooks=[],
            assertions=[],
            dependencies=[],
        )

    def initialize(self, context: PluginContext) -> bool:
        """Initialize the plugin.

        Args:
            context: Plugin context

        Returns:
            True if initialization successful
        """
        self._config = PluginConfig(self.name)
        self._config.load()
        self._sdk = PluginSDK()
        self._state = PluginLifecycle.INITIALIZED
        return True

    def shutdown(self):
        """Shutdown the plugin."""
        self._state = PluginLifecycle.DISABLED

    def get_config(self) -> Optional[PluginConfig]:
        """Get plugin configuration."""
        return self._config

    def get_sdk(self) -> Optional[PluginSDK]:
        """Get plugin SDK."""
        return self._sdk


class PluginValidator:
    """Validate plugin structure and requirements."""

    @staticmethod
    def validate(plugin: IPlugin) -> List[str]:
        """Validate a plugin.

        Args:
            plugin: Plugin to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        if not plugin.name:
            errors.append("Plugin must have a name")

        if not plugin.version:
            errors.append("Plugin must have a version")

        if not hasattr(plugin, "initialize") or not callable(
            plugin.initialize
        ):
            errors.append("Plugin must have an initialize method")

        if not hasattr(plugin, "shutdown") or not callable(plugin.shutdown):
            errors.append("Plugin must have a shutdown method")

        return errors

    @staticmethod
    def check_dependencies(plugin: IPlugin, available_plugins: List[str]) -> List[str]:
        """Check if plugin dependencies are available.

        Args:
            plugin: Plugin to check
            available_plugins: List of available plugin names

        Returns:
            List of missing dependencies
        """
        metadata = plugin.metadata
        missing = []

        for dep in metadata.dependencies:
            if dep not in available_plugins:
                missing.append(dep)

        return missing
