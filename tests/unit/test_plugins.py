"""Tests for the plugin system.

This module contains unit tests for the plugin system including:
- Plugin interfaces
- Plugin manager
- Hook system
- Assertion registry
"""

import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import Mock, patch

import pytest

from socialseed_e2e.plugins import (
    AssertionRegistry,
    Hook,
    HookManager,
    IAssertionPlugin,
    IHookPlugin,
    IPlugin,
    ITestReporterPlugin,
    LoadedPlugin,
    PluginContext,
    PluginError,
    PluginLoadError,
    PluginManager,
    PluginMetadata,
    PluginNotFoundError,
    load_plugin,
)

pytestmark = pytest.mark.unit


# Test fixtures
@pytest.fixture
def sample_plugin_class():
    """Create a sample plugin class for testing."""

    class SamplePlugin(IPlugin):
        name = "sample-plugin"
        version = "1.0.0"
        description = "A sample plugin for testing"

        def __init__(self):
            self.initialized = False
            self.shutdown_called = False
            self.config = None

        def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
            self.initialized = True
            self.config = config

        def shutdown(self) -> None:
            self.shutdown_called = True

    return SamplePlugin


@pytest.fixture
def plugin_manager(tmp_path):
    """Create a plugin manager with a temporary directory."""
    return PluginManager(plugin_dirs=[tmp_path])


# Test PluginMetadata
class TestPluginMetadata:
    """Test cases for PluginMetadata."""

    def test_creation(self):
        """Test creating plugin metadata."""
        metadata = PluginMetadata(
            name="test-plugin",
            version="1.0.0",
            description="Test description",
            author="Test Author",
            entry_point="test_plugin:TestPlugin",
            dependencies=["dep1", "dep2"],
            tags=["test", "example"],
        )

        assert metadata.name == "test-plugin"
        assert metadata.version == "1.0.0"
        assert metadata.description == "Test description"
        assert metadata.author == "Test Author"
        assert metadata.entry_point == "test_plugin:TestPlugin"
        assert metadata.dependencies == ["dep1", "dep2"]
        assert metadata.tags == ["test", "example"]

    def test_to_dict(self):
        """Test converting metadata to dictionary."""
        metadata = PluginMetadata(
            name="test-plugin",
            version="1.0.0",
            description="Test",
        )

        data = metadata.to_dict()
        assert data["name"] == "test-plugin"
        assert data["version"] == "1.0.0"
        assert data["description"] == "Test"

    def test_from_dict(self):
        """Test creating metadata from dictionary."""
        data = {
            "name": "test-plugin",
            "version": "1.0.0",
            "description": "Test description",
            "author": "Test Author",
        }

        metadata = PluginMetadata.from_dict(data)
        assert metadata.name == "test-plugin"
        assert metadata.version == "1.0.0"
        assert metadata.description == "Test description"
        assert metadata.author == "Test Author"


# Test AssertionRegistry
class TestAssertionRegistry:
    """Test cases for AssertionRegistry."""

    def test_register_and_get(self):
        """Test registering and retrieving assertions."""
        registry = AssertionRegistry()

        def custom_assertion():
            pass

        registry.register("custom_assert", custom_assertion)
        retrieved = registry.get("custom_assert")

        assert retrieved is custom_assertion

    def test_get_nonexistent(self):
        """Test getting non-existent assertion."""
        registry = AssertionRegistry()
        result = registry.get("nonexistent")
        assert result is None

    def test_has(self):
        """Test checking if assertion exists."""
        registry = AssertionRegistry()

        def test_assert():
            pass

        registry.register("test", test_assert)

        assert registry.has("test") is True
        assert registry.has("nonexistent") is False

    def test_list_assertions(self):
        """Test listing registered assertions."""
        registry = AssertionRegistry()

        registry.register("assert1", lambda: None)
        registry.register("assert2", lambda: None)

        assertions = registry.list_assertions()
        assert "assert1" in assertions
        assert "assert2" in assertions
        assert len(assertions) == 2


