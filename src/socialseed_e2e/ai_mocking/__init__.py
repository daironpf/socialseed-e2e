"""AI Mocking system for external Third-Party APIs.

This module provides automatic detection and mocking of external API calls
for air-gapped E2E testing, including stateful mocks with AI-powered responses.
"""

from .contract_validator import ContractValidator
from .external_api_analyzer import ExternalAPIAnalyzer
from .external_service_registry import ExternalServiceRegistry
from .mock_server_generator import MockServerGenerator
from .stateful_mocks import (
    InterceptedCall,
    MockIsolationManager,
    MockMode,
    RequestState,
    ResourceState,
    SmartMockOrchestrator,
    SmartMockServer,
    StatefulMockConfig,
)

__all__ = [
    "ExternalAPIAnalyzer",
    "ExternalServiceRegistry",
    "MockServerGenerator",
    "ContractValidator",
    # Stateful Mocks (Issue #2 - Phase 2)
    "InterceptedCall",
    "MockIsolationManager",
    "MockMode",
    "RequestState",
    "ResourceState",
    "SmartMockOrchestrator",
    "SmartMockServer",
    "StatefulMockConfig",
]
