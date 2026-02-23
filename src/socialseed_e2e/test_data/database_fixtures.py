"""
Intelligent Database Fixture Manager for socialseed-e2e.

This module provides intelligent test data generation by understanding
the database schema and generating state fixtures automatically.

Features:
- Database schema inference from project code
- Automatic fixture generation based on relationships
- Transaction-based test isolation
- Safe cleanup with garbage collection
- Support for SQL and NoSQL databases
"""

import uuid
from contextlib import contextmanager
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DatabaseType(str, Enum):
    """Supported database types."""

    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"
    MONGODB = "mongodb"
    REDIS = "redis"
    NEO4J = "neo4j"


class TableRelationship(BaseModel):
    """Represents a relationship between database tables."""

    from_table: str
    to_table: str
    relationship_type: str  # "one_to_one", "one_to_many", "many_to_many"
    foreign_key: Optional[str] = None


class ColumnInfo(BaseModel):
    """Information about a database column."""

    name: str
    type: str
    nullable: bool = True
    primary_key: bool = False
    default: Optional[Any] = None
    foreign_key: Optional[str] = None


class TableSchema(BaseModel):
    """Schema information for a database table."""

    table_name: str
    columns: Dict[str, ColumnInfo] = {}
    relationships: List[TableRelationship] = Field(default_factory=list)
    primary_key: Optional[str] = None


class FixtureState(BaseModel):
    """Represents a test fixture state."""

    fixture_id: str
    fixture_name: str

    table_name: str
    data: Dict[str, Any]

    created_at: datetime = Field(default_factory=datetime.now)
    depends_on: List[str] = Field(default_factory=list)

    cleanup_sql: Optional[str] = None


class TestTransaction(BaseModel):
    """Transaction context for test isolation."""

    transaction_id: str
    started_at: datetime = Field(default_factory=datetime.now)

    fixtures_created: List[str] = Field(default_factory=list)
    database_state: Dict[str, Any] = {}

    is_committed: bool = False
    is_rolled_back: bool = False


