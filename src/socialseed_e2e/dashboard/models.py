"""Database models for dashboard."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path.cwd()
DB_PATH = PROJECT_ROOT / ".e2e" / "dashboard.db"


def get_db() -> sqlite3.Connection:
    """Get database connection."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database tables."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            test_name TEXT NOT NULL,
            test_path TEXT NOT NULL,
            service_name TEXT,
            status TEXT NOT NULL,
            duration_ms INTEGER,
            output TEXT,
            error_message TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_suites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            tests TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS environments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            variables TEXT NOT NULL,
            is_active INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS collections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS saved_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            collection_id INTEGER,
            name TEXT NOT NULL,
            method TEXT NOT NULL,
            url TEXT NOT NULL,
            headers TEXT,
            body TEXT,
            params TEXT,
            tests TEXT,
            order_index INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (collection_id) REFERENCES collections(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS request_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            method TEXT NOT NULL,
            url TEXT NOT NULL,
            headers TEXT,
            body TEXT,
            response_status INTEGER,
            response_body TEXT,
            response_headers TEXT,
            duration_ms INTEGER,
            environment_id INTEGER
        )
    """)

    conn.commit()
    conn.close()


class Environment:
    """Environment model."""

    def __init__(
        self,
        id: int = None,
        name: str = "",
        variables: Dict[str, str] = None,
        is_active: bool = False,
        created_at: str = None,
        updated_at: str = None,
    ):
        self.id = id
        self.name = name
        self.variables = variables or {}
        self.is_active = is_active
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = updated_at or datetime.now().isoformat()

    @staticmethod
    def get_all() -> List["Environment"]:
        """Get all environments."""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM environments ORDER BY name")
        rows = cursor.fetchall()
        conn.close()
        return [Environment.from_row(row) for row in rows]

    @staticmethod
    def get_active() -> Optional["Environment"]:
        """Get active environment."""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM environments WHERE is_active = 1 LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        return Environment.from_row(row) if row else None

    @staticmethod
    def from_row(row) -> "Environment":
        """Create from database row."""
        import json

        return Environment(
            id=row["id"],
            name=row["name"],
            variables=json.loads(row["variables"]),
            is_active=bool(row["is_active"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def save(self) -> "Environment":
        """Save environment to database."""
        import json

        conn = get_db()
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        if self.id:
            cursor.execute(
                """
                UPDATE environments
                SET name = ?, variables = ?, is_active = ?, updated_at = ?
                WHERE id = ?
            """,
                (
                    self.name,
                    json.dumps(self.variables),
                    int(self.is_active),
                    now,
                    self.id,
                ),
            )
        else:
            cursor.execute(
                """
                INSERT INTO environments (name, variables, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """,
                (self.name, json.dumps(self.variables), int(self.is_active), now, now),
            )
            self.id = cursor.lastrowid

        conn.commit()
        conn.close()
        self.updated_at = now
        return self

    def delete(self) -> None:
        """Delete environment."""
        if self.id:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM environments WHERE id = ?", (self.id,))
            conn.commit()
            conn.close()

    def activate(self) -> "Environment":
        """Activate this environment (deactivate others)."""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE environments SET is_active = 0")
        cursor.execute("UPDATE environments SET is_active = 1 WHERE id = ?", (self.id,))
        conn.commit()
        conn.close()
        self.is_active = True
        return self


# Initialize database on module load
init_db()
