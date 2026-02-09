"""Tests for Dummy Data Generator."""

from datetime import datetime

import pytest

from socialseed_e2e.project_manifest.db_model_parsers import ColumnInfo, DatabaseSchema, EntityInfo
from socialseed_e2e.project_manifest.dummy_data_generator import (
    DataGenerationStrategy,
    DummyDataGenerator,
)
from socialseed_e2e.project_manifest.models import DtoField, DtoSchema


class TestDummyDataGenerator:
    """Test suite for dummy data generation."""

    def test_generate_valid_string(self):
        """Test generation of valid string values."""
        generator = DummyDataGenerator()

        dto = DtoSchema(
            name="TestDTO",
            fields=[
                DtoField(name="username", type="str", required=True),
                DtoField(name="email", type="EmailStr", required=True),
            ],
            file_path="test.py",
            line_number=1,
        )

        result = generator.generate_for_dto(dto, DataGenerationStrategy.VALID)

        assert "username" in result
        assert "email" in result
        assert result["username"].value is not None
        assert result["email"].value is not None
        assert "@" in result["email"].value  # Email should contain @

    def test_generate_with_validation_rules(self):
        """Test generation respecting validation rules."""
        generator = DummyDataGenerator()

        dto = DtoSchema(
            name="TestDTO",
            fields=[
                DtoField(
                    name="username",
                    type="str",
                    required=True,
                    validations=[
                        {"rule_type": "min_length", "value": 5},
                        {"rule_type": "max_length", "value": 20},
                    ],
                ),
            ],
            file_path="test.py",
            line_number=1,
        )

        result = generator.generate_for_dto(dto, DataGenerationStrategy.VALID)

        username = result["username"].value
        assert len(username) >= 5
        assert len(username) <= 20

    def test_generate_invalid_data(self):
        """Test generation of invalid data."""
        generator = DummyDataGenerator()

        dto = DtoSchema(
            name="TestDTO",
            fields=[
                DtoField(
                    name="username",
                    type="str",
                    required=True,
                    validations=[{"rule_type": "max_length", "value": 10}],
                ),
            ],
            file_path="test.py",
            line_number=1,
        )

        result = generator.generate_for_dto(dto, DataGenerationStrategy.INVALID)

        # Should generate a string that exceeds max_length
        username = result["username"].value
        assert len(username) > 10

    def test_generate_edge_cases(self):
        """Test generation of edge case data."""
        generator = DummyDataGenerator()

        dto = DtoSchema(
            name="TestDTO",
            fields=[
                DtoField(
                    name="username",
                    type="str",
                    required=True,
                    validations=[{"rule_type": "min_length", "value": 5}],
                ),
            ],
            file_path="test.py",
            line_number=1,
        )

        result = generator.generate_for_dto(dto, DataGenerationStrategy.EDGE_CASE)

        # Should generate exactly at the boundary
        username = result["username"].value
        assert len(username) == 5

    def test_generate_chaos_data(self):
        """Test generation of chaos/random data."""
        generator = DummyDataGenerator()

        dto = DtoSchema(
            name="TestDTO",
            fields=[
                DtoField(name="username", type="str", required=True),
            ],
            file_path="test.py",
            line_number=1,
        )

        result = generator.generate_for_dto(dto, DataGenerationStrategy.CHAOS)

        # Should generate some value (could be null, empty, or random)
        assert "username" in result

    def test_semantic_field_names(self):
        """Test semantic awareness for common field names."""
        generator = DummyDataGenerator()

        dto = DtoSchema(
            name="TestDTO",
            fields=[
                DtoField(name="first_name", type="str", required=True),
                DtoField(name="last_name", type="str", required=True),
                DtoField(name="phone", type="str", required=True),
                DtoField(name="company", type="str", required=True),
            ],
            file_path="test.py",
            line_number=1,
        )

        result = generator.generate_for_dto(dto, DataGenerationStrategy.VALID)

        # Check that semantic fields have appropriate values
        assert result["first_name"].value in generator.FIRST_NAMES
        assert result["last_name"].value in generator.LAST_NAMES
        assert result["company"].value in generator.COMPANIES
        # Phone should start with + or be numeric
        phone = result["phone"].value
        assert phone.startswith("+") or phone.replace("-", "").isdigit()

    def test_generate_for_entity(self):
        """Test generation for database entities."""
        generator = DummyDataGenerator()

        entity = EntityInfo(
            name="User",
            table_name="users",
            columns=[
                ColumnInfo(name="id", data_type="int", primary_key=True),
                ColumnInfo(name="username", data_type="str", max_length=50),
                ColumnInfo(name="email", data_type="str", max_length=100),
                ColumnInfo(name="age", data_type="int"),
            ],
            orm_framework="sqlalchemy",
        )

        result = generator.generate_for_entity(entity, DataGenerationStrategy.VALID)

        assert "id" in result
        assert "username" in result
        assert "email" in result
        assert "age" in result

        # Check types
        assert isinstance(result["age"].value, int)
        assert isinstance(result["username"].value, str)

    def test_test_scenarios_generation(self):
        """Test generation of complete test scenarios."""
        generator = DummyDataGenerator()

        dto = DtoSchema(
            name="UserRequest",
            fields=[
                DtoField(
                    name="username",
                    type="str",
                    required=True,
                    validations=[{"rule_type": "min_length", "value": 3}],
                ),
            ],
            file_path="test.py",
            line_number=1,
        )

        scenarios = generator.generate_test_scenarios(dto, num_valid=2, num_invalid=1)

        # Should have valid scenarios, failure scenarios, and chaos
        assert len(scenarios) >= 3

        types = {s["type"] for s in scenarios}
        assert "success" in types
        assert "failure" in types
        assert "chaos" in types

    def test_generate_int_with_constraints(self):
        """Test integer generation with min/max constraints."""
        generator = DummyDataGenerator()

        dto = DtoSchema(
            name="TestDTO",
            fields=[
                DtoField(
                    name="age",
                    type="int",
                    required=True,
                    validations=[
                        {"rule_type": "ge", "value": 18},
                        {"rule_type": "le", "value": 65},
                    ],
                ),
            ],
            file_path="test.py",
            line_number=1,
        )

        result = generator.generate_for_dto(dto, DataGenerationStrategy.VALID)

        age = result["age"].value
        assert isinstance(age, int)
        assert age >= 18
        assert age <= 65


