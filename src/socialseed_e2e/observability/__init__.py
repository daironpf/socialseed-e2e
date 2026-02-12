"""Observability and APM integration for socialseed-e2e.

This module provides integration with popular observability tools like
DataDog, New Relic, Prometheus, and jaeger for tracing and metrics.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
import time


class ObservabilityProvider(ABC):
    """Base class for all observability providers."""
    
    @abstractmethod
    def record_test_result(self, test_name: str, status: str, duration_ms: float, metadata: Optional[Dict[str, Any]] = None):
        """Record the result of a test."""
        pass

    @abstractmethod
    def record_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a custom metric."""
        pass


class TracingProvider(ABC):
    """Base class for distributed tracing providers."""
    
    @abstractmethod
    def start_span(self, name: str, tags: Optional[Dict[str, str]] = None) -> Any:
        """Start a new trace span."""
        pass

    @abstractmethod
    def end_span(self, span: Any):
        """End an active span."""
        pass


class ObservabilityManager:
    """Manages multiple observability providers."""
    
    def __init__(self):
        self.providers: List[ObservabilityProvider] = []
        self.tracing_provider: Optional[TracingProvider] = None

    def add_provider(self, provider: ObservabilityProvider):
        self.providers.append(provider)

    def set_tracing_provider(self, provider: TracingProvider):
        self.tracing_provider = provider

    def record_test(self, test_name: str, status: str, duration_ms: float, metadata: Optional[Dict[str, Any]] = None):
        for provider in self.providers:
            provider.record_test_result(test_name, status, duration_ms, metadata)

    def record_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        for provider in self.providers:
            provider.record_metric(name, value, tags)
