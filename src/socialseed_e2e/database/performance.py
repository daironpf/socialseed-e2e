"""Database query performance testing for socialseed-e2e."""

import time
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class QueryStats:
    duration_ms: float
    row_count: int
    query: str

class QueryPerformance:
    """Helper for measuring query performance."""

    def __init__(self, connection: Any):
        self.connection = connection

    def measure_sql_query(self, query: str, params: Optional[tuple] = None) -> QueryStats:
        """Measure the execution time of a SQL query."""
        cursor = self.connection.cursor()

        start_time = time.perf_counter()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        rows = cursor.fetchall()
        end_time = time.perf_counter()

        duration_ms = (end_time - start_time) * 1000
        return QueryStats(
            duration_ms=duration_ms,
            row_count=len(rows),
            query=query
        )

    def assert_sql_query_time(self, query: str, max_ms: float, params: Optional[tuple] = None):
        """Assert that a SQL query completes within a specified time limit."""
        stats = self.measure_sql_query(query, params)
        if stats.duration_ms > max_ms:
            raise AssertionError(
                f"Query exceeded time limit of {max_ms}ms (took {stats.duration_ms:.2f}ms): {query}"
            )

    def measure_mongo_query(self, db_name: str, collection_name: str, filter: Dict[str, Any]) -> QueryStats:
        """Measure the execution time of a MongoDB query."""
        collection = self.connection[db_name][collection_name]

        start_time = time.perf_counter()
        results = list(collection.find(filter))
        end_time = time.perf_counter()

        duration_ms = (end_time - start_time) * 1000
        return QueryStats(
            duration_ms=duration_ms,
            row_count=len(results),
            query=str(filter)
        )
