"""Database Model Parsers for extracting entity schemas from ORM models.

This module provides parsers for multiple ORM frameworks to extract:
- Entity/table definitions
- Column types and constraints
- Relationships between entities
- Validation constraints from database schema
"""

import ast
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Type, Union


@dataclass
class ColumnInfo:
    """Information about a database column."""

    name: str
    data_type: str
    nullable: bool = True
    default_value: Any = None
    primary_key: bool = False
    unique: bool = False
    foreign_key: Optional[str] = None  # "table.column"
    max_length: Optional[int] = None
    precision: Optional[int] = None
    scale: Optional[int] = None

    # Validation constraints extracted from DB
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    regex_pattern: Optional[str] = None
    enum_values: Optional[List[str]] = None


@dataclass
class EntityRelationship:
    """Relationship between database entities."""

    source_entity: str
    target_entity: str
    relationship_type: str  # "one-to-one", "one-to-many", "many-to-one", "many-to-many"
    source_column: str
    target_column: str
    cascade: List[str] = field(default_factory=list)
    nullable: bool = True


@dataclass
class EntityInfo:
    """Information about a database entity/table."""

    name: str
    table_name: str
    columns: List[ColumnInfo] = field(default_factory=list)
    primary_keys: List[str] = field(default_factory=list)
    relationships: List[EntityRelationship] = field(default_factory=list)
    indexes: List[List[str]] = field(default_factory=list)
    file_path: Optional[str] = None
    orm_framework: str = "unknown"  # sqlalchemy, prisma, hibernate, etc.


@dataclass
class DatabaseSchema:
    """Complete database schema information."""

    entities: List[EntityInfo] = field(default_factory=list)
    relationships: List[EntityRelationship] = field(default_factory=list)

    def get_entity(self, name: str) -> Optional[EntityInfo]:
        """Get entity by name."""
        for entity in self.entities:
            if entity.name == name or entity.table_name == name:
                return entity
        return None

    def get_column(self, entity_name: str, column_name: str) -> Optional[ColumnInfo]:
        """Get specific column from entity."""
        entity = self.get_entity(entity_name)
        if entity:
            for col in entity.columns:
                if col.name == column_name:
                    return col
        return None


