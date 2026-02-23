"""Database testing module for socialseed-e2e.

This module provides comprehensive support for SQL and NoSQL database testing,
including connection management, fixtures, assertions, integrity testing,
performance analysis, transaction testing, and migration validation.
"""

from typing import Any, Dict, List, Optional

from socialseed_e2e.database.assertions import DatabaseAssertions
from socialseed_e2e.database.connection_manager import ConnectionManager
from socialseed_e2e.database.fixture_manager import FixtureManager
from socialseed_e2e.database.performance import QueryPerformanceAnalyzer

from .integrity.integrity_tester import IntegrityTester
from .migrations.migration_tester import MigrationTester

# New Issue #017 components
from .models import (
    ConstraintViolation,
    DatabaseTestResult,
    DatabaseType,
    DeadlockInfo,
    IntegrityCheck,
    MigrationTest,
    QueryPerformance,
    QueryPlan,
    TransactionTest,
)
from .performance.query_analyzer import QueryAnalyzer
from .transactions.transaction_tester import TransactionTester

__all__ = [
    "ConnectionManager",
    "FixtureManager",
    "DatabaseAssertions",
    "QueryPerformanceAnalyzer",
    # Issue #017 components
    "DatabaseTestResult",
    "IntegrityCheck",
    "QueryPerformance",
    "TransactionTest",
    "MigrationTest",
    "DatabaseType",
    "ConstraintViolation",
    "QueryPlan",
    "DeadlockInfo",
    "IntegrityTester",
    "QueryAnalyzer",
    "TransactionTester",
    "MigrationTester",
]
