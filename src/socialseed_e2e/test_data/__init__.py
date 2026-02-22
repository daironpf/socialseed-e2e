"""
Enterprise Test Data Management module for socialseed-e2e.
Provides tools for generating synthetic data, factory-based model creation, database fixtures, and environment seeding.

Exposes:
- DataFactory: Base class for creating model instances with fake data.
- DataSeeder: Context manager for seeding and cleaning up test data.
- DatabaseFixtureManager: Manages database fixtures for test data generation.
- IntelligentFixtureGenerator: AI-powered fixture generator that understands DB relationships.
- TestDataManager: High-level manager for test data with API integration.
"""

from .database_fixtures import (
    DatabaseFixtureManager,
    DatabaseType,
    IntelligentFixtureGenerator,
    TableSchema,
    TestDataManager,
    TestTransaction,
)
from .factories import DataFactory
from .seeder import DataSeeder

__all__ = [
    # Factories
    "DataFactory",
    # Seeder
    "DataSeeder",
    # Database Fixtures (Issue #6)
    "DatabaseFixtureManager",
    "DatabaseType",
    "IntelligentFixtureGenerator",
    "TableSchema",
    "TestDataManager",
    "TestTransaction",
]
