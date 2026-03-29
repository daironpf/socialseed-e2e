"""Global and service-level context for socialseed-e2e.

Provides shared state management between test modules and services,
supporting thread-safe and process-safe (where applicable) data exchange.
"""

import logging
from typing import Any, Dict, Optional
from threading import Lock

logger = logging.getLogger(__name__)

class ServiceContext:
    """Manages shared state for a specific service.
    
    This context allows different test modules within the same service
    to share data (e.g., authentication tokens, created IDs).
    """

    def __init__(self, service_name: str):
        self.service_name = service_name
        self._data: Dict[str, Any] = {}
        self._lock = Lock()

    def set(self, key: str, value: Any) -> None:
        """Set a value in the service context."""
        with self._lock:
            self._data[key] = value
            logger.debug(f"Context [{self.service_name}] - Set {key}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the service context."""
        with self._lock:
            return self._data.get(key, default)

    def clear(self) -> None:
        """Clear all data in the service context."""
        with self._lock:
            self._data.clear()

    def to_dict(self) -> Dict[str, Any]:
        """Return a copy of the context data."""
        with self._lock:
            return self._data.copy()

class GlobalContext:
    """Manages shared state across all services.
    
    Useful for global configuration or data that needs to be
    passed between different services.
    """
    
    _instance: Optional['GlobalContext'] = None
    _lock = Lock()
    _data: Dict[str, Any] = {}
    _service_contexts: Dict[str, ServiceContext] = {}

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(GlobalContext, cls).__new__(cls)
            return cls._instance

    def get_service_context(self, service_name: str) -> ServiceContext:
        """Get or create a ServiceContext for a specific service."""
        with self._lock:
            if service_name not in self._service_contexts:
                self._service_contexts[service_name] = ServiceContext(service_name)
            return self._service_contexts[service_name]

    def set(self, key: str, value: Any) -> None:
        """Set a global value."""
        with self._lock:
            self._data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get a global value."""
        with self._lock:
            return self._data.get(key, default)
