"""Vue Dashboard Backend - FastAPI Server

This module provides the backend API for the Vue.js dashboard,
replacing the old Streamlit interface with a modern reactive frontend.
"""

import asyncio
import json
import os
import sys
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import socketio
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

# Initialize FastAPI app
app = FastAPI(title="SocialSeed E2E Dashboard API", version="2.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Socket.IO server for real-time updates
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins=["*"])
socket_app = socketio.ASGIApp(sio)

# Project root
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

    conn.commit()
    conn.close()


# Initialize DB on startup
init_db()


# ==================== API Routes ====================


@app.get("/")
async def root():
    """Serve the Vue app."""
    vue_dist = Path(__file__).parent / "vue" / "dist"
    index_path = vue_dist / "index.html"

    if index_path.exists():
        return FileResponse(str(index_path))

    return HTMLResponse(
        content="""
        <html>
            <head><title>SocialSeed E2E Dashboard</title></head>
            <body>
                <h1>SocialSeed E2E Dashboard</h1>
                <p>Vue dashboard files not found. Run 'npm run build' in dashboard/vue/</p>
            </body>
        </html>
    """
    )


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "dashboard-api", "version": "2.0.0"}


@app.get("/api/tests")
async def get_tests() -> Dict[str, Any]:
    """Get all available tests."""
    services = {}
    tests = []

    services_path = PROJECT_ROOT / "services"

    if services_path.exists():
        for service_dir in services_path.iterdir():
            if service_dir.is_dir() and (service_dir / "modules").exists():
                service_name = service_dir.name
                modules_path = service_dir / "modules"

                test_count = 0
                for module_file in modules_path.glob("*.py"):
                    if (
                        module_file.name.startswith("0")
                        and module_file.name != "__init__.py"
                    ):
                        test_count += 1
                        tests.append(
                            {
                                "name": module_file.stem,
                                "path": str(module_file.relative_to(PROJECT_ROOT)),
                                "service": service_name,
                                "type": "module",
                            }
                        )

                if test_count > 0:
                    services[service_name] = {
                        "name": service_name,
                        "test_count": test_count,
                        "path": str(service_dir.relative_to(PROJECT_ROOT)),
                    }

    return {"services": list(services.values()), "tests": tests}


@app.post("/api/tests/run")
async def run_test(data: Dict[str, Any]) -> Dict[str, Any]:
    """Run a specific test."""
    test_path = data.get("test_path")
    params = data.get("params", {})

    if not test_path:
        raise HTTPException(status_code=400, detail="test_path is required")

    start_time = datetime.now()

    # Emit start event
    await sio.emit("test_start", {"test_path": test_path})

    try:
        # Import and run the test
        sys.path.insert(0, str(PROJECT_ROOT))

        module_path = PROJECT_ROOT / test_path
        module_name = f"services.{module_path.parent.name}.modules.{module_path.stem}"

        spec = __import__(module_name, fromlist=["run"])

        # Create a mock page object
        class MockPage:
            def __init__(self, base_url="http://localhost:8000"):
                self.base_url = base_url
                self.last_request = {}
                self.last_response = None

            def get(self, path, **kwargs):
                self.last_request = {"method": "GET", "path": path, **kwargs}
                return MockResponse(200, {"message": "OK"})

            def post(self, path, **kwargs):
                self.last_request = {"method": "POST", "path": path, **kwargs}
                return MockResponse(200, {"message": "Created"})

            def put(self, path, **kwargs):
                self.last_request = {"method": "PUT", "path": path, **kwargs}
                return MockResponse(200, {"message": "Updated"})

            def delete(self, path, **kwargs):
                self.last_request = {"method": "DELETE", "path": path, **kwargs}
                return MockResponse(200, {"message": "Deleted"})

        class MockResponse:
            def __init__(self, status, json_data):
                self.status = status
                self._json_data = json_data

            def json(self):
                return self._json_data

        page = MockPage()

        # Run the test
        result = spec.run(page)

        end_time = datetime.now()
        duration = int((end_time - start_time).total_seconds() * 1000)

        test_result = {
            "id": f"run_{int(start_time.timestamp())}",
            "test_name": module_path.stem,
            "test_path": test_path,
            "status": "passed",
            "duration": duration,
            "timestamp": start_time.isoformat(),
            "output": "Test executed successfully",
        }

        # Save to database
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO test_runs (timestamp, test_name, test_path, status, duration_ms, output)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                test_result["timestamp"],
                test_result["test_name"],
                test_path,
                test_result["status"],
                test_result["duration"],
                test_result["output"],
            ),
        )
        conn.commit()
        conn.close()

        # Emit result via WebSocket
        await sio.emit("test_result", {"result": test_result})

        return {"result": test_result}

    except Exception as e:
        end_time = datetime.now()
        duration = int((end_time - start_time).total_seconds() * 1000)

        test_result = {
            "id": f"run_{int(start_time.timestamp())}",
            "test_name": Path(test_path).stem,
            "test_path": test_path,
            "status": "failed",
            "duration": duration,
            "timestamp": start_time.isoformat(),
            "error": str(e),
        }

        # Save failed result
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO test_runs (timestamp, test_name, test_path, status, duration_ms, error_message)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                test_result["timestamp"],
                test_result["test_name"],
                test_path,
                test_result["status"],
                test_result["duration"],
                str(e),
            ),
        )
        conn.commit()
        conn.close()

        await sio.emit("test_result", {"result": test_result})

        return {"result": test_result}


@app.get("/api/tests/history")
async def get_history(limit: int = 20) -> List[Dict[str, Any]]:
    """Get test run history."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT * FROM test_runs 
        ORDER BY timestamp DESC 
        LIMIT ?
    """,
        (limit,),
    )

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


@app.get("/api/config")
async def get_config() -> Dict[str, Any]:
    """Get current configuration."""
    config_path = PROJECT_ROOT / "e2e.conf"

    if config_path.exists():
        content = config_path.read_text()
        return {"config": content, "path": str(config_path)}

    return {"config": None, "path": str(config_path)}


# ==================== WebSocket Events ====================


@sio.event
async def connect(sid, environ):
    """Handle client connection."""
    print(f"Client connected: {sid}")
    await sio.emit("connected", {"sid": sid})


@sio.event
async def disconnect(sid):
    """Handle client disconnection."""
    print(f"Client disconnected: {sid}")


@sio.event
async def run_all_tests(sid, data):
    """Run all tests."""
    service = data.get("service")

    # Get tests
    tests_data = await get_tests()
    tests = tests_data.get("tests", [])

    if service:
        tests = [t for t in tests if t.get("service") == service]

    for i, test in enumerate(tests):
        await sio.emit(
            "test_progress",
            {"current": i + 1, "total": len(tests), "test": test["name"]},
        )

        result = await run_test({"test_path": test["path"]})

        await asyncio.sleep(0.1)

    await sio.emit("all_tests_complete", {"total": len(tests)})


# Mount Socket.IO app
app.mount("/ws", socket_app)


if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("🚀 SocialSeed E2E Dashboard (Vue.js)")
    print("=" * 60)
    print("\n📍 API URL: http://localhost:8000")
    print("\nPress Ctrl+C")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000)
