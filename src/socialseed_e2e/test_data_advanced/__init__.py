"""Advanced Test Data Factory Module.

This module provides intelligent test data generation:
- Schema-based generation from OpenAPI/GraphQL schemas
- Edge case generation (boundary values, nulls, empty)
- Relationship-aware generation (foreign keys, dependencies)
- Faker integration for realistic data
- Data pool management for parallel tests
- AI-powered scenario generation

Usage:
    from socialseed_e2e.test_data_advanced import (
        AdvancedDataFactory,
        DataPool,
        SchemaGenerator,
    )
"""

import json
import random
import string
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from faker import Faker


class DataType(str, Enum):
    """Supported data types."""

    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    EMAIL = "email"
    UUID = "uuid"
    PHONE = "phone"
    ADDRESS = "address"
    URL = "url"
    TEXT = "text"
    NAME = "full_name"
    FIRST_NAME = "first_name"
    LAST_NAME = "last_name"
    COMPANY = "company"
    CREDIT_CARD = "credit_card"


@dataclass
class FieldDefinition:
    """Definition of a field for data generation."""

    name: str
    data_type: DataType
    required: bool = True
    default: Any = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    pattern: Optional[str] = None
    enum_values: Optional[List[Any]] = None
    faker_provider: Optional[str] = None
    related_to: Optional[str] = None


@dataclass
class SchemaDefinition:
    """Definition of a data schema."""

    name: str
    fields: List[FieldDefinition] = field(default_factory=list)
    primary_key: Optional[str] = None
    foreign_keys: Dict[str, str] = field(default_factory=dict)


class SchemaGenerator:
    """Generates test data from schema definitions.

    Example:
        generator = SchemaGenerator()

        schema = SchemaDefinition(
            name="User",
            fields=[
                FieldDefinition("id", DataType.UUID, required=True),
                FieldDefinition("name", DataType.NAME, required=True),
                FieldDefinition("email", DataType.EMAIL, required=True),
            ],
            primary_key="id"
        )

        user = generator.generate(schema)
    """

    def __init__(self, locale: str = "en_US"):
        """Initialize schema generator."""
        self.faker = Faker(locale)
        self.generators: Dict[DataType, Callable] = {
            DataType.STRING: self._generate_string,
            DataType.INTEGER: self._generate_integer,
            DataType.NUMBER: self._generate_number,
            DataType.BOOLEAN: self._generate_boolean,
            DataType.DATE: self._generate_date,
            DataType.DATETIME: self._generate_datetime,
            DataType.EMAIL: self._generate_email,
            DataType.UUID: self._generate_uuid,
            DataType.PHONE: self._generate_phone,
            DataType.ADDRESS: self._generate_address,
            DataType.URL: self._generate_url,
            DataType.TEXT: self._generate_text,
            DataType.NAME: self._generate_full_name,
            DataType.FIRST_NAME: self._generate_first_name,
            DataType.LAST_NAME: self._generate_last_name,
            DataType.COMPANY: self._generate_company,
            DataType.CREDIT_CARD: self._generate_credit_card,
        }

    def generate(self, schema: SchemaDefinition) -> Dict[str, Any]:
        """Generate data from schema."""
        data = {}
        for field_def in schema.fields:
            if field_def.required and field_def.default is None:
                data[field_def.name] = self._generate_field(field_def)
            elif field_def.default is not None:
                data[field_def.name] = field_def.default
            else:
                data[field_def.name] = None
        return data

    def generate_batch(
        self, schema: SchemaDefinition, count: int
    ) -> List[Dict[str, Any]]:
        """Generate batch of data from schema."""
        return [self.generate(schema) for _ in range(count)]

    def _generate_field(self, field_def: FieldDefinition) -> Any:
        """Generate value for a field."""
        if field_def.enum_values:
            return random.choice(field_def.enum_values)
        generator = self.generators.get(field_def.data_type)
        return generator(field_def) if generator else None

    def _generate_string(self, field_def: FieldDefinition) -> str:
        length = field_def.max_value or 20
        return "".join(random.choices(string.ascii_letters + string.digits, k=length))

    def _generate_integer(self, field_def: FieldDefinition) -> int:
        min_val = field_def.min_value or 1
        max_val = field_def.max_value or 1000
        return random.randint(int(min_val), int(max_val))

    def _generate_number(self, field_def: FieldDefinition) -> float:
        min_val = field_def.min_value or 0.0
        max_val = field_def.max_value or 1000.0
        return random.uniform(min_val, max_val)

    def _generate_boolean(self, field_def: FieldDefinition) -> bool:
        return random.choice([True, False])

    def _generate_date(self, field_def: FieldDefinition) -> str:
        days_ago = random.randint(0, 365)
        date = datetime.now() - timedelta(days=days_ago)
        return date.strftime("%Y-%m-%d")

    def _generate_datetime(self, field_def: FieldDefinition) -> str:
        days_ago = random.randint(0, 365)
        dt = datetime.now() - timedelta(days=days_ago)
        return dt.isoformat()

    def _generate_email(self, field_def: FieldDefinition) -> str:
        return self.faker.email()

    def _generate_uuid(self, field_def: FieldDefinition) -> str:
        return str(uuid.uuid4())

    def _generate_phone(self, field_def: FieldDefinition) -> str:
        return self.faker.phone_number()

    def _generate_address(self, field_def: FieldDefinition) -> Dict[str, str]:
        return {
            "street": self.faker.street_address(),
            "city": self.faker.city(),
            "state": self.faker.state(),
            "zip": self.faker.zipcode(),
            "country": self.faker.country(),
        }

    def _generate_url(self, field_def: FieldDefinition) -> str:
        return self.faker.url()

    def _generate_text(self, field_def: FieldDefinition) -> str:
        paragraphs = random.randint(1, 3)
        return "\n\n".join([self.faker.paragraph() for _ in range(paragraphs)])

    def _generate_full_name(self, field_def: FieldDefinition) -> str:
        return self.faker.name()

    def _generate_first_name(self, field_def: FieldDefinition) -> str:
        return self.faker.first_name()

    def _generate_last_name(self, field_def: FieldDefinition) -> str:
        return self.faker.last_name()

    def _generate_company(self, field_def: FieldDefinition) -> str:
        return self.faker.company()

    def _generate_credit_card(self, field_def: FieldDefinition) -> str:
        return self.faker.credit_card_number()


