"""AI-Powered Context-Aware Dummy Data Generator for test scenarios.

This module generates intelligent dummy data based on:
- Database schema constraints (type, length, nullable, etc.)
- Validation rules from DTOs/Models
- Business logic requirements and rules
- Foreign key relationships with referential integrity
- Edge cases and boundary conditions
- Data anonymization for production data

Supports multiple data generation strategies:
- Valid data (for success tests)
- Invalid data (for failure tests)
- Edge cases (boundary values)
- Chaos data (random/fuzzy data)
- Anonymized production data
"""

import hashlib
import random
import re
import string
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from socialseed_e2e.project_manifest.db_model_parsers import (
    ColumnInfo,
    DatabaseSchema,
    EntityInfo,
    EntityRelationship,
)
from socialseed_e2e.project_manifest.models import DtoField, DtoSchema, ValidationRule


class DataGenerationStrategy(Enum):
    """Strategies for generating test data."""

    VALID = "valid"  # Valid data that should pass validation
    INVALID = "invalid"  # Invalid data that should fail validation
    EDGE_CASE = "edge_case"  # Boundary values (min, max, empty)
    CHAOS = "chaos"  # Random/fuzzy data
    NULL = "null"  # Null/None values
    EMPTY = "empty"  # Empty strings, lists, etc.


@dataclass
class GeneratedData:
    """Result of data generation."""

    field_name: str
    value: Any
    strategy: DataGenerationStrategy
    description: str
    expected_result: str  # "success", "failure", "depends"


@dataclass
class DataGenerationContext:
    """Context for data generation."""

    dto_name: Optional[str] = None
    entity_name: Optional[str] = None
    strategy: DataGenerationStrategy = DataGenerationStrategy.VALID
    previous_values: Dict[str, Any] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)
    # AI-powered context additions
    business_rules: Dict[str, Any] = field(default_factory=dict)
    related_entities: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    anonymization_mapping: Dict[str, str] = field(default_factory=dict)


@dataclass
class BusinessRule:
    """Business rule for intelligent data generation."""

    rule_type: str  # "email_format", "date_range", "reference_exists", "custom"
    field_pattern: str  # Regex pattern to match field names
    constraint: Dict[str, Any] = field(default_factory=dict)
    error_message: str = ""


@dataclass
class EdgeCaseScenario:
    """Edge case scenario for comprehensive testing."""

    name: str
    field_name: str
    value: Any
    description: str
    expected_result: str  # "success", "failure", "boundary"
    category: str  # "null", "empty", "boundary", "type_mismatch", "extreme"


@dataclass
class AnonymizationRule:
    """Rule for anonymizing production data."""

    field_pattern: str
    method: str  # "hash", "mask", "replace", "shuffle", "noise"
    preserve_format: bool = True
    custom_mapping: Optional[Dict[str, str]] = None


