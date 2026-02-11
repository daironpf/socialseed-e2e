"""Plugin manager for socialseed-e2e.

This module provides the PluginManager class that handles plugin discovery,
loading, and lifecycle management.

Example:
    >>> from socialseed_e2e.plugins import PluginManager
    >>>
    >>> manager = PluginManager()
    >>> manager.discover_plugins()  # Discover available plugins
    >>> manager.load_all()  # Load all discovered plugins
    >>>
    >>> # Get a specific plugin
    >>> plugin = manager.get_plugin("my-plugin")
    >>>
    >>> # Shutdown all plugins
    >>> manager.unload_all()
"""

import importlib
import importlib.util
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union

from socialseed_e2e.plugins.interfaces import (
    AssertionRegistry,
    HookManager,
    IPlugin,
    PluginContext,
    PluginMetadata,
)

logger = logging.getLogger(__name__)


class PluginError(Exception):
    """Exception raised for plugin-related errors."""

    pass


class PluginNotFoundError(PluginError):
    """Exception raised when a plugin is not found."""

    pass


class PluginLoadError(PluginError):
    """Exception raised when a plugin fails to load."""

    pass


class LoadedPlugin:
    """Represents a loaded plugin instance.

    Attributes:
        metadata: Plugin metadata
        instance: Plugin instance
        context: Plugin context
    """

    def __init__(
        self,
        metadata: PluginMetadata,
        instance: IPlugin,
        context: PluginContext,
    ):
        self.metadata = metadata
        self.instance = instance
        self.context = context
        self._loaded = False

    def load(self) -> None:
        """Load and initialize the plugin."""
        if not self._loaded:
            try:
                self.instance.initialize(self.context.config)
                self._loaded = True
                logger.info(f"Plugin '{self.metadata.name}' loaded successfully")
            except Exception as e:
                raise PluginLoadError(
                    f"Failed to load plugin '{self.metadata.name}': {e}"
                ) from e

    def unload(self) -> None:
        """Unload and cleanup the plugin."""
        if self._loaded:
            try:
                self.instance.shutdown()
                self._loaded = False
                logger.info(f"Plugin '{self.metadata.name}' unloaded")
            except Exception as e:
                logger.error(f"Error unloading plugin '{self.metadata.name}': {e}")

    def is_loaded(self) -> bool:
        """Check if the plugin is loaded."""
        return self._loaded


