"""Database fixture manager for socialseed-e2e."""

import json
import yaml
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

class FixtureManager:
    """Manages loading and applying database fixtures."""

    def __init__(self, connection: Any):
        self.connection = connection

    def load_from_file(self, file_path: Union[str, Path]):
        """Load fixture data from JSON or YAML file."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Fixture file not found: {file_path}")

        if file_path.suffix == ".json":
            with open(file_path, "r") as f:
                return json.load(f)
        elif file_path.suffix in [".yaml", ".yml"]:
            with open(file_path, "r") as f:
                return yaml.safe_load(f)
        else:
            raise ValueError(f"Unsupported fixture file format: {file_path.suffix}")

    def seed_sql_table(self, table_name: str, data: List[Dict[str, Any]], truncate: bool = False):
        """Seed a SQL table with data."""
        import sqlite3
        cursor = self.connection.cursor()
        
        if truncate:
            # Check for PostgreSQL/MySQL vs SQLite
            if isinstance(self.connection, sqlite3.Connection):
                cursor.execute(f"DELETE FROM {table_name}")
            else:
                cursor.execute(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE")

        if not data:
            self.connection.commit()
            return

        columns = data[0].keys()
        placeholders = ", ".join(["?" if isinstance(self.connection, sqlite3.Connection) else "%s"] * len(columns))
        query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
        
        values = [tuple(row[col] for col in columns) for row in data]
        cursor.executemany(query, values)
        self.connection.commit()

    def seed_mongodb_collection(self, db_name: str, collection_name: str, data: List[Dict[str, Any]]):
        """Seed a MongoDB collection."""
        db = self.connection[db_name]
        collection = db[collection_name]
        if data:
            collection.insert_many(data)

    def start_transaction(self):
        """Start a SQL transaction (if supported)."""
        if hasattr(self.connection, "autocommit"):
            self.connection.autocommit = False
            
    def rollback(self):
        """Rollback current SQL transaction."""
        if hasattr(self.connection, "rollback"):
            self.connection.rollback()
