"""
Enterprise Test Data Management module for socialseed-e2e.
Provides tools for generating synthetic data, factory-based model creation, and environment seeding.

Exposes:
- DataFactory: Base class for creating model instances with fake data.
- DataSeeder: Context manager for seeding and cleaning up test data.
"""

from .factories import DataFactory
from .seeder import DataSeeder

__all__ = ["DataFactory", "DataSeeder"]