class PluginManager:
    """Manages plugins for the socialseed-e2e framework.

    Handles plugin discovery, loading, and lifecycle management.

    Attributes:
        plugin_dirs: Directories to search for plugins
        assertion_registry: Registry for custom assertions
        hook_manager: Manager for hooks
        plugins: Dictionary of loaded plugins

    Example:
        >>> manager = PluginManager()
        >>> manager.discover_plugins()  # Auto-discover from default locations
        >>> manager.load_all()
        >>>
        >>> # Or load specific plugins
        >>> manager.load_plugin("my-plugin", metadata, plugin_class)
        >>>
        >>> # Access plugins
        >>> plugin = manager.get_plugin("my-plugin")
        >>>
        >>> # Cleanup
        >>> manager.unload_all()
    """

    # Default plugin directories
    DEFAULT_PLUGIN_DIRS = [
        Path(".e2e/plugins"),
        Path("plugins"),
        Path.home() / ".socialseed-e2e/plugins",
    ]

    def __init__(
        self,
        plugin_dirs: Optional[List[Union[str, Path]]] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the plugin manager.

        Args:
            plugin_dirs: Additional directories to search for plugins
            config: Global configuration for plugins
        """
        self.plugin_dirs: List[Path] = []
        self._add_default_plugin_dirs()

        if plugin_dirs:
            for dir_path in plugin_dirs:
                self.plugin_dirs.append(Path(dir_path))

        self.config = config or {}
        self.assertion_registry = AssertionRegistry()
        self.hook_manager = HookManager()
        self._plugins: Dict[str, LoadedPlugin] = {}
        self._discovered: Dict[str, PluginMetadata] = {}

    def _add_default_plugin_dirs(self) -> None:
        """Add default plugin directories."""
        for dir_path in self.DEFAULT_PLUGIN_DIRS:
            if dir_path.exists():
                self.plugin_dirs.append(dir_path)

    def discover_plugins(self, additional_dirs: Optional[List[Path]] = None) -> int:
        """Discover available plugins.

        Searches for plugin metadata files in plugin directories.

        Args:
            additional_dirs: Additional directories to search

        Returns:
            Number of plugins discovered
        """
        search_dirs = self.plugin_dirs.copy()
        if additional_dirs:
            search_dirs.extend(additional_dirs)

        discovered_count = 0

        for plugin_dir in search_dirs:
            if not plugin_dir.exists():
                continue

            # Look for plugin.json files
            for metadata_file in plugin_dir.rglob("plugin.json"):
                try:
                    metadata = self._load_metadata(metadata_file)
                    if metadata:
                        self._discovered[metadata.name] = metadata
                        discovered_count += 1
                        logger.debug(f"Discovered plugin: {metadata.name}")
                except Exception as e:
                    logger.warning(
                        f"Failed to load plugin metadata from {metadata_file}: {e}"
                    )

            # Also look for Python modules with plugin.py or __init__.py
            for plugin_file in plugin_dir.rglob("plugin.py"):
                try:
                    metadata = self._discover_from_module(plugin_file)
                    if metadata and metadata.name not in self._discovered:
                        self._discovered[metadata.name] = metadata
                        discovered_count += 1
                except Exception as e:
                    logger.debug(f"Could not discover from {plugin_file}: {e}")

        logger.info(f"Discovered {discovered_count} plugins")
        return discovered_count

    def _load_metadata(self, metadata_file: Path) -> Optional[PluginMetadata]:
        """Load plugin metadata from a JSON file.

        Args:
            metadata_file: Path to plugin.json file

        Returns:
            PluginMetadata or None if invalid
        """
        try:
            with open(metadata_file, "r") as f:
                data = json.load(f)
            return PluginMetadata.from_dict(data)
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Invalid plugin metadata in {metadata_file}: {e}")
            return None

    def _discover_from_module(self, module_file: Path) -> Optional[PluginMetadata]:
        """Discover plugin metadata from a Python module.

        Args:
            module_file: Path to plugin.py file

        Returns:
            PluginMetadata or None
        """
        try:
            # Load module
            spec = importlib.util.spec_from_file_location("plugin", module_file)
            if not spec or not spec.loader:
                return None

            module = importlib.util.module_from_spec(spec)
            sys.modules["discovered_plugin"] = module
            spec.loader.exec_module(module)

            # Look for __plugin_metadata__ or plugin class
            if hasattr(module, "__plugin_metadata__"):
                data = module.__plugin_metadata__
                if isinstance(data, dict):
                    return PluginMetadata.from_dict(data)

            # Try to infer from a plugin class
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and hasattr(attr, "name")
                    and hasattr(attr, "version")
                ):
                    return PluginMetadata(
                        name=getattr(attr, "name"),
                        version=getattr(attr, "version"),
                        description=getattr(attr, "description", ""),
                        entry_point=f"{module_file.parent.name}.plugin:{attr_name}",
                    )

            return None
        except Exception as e:
            logger.debug(f"Error discovering from {module_file}: {e}")
            return None

    def load_plugin(
        self,
        name: str,
        metadata: Optional[PluginMetadata] = None,
        plugin_class: Optional[Type[IPlugin]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> LoadedPlugin:
        """Load a plugin by name or with explicit metadata/class.

        Args:
            name: Plugin name
            metadata: Optional plugin metadata
            plugin_class: Optional plugin class
            config: Optional plugin-specific configuration

        Returns:
            LoadedPlugin instance

        Raises:
            PluginNotFoundError: If plugin not found
            PluginLoadError: If plugin fails to load
        """
        if name in self._plugins:
            return self._plugins[name]

        # Use discovered metadata if not provided
        if metadata is None:
            if name not in self._discovered:
                raise PluginNotFoundError(f"Plugin '{name}' not found")
            metadata = self._discovered[name]

        # Load plugin class from entry point if not provided
        if plugin_class is None:
            if not metadata.entry_point:
                raise PluginLoadError(f"Plugin '{name}' has no entry point")
            plugin_class = self._load_plugin_class(metadata.entry_point)

        # Create plugin instance
        try:
            instance = plugin_class()
        except Exception as e:
            raise PluginLoadError(f"Failed to instantiate plugin '{name}': {e}") from e

        # Create context
        context = PluginContext(
            assertion_registry=self.assertion_registry,
            hook_manager=self.hook_manager,
            config=config or self.config.get(name, {}),
        )

        # Create loaded plugin
        loaded = LoadedPlugin(metadata, instance, context)
        loaded.load()

        # Store
        self._plugins[name] = loaded

        # Register with subsystems
        self._register_with_subsystems(loaded)

        return loaded

    def _load_plugin_class(self, entry_point: str) -> Type[IPlugin]:
        """Load a plugin class from an entry point string.

        Args:
            entry_point: Entry point in format "module.path:ClassName"

        Returns:
            Plugin class

        Raises:
            PluginLoadError: If class cannot be loaded
        """
        try:
            if ":" in entry_point:
                module_path, class_name = entry_point.split(":")
            else:
                # Assume it's a module path with a class at the end
                parts = entry_point.split(".")
                module_path = ".".join(parts[:-1])
                class_name = parts[-1]

            # Try to import module
            try:
                module = importlib.import_module(module_path)
            except ImportError:
                # Try loading from plugin directories
                module = self._load_module_from_plugin_dirs(module_path)

            if not hasattr(module, class_name):
                raise PluginLoadError(
                    f"Class '{class_name}' not found in module '{module_path}'"
                )

            plugin_class = getattr(module, class_name)

            if not isinstance(plugin_class, type):
                raise PluginLoadError(f"'{entry_point}' is not a class")

            return plugin_class

        except Exception as e:
            raise PluginLoadError(
                f"Failed to load plugin class '{entry_point}': {e}"
            ) from e

    def _load_module_from_plugin_dirs(self, module_path: str):
        """Load a module from plugin directories.

        Args:
            module_path: Module path

        Returns:
            Loaded module

        Raises:
            ImportError: If module cannot be loaded
        """
        # Convert module path to file path
        parts = module_path.split(".")

        for plugin_dir in self.plugin_dirs:
            # Try as a file
            file_path = plugin_dir / "/".join(parts) + ".py"
            if file_path.exists():
                spec = importlib.util.spec_from_file_location(module_path, file_path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_path] = module
                    spec.loader.exec_module(module)
                    return module

            # Try as a package
            init_file = plugin_dir / "/".join(parts) / "__init__.py"
            if init_file.exists():
                spec = importlib.util.spec_from_file_location(module_path, init_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_path] = module
                    spec.loader.exec_module(module)
                    return module

        raise ImportError(f"Cannot find module '{module_path}' in plugin directories")

    def _register_with_subsystems(self, loaded: LoadedPlugin) -> None:
        """Register a loaded plugin with framework subsystems.

        Args:
            loaded: Loaded plugin
        """
        instance = loaded.instance

        # Register assertions
        if hasattr(instance, "register_assertions"):
            try:
                instance.register_assertions(self.assertion_registry)
            except Exception as e:
                logger.warning(
                    f"Plugin '{loaded.metadata.name}' failed to register assertions: {e}"
                )

        # Register hooks
        if hasattr(instance, "register_hooks"):
            try:
                instance.register_hooks(self.hook_manager)
            except Exception as e:
                logger.warning(
                    f"Plugin '{loaded.metadata.name}' failed to register hooks: {e}"
                )

    def load_all(self, config: Optional[Dict[str, Dict[str, Any]]] = None) -> int:
        """Load all discovered plugins.

        Args:
            config: Configuration dictionary mapping plugin names to configs

        Returns:
            Number of plugins loaded
        """
        loaded_count = 0

        for name, metadata in self._discovered.items():
            if name not in self._plugins:
                try:
                    plugin_config = config.get(name, {}) if config else None
                    self.load_plugin(name, metadata=metadata, config=plugin_config)
                    loaded_count += 1
                except Exception as e:
                    logger.error(f"Failed to load plugin '{name}': {e}")

        logger.info(f"Loaded {loaded_count} plugins")
        return loaded_count

    def unload_plugin(self, name: str) -> None:
        """Unload a specific plugin.

        Args:
            name: Plugin name
        """
        if name in self._plugins:
            self._plugins[name].unload()
            del self._plugins[name]

    def unload_all(self) -> None:
        """Unload all loaded plugins."""
        for name in list(self._plugins.keys()):
            self.unload_plugin(name)
        logger.info("All plugins unloaded")

    def get_plugin(self, name: str) -> Optional[IPlugin]:
        """Get a loaded plugin instance.

        Args:
            name: Plugin name

        Returns:
            Plugin instance or None if not loaded
        """
        loaded = self._plugins.get(name)
        return loaded.instance if loaded else None

    def get_loaded_plugin(self, name: str) -> Optional[LoadedPlugin]:
        """Get a loaded plugin wrapper.

        Args:
            name: Plugin name

        Returns:
            LoadedPlugin or None
        """
        return self._plugins.get(name)

    def list_discovered(self) -> List[str]:
        """List all discovered plugin names."""
        return list(self._discovered.keys())

    def list_loaded(self) -> List[str]:
        """List all loaded plugin names."""
        return list(self._plugins.keys())

    def is_loaded(self, name: str) -> bool:
        """Check if a plugin is loaded."""
        return name in self._plugins and self._plugins[name].is_loaded()

    def get_metadata(self, name: str) -> Optional[PluginMetadata]:
        """Get metadata for a discovered or loaded plugin.

        Args:
            name: Plugin name

        Returns:
            PluginMetadata or None
        """
        if name in self._discovered:
            return self._discovered[name]
        if name in self._plugins:
            return self._plugins[name].metadata
        return None


# Convenience function for quick plugin loading
def load_plugin(
    entry_point: str,
    config: Optional[Dict[str, Any]] = None,
) -> IPlugin:
    """Load a plugin by entry point.

    This is a convenience function for loading a single plugin without
    creating a PluginManager instance.

    Args:
        entry_point: Plugin entry point (e.g., "myplugin:MyPlugin")
        config: Optional plugin configuration

    Returns:
        Loaded plugin instance

    Example:
        >>> from socialseed_e2e.plugins import load_plugin
        >>> plugin = load_plugin("myplugin:MyReporter")
        >>> plugin.initialize()
    """
    manager = PluginManager()

    # Create temporary metadata
    if ":" in entry_point:
        name = entry_point.split(":")[-1]
    else:
        name = entry_point.split(".")[-1]

    metadata = PluginMetadata(
        name=name,
        version="0.0.0",
        entry_point=entry_point,
    )

    loaded = manager.load_plugin(name, metadata=metadata, config=config)
    return loaded.instance


__all__ = [
    "PluginManager",
    "LoadedPlugin",
    "PluginError",
    "PluginNotFoundError",
    "PluginLoadError",
    "load_plugin",
]
