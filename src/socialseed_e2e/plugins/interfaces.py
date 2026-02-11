"""Plugin system for socialseed-e2e.

This module provides a plugin architecture that allows users to extend
the framework with custom functionality.

Example:
    >>> from socialseed_e2e.plugins import PluginManager
    >>>
    >>> # Discover and load plugins
    >>> manager = PluginManager()
    >>> manager.discover_plugins()
    >>> manager.load_all()
    >>>
    >>> # Use a plugin
    >>> reporter = manager.get_plugin("custom-reporter")
    >>> reporter.generate_report()
"""

from typing import Any, Callable, Dict, List, Optional, Protocol, runtime_checkable


@runtime_checkable
class IPlugin(Protocol):
    """Protocol that all plugins must implement."""

    name: str
    version: str
    description: str

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the plugin with optional configuration."""
        ...

    def shutdown(self) -> None:
        """Clean up resources when the plugin is unloaded."""
        ...


@runtime_checkable
class ITestReporterPlugin(IPlugin, Protocol):
    """Protocol for test reporter plugins."""

    def on_test_start(self, test_name: str) -> None:
        """Called when a test starts."""
        ...

    def on_test_end(self, test_name: str, result: Any) -> None:
        """Called when a test ends."""
        ...

    def on_suite_start(self, suite_name: str) -> None:
        """Called when a test suite starts."""
        ...

    def on_suite_end(self, suite_name: str, results: Any) -> None:
        """Called when a test suite ends."""
        ...

    def generate_report(self, output_path: str) -> None:
        """Generate a report from collected data."""
        ...


@runtime_checkable
class IAssertionPlugin(IPlugin, Protocol):
    """Protocol for custom assertion plugins."""

    def register_assertions(self, registry: "AssertionRegistry") -> None:
        """Register custom assertions with the framework."""
        ...


@runtime_checkable
class IDataSourcePlugin(IPlugin, Protocol):
    """Protocol for custom data source plugins."""

    def get_data(self, query: str) -> Any:
        """Retrieve data based on a query."""
        ...

    def supports_query(self, query: str) -> bool:
        """Check if this data source supports the given query."""
        ...


@runtime_checkable
class IHookPlugin(IPlugin, Protocol):
    """Protocol for hook-based plugins."""

    def register_hooks(self, hook_manager: "HookManager") -> None:
        """Register hooks with the framework."""
        ...


class PluginMetadata:
    """Metadata about a plugin.

    Attributes:
        name: Plugin name
        version: Plugin version
        description: Plugin description
        author: Plugin author
        entry_point: Python path to plugin class
        dependencies: List of required dependencies
        tags: List of tags for categorization
    """

    def __init__(
        self,
        name: str,
        version: str,
        description: str = "",
        author: str = "",
        entry_point: str = "",
        dependencies: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ):
        self.name = name
        self.version = version
        self.description = description
        self.author = author
        self.entry_point = entry_point
        self.dependencies = dependencies or []
        self.tags = tags or []

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "entry_point": self.entry_point,
            "dependencies": self.dependencies,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PluginMetadata":
        """Create metadata from dictionary."""
        return cls(
            name=data["name"],
            version=data["version"],
            description=data.get("description", ""),
            author=data.get("author", ""),
            entry_point=data.get("entry_point", ""),
            dependencies=data.get("dependencies", []),
            tags=data.get("tags", []),
        )


class AssertionRegistry:
    """Registry for custom assertions.

    Allows plugins to register custom assertion functions that can be
    used throughout the framework.
    """

    def __init__(self):
        self._assertions: Dict[str, Callable] = {}

    def register(self, name: str, assertion_func: Callable) -> None:
        """Register a custom assertion.

        Args:
            name: Name of the assertion
            assertion_func: Assertion function
        """
        self._assertions[name] = assertion_func

    def get(self, name: str) -> Optional[Callable]:
        """Get a registered assertion.

        Args:
            name: Name of the assertion

        Returns:
            The assertion function or None
        """
        return self._assertions.get(name)

    def has(self, name: str) -> bool:
        """Check if an assertion is registered.

        Args:
            name: Name of the assertion

        Returns:
            True if registered
        """
        return name in self._assertions

    def list_assertions(self) -> List[str]:
        """List all registered assertion names."""
        return list(self._assertions.keys())


class Hook:
    """Represents a hook that plugins can subscribe to.

    Attributes:
        name: Hook name
        callbacks: List of registered callbacks
    """

    def __init__(self, name: str):
        self.name = name
        self._callbacks: List[Callable] = []
        self._priority: Dict[Callable, int] = {}

    def subscribe(self, callback: Callable, priority: int = 10) -> None:
        """Subscribe a callback to this hook.

        Args:
            callback: Function to call when hook is triggered
            priority: Lower numbers execute first (default: 10)
        """
        self._callbacks.append(callback)
        self._priority[callback] = priority
        # Sort by priority
        self._callbacks.sort(key=lambda c: self._priority[c])

    def unsubscribe(self, callback: Callable) -> None:
        """Unsubscribe a callback from this hook.

        Args:
            callback: Function to remove
        """
        if callback in self._callbacks:
            self._callbacks.remove(callback)
            del self._priority[callback]

    def trigger(self, *args, **kwargs) -> List[Any]:
        """Trigger all subscribed callbacks.

        Args:
            *args: Positional arguments to pass to callbacks
            **kwargs: Keyword arguments to pass to callbacks

        Returns:
            List of callback results
        """
        results = []
        for callback in self._callbacks:
            try:
                result = callback(*args, **kwargs)
                results.append(result)
            except Exception as e:
                # Log error but continue with other callbacks
                import logging

                logging.getLogger(__name__).error(
                    f"Hook '{self.name}' callback failed: {e}"
                )
        return results


class HookManager:
    """Manages hooks for the plugin system.

    Allows plugins to register and trigger hooks at various points
    in the test lifecycle.
    """

    def __init__(self):
        self._hooks: Dict[str, Hook] = {}

    def register_hook(self, name: str) -> Hook:
        """Register a new hook.

        Args:
            name: Hook name

        Returns:
            The registered hook
        """
        if name not in self._hooks:
            self._hooks[name] = Hook(name)
        return self._hooks[name]

    def get_hook(self, name: str) -> Optional[Hook]:
        """Get a registered hook.

        Args:
            name: Hook name

        Returns:
            The hook or None
        """
        return self._hooks.get(name)

    def subscribe(self, hook_name: str, callback: Callable, priority: int = 10) -> None:
        """Subscribe to a hook.

        Args:
            hook_name: Name of the hook
            callback: Function to call
            priority: Execution priority (lower = first)
        """
        hook = self.register_hook(hook_name)
        hook.subscribe(callback, priority)

    def trigger(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """Trigger a hook.

        Args:
            hook_name: Name of the hook
            *args: Arguments to pass to callbacks
            **kwargs: Keyword arguments to pass to callbacks

        Returns:
            List of callback results
        """
        hook = self._hooks.get(hook_name)
        if hook:
            return hook.trigger(*args, **kwargs)
        return []

    def list_hooks(self) -> List[str]:
        """List all registered hook names."""
        return list(self._hooks.keys())


class PluginContext:
    """Context passed to plugins during initialization.

    Provides access to framework components and utilities.
    """

    def __init__(
        self,
        assertion_registry: AssertionRegistry,
        hook_manager: HookManager,
        config: Optional[Dict[str, Any]] = None,
    ):
        self.assertion_registry = assertion_registry
        self.hook_manager = hook_manager
        self.config = config or {}


__all__ = [
    "IPlugin",
    "ITestReporterPlugin",
    "IAssertionPlugin",
    "IDataSourcePlugin",
    "IHookPlugin",
    "PluginMetadata",
    "AssertionRegistry",
    "Hook",
    "HookManager",
    "PluginContext",
]
