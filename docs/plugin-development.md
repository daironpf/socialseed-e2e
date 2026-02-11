# Plugin Development Guide

This guide explains how to create plugins for the socialseed-e2e framework.

## Overview

The socialseed-e2e plugin system allows you to extend the framework with custom functionality. Plugins can:

- Add custom test reporters
- Register custom assertions
- Provide data sources
- Hook into test lifecycle events
- Add new functionality

## Quick Start

### 1. Create a Basic Plugin

```python
# my_plugin.py
from socialseed_e2e.plugins import IPlugin

class MyPlugin(IPlugin):
    name = "my-plugin"
    version = "1.0.0"
    description = "My custom plugin"

    def initialize(self, config=None):
        print(f"Plugin {self.name} initialized!")

    def shutdown(self):
        print(f"Plugin {self.name} shutdown!")
```

### 2. Load and Use Your Plugin

```python
from socialseed_e2e.plugins import PluginManager

manager = PluginManager()
manager.load_plugin("my-plugin", plugin_class=MyPlugin)

# Use the plugin
plugin = manager.get_plugin("my-plugin")

# Cleanup
manager.unload_all()
```

## Plugin Types

### Test Reporter Plugin

Create custom test reporters:

```python
from socialseed_e2e.plugins import ITestReporterPlugin

class CustomReporter(ITestReporterPlugin):
    name = "custom-reporter"
    version = "1.0.0"
    description = "Custom test reporter"

    def initialize(self, config=None):
        self.results = []

    def shutdown(self):
        self.generate_report("report.json")

    def on_test_start(self, test_name):
        print(f"Starting: {test_name}")

    def on_test_end(self, test_name, result):
        self.results.append({"name": test_name, "passed": result.passed})

    def on_suite_start(self, suite_name):
        print(f"Suite: {suite_name}")

    def on_suite_end(self, suite_name, results):
        print(f"Suite completed: {suite_name}")

    def generate_report(self, output_path):
        import json
        with open(output_path, "w") as f:
            json.dump(self.results, f)
```

### Custom Assertions Plugin

Register custom assertion functions:

```python
from socialseed_e2e.plugins import IAssertionPlugin, AssertionRegistry

class CustomAssertions(IAssertionPlugin):
    name = "custom-assertions"
    version = "1.0.0"

    def initialize(self, config=None):
        pass

    def shutdown(self):
        pass

    def register_assertions(self, registry: AssertionRegistry):
        registry.register("assert_valid_email", self.assert_valid_email)
        registry.register("assert_valid_uuid", self.assert_valid_uuid)

    def assert_valid_email(self, email):
        import re
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            raise AssertionError(f"Invalid email: {email}")

    def assert_valid_uuid(self, uuid):
        import re
        if not re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', uuid, re.I):
            raise AssertionError(f"Invalid UUID: {uuid}")
```

### Hook Plugin

Hook into test lifecycle events:

```python
from socialseed_e2e.plugins import IHookPlugin, HookManager

class LifecycleHooks(IHookPlugin):
    name = "lifecycle-hooks"
    version = "1.0.0"

    def initialize(self, config=None):
        pass

    def shutdown(self):
        pass

    def register_hooks(self, hook_manager: HookManager):
        hook_manager.subscribe("before_test", self.before_test)
        hook_manager.subscribe("after_test", self.after_test)

    def before_test(self, test_name, **kwargs):
        print(f"Before test: {test_name}")

    def after_test(self, test_name, result, **kwargs):
        print(f"After test: {test_name}")
```

## Plugin Discovery

Plugins can be automatically discovered from:

1. `.e2e/plugins/` directory (project-specific)
2. `plugins/` directory (project-specific)
3. `~/.socialseed-e2e/plugins/` directory (user-wide)
4. Additional directories configured in `PluginManager`

### Plugin Metadata

Create a `plugin.json` file in your plugin directory:

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "My custom plugin",
  "author": "Your Name",
  "entry_point": "my_plugin:MyPlugin",
  "dependencies": [],
  "tags": ["reporter", "custom"]
}
```

Or define metadata in your Python file:

```python
__plugin_metadata__ = {
    "name": "my-plugin",
    "version": "1.0.0",
    "description": "My custom plugin",
    "entry_point": "my_plugin:MyPlugin",
}
```

## Plugin Manager API

### Discover Plugins

```python
from socialseed_e2e.plugins import PluginManager

