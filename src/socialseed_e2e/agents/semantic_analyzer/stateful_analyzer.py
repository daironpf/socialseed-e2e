"""Stateful Analyzer.

Captures snapshots of API responses and database states before and after
code changes to enable semantic comparison.
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import uuid

from models import APISnapshot, DatabaseSnapshot, StateSnapshot


class StatefulAnalyzer:
    """Analyzer that captures and compares system states."""

    def __init__(self, project_root: Path, base_url: Optional[str] = None):
        self.project_root = project_root
        self.base_url = base_url or "http://localhost:8080"
        self.snapshots: Dict[str, StateSnapshot] = {}

    def capture_baseline_state(
        self,
        commit_hash: Optional[str] = None,
        branch: Optional[str] = None,
        api_endpoints: Optional[List[Dict[str, Any]]] = None,
        database_configs: Optional[List[Dict[str, Any]]] = None,
    ) -> StateSnapshot:
        """Capture baseline state before code changes."""
        snapshot_id = self._generate_snapshot_id("baseline")

        snapshot = StateSnapshot(
            snapshot_id=snapshot_id,
            commit_hash=commit_hash,
            branch=branch,
        )

        # Capture API states
        if api_endpoints:
            for endpoint_config in api_endpoints:
                api_snapshot = self._capture_api_state(endpoint_config)
                if api_snapshot:
                    snapshot.api_snapshots.append(api_snapshot)

        # Capture database states
        if database_configs:
            for db_config in database_configs:
                db_snapshot = self._capture_database_state(db_config)
                if db_snapshot:
                    snapshot.database_snapshots.append(db_snapshot)

        self.snapshots[snapshot_id] = snapshot
        return snapshot

    def capture_current_state(
        self,
        baseline_snapshot: StateSnapshot,
        commit_hash: Optional[str] = None,
    ) -> StateSnapshot:
        """Capture current state after code changes."""
        snapshot_id = self._generate_snapshot_id("current")

        snapshot = StateSnapshot(
            snapshot_id=snapshot_id,
            commit_hash=commit_hash,
        )

        # Re-capture the same API endpoints as baseline
        for api_snapshot in baseline_snapshot.api_snapshots:
            endpoint_config = {
                "endpoint": api_snapshot.endpoint,
                "method": api_snapshot.method,
                "params": api_snapshot.request_params,
                "body": api_snapshot.request_body,
            }
            new_snapshot = self._capture_api_state(endpoint_config)
            if new_snapshot:
                snapshot.api_snapshots.append(new_snapshot)

        # Re-capture the same databases as baseline
        for db_snapshot in baseline_snapshot.database_snapshots:
            db_config = {
                "type": db_snapshot.database_type,
                "connection": db_snapshot.connection_string,
            }
            new_snapshot = self._capture_database_state(db_config)
            if new_snapshot:
                snapshot.database_snapshots.append(new_snapshot)

        self.snapshots[snapshot_id] = snapshot
        return snapshot

    def _capture_api_state(
        self, endpoint_config: Dict[str, Any]
    ) -> Optional[APISnapshot]:
        """Capture state of a single API endpoint."""
        try:
            # Import here to avoid dependency issues
            import requests

            endpoint = endpoint_config.get("endpoint", "/")
            method = endpoint_config.get("method", "GET").upper()
            params = endpoint_config.get("params", {})
            body = endpoint_config.get("body")
            headers = endpoint_config.get("headers", {})

            url = f"{self.base_url}{endpoint}"

            start_time = datetime.now()

            if method == "GET":
                response = requests.get(url, params=params, headers=headers, timeout=30)
            elif method == "POST":
                response = requests.post(url, json=body, headers=headers, timeout=30)
            elif method == "PUT":
                response = requests.put(url, json=body, headers=headers, timeout=30)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, timeout=30)
            elif method == "PATCH":
                response = requests.patch(url, json=body, headers=headers, timeout=30)
            else:
                return None

            duration = (datetime.now() - start_time).total_seconds() * 1000

            response_body = {}
            try:
                response_body = response.json()
            except:
                response_body = {"text": response.text}

            return APISnapshot(
                endpoint=endpoint,
                method=method,
                request_params=params,
                request_body=body,
                response_body=response_body,
                response_status=response.status_code,
                response_headers=dict(response.headers),
                duration_ms=duration,
            )

        except Exception as e:
            print(f"Warning: Could not capture API state for {endpoint_config}: {e}")
            return None

    def _capture_database_state(
        self, db_config: Dict[str, Any]
    ) -> Optional[DatabaseSnapshot]:
        """Capture state of a database."""
        db_type = db_config.get("type", "").lower()

        try:
            if db_type == "neo4j":
                return self._capture_neo4j_state(db_config)
            elif db_type in ["postgresql", "postgres", "mysql", "sqlite"]:
                return self._capture_sql_state(db_config)
            elif db_type in ["mongodb", "mongo"]:
                return self._capture_mongodb_state(db_config)
            else:
                print(f"Warning: Unsupported database type: {db_type}")
                return None
        except Exception as e:
            print(f"Warning: Could not capture database state: {e}")
            return None

    def _capture_neo4j_state(
        self, db_config: Dict[str, Any]
    ) -> Optional[DatabaseSnapshot]:
        """Capture Neo4j graph database state."""
        try:
            from neo4j import GraphDatabase

            uri = db_config.get("uri", "bolt://localhost:7687")
            user = db_config.get("user", "neo4j")
            password = db_config.get("password", "password")

            driver = GraphDatabase.driver(uri, auth=(user, password))

            entities = {}
            relationships = []

            with driver.session() as session:
                # Get all node labels
                result = session.run("CALL db.labels() YIELD label RETURN label")
                labels = [record["label"] for record in result]

                # Get entities for each label
                for label in labels:
                    result = session.run(f"MATCH (n:{label}) RETURN n LIMIT 100")
                    entities[label] = [dict(record["n"].items()) for record in result]

                # Get all relationship types
                result = session.run(
                    "CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType"
                )
                rel_types = [record["relationshipType"] for record in result]

                # Get relationships
                for rel_type in rel_types:
                    result = session.run(
                        f"MATCH (a)-[r:{rel_type}]->(b) RETURN a, r, b LIMIT 100"
                    )
                    for record in result:
                        relationships.append(
                            {
                                "from": dict(record["a"].items()),
                                "relationship": rel_type,
                                "to": dict(record["b"].items()),
                                "properties": dict(record["r"].items()),
                            }
                        )

                # Get constraints
                result = session.run("CALL db.constraints() YIELD name RETURN name")
                constraints = [record["name"] for record in result]

                # Get indexes
                result = session.run("CALL db.indexes() YIELD name RETURN name")
                indexes = [record["name"] for record in result]

            driver.close()

            return DatabaseSnapshot(
                database_type="neo4j",
                connection_string=uri,
                entities=entities,
                relationships=relationships,
                constraints=constraints,
                indexes=indexes,
            )

        except ImportError:
            print("Warning: neo4j driver not installed. Skipping Neo4j snapshot.")
            return None
        except Exception as e:
            print(f"Warning: Could not capture Neo4j state: {e}")
            return None

    def _capture_sql_state(
        self, db_config: Dict[str, Any]
    ) -> Optional[DatabaseSnapshot]:
        """Capture SQL database state (PostgreSQL, MySQL, SQLite)."""
        try:
            import sqlalchemy as sa

            connection_string = db_config.get("connection")
            if not connection_string:
                return None

            engine = sa.create_engine(connection_string)

            entities = {}

            with engine.connect() as conn:
                # Get all tables
                result = conn.execute(
                    sa.text(
                        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
                    )
                )
                tables = [row[0] for row in result]

                # Get entities from each table
                for table in tables:
                    result = conn.execute(sa.text(f"SELECT * FROM {table} LIMIT 100"))
                    columns = result.keys()
                    entities[table] = [dict(zip(columns, row)) for row in result]

            return DatabaseSnapshot(
                database_type=db_config.get("type", "sql"),
                connection_string=connection_string,
                entities=entities,
            )

        except ImportError:
            print("Warning: sqlalchemy not installed. Skipping SQL snapshot.")
            return None
        except Exception as e:
            print(f"Warning: Could not capture SQL state: {e}")
            return None

    def _capture_mongodb_state(
        self, db_config: Dict[str, Any]
    ) -> Optional[DatabaseSnapshot]:
        """Capture MongoDB state."""
        try:
            from pymongo import MongoClient

            connection_string = db_config.get("connection", "mongodb://localhost:27017")
            database_name = db_config.get("database", "test")

            client = MongoClient(connection_string)
            db = client[database_name]

            entities = {}

            # Get all collections
            for collection_name in db.list_collection_names():
                collection = db[collection_name]
                entities[collection_name] = list(collection.find().limit(100))

            client.close()

            return DatabaseSnapshot(
                database_type="mongodb",
                connection_string=connection_string,
                entities=entities,
            )

        except ImportError:
            print("Warning: pymongo not installed. Skipping MongoDB snapshot.")
            return None
        except Exception as e:
            print(f"Warning: Could not capture MongoDB state: {e}")
            return None

    def compare_states(
        self,
        before: StateSnapshot,
        after: StateSnapshot,
    ) -> Dict[str, Any]:
        """Compare two states and identify differences."""
        differences = {
            "api_changes": [],
            "database_changes": [],
            "structural_changes": [],
        }

        # Compare API responses
        for before_api in before.api_snapshots:
            after_api = after.get_api_snapshot(before_api.endpoint, before_api.method)
            if after_api:
                api_diff = self._compare_api_snapshots(before_api, after_api)
                if api_diff:
                    differences["api_changes"].append(api_diff)

        # Compare database states
        for before_db in before.database_snapshots:
            after_db = self._find_database_snapshot(after, before_db.database_type)
            if after_db:
                db_diff = self._compare_database_snapshots(before_db, after_db)
                if db_diff:
                    differences["database_changes"].append(db_diff)

        return differences

    def _compare_api_snapshots(
        self, before: APISnapshot, after: APISnapshot
    ) -> Optional[Dict[str, Any]]:
        """Compare two API snapshots."""
        changes = {
            "endpoint": before.endpoint,
            "method": before.method,
            "status_changed": before.response_status != after.response_status,
            "body_changed": before.response_body != after.response_body,
            "performance_changed": abs(before.duration_ms - after.duration_ms) > 100,
            "before_status": before.response_status,
            "after_status": after.response_status,
            "before_duration_ms": before.duration_ms,
            "after_duration_ms": after.duration_ms,
        }

        if changes["body_changed"]:
            changes["body_diff"] = self._compute_json_diff(
                before.response_body, after.response_body
            )

        # Only return if there are changes
        if any(
            [
                changes["status_changed"],
                changes["body_changed"],
                changes["performance_changed"],
            ]
        ):
            return changes

        return None

    def _compare_database_snapshots(
        self, before: DatabaseSnapshot, after: DatabaseSnapshot
    ) -> Optional[Dict[str, Any]]:
        """Compare two database snapshots."""
        changes = {
            "database_type": before.database_type,
            "entity_changes": {},
            "relationship_changes": [],
            "schema_changes": [],
        }

        # Compare entities
        all_entities = set(before.entities.keys()) | set(after.entities.keys())
        for entity in all_entities:
            before_data = before.entities.get(entity, [])
            after_data = after.entities.get(entity, [])

            if before_data != after_data:
                changes["entity_changes"][entity] = {
                    "before_count": len(before_data),
                    "after_count": len(after_data),
                    "changed": len(before_data) != len(after_data),
                }

        # Compare relationships (for graph databases)
        if before.relationships != after.relationships:
            changes["relationship_changes"] = {
                "before_count": len(before.relationships),
                "after_count": len(after.relationships),
            }

        # Return only if there are changes
        if changes["entity_changes"] or changes["relationship_changes"]:
            return changes

        return None

    def _find_database_snapshot(
        self, snapshot: StateSnapshot, db_type: str
    ) -> Optional[DatabaseSnapshot]:
        """Find database snapshot by type."""
        for db_snapshot in snapshot.database_snapshots:
            if db_snapshot.database_type == db_type:
                return db_snapshot
        return None

    def _compute_json_diff(self, before: Dict, after: Dict) -> Dict[str, Any]:
        """Compute difference between two JSON objects."""
        diff = {
            "added": {},
            "removed": {},
            "modified": {},
        }

        all_keys = set(before.keys()) | set(after.keys())

        for key in all_keys:
            if key not in before:
                diff["added"][key] = after[key]
            elif key not in after:
                diff["removed"][key] = before[key]
            elif before[key] != after[key]:
                diff["modified"][key] = {
                    "before": before[key],
                    "after": after[key],
                }

        return diff

    def _generate_snapshot_id(self, prefix: str) -> str:
        """Generate unique snapshot ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        return f"{prefix}_{timestamp}_{unique_id}"

    def save_snapshot(self, snapshot: StateSnapshot, output_path: Path) -> None:
        """Save snapshot to disk."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "snapshot_id": snapshot.snapshot_id,
            "commit_hash": snapshot.commit_hash,
            "branch": snapshot.branch,
            "timestamp": snapshot.timestamp.isoformat(),
            "api_snapshots": [api.to_dict() for api in snapshot.api_snapshots],
            "database_snapshots": [db.to_dict() for db in snapshot.database_snapshots],
            "metadata": snapshot.metadata,
        }

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def load_snapshot(self, input_path: Path) -> StateSnapshot:
        """Load snapshot from disk."""
        with open(input_path) as f:
            data = json.load(f)

        # Reconstruct snapshot (simplified)
        return StateSnapshot(
            snapshot_id=data["snapshot_id"],
            commit_hash=data.get("commit_hash"),
            branch=data.get("branch"),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {}),
        )
