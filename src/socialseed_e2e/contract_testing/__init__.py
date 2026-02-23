"""Consumer-Driven Contract Testing for socialseed-e2e.

Ensures that API consumers and providers stay compatible by defining
and verifying contracts.

This module provides comprehensive contract testing including:
- Consumer contract definition
- Provider verification
- Pact Broker integration
- Contract migration and breaking change detection
- Multi-protocol support (REST, GraphQL, gRPC)
"""

from socialseed_e2e.contract_testing.consumer import ConsumerContract
from socialseed_e2e.contract_testing.provider import ProviderVerifier
from socialseed_e2e.contract_testing.registry import LocalContractRegistry

# Pact Broker Integration
try:
    from socialseed_e2e.contract_testing.pact_broker import (
        CompatibilityResult,
        ContractVersion,
        PactBrokerClient,
        PactBrokerConfig,
        VerificationResult,
    )

    _PACT_BROKER_AVAILABLE = True
except ImportError:
    _PACT_BROKER_AVAILABLE = False

# Contract Migration
from socialseed_e2e.contract_testing.migration import (
    ChangeSeverity,
    ChangeType,
    ContractChange,
    ContractMigrationAnalyzer,
    DeprecationNotice,
    MigrationAnalysisResult,
    MigrationPath,
)

# Multi-Protocol Support
from socialseed_e2e.contract_testing.multi_protocol import (
    FieldDefinition,
    GraphQLContractBuilder,
    GraphQLOperation,
    GRPCContractBuilder,
    GRPCMethod,
    MultiProtocolContractBuilder,
    ProtocolType,
    RESTContractBuilder,
    RESTEndpoint,
)

__all__ = [
    # Core
    "ConsumerContract",
    "ProviderVerifier",
    "LocalContractRegistry",
    # Migration
    "ChangeSeverity",
    "ChangeType",
    "ContractChange",
    "ContractMigrationAnalyzer",
    "DeprecationNotice",
    "MigrationAnalysisResult",
    "MigrationPath",
    # Multi-Protocol
    "FieldDefinition",
    "GRPCMethod",
    "GraphQLContractBuilder",
    "GraphQLOperation",
    "GRPCContractBuilder",
    "MultiProtocolContractBuilder",
    "ProtocolType",
    "RESTContractBuilder",
    "RESTEndpoint",
]

# Add Pact Broker exports if available
if _PACT_BROKER_AVAILABLE:
    __all__.extend(
        [
            "CompatibilityResult",
            "ContractVersion",
            "PactBrokerClient",
            "PactBrokerConfig",
            "VerificationResult",
        ]
    )