# Test Hook
class TestHook:
    """Test cases for Hook."""

    def test_subscribe_and_trigger(self):
        """Test subscribing and triggering callbacks."""
        hook = Hook("test-hook")

        results = []

        def callback1():
            results.append("callback1")

        def callback2():
            results.append("callback2")

        hook.subscribe(callback1)
        hook.subscribe(callback2)

        hook.trigger()

        assert "callback1" in results
        assert "callback2" in results

    def test_priority_ordering(self):
        """Test that callbacks execute in priority order."""
        hook = Hook("test-hook")

        results = []

        def low_priority():
            results.append("low")

        def high_priority():
            results.append("high")

        hook.subscribe(low_priority, priority=10)
        hook.subscribe(high_priority, priority=1)

        hook.trigger()

        assert results[0] == "high"
        assert results[1] == "low"

    def test_unsubscribe(self):
        """Test unsubscribing from hook."""
        hook = Hook("test-hook")

        results = []

        def callback():
            results.append("called")

        hook.subscribe(callback)
        hook.trigger()
        assert len(results) == 1

        hook.unsubscribe(callback)
        hook.trigger()
        assert len(results) == 1  # Should not increase

    def test_trigger_with_args(self):
        """Test triggering with arguments."""
        hook = Hook("test-hook")

        received_args = []
        received_kwargs = {}

        def callback(*args, **kwargs):
            received_args.extend(args)
            received_kwargs.update(kwargs)

        hook.subscribe(callback)
        hook.trigger("arg1", "arg2", key="value")

        assert "arg1" in received_args
        assert "arg2" in received_args
        assert received_kwargs["key"] == "value"


# Test HookManager
class TestHookManager:
    """Test cases for HookManager."""

    def test_register_hook(self):
        """Test registering a hook."""
        manager = HookManager()
        hook = manager.register_hook("test-hook")

        assert hook.name == "test-hook"
        assert manager.get_hook("test-hook") is hook

    def test_subscribe(self):
        """Test subscribing to a hook."""
        manager = HookManager()

        results = []

        def callback():
            results.append("called")

        manager.subscribe("test-hook", callback)
        manager.trigger("test-hook")

        assert len(results) == 1

    def test_trigger_nonexistent_hook(self):
        """Test triggering a non-existent hook."""
        manager = HookManager()
        results = manager.trigger("nonexistent")

        assert results == []

    def test_list_hooks(self):
        """Test listing registered hooks."""
        manager = HookManager()

        manager.register_hook("hook1")
        manager.register_hook("hook2")

        hooks = manager.list_hooks()
        assert "hook1" in hooks
        assert "hook2" in hooks


# Test LoadedPlugin
class TestLoadedPlugin:
    """Test cases for LoadedPlugin."""

    def test_load(self, sample_plugin_class):
        """Test loading a plugin."""
        metadata = PluginMetadata(name="test", version="1.0.0")
        instance = sample_plugin_class()
        context = PluginContext(
            assertion_registry=AssertionRegistry(),
            hook_manager=HookManager(),
        )

        loaded = LoadedPlugin(metadata, instance, context)
        assert not loaded.is_loaded()

        loaded.load()

        assert loaded.is_loaded()
        assert instance.initialized is True

    def test_unload(self, sample_plugin_class):
        """Test unloading a plugin."""
        metadata = PluginMetadata(name="test", version="1.0.0")
        instance = sample_plugin_class()
        context = PluginContext(
            assertion_registry=AssertionRegistry(),
            hook_manager=HookManager(),
        )

        loaded = LoadedPlugin(metadata, instance, context)
        loaded.load()
        assert loaded.is_loaded()

        loaded.unload()
        assert not loaded.is_loaded()
        assert instance.shutdown_called is True

    def test_load_failure(self):
        """Test handling of plugin load failure."""

        class BadPlugin(IPlugin):
            name = "bad-plugin"
            version = "1.0.0"

            def initialize(self, config=None):
                raise RuntimeError("Initialization failed")

            def shutdown(self):
                pass

        metadata = PluginMetadata(name="bad", version="1.0.0")
        instance = BadPlugin()
        context = PluginContext(
            assertion_registry=AssertionRegistry(),
            hook_manager=HookManager(),
        )

        loaded = LoadedPlugin(metadata, instance, context)

        with pytest.raises(PluginLoadError):
            loaded.load()


