"""Database schema scanner for extracting database schemas.

This module scans for database schemas, tables, relationships, and indexes.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class Table:
    """Represents a database table."""

    name: str
    columns: List[Dict[str, str]] = field(default_factory=list)
    primary_key: List[str] = field(default_factory=list)
    foreign_keys: List[Dict[str, str]] = field(default_factory=list)
    indexes: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class DatabaseInfo:
    """Represents database schema information."""

    type: str = ""
    tables: List[Table] = field(default_factory=list)
    relationships: List[Dict[str, str]] = field(default_factory=list)


class DatabaseSchemaScanner:
    """Scans for database schemas."""

    DB_TYPE_PATTERNS = {
        "PostgreSQL": [r"postgresql", r"psycopg2", r"pg_", r"CREATE TABLE"],
        "MySQL": [r"mysql", r"mysqld", r"mysql2", r"InnoDB"],
        "MongoDB": [r"mongodb", r"mongoose", r"MongoClient"],
        "SQLite": [r"sqlite", r"sqlite3", r"sqlite3\."],
        "Neo4j": [r"neo4j", r"cypher", r"graph DB"],
    }

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def scan(self) -> DatabaseInfo:
        """Scan project for database schemas."""
        info = DatabaseInfo()

        self._detect_db_type(info)
        self._extract_tables(info)
        self._detect_relationships(info)

        return info

    def _detect_db_type(self, info: DatabaseInfo) -> None:
        """Detect database type."""
        for ext in [".py", ".js", ".ts", ".java", ".sql"]:
            for file_path in self.project_root.rglob(f"*{ext}"):
                try:
                    content = file_path.read_text(errors="ignore")
                    for db_type, patterns in self.DB_TYPE_PATTERNS.items():
                        for pattern in patterns:
                            if re.search(pattern, content, re.IGNORECASE):
                                info.type = db_type
                                return
                except Exception:
                    pass

    def _extract_tables(self, info: DatabaseInfo) -> None:
        """Extract table definitions."""
        sql_files = list(self.project_root.rglob("*.sql"))
        
        for sql_file in sql_files:
            content = sql_file.read_text(errors="ignore")
            
            table_pattern = re.compile(r"CREATE TABLE\s+(?:IF NOT EXISTS\s+)?[\"`]?(\w+)[\"`]?", re.IGNORECASE)
            matches = table_pattern.finditer(content)
            
            for match in matches:
                table = Table(name=match.group(1))
                
                table_start = match.end()
                table_end = content.find(";", table_start)
                if table_end == -1:
                    table_end = len(content)
                
                table_content = content[table_start:table_end]
                
                col_pattern = re.compile(r"[\"`]?(\w+)[\"`]?\s+(\w+)", re.IGNORECASE)
                for col_match in col_pattern.finditer(table_content):
                    table.columns.append({
                        "name": col_match.group(1),
                        "type": col_match.group(2),
                    })
                
                pk_pattern = re.compile(r"PRIMARY KEY\s*\(([\w,\s]+)\)", re.IGNORECASE)
                pk_match = pk_pattern.search(table_content)
                if pk_match:
                    table.primary_key = [k.strip() for k in pk_match.group(1).split(",")]
                
                info.tables.append(table)

    def _detect_relationships(self, info: DatabaseInfo) -> None:
        """Detect table relationships."""
        for table in info.tables:
            for col in table.columns:
                col_name = col["name"].lower()
                if col_name.endswith("_id") or col_name == "id":
                    ref_table = col_name.replace("_id", "")
                    info.relationships.append({
                        "from": table.name,
                        "to": ref_table,
                        "type": "many-to-one",
                    })


def generate_database_schema_doc(project_root: Path, output_path: Optional[Path] = None) -> str:
    """Generate DATABASE_SCHEMA.md document."""
    scanner = DatabaseSchemaScanner(project_root)
    info = scanner.scan()

    doc = "# Schema de Base de Datos\n\n"

    doc += f"**Tipo de BD**: {info.type or 'No detectado'}\n\n"

    if info.tables:
        doc += "## Tablas\n\n"
        
        for table in info.tables:
            doc += f"### {table.name}\n\n"
            
            if table.primary_key:
                doc += f"**Primary Key**: {', '.join(table.primary_key)}\n\n"
            
            if table.columns:
                doc += "| Columna | Tipo |\n"
                doc += "|--------|------|\n"
                for col in table.columns:
                    doc += f"| {col['name']} | {col['type']} |\n"
                doc += "\n"
            
            if table.indexes:
                doc += "**Índices**: "
                doc += ", ".join([idx["name"] for idx in table.indexes])
                doc += "\n\n"

    if info.relationships:
        doc += "## Relaciones\n\n"
        doc += "| Desde | Hacia | Tipo |\n"
        doc += "|-------|-------|------|\n"
        for rel in info.relationships:
            doc += f"| {rel['from']} | {rel['to']} | {rel['type']} |\n"
        doc += "\n"

    if output_path:
        output_path.write_text(doc)

    return doc


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        project_root = Path(sys.argv[1])
        print(generate_database_schema_doc(project_root))
    else:
        print("Usage: python database_schema_scanner.py <project_root>")
