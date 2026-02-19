"""Tests for Test Data Factory Module.

This module tests the test data generation features.
"""

import pytest

from socialseed_e2e.test_data_advanced import (
    AdvancedDataFactory,
    DataPool,
    DataType,
    EdgeCaseGenerator,
    FieldDefinition,
    RelationshipGenerator,
    SchemaDefinition,
    SchemaGenerator,
)


class TestSchemaGenerator:
    """Tests for SchemaGenerator."""

    def test_initialization(self):
        """Test generator initialization."""
        generator = SchemaGenerator()
        assert generator is not None

    def test_generate_user_schema(self):
        """Test generating user data from schema."""
        generator = SchemaGenerator()
        schema = SchemaDefinition(
            name="User",
            fields=[
                FieldDefinition("id", DataType.UUID, required=True),
                FieldDefinition("name", DataType.NAME, required=True),
                FieldDefinition("email", DataType.EMAIL, required=True),
            ],
            primary_key="id",
        )

        user = generator.generate(schema)
        assert "id" in user
        assert "name" in user
        assert "email" in user

    def test_generate_batch(self):
        """Test batch generation."""
        generator = SchemaGenerator()
        schema = SchemaDefinition(
            name="User",
            fields=[
                FieldDefinition("id", DataType.UUID, required=True),
            ],
        )

        users = generator.generate_batch(schema, 5)
        assert len(users) == 5


class TestEdgeCaseGenerator:
    """Tests for EdgeCaseGenerator."""

    def test_integer_edge_cases(self):
        """Test integer edge cases."""
        generator = EdgeCaseGenerator()
        cases = generator.generate_edge_cases("age", DataType.INTEGER)

        assert 0 in cases
        assert -1 in cases
        assert None in cases

    def test_string_edge_cases(self):
        """Test string edge cases."""
        generator = EdgeCaseGenerator()
        cases = generator.generate_edge_cases("name", DataType.STRING)

        assert "" in cases
        assert None in cases

    def test_email_edge_cases(self):
        """Test email edge cases."""
        generator = EdgeCaseGenerator()
        cases = generator.generate_edge_cases("email", DataType.EMAIL)

        assert "" in cases
        assert "notanemail" in cases


class TestDataPool:
    """Tests for DataPool."""

    def test_initialization(self):
        """Test pool initialization."""
        generator = SchemaGenerator()
        pool = DataPool(generator)
        assert pool is not None

    def test_add_schema(self):
        """Test adding schema to pool."""
        generator = SchemaGenerator()
        pool = DataPool(generator)

        schema = SchemaDefinition(
            name="User",
            fields=[FieldDefinition("id", DataType.UUID, required=True)],
        )

        pool.add_schema(schema, 5)
        assert "User" in pool.pools
        assert len(pool.pools["User"]) == 5

    def test_get_release(self):
        """Test getting and releasing data."""
        generator = SchemaGenerator()
        pool = DataPool(generator)

        schema = SchemaDefinition(
            name="User",
            fields=[FieldDefinition("id", DataType.UUID, required=True)],
        )

        pool.add_schema(schema, 5)

        # Get all available
        users = []
        for _ in range(5):
            user = pool.get("User")
            if user:
                users.append(user)

        # Now all should be in use
        stats = pool.get_stats()
        assert stats["User"]["in_use"] == 5
        assert stats["User"]["available"] == 0


class TestRelationshipGenerator:
    """Tests for RelationshipGenerator."""

    def test_initialization(self):
        """Test relationship generator initialization."""
        generator = SchemaGenerator()
        rel_gen = RelationshipGenerator(generator)
        assert rel_gen is not None

    def test_add_schema_with_relationships(self):
        """Test adding schema with relationships."""
        generator = SchemaGenerator()
        rel_gen = RelationshipGenerator(generator)

        user_schema = SchemaDefinition(
            name="User",
            fields=[FieldDefinition("id", DataType.UUID, required=True)],
        )

        order_schema = SchemaDefinition(
            name="Order",
            fields=[
                FieldDefinition("id", DataType.UUID, required=True),
                FieldDefinition("user_id", DataType.UUID, required=True),
            ],
        )

        rel_gen.add_schema(user_schema, has_many=["Order"])
        rel_gen.add_schema(order_schema)

        data = rel_gen.generate_with_relationships({"User": 2, "Order": 4})

        assert "User" in data
        assert "Order" in data
        assert len(data["User"]) == 2
        assert len(data["Order"]) == 4


class TestAdvancedDataFactory:
    """Tests for AdvancedDataFactory."""

    def test_initialization(self):
        """Test factory initialization."""
        factory = AdvancedDataFactory()
        assert factory is not None

    def test_create_simple(self):
        """Test simple data creation."""
        factory = AdvancedDataFactory()
        user = factory.create("User", name="John", email="john@example.com")

        assert user["name"] == "John"
        assert user["email"] == "john@example.com"
        assert "id" in user

    def test_create_from_schema(self):
        """Test schema-based creation."""
        factory = AdvancedDataFactory()
        schema = SchemaDefinition(
            name="User",
            fields=[
                FieldDefinition("id", DataType.UUID, required=True),
                FieldDefinition("name", DataType.NAME, required=True),
            ],
        )

        user = factory.create_from_schema("User", schema)
        assert "id" in user
        assert "name" in user

    def test_create_edge_cases(self):
        """Test edge case creation."""
        factory = AdvancedDataFactory()
        cases = factory.create_edge_cases("User", "email", DataType.EMAIL)

        assert len(cases) > 0

    def test_import_export_json(self):
        """Test JSON import/export."""
        factory = AdvancedDataFactory()
        data = [{"id": "1", "name": "John"}]

        json_str = factory.export_to_json(data)
        imported = factory.import_from_json(json_str)

        assert imported == data


class TestFieldDefinition:
    """Tests for FieldDefinition."""

    def test_required_field(self):
        """Test required field."""
        field = FieldDefinition("name", DataType.STRING, required=True)
        assert field.required is True

    def test_default_value(self):
        """Test default value."""
        field = FieldDefinition("status", DataType.STRING, default="active")
        assert field.default == "active"

    def test_enum_values(self):
        """Test enum values."""
        field = FieldDefinition(
            "status", DataType.STRING, enum_values=["active", "inactive"]
        )
        assert field.enum_values == ["active", "inactive"]


class TestSchemaDefinition:
    """Tests for SchemaDefinition."""

    def test_initialization(self):
        """Test schema initialization."""
        schema = SchemaDefinition(name="User")
        assert schema.name == "User"
        assert schema.fields == []

    def test_with_fields(self):
        """Test schema with fields."""
        fields = [
            FieldDefinition("id", DataType.UUID),
            FieldDefinition("name", DataType.NAME),
        ]
        schema = SchemaDefinition(name="User", fields=fields)
        assert len(schema.fields) == 2