# Test PluginManager
class TestPluginManager:
    """Test cases for PluginManager."""

    def test_init(self, tmp_path):
        """Test initialization."""
        manager = PluginManager(plugin_dirs=[tmp_path])
        assert tmp_path in manager.plugin_dirs
        assert manager.assertion_registry is not None
        assert manager.hook_manager is not None

    def test_discover_plugins_empty(self, plugin_manager):
        """Test discovery with no plugins."""
        count = plugin_manager.discover_plugins()
        assert count == 0
        assert plugin_manager.list_discovered() == []

    def test_discover_plugins_with_json(self, plugin_manager, tmp_path):
        """Test discovery with plugin.json files."""
        # Create a plugin directory with metadata
        plugin_dir = tmp_path / "my-plugin"
        plugin_dir.mkdir()

        metadata = {
            "name": "my-plugin",
            "version": "1.0.0",
            "entry_point": "my_plugin:MyPlugin",
        }
        with open(plugin_dir / "plugin.json", "w") as f:
            json.dump(metadata, f)

        count = plugin_manager.discover_plugins()

        assert count == 1
        assert "my-plugin" in plugin_manager.list_discovered()

    @pytest.mark.skip(reason="Test requires actual plugin module, not mock")
    def test_load_plugin(self, plugin_manager, sample_plugin_class):
        """Test loading a plugin."""
        metadata = PluginMetadata(
            name="test-plugin",
            version="1.0.0",
            entry_point="test:TestPlugin",
        )

        loaded = plugin_manager.load_plugin(
            "test-plugin",
            metadata=metadata,
            plugin_class=sample_plugin_class,
        )

        assert loaded.is_loaded()
        assert "test-plugin" in plugin_manager.list_loaded()

    def test_load_plugin_not_found(self, plugin_manager):
        """Test loading non-existent plugin."""
        with pytest.raises(PluginNotFoundError):
            plugin_manager.load_plugin("nonexistent")

    def test_get_plugin(self, plugin_manager, sample_plugin_class):
        """Test getting a loaded plugin."""
        metadata = PluginMetadata(name="test", version="1.0.0")

        plugin_manager.load_plugin(
            "test",
            metadata=metadata,
            plugin_class=sample_plugin_class,
        )

        plugin = plugin_manager.get_plugin("test")
        assert plugin is not None
        # The plugin class has name="sample-plugin", not "test"
        assert plugin.name == "sample-plugin"

    def test_get_plugin_not_loaded(self, plugin_manager):
        """Test getting plugin that is not loaded."""
        plugin = plugin_manager.get_plugin("nonexistent")
        assert plugin is None

    def test_unload_plugin(self, plugin_manager, sample_plugin_class):
        """Test unloading a plugin."""
        metadata = PluginMetadata(name="test", version="1.0.0")

        plugin_manager.load_plugin(
            "test",
            metadata=metadata,
            plugin_class=sample_plugin_class,
        )

        assert "test" in plugin_manager.list_loaded()

        plugin_manager.unload_plugin("test")

        assert "test" not in plugin_manager.list_loaded()

    def test_unload_all(self, plugin_manager, sample_plugin_class):
        """Test unloading all plugins."""
        metadata = PluginMetadata(name="test", version="1.0.0")

        plugin_manager.load_plugin(
            "test",
            metadata=sample_plugin_class(),
            plugin_class=sample_plugin_class,
        )

        assert len(plugin_manager.list_loaded()) == 1

        plugin_manager.unload_all()

        assert len(plugin_manager.list_loaded()) == 0

    def test_is_loaded(self, plugin_manager, sample_plugin_class):
        """Test checking if plugin is loaded."""
        metadata = PluginMetadata(name="test", version="1.0.0")

        assert plugin_manager.is_loaded("test") is False

        plugin_manager.load_plugin(
            "test",
            metadata=metadata,
            plugin_class=sample_plugin_class,
        )

        assert plugin_manager.is_loaded("test") is True

    def test_get_metadata(self, plugin_manager, sample_plugin_class):
        """Test getting plugin metadata."""
        metadata = PluginMetadata(
            name="test",
            version="1.0.0",
            description="Test plugin",
        )

        plugin_manager.load_plugin(
            "test",
            metadata=metadata,
            plugin_class=sample_plugin_class,
        )

        retrieved = plugin_manager.get_metadata("test")
        assert retrieved is not None
        assert retrieved.name == "test"
        assert retrieved.description == "Test plugin"


# Test load_plugin convenience function
class TestLoadPluginConvenience:
    """Test cases for the load_plugin convenience function."""

    @patch("socialseed_e2e.plugins.manager.PluginManager")
    def test_load_plugin(self, mock_manager_class):
        """Test the load_plugin convenience function."""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager

        mock_loaded = Mock()
        mock_loaded.instance = Mock()
        mock_manager.load_plugin.return_value = mock_loaded

        result = load_plugin("my_plugin:MyPlugin")

        assert result is mock_loaded.instance
        mock_manager.load_plugin.assert_called_once()


# Test ITestReporterPlugin
class TestITestReporterPlugin:
    """Test cases for ITestReporterPlugin interface."""

    def test_interface_compliance(self):
        """Test that a valid reporter implements the interface."""

        class ValidReporter(ITestReporterPlugin):
            name = "valid-reporter"
            version = "1.0.0"

            def initialize(self, config=None):
                pass

            def shutdown(self):
                pass

            def on_test_start(self, test_name):
                pass

            def on_test_end(self, test_name, result):
                pass

            def on_suite_start(self, suite_name):
                pass

            def on_suite_end(self, suite_name, results):
                pass

            def generate_report(self, output_path):
                pass

        # Test that it can be instantiated
        reporter = ValidReporter()
        assert reporter.name == "valid-reporter"


