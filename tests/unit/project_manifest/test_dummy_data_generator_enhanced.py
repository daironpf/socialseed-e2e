"""Unit tests for AI-Powered Context-Aware Dummy Data Generator.

Tests for Issue #109: Enhanced dummy data generation with:
- Foreign key relationship support
- Business rule understanding
- Edge case generation
- Data anonymization
"""

from datetime import date, datetime
from typing import Dict, List

import pytest

from socialseed_e2e.project_manifest.db_model_parsers import (
    ColumnInfo,
    DatabaseSchema,
    EntityInfo,
    EntityRelationship,
)
from socialseed_e2e.project_manifest.dummy_data_generator import (
    AnonymizationRule,
    BusinessRule,
    DataGenerationStrategy,
    DummyDataGenerator,
    EdgeCaseScenario,
)
from socialseed_e2e.project_manifest.models import DtoField, DtoSchema, ValidationRule


class TestBusinessRules:
    """Test business rules integration."""

    def test_email_business_rule(self):
        """Test email format business rule."""
        generator = DummyDataGenerator()

        # Check that email rule is initialized
        email_rules = [r for r in generator._business_rules if r.rule_type == "email_format"]
        assert len(email_rules) > 0
        assert email_rules[0].field_pattern == r".*email.*"

    def test_date_range_business_rule(self):
        """Test date range business rule."""
        generator = DummyDataGenerator()

        date_rules = [r for r in generator._business_rules if r.rule_type == "date_range"]
        assert len(date_rules) >= 2  # Should have birth date and future date rules


class TestEntityGraphGeneration:
    """Test entity graph generation with relationships."""

    def test_generate_entity_graph(self):
        """Test generating complete entity graph."""
        # Create parent entity (User)
        user_entity = EntityInfo(
            name="User",
            table_name="users",
            columns=[
                ColumnInfo(name="id", data_type="int", primary_key=True),
                ColumnInfo(name="name", data_type="str"),
                ColumnInfo(name="email", data_type="str"),
            ],
            primary_keys=["id"],
        )

        # Create child entity (Post) with FK
        post_entity = EntityInfo(
            name="Post",
            table_name="posts",
            columns=[
                ColumnInfo(name="id", data_type="int", primary_key=True),
                ColumnInfo(name="title", data_type="str"),
                ColumnInfo(name="user_id", data_type="int", foreign_key="users.id"),
            ],
            primary_keys=["id"],
            relationships=[
                EntityRelationship(
                    source_entity="Post",
                    target_entity="User",
                    relationship_type="many-to-one",
                    source_column="user_id",
                    target_column="id",
                )
            ],
        )

        # Create schema
        schema = DatabaseSchema(entities=[user_entity, post_entity])
        generator = DummyDataGenerator(db_schema=schema)

        # Generate graph
        result = generator.generate_entity_graph(user_entity, depth=2, records_per_level=2)

        # Verify
        assert "User" in result
        assert len(result["User"]) == 2
        # Each user should have an id
        for user in result["User"]:
            assert "id" in user
            assert user["id"] is not None


class TestConstraintSatisfaction:
    """Test constraint satisfaction system."""

    def test_generate_with_constraints(self):
        """Test generating data satisfying constraints."""
        entity = EntityInfo(
            name="Product",
            table_name="products",
            columns=[
                ColumnInfo(name="id", data_type="int", primary_key=True),
                ColumnInfo(name="name", data_type="str"),
                ColumnInfo(name="price", data_type="float"),
                ColumnInfo(name="quantity", data_type="int"),
            ],
            primary_keys=["id"],
        )

        generator = DummyDataGenerator()

        # Generate with constraints
        constraints = {
            "price": {"ge": 10.0, "le": 100.0},
            "quantity": {"ge": 0, "le": 100},
        }

        data = generator.generate_with_constraints(entity, constraints)

        # Verify constraints are satisfied
        assert "price" in data
        assert "quantity" in data
        assert data["price"].value >= 10.0
        assert data["price"].value <= 100.0
        assert data["quantity"].value >= 0
        assert data["quantity"].value <= 100

    def test_check_constraint(self):
        """Test constraint checking logic."""
        generator = DummyDataGenerator()

        # Test various constraints
        assert generator._check_constraint(5, {"gt": 3}) is True
        assert generator._check_constraint(5, {"gt": 5}) is False
        assert generator._check_constraint(5, {"ge": 5}) is True
        assert generator._check_constraint(5, {"lt": 10}) is True
        assert generator._check_constraint(5, {"eq": 5}) is True
        assert generator._check_constraint(5, {"eq": 3}) is False
        assert generator._check_constraint("test", {"regex": r"^test$"}) is True


