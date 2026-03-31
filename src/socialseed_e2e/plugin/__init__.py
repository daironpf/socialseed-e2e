"""
Plugin System - EPIC-017
Extensible plugin architecture for socialseed-e2e.
"""

from .core import (
    Plugin,
    PluginContext,
    PluginHook,
    PluginManager,
    PluginMetadata,
    PluginType,
    get_plugin_manager,
)

__all__ = [
    "Plugin",
    "PluginContext",
    "PluginHook",
    "PluginManager",
    "PluginMetadata",
    "PluginType",
    "get_plugin_manager",
]