# Test IAssertionPlugin
class TestIAssertionPlugin:
    """Test cases for IAssertionPlugin interface."""

    def test_register_assertions(self):
        """Test that assertion plugins can register assertions."""

        class ValidAssertionPlugin(IAssertionPlugin):
            name = "valid-assertions"
            version = "1.0.0"

            def initialize(self, config=None):
                pass

            def shutdown(self):
                pass

            def register_assertions(self, registry):
                registry.register("custom", lambda: None)

        plugin = ValidAssertionPlugin()
        registry = AssertionRegistry()
        plugin.register_assertions(registry)

        assert registry.has("custom")


# Test IHookPlugin
class TestIHookPlugin:
    """Test cases for IHookPlugin interface."""

    def test_register_hooks(self):
        """Test that hook plugins can register hooks."""

        class ValidHookPlugin(IHookPlugin):
            name = "valid-hooks"
            version = "1.0.0"

            def initialize(self, config=None):
                pass

            def shutdown(self):
                pass

            def register_hooks(self, hook_manager):
                hook_manager.subscribe("test", lambda: None)

        plugin = ValidHookPlugin()
        manager = HookManager()
        plugin.register_hooks(manager)

        assert "test" in manager.list_hooks()


# Integration tests
class TestPluginIntegration:
    """Integration tests for the plugin system."""

    def test_full_plugin_lifecycle(self, tmp_path, sample_plugin_class):
        """Test the complete plugin lifecycle."""
        manager = PluginManager(plugin_dirs=[tmp_path])

        # Create plugin metadata
        plugin_dir = tmp_path / "test-plugin"
        plugin_dir.mkdir()
        metadata = {
            "name": "test-plugin",
            "version": "1.0.0",
            "entry_point": "test:TestPlugin",
        }
        with open(plugin_dir / "plugin.json", "w") as f:
            json.dump(metadata, f)

        # Discover
        count = manager.discover_plugins()
        assert count == 1

        # Load
        loaded = manager.load_plugin(
            "test-plugin",
            plugin_class=sample_plugin_class,
        )
        assert loaded.is_loaded()

        # Get plugin
        plugin = manager.get_plugin("test-plugin")
        assert plugin is not None
        assert plugin.initialized is True

        # Unload
        manager.unload_plugin("test-plugin")
        assert plugin.shutdown_called is True
        assert not manager.is_loaded("test-plugin")

    def test_hook_integration(self, sample_plugin_class):
        """Test plugin hook integration."""
        manager = PluginManager()

        # Create a hook plugin
        class HookPlugin(IHookPlugin):
            name = "hook-plugin"
            version = "1.0.0"

            def __init__(self):
                self.events = []

            def initialize(self, config=None):
                pass

            def shutdown(self):
                pass

            def register_hooks(self, hook_manager):
                hook_manager.subscribe("test-event", self.on_event)

            def on_event(self, data, **kwargs):
                self.events.append(data)

        # Load plugin
        metadata = PluginMetadata(name="hook-plugin", version="1.0.0")
        manager.load_plugin(
            "hook-plugin",
            metadata=metadata,
            plugin_class=HookPlugin,
        )

        # Trigger hook
        results = manager.hook_manager.trigger("test-event", data="test-data")

        # Verify
        plugin = manager.get_plugin("hook-plugin")
        assert "test-data" in plugin.events

    def test_assertion_integration(self):
        """Test plugin assertion integration."""
        manager = PluginManager()

        # Create assertion plugin
        class AssertionPlugin(IAssertionPlugin):
            name = "assertion-plugin"
            version = "1.0.0"

            def initialize(self, config=None):
                pass

            def shutdown(self):
                pass

            def register_assertions(self, registry):
                registry.register("custom_assert", self.custom_assert)

            def custom_assert(self, value):
                assert value is True

        # Load plugin
        metadata = PluginMetadata(name="assertion-plugin", version="1.0.0")
        manager.load_plugin(
            "assertion-plugin",
            metadata=metadata,
            plugin_class=AssertionPlugin,
        )

        # Verify assertion is registered
        assert manager.assertion_registry.has("custom_assert")

        # Use assertion
        assert_fn = manager.assertion_registry.get("custom_assert")
        assert_fn(True)  # Should not raise


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