class TestEdgeCaseGeneration:
    """Test comprehensive edge case generation."""

    def test_generate_edge_cases_comprehensive(self):
        """Test generating comprehensive edge cases."""
        dto = DtoSchema(
            name="UserDTO",
            file_path="test/dto.py",
            fields=[
                DtoField(
                    name="username",
                    type="str",
                    required=True,
                    validations=[
                        ValidationRule(rule_type="min_length", value=3),
                        ValidationRule(rule_type="max_length", value=20),
                    ],
                ),
                DtoField(
                    name="age",
                    type="int",
                    required=False,
                    validations=[
                        ValidationRule(rule_type="gt", value=0),
                        ValidationRule(rule_type="lt", value=150),
                    ],
                ),
            ],
        )

        generator = DummyDataGenerator()
        scenarios = generator.generate_edge_cases_comprehensive(dto)

        # Should generate multiple scenarios
        assert len(scenarios) > 0

        # Check for boundary cases
        boundary_cases = [s for s in scenarios if s.category == "boundary"]
        assert len(boundary_cases) > 0

        # Check for null cases
        null_cases = [s for s in scenarios if s.category == "null"]
        assert len(null_cases) >= 2  # One for optional, one for null case

    def test_generate_field_edge_cases_string(self):
        """Test edge cases for string fields."""
        generator = DummyDataGenerator()

        field = DtoField(
            name="username",
            type="str",
            required=True,
            validations=[
                ValidationRule(rule_type="min_length", value=5),
                ValidationRule(rule_type="max_length", value=50),
            ],
        )

        scenarios = generator._generate_field_edge_cases(field)

        # Should include boundary cases
        at_min = [s for s in scenarios if "At Min Length" in s.name]
        below_min = [s for s in scenarios if "Below Min Length" in s.name]
        at_max = [s for s in scenarios if "At Max Length" in s.name]

        assert len(at_min) > 0
        assert len(below_min) > 0
        assert len(at_max) > 0

        # Check values
        at_min_case = at_min[0]
        assert at_min_case.value == "x" * 5

    def test_generate_field_edge_cases_numeric(self):
        """Test edge cases for numeric fields."""
        generator = DummyDataGenerator()

        field = DtoField(
            name="age",
            type="int",
            required=True,
            validations=[
                ValidationRule(rule_type="gt", value=0),
                ValidationRule(rule_type="lt", value=150),
            ],
        )

        scenarios = generator._generate_field_edge_cases(field)

        # Should include boundary cases
        just_above = [s for s in scenarios if "Just Above" in s.name]
        extreme = [s for s in scenarios if s.category == "extreme"]

        assert len(just_above) > 0
        assert len(extreme) >= 2  # Zero and negative


class TestDataAnonymization:
    """Test data anonymization features."""

    def test_anonymize_email(self):
        """Test email anonymization."""
        generator = DummyDataGenerator()

        original = "john.doe@example.com"
        anonymized = generator._anonymize_email(original)

        # Should mask local part
        assert "@" in anonymized
        assert "example.com" in anonymized
        assert "***" in anonymized or "jo" not in anonymized.lower()

    def test_anonymize_phone(self):
        """Test phone number anonymization."""
        generator = DummyDataGenerator()

        original = "+1-555-123-4567"
        anonymized = generator._anonymize_phone(original)

        # Should show only last 4 digits
        assert "4567" in anonymized
        assert "***" in anonymized or "555" not in anonymized

    def test_anonymize_name(self):
        """Test name anonymization."""
        generator = DummyDataGenerator()

        original = "John Michael Doe"
        anonymized = generator._anonymize_name(original)

        # Should be initials
        assert "J." in anonymized or "J" in anonymized
        assert "D." in anonymized or "D" in anonymized
        assert "John" not in anonymized

    def test_anonymize_data(self):
        """Test full data anonymization."""
        generator = DummyDataGenerator()

        data = {
            "id": 123,
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "+1-555-123-4567",
            "address": "123 Main St",
            "active": True,
        }

        anonymized = generator.anonymize_data(data)

        # Sensitive fields should be anonymized
        assert anonymized["email"] != data["email"]
        assert anonymized["phone"] != data["phone"]
        assert anonymized["name"] != data["name"]

        # Non-sensitive fields should remain
        assert anonymized["id"] == data["id"]
        assert anonymized["active"] == data["active"]

    def test_add_custom_anonymization_rule(self):
        """Test adding custom anonymization rules."""
        generator = DummyDataGenerator()

        rule = AnonymizationRule(
            field_pattern=r".*custom.*",
            method="hash",
            preserve_format=False,
        )

        generator.add_anonymization_rule(rule)
        assert len(generator._anonymization_rules) > 0

    def test_is_sensitive_field(self):
        """Test sensitive field detection."""
        generator = DummyDataGenerator()

        assert generator._is_sensitive_field("password") is True
        assert generator._is_sensitive_field("email") is True
        assert generator._is_sensitive_field("phone_number") is True
        assert generator._is_sensitive_field("ssn") is True
        assert generator._is_sensitive_field("status") is False
        assert generator._is_sensitive_field("count") is False