class EdgeCaseGenerator:
    """Generates edge case test data."""

    def generate_edge_cases(self, field_name: str, data_type: DataType) -> List[Any]:
        """Generate edge case values for a field."""
        edge_cases = []

        if data_type in (DataType.INTEGER, DataType.NUMBER):
            edge_cases.extend([0, -1, 1, 999999999, -999999999, None])
        elif data_type == DataType.STRING:
            edge_cases.extend(
                ["", " ", "a" * 10000, None, "\n\t", "<script>alert('xss')</script>"]
            )
        elif data_type == DataType.EMAIL:
            edge_cases.extend(
                ["", "notanemail", "@nodomain.com", "spaces in@email.com", None]
            )
        elif data_type in (DataType.DATE, DataType.DATETIME):
            edge_cases.extend(["1900-01-01", "9999-12-31", "", "not-a-date", None])
        elif data_type == DataType.BOOLEAN:
            edge_cases.extend([True, False, None, "true", "false", 1, 0])
        else:
            edge_cases.append(None)

        return edge_cases


class DataPool:
    """Manages data pool for parallel tests."""

    def __init__(self, generator: SchemaGenerator):
        """Initialize data pool."""
        self.generator = generator
        self.pools: Dict[str, List[Dict[str, Any]]] = {}
        self.in_use: Dict[str, Set[str]] = {}

    def add_schema(self, schema: SchemaDefinition, count: int = 10) -> None:
        """Add schema to pool."""
        self.pools[schema.name] = self.generator.generate_batch(schema, count)
        self.in_use[schema.name] = set()

    def get(self, schema_name: str) -> Optional[Dict[str, Any]]:
        """Get data from pool."""
        if schema_name not in self.pools:
            return None

        pool = self.pools[schema_name]
        in_use = self.in_use[schema_name]

        for i, record in enumerate(pool):
            record_id = f"{schema_name}_{i}"
            if record_id not in in_use:
                in_use.add(record_id)
                return record
        return None

    def release(self, schema_name: str, record: Dict[str, Any]) -> None:
        """Release data back to pool."""
        if schema_name not in self.in_use:
            return
        record_id = f"{schema_name}_{record.get('id', '')}"
        self.in_use[schema_name].discard(record_id)

    def get_stats(self) -> Dict[str, Dict[str, int]]:
        """Get pool statistics."""
        stats = {}
        for schema_name, pool in self.pools.items():
            total = len(pool)
            in_use = len(self.in_use[schema_name])
            stats[schema_name] = {
                "total": total,
                "available": total - in_use,
                "in_use": in_use,
            }
        return stats