class TestDataGenerationStrategies:
    """Test different data generation strategies."""

    def test_null_strategy(self):
        """Test NULL data generation."""
        generator = DummyDataGenerator()

        dto = DtoSchema(
            name="TestDTO",
            fields=[
                DtoField(name="optional_field", type="str", required=False),
            ],
            file_path="test.py",
            line_number=1,
        )

        result = generator.generate_for_dto(dto, DataGenerationStrategy.NULL)

        assert result["optional_field"].value is None

    def test_empty_strategy(self):
        """Test empty data generation."""
        generator = DummyDataGenerator()

        dto = DtoSchema(
            name="TestDTO",
            fields=[
                DtoField(name="text", type="str", required=True),
            ],
            file_path="test.py",
            line_number=1,
        )

        result = generator.generate_for_dto(dto, DataGenerationStrategy.EMPTY)

        assert result["text"].value == ""

    def test_expected_results(self):
        """Test that expected results are correctly set."""
        generator = DummyDataGenerator()

        dto = DtoSchema(
            name="TestDTO",
            fields=[
                DtoField(name="required_field", type="str", required=True),
                DtoField(name="optional_field", type="str", required=False),
            ],
            file_path="test.py",
            line_number=1,
        )

        # Valid data should expect success
        valid = generator.generate_for_dto(dto, DataGenerationStrategy.VALID)
        assert all(r.expected_result == "success" for r in valid.values())

        # Null for required should expect failure
        null_result = generator.generate_for_dto(dto, DataGenerationStrategy.NULL)
        assert null_result["required_field"].expected_result == "failure"
        assert null_result["optional_field"].expected_result == "success"
