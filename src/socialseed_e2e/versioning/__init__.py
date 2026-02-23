"""API Versioning Module.

This module provides comprehensive API versioning support including:
- Version detection (URL path, header, query parameter)
- Migration testing between versions
- Version-specific contract management
- Breaking change detection

Usage:
    from socialseed_e2e.versioning import VersionDetector, MigrationTester, VersionedContract

    # Detect versioning strategy
    detector = VersionDetector("http://localhost:8080")
    strategy = detector.detect_strategy(endpoints)
    versions = detector.discover_versions()

    # Test migration
    tester = MigrationTester("http://localhost:8080")
    results = tester.test_all_versions(test_function)

    # Manage contracts
    contracts = VersionedContract()
    contracts.add_contract("v1", openapi_spec)
    contracts.add_contract("v2", openapi_spec_v2)
    breaking = contracts.detect_breaking_changes("v1", "v2")
"""

from .migration_tester import BreakingChange, MigrationTester
from .models import (
    APIVersion,
    DeprecationInfo,
    MigrationTestResult,
    VersionCoverage,
    VersionStrategy,
    VersionTestResult,
)
from .version_detector import VersionDetector
from .versioned_contract import ContractType, VersionedContract

__all__ = [
    "VersionStrategy",
    "APIVersion",
    "VersionTestResult",
    "MigrationTestResult",
    "VersionCoverage",
    "DeprecationInfo",
    "VersionDetector",
    "MigrationTester",
    "BreakingChange",
    "VersionedContract",
    "ContractType",
]
