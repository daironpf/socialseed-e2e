"""Plugin system for socialseed-e2e.

This module provides a plugin architecture that allows users to extend
the framework with custom functionality.

Quick Start:
    >>> from socialseed_e2e.plugins import PluginManager, IPlugin
    >>>
    >>> # Create a plugin
    >>> class MyPlugin(IPlugin):
    ...     name = "my-plugin"
    ...     version = "1.0.0"
    ...     description = "My custom plugin"
    ...
    ...     def initialize(self, config=None):
    ...         print(f"Plugin {self.name} initialized!")
    ...
    ...     def shutdown(self):
    ...         print(f"Plugin {self.name} shutdown!")
    >>>
    >>> # Load and use
    >>> manager = PluginManager()
    >>> manager.load_plugin("my-plugin", plugin_class=MyPlugin)
"""

from socialseed_e2e.plugins.interfaces import (
    AssertionRegistry,
    Hook,
    HookManager,
    IAssertionPlugin,
    IDataSourcePlugin,
    IHookPlugin,
    IPlugin,
    ITestReporterPlugin,
    PluginContext,
    PluginMetadata,
)
from socialseed_e2e.plugins.manager import (
    LoadedPlugin,
    PluginError,
    PluginLoadError,
    PluginManager,
    PluginNotFoundError,
    load_plugin,
)

__all__ = [
    # Interfaces
    "IPlugin",
    "ITestReporterPlugin",
    "IAssertionPlugin",
    "IDataSourcePlugin",
    "IHookPlugin",
    "PluginMetadata",
    "PluginContext",
    # Subsystems
    "AssertionRegistry",
    "Hook",
    "HookManager",
    # Manager
    "PluginManager",
    "LoadedPlugin",
    "PluginError",
    "PluginNotFoundError",
    "PluginLoadError",
    "load_plugin",
]
