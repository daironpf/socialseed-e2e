"""Plugin system for socialseed-e2e.

This module provides a plugin architecture that allows users to extend
the framework with custom functionality.

Quick Start:
    >>> from socialseed_e2e.plugins import PluginManager, IPlugin, PluginSDK, BasePlugin
    >>>
    >>> # Create a plugin
    >>> class MyPlugin(BasePlugin):
    ...     @property
    ...     def name(self): return "my-plugin"
    ...     @property
    ...     def version(self): return "1.0.0"
    ...     @property
    ...     def description(self): return "My custom plugin"
    ...
    >>> # Use SDK to register hooks/assertions
    >>> sdk = PluginSDK()
    >>> sdk.register_hook("before_test", my_callback)
    >>> sdk.register_assertion("my_assertion", my_assertion_fn)
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
from socialseed_e2e.plugins.marketplace import (
    PluginInstaller,
    PluginListing,
    PluginMarketplace,
)
from socialseed_e2e.plugins.sdk import (
    BasePlugin,
    PluginConfig,
    PluginLifecycle,
    PluginSDK,
    PluginValidator,
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
    # SDK
    "PluginLifecycle",
    "PluginConfig",
    "PluginSDK",
    "BasePlugin",
    "PluginValidator",
    # Marketplace
    "PluginListing",
    "PluginMarketplace",
    "PluginInstaller",
]
