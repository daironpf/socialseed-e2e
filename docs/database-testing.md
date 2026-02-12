# Database Testing Support

socialseed-e2e provides comprehensive support for testing both SQL and NoSQL databases. This allows you to verify the actual state of your data, manage test fixtures, and measure query performance.

## Key Features

- **Multi-Database Support**: PostgreSQL, MySQL, SQLite, MongoDB, Redis, and Neo4j.
- **Fixture Management**: Load seed data from JSON or YAML files.
- **State Assertions**: Verify that records exist or that row counts match expectations.
- **Performance Testing**: Assert that queries complete within specified time limits.
- **Transaction Support**: Rollback changes after tests to keep your DB clean.

## Connection Management

Use the `ConnectionManager` to handle your database connections:

```python
from socialseed_e2e.database import ConnectionManager

manager = ConnectionManager()

# Connect to SQLite
sqlite_conn = manager.connect_sql("sqlite", "test.db")

# Connect to PostgreSQL
pg_conn = manager.connect_sql("postgresql", "postgresql://user:pass@localhost/dbname")

# Connect to MongoDB
mongo_client = manager.connect_mongodb("mongodb://localhost:27017")
```

## Fixture Management

Seed your database with test data:

```python
from socialseed_e2e.database import ConnectionManager, FixtureManager

manager = ConnectionManager()
conn = manager.connect_sql("sqlite", ":memory:")

fixtures = FixtureManager(conn)

# Data to seed
users = [
    {"id": 1, "username": "alice", "email": "alice@example.com"},
    {"id": 2, "username": "bob", "email": "bob@example.com"}
]

# Seed a table
fixtures.seed_sql_table("users", users)
```

## Database Assertions

Verify the state of your database after performing actions:

```python
from socialseed_e2e.database.assertions import DatabaseAssertions

db_assert = DatabaseAssertions(conn)

# Assert a record exists
db_assert.assert_sql_row_exists("users", {"username": "alice"})

# Assert row count
db_assert.assert_sql_row_count("users", 2)
```

## Performance Testing

Measure and assert query performance:

```python
from socialseed_e2e.database.performance import QueryPerformance

perf = QueryPerformance(conn)

# Assert query time
perf.assert_sql_query_time("SELECT * FROM users", max_ms=50.0)
```

## Best Practices

1.  **Isolation**: Use transactions or truncate tables before each test to ensure a clean state.
2.  **Environment Sync**: Use the same database type in tests as you use in production when possible.
3.  **Clean Up**: Always close connections using `manager.close_all()` in your teardown phase.
4.  **Schema Consistency**: Use migrations to keep your test database schema in sync with your application.