class TestForeignKeyGeneration:
    """Test foreign key value generation."""

    def test_generate_valid_fk_value(self):
        """Test generating valid foreign key values."""
        # Create referenced entity
        user_entity = EntityInfo(
            name="User",
            table_name="users",
            columns=[
                ColumnInfo(name="id", data_type="int", primary_key=True),
                ColumnInfo(name="name", data_type="str"),
            ],
            primary_keys=["id"],
        )

        # Create referencing entity
        post_entity = EntityInfo(
            name="Post",
            table_name="posts",
            columns=[
                ColumnInfo(name="id", data_type="int", primary_key=True),
                ColumnInfo(
                    name="user_id",
                    data_type="int",
                    foreign_key="users.id",
                ),
            ],
            primary_keys=["id"],
        )

        schema = DatabaseSchema(entities=[user_entity, post_entity])
        generator = DummyDataGenerator(db_schema=schema)

        # Generate FK value
        fk_column = post_entity.columns[1]
        fk_value = generator.generate_valid_fk_value(post_entity, fk_column)

        # Should be a valid integer
        assert isinstance(fk_value, int)

        # Should be cached
        assert "users.id" in generator._fk_value_cache

    def test_validate_referential_integrity(self):
        """Test referential integrity validation."""
        user_entity = EntityInfo(
            name="User",
            table_name="users",
            columns=[
                ColumnInfo(name="id", data_type="int", primary_key=True),
            ],
            primary_keys=["id"],
        )

        post_entity = EntityInfo(
            name="Post",
            table_name="posts",
            columns=[
                ColumnInfo(name="id", data_type="int", primary_key=True),
                ColumnInfo(
                    name="user_id",
                    data_type="int",
                    foreign_key="users.id",
                ),
            ],
            primary_keys=["id"],
        )

        schema = DatabaseSchema(entities=[user_entity, post_entity])
        generator = DummyDataGenerator(db_schema=schema)

        # Pre-populate cache with valid IDs
        generator._fk_value_cache["users.id"] = [1, 2, 3]

        # Valid data
        valid_data = {"id": 1, "user_id": 2}
        is_valid, errors = generator.validate_referential_integrity(valid_data, post_entity)
        assert is_valid is True
        assert len(errors) == 0

        # Invalid data
        invalid_data = {"id": 1, "user_id": 999}
        is_valid, errors = generator.validate_referential_integrity(invalid_data, post_entity)
        assert is_valid is False
        assert len(errors) > 0


class TestIntegration:
    """Integration tests combining multiple features."""

    def test_complete_workflow(self):
        """Test complete workflow with all features."""
        # Create entities with relationships
        user_entity = EntityInfo(
            name="User",
            table_name="users",
            columns=[
                ColumnInfo(name="id", data_type="int", primary_key=True),
                ColumnInfo(name="email", data_type="str"),
                ColumnInfo(name="name", data_type="str"),
                ColumnInfo(name="age", data_type="int"),
            ],
            primary_keys=["id"],
        )

        schema = DatabaseSchema(entities=[user_entity])
        generator = DummyDataGenerator(db_schema=schema)

        # 1. Generate entity graph
        graph = generator.generate_entity_graph(user_entity, depth=1, records_per_level=2)
        assert "User" in graph

        # 2. Generate with constraints
        constraints = {"age": {"ge": 18, "le": 65}}
        constrained_data = generator.generate_with_constraints(user_entity, constraints)
        assert constrained_data["age"].value >= 18
        assert constrained_data["age"].value <= 65

        # 3. Anonymize production-like data
        production_data = {
            "id": 1,
            "email": "real.user@company.com",
            "name": "Real User",
            "age": 30,
        }
        anonymized = generator.anonymize_data(production_data)
        assert anonymized["email"] != production_data["email"]

        # 4. Generate comprehensive edge cases
        dto = DtoSchema(
            name="UserDTO",
            file_path="test/dto.py",
            fields=[
                DtoField(
                    name="email",
                    type="str",
                    required=True,
                    validations=[ValidationRule(rule_type="regex", value=r".*@.*")],
                ),
            ],
        )
        edge_cases = generator.generate_edge_cases_comprehensive(dto)
        assert len(edge_cases) > 0