class RelationshipGenerator:
    """Generates data with relationships."""

    def __init__(self, schema_generator: SchemaGenerator):
        """Initialize relationship generator."""
        self.schema_generator = schema_generator
        self.schemas: Dict[str, SchemaDefinition] = {}
        self.relationships: Dict[str, List[str]] = {}
        self.generated_data: Dict[str, List[Dict[str, Any]]] = {}

    def add_schema(
        self, schema: SchemaDefinition, has_many: Optional[List[str]] = None
    ) -> None:
        """Add schema with relationships."""
        self.schemas[schema.name] = schema
        self.relationships[schema.name] = has_many or []

    def generate_with_relationships(
        self, counts: Optional[Dict[str, int]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Generate data with relationships."""
        counts = counts or dict.fromkeys(self.schemas, 5)

        for schema_name, count in counts.items():
            schema = self.schemas[schema_name]
            self.generated_data[schema_name] = self.schema_generator.generate_batch(
                schema, count
            )

        for schema_name, related_schemas in self.relationships.items():
            if not related_schemas:
                continue
            parent_data = self.generated_data.get(schema_name, [])
            if not parent_data:
                continue
            for related_name in related_schemas:
                related_data = self.generated_data.get(related_name, [])
                for record in related_data:
                    parent = random.choice(parent_data)
                    fk_field = f"{schema_name.lower()}_id"
                    if fk_field in record:
                        record[fk_field] = parent.get("id")

        return self.generated_data


class AdvancedDataFactory:
    """Comprehensive test data factory."""

    def __init__(self, locale: str = "en_US"):
        """Initialize test data factory."""
        self.schema_generator = SchemaGenerator(locale)
        self.edge_case_generator = EdgeCaseGenerator()
        self.relationship_generator = RelationshipGenerator(self.schema_generator)
        self.data_pool: Optional[DataPool] = None

    def create(self, entity: str, **kwargs) -> Dict[str, Any]:
        """Create simple test data."""
        data = {"id": str(uuid.uuid4())}
        data.update(kwargs)
        return data

    def create_from_schema(
        self, entity: str, schema: SchemaDefinition
    ) -> Dict[str, Any]:
        """Create data from schema."""
        return self.schema_generator.generate(schema)

    def create_batch_from_schema(
        self, entity: str, schema: SchemaDefinition, count: int
    ) -> List[Dict[str, Any]]:
        """Create batch of data from schema."""
        return self.schema_generator.generate_batch(schema, count)

    def create_edge_cases(
        self, entity: str, field_name: str, data_type: DataType
    ) -> List[Any]:
        """Create edge case values for a field."""
        return self.edge_case_generator.generate_edge_cases(field_name, data_type)

    def create_with_relationships(
        self, counts: Dict[str, int]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Create data with relationships."""
        return self.relationship_generator.generate_with_relationships(counts)

    def create_pool(self) -> DataPool:
        """Create data pool."""
        self.data_pool = DataPool(self.schema_generator)
        return self.data_pool

    def import_from_json(self, json_data: str) -> List[Dict[str, Any]]:
        """Import data from JSON."""
        return json.loads(json_data)

    def export_to_json(self, data: List[Dict[str, Any]]) -> str:
        """Export data to JSON."""
        return json.dumps(data, indent=2)
