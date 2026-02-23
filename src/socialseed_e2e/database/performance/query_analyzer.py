"""
Query performance analyzer for database testing.

Analyzes query performance, execution plans, and provides optimization recommendations.
"""

import re
import time
import uuid
from typing import Any, Dict, List, Optional

from ..models import QueryPerformance, QueryPlan


class QueryAnalyzer:
    """Analyzes database query performance and execution plans.

    Provides:
    - Query execution time analysis
    - Execution plan analysis
    - Index usage verification
    - Slow query detection
    - Performance recommendations

    Example:
        analyzer = QueryAnalyzer(db_connection)

        # Analyze a query
        result = analyzer.analyze_query(
            "SELECT * FROM users WHERE email = 'test@example.com'",
            threshold_ms=100
        )

        if result.is_slow:
            print("Slow query detected!")
            for rec in result.recommendations:
                print(f"  - {rec}")
    """

    def __init__(self, db_connection: Any):
        """Initialize query analyzer.

        Args:
            db_connection: Database connection object
        """
        self.connection = db_connection
        self.analyzed_queries: List[QueryPerformance] = []

    def analyze_query(
        self,
        query: str,
        threshold_ms: float = 1000.0,
        parameters: Optional[List[Any]] = None,
    ) -> QueryPerformance:
        """Analyze a single query's performance.

        Args:
            query: SQL query to analyze
            threshold_ms: Threshold for slow query detection
            parameters: Query parameters

        Returns:
            QueryPerformance result
        """
        query_id = str(uuid.uuid4())
        parameters = parameters or []

        try:
            cursor = self.connection.cursor()

            # Get execution plan
            plan = self._get_query_plan(query, parameters)

            # Measure execution time
            start_time = time.time()
            cursor.execute(query, parameters)
            execution_time = (time.time() - start_time) * 1000

            # Get affected/returned rows
            if cursor.description:
                rows_returned = len(cursor.fetchall())
                rows_affected = 0
            else:
                rows_returned = 0
                rows_affected = cursor.rowcount

            # Generate recommendations
            recommendations = self._generate_recommendations(
                query, plan, execution_time
            )

            result = QueryPerformance(
                id=query_id,
                query=query,
                execution_time_ms=execution_time,
                rows_affected=rows_affected,
                rows_returned=rows_returned,
                query_plan=plan,
                is_slow=execution_time > threshold_ms,
                threshold_ms=threshold_ms,
                recommendations=recommendations,
            )

        except Exception as e:
            result = QueryPerformance(
                id=query_id,
                query=query,
                execution_time_ms=0.0,
                is_slow=True,
                threshold_ms=threshold_ms,
                recommendations=[f"Query execution failed: {str(e)}"],
            )

        self.analyzed_queries.append(result)
        return result

    def find_slow_queries(
        self,
        threshold_ms: float = 1000.0,
        limit: int = 10,
    ) -> List[QueryPerformance]:
        """Find slow queries from query log.

        Args:
            threshold_ms: Threshold for slow query
            limit: Maximum number of queries to return

        Returns:
            List of slow queries
        """
        slow_queries = []

        try:
            cursor = self.connection.cursor()

            # Query database-specific slow query log
            # This is a simplified version - actual implementation depends on DB
            cursor.execute(
                """
                SELECT query, calls, total_time, mean_time, rows
                FROM pg_stat_statements
                WHERE mean_time > %s
                ORDER BY mean_time DESC
                LIMIT %s
            """,
                (threshold_ms, limit),
            )

            for row in cursor.fetchall():
                query, calls, total_time, mean_time, rows = row

                perf = QueryPerformance(
                    id=str(uuid.uuid4()),
                    query=query,
                    execution_time_ms=mean_time,
                    rows_returned=rows,
                    is_slow=True,
                    threshold_ms=threshold_ms,
                )
                slow_queries.append(perf)

        except Exception:
            # Fallback: use analyzed queries
            slow_queries = [q for q in self.analyzed_queries if q.is_slow][:limit]

        return slow_queries

    def analyze_index_usage(self, table_name: str) -> Dict[str, Any]:
        """Analyze index usage for a table.

        Args:
            table_name: Table to analyze

        Returns:
            Index usage statistics
        """
        try:
            cursor = self.connection.cursor()

            # Get index statistics (PostgreSQL-specific)
            cursor.execute(
                """
                SELECT
                    schemaname,
                    tablename,
                    indexrelname,
                    idx_scan,
                    idx_tup_read,
                    idx_tup_fetch
                FROM pg_stat_user_indexes
                WHERE tablename = %s
                ORDER BY idx_scan DESC
            """,
                (table_name,),
            )

            indexes = []
            for row in cursor.fetchall():
                indexes.append(
                    {
                        "index_name": row[2],
                        "scans": row[3],
                        "tuples_read": row[4],
                        "tuples_fetched": row[5],
                    }
                )

            return {
                "table": table_name,
                "indexes": indexes,
                "recommendations": self._suggest_indexes(table_name),
            }

        except Exception as e:
            return {
                "table": table_name,
                "error": str(e),
                "indexes": [],
                "recommendations": [],
            }

    def get_missing_indexes(self) -> List[Dict[str, Any]]:
        """Identify columns that would benefit from indexing.

        Returns:
            List of missing index suggestions
        """
        missing_indexes = []

        try:
            cursor = self.connection.cursor()

            # Find frequently filtered columns without indexes
            cursor.execute("""
                SELECT
                    schemaname,
                    tablename,
                    attname as column_name,
                    n_tup_read,
                    n_tup_fetch
                FROM pg_stats
                WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
                AND n_tup_read > 1000
                ORDER BY n_tup_read DESC
                LIMIT 20
            """)

            for row in cursor.fetchall():
                missing_indexes.append(
                    {
                        "schema": row[0],
                        "table": row[1],
                        "column": row[2],
                        "suggestion": f"CREATE INDEX idx_{row[1]}_{row[2]} ON {row[1]}({row[2]});",
                    }
                )

        except Exception:
            pass

        return missing_indexes

    def get_all_analyzed_queries(self) -> List[QueryPerformance]:
        """Get all analyzed queries.

        Returns:
            List of all query analyses
        """
        return self.analyzed_queries

    def _get_query_plan(self, query: str, parameters: List[Any]) -> QueryPlan:
        """Get execution plan for a query.

        Args:
            query: SQL query
            parameters: Query parameters

        Returns:
            QueryPlan object
        """
        try:
            cursor = self.connection.cursor()

            # Execute EXPLAIN
            cursor.execute(f"EXPLAIN (FORMAT JSON) {query}", parameters)
            plan_data = cursor.fetchone()[0]

            # Parse plan (simplified)
            if isinstance(plan_data, list) and len(plan_data) > 0:
                plan_info = plan_data[0].get("Plan", {})

                return QueryPlan(
                    query=query,
                    plan_type=plan_info.get("Node Type", "unknown"),
                    estimated_cost=plan_info.get("Total Cost", 0.0),
                    estimated_rows=plan_info.get("Plan Rows", 0),
                    index_usage=self._extract_index_usage(plan_info),
                    full_table_scans=self._extract_table_scans(plan_info),
                )

        except Exception:
            pass

        return QueryPlan(query=query)

    def _generate_recommendations(
        self,
        query: str,
        plan: Optional[QueryPlan],
        execution_time: float,
    ) -> List[str]:
        """Generate performance recommendations.

        Args:
            query: SQL query
            plan: Query execution plan
            execution_time: Execution time in ms

        Returns:
            List of recommendations
        """
        recommendations = []

        # Check for slow execution
        if execution_time > 1000:
            recommendations.append(
                f"Query is slow ({execution_time:.0f}ms). Consider optimization."
            )

        # Check for full table scans
        if plan and plan.full_table_scans:
            for table in plan.full_table_scans:
                recommendations.append(
                    f"Full table scan on '{table}'. Consider adding an index."
                )

        # Check for SELECT *
        if re.search(r"SELECT\s+\*", query, re.IGNORECASE):
            recommendations.append("Avoid SELECT *. Specify only needed columns.")

        # Check for missing WHERE clause
        if (
            re.search(r"SELECT.*FROM", query, re.IGNORECASE)
            and "WHERE" not in query.upper()
        ):
            recommendations.append(
                "Query lacks WHERE clause. May return too many rows."
            )

        # Check for N+1 query pattern
        if execution_time < 10 and "WHERE" in query.upper():
            recommendations.append(
                "Fast query with filter. Check for N+1 query pattern in application."
            )

        return recommendations

    def _extract_index_usage(self, plan_info: Dict[str, Any]) -> List[str]:
        """Extract index usage from plan."""
        indexes = []

        if "Index Name" in plan_info:
            indexes.append(plan_info["Index Name"])

        # Recurse into sub-plans
        if "Plans" in plan_info:
            for sub_plan in plan_info["Plans"]:
                indexes.extend(self._extract_index_usage(sub_plan))

        return indexes

    def _extract_table_scans(self, plan_info: Dict[str, Any]) -> List[str]:
        """Extract tables with full scans."""
        scans = []

        if plan_info.get("Node Type") == "Seq Scan":
            if "Relation Name" in plan_info:
                scans.append(plan_info["Relation Name"])

        # Recurse into sub-plans
        if "Plans" in plan_info:
            for sub_plan in plan_info["Plans"]:
                scans.extend(self._extract_table_scans(sub_plan))

        return scans

    def _suggest_indexes(self, table_name: str) -> List[str]:
        """Suggest indexes for a table."""
        suggestions = []

        try:
            cursor = self.connection.cursor()

            # Find columns frequently used in WHERE clauses
            cursor.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = %s
                AND data_type IN ('character varying', 'text', 'integer', 'bigint')
                LIMIT 5
            """,
                (table_name,),
            )

            for row in cursor.fetchall():
                column = row[0]
                suggestions.append(f"Consider index on {column} if frequently filtered")

        except Exception:
            pass

        return suggestions