class BaseDBParser(ABC):
    """Base class for database model parsers."""

    ORM_NAME: str = ""
    FILE_EXTENSIONS: List[str] = []

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.schema = DatabaseSchema()

    @abstractmethod
    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file."""
        pass

    @abstractmethod
    def parse_file(self, file_path: Path) -> List[EntityInfo]:
        """Parse a file and extract entity definitions."""
        pass

    def parse_project(self) -> DatabaseSchema:
        """Parse all files in the project to build complete schema."""
        for file_path in self.project_root.rglob("*"):
            if file_path.is_file() and self.can_parse(file_path):
                try:
                    entities = self.parse_file(file_path)
                    self.schema.entities.extend(entities)
                except Exception as e:
                    # Log error but continue parsing other files
                    print(f"Warning: Could not parse {file_path}: {e}")

        # Extract relationships after all entities are parsed
        self._extract_relationships()
        return self.schema

    def _extract_relationships(self) -> None:
        """Extract relationships between entities."""
        for entity in self.schema.entities:
            for col in entity.columns:
                if col.foreign_key:
                    target_table = col.foreign_key.split(".")[0]
                    target_entity = self.schema.get_entity(target_table)
                    if target_entity:
                        rel = EntityRelationship(
                            source_entity=entity.name,
                            target_entity=target_entity.name,
                            relationship_type="many-to-one",
                            source_column=col.name,
                            target_column=col.foreign_key.split(".")[1],
                        )
                        entity.relationships.append(rel)
                        self.schema.relationships.append(rel)


class SQLAlchemyParser(BaseDBParser):
    """Parser for SQLAlchemy models (Python)."""

    ORM_NAME = "sqlalchemy"
    FILE_EXTENSIONS = [".py"]

    # SQLAlchemy type mappings
    TYPE_MAPPINGS = {
        "String": "str",
        "Integer": "int",
        "BigInteger": "int",
        "SmallInteger": "int",
        "Float": "float",
        "Numeric": "float",
        "Boolean": "bool",
        "Date": "date",
        "DateTime": "datetime",
        "Time": "time",
        "Text": "str",
        "Unicode": "str",
        "UnicodeText": "str",
        "JSON": "dict",
        "ARRAY": "list",
        "Enum": "enum",
        "UUID": "uuid",
    }

    def can_parse(self, file_path: Path) -> bool:
        """Check if file contains SQLAlchemy models."""
        if file_path.suffix != ".py":
            return False

        try:
            content = file_path.read_text(encoding="utf-8")
            return "from sqlalchemy" in content or "import sqlalchemy" in content
        except:
            return False

    def parse_file(self, file_path: Path) -> List[EntityInfo]:
        """Parse SQLAlchemy models from Python file."""
        content = file_path.read_text(encoding="utf-8")
        entities = []

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return entities

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                entity = self._parse_class(node, content, str(file_path))
                if entity:
                    entities.append(entity)

        return entities

    def _parse_class(
        self, node: ast.ClassDef, content: str, file_path: str
    ) -> Optional[EntityInfo]:
        """Parse a SQLAlchemy model class."""
        # Check if it's a SQLAlchemy model
        is_declarative = False
        for base in node.bases:
            base_name = self._get_base_name(base)
            if base_name and ("Base" in base_name or "Model" in base_name):
                is_declarative = True
                break

        if not is_declarative:
            return None

        entity = EntityInfo(
            name=node.name,
            table_name=self._extract_table_name(node, content),
            file_path=file_path,
            orm_framework="sqlalchemy",
        )

        # Parse columns
        for item in node.body:
            if isinstance(item, ast.Assign):
                column = self._parse_column_assignment(item, content)
                if column:
                    entity.columns.append(column)
            elif isinstance(item, ast.AnnAssign):
                column = self._parse_column_annotation(item, content)
                if column:
                    entity.columns.append(column)

        # Extract primary keys
        entity.primary_keys = [col.name for col in entity.columns if col.primary_key]

        return entity

    def _get_base_name(self, base: ast.AST) -> Optional[str]:
        """Get name of base class."""
        if isinstance(base, ast.Name):
            return base.id
        elif isinstance(base, ast.Attribute):
            return base.attr
        return None

    def _extract_table_name(self, node: ast.ClassDef, content: str) -> str:
        """Extract __tablename__ from class."""
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name) and target.id == "__tablename__":
                        if isinstance(item.value, ast.Constant):
                            return item.value.value
                        elif isinstance(item.value, ast.Str):
                            return item.value.s

        # Default to snake_case of class name
        return self._to_snake_case(node.name)

    def _parse_column_assignment(self, node: ast.Assign, content: str) -> Optional[ColumnInfo]:
        """Parse a column defined via assignment."""
        if len(node.targets) != 1:
            return None

        target = node.targets[0]
        if not isinstance(target, ast.Name):
            return None

        column_name = target.id

        # Check if value is a Column() call
        if isinstance(node.value, ast.Call):
            func_name = self._get_call_name(node.value.func)
            if func_name and "Column" in func_name:
                return self._extract_column_info(node.value, column_name)

        return None

    def _parse_column_annotation(self, node: ast.AnnAssign, content: str) -> Optional[ColumnInfo]:
        """Parse a column defined via type annotation (SQLAlchemy 2.0)."""
        if not isinstance(node.target, ast.Name):
            return None

        column_name = node.target.id

        # For SQLAlchemy 2.0 mapped_column
        if isinstance(node.value, ast.Call):
            func_name = self._get_call_name(node.value.func)
            if func_name and "mapped_column" in func_name:
                return self._extract_mapped_column_info(node.value, column_name, node.annotation)

        return None

    def _get_call_name(self, func: ast.AST) -> Optional[str]:
        """Get name of a function call."""
        if isinstance(func, ast.Name):
            return func.id
        elif isinstance(func, ast.Attribute):
            return func.attr
        return None

    def _extract_column_info(self, call: ast.Call, column_name: str) -> ColumnInfo:
        """Extract column information from Column() call."""
        column = ColumnInfo(name=column_name)

        # First argument is usually the type
        if call.args:
            type_info = self._extract_type_info(call.args[0])
            column.data_type = type_info.get("type", "str")
            column.max_length = type_info.get("length")
            column.precision = type_info.get("precision")
            column.scale = type_info.get("scale")

        # Parse keyword arguments
        for keyword in call.keywords:
            arg_name = keyword.arg
            if arg_name == "primary_key":
                column.primary_key = self._get_bool_value(keyword.value)
            elif arg_name == "nullable":
                column.nullable = self._get_bool_value(keyword.value)
            elif arg_name == "unique":
                column.unique = self._get_bool_value(keyword.value)
            elif arg_name == "default":
                column.default_value = self._get_value(keyword.value)
            elif arg_name == "ForeignKey":
                if isinstance(keyword.value, (ast.Constant, ast.Str)):
                    column.foreign_key = self._get_string_value(keyword.value)

        return column

    def _extract_mapped_column_info(
        self, call: ast.Call, column_name: str, annotation: ast.AST
    ) -> ColumnInfo:
        """Extract column info from mapped_column() call."""
        column = ColumnInfo(name=column_name)

        # Extract type from annotation
        column.data_type = self._annotation_to_type(annotation)

        # Parse keyword arguments
        for keyword in call.keywords:
            arg_name = keyword.arg
            if arg_name == "primary_key":
                column.primary_key = self._get_bool_value(keyword.value)
            elif arg_name == "nullable":
                column.nullable = self._get_bool_value(keyword.value)
            elif arg_name == "unique":
                column.unique = self._get_bool_value(keyword.value)
            elif arg_name == "default":
                column.default_value = self._get_value(keyword.value)

        return column

    def _extract_type_info(self, node: ast.AST) -> Dict[str, Any]:
        """Extract type information from SQLAlchemy type."""
        info = {"type": "str"}

        if isinstance(node, ast.Call):
            func_name = self._get_call_name(node.func)

            # Map SQLAlchemy types to Python types
            for sa_type, py_type in self.TYPE_MAPPINGS.items():
                if func_name and sa_type in func_name:
                    info["type"] = py_type
                    break

            # Extract length for String types
            if func_name and "String" in func_name:
                if node.args:
                    info["length"] = self._get_int_value(node.args[0])

            # Extract precision/scale for Numeric
            if func_name and ("Numeric" in func_name or "Float" in func_name):
                if len(node.args) >= 1:
                    info["precision"] = self._get_int_value(node.args[0])
                if len(node.args) >= 2:
                    info["scale"] = self._get_int_value(node.args[1])

        return info

    def _annotation_to_type(self, annotation: ast.AST) -> str:
        """Convert type annotation to string type."""
        if isinstance(annotation, ast.Name):
            return annotation.id.lower()
        elif isinstance(annotation, ast.Subscript):
            value = self._annotation_to_type(annotation.value)
            slice_val = self._annotation_to_type(annotation.slice)
            return f"{value}[{slice_val}]"
        elif isinstance(annotation, ast.Constant):
            return str(annotation.value)
        return "str"

    def _get_bool_value(self, node: ast.AST) -> bool:
        """Extract boolean value from AST node."""
        if isinstance(node, ast.Constant):
            return bool(node.value)
        elif isinstance(node, ast.NameConstant):
            return bool(node.value)
        return False

    def _get_int_value(self, node: ast.AST) -> Optional[int]:
        """Extract integer value from AST node."""
        if isinstance(node, ast.Constant):
            return int(node.value) if isinstance(node.value, (int, float)) else None
        elif isinstance(node, ast.Num):
            return int(node.n)
        return None

    def _get_string_value(self, node: ast.AST) -> Optional[str]:
        """Extract string value from AST node."""
        if isinstance(node, ast.Constant):
            return str(node.value)
        elif isinstance(node, ast.Str):
            return node.s
        return None

    def _get_value(self, node: ast.AST) -> Any:
        """Extract value from AST node."""
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.NameConstant):
            return node.value
        elif isinstance(node, ast.Name):
            return node.id
        return None

    def _to_snake_case(self, name: str) -> str:
        """Convert CamelCase to snake_case."""
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


class PrismaParser(BaseDBParser):
    """Parser for Prisma schema files."""

    ORM_NAME = "prisma"
    FILE_EXTENSIONS = [".prisma"]

    # Prisma type mappings
    TYPE_MAPPINGS = {
        "String": "str",
        "Int": "int",
        "BigInt": "int",
        "Float": "float",
        "Decimal": "float",
        "Boolean": "bool",
        "DateTime": "datetime",
        "Json": "dict",
        "Bytes": "bytes",
        "Enum": "enum",
        "UUID": "uuid",
    }

    def can_parse(self, file_path: Path) -> bool:
        """Check if file is a Prisma schema file."""
        return file_path.suffix == ".prisma"

    def parse_file(self, file_path: Path) -> List[EntityInfo]:
        """Parse Prisma schema file."""
        content = file_path.read_text(encoding="utf-8")
        entities = []

        # Parse model definitions
        model_pattern = r"model\s+(\w+)\s*\{([^}]+)\}"
        matches = re.finditer(model_pattern, content, re.DOTALL)

        for match in matches:
            model_name = match.group(1)
            model_body = match.group(2)

            entity = EntityInfo(
                name=model_name,
                table_name=self._to_snake_case(model_name),
                file_path=str(file_path),
                orm_framework="prisma",
            )

            # Parse fields
            entity.columns = self._parse_prisma_fields(model_body)

            # Extract primary keys
            entity.primary_keys = [col.name for col in entity.columns if col.primary_key]

            entities.append(entity)

        return entities

    def _parse_prisma_fields(self, model_body: str) -> List[ColumnInfo]:
        """Parse fields from Prisma model body."""
        columns = []

        # Split by lines and parse each field
        lines = model_body.strip().split("\n")

        for line in lines:
            line = line.strip()
            if not line or line.startswith("//") or line.startswith("@@"):
                continue

            column = self._parse_prisma_field_line(line)
            if column:
                columns.append(column)

        return columns

    def _parse_prisma_field_line(self, line: str) -> Optional[ColumnInfo]:
        """Parse a single Prisma field definition."""
        # Pattern: fieldName Type @attributes
        pattern = r"^(\w+)\s+(\w+)(?:\(([^)]+)\))?\s*(.*)$"
        match = re.match(pattern, line)

        if not match:
            return None

        field_name = match.group(1)
        field_type = match.group(2)
        type_args = match.group(3)
        attributes = match.group(4)

        column = ColumnInfo(name=field_name)

        # Map type
        column.data_type = self.TYPE_MAPPINGS.get(field_type, "str")

        # Parse type arguments (e.g., String(255))
        if type_args:
            try:
                column.max_length = int(type_args)
            except ValueError:
                pass

        # Parse attributes
        if attributes:
            # Check for @id (primary key)
            if "@id" in attributes:
                column.primary_key = True
                column.nullable = False

            # Check for @unique
            if "@unique" in attributes:
                column.unique = True

            # Check for @default
            default_match = re.search(r"@default\(([^)]+)\)", attributes)
            if default_match:
                column.default_value = default_match.group(1)

            # Check for @relation (foreign key)
            relation_match = re.search(r"@relation\([^)]*fields:\s*\[([^\]]+)\]", attributes)
            if relation_match:
                # This is a relation field, not a direct FK column
                pass

            # Check for ? (nullable)
            if field_type.endswith("?"):
                column.nullable = True
            elif "@id" in attributes or "@default" in attributes:
                column.nullable = False
            else:
                column.nullable = False  # Prisma fields are NOT NULL by default

        return column

    def _to_snake_case(self, name: str) -> str:
        """Convert CamelCase to snake_case."""
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


class HibernateParser(BaseDBParser):
    """Parser for Hibernate/JPA entities (Java)."""

    ORM_NAME = "hibernate"
    FILE_EXTENSIONS = [".java"]

    # Hibernate type mappings
    TYPE_MAPPINGS = {
        "String": "str",
        "Integer": "int",
        "Long": "int",
        "Short": "int",
        "Float": "float",
        "Double": "float",
        "BigDecimal": "float",
        "Boolean": "bool",
        "Date": "datetime",
        "LocalDate": "date",
        "LocalDateTime": "datetime",
        "Timestamp": "datetime",
        "Time": "time",
        "Text": "str",
        "Clob": "str",
        "Blob": "bytes",
        "UUID": "uuid",
        "EnumType": "enum",
    }

    def can_parse(self, file_path: Path) -> bool:
        """Check if file is a Java file with JPA annotations."""
        if file_path.suffix != ".java":
            return False

        try:
            content = file_path.read_text(encoding="utf-8")
            return (
                "@Entity" in content
                or "javax.persistence" in content
                or "jakarta.persistence" in content
            )
        except:
            return False

    def parse_file(self, file_path: Path) -> List[EntityInfo]:
        """Parse JPA entity from Java file."""
        content = file_path.read_text(encoding="utf-8")
        entities = []

        # Find @Entity classes
        entity_pattern = r'@Entity(?:\s*\(\s*name\s*=\s*"([^"]+)"\s*\))?.*?class\s+(\w+)'
        matches = re.finditer(entity_pattern, content, re.DOTALL)

        for match in matches:
            entity_name = match.group(2)
            table_name = match.group(1) or self._to_snake_case(entity_name)

            entity = EntityInfo(
                name=entity_name,
                table_name=table_name,
                file_path=str(file_path),
                orm_framework="hibernate",
            )

            # Find class body
            class_start = match.end()
            class_body = self._extract_class_body(content[class_start:])

            # Parse fields
            entity.columns = self._parse_java_fields(class_body)

            # Extract primary keys
            entity.primary_keys = [col.name for col in entity.columns if col.primary_key]

            entities.append(entity)

        return entities

    def _extract_class_body(self, content: str) -> str:
        """Extract the body of a Java class."""
        brace_count = 0
        start_found = False
        end_pos = 0

        for i, char in enumerate(content):
            if char == "{":
                if not start_found:
                    start_found = True
                brace_count += 1
            elif char == "}":
                brace_count -= 1
                if brace_count == 0 and start_found:
                    end_pos = i
                    break

        return content[:end_pos]

    def _parse_java_fields(self, class_body: str) -> List[ColumnInfo]:
        """Parse fields from Java class body."""
        columns = []

        # Pattern for field declarations with JPA annotations
        field_pattern = (
            r"((?:@\w+(?:\([^)]*\))?\s+)*)"
            r"(?:private|protected|public)\s+"
            r"(\w+(?:<[^>]+>)?)\s+"
            r"(\w+)\s*;"
        )

        matches = re.finditer(field_pattern, class_body)

        for match in matches:
            annotations = match.group(1)
            field_type = match.group(2)
            field_name = match.group(3)

            column = ColumnInfo(name=field_name)

            # Map Java type
            for java_type, py_type in self.TYPE_MAPPINGS.items():
                if java_type in field_type:
                    column.data_type = py_type
                    break
            else:
                column.data_type = "str"  # Default

            # Parse JPA annotations
            if annotations:
                # @Id (primary key)
                if "@Id" in annotations:
                    column.primary_key = True
                    column.nullable = False

                # @Column attributes
                column_match = re.search(r"@Column\(([^)]+)\)", annotations)
                if column_match:
                    column_attrs = column_match.group(1)

                    # nullable
                    nullable_match = re.search(r"nullable\s*=\s*(\w+)", column_attrs)
                    if nullable_match:
                        column.nullable = nullable_match.group(1).lower() == "true"

                    # unique
                    unique_match = re.search(r"unique\s*=\s*(\w+)", column_attrs)
                    if unique_match:
                        column.unique = unique_match.group(1).lower() == "true"

                    # length
                    length_match = re.search(r"length\s*=\s*(\d+)", column_attrs)
                    if length_match:
                        column.max_length = int(length_match.group(1))

                # @GeneratedValue (auto-generated)
                if "@GeneratedValue" in annotations:
                    column.default_value = "auto"

            columns.append(column)

        return columns

    def _to_snake_case(self, name: str) -> str:
        """Convert CamelCase to snake_case."""
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


class DatabaseParserRegistry:
    """Registry for database model parsers."""

    def __init__(self):
        self._parsers: List[Type[BaseDBParser]] = []
        self.register_defaults()

    def register(self, parser_class: Type[BaseDBParser]) -> None:
        """Register a parser class."""
        self._parsers.append(parser_class)

    def register_defaults(self) -> None:
        """Register default parsers."""
        self.register(SQLAlchemyParser)
        self.register(PrismaParser)
        self.register(HibernateParser)

    def get_parser(self, file_path: Path, project_root: Path) -> Optional[BaseDBParser]:
        """Get appropriate parser for a file."""
        for parser_class in self._parsers:
            parser = parser_class(project_root)
            if parser.can_parse(file_path):
                return parser
        return None

    def parse_project(self, project_root: Path) -> DatabaseSchema:
        """Parse entire project and return complete schema."""
        schema = DatabaseSchema()

        for parser_class in self._parsers:
            parser = parser_class(project_root)
            parsed_schema = parser.parse_project()
            schema.entities.extend(parsed_schema.entities)
            schema.relationships.extend(parsed_schema.relationships)

        return schema


# Global registry instance
db_parser_registry = DatabaseParserRegistry()
