"""
Migration tester for database schema and data migrations.

Validates migration scripts, tests rollback procedures, and verifies data transformations.
"""

import time
import uuid
from typing import Any, Callable, Dict, List, Optional

from ..models import MigrationTest


class MigrationTester:
    """Tests database migrations and rollbacks.

    Validates:
    - Migration script correctness
    - Rollback procedures
    - Data transformations
    - Schema changes

    Example:
        tester = MigrationTester(db_connection)

        # Test a migration
        result = tester.test_migration(
            migration_name="add_user_status",
            up_func=migration_up,
            down_func=migration_down
        )

        if result.success and result.rollback_success:
            print("Migration and rollback successful!")
    """

    def __init__(self, db_connection: Any):
        """Initialize migration tester.

        Args:
            db_connection: Database connection object
        """
        self.connection = db_connection
        self.migrations_tested: List[MigrationTest] = []

    def test_migration(
        self,
        migration_name: str,
        up_func: Callable[[Any], None],
        down_func: Callable[[Any], None],
        test_data: Optional[Dict[str, Any]] = None,
    ) -> MigrationTest:
        """Test a single migration with rollback.

        Args:
            migration_name: Name of migration
            up_func: Function to apply migration
            down_func: Function to rollback migration
            test_data: Test data for validation

        Returns:
            MigrationTest result
        """
        test_id = str(uuid.uuid4())
        errors = []

        # Test migration up
        up_result = self._test_migration_up(migration_name, up_func, test_data)

        if not up_result["success"]:
            errors.extend(up_result.get("errors", []))

        # Test migration down (rollback)
        rollback_result = (
            self._test_migration_down(
                migration_name, down_func, up_result.get("schema_changes", [])
            )
            if up_result["success"]
            else {"success": None}
        )

        result = MigrationTest(
            id=test_id,
            migration_name=migration_name,
            direction="up",
            success=up_result["success"],
            execution_time_ms=up_result.get("duration_ms", 0),
            rows_affected=up_result.get("rows_affected", 0),
            schema_changes=up_result.get("schema_changes", []),
            data_transformations=up_result.get("transformations", []),
            rollback_success=rollback_result.get("success"),
            rollback_time_ms=rollback_result.get("duration_ms"),
            errors=errors,
        )

        self.migrations_tested.append(result)
        return result

    def test_migration_chain(
        self,
        migrations: List[Dict[str, Any]],
    ) -> List[MigrationTest]:
        """Test a chain of dependent migrations.

        Args:
            migrations: List of migration definitions

        Returns:
            List of MigrationTest results
        """
        results = []

        for migration in migrations:
            result = self.test_migration(
                migration_name=migration["name"],
                up_func=migration["up"],
                down_func=migration["down"],
                test_data=migration.get("test_data"),
            )
            results.append(result)

            # Stop if migration failed
            if not result.success:
                break

        return results

    def validate_schema_version(
        self,
        expected_version: str,
        version_table: str = "schema_migrations",
    ) -> Dict[str, Any]:
        """Validate current database schema version.

        Args:
            expected_version: Expected schema version
            version_table: Table storing schema versions

        Returns:
            Validation result
        """
        try:
            cursor = self.connection.cursor()

            cursor.execute(f"""
                SELECT version FROM {version_table}
                ORDER BY applied_at DESC
                LIMIT 1
            """)

            row = cursor.fetchone()
            actual_version = row[0] if row else None

            return {
                "valid": actual_version == expected_version,
                "expected_version": expected_version,
                "actual_version": actual_version,
                "message": (
                    f"Schema version matches: {expected_version}"
                    if actual_version == expected_version
                    else f"Version mismatch. Expected: {expected_version}, Got: {actual_version}"
                ),
            }

        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "message": f"Failed to validate schema version: {str(e)}",
            }

    def detect_schema_drift(
        self,
        expected_schema: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Detect if actual schema differs from expected.

        Args:
            expected_schema: Expected schema definition

        Returns:
            Drift detection result
        """
        try:
            cursor = self.connection.cursor()

            drift = {
                "has_drift": False,
                "missing_tables": [],
                "extra_tables": [],
                "column_mismatches": [],
            }

            # Get actual tables
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
            """)
            actual_tables = {row[0] for row in cursor.fetchall()}
            expected_tables = set(expected_schema.keys())

            drift["missing_tables"] = list(expected_tables - actual_tables)
            drift["extra_tables"] = list(actual_tables - expected_tables)

            # Check columns for each expected table
            for table_name in expected_tables & actual_tables:
                cursor.execute(f"""
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_name = '{table_name}'
                """)
                actual_columns = {row[0]: row[1] for row in cursor.fetchall()}
                expected_columns = expected_schema.get(table_name, {}).get(
                    "columns", {}
                )

                for col_name, col_type in expected_columns.items():
                    if col_name not in actual_columns:
                        drift["column_mismatches"].append(
                            {
                                "table": table_name,
                                "column": col_name,
                                "issue": "missing",
                            }
                        )
                    elif actual_columns[col_name] != col_type:
                        drift["column_mismatches"].append(
                            {
                                "table": table_name,
                                "column": col_name,
                                "issue": "type_mismatch",
                                "expected": col_type,
                                "actual": actual_columns[col_name],
                            }
                        )

            drift["has_drift"] = bool(
                drift["missing_tables"]
                or drift["extra_tables"]
                or drift["column_mismatches"]
            )

            return drift

        except Exception as e:
            return {
                "has_drift": True,
                "error": str(e),
            }

    def verify_data_transformation(
        self,
        table_name: str,
        transformation_func: Callable[[Any], Any],
        sample_size: int = 100,
    ) -> Dict[str, Any]:
        """Verify data transformation during migration.

        Args:
            table_name: Table to verify
            transformation_func: Function to apply transformation
            sample_size: Number of rows to sample

        Returns:
            Verification result
        """
        try:
            cursor = self.connection.cursor()

            # Get sample data before transformation
            cursor.execute(f"""
                SELECT * FROM {table_name}
                LIMIT {sample_size}
            """)

            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]

            successful_transforms = 0
            failed_transforms = 0

            for row in rows:
                row_dict = dict(zip(columns, row))
                try:
                    transformation_func(row_dict)
                    successful_transforms += 1
                except Exception:
                    failed_transforms += 1

            return {
                "verified": failed_transforms == 0,
                "sample_size": len(rows),
                "successful_transforms": successful_transforms,
                "failed_transforms": failed_transforms,
                "message": (
                    f"Data transformation verified: {successful_transforms}/{len(rows)} successful"
                    if failed_transforms == 0
                    else f"Data transformation issues: {failed_transforms} failures"
                ),
            }

        except Exception as e:
            return {
                "verified": False,
                "error": str(e),
                "message": f"Failed to verify data transformation: {str(e)}",
            }

    def get_all_migrations(self) -> List[MigrationTest]:
        """Get all migration tests performed.

        Returns:
            List of all migration tests
        """
        return self.migrations_tested

    def _test_migration_up(
        self,
        migration_name: str,
        up_func: Callable[[Any], None],
        test_data: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Test migration up.

        Args:
            migration_name: Migration name
            up_func: Migration function
            test_data: Test data

        Returns:
            Test result
        """
        result = {
            "success": False,
            "duration_ms": 0,
            "rows_affected": 0,
            "schema_changes": [],
            "transformations": [],
            "errors": [],
        }

        try:
            cursor = self.connection.cursor()

            # Record schema before
            before_schema = self._get_current_schema(cursor)

            # Apply migration
            start_time = time.time()
            up_func(self.connection)
            duration = (time.time() - start_time) * 1000

            # Record schema after
            after_schema = self._get_current_schema(cursor)

            # Detect schema changes
            schema_changes = self._detect_schema_changes(before_schema, after_schema)

            # Count rows affected (approximation)
            rows_affected = self._estimate_rows_affected(cursor)

            result.update(
                {
                    "success": True,
                    "duration_ms": duration,
                    "rows_affected": rows_affected,
                    "schema_changes": schema_changes,
                }
            )

            self.connection.commit()

        except Exception as e:
            result["errors"].append(str(e))
            self.connection.rollback()

        return result

    def _test_migration_down(
        self,
        migration_name: str,
        down_func: Callable[[Any], None],
        schema_changes: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Test migration down (rollback).

        Args:
            migration_name: Migration name
            down_func: Rollback function
            schema_changes: Schema changes from migration

        Returns:
            Rollback result
        """
        result = {
            "success": False,
            "duration_ms": 0,
        }

        try:
            # Apply rollback
            start_time = time.time()
            down_func(self.connection)
            duration = (time.time() - start_time) * 1000

            result.update(
                {
                    "success": True,
                    "duration_ms": duration,
                }
            )

            # Rollback the rollback (keep migration applied)
            self.connection.rollback()

        except Exception as e:
            result["error"] = str(e)
            self.connection.rollback()

        return result

    def _get_current_schema(self, cursor: Any) -> Dict[str, Any]:
        """Get current database schema."""
        try:
            cursor.execute("""
                SELECT table_name, column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
            """)

            schema = {}
            for row in cursor.fetchall():
                table, column, data_type = row
                if table not in schema:
                    schema[table] = {"columns": {}}
                schema[table]["columns"][column] = data_type

            return schema

        except Exception:
            return {}

    def _detect_schema_changes(
        self,
        before: Dict[str, Any],
        after: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Detect schema changes between two states."""
        changes = []

        # Find new tables
        for table in after:
            if table not in before:
                changes.append(
                    {
                        "type": "table_added",
                        "table": table,
                        "columns": list(after[table].get("columns", {}).keys()),
                    }
                )

        # Find modified tables
        for table in before:
            if table in after:
                before_cols = set(before[table].get("columns", {}).keys())
                after_cols = set(after[table].get("columns", {}).keys())

                added_cols = after_cols - before_cols
                if added_cols:
                    changes.append(
                        {
                            "type": "columns_added",
                            "table": table,
                            "columns": list(added_cols),
                        }
                    )

        return changes

    def _estimate_rows_affected(self, cursor: Any) -> int:
        """Estimate rows affected by recent operations."""
        try:
            # This is a placeholder - real implementation would track actual changes
            return 0
        except Exception:
            return 0
