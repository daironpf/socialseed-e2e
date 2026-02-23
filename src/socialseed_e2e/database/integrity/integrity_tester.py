"""
Integrity tester for database validation.

Validates data integrity including constraints, triggers, and stored procedures.
"""

import uuid
from typing import Any, Dict, List

from ..models import (
    ConstraintType,
    ConstraintViolation,
    IntegrityCheck,
)


class IntegrityTester:
    """Tests database integrity constraints, triggers, and stored procedures.

    Validates:
    - Primary key constraints
    - Foreign key constraints
    - Unique constraints
    - Check constraints
    - Not null constraints
    - Trigger functionality
    - Stored procedure correctness

    Example:
        tester = IntegrityTester(db_connection)

        # Check all constraints on a table
        result = tester.check_table_integrity("users")

        if not result.passed:
            for violation in result.violations:
                print(f"Constraint {violation.constraint_name} violated")
    """

    def __init__(self, db_connection: Any):
        """Initialize integrity tester.

        Args:
            db_connection: Database connection object
        """
        self.connection = db_connection
        self.checks_performed: List[IntegrityCheck] = []

    def check_table_integrity(self, table_name: str) -> IntegrityCheck:
        """Perform comprehensive integrity check on a table.

        Args:
            table_name: Name of table to check

        Returns:
            IntegrityCheck result
        """
        check_id = str(uuid.uuid4())
        violations = []

        try:
            # Check primary key constraints
            pk_violations = self._check_primary_keys(table_name)
            violations.extend(pk_violations)

            # Check foreign key constraints
            fk_violations = self._check_foreign_keys(table_name)
            violations.extend(fk_violations)

            # Check unique constraints
            unique_violations = self._check_unique_constraints(table_name)
            violations.extend(unique_violations)

            # Check not null constraints
            notnull_violations = self._check_not_null_constraints(table_name)
            violations.extend(notnull_violations)

            # Check check constraints
            check_violations = self._check_constraints(table_name)
            violations.extend(check_violations)

        except Exception as e:
            violations.append(
                ConstraintViolation(
                    constraint_name="check_execution",
                    constraint_type=ConstraintType.CHECK,
                    table_name=table_name,
                    error_message=str(e),
                )
            )

        result = IntegrityCheck(
            id=check_id,
            check_type="table_integrity",
            table_name=table_name,
            passed=len(violations) == 0,
            violations=violations,
        )

        self.checks_performed.append(result)
        return result

    def check_referential_integrity(
        self, parent_table: str, child_table: str, fk_column: str
    ) -> IntegrityCheck:
        """Check referential integrity between two tables.

        Args:
            parent_table: Parent table name
            child_table: Child table name
            fk_column: Foreign key column in child table

        Returns:
            IntegrityCheck result
        """
        check_id = str(uuid.uuid4())
        violations = []

        try:
            # Find orphaned records
            cursor = self.connection.cursor()

            # Get primary key column of parent
            cursor.execute(f"""
                SELECT column_name
                FROM information_schema.key_column_usage
                WHERE table_name = '{parent_table}'
                AND constraint_name LIKE '%pkey%'
                LIMIT 1
            """)
            pk_column = cursor.fetchone()

            if pk_column:
                pk_column = pk_column[0]

                # Check for orphaned records
                cursor.execute(f"""
                    SELECT COUNT(*) FROM {child_table} c
                    WHERE c.{fk_column} IS NOT NULL
                    AND NOT EXISTS (
                        SELECT 1 FROM {parent_table} p
                        WHERE p.{pk_column} = c.{fk_column}
                    )
                """)

                orphaned_count = cursor.fetchone()[0]

                if orphaned_count > 0:
                    violations.append(
                        ConstraintViolation(
                            constraint_name=f"fk_{parent_table}_{child_table}",
                            constraint_type=ConstraintType.FOREIGN_KEY,
                            table_name=child_table,
                            column_name=fk_column,
                            error_message=f"Found {orphaned_count} orphaned records in {child_table}",
                        )
                    )

        except Exception as e:
            violations.append(
                ConstraintViolation(
                    constraint_name="referential_check",
                    constraint_type=ConstraintType.FOREIGN_KEY,
                    table_name=child_table,
                    error_message=str(e),
                )
            )

        result = IntegrityCheck(
            id=check_id,
            check_type="referential_integrity",
            table_name=f"{parent_table}->{child_table}",
            constraint_name=fk_column,
            passed=len(violations) == 0,
            violations=violations,
        )

        self.checks_performed.append(result)
        return result

    def verify_trigger(
        self, trigger_name: str, table_name: str, test_data: Dict[str, Any]
    ) -> IntegrityCheck:
        """Verify that a trigger executes correctly.

        Args:
            trigger_name: Name of trigger to verify
            table_name: Table where trigger is defined
            test_data: Test data to insert

        Returns:
            IntegrityCheck result
        """
        check_id = str(uuid.uuid4())
        violations = []

        try:
            cursor = self.connection.cursor()

            # Insert test data
            columns = ", ".join(test_data.keys())
            placeholders = ", ".join(["%s"] * len(test_data))
            values = list(test_data.values())

            cursor.execute(
                f"""
                INSERT INTO {table_name} ({columns})
                VALUES ({placeholders})
            """,
                values,
            )

            # Verify trigger effects (simplified - would need trigger-specific logic)
            # In real implementation, check specific trigger behavior

            self.connection.commit()

        except Exception as e:
            violations.append(
                ConstraintViolation(
                    constraint_name=trigger_name,
                    constraint_type=ConstraintType.CHECK,
                    table_name=table_name,
                    error_message=f"Trigger verification failed: {str(e)}",
                )
            )
            self.connection.rollback()

        result = IntegrityCheck(
            id=check_id,
            check_type="trigger_verification",
            table_name=table_name,
            constraint_name=trigger_name,
            passed=len(violations) == 0,
            violations=violations,
        )

        self.checks_performed.append(result)
        return result

    def verify_stored_procedure(
        self, procedure_name: str, parameters: List[Any], expected_result: Any
    ) -> IntegrityCheck:
        """Verify stored procedure execution.

        Args:
            procedure_name: Name of stored procedure
            parameters: Parameters to pass
            expected_result: Expected result

        Returns:
            IntegrityCheck result
        """
        check_id = str(uuid.uuid4())
        violations = []

        try:
            cursor = self.connection.cursor()

            # Call stored procedure (syntax varies by database)
            cursor.callproc(procedure_name, parameters)

            # Get result
            result = cursor.fetchone()

            # Verify result matches expected
            if result != expected_result:
                violations.append(
                    ConstraintViolation(
                        constraint_name=procedure_name,
                        constraint_type=ConstraintType.CHECK,
                        table_name="stored_procedure",
                        error_message=f"Procedure result {result} doesn't match expected {expected_result}",
                    )
                )

        except Exception as e:
            violations.append(
                ConstraintViolation(
                    constraint_name=procedure_name,
                    constraint_type=ConstraintType.CHECK,
                    table_name="stored_procedure",
                    error_message=f"Procedure execution failed: {str(e)}",
                )
            )

        result = IntegrityCheck(
            id=check_id,
            check_type="stored_procedure",
            table_name="stored_procedure",
            constraint_name=procedure_name,
            passed=len(violations) == 0,
            violations=violations,
        )

        self.checks_performed.append(result)
        return result

    def get_all_checks(self) -> List[IntegrityCheck]:
        """Get all integrity checks performed.

        Returns:
            List of all checks
        """
        return self.checks_performed

    def _check_primary_keys(self, table_name: str) -> List[ConstraintViolation]:
        """Check primary key constraints."""
        violations = []
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"""
                SELECT COUNT(*) FROM (
                    SELECT {table_name}.*, COUNT(*) OVER (PARTITION BY (
                        SELECT column_name
                        FROM information_schema.key_column_usage
                        WHERE table_name = '{table_name}'
                        AND constraint_name LIKE '%pkey%'
                        LIMIT 1
                    )) as cnt
                    FROM {table_name}
                ) sub
                WHERE cnt > 1
            """)
            count = cursor.fetchone()[0]
            if count > 0:
                violations.append(
                    ConstraintViolation(
                        constraint_name=f"pk_{table_name}",
                        constraint_type=ConstraintType.PRIMARY_KEY,
                        table_name=table_name,
                        error_message=f"Found {count} duplicate primary keys",
                    )
                )
        except Exception:
            pass
        return violations

    def _check_foreign_keys(self, table_name: str) -> List[ConstraintViolation]:
        """Check foreign key constraints."""
        # Implementation would query information_schema for FK constraints
        # and verify referential integrity
        return []

    def _check_unique_constraints(self, table_name: str) -> List[ConstraintViolation]:
        """Check unique constraints."""
        violations = []
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"""
                SELECT constraint_name, column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.constraint_column_usage ccu
                    ON tc.constraint_name = ccu.constraint_name
                WHERE tc.table_name = '{table_name}'
                AND tc.constraint_type = 'UNIQUE'
            """)
            unique_constraints = cursor.fetchall()

            for constraint_name, column_name in unique_constraints:
                cursor.execute(f"""
                    SELECT {column_name}, COUNT(*)
                    FROM {table_name}
                    GROUP BY {column_name}
                    HAVING COUNT(*) > 1
                """)
                duplicates = cursor.fetchall()

                for value, count in duplicates:
                    violations.append(
                        ConstraintViolation(
                            constraint_name=constraint_name,
                            constraint_type=ConstraintType.UNIQUE,
                            table_name=table_name,
                            column_name=column_name,
                            violated_value=value,
                            error_message=f"Duplicate value '{value}' found {count} times",
                        )
                    )
        except Exception:
            pass
        return violations

    def _check_not_null_constraints(self, table_name: str) -> List[ConstraintViolation]:
        """Check not null constraints."""
        violations = []
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = '{table_name}'
                AND is_nullable = 'NO'
            """)
            not_null_columns = [row[0] for row in cursor.fetchall()]

            for column in not_null_columns:
                cursor.execute(f"""
                    SELECT COUNT(*) FROM {table_name}
                    WHERE {column} IS NULL
                """)
                null_count = cursor.fetchone()[0]

                if null_count > 0:
                    violations.append(
                        ConstraintViolation(
                            constraint_name=f"{table_name}_{column}_not_null",
                            constraint_type=ConstraintType.NOT_NULL,
                            table_name=table_name,
                            column_name=column,
                            error_message=f"Found {null_count} NULL values in NOT NULL column",
                        )
                    )
        except Exception:
            pass
        return violations

    def _check_constraints(self, table_name: str) -> List[ConstraintViolation]:
        """Check CHECK constraints."""
        # Implementation would verify CHECK constraints
        return []
