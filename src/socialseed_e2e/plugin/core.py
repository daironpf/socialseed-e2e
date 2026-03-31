"""
Plugin System - EPIC-017
Extensible plugin architecture for socialseed-e2e.
"""

import importlib
import importlib.util
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type

from pydantic import BaseModel


class PluginType(str, Enum):
    """Types of plugins."""
    INTERCEPTOR = "interceptor"
    GENERATOR = "generator"
    NOTIFIER = "notifier"
    ANALYZER = "analyzer"
    UI_COMPONENT = "ui_component"
    CUSTOM = "custom"


class PluginHook(str, Enum):
    """Plugin lifecycle hooks."""
    ON_REQUEST_CAPTURED = "on_request_captured"
    ON_RESPONSE_RECEIVED = "on_response_received"
    ON_TEST_GENERATED = "on_test_generated"
    ON_ALERT_TRIGGERED = "on_alert_triggered"
    ON_DASHBOARD_READY = "on_dashboard_ready"
    ON_STARTUP = "on_startup"
    ON_SHUTDOWN = "on_shutdown"


@dataclass
class PluginMetadata:
    """Plugin metadata."""
    name: str
    version: str
    plugin_type: PluginType
    description: str = ""
    author: str = ""
    homepage: str = ""
    dependencies: List[str] = field(default_factory=list)


class Plugin(ABC):
    """Base class for plugins."""
    
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        pass
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the plugin."""
        pass
    
    @abstractmethod
    def shutdown(self) -> None:
        """Clean up resources."""
        pass
    
    def on_hook(self, hook: PluginHook, callback: Callable) -> None:
        """Register a hook callback."""
        pass


@dataclass
class PluginContext:
    """Context passed to plugins."""
    config: Dict[str, Any]
    workspace_root: Path
    services: Dict[str, str] = field(default_factory=dict)


class PluginManager:
    """Manages plugin lifecycle and hooks."""
    
    def __init__(self, plugin_dir: Optional[Path] = None):
        self.plugin_dir = plugin_dir or Path.home() / ".socialseed" / "plugins"
        self._plugins: Dict[str, Plugin] = {}
        self._hooks: Dict[PluginHook, List[Callable]] = {
            hook: [] for hook in PluginHook
        }
        self._context: Optional[PluginContext] = None
    
    def set_context(self, context: PluginContext) -> None:
        """Set the plugin context."""
        self._context = context
    
    def register_hook(self, hook: PluginHook, callback: Callable) -> None:
        """Register a hook callback."""
        self._hooks[hook].append(callback)
    
    def trigger_hook(self, hook: PluginHook, *args, **kwargs) -> List[Any]:
        """Trigger all callbacks for a hook."""
        results = []
        for callback in self._hooks.get(hook, []):
            try:
                result = callback(*args, **kwargs)
                results.append(result)
            except Exception as e:
                print(f"Hook {hook.value} failed: {e}")
        return results
    
    def load_plugin(self, plugin: Plugin) -> None:
        """Load a plugin."""
        metadata = plugin.metadata
        self._plugins[metadata.name] = plugin
        
        if self._context:
            plugin.initialize(self._context.config)
    
    def unload_plugin(self, name: str) -> bool:
        """Unload a plugin."""
        if name in self._plugins:
            plugin = self._plugins[name]
            plugin.shutdown()
            del self._plugins[name]
            return True
        return False
    
    def get_plugin(self, name: str) -> Optional[Plugin]:
        """Get a plugin by name."""
        return self._plugins.get(name)
    
    def list_plugins(self) -> List[Dict[str, Any]]:
        """List all loaded plugins."""
        return [
            {
                "name": p.metadata.name,
                "version": p.metadata.version,
                "type": p.metadata.plugin_type.value,
                "description": p.metadata.description,
            }
            for p in self._plugins.values()
        ]
    
    def load_from_file(self, plugin_path: Path) -> Optional[Plugin]:
        """Load a plugin from a Python file."""
        try:
            spec = importlib.util.spec_from_file_location("plugin_module", plugin_path)
            if not spec or not spec.loader:
                return None
            
            module = importlib.util.module_from_spec(spec)
            sys.modules["plugin_module"] = module
            spec.loader.exec_module(module)
            
            for name in dir(module):
                obj = getattr(module, name)
                if isinstance(obj, type) and issubclass(obj, Plugin) and obj != Plugin:
                    plugin = obj()
                    self.load_plugin(plugin)
                    return plugin
                    
        except Exception as e:
            print(f"Failed to load plugin from {plugin_path}: {e}")
        
        return None
    
    def discover_plugins(self) -> List[Path]:
        """Discover plugins in the plugin directory."""
        if not self.plugin_dir.exists():
            return []
        
        plugins = []
        for file in self.plugin_dir.glob("*.py"):
            if file.stem != "__init__":
                plugins.append(file)
        
        return plugins


_global_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """Get global plugin manager."""
    global _global_manager
    if _global_manager is None:
        _global_manager = PluginManager()
    return _global_manager