class DummyDataGenerator:
    """Generator for intelligent dummy test data."""

    # Common test data pools
    FIRST_NAMES = [
        "James",
        "Mary",
        "John",
        "Patricia",
        "Robert",
        "Jennifer",
        "Michael",
        "Linda",
        "William",
        "Elizabeth",
        "David",
        "Barbara",
        "Richard",
        "Susan",
        "Joseph",
        "Jessica",
        "Thomas",
        "Sarah",
        "Charles",
        "Karen",
        "Christopher",
        "Nancy",
        "Daniel",
        "Lisa",
        "Matthew",
        "Betty",
        "Anthony",
        "Margaret",
        "Mark",
        "Sandra",
    ]

    LAST_NAMES = [
        "Smith",
        "Johnson",
        "Williams",
        "Brown",
        "Jones",
        "Garcia",
        "Miller",
        "Davis",
        "Rodriguez",
        "Martinez",
        "Hernandez",
        "Lopez",
        "Gonzalez",
        "Wilson",
        "Anderson",
        "Thomas",
        "Taylor",
        "Moore",
        "Jackson",
        "Martin",
        "Lee",
        "Perez",
        "Thompson",
        "White",
    ]

    DOMAINS = ["example.com", "test.org", "demo.io", "sample.net", "e2e.test"]

    COMPANIES = [
        "Acme Corp",
        "Globex",
        "Soylent Corp",
        "Initech",
        "Umbrella Corp",
        "Stark Industries",
        "Wayne Enterprises",
        "Cyberdyne",
        "Massive Dynamic",
    ]

    STREETS = [
        "123 Main St",
        "456 Oak Ave",
        "789 Pine Rd",
        "321 Elm Blvd",
        "654 Maple Dr",
        "987 Cedar Ln",
        "147 Birch Way",
        "258 Spruce Ct",
    ]

    CITIES = [
        "New York",
        "Los Angeles",
        "Chicago",
        "Houston",
        "Phoenix",
        "Philadelphia",
        "San Antonio",
        "San Diego",
        "Dallas",
        "San Jose",
    ]

    COUNTRIES = ["USA", "Canada", "UK", "Germany", "France", "Japan", "Australia"]

    LOREM_WORDS = [
        "lorem",
        "ipsum",
        "dolor",
        "sit",
        "amet",
        "consectetur",
        "adipiscing",
        "elit",
        "sed",
        "do",
        "eiusmod",
        "tempor",
        "incididunt",
        "ut",
        "labore",
        "et",
        "dolore",
        "magna",
        "aliqua",
        "ut",
        "enim",
        "ad",
        "minim",
        "veniam",
    ]

    def generate_for_dto(
        self,
        dto: DtoSchema,
        strategy: DataGenerationStrategy = DataGenerationStrategy.VALID,
        context: Optional[DataGenerationContext] = None,
    ) -> Dict[str, GeneratedData]:
        """Generate dummy data for a DTO.

        Args:
            dto: DTO schema to generate data for
            strategy: Data generation strategy
            context: Optional generation context

        Returns:
            Dictionary mapping field names to GeneratedData
        """
        if context is None:
            context = DataGenerationContext(dto_name=dto.name, strategy=strategy)

        result = {}

        for field in dto.fields:
            generated = self._generate_field_value(field, strategy, context)
            result[field.name] = generated

            # Store for potential reuse in relationships
            if strategy == DataGenerationStrategy.VALID:
                self.generated_values[f"{dto.name}.{field.name}"] = generated.value

        return result

    def generate_for_entity(
        self,
        entity: EntityInfo,
        strategy: DataGenerationStrategy = DataGenerationStrategy.VALID,
        context: Optional[DataGenerationContext] = None,
    ) -> Dict[str, GeneratedData]:
        """Generate dummy data for a database entity.

        Args:
            entity: Entity to generate data for
            strategy: Data generation strategy
            context: Optional generation context

        Returns:
            Dictionary mapping column names to GeneratedData
        """
        if context is None:
            context = DataGenerationContext(entity_name=entity.name, strategy=strategy)

        result = {}

        for column in entity.columns:
            generated = self._generate_column_value(column, strategy, context)
            result[column.name] = generated

            if strategy == DataGenerationStrategy.VALID:
                self.generated_values[f"{entity.name}.{column.name}"] = generated.value

        return result

    def generate_test_scenarios(
        self, dto: DtoSchema, num_valid: int = 3, num_invalid: int = 2
    ) -> List[Dict[str, Any]]:
        """Generate multiple test scenarios for a DTO.

        Args:
            dto: DTO schema
            num_valid: Number of valid scenarios to generate
            num_invalid: Number of invalid scenarios to generate

        Returns:
            List of test scenarios
        """
        scenarios = []

        # Generate valid scenarios
        for i in range(num_valid):
            data = self.generate_for_dto(dto, DataGenerationStrategy.VALID)
            scenarios.append(
                {
                    "name": f"Valid {dto.name} - Scenario {i + 1}",
                    "type": "success",
                    "data": {k: v.value for k, v in data.items()},
                    "expected": "success",
                    "description": f"Valid data scenario {i + 1}",
                }
            )

        # Generate invalid scenarios for each field
        for field in dto.fields:
            if field.required:
                # Missing required field
                data = self.generate_for_dto(dto, DataGenerationStrategy.VALID)
                invalid_data = {k: v.value for k, v in data.items()}
                invalid_data[field.name] = None
                scenarios.append(
                    {
                        "name": f"Missing Required Field: {field.name}",
                        "type": "failure",
                        "data": invalid_data,
                        "expected": "validation_error",
                        "description": f"Test missing required field: {field.name}",
                    }
                )

            # Generate edge cases based on validations
            for validation in field.validations:
                edge_cases = self._generate_edge_cases(field, validation)
                for case in edge_cases:
                    scenarios.append(case)

        # Generate chaos scenario
        chaos_data = self.generate_for_dto(dto, DataGenerationStrategy.CHAOS)
        scenarios.append(
            {
                "name": f"Chaos Test - {dto.name}",
                "type": "chaos",
                "data": {k: v.value for k, v in chaos_data.items()},
                "expected": "varies",
                "description": "Random chaos test data",
            }
        )

        return scenarios

    def _generate_field_value(
        self,
        field: DtoField,
        strategy: DataGenerationStrategy,
        context: DataGenerationContext,
    ) -> GeneratedData:
        """Generate value for a single DTO field."""
        # Check if we have a database column for additional constraints
        db_column = None
        if self.db_schema and context.entity_name:
            entity = self.db_schema.get_entity(context.entity_name)
            if entity:
                db_column = next((c for c in entity.columns if c.name == field.name), None)

        # Generate based on strategy
        if strategy == DataGenerationStrategy.VALID:
            value = self._generate_valid_value(field, db_column)
            expected = "success"
            description = f"Valid {field.type} value"
        elif strategy == DataGenerationStrategy.INVALID:
            value = self._generate_invalid_value(field, db_column)
            expected = "failure"
            description = f"Invalid {field.type} value"
        elif strategy == DataGenerationStrategy.EDGE_CASE:
            value = self._generate_edge_case_value(field, db_column)
            expected = "depends"
            description = f"Edge case for {field.name}"
        elif strategy == DataGenerationStrategy.CHAOS:
            value = self._generate_chaos_value(field)
            expected = "varies"
            description = f"Random chaos value"
        elif strategy == DataGenerationStrategy.NULL:
            value = None
            expected = "failure" if field.required else "success"
            description = "Null value"
        elif strategy == DataGenerationStrategy.EMPTY:
            value = self._get_empty_value(field.type)
            expected = "depends"
            description = "Empty value"
        else:
            value = None
            expected = "unknown"
            description = "Unknown strategy"

        return GeneratedData(
            field_name=field.name,
            value=value,
            strategy=strategy,
            description=description,
            expected_result=expected,
        )

    def _generate_column_value(
        self,
        column: ColumnInfo,
        strategy: DataGenerationStrategy,
        context: DataGenerationContext,
    ) -> GeneratedData:
        """Generate value for a database column."""
        if strategy == DataGenerationStrategy.VALID:
            value = self._generate_valid_column_value(column)
            expected = "success"
            description = f"Valid {column.data_type} value"
        elif strategy == DataGenerationStrategy.NULL:
            value = None
            expected = "failure" if not column.nullable else "success"
            description = "Null value"
        elif strategy == DataGenerationStrategy.INVALID:
            value = self._generate_invalid_column_value(column)
            expected = "failure"
            description = f"Invalid {column.data_type} value"
        else:
            value = self._generate_valid_column_value(column)
            expected = "success"
            description = f"Default {column.data_type} value"

        return GeneratedData(
            field_name=column.name,
            value=value,
            strategy=strategy,
            description=description,
            expected_result=expected,
        )

    def _generate_valid_value(self, field: DtoField, db_column: Optional[ColumnInfo] = None) -> Any:
        """Generate a valid value for a field."""
        field_type = field.type.lower()

        # Get constraints from validations
        min_length = None
        max_length = None
        pattern = None
        min_value = None
        max_value = None

        for validation in field.validations:
            if validation.rule_type == "min_length":
                min_length = validation.value
            elif validation.rule_type == "max_length":
                max_length = validation.value
            elif validation.rule_type == "regex":
                pattern = validation.value
            elif validation.rule_type == "gt":
                min_value = validation.value + 1
            elif validation.rule_type == "ge":
                min_value = validation.value
            elif validation.rule_type == "lt":
                max_value = validation.value - 1
            elif validation.rule_type == "le":
                max_value = validation.value

        # Override with DB constraints if available
        if db_column:
            if db_column.max_length:
                max_length = db_column.max_length
            if db_column.min_value is not None:
                min_value = db_column.min_value
            if db_column.max_value is not None:
                max_value = db_column.max_value

        # Generate based on type
        if "str" in field_type or "email" in field_type:
            return self._generate_string_value(
                field.name, min_length, max_length, pattern, field_type
            )
        elif "int" in field_type:
            return self._generate_int_value(min_value, max_value)
        elif "float" in field_type or "decimal" in field_type or "double" in field_type:
            return self._generate_float_value(min_value, max_value)
        elif "bool" in field_type:
            return random.choice([True, False])
        elif "datetime" in field_type or "date" in field_type:
            return self._generate_datetime_value()
        elif "uuid" in field_type:
            return str(uuid.uuid4())
        elif "list" in field_type or "array" in field_type:
            return self._generate_list_value()
        elif "dict" in field_type or "json" in field_type:
            return self._generate_dict_value()
        else:
            return self._generate_string_value(field.name, min_length, max_length)

    def _generate_valid_column_value(self, column: ColumnInfo) -> Any:
        """Generate a valid value for a database column."""
        data_type = column.data_type.lower()

        if data_type == "str" or data_type == "string":
            min_len = 1
            max_len = column.max_length or 255
            return self._generate_random_string(random.randint(min_len, min(max_len, 50)))
        elif data_type == "int" or data_type == "integer":
            min_val = column.min_value or 0
            max_val = column.max_value or 1000000
            return random.randint(int(min_val), int(max_val))
        elif data_type == "float":
            min_val = column.min_value or 0.0
            max_val = column.max_value or 1000000.0
            return random.uniform(float(min_val), float(max_val))
        elif data_type == "bool" or data_type == "boolean":
            return random.choice([True, False])
        elif data_type == "datetime":
            return datetime.now() - timedelta(days=random.randint(0, 365))
        elif data_type == "date":
            return date.today() - timedelta(days=random.randint(0, 365))
        elif data_type == "uuid":
            return str(uuid.uuid4())
        elif data_type == "enum":
            if column.enum_values:
                return random.choice(column.enum_values)
            return "value1"
        else:
            return self._generate_random_string(20)

    def _generate_invalid_value(
        self, field: DtoField, db_column: Optional[ColumnInfo] = None
    ) -> Any:
        """Generate an invalid value that should fail validation."""
        field_type = field.type.lower()

        # Get max length constraint
        max_length = None
        for validation in field.validations:
            if validation.rule_type == "max_length":
                max_length = validation.value

        if db_column and db_column.max_length:
            max_length = db_column.max_length

        # Generate value that violates constraints
        if "str" in field_type:
            if max_length:
                # Generate string exceeding max length
                return "x" * (max_length + 10)
            else:
                # Generate very long string
                return "x" * 10000
        elif "int" in field_type:
            return "not_a_number"
        elif "float" in field_type:
            return "not_a_float"
        elif "email" in field_type:
            return "invalid_email_format"
        elif "bool" in field_type:
            return "not_a_boolean"
        elif "datetime" in field_type:
            return "invalid_date"
        else:
            return None

    def _generate_invalid_column_value(self, column: ColumnInfo) -> Any:
        """Generate an invalid value for a database column."""
        data_type = column.data_type.lower()

        if data_type == "str":
            if column.max_length:
                return "x" * (column.max_length + 10)
            return "x" * 10000
        elif data_type == "int":
            return "not_an_integer"
        elif data_type == "float":
            return "not_a_float"
        elif data_type == "bool":
            return "not_boolean"
        elif data_type == "datetime":
            return "invalid_datetime"
        else:
            return None

    def _generate_edge_case_value(
        self, field: DtoField, db_column: Optional[ColumnInfo] = None
    ) -> Any:
        """Generate an edge case value (boundary testing)."""
        field_type = field.type.lower()

        # Get constraints
        min_length = None
        max_length = None
        min_value = None
        max_value = None

        for validation in field.validations:
            if validation.rule_type == "min_length":
                min_length = validation.value
            elif validation.rule_type == "max_length":
                max_length = validation.value
            elif validation.rule_type == "ge":
                min_value = validation.value
            elif validation.rule_type == "le":
                max_value = validation.value

        if db_column:
            if db_column.max_length:
                max_length = db_column.max_length
            if db_column.min_value is not None:
                min_value = db_column.min_value
            if db_column.max_value is not None:
                max_value = db_column.max_value

        # Generate boundary value
        if "str" in field_type:
            if min_length is not None:
                return "x" * min_length  # Exactly at minimum
            elif max_length is not None:
                return "x" * max_length  # Exactly at maximum
            else:
                return ""  # Empty string
        elif "int" in field_type:
            if min_value is not None:
                return int(min_value)
            elif max_value is not None:
                return int(max_value)
            else:
                return 0
        elif "float" in field_type:
            if min_value is not None:
                return float(min_value)
            elif max_value is not None:
                return float(max_value)
            else:
                return 0.0
        elif "bool" in field_type:
            return True  # Or False, both are edge cases
        else:
            return None

    def _generate_chaos_value(self, field: DtoField) -> Any:
        """Generate a random chaos value."""
        chaos_types = [
            "null",
            "empty",
            "random_string",
            "random_number",
            "special_chars",
            "unicode",
        ]
        chaos_type = random.choice(chaos_types)

        if chaos_type == "null":
            return None
        elif chaos_type == "empty":
            return ""
        elif chaos_type == "random_string":
            return self._generate_random_string(random.randint(1, 100))
        elif chaos_type == "random_number":
            return random.randint(-1000000, 1000000)
        elif chaos_type == "special_chars":
            return "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        elif chaos_type == "unicode":
            return "日本語中文한국어العربيةעברית"
        else:
            return None

    def _generate_edge_cases(
        self, field: DtoField, validation: ValidationRule
    ) -> List[Dict[str, Any]]:
        """Generate edge case scenarios for a specific validation."""
        scenarios = []

        if validation.rule_type == "min_length":
            min_val = validation.value
            scenarios.append(
                {
                    "name": f"{field.name} - At Minimum Length ({min_val})",
                    "type": "edge_case",
                    "field": field.name,
                    "data": "x" * min_val,
                    "expected": "success",
                    "description": f"Boundary test: exactly {min_val} characters",
                }
            )
            if min_val > 0:
                scenarios.append(
                    {
                        "name": f"{field.name} - Below Minimum Length ({min_val - 1})",
                        "type": "edge_case",
                        "field": field.name,
                        "data": "x" * (min_val - 1),
                        "expected": "failure",
                        "description": f"Boundary test: {min_val - 1} characters (should fail)",
                    }
                )

        elif validation.rule_type == "max_length":
            max_val = validation.value
            scenarios.append(
                {
                    "name": f"{field.name} - At Maximum Length ({max_val})",
                    "type": "edge_case",
                    "field": field.name,
                    "data": "x" * max_val,
                    "expected": "success",
                    "description": f"Boundary test: exactly {max_val} characters",
                }
            )
            scenarios.append(
                {
                    "name": f"{field.name} - Above Maximum Length ({max_val + 1})",
                    "type": "edge_case",
                    "field": field.name,
                    "data": "x" * (max_val + 1),
                    "expected": "failure",
                    "description": f"Boundary test: {max_val + 1} characters (should fail)",
                }
            )

        return scenarios

    def _generate_string_value(
        self,
        field_name: str,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        pattern: Optional[str] = None,
        field_type: str = "str",
    ) -> str:
        """Generate a valid string value based on field name and constraints."""
        # Check field name patterns for semantic generation
        field_lower = field_name.lower()

        if "email" in field_type or "email" in field_lower:
            return self._generate_email()
        elif "password" in field_lower:
            return self._generate_password(min_length, max_length)
        elif "username" in field_lower or "user" in field_lower:
            return self._generate_username(min_length, max_length)
        elif "name" in field_lower:
            if "first" in field_lower:
                return random.choice(self.FIRST_NAMES)
            elif "last" in field_lower or "surname" in field_lower:
                return random.choice(self.LAST_NAMES)
            else:
                return f"{random.choice(self.FIRST_NAMES)} {random.choice(self.LAST_NAMES)}"
        elif "phone" in field_lower or "mobile" in field_lower:
            return self._generate_phone()
        elif "address" in field_lower:
            return random.choice(self.STREETS)
        elif "city" in field_lower:
            return random.choice(self.CITIES)
        elif "country" in field_lower:
            return random.choice(self.COUNTRIES)
        elif "company" in field_lower or "organization" in field_lower:
            return random.choice(self.COMPANIES)
        elif "description" in field_lower or "comment" in field_lower or "note" in field_lower:
            return self._generate_lorem_text(20)
        elif "url" in field_lower or "website" in field_lower:
            return f"https://www.{random.choice(self.DOMAINS)}"
        elif "uuid" in field_lower or "id" in field_lower:
            return str(uuid.uuid4())
        elif "token" in field_lower:
            return self._generate_random_string(32)
        else:
            # Default random string
            length = self._determine_length(min_length, max_length)
            return self._generate_random_string(length)

    def _generate_int_value(
        self,
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
    ) -> int:
        """Generate a valid integer value."""
        min_val = int(min_value) if min_value is not None else 0
        max_val = int(max_value) if max_value is not None else 1000000
        return random.randint(min_val, max_val)

    def _generate_float_value(
        self,
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
    ) -> float:
        """Generate a valid float value."""
        min_val = float(min_value) if min_value is not None else 0.0
        max_val = float(max_value) if max_value is not None else 1000000.0
        return round(random.uniform(min_val, max_val), 2)

    def _generate_datetime_value(self) -> datetime:
        """Generate a valid datetime value."""
        days = random.randint(0, 365 * 5)  # Last 5 years
        return datetime.now() - timedelta(days=days)

    def _generate_list_value(self) -> List[Any]:
        """Generate a list value."""
        return [self._generate_random_string(10) for _ in range(random.randint(1, 5))]

    def _generate_dict_value(self) -> Dict[str, Any]:
        """Generate a dictionary value."""
        return {
            "key1": self._generate_random_string(10),
            "key2": random.randint(1, 100),
            "key3": random.choice([True, False]),
        }

    def _generate_email(self) -> str:
        """Generate a valid email address."""
        first = random.choice(self.FIRST_NAMES).lower()
        last = random.choice(self.LAST_NAMES).lower()
        domain = random.choice(self.DOMAINS)
        return f"{first}.{last}@{domain}"

    def _generate_password(
        self, min_length: Optional[int] = None, max_length: Optional[int] = None
    ) -> str:
        """Generate a valid password meeting common requirements."""
        min_len = min_length or 8
        max_len = max_length or 50

        # Ensure password meets common requirements
        length = max(min_len, min(20, max_len))

        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        password = "".join(random.choice(chars) for _ in range(length - 4))
        password += "A1!"  # Ensure uppercase, number, and special char

        return password

    def _generate_username(
        self, min_length: Optional[int] = None, max_length: Optional[int] = None
    ) -> str:
        """Generate a valid username."""
        first = random.choice(self.FIRST_NAMES).lower()
        last = random.choice(self.LAST_NAMES).lower()
        number = random.randint(1, 999)

        username = f"{first}.{last}{number}"

        # Apply length constraints
        if min_length and len(username) < min_length:
            username += "0" * (min_length - len(username))
        if max_length and len(username) > max_length:
            username = username[:max_length]

        return username

    def _generate_phone(self) -> str:
        """Generate a valid phone number."""
        return (
            f"+1-{random.randint(200, 999)}-{random.randint(200, 999)}-{random.randint(1000, 9999)}"
        )

    def _generate_lorem_text(self, num_words: int = 10) -> str:
        """Generate lorem ipsum text."""
        words = [random.choice(self.LOREM_WORDS) for _ in range(num_words)]
        return " ".join(words).capitalize() + "."

    def _generate_random_string(self, length: int) -> str:
        """Generate a random string of specified length."""
        chars = string.ascii_letters + string.digits
        return "".join(random.choice(chars) for _ in range(length))

    def _determine_length(
        self, min_length: Optional[int] = None, max_length: Optional[int] = None
    ) -> int:
        """Determine a valid string length based on constraints."""
        min_len = min_length or 5
        max_len = max_length or 50

        # Generate length within constraints
        return random.randint(min_len, min(max_len, min_len + 20))

    def _get_empty_value(self, field_type: str) -> Any:
        """Get an empty value for a type."""
        field_lower = field_type.lower()

        if "str" in field_lower:
            return ""
        elif "list" in field_lower or "array" in field_lower:
            return []
        elif "dict" in field_lower:
            return {}
        else:
            return None

    def generate_related_entities(
        self, entity: EntityInfo, related_entity: EntityInfo, num_records: int = 3
    ) -> List[Dict[str, Any]]:
        """Generate related entity records with proper foreign key references."""
        records = []

        # First generate parent entity records
        parent_records = []
        for i in range(num_records):
            data = self.generate_for_entity(entity, DataGenerationStrategy.VALID)
            parent_record = {k: v.value for k, v in data.items()}
            parent_records.append(parent_record)

        # Now generate related records with FK references
        for parent in parent_records:
            related_data = self.generate_for_entity(related_entity, DataGenerationStrategy.VALID)
            related_record = {k: v.value for k, v in related_data.items()}

            # Set foreign key to parent primary key
            for col in related_entity.columns:
                if col.foreign_key and col.foreign_key.startswith(entity.table_name):
                    pk_field = entity.primary_keys[0] if entity.primary_keys else "id"
                    related_record[col.name] = parent.get(pk_field)

            records.append(related_record)

        return records

    # =========================================================================
    # AI-Powered Context-Aware Data Generation (Issue #109)
    # =========================================================================

    def __init__(self, db_schema: Optional[DatabaseSchema] = None):
        """Initialize the AI-powered dummy data generator.

        Args:
            db_schema: Optional database schema for constraint-aware generation
        """
        self.db_schema = db_schema
        self.generated_values: Dict[str, Any] = {}
        self._entity_cache: Dict[str, List[Dict[str, Any]]] = {}
        self._fk_value_cache: Dict[str, List[Any]] = {}
        self._business_rules: List[BusinessRule] = self._init_business_rules()
        self._anonymization_rules: List[AnonymizationRule] = []
        self._constraint_graph: Dict[str, Set[str]] = {}

    def _init_business_rules(self) -> List[BusinessRule]:
        """Initialize default business rules for intelligent generation."""
        return [
            BusinessRule(
                rule_type="email_format",
                field_pattern=r".*email.*",
                constraint={"format": "user@domain.com", "domains": self.DOMAINS},
                error_message="Invalid email format",
            ),
            BusinessRule(
                rule_type="date_range",
                field_pattern=r".*(birth|dob|birthday).*",
                constraint={"min_years_ago": 100, "max_years_ago": 18},
                error_message="Invalid date of birth",
            ),
            BusinessRule(
                rule_type="date_range",
                field_pattern=r".*(future|expir).*",
                constraint={"min_days_future": 1, "max_days_future": 365},
                error_message="Invalid future date",
            ),
            BusinessRule(
                rule_type="phone_format",
                field_pattern=r".*phone.*",
                constraint={"format": "+1-XXX-XXX-XXXX"},
                error_message="Invalid phone format",
            ),
            BusinessRule(
                rule_type="credit_card",
                field_pattern=r".*(card|cc_number).*",
                constraint={"format": "luhn", "mask": True},
                error_message="Invalid card number",
            ),
            BusinessRule(
                rule_type="url_format",
                field_pattern=r".*(url|website|link).*",
                constraint={"protocols": ["https", "http"]},
                error_message="Invalid URL format",
            ),
        ]

    def generate_entity_graph(
        self,
        root_entity: EntityInfo,
        depth: int = 2,
        records_per_level: int = 3,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Generate a complete entity graph with referential integrity.

        Args:
            root_entity: Root entity to start from
            depth: How many levels of relationships to generate
            records_per_level: Number of records per entity

        Returns:
            Dictionary mapping entity names to their generated records
        """
        result: Dict[str, List[Dict[str, Any]]] = {}
        generated_ids: Dict[str, Set[Any]] = {}

        def generate_level(
            entity: EntityInfo,
            current_depth: int,
            parent_records: Optional[List[Dict]] = None,
        ):
            if current_depth > depth or entity.name in result:
                return

            records = []
            for i in range(records_per_level):
                # Generate entity data
                data = self.generate_for_entity(entity, DataGenerationStrategy.VALID)
                record = {k: v.value for k, v in data.items()}

                # Ensure unique primary key
                pk_field = entity.primary_keys[0] if entity.primary_keys else "id"
                if pk_field in record:
                    base_pk = record[pk_field]
                    counter = 0
                    while base_pk in generated_ids.get(entity.name, set()):
                        counter += 1
                        if isinstance(base_pk, int):
                            base_pk = base_pk + counter
                        else:
                            base_pk = f"{base_pk}_{counter}"
                    record[pk_field] = base_pk
                    generated_ids.setdefault(entity.name, set()).add(base_pk)

                # Set foreign keys to parent
                if parent_records and i < len(parent_records):
                    parent = parent_records[i]
                    parent_entity = self._find_parent_entity(entity)
                    if parent_entity:
                        parent_pk = (
                            parent_entity.primary_keys[0] if parent_entity.primary_keys else "id"
                        )
                        for col in entity.columns:
                            if col.foreign_key and parent_entity.table_name in col.foreign_key:
                                record[col.name] = parent.get(parent_pk)

                records.append(record)

            result[entity.name] = records
            self._entity_cache[entity.name] = records

            # Generate related entities
            if current_depth < depth:
                for rel in entity.relationships:
                    target_entity = self._get_entity_by_name(rel.target_entity)
                    if target_entity:
                        generate_level(target_entity, current_depth + 1, records)

        generate_level(root_entity, 0)
        return result

    def _find_parent_entity(self, entity: EntityInfo) -> Optional[EntityInfo]:
        """Find parent entity based on foreign keys."""
        if not self.db_schema:
            return None

        for col in entity.columns:
            if col.foreign_key:
                parts = col.foreign_key.split(".")
                if len(parts) >= 1:
                    return self.db_schema.get_entity(parts[0])
        return None

    def _get_entity_by_name(self, name: str) -> Optional[EntityInfo]:
        """Get entity by name from schema."""
        if not self.db_schema:
            return None
        return self.db_schema.get_entity(name)

    def generate_with_constraints(
        self,
        entity: EntityInfo,
        constraints: Dict[str, Any],
        max_attempts: int = 100,
    ) -> Dict[str, GeneratedData]:
        """Generate data satisfying complex constraints.

        Args:
            entity: Entity to generate data for
            constraints: Dict of field constraints (e.g., {"age": {"gt": 18}})
            max_attempts: Maximum attempts to satisfy constraints

        Returns:
            Generated data satisfying all constraints
        """
        for attempt in range(max_attempts):
            data = self.generate_for_entity(entity, DataGenerationStrategy.VALID)
            record = {k: v.value for k, v in data.items()}

            # Apply constraint-satisfying values for constrained fields
            for field, constraint in constraints.items():
                if field in record:
                    record[field] = self._generate_constraint_satisfying_value(
                        entity, field, constraint
                    )

            # Verify all constraints are satisfied
            all_satisfied = all(
                self._check_constraint(record[field], constraint)
                for field, constraint in constraints.items()
                if field in record
            )

            if all_satisfied:
                return {
                    k: GeneratedData(
                        field_name=k,
                        value=v,
                        strategy=DataGenerationStrategy.VALID,
                        description="Constraint-satisfying value",
                        expected_result="success",
                    )
                    for k, v in record.items()
                }

        # If we couldn't satisfy constraints, return best effort with constraints applied
        data = self.generate_for_entity(entity, DataGenerationStrategy.VALID)
        record = {k: v.value for k, v in data.items()}
        for field, constraint in constraints.items():
            if field in record:
                record[field] = self._generate_constraint_satisfying_value(
                    entity, field, constraint
                )

        return {
            k: GeneratedData(
                field_name=k,
                value=v,
                strategy=DataGenerationStrategy.VALID,
                description="Best-effort constraint-satisfying value",
                expected_result="success",
            )
            for k, v in record.items()
        }

    def _check_constraint(self, value: Any, constraint: Dict[str, Any]) -> bool:
        """Check if a value satisfies a constraint."""
        for op, target in constraint.items():
            if op == "eq" and value != target:
                return False
            elif op == "ne" and value == target:
                return False
            elif op == "gt" and not (value > target):
                return False
            elif op == "ge" and not (value >= target):
                return False
            elif op == "lt" and not (value < target):
                return False
            elif op == "le" and not (value <= target):
                return False
            elif op == "in" and value not in target:
                return False
            elif op == "regex" and not re.match(target, str(value)):
                return False
        return True

    def _generate_constraint_satisfying_value(
        self, entity: EntityInfo, field: str, constraint: Dict[str, Any]
    ) -> Any:
        """Generate a value that satisfies a constraint."""
        column = next((c for c in entity.columns if c.name == field), None)

        if not column:
            return None

        # Handle numeric constraints
        if column.data_type.lower() in ("int", "integer", "float"):
            min_val = constraint.get("ge", constraint.get("gt", 0))
            max_val = constraint.get("le", constraint.get("lt", 1000000))

            if "gt" in constraint:
                min_val = constraint["gt"] + 1
            if "lt" in constraint:
                max_val = constraint["lt"] - 1

            if column.data_type.lower() == "int":
                return random.randint(int(min_val), int(max_val))
            else:
                return random.uniform(float(min_val), float(max_val))

        # Handle string constraints
        elif column.data_type.lower() in ("str", "string"):
            if "regex" in constraint:
                # Generate simple matching string
                return "valid" + str(random.randint(1000, 9999))
            elif "eq" in constraint:
                return constraint["eq"]

        return self._generate_valid_column_value(column)

    def generate_edge_cases_comprehensive(self, dto: DtoSchema) -> List[EdgeCaseScenario]:
        """Generate comprehensive edge cases for all fields.

        Args:
            dto: DTO schema to generate edge cases for

        Returns:
            List of edge case scenarios
        """
        scenarios = []

        for field in dto.fields:
            field_scenarios = self._generate_field_edge_cases(field)
            scenarios.extend(field_scenarios)

        return scenarios

    def _generate_field_edge_cases(self, field: DtoField) -> List[EdgeCaseScenario]:
        """Generate edge cases for a single field."""
        scenarios = []
        field_type = field.type.lower()

        # Null/None cases
        if not field.required:
            scenarios.append(
                EdgeCaseScenario(
                    name=f"{field.name} - Null Value",
                    field_name=field.name,
                    value=None,
                    description=f"Null value for optional field {field.name}",
                    expected_result="success",
                    category="null",
                )
            )
        else:
            scenarios.append(
                EdgeCaseScenario(
                    name=f"{field.name} - Null on Required",
                    field_name=field.name,
                    value=None,
                    description=f"Null value for required field {field.name}",
                    expected_result="failure",
                    category="null",
                )
            )

        # Empty string cases
        if "str" in field_type:
            scenarios.append(
                EdgeCaseScenario(
                    name=f"{field.name} - Empty String",
                    field_name=field.name,
                    value="",
                    description=f"Empty string for {field.name}",
                    expected_result="boundary",
                    category="empty",
                )
            )

            # Boundary length cases
            for validation in field.validations:
                if validation.rule_type == "min_length":
                    min_len = validation.value
                    scenarios.extend(
                        [
                            EdgeCaseScenario(
                                name=f"{field.name} - At Min Length ({min_len})",
                                field_name=field.name,
                                value="x" * min_len,
                                description=f"Exactly at minimum length {min_len}",
                                expected_result="success",
                                category="boundary",
                            ),
                            EdgeCaseScenario(
                                name=f"{field.name} - Below Min Length ({min_len - 1})",
                                field_name=field.name,
                                value="x" * (min_len - 1) if min_len > 0 else "",
                                description=f"One below minimum length",
                                expected_result="failure",
                                category="boundary",
                            ),
                        ]
                    )
                elif validation.rule_type == "max_length":
                    max_len = validation.value
                    scenarios.extend(
                        [
                            EdgeCaseScenario(
                                name=f"{field.name} - At Max Length ({max_len})",
                                field_name=field.name,
                                value="x" * max_len,
                                description=f"Exactly at maximum length {max_len}",
                                expected_result="success",
                                category="boundary",
                            ),
                            EdgeCaseScenario(
                                name=f"{field.name} - Above Max Length ({max_len + 1})",
                                field_name=field.name,
                                value="x" * (max_len + 1),
                                description=f"One above maximum length",
                                expected_result="failure",
                                category="boundary",
                            ),
                        ]
                    )

        # Numeric boundary cases
        elif "int" in field_type or "float" in field_type:
            for validation in field.validations:
                if validation.rule_type == "gt":
                    val = validation.value
                    scenarios.extend(
                        [
                            EdgeCaseScenario(
                                name=f"{field.name} - Just Above {val}",
                                field_name=field.name,
                                value=val + 1,
                                description=f"One above minimum {val}",
                                expected_result="success",
                                category="boundary",
                            ),
                            EdgeCaseScenario(
                                name=f"{field.name} - At {val}",
                                field_name=field.name,
                                value=val,
                                description=f"Exactly at boundary {val}",
                                expected_result="failure",
                                category="boundary",
                            ),
                        ]
                    )
                elif validation.rule_type == "lt":
                    val = validation.value
                    scenarios.extend(
                        [
                            EdgeCaseScenario(
                                name=f"{field.name} - Just Below {val}",
                                field_name=field.name,
                                value=val - 1,
                                description=f"One below maximum {val}",
                                expected_result="success",
                                category="boundary",
                            ),
                            EdgeCaseScenario(
                                name=f"{field.name} - At {val}",
                                field_name=field.name,
                                value=val,
                                description=f"Exactly at boundary {val}",
                                expected_result="failure",
                                category="boundary",
                            ),
                        ]
                    )

            # Extreme values
            scenarios.extend(
                [
                    EdgeCaseScenario(
                        name=f"{field.name} - Zero",
                        field_name=field.name,
                        value=0,
                        description="Zero value",
                        expected_result="boundary",
                        category="extreme",
                    ),
                    EdgeCaseScenario(
                        name=f"{field.name} - Negative",
                        field_name=field.name,
                        value=-1,
                        description="Negative value",
                        expected_result="boundary",
                        category="extreme",
                    ),
                ]
            )

        # Type mismatch cases
        type_mismatches = {
            "str": 123,
            "int": "not_a_number",
            "float": "not_a_float",
            "bool": "not_a_boolean",
            "datetime": "invalid_date",
        }

        for type_key, mismatch_val in type_mismatches.items():
            if type_key in field_type:
                scenarios.append(
                    EdgeCaseScenario(
                        name=f"{field.name} - Type Mismatch ({type_key})",
                        field_name=field.name,
                        value=mismatch_val,
                        description=f"Wrong type for {field.name}",
                        expected_result="failure",
                        category="type_mismatch",
                    )
                )

        return scenarios

    def add_anonymization_rule(self, rule: AnonymizationRule) -> None:
        """Add a custom anonymization rule."""
        self._anonymization_rules.append(rule)

    def anonymize_data(
        self,
        data: Dict[str, Any],
        entity_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Anonymize production data while preserving format.

        Args:
            data: Original data to anonymize
            entity_name: Optional entity name for context

        Returns:
            Anonymized data
        """
        result = {}

        for field, value in data.items():
            rule = self._find_anonymization_rule(field)
            if rule:
                result[field] = self._apply_anonymization(value, rule)
            else:
                # Auto-detect sensitive fields
                if self._is_sensitive_field(field):
                    result[field] = self._auto_anonymize(field, value)
                else:
                    result[field] = value

        return result

    def _find_anonymization_rule(self, field: str) -> Optional[AnonymizationRule]:
        """Find matching anonymization rule for field."""
        for rule in self._anonymization_rules:
            if re.match(rule.field_pattern, field, re.IGNORECASE):
                return rule
        return None

    def _is_sensitive_field(self, field: str) -> bool:
        """Auto-detect if field is sensitive."""
        sensitive_patterns = [
            r".*password.*",
            r".*secret.*",
            r".*token.*",
            r".*credit.*card.*",
            r".*ssn.*",
            r".*social.*security.*",
            r".*phone.*",
            r".*email.*",
            r".*address.*",
            r".*name.*",
        ]
        for pattern in sensitive_patterns:
            if re.match(pattern, field, re.IGNORECASE):
                return True
        return False

    def _apply_anonymization(self, value: Any, rule: AnonymizationRule) -> Any:
        """Apply anonymization method to value."""
        if value is None:
            return None

        if rule.method == "hash":
            return hashlib.sha256(str(value).encode()).hexdigest()[:16]
        elif rule.method == "mask":
            return self._mask_value(value, rule.preserve_format)
        elif rule.method == "replace":
            return self._generate_replacement_value(value)
        elif rule.method == "shuffle":
            # Return deterministic shuffle based on hash
            return self._shuffle_value(value)
        elif rule.method == "noise":
            return self._add_noise(value)
        else:
            return value

    def _auto_anonymize(self, field: str, value: Any) -> Any:
        """Auto-anonymize based on field name patterns."""
        field_lower = field.lower()

        if "email" in field_lower:
            return self._anonymize_email(value)
        elif "phone" in field_lower:
            return self._anonymize_phone(value)
        elif "name" in field_lower:
            return self._anonymize_name(value)
        elif "address" in field_lower:
            return self._anonymize_address(value)
        elif "password" in field_lower or "secret" in field_lower:
            return "********"
        else:
            # Default: hash
            return hashlib.sha256(str(value).encode()).hexdigest()[:12]

    def _mask_value(self, value: Any, preserve_format: bool) -> Any:
        """Mask value preserving format if needed."""
        str_val = str(value)
        if len(str_val) <= 4:
            return "****"
        return str_val[:2] + "****" + str_val[-2:]

    def _generate_replacement_value(self, original: Any) -> Any:
        """Generate a replacement value of same type."""
        if isinstance(original, str):
            return self._generate_random_string(len(original))
        elif isinstance(original, int):
            return random.randint(0, 1000000)
        elif isinstance(original, float):
            return random.uniform(0, 1000000)
        else:
            return original

    def _shuffle_value(self, value: Any) -> Any:
        """Deterministic shuffle of value."""
        str_val = str(value)
        # Use hash to seed for deterministic result
        hash_val = int(hashlib.sha256(str_val.encode()).hexdigest(), 16)
        random.seed(hash_val)
        shuffled = "".join(random.sample(str_val, len(str_val)))
        random.seed()  # Reset seed
        return shuffled

    def _add_noise(self, value: Any) -> Any:
        """Add noise to numeric values."""
        if isinstance(value, (int, float)):
            noise = random.uniform(-0.1, 0.1) * value
            return value + noise
        return value

    def _anonymize_email(self, email: Any) -> str:
        """Anonymize email while preserving domain."""
        if not isinstance(email, str) or "@" not in email:
            return "anonymous@example.com"
        local, domain = email.rsplit("@", 1)
        masked_local = local[:2] + "***" if len(local) > 2 else "***"
        return f"{masked_local}@{domain}"

    def _anonymize_phone(self, phone: Any) -> str:
        """Anonymize phone number."""
        if not isinstance(phone, str):
            phone = str(phone)
        # Keep last 4 digits
        return "***-***-" + phone[-4:] if len(phone) >= 4 else "***-***-****"

    def _anonymize_name(self, name: Any) -> str:
        """Anonymize name."""
        if not isinstance(name, str):
            name = str(name)
        # Replace with initials
        parts = name.split()
        return " ".join([p[0] + "." if p else "" for p in parts])

    def _anonymize_address(self, address: Any) -> str:
        """Anonymize address."""
        if not isinstance(address, str):
            address = str(address)
        # Keep street number and zip if present
        return address[:3] + " ***"

    def generate_valid_fk_value(self, entity: EntityInfo, fk_column: ColumnInfo) -> Any:
        """Generate a valid foreign key value from referenced entity.

        Args:
            entity: Entity containing the FK
            fk_column: Foreign key column

        Returns:
            Valid foreign key value from referenced entity
        """
        if not fk_column.foreign_key or not self.db_schema:
            return self._generate_valid_column_value(fk_column)

        # Parse foreign key reference (format: "table.column")
        parts = fk_column.foreign_key.split(".")
        if len(parts) < 1:
            return self._generate_valid_column_value(fk_column)

        ref_entity_name = parts[0]
        ref_column = parts[1] if len(parts) > 1 else "id"

        # Check if we have cached values
        cache_key = f"{ref_entity_name}.{ref_column}"
        if cache_key in self._fk_value_cache and self._fk_value_cache[cache_key]:
            return random.choice(self._fk_value_cache[cache_key])

        # Generate referenced entity if not exists
        ref_entity = self.db_schema.get_entity(ref_entity_name)
        if ref_entity:
            # Generate a few records and cache their PKs
            records = []
            for _ in range(5):
                data = self.generate_for_entity(ref_entity, DataGenerationStrategy.VALID)
                record = {k: v.value for k, v in data.items()}
                records.append(record)
                if ref_column in record:
                    self._fk_value_cache.setdefault(cache_key, []).append(record[ref_column])

            if self._fk_value_cache.get(cache_key):
                return random.choice(self._fk_value_cache[cache_key])

        return self._generate_valid_column_value(fk_column)

    def validate_referential_integrity(
        self, data: Dict[str, Any], entity: EntityInfo
    ) -> Tuple[bool, List[str]]:
        """Validate that generated data maintains referential integrity.

        Args:
            data: Generated data
            entity: Entity schema

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        for col in entity.columns:
            if col.foreign_key and col.name in data:
                fk_value = data[col.name]

                # Check if FK value exists in cache
                parts = col.foreign_key.split(".")
                if len(parts) >= 1:
                    ref_entity = parts[0]
                    ref_col = parts[1] if len(parts) > 1 else "id"
                    cache_key = f"{ref_entity}.{ref_col}"

                    if cache_key in self._fk_value_cache:
                        if fk_value not in self._fk_value_cache[cache_key]:
                            errors.append(
                                f"FK violation: {col.name}={fk_value} not in {ref_entity}.{ref_col}"
                            )

        return len(errors) == 0, errors
