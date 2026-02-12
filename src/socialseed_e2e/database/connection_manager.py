"""Database connection manager for socialseed-e2e."""

from typing import Any, Dict, Optional, Union
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages connections to various database types."""

    def __init__(self):
        self._connections: Dict[str, Any] = {}

    def connect_sql(self, db_type: str, dsn: str, name: str = "default") -> Any:
        """Connect to a SQL database (Postgres, MySQL, SQLite)."""
        if db_type == "sqlite":
            import sqlite3
            conn = sqlite3.connect(dsn)
        elif db_type == "postgresql":
            try:
                import psycopg2
                conn = psycopg2.connect(dsn)
            except ImportError:
                raise ImportError("psycopg2 is required for PostgreSQL. Install it with 'pip install psycopg2-binary'")
        elif db_type == "mysql":
            try:
                import pymysql
                conn = pymysql.connect(dsn)
            except ImportError:
                raise ImportError("pymysql is required for MySQL. Install it with 'pip install pymysql'")
        else:
            raise ValueError(f"Unsupported SQL database type: {db_type}")
        
        self._connections[name] = conn
        return conn

    def connect_mongodb(self, uri: str, name: str = "mongodb") -> Any:
        """Connect to a MongoDB database."""
        try:
            from pymongo import MongoClient
            client = MongoClient(uri)
            self._connections[name] = client
            return client
        except ImportError:
            raise ImportError("pymongo is required for MongoDB. Install it with 'pip install pymongo'")

    def connect_redis(self, host: str = "localhost", port: int = 6379, db: int = 0, name: str = "redis") -> Any:
        """Connect to a Redis instance."""
        try:
            import redis
            client = redis.Redis(host=host, port=port, db=db)
            self._connections[name] = client
            return client
        except ImportError:
            raise ImportError("redis is required for Redis support. Install it with 'pip install redis'")

    def connect_neo4j(self, uri: str, user: str, password: str, name: str = "neo4j") -> Any:
        """Connect to a Neo4j database."""
        try:
            from neo4j import GraphDatabase
            driver = GraphDatabase.driver(uri, auth=(user, password))
            self._connections[name] = driver
            return driver
        except ImportError:
            raise ImportError("neo4j is required for Neo4j support. Install it with 'pip install neo4j'")

    def get_connection(self, name: str = "default") -> Any:
        """Get an existing connection by name."""
        if name not in self._connections:
            raise KeyError(f"No connection found with name: {name}")
        return self._connections[name]

    def close_all(self):
        """Close all managed connections."""
        for name, conn in self._connections.items():
            try:
                if hasattr(conn, "close"):
                    conn.close()
                elif hasattr(conn, "driver"): # For Neo4j driver
                     conn.close()
            except Exception as e:
                logger.error(f"Error closing connection {name}: {e}")
        self._connections = {}
