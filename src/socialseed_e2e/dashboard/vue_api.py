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
    """Serve the Vue app or fallback HTML."""
    vue_dist = Path(__file__).parent / "vue" / "dist"
    index_path = vue_dist / "index.html"

    if index_path.exists():
        return FileResponse(str(index_path))

    return HTMLResponse(content=FALLBACK_DASHBOARD_HTML)


FALLBACK_DASHBOARD_HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SocialSeed E2E Dashboard</title>
    <style>
        :root {
            --bg-primary: #1e1e1e;
            --bg-secondary: #252526;
            --bg-tertiary: #2d2d30;
            --bg-hover: #3c3c3c;
            --text-primary: #cccccc;
            --text-secondary: #858585;
            --accent: #f59e0b;
            --accent-hover: #d97706;
            --success: #22c55e;
            --error: #ef4444;
            --border: #3c3c3c;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif; background: var(--bg-primary); color: var(--text-primary); height: 100vh; overflow: hidden; }
        
        .app { display: flex; height: 100vh; }
        
        /* Sidebar */
        .sidebar { width: 260px; background: var(--bg-secondary); border-right: 1px solid var(--border); display: flex; flex-direction: column; }
        .sidebar-header { padding: 1rem; border-bottom: 1px solid var(--border); display: flex; align-items: center; gap: 0.5rem; }
        .logo { color: var(--accent); font-weight: 700; font-size: 1.1rem; }
        .version { background: var(--bg-tertiary); padding: 0.15rem 0.5rem; border-radius: 0.25rem; font-size: 0.7rem; color: var(--text-secondary); }
        
        .sidebar-actions { padding: 0.75rem; display: flex; gap: 0.5rem; }
        .btn-sm { padding: 0.4rem 0.75rem; background: var(--accent); color: white; border: none; border-radius: 0.25rem; cursor: pointer; font-size: 0.8rem; font-weight: 500; }
        .btn-sm:hover { background: var(--accent-hover); }
        .btn-sm.secondary { background: var(--bg-tertiary); }
        .btn-sm.secondary:hover { background: var(--bg-hover); }
        
        .search-box { padding: 0.5rem 0.75rem; }
        .search-box input { width: 100%; padding: 0.5rem; background: var(--bg-tertiary); border: 1px solid var(--border); border-radius: 0.25rem; color: var(--text-primary); font-size: 0.85rem; }
        .search-box input::placeholder { color: var(--text-secondary); }
        .search-box input:focus { outline: none; border-color: var(--accent); }
        
        .services-list { flex: 1; overflow-y: auto; }
        .service-item { border-bottom: 1px solid var(--border); }
        .service-header { padding: 0.6rem 0.75rem; display: flex; align-items: center; gap: 0.5rem; cursor: pointer; font-weight: 500; font-size: 0.85rem; }
        .service-header:hover { background: var(--bg-hover); }
        .service-icon { color: var(--accent); font-size: 0.9rem; }
        .service-count { margin-left: auto; background: var(--bg-tertiary); padding: 0.1rem 0.4rem; border-radius: 0.75rem; font-size: 0.7rem; color: var(--text-secondary); }
        
        .test-list { background: var(--bg-primary); }
        .test-item { padding: 0.5rem 1rem 0.5rem 2rem; display: flex; align-items: center; gap: 0.5rem; cursor: pointer; font-size: 0.8rem; }
        .test-item:hover { background: var(--bg-hover); }
        .test-item.active { background: var(--bg-tertiary); border-left: 2px solid var(--accent); }
        .test-icon { color: var(--text-secondary); }
        .sandbox-badge { background: #7c3aed; color: white; padding: 0.1rem 0.3rem; border-radius: 0.25rem; font-size: 0.6rem; margin-left: auto; }
        
        /* Main Panel */
        .main { flex: 1; display: flex; flex-direction: column; }
        
        .main-header { padding: 0.75rem 1rem; background: var(--bg-secondary); border-bottom: 1px solid var(--border); display: flex; align-items: center; justify-content: space-between; }
        .test-title { font-weight: 600; font-size: 0.95rem; display: flex; align-items: center; gap: 0.5rem; }
        .test-path { color: var(--text-secondary); font-size: 0.75rem; font-weight: normal; }
        
        .test-actions { display: flex; gap: 0.5rem; }
        .btn-run { background: var(--success); }
        .btn-run:hover { background: #16a34a; }
        .btn-duplicate { background: #7c3aed; }
        .btn-duplicate:hover { background: #6d28d9; }
        
        /* Request Panel */
        .request-panel { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
        .request-bar { padding: 0.75rem 1rem; background: var(--bg-tertiary); display: flex; gap: 0.5rem; align-items: center; }
        .method-select { padding: 0.4rem 0.6rem; background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 0.25rem; color: var(--success); font-weight: 600; font-size: 0.8rem; }
        .url-input { flex: 1; padding: 0.4rem 0.75rem; background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 0.25rem; color: var(--text-primary); font-size: 0.85rem; font-family: monospace; }
        .url-input:focus { outline: none; border-color: var(--accent); }
        
        /* Tabs */
        .tabs { display: flex; background: var(--bg-secondary); border-bottom: 1px solid var(--border); }
        .tab { padding: 0.6rem 1rem; cursor: pointer; font-size: 0.8rem; color: var(--text-secondary); border-bottom: 2px solid transparent; }
        .tab:hover { color: var(--text-primary); }
        .tab.active { color: var(--accent); border-bottom-color: var(--accent); }
        
        /* Content Area */
        .tab-content { flex: 1; overflow: auto; padding: 1rem; }
        .tab-panel { display: none; height: 100%; }
        .tab-panel.active { display: block; }
        
        textarea.code-editor { width: 100%; height: 200px; background: var(--bg-primary); border: 1px solid var(--border); border-radius: 0.25rem; color: var(--text-primary); font-family: 'Consolas', monospace; font-size: 0.85rem; padding: 0.75rem; resize: vertical; }
        
        /* Response */
        .response-panel { height: 200px; border-top: 1px solid var(--border); }
        .response-header { padding: 0.5rem 1rem; background: var(--bg-tertiary); display: flex; align-items: center; gap: 1rem; font-size: 0.8rem; }
        .status-badge { padding: 0.2rem 0.5rem; border-radius: 0.25rem; font-weight: 600; }
        .status-badge.success { background: rgba(34, 197, 94, 0.2); color: var(--success); }
        .status-badge.error { background: rgba(239, 68, 68, 0.2); color: var(--error); }
        .response-body { padding: 0.75rem 1rem; background: var(--bg-primary); height: calc(100% - 2.5rem); overflow: auto; font-family: monospace; font-size: 0.8rem; white-space: pre-wrap; }
        
        /* History Panel */
        .history-list { display: flex; flex-direction: column; gap: 0.5rem; }
        .history-item { padding: 0.75rem; background: var(--bg-tertiary); border-radius: 0.25rem; display: flex; align-items: center; gap: 0.75rem; }
        .history-time { font-size: 0.75rem; color: var(--text-secondary); min-width: 80px; }
        .history-method { font-size: 0.7rem; font-weight: 600; color: var(--success); min-width: 50px; }
        .history-name { flex: 1; font-size: 0.85rem; }
        
        /* Status Bar */
        .status-bar { padding: 0.4rem 1rem; background: var(--bg-secondary); border-top: 1px solid var(--border); font-size: 0.75rem; color: var(--text-secondary); display: flex; justify-content: space-between; }
        .sync-status { display: flex; align-items: center; gap: 0.5rem; }
        .sync-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--success); }
        
        /* Sandbox Indicator */
        .sandbox-indicator { background: #7c3aed; color: white; padding: 0.25rem 0.5rem; border-radius: 0.25rem; font-size: 0.7rem; display: flex; align-items: center; gap: 0.25rem; }
        
        .empty-state { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: var(--text-secondary); }
        .empty-state-icon { font-size: 3rem; margin-bottom: 1rem; opacity: 0.5; }
    </style>
</head>
<body>
    <div class="app">
        <!-- Sidebar -->
        <div class="sidebar">
            <div class="sidebar-header">
                <span class="logo">🌱</span>
                <span>SocialSeed</span>
                <span class="version">E2E</span>
            </div>
            
            <div class="sidebar-actions">
                <button class="btn-sm btn-run" onclick="runSelectedTest()">▶ Run</button>
                <button class="btn-sm btn-duplicate" onclick="duplicateTest()">📋 Copy</button>
                <button class="btn-sm secondary" onclick="refreshTests()">🔄</button>
            </div>
            
            <div class="search-box">
                <input type="text" id="searchInput" placeholder="Search tests..." onkeyup="filterTests()">
            </div>
            
            <div class="services-list" id="servicesList">
                Loading services...
            </div>
        </div>
        
        <!-- Main Panel -->
        <div class="main">
            <div class="main-header">
                <div class="test-title" id="testTitle">
                    Select a test
                    <span class="sandbox-indicator" id="sandboxBadge" style="display: none;">🧪 Sandbox</span>
                </div>
                <div class="test-actions">
                    <button class="btn-sm btn-run" onclick="runSelectedTest()">▶ Run</button>
                    <button class="btn-sm btn-duplicate" onclick="duplicateTest()">📋 Duplicate</button>
                </div>
            </div>
            
            <div class="request-panel">
                <div class="request-bar">
                    <select class="method-select" id="methodSelect">
                        <option value="GET">GET</option>
                        <option value="POST">POST</option>
                        <option value="PUT">PUT</option>
                        <option value="DELETE">DELETE</option>
                        <option value="PATCH">PATCH</option>
                    </select>
                    <input type="text" class="url-input" id="urlInput" placeholder="Enter URL or select a test" value="">
                </div>
                
                <div class="tabs">
                    <div class="tab active" onclick="switchTab('params')">Params</div>
                    <div class="tab" onclick="switchTab('headers')">Headers</div>
                    <div class="tab" onclick="switchTab('body')">Body</div>
                    <div class="tab" onclick="switchTab('tests')">Tests</div>
                </div>
                
                <div class="tab-content">
                    <div class="tab-panel active" id="panel-params">
                        <textarea class="code-editor" id="paramsEditor" placeholder='{"key": "value"}'></textarea>
                    </div>
                    <div class="tab-panel" id="panel-headers">
                        <textarea class="code-editor" id="headersEditor" placeholder='{"Content-Type": "application/json"}'></textarea>
                    </div>
                    <div class="tab-panel" id="panel-body">
                        <textarea class="code-editor" id="bodyEditor" placeholder='{"key": "value"}'></textarea>
                    </div>
                    <div class="tab-panel" id="panel-tests">
                        <textarea class="code-editor" id="testsEditor" placeholder="// Assertions\n// response.status === 200\n// response.json().token"></textarea>
                    </div>
                </div>
                
                <div class="response-panel">
                    <div class="response-header">
                        <span class="status-badge" id="statusBadge">--</span>
                        <span id="responseTime">-- ms</span>
                        <span id="responseSize">-- bytes</span>
                    </div>
                    <div class="response-body" id="responseBody">
                        Response will appear here...
                    </div>
                </div>
            </div>
            
            <div class="status-bar">
                <div class="sync-status">
                    <span class="sync-dot"></span>
                    <span>Watching for changes</span>
                </div>
                <span id="lastSync">Last sync: --</span>
            </div>
        </div>
    </div>

    <script>
        let services = {};
        let tests = [];
        let selectedTest = null;
        let sandboxTests = {};
        let lastModified = {};
        
        async function loadData() {
            try {
                const res = await fetch('/api/tests');
                const data = await res.json();
                services = data.services || [];
                tests = data.tests || [];
                
                // Group tests by service
                const servicesMap = {};
                services.forEach(s => {
                    servicesMap[s.name] = tests.filter(t => t.service === s.name);
                });
                renderServices();
                updateSyncStatus();
            } catch(e) {
                console.error('Error loading:', e);
            }
        }
        
        function renderServices() {
            const container = document.getElementById('servicesList');
            const search = document.getElementById('searchInput').value.toLowerCase();
            
            let html = '';
            
            // Regular tests
            for (const [serviceName, serviceTests] of Object.entries(servicesMap)) {
                const filteredTests = serviceTests.filter(t => t.name.toLowerCase().includes(search));
                if (filteredTests.length === 0 && search) continue;
                
                html += \`
                    <div class="service-item">
                        <div class="service-header" onclick="toggleService('\${serviceName}')">
                            <span class="service-icon">📁</span>
                            <span>\${serviceName}</span>
                            <span class="service-count">\${filteredTests.length}</span>
                        </div>
                        <div class="test-list" id="service-\${serviceName}">
                            \${filteredTests.map(t => \`
                                <div class="test-item \${selectedTest?.path === t.path ? 'active' : ''}" 
                                     onclick="selectTest('\${t.path}', '\${t.name}', '\${serviceName}', false)">
                                    <span class="test-icon">🧪</span>
                                    <span>\${t.name}</span>
                                </div>
                            \`).join('')}
                        </div>
                    </div>
                \`;
            }
            
            // Sandbox tests
            const sandboxNames = Object.keys(sandboxTests);
            if (sandboxNames.length > 0) {
                html += \`
                    <div class="service-item">
                        <div class="service-header">
                            <span class="service-icon">🧪</span>
                            <span>Sandbox (Copies)</span>
                            <span class="service-count">\${sandboxNames.length}</span>
                        </div>
                        <div class="test-list">
                            \${sandboxNames.map(name => \`
                                <div class="test-item \${selectedTest?.sandbox === name ? 'active' : ''}"
                                     onclick="selectSandboxTest('\${name}')">
                                    <span class="test-icon">📋</span>
                                    <span>\${name}</span>
                                    <span class="sandbox-badge">COPY</span>
                                </div>
                            \`).join('')}
                        </div>
                    </div>
                \`;
            }
            
            if (!html) html = '<div style="padding:1rem;color:var(--text-secondary)">No tests found</div>';
            container.innerHTML = html;
        }
        
        function selectTest(path, name, service, isSandbox) {
            selectedTest = { path, name, service, sandbox: isSandbox ? name : null };
            document.getElementById('testTitle').innerHTML = \`
                \${name}
                <span class="test-path">\${service} / \${path}</span>
                \${isSandbox ? '<span class="sandbox-indicator">🧪 Sandbox</span>' : ''}
            \`;
            
            document.getElementById('urlInput').value = \`http://localhost:5000\${path.replace('modules/', '/').replace('.py', '')}\`;
            
            // Load test content
            loadTestContent(path, isSandbox ? null : path);
            renderServices();
        }
        
        function selectSandboxTest(name) {
            const sandbox = sandboxTests[name];
            if (sandbox) {
                selectedTest = { name, service: 'sandbox', sandbox: name };
                document.getElementById('testTitle').innerHTML = \`
                    \${name}
                    <span class="test-path">Sandbox Copy</span>
                    <span class="sandbox-indicator">🧪 Sandbox</span>
                \`;
                document.getElementById('urlInput').value = sandbox.url || '';
                document.getElementById('bodyEditor').value = sandbox.body || '';
                document.getElementById('paramsEditor').value = sandbox.params || '';
                document.getElementById('headersEditor').value = sandbox.headers || '';
                document.getElementById('testsEditor').value = sandbox.tests || '';
            }
        }
        
        async function loadTestContent(path, originalPath) {
            try {
                const res = await fetch('/api/test-content?path=' + encodeURIComponent(path));
                const data = await res.json();
                
                if (data.content) {
                    // Extract URL and params from test content
                    const urlMatch = data.content.match(/["'](https?:\/\/[^"']+)["']/);
                    const bodyMatch = data.content.match(/json\s*=\s*(\{[^}]+\})/s);
                    
                    if (urlMatch) document.getElementById('urlInput').value = urlMatch[1];
                    if (bodyMatch) document.getElementById('bodyEditor').value = bodyMatch[1];
                }
            } catch(e) {
                console.error('Error loading test:', e);
            }
        }
        
        function duplicateTest() {
            if (!selectedTest) {
                alert('Select a test first');
                return;
            }
            
            const copyName = selectedTest.sandbox || selectedTest.name + ' (Copy)';
            sandboxTests[copyName] = {
                url: document.getElementById('urlInput').value,
                body: document.getElementById('bodyEditor').value,
                params: document.getElementById('paramsEditor').value,
                headers: document.getElementById('headersEditor').value,
                tests: document.getElementById('testsEditor').value,
                original: selectedTest.path
            };
            
            selectedTest = { name: copyName, service: 'sandbox', sandbox: copyName };
            renderServices();
            alert('Test duplicated to Sandbox! You can modify it without affecting the original.');
        }
        
        function runSelectedTest() {
            if (!selectedTest) {
                alert('Select a test first');
                return;
            }
            
            const url = document.getElementById('urlInput').value;
            const method = document.getElementById('methodSelect').value;
            const body = document.getElementById('bodyEditor').value;
            
            const statusBadge = document.getElementById('statusBadge');
            statusBadge.textContent = 'Running...';
            statusBadge.className = 'status-badge';
            
            const startTime = Date.now();
            
            fetch('/api/test-run', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    url,
                    method,
                    body: body ? JSON.parse(body) : null,
                    isSandbox: !!selectedTest.sandbox,
                    testName: selectedTest.name
                })
            })
            .then(res => res.json())
            .then(data => {
                const duration = Date.now() - startTime;
                document.getElementById('responseTime').textContent = duration + ' ms';
                document.getElementById('responseSize').textContent = JSON.stringify(data).length + ' bytes';
                
                if (data.status >= 200 && data.status < 300) {
                    statusBadge.textContent = data.status + ' OK';
                    statusBadge.className = 'status-badge success';
                } else {
                    statusBadge.textContent = data.status + ' Error';
                    statusBadge.className = 'status-badge error';
                }
                
                document.getElementById('responseBody').textContent = JSON.stringify(data, null, 2);
            })
            .catch(err => {
                statusBadge.textContent = 'Error';
                statusBadge.className = 'status-badge error';
                document.getElementById('responseBody').textContent = 'Error: ' + err.message;
            });
        }
        
        function switchTab(tabName) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
            
            event.target.classList.add('active');
            document.getElementById('panel-' + tabName).classList.add('active');
        }
        
        function filterTests() {
            renderServices();
        }
        
        function toggleService(name) {
            const el = document.getElementById('service-' + name);
            el.style.display = el.style.display === 'none' ? 'block' : 'none';
        }
        
        function refreshTests() {
            loadData();
        }
        
        function updateSyncStatus() {
            document.getElementById('lastSync').textContent = 'Last sync: ' + new Date().toLocaleTimeString();
        }
        
        // Auto-refresh every 5 seconds
        setInterval(loadData, 5000);
        
        // Initial load
        loadData();
    </script>
</body>
</html>
"""


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


@app.get("/api/test-content")
async def get_test_content(path: str) -> Dict[str, Any]:
    """Get test file content."""
    test_path = PROJECT_ROOT / "services" / path

    if test_path.exists():
        content = test_path.read_text()
        return {"content": content, "path": str(test_path)}

    return {"error": "Test not found", "path": path}


@app.post("/api/test-run")
async def run_test_request(data: Dict[str, Any]) -> Dict[str, Any]:
    """Run a test request (for dashboard testing)."""
    import requests as req

    url = data.get("url", "")
    method = data.get("method", "GET")
    body = data.get("body")
    is_sandbox = data.get("isSandbox", False)
    test_name = data.get("testName", "ad-hoc")

    try:
        kwargs = {"timeout": 30}
        if body and method in ["POST", "PUT", "PATCH"]:
            kwargs["json"] = body

        response = req.request(method, url, **kwargs)

        result = {
            "status": response.status_code,
            "headers": dict(response.headers),
            "body": response.json()
            if response.headers.get("content-type", "").startswith("application/json")
            else response.text,
            "test_name": test_name,
            "sandbox": is_sandbox,
            "timestamp": datetime.now().isoformat(),
        }

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO test_runs (timestamp, test_name, test_path, status, duration_ms)
               VALUES (?, ?, ?, ?, ?)""",
            (
                result["timestamp"],
                test_name,
                url,
                "passed" if response.status_code < 400 else "failed",
                0,
            ),
        )
        conn.commit()
        conn.close()

        return result

    except Exception as e:
        return {
            "status": 0,
            "error": str(e),
            "test_name": test_name,
            "sandbox": is_sandbox,
            "timestamp": datetime.now().isoformat(),
        }


class TestFileWatcher:
    """Watch for changes in test files."""

    def __init__(self):
        self.last_modified = {}

    def get_file_hash(self, path: Path) -> float:
        if path.exists():
            return path.stat().st_mtime
        return 0

    def check_changes(self) -> List[str]:
        """Check for modified test files."""
        changes = []
        services_path = PROJECT_ROOT / "services"

        if not services_path.exists():
            return changes

        for module_file in services_path.rglob("modules/*.py"):
            if module_file.name.startswith("_"):
                continue

            current_hash = self.get_file_hash(module_file)
            last_hash = self.last_modified.get(str(module_file), 0)

            if current_hash != last_hash:
                changes.append(str(module_file.relative_to(PROJECT_ROOT)))
                self.last_modified[str(module_file)] = current_hash

        return changes


test_watcher = TestFileWatcher()


@app.get("/api/watch-status")
async def get_watch_status() -> Dict[str, Any]:
    """Get file watcher status and check for changes."""
    changes = test_watcher.check_changes()
    return {
        "watching": True,
        "changes": changes,
        "last_check": datetime.now().isoformat(),
    }


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


def run_server(
    host: str = "localhost", port: int = 5173, open_browser: bool = True
) -> None:
    """Run the Vue dashboard server."""
    import uvicorn

    url = f"http://{host}:{port}"

    print("=" * 60)
    print("🚀 SocialSeed E2E Dashboard (Vue.js)")
    print("=" * 60)
    print(f"\n📍 Dashboard URL: {url}")
    print("\nPress Ctrl+C to stop")
    print("=" * 60)

    if open_browser:
        import webbrowser

        webbrowser.open(url)

    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("🚀 SocialSeed E2E Dashboard (Vue.js)")
    print("=" * 60)
    print("\n📍 API URL: http://localhost:8000")
    print("\nPress Ctrl+C")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000)