manager = PluginManager()

# Discover plugins from default locations
count = manager.discover_plugins()
print(f"Discovered {count} plugins")

# List discovered plugins
for name in manager.list_discovered():
    print(f"Found: {name}")
```

### Load Plugins

```python
# Load all discovered plugins
manager.load_all()

# Load a specific plugin
manager.load_plugin("my-plugin")

# Load with custom configuration
manager.load_plugin("my-plugin", config={"output_path": "/tmp/report.json"})
```

### Access Plugins

```python
# Get a loaded plugin
plugin = manager.get_plugin("my-plugin")

# Check if loaded
if manager.is_loaded("my-plugin"):
    print("Plugin is loaded")

# Get plugin metadata
metadata = manager.get_metadata("my-plugin")
print(f"Version: {metadata.version}")
```

### Cleanup

```python
# Unload a specific plugin
manager.unload_plugin("my-plugin")

# Unload all plugins
manager.unload_all()
```

## Hook System

The hook system allows you to execute code at specific points:

### Available Hooks

- `before_test` - Called before each test
- `after_test` - Called after each test
- `before_suite` - Called before test suite
- `after_suite` - Called after test suite
- `on_error` - Called when an error occurs

### Registering Hooks

```python
from socialseed_e2e.plugins import HookManager

hook_manager = HookManager()

# Subscribe to a hook
hook_manager.subscribe("before_test", my_callback, priority=10)

# Trigger a hook
results = hook_manager.trigger("before_test", test_name="my_test")
```

### Hook Priority

Lower priority numbers execute first:

```python
# This will execute first
hook_manager.subscribe("before_test", setup_db, priority=1)

# This will execute after
hook_manager.subscribe("before_test", log_test, priority=10)
```

## Assertion Registry

Register and use custom assertions:

### Register Assertions

```python
from socialseed_e2e.plugins import AssertionRegistry

registry = AssertionRegistry()
registry.register("assert_is_json", assert_is_json)
```

### Use Assertions

```python
# Get assertion function
assert_fn = registry.get("assert_is_json")
assert_fn('{"key": "value"}')

# Check if assertion exists
if registry.has("assert_is_json"):
    print("Assertion is registered")

# List all assertions
for name in registry.list_assertions():
    print(f"Assertion: {name}")
```

## Best Practices

1. **Naming**: Use descriptive names with hyphens (e.g., `json-reporter`)
2. **Versioning**: Follow semantic versioning (e.g., `1.0.0`)
3. **Error Handling**: Handle errors gracefully in plugins
4. **Cleanup**: Always implement `shutdown()` to clean up resources
5. **Configuration**: Accept configuration via `initialize(config)`
6. **Documentation**: Document your plugin's functionality

## Examples

See the `examples/plugins/` directory for complete examples:

- `json_reporter_plugin.py` - Custom JSON reporter
- `custom_assertions_plugin.py` - Custom assertions
- `hook_plugin.py` - Lifecycle hooks

## Troubleshooting

### Plugin Not Found

Ensure:
1. Plugin directory is in the search path
2. `plugin.json` or `__plugin_metadata__` is present
3. Entry point is correct

### Plugin Load Error

Check:
1. Plugin class implements required interface
2. All dependencies are installed
3. No syntax errors in plugin code

### Hook Not Triggered

Verify:
1. Plugin is loaded
2. Hook is registered in `register_hooks()`
3. Hook name matches the trigger

## Advanced Topics

### Plugin Dependencies

Specify dependencies in metadata:

```json
{
  "name": "my-plugin",
  "dependencies": ["base-plugin>=1.0.0"]
}
```

### Plugin Context

Access framework components:

```python
from socialseed_e2e.plugins import IPlugin, PluginContext

class MyPlugin(IPlugin):
    def initialize(self, config=None):
        # Access assertion registry
        self.context.assertion_registry

        # Access hook manager
        self.context.hook_manager
```

### Custom Plugin Types

Create your own plugin interfaces:

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class ICustomPlugin(Protocol):
    name: str

    def custom_method(self):
        ...
```

## Further Reading

- Plugin API Reference: `socialseed_e2e.plugins`
- Example Plugins: `examples/plugins/`
- Core Interfaces: `socialseed_e2e/plugins/interfaces.py`
