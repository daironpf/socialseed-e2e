"""
Models for database testing module.
"""

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
    ELASTICSEARCH = "elasticsearch"


class ConstraintType(str, Enum):
    """Types of database constraints."""

    PRIMARY_KEY = "primary_key"
    FOREIGN_KEY = "foreign_key"
    UNIQUE = "unique"
    CHECK = "check"
    NOT_NULL = "not_null"
    DEFAULT = "default"


class IsolationLevel(str, Enum):
    """Transaction isolation levels."""

    READ_UNCOMMITTED = "read_uncommitted"
    READ_COMMITTED = "read_committed"
    REPEATABLE_READ = "repeatable_read"
    SERIALIZABLE = "serializable"


class ConstraintViolation(BaseModel):
    """Represents a constraint violation."""

    constraint_name: str = Field(..., description="Name of the constraint")
    constraint_type: ConstraintType = Field(..., description="Type of constraint")
    table_name: str = Field(..., description="Table where violation occurred")
    column_name: Optional[str] = Field(default=None, description="Column if applicable")
    violated_value: Any = Field(
        default=None, description="Value that violated constraint"
    )
    error_message: str = Field(..., description="Error message")

    model_config = {"populate_by_name": True}


class QueryPlan(BaseModel):
    """Represents a query execution plan."""

    query: str = Field(..., description="SQL query")
    plan_type: str = Field(
        default="unknown", description="Type of plan (sequential, index, etc.)"
    )
    estimated_cost: float = Field(default=0.0, description="Estimated cost")
    estimated_rows: int = Field(default=0, description="Estimated rows")
    actual_time_ms: float = Field(default=0.0, description="Actual execution time")
    index_usage: List[str] = Field(default_factory=list, description="Indexes used")
    full_table_scans: List[str] = Field(
        default_factory=list, description="Tables with full scans"
    )
    joins: List[Dict[str, Any]] = Field(
        default_factory=list, description="Join operations"
    )

    model_config = {"populate_by_name": True}


class DeadlockInfo(BaseModel):
    """Information about a deadlock."""

    transaction_id: str = Field(..., description="Transaction ID")
    blocked_by: str = Field(..., description="Blocking transaction")
    resource_type: str = Field(..., description="Type of resource (table, row, etc.)")
    resource_name: str = Field(..., description="Name of resource")
    wait_time_ms: int = Field(default=0, description="Wait time in milliseconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"populate_by_name": True}


class IntegrityCheck(BaseModel):
    """Result of an integrity check."""

    id: str = Field(..., description="Check ID")
    check_type: str = Field(..., description="Type of integrity check")
    table_name: str = Field(..., description="Table checked")
    constraint_name: Optional[str] = Field(
        default=None, description="Constraint name if applicable"
    )
    passed: bool = Field(default=False, description="Whether check passed")
    violations: List[ConstraintViolation] = Field(
        default_factory=list, description="Violations found"
    )
    duration_ms: float = Field(default=0.0, description="Check duration")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"populate_by_name": True}


class QueryPerformance(BaseModel):
    """Performance metrics for a query."""

    id: str = Field(..., description="Query ID")
    query: str = Field(..., description="SQL query")
    execution_time_ms: float = Field(default=0.0, description="Execution time")
    rows_affected: int = Field(default=0, description="Rows affected")
    rows_returned: int = Field(default=0, description="Rows returned")
    query_plan: Optional[QueryPlan] = Field(default=None, description="Execution plan")
    is_slow: bool = Field(default=False, description="Whether query is slow")
    threshold_ms: float = Field(default=1000.0, description="Threshold for slow query")
    recommendations: List[str] = Field(
        default_factory=list, description="Performance recommendations"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"populate_by_name": True}


class TransactionTest(BaseModel):
    """Result of a transaction test."""

    id: str = Field(..., description="Test ID")
    test_name: str = Field(..., description="Name of test")
    isolation_level: IsolationLevel = Field(default=IsolationLevel.READ_COMMITTED)
    acid_compliant: bool = Field(default=True, description="ACID compliance result")
    atomicity_passed: bool = Field(default=True)
    consistency_passed: bool = Field(default=True)
    isolation_passed: bool = Field(default=True)
    durability_passed: bool = Field(default=True)
    deadlocks_detected: List[DeadlockInfo] = Field(default_factory=list)
    duration_ms: float = Field(default=0.0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"populate_by_name": True}


class MigrationTest(BaseModel):
    """Result of a migration test."""

    id: str = Field(..., description="Test ID")
    migration_name: str = Field(..., description="Migration name/version")
    direction: str = Field(default="up", description="up or down")
    success: bool = Field(default=False)
    execution_time_ms: float = Field(default=0.0)
    rows_affected: int = Field(default=0)
    schema_changes: List[Dict[str, Any]] = Field(default_factory=list)
    data_transformations: List[Dict[str, Any]] = Field(default_factory=list)
    rollback_success: Optional[bool] = Field(default=None)
    rollback_time_ms: Optional[float] = Field(default=None)
    errors: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"populate_by_name": True}


class DatabaseTestResult(BaseModel):
    """Complete database testing result."""

    id: str = Field(..., description="Result ID")
    database_type: DatabaseType = Field(..., description="Type of database tested")
    database_name: str = Field(..., description="Database name")
    test_timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Results by category
    integrity_checks: List[IntegrityCheck] = Field(default_factory=list)
    query_performances: List[QueryPerformance] = Field(default_factory=list)
    transaction_tests: List[TransactionTest] = Field(default_factory=list)
    migration_tests: List[MigrationTest] = Field(default_factory=list)

    # Summary
    total_checks: int = Field(default=0)
    passed_checks: int = Field(default=0)
    failed_checks: int = Field(default=0)
    warnings: List[str] = Field(default_factory=list)

    # Performance summary
    slow_queries_count: int = Field(default=0)
    deadlocks_count: int = Field(default=0)
    constraint_violations_count: int = Field(default=0)

    model_config = {"populate_by_name": True}
