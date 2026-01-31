# API Reference

## Core Classes

### BasePage

The base class for API testing.

```python
from socialseed_e2e import BasePage

class MyPage(BasePage):
    def __init__(self, playwright=None, base_url=None):
        super().__init__(base_url, playwright)
```

#### Methods

- `get(url, **kwargs)` - Make GET request
- `post(url, **kwargs)` - Make POST request
- `put(url, **kwargs)` - Make PUT request
- `delete(url, **kwargs)` - Make DELETE request
- `patch(url, **kwargs)` - Make PATCH request

### ApiConfigLoader

Configuration loading utility.

```python
from socialseed_e2e import ApiConfigLoader

config = ApiConfigLoader.load("e2e.conf")
```

### TestOrchestrator

Test execution orchestrator.

```python
from socialseed_e2e import TestOrchestrator

orchestrator = TestOrchestrator(config)
orchestrator.run_all()
```

### ModuleLoader

Dynamic module loading.

```python
from socialseed_e2e import ModuleLoader

modules = ModuleLoader.discover("services/myapi/modules")
```

## Models

### ServiceConfig

Pydantic model for service configuration.

### TestContext

Context for test execution.

## Exceptions

- `ConfigError` - Configuration errors
- `ModuleError` - Module loading errors
- `TestError` - Test execution errors