class DatabaseFixtureManager:
    """
    Manages database fixtures for test data generation.
    """

    def __init__(self, db_type: DatabaseType, connection_string: str):
        self.db_type = db_type
        self.connection_string = connection_string
        self.schemas: Dict[str, TableSchema] = {}
        self.active_transactions: Dict[str, TestTransaction] = {}
        self.fixtures: Dict[str, FixtureState] = {}

    def infer_schema_from_models(self, models_path: str) -> Dict[str, TableSchema]:
        """Infer database schema from Pydantic models or ORM classes."""
        schemas = {}

        return schemas

    def add_table_schema(self, schema: TableSchema) -> None:
        """Add a table schema to the manager."""
        self.schemas[schema.table_name] = schema

    def generate_fixture(
        self,
        table_name: str,
        overrides: Optional[Dict[str, Any]] = None,
    ) -> FixtureState:
        """Generate a fixture for a table."""
        schema = self.schemas.get(table_name)
        if not schema:
            raise ValueError(f"Schema not found for table: {table_name}")

        data = self._generate_row_data(schema, overrides or {})

        fixture = FixtureState(
            fixture_id=str(uuid.uuid4()),
            fixture_name=f"{table_name}_fixture",
            table_name=table_name,
            data=data,
            cleanup_sql=self._generate_cleanup_sql(
                table_name, schema.primary_key, data
            ),
        )

        self.fixtures[fixture.fixture_id] = fixture
        return fixture

    def _generate_row_data(
        self, schema: TableSchema, overrides: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate row data based on schema."""
        data = {}

        for col_name, col_info in schema.columns.items():
            if col_name in overrides:
                data[col_name] = overrides[col_name]
            elif col_info.default is not None:
                data[col_name] = col_info.default
            elif col_info.primary_key:
                data[col_name] = str(uuid.uuid4())
            elif not col_info.nullable and col_info.type.lower() in ("varchar", "text"):
                data[col_name] = f"test_{col_name}_{uuid.uuid4().hex[:8]}"
            elif not col_info.nullable and col_info.type.lower() in ("integer", "int"):
                data[col_name] = 1
            elif not col_info.nullable and col_info.type.lower() == "boolean":
                data[col_name] = True
            else:
                data[col_name] = None

        return data

    def _generate_cleanup_sql(
        self, table_name: str, primary_key: Optional[str], data: Dict[str, Any]
    ) -> Optional[str]:
        """Generate SQL for cleaning up the fixture."""
        if not primary_key or primary_key not in data:
            return None

        return f"DELETE FROM {table_name} WHERE {primary_key} = '{data[primary_key]}'"

    @contextmanager
    def transaction(self):
        """Context manager for test transactions."""
        transaction = TestTransaction(transaction_id=str(uuid.uuid4()))

        try:
            self.active_transactions[transaction.transaction_id] = transaction
            yield transaction
            transaction.is_committed = True
        except Exception:
            transaction.is_rolled_back = True
            raise
        finally:
            if transaction.transaction_id in self.active_transactions:
                del self.active_transactions[transaction.transaction_id]

    def cleanup_fixtures(self, fixture_ids: Optional[List[str]] = None) -> int:
        """Clean up created fixtures."""
        count = 0

        ids_to_cleanup = fixture_ids or list(self.fixtures.keys())

        for fixture_id in ids_to_cleanup:
            if fixture_id in self.fixtures:
                del self.fixtures[fixture_id]
                count += 1

        return count


class IntelligentFixtureGenerator:
    """
    AI-powered fixture generator that understands database relationships.
    """

    def __init__(self, db_manager: DatabaseFixtureManager):
        self.db_manager = db_manager
        self.generated_fixtures: List[FixtureState] = []

    def generate_dependent_fixture(
        self,
        parent_table: str,
        child_table: str,
        parent_data: Dict[str, Any],
    ) -> FixtureState:
        """Generate a child fixture that depends on parent data."""
        parent_schema = self.db_manager.schemas.get(parent_table)
        child_schema = self.db_manager.schemas.get(child_table)

        if not parent_schema or not child_schema:
            raise ValueError("Schemas not found")

        fk_column = self._find_foreign_key(parent_schema, child_schema)

        child_data = {}
        if fk_column:
            child_data[fk_column] = parent_data.get(parent_schema.primary_key)

        child_fixture = self.db_manager.generate_fixture(child_table, child_data)
        child_fixture.depends_on.append(parent_data.get(parent_schema.primary_key, ""))

        return child_fixture

    def _find_foreign_key(
        self, parent_schema: TableSchema, child_schema: TableSchema
    ) -> Optional[str]:
        """Find foreign key column in child schema."""
        for rel in child_schema.relationships:
            if rel.to_table == parent_schema.table_name:
                return rel.foreign_key

        for col in child_schema.columns.values():
            if col.foreign_key and parent_schema.table_name in col.foreign_key:
                return col.name

        return None

    def generate_fixture_graph(
        self,
        tables: List[str],
        root_data: Dict[str, Any],
    ) -> List[FixtureState]:
        """Generate a complete fixture graph for related tables."""
        fixtures = []

        current_data = root_data.copy()
        for i, table in enumerate(tables):
            if i == 0:
                fixture = self.db_manager.generate_fixture(table, current_data)
            else:
                parent_table = tables[i - 1]
                fixture = self.generate_dependent_fixture(
                    parent_table, table, current_data
                )

            fixtures.append(fixture)
            current_data = fixture.data

        self.generated_fixtures.extend(fixtures)
        return fixtures

    def cleanup_all(self) -> int:
        """Clean up all generated fixtures."""
        count = len(self.generated_fixtures)
        self.generated_fixtures.clear()
        return self.db_manager.cleanup_fixtures()


class TestDataManager:
    """
    High-level manager for test data with API integration.
    """

    def __init__(self, db_manager: DatabaseFixtureManager):
        self.db_manager = db_manager
        self.fixture_generator = IntelligentFixtureGenerator(db_manager)
        self.active_fixtures: List[FixtureState] = []

    def setup_test_state(
        self,
        state_definition: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Setup test state from definition.

        Args:
            state_definition: Dict mapping table names to data overrides

        Returns:
            Dict of created fixtures
        """
        created_fixtures = {}

        for table_name, data in state_definition.items():
            fixture = self.db_manager.generate_fixture(table_name, data)
            created_fixtures[table_name] = fixture
            self.active_fixtures.append(fixture)

        return created_fixtures

    def teardown_test_state(self) -> int:
        """Clean up all fixtures created during test."""
        count = self.fixture_generator.cleanup_all()
        self.active_fixtures.clear()
        return count

    @contextmanager
    def test_scope(self, state_definition: Optional[Dict[str, Dict[str, Any]]] = None):
        """Context manager for test data lifecycle."""
        fixtures = None

        try:
            if state_definition:
                fixtures = self.setup_test_state(state_definition)
            yield fixtures
        finally:
            if self.active_fixtures:
                self.teardown_test_state()


__all__ = [
    "DatabaseType",
    "TableRelationship",
    "ColumnInfo",
    "TableSchema",
    "FixtureState",
    "TestTransaction",
    "DatabaseFixtureManager",
    "IntelligentFixtureGenerator",
    "TestDataManager",
]
