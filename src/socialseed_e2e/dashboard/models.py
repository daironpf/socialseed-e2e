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


class RequestHistory:
    """Request history model."""

    def __init__(
        self,
        id: int = None,
        timestamp: str = None,
        method: str = "",
        url: str = "",
        headers: str = None,
        body: str = None,
        response_status: int = None,
        response_body: str = None,
        response_headers: str = None,
        duration_ms: int = None,
        environment_id: int = None,
    ):
        self.id = id
        self.timestamp = timestamp or datetime.now().isoformat()
        self.method = method
        self.url = url
        self.headers = headers or "{}"
        self.body = body or ""
        self.response_status = response_status
        self.response_body = response_body or ""
        self.response_headers = response_headers or "{}"
        self.duration_ms = duration_ms
        self.environment_id = environment_id

    @staticmethod
    def get_all(limit: int = 100) -> List["RequestHistory"]:
        """Get all history entries."""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM request_history ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        )
        rows = cursor.fetchall()
        conn.close()
        return [RequestHistory.from_row(row) for row in rows]

    @staticmethod
    def get_by_id(id: int) -> Optional["RequestHistory"]:
        """Get history by ID."""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM request_history WHERE id = ?", (id,))
        row = cursor.fetchone()
        conn.close()
        return RequestHistory.from_row(row) if row else None

    @staticmethod
    def from_row(row) -> "RequestHistory":
        """Create from database row."""
        return RequestHistory(
            id=row["id"],
            timestamp=row["timestamp"],
            method=row["method"],
            url=row["url"],
            headers=row["headers"],
            body=row["body"],
            response_status=row["response_status"],
            response_body=row["response_body"],
            response_headers=row["response_headers"],
            duration_ms=row["duration_ms"],
            environment_id=row["environment_id"],
        )

    def save(self) -> "RequestHistory":
        """Save history entry to database."""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO request_history 
            (timestamp, method, url, headers, body, response_status, response_body, response_headers, duration_ms, environment_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                self.timestamp,
                self.method,
                self.url,
                self.headers,
                self.body,
                self.response_status,
                self.response_body,
                self.response_headers,
                self.duration_ms,
                self.environment_id,
            ),
        )
        self.id = cursor.lastrowid
        conn.commit()
        conn.close()
        return self

    def delete(self) -> None:
        """Delete history entry."""
        if self.id:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM request_history WHERE id = ?", (self.id,))
            conn.commit()
            conn.close()

    @staticmethod
    def delete_all() -> None:
        """Delete all history entries."""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM request_history")
        conn.commit()
        conn.close()


class Collection:
    """Collection model for grouping requests."""

    def __init__(
        self,
        id: int = None,
        name: str = "",
        description: str = "",
        created_at: str = None,
        updated_at: str = None,
    ):
        self.id = id
        self.name = name
        self.description = description or ""
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = updated_at or datetime.now().isoformat()

    @staticmethod
    def get_all() -> List["Collection"]:
        """Get all collections."""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM collections ORDER BY name")
        rows = cursor.fetchall()
        conn.close()
        return [Collection.from_row(row) for row in rows]

    @staticmethod
    def get_by_id(id: int) -> Optional["Collection"]:
        """Get collection by ID."""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM collections WHERE id = ?", (id,))
        row = cursor.fetchone()
        conn.close()
        return Collection.from_row(row) if row else None

    @staticmethod
    def from_row(row) -> "Collection":
        """Create from database row."""
        return Collection(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def save(self) -> "Collection":
        """Save collection to database."""
        conn = get_db()
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        if self.id:
            cursor.execute(
                """
                UPDATE collections SET name = ?, description = ?, updated_at = ?
                WHERE id = ?
            """,
                (self.name, self.description, now, self.id),
            )
        else:
            cursor.execute(
                """
                INSERT INTO collections (name, description, created_at, updated_at)
                VALUES (?, ?, ?, ?)
            """,
                (self.name, self.description, now, now),
            )
            self.id = cursor.lastrowid

        conn.commit()
        conn.close()
        self.updated_at = now
        return self

    def delete(self) -> None:
        """Delete collection."""
        if self.id:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM collections WHERE id = ?", (self.id,))
            conn.commit()
            conn.close()


class SavedRequest:
    """Saved request model."""

    def __init__(
        self,
        id: int = None,
        collection_id: int = None,
        name: str = "",
        method: str = "GET",
        url: str = "",
        headers: str = "{}",
        body: str = "",
        params: str = "{}",
        tests: str = "",
        order_index: int = 0,
        created_at: str = None,
        updated_at: str = None,
    ):
        self.id = id
        self.collection_id = collection_id
        self.name = name
        self.method = method
        self.url = url
        self.headers = headers or "{}"
        self.body = body or ""
        self.params = params or "{}"
        self.tests = tests or ""
        self.order_index = order_index
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = updated_at or datetime.now().isoformat()

    @staticmethod
    def get_all(collection_id: int = None) -> List["SavedRequest"]:
        """Get all saved requests, optionally filtered by collection."""
        conn = get_db()
        cursor = conn.cursor()
        if collection_id:
            cursor.execute(
                "SELECT * FROM saved_requests WHERE collection_id = ? ORDER BY order_index, name",
                (collection_id,),
            )
        else:
            cursor.execute(
                "SELECT * FROM saved_requests ORDER BY collection_id, order_index, name"
            )
        rows = cursor.fetchall()
        conn.close()
        return [SavedRequest.from_row(row) for row in rows]

    @staticmethod
    def get_by_id(id: int) -> Optional["SavedRequest"]:
        """Get saved request by ID."""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM saved_requests WHERE id = ?", (id,))
        row = cursor.fetchone()
        conn.close()
        return SavedRequest.from_row(row) if row else None

    @staticmethod
    def from_row(row) -> "SavedRequest":
        """Create from database row."""
        return SavedRequest(
            id=row["id"],
            collection_id=row["collection_id"],
            name=row["name"],
            method=row["method"],
            url=row["url"],
            headers=row["headers"],
            body=row["body"],
            params=row["params"],
            tests=row["tests"],
            order_index=row["order_index"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def save(self) -> "SavedRequest":
        """Save request to database."""
        conn = get_db()
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        if self.id:
            cursor.execute(
                """
                UPDATE saved_requests 
                SET collection_id = ?, name = ?, method = ?, url = ?, headers = ?, 
                    body = ?, params = ?, tests = ?, order_index = ?, updated_at = ?
                WHERE id = ?
            """,
                (
                    self.collection_id,
                    self.name,
                    self.method,
                    self.url,
                    self.headers,
                    self.body,
                    self.params,
                    self.tests,
                    self.order_index,
                    now,
                    self.id,
                ),
            )
        else:
            cursor.execute(
                """
                INSERT INTO saved_requests 
                (collection_id, name, method, url, headers, body, params, tests, order_index, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    self.collection_id,
                    self.name,
                    self.method,
                    self.url,
                    self.headers,
                    self.body,
                    self.params,
                    self.tests,
                    self.order_index,
                    now,
                    now,
                ),
            )
            self.id = cursor.lastrowid

        conn.commit()
        conn.close()
        self.updated_at = now
        return self

    def delete(self) -> None:
        """Delete saved request."""
        if self.id:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM saved_requests WHERE id = ?", (self.id,))
            conn.commit()
            conn.close()


# Initialize database on module load
init_db()
