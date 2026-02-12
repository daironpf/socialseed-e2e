"""Database-specific assertions for socialseed-e2e."""

from typing import Any, Dict, List, Optional
import unittest

class DatabaseAssertions:
    """Helper for database state assertions."""

    def __init__(self, connection: Any):
        self.connection = connection

    def assert_sql_row_exists(self, table: str, criteria: Dict[str, Any], msg: Optional[str] = None):
        """Assert that at least one row matching the criteria exists in a SQL table."""
        import sqlite3
        cursor = self.connection.cursor()
        
        where_clause = " AND ".join([f"{k} = ?" if isinstance(self.connection, sqlite3.Connection) else f"{k} = %s" for k in criteria.keys()])
        query = f"SELECT COUNT(*) FROM {table} WHERE {where_clause}"
        
        cursor.execute(query, tuple(criteria.values()))
        count = cursor.fetchone()[0]
        
        if count == 0:
            error_msg = msg or f"No row found in {table} matching criteria: {criteria}"
            raise AssertionError(error_msg)

    def assert_sql_row_count(self, table: str, expected_count: int, msg: Optional[str] = None):
        """Assert the total number of rows in a SQL table."""
        cursor = self.connection.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        
        if count != expected_count:
            error_msg = msg or f"Expected {expected_count} rows in {table}, but found {count}"
            raise AssertionError(error_msg)

    def assert_mongo_document_exists(self, db_name: str, collection_name: str, filter: Dict[str, Any], msg: Optional[str] = None):
        """Assert that a document matching the filter exists in MongoDB."""
        db = self.connection[db_name]
        collection = db[collection_name]
        count = collection.count_documents(filter)
        
        if count == 0:
            error_msg = msg or f"No document found in {db_name}.{collection_name} matching filter: {filter}"
            raise AssertionError(error_msg)
            
    def assert_redis_key_exists(self, key: str, msg: Optional[str] = None):
        """Assert that a key exists in Redis."""
        if not self.connection.exists(key):
            error_msg = msg or f"Redis key '{key}' does not exist"
            raise AssertionError(error_msg)
