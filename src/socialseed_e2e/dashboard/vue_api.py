"""Vue Dashboard Backend - FastAPI Server

This module provides the backend API for the Vue.js dashboard,
replacing the old Streamlit interface with a modern reactive frontend.
"""

import asyncio
import json
import os
import re
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

from socialseed_e2e.dashboard.models import (
    Environment,
    RequestHistory,
    Collection,
    SavedRequest,
)

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
        [data-theme="light"] {
            --bg-primary: #ffffff;
            --bg-secondary: #f5f5f5;
            --bg-tertiary: #e5e5e5;
            --bg-hover: #e0e0e0;
            --text-primary: #333333;
            --text-secondary: #666666;
            --accent: #f59e0b;
            --accent-hover: #d97706;
            --border: #e0e0e0;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif; background: var(--bg-primary); color: var(--text-primary); height: 100vh; overflow: hidden; }
        
        .app { display: flex; height: 100vh; }
        
        /* Sidebar */
        .sidebar { width: 260px; background: var(--bg-secondary); border-right: 1px solid var(--border); display: flex; flex-direction: column; }
        .sidebar-header { padding: 1rem; border-bottom: 1px solid var(--border); display: flex; align-items: center; gap: 0.5rem; }
        .logo { color: var(--accent); font-weight: 700; font-size: 1.1rem; }
        .version { background: var(--bg-tertiary); padding: 0.15rem 0.5rem; border-radius: 0.25rem; font-size: 0.7rem; color: var(--text-secondary); }
        .env-select { flex: 1; padding: 0.3rem 0.5rem; background: var(--bg-tertiary); border: 1px solid var(--border); border-radius: 0.25rem; color: var(--text-primary); font-size: 0.75rem; cursor: pointer; }
        .env-select:focus { outline: none; border-color: var(--accent); }
        
        /* Modal */
        .modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.7); display: none; align-items: center; justify-content: center; z-index: 1000; }
        .modal-overlay.active { display: flex; }
        .modal { background: var(--bg-secondary); border-radius: 0.5rem; width: 90%; max-width: 500px; max-height: 80vh; overflow: auto; }
        .modal-header { padding: 1rem; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; }
        .modal-header h3 { margin: 0; font-size: 1rem; }
        .modal-body { padding: 1rem; }
        .modal-footer { padding: 1rem; border-top: 1px solid var(--border); display: flex; gap: 0.5rem; justify-content: flex-end; }
        .close-btn { background: none; border: none; color: var(--text-secondary); font-size: 1.5rem; cursor: pointer; }
        
        .env-list { display: flex; flex-direction: column; gap: 0.5rem; }
        .env-item { display: flex; align-items: center; gap: 0.5rem; padding: 0.75rem; background: var(--bg-tertiary); border-radius: 0.25rem; }
        .env-item-name { flex: 1; font-weight: 500; }
        .env-item.active { border: 1px solid var(--accent); }
        .env-var-list { margin-top: 0.5rem; padding-left: 1rem; }
        .env-var-item { display: flex; gap: 0.5rem; margin-bottom: 0.25rem; }
        .env-var-item input { flex: 1; padding: 0.3rem; background: var(--bg-primary); border: 1px solid var(--border); border-radius: 0.25rem; color: var(--text-primary); font-size: 0.8rem; }
        .var-key { width: 30%; }
        .var-value { flex: 1; }
        .btn-icon { background: none; border: none; color: var(--text-secondary); cursor: pointer; padding: 0.25rem; }
        .btn-icon:hover { color: var(--text-primary); }
        .add-var-btn { font-size: 0.75rem; padding: 0.3rem 0.5rem; }
        
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
                <select class="env-select" id="envSelect" onchange="switchEnvironment()">
                    <option value="">No Environment</option>
                </select>
                <button class="btn-sm secondary" onclick="openEnvModal()" title="Manage Environments">⚙️</button>
                <button class="btn-sm secondary" onclick="toggleTheme()" title="Toggle Theme" id="themeToggle">🌙</button>
            </div>
            
            <div class="sidebar-actions">
                <button class="btn-sm btn-run" onclick="runSelectedTest()">▶ Run</button>
                <button class="btn-sm btn-duplicate" onclick="duplicateTest()">📋 Copy</button>
                <button class="btn-sm secondary" onclick="refreshTests()">🔄</button>
                <button class="btn-sm secondary" onclick="openImportModal()">📥 Import</button>
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
                    <select class="method-select" id="methodSelect" onchange="handleMethodChange()">
                        <option value="GET">GET</option>
                        <option value="POST">POST</option>
                        <option value="PUT">PUT</option>
                        <option value="DELETE">DELETE</option>
                        <option value="PATCH">PATCH</option>
                        <option value="WS">WebSocket</option>
                    </select>
                    <input type="text" class="url-input" id="urlInput" placeholder="Enter URL or select a test" value="">
                    <button class="btn-sm btn-run" id="wsConnectBtn" onclick="toggleWebSocket()" style="display:none;">Connect</button>
                </div>
                
                <div class="tabs">
                    <div class="tab active" onclick="switchTab('params')">Params</div>
                    <div class="tab" onclick="switchTab('headers')">Headers</div>
                    <div class="tab" onclick="switchTab('body')">Body</div>
                    <div class="tab" onclick="switchTab('tests')">Tests</div>
                    <div class="tab" onclick="switchTab('history')">History</div>
                    <div class="tab" id="wsTab" onclick="switchTab('ws')" style="display:none;">WebSocket</div>
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
                    <div class="tab-panel" id="panel-history">
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;">
                            <input type="text" id="historySearch" placeholder="Search history..." 
                                   style="flex:1;padding:0.5rem;background:var(--bg-tertiary);border:1px solid var(--border);border-radius:0.25rem);color:var(--text-primary);"
                                   onkeyup="filterHistory()">
                            <button class="btn-sm secondary" onclick="clearHistory()" style="margin-left:0.5rem;">Clear</button>
                            <button class="btn-sm secondary" onclick="compareSelected()" style="margin-left:0.5rem;" id="compareBtn" disabled>Compare</button>
                        </div>
                        <div class="history-list" id="historyListContent">
                            <p style="color:var(--text-secondary)">No history yet. Run some requests.</p>
                        </div>
                    </div>
                    <div class="tab-panel" id="panel-ws">
                        <div style="margin-bottom:1rem;">
                            <button class="btn-sm btn-run" id="wsSendBtn" onclick="sendWsMessage()" disabled>Send</button>
                            <input type="text" id="wsMessageInput" placeholder="Enter message..." 
                                   style="flex:1;padding:0.5rem;background:var(--bg-tertiary);border:1px solid var(--border);border-radius:0.25rem;color:var(--text-primary);margin-left:0.5rem;">
                        </div>
                        <div class="ws-messages" id="wsMessages" style="height:200px;overflow-y:auto;background:var(--bg-tertiary);border-radius:0.25rem;padding:0.5rem;font-family:monospace;font-size:0.85rem;">
                            <p style="color:var(--text-secondary)">WebSocket messages will appear here...</p>
                        </div>
                    </div>
                </div>
                
                <div class="response-panel">
                    <div class="response-header">
                        <span class="status-badge" id="statusBadge">--</span>
                        <span id="responseTime">-- ms</span>
                        <span id="responseSize">-- bytes</span>
                        <div style="margin-left:auto;display:flex;gap:0.5rem;">
                            <button class="btn-sm secondary" onclick="setResponseView('raw')" id="viewRaw">Raw</button>
                            <button class="btn-sm secondary" onclick="setResponseView('pretty')" id="viewPretty">Pretty</button>
                            <button class="btn-sm secondary" onclick="setResponseView('preview')" id="viewPreview">Preview</button>
                        </div>
                    </div>
                    <div class="response-body" id="responseBody">
                        Response will appear here...
                    </div>
                    <div class="response-body" id="responsePreview" style="display:none;height:300px;background:white;">
                        <iframe id="previewFrame" style="width:100%;height:100%;border:none;"></iframe>
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
            
            // Substitute variables
            const rawUrl = document.getElementById('urlInput').value;
            const url = substituteVars(rawUrl);
            const method = document.getElementById('methodSelect').value;
            const rawBody = document.getElementById('bodyEditor').value;
            const body = substituteVars(rawBody);
            
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
                    testName: selectedTest.name,
                    substituted: rawUrl !== url || rawBody !== body
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
                
                const responseBody = document.getElementById('responseBody');
                const bodyText = typeof data.body === 'object' ? JSON.stringify(data.body) : data.body;
                currentResponseData = bodyText;
                responseBody.dataset.contentType = data.headers?.['Content-Type'] || '';
                responseBody.textContent = bodyText;
                setResponseView(currentResponseView);
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
        
        let requestHistory = [];
        
        async function loadHistory() {
            try {
                const res = await fetch('/api/history');
                const data = await res.json();
                requestHistory = data.history || [];
                renderHistory();
            } catch(e) {
                console.error('Error loading history:', e);
            }
        }
        
        function renderHistory() {
            const search = document.getElementById('historySearch')?.value?.toLowerCase() || '';
            const container = document.getElementById('historyListContent');
            
            const filtered = requestHistory.filter(h => 
                h.url.toLowerCase().includes(search) ||
                h.method.toLowerCase().includes(search)
            );
            
            if (filtered.length === 0) {
                container.innerHTML = '<p style="color:var(--text-secondary)">No history found</p>';
                return;
            }
            
            container.innerHTML = filtered.map(h => `
                <div class="history-item" style="display:flex;align-items:center;gap:0.5rem;padding:0.5rem;border-bottom:1px solid var(--border);cursor:pointer;">
                    <input type="checkbox" class="history-checkbox" value="${h.id}" onchange="updateCompareButton()" onclick="event.stopPropagation()">
                    <span class="history-time" style="font-size:0.7rem;color:var(--text-secondary)">${new Date(h.timestamp).toLocaleTimeString()}</span>
                    <span class="history-method" style="color:${h.response_status < 400 ? 'var(--success)' : 'var(--error)'};font-size:0.75rem;">${h.method}</span>
                    <span class="history-name" style="flex:1;font-size:0.8rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${h.url}</span>
                    <span style="color:var(--text-secondary);font-size:0.75rem;">${h.response_status || '--'}</span>
                </div>
            `).join('');
        }
        
        let selectedForCompare = [];
        
        function updateCompareButton() {
            const checkboxes = document.querySelectorAll('.history-checkbox:checked');
            selectedForCompare = Array.from(checkboxes).map(c => parseInt(c.value));
            const btn = document.getElementById('compareBtn');
            btn.disabled = selectedForCompare.length !== 2;
        }
        
        function compareSelected() {
            if (selectedForCompare.length !== 2) return;
            
            const item1 = requestHistory.find(h => h.id === selectedForCompare[0]);
            const item2 = requestHistory.find(h => h.id === selectedForCompare[1]);
            
            if (!item1 || !item2) return;
            
            document.getElementById('compare1').innerHTML = formatHistoryItem(item1);
            document.getElementById('compare2').innerHTML = formatHistoryItem(item2);
            
            const diff = computeDiff(item1, item2);
            document.getElementById('compareDiff').innerHTML = diff;
            
            document.getElementById('compareModal').classList.add('active');
        }
        
        function formatHistoryItem(item) {
            return `
                <div><strong>${item.method}</strong> ${item.url}</div>
                <div style="color:var(--text-secondary);margin-top:0.5rem;">Status: ${item.response_status || '--'}</div>
                <div style="margin-top:0.5rem;"><pre style="margin:0;white-space:pre-wrap;">${item.response_body?.substring(0, 500) || ''}</pre></div>
            `;
        }
        
        function computeDiff(item1, item2) {
            let diff = [];
            
            if (item1.method !== item2.method) {
                diff.push(`<div style="color:var(--error)">Method: ${item1.method} → ${item2.method}</div>`);
            }
            if (item1.url !== item2.url) {
                diff.push(`<div style="color:var(--error)">URL changed</div>`);
            }
            if (item1.response_status !== item2.response_status) {
                diff.push(`<div style="color:var(--error)">Status: ${item1.response_status} → ${item2.response_status}</div>`);
            }
            
            const body1 = item1.response_body || '';
            const body2 = item2.response_body || '';
            if (body1 !== body2) {
                diff.push(`<div style="color:var(--accent)">Response body differs</div>`);
            }
            
            if (diff.length === 0) {
                return '<div style="color:var(--success)">No differences found</div>';
            }
            
            return diff.join('');
        }
        
        function closeCompareModal() {
            document.getElementById('compareModal').classList.remove('active');
        }
        
        function filterHistory() {
            renderHistory();
        }
            
            container.innerHTML = filtered.map(h => \`
                <div class="history-item" onclick="restoreFromHistory(\${h.id})" style="cursor:pointer;">
                    <span class="history-time">\${new Date(h.timestamp).toLocaleTimeString()}</span>
                    <span class="history-method" style="color:\${h.response_status < 400 ? 'var(--success)' : 'var(--error)'}">\${h.method}</span>
                    <span class="history-name">\${h.url}</span>
                    <span style="color:var(--text-secondary);font-size:0.75rem;">\${h.response_status || '--'}</span>
                </div>
            \`).join('');
        }
        
        function filterHistory() {
            renderHistory();
        }
        
        function restoreFromHistory(id) {
            const item = requestHistory.find(h => h.id === id);
            if (item) {
                document.getElementById('methodSelect').value = item.method;
                document.getElementById('urlInput').value = item.url;
                document.getElementById('bodyEditor').value = item.body || '';
                switchTab('params');
                alert('Request restored from history');
            }
        }
        
        async function clearHistory() {
            if (!confirm('Clear all history?')) return;
            try {
                await fetch('/api/history', {method: 'DELETE'});
                requestHistory = [];
                renderHistory();
            } catch(e) {
                console.error('Error clearing history:', e);
            }
        }
        
        // Load history when switching to history tab
        const originalSwitchTab = switchTab;
        switchTab = function(tabName) {
            if (tabName === 'history') {
                loadHistory();
            }
            originalSwitchTab(tabName);
        };
        
        // Auto-refresh every 5 seconds
        setInterval(loadData, 5000);
        
        // Initial load
        loadData();
        loadEnvironments();
        loadTheme();
        
        // Environment functions
        let currentEnvironments = [];
        let activeEnvVars = {};
        
        async function loadEnvironments() {
            try {
                const res = await fetch('/api/environments');
                const data = await res.json();
                currentEnvironments = data.environments || [];
                const select = document.getElementById('envSelect');
                select.innerHTML = '<option value="">No Environment</option>';
                currentEnvironments.forEach(env => {
                    const opt = document.createElement('option');
                    opt.value = env.id;
                    opt.textContent = env.name + (env.is_active ? ' ✓' : '');
                    if (env.is_active) {
                        activeEnvVars = env.variables || {};
                        opt.selected = true;
                    }
                    select.appendChild(opt);
                });
            } catch(e) {
                console.error('Error loading environments:', e);
            }
        }
        
        function switchEnvironment() {
            const select = document.getElementById('envSelect');
            const envId = select.value;
            if (!envId) {
                activeEnvVars = {};
                return;
            }
            const env = currentEnvironments.find(e => e.id == envId);
            if (env) {
                activeEnvVars = env.variables || {};
            }
        }
        
        function openEnvModal() {
            document.getElementById('envModal').classList.add('active');
            renderEnvList();
        }
        
        function closeEnvModal() {
            document.getElementById('envModal').classList.remove('active');
        }
        
        function toggleTheme() {
            const html = document.documentElement;
            const current = html.getAttribute('data-theme');
            const toggle = document.getElementById('themeToggle');
            
            if (current === 'light') {
                html.removeAttribute('data-theme');
                localStorage.setItem('theme', 'dark');
                toggle.textContent = '🌙';
            } else {
                html.setAttribute('data-theme', 'light');
                localStorage.setItem('theme', 'light');
                toggle.textContent = '☀️';
            }
        }
        
        function loadTheme() {
            const saved = localStorage.getItem('theme');
            const toggle = document.getElementById('themeToggle');
            if (saved === 'light') {
                document.documentElement.setAttribute('data-theme', 'light');
                toggle.textContent = '☀️';
            }
        }
        
        // Keyboard shortcuts
        document.addEventListener('keydown', function(e) {
            // Ctrl/Cmd + Enter - Send request
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                e.preventDefault();
                runSelectedTest();
            }
            // Ctrl/Cmd + N - New request
            if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
                e.preventDefault();
                newRequest();
            }
            // Ctrl/Cmd + S - Save request
            if ((e.ctrlKey || e.metaKey) && e.key === 's') {
                e.preventDefault();
                saveCurrentRequest();
            }
            // Ctrl/Cmd + D - Duplicate request
            if ((e.ctrlKey || e.metaKey) && e.key === 'd') {
                e.preventDefault();
                duplicateTest();
            }
            // Escape - Close modals
            if (e.key === 'Escape') {
                document.querySelectorAll('.modal-overlay.active').forEach(m => m.classList.remove('active'));
            }
        });
        
        function newRequest() {
            document.getElementById('requestName').value = 'New Request';
            document.getElementById('requestMethod').value = 'GET';
            document.getElementById('requestUrl').value = '';
            document.getElementById('requestBody').value = '';
            currentRequestId = null;
        }
        
        function saveCurrentRequest() {
            const name = document.getElementById('requestName').value;
            const method = document.getElementById('requestMethod').value;
            const url = document.getElementById('requestUrl').value;
            const body = document.getElementById('requestBody').value;
            
            if (!name || !url) {
                alert('Please enter a name and URL');
                return;
            }
            
            if (currentRequestId) {
                fetch(`/api/requests/${currentRequestId}`, {
                    method: 'PUT',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({name, method, url, body})
                }).then(() => {
                    loadData();
                    alert('Request updated!');
                });
            } else {
                fetch('/api/requests', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({name, method, url, body})
                }).then(() => {
                    loadData();
                    alert('Request saved!');
                });
            }
        }
        
        // WebSocket support
        let ws = null;
        let wsConnected = false;
        
        function handleMethodChange() {
            const method = document.getElementById('methodSelect').value;
            const wsBtn = document.getElementById('wsConnectBtn');
            const wsTab = document.getElementById('wsTab');
            
            if (method === 'WS') {
                wsBtn.style.display = 'inline-block';
                wsTab.style.display = 'block';
            } else {
                wsBtn.style.display = 'none';
                wsTab.style.display = 'none';
                if (wsConnected) {
                    toggleWebSocket();
                }
            }
        }
        
        function toggleWebSocket() {
            const url = document.getElementById('urlInput').value;
            const btn = document.getElementById('wsConnectBtn');
            const sendBtn = document.getElementById('wsSendBtn');
            
            if (!wsConnected) {
                if (!url) {
                    alert('Please enter a WebSocket URL');
                    return;
                }
                try {
                    ws = new WebSocket(url);
                    
                    ws.onopen = function() {
                        wsConnected = true;
                        btn.textContent = 'Disconnect';
                        btn.classList.remove('btn-run');
                        btn.classList.add('secondary');
                        sendBtn.disabled = false;
                        addWsMessage('system', 'Connected to ' + url);
                    };
                    
                    ws.onmessage = function(event) {
                        addWsMessage('received', event.data);
                    };
                    
                    ws.onclose = function() {
                        wsConnected = false;
                        btn.textContent = 'Connect';
                        btn.classList.add('btn-run');
                        btn.classList.remove('secondary');
                        sendBtn.disabled = true;
                        addWsMessage('system', 'Disconnected');
                    };
                    
                    ws.onerror = function(error) {
                        addWsMessage('error', 'Error: ' + error);
                    };
                } catch (e) {
                    alert('Failed to connect: ' + e.message);
                }
            } else {
                ws.close();
            }
        }
        
        function sendWsMessage() {
            const input = document.getElementById('wsMessageInput');
            const message = input.value;
            
            if (ws && wsConnected && message) {
                ws.send(message);
                addWsMessage('sent', message);
                input.value = '';
            }
        }
        
        function addWsMessage(type, message) {
            const container = document.getElementById('wsMessages');
            const msgDiv = document.createElement('div');
            msgDiv.style.marginBottom = '0.5rem';
            
            if (type === 'sent') {
                msgDiv.innerHTML = '<span style="color:#22c55e;">➤</span> <span style="color:var(--text-primary);">' + escapeHtml(message) + '</span>';
            } else if (type === 'received') {
                msgDiv.innerHTML = '<span style="color:#f59e0b;">◀</span> <span style="color:var(--text-primary);">' + escapeHtml(message) + '</span>';
            } else if (type === 'error') {
                msgDiv.innerHTML = '<span style="color:#ef4444;">⚠</span> <span style="color:var(--text-primary);">' + escapeHtml(message) + '</span>';
            } else {
                msgDiv.innerHTML = '<span style="color:var(--text-secondary);">' + escapeHtml(message) + '</span>';
            }
            
            container.appendChild(msgDiv);
            container.scrollTop = container.scrollHeight;
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        let currentResponseView = 'raw';
        let currentResponseData = '';
        
        function setResponseView(view) {
            currentResponseView = view;
            const rawBody = document.getElementById('responseBody');
            const previewBody = document.getElementById('responsePreview');
            const btnRaw = document.getElementById('viewRaw');
            const btnPretty = document.getElementById('viewPretty');
            const btnPreview = document.getElementById('viewPreview');
            
            btnRaw.classList.remove('btn-run');
            btnPretty.classList.remove('btn-run');
            btnPreview.classList.remove('btn-run');
            btnRaw.classList.add('secondary');
            btnPretty.classList.add('secondary');
            btnPreview.classList.add('secondary');
            
            if (view === 'raw') {
                rawBody.style.display = 'block';
                previewBody.style.display = 'none';
                btnRaw.classList.remove('secondary');
                btnRaw.classList.add('btn-run');
                rawBody.textContent = currentResponseData;
            } else if (view === 'pretty') {
                rawBody.style.display = 'block';
                previewBody.style.display = 'none';
                btnPretty.classList.remove('secondary');
                btnPretty.classList.add('btn-run');
                try {
                    const json = JSON.parse(currentResponseData);
                    rawBody.textContent = JSON.stringify(json, null, 2);
                } catch (e) {
                    rawBody.textContent = currentResponseData;
                }
            } else if (view === 'preview') {
                btnPreview.classList.remove('secondary');
                btnPreview.classList.add('btn-run');
                const contentType = document.getElementById('responseBody').dataset.contentType || '';
                if (contentType.includes('html')) {
                    rawBody.style.display = 'none';
                    previewBody.style.display = 'block';
                    document.getElementById('previewFrame').srcdoc = currentResponseData;
                } else if (contentType.includes('image')) {
                    rawBody.style.display = 'block';
                    previewBody.style.display = 'none';
                    rawBody.innerHTML = '<img src="' + currentResponseData + '" style="max-width:100%;">';
                } else {
                    rawBody.style.display = 'block';
                    previewBody.style.display = 'none';
                    rawBody.textContent = 'Preview not available for this content type';
                }
            }
        }
        
        function renderEnvList() {
            const container = document.getElementById('envListContent');
            if (currentEnvironments.length === 0) {
                container.innerHTML = '<p style="color:var(--text-secondary)">No environments. Create one below.</p>';
                return;
            }
            container.innerHTML = currentEnvironments.map(env => \`
                <div class="env-item \${env.is_active ? 'active' : ''}">
                    <span class="env-item-name">\${env.name}</span>
                    <button class="btn-icon" onclick="activateEnv(\${env.id})" title="Activate">✓</button>
                    <button class="btn-icon" onclick="editEnv(\${env.id})" title="Edit">✏️</button>
                    <button class="btn-icon" onclick="deleteEnv(\${env.id})" title="Delete">🗑️</button>
                </div>
            \`).join('');
        }
        
        async function createEnv() {
            const name = prompt('Environment name:');
            if (!name) return;
            const res = await fetch('/api/environments', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name, variables: {}})
            });
            await loadEnvironments();
            renderEnvList();
        }
        
        async function activateEnv(id) {
            await fetch('/api/environments/' + id + '/activate', {method: 'POST'});
            await loadEnvironments();
            renderEnvList();
        }
        
        async function deleteEnv(id) {
            if (!confirm('Delete this environment?')) return;
            await fetch('/api/environments/' + id, {method: 'DELETE'});
            await loadEnvironments();
            renderEnvList();
        }
        
        async function editEnv(id) {
            const env = currentEnvironments.find(e => e.id === id);
            if (!env) return;
            
            const name = prompt('Environment name:', env.name);
            if (!name) return;
            
            let vars = prompt('Variables (JSON format):', JSON.stringify(env.variables || {}, null, 2));
            try {
                vars = vars ? JSON.parse(vars) : {};
            } catch(e) {
                alert('Invalid JSON');
                return;
            }
            
            await fetch('/api/environments/' + id, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name, variables: vars})
            });
            await loadEnvironments();
            renderEnvList();
        }
        
        function substituteVars(text) {
            if (!text || !activeEnvVars) return text;
            return text.replace(/\{\{([^}]+)\}\}/g, (match, varName) => {
                return activeEnvVars[varName.trim()] || match;
            });
        }
    </script>
    
    <!-- Environment Modal -->
    <div class="modal-overlay" id="envModal">
        <div class="modal">
            <div class="modal-header">
                <h3>Manage Environments</h3>
                <button class="close-btn" onclick="closeEnvModal()">×</button>
            </div>
            <div class="modal-body">
                <button class="btn-sm btn-run" onclick="createEnv()" style="margin-bottom:1rem;">+ New Environment</button>
                <div class="env-list" id="envListContent"></div>
            </div>
            <div class="modal-footer">
                <button class="btn-sm secondary" onclick="closeEnvModal()">Close</button>
            </div>
        </div>
    </div>
    
    <!-- Import Modal -->
    <div class="modal-overlay" id="importModal">
        <div class="modal" style="max-width:600px;">
            <div class="modal-header">
                <h3>Import API Definition</h3>
                <button class="close-btn" onclick="closeImportModal()">×</button>
            </div>
            <div class="modal-body">
                <div style="margin-bottom:1rem;">
                    <label style="display:block;margin-bottom:0.5rem;font-weight:500;">Import Type</label>
                    <select id="importType" class="env-select" style="width:100%;" onchange="toggleImportType()">
                        <option value="openapi">OpenAPI / Swagger</option>
                        <option value="postman">Postman Collection</option>
                    </select>
                </div>
                <div style="margin-bottom:1rem;">
                    <label style="display:block;margin-bottom:0.5rem;font-weight:500;">Paste JSON / YAML</label>
                    <textarea id="importData" class="code-editor" style="height:200px;" placeholder='{"openapi":"3.0.0","paths":{...}}'></textarea>
                </div>
                <div id="importPreview" style="max-height:200px;overflow:auto;background:var(--bg-tertiary);padding:0.5rem;border-radius:0.25rem;font-size:0.8rem;"></div>
            </div>
            <div class="modal-footer">
                <button class="btn-sm secondary" onclick="previewImport()">Preview</button>
                <button class="btn-sm btn-run" onclick="doImport()">Import</button>
                <button class="btn-sm secondary" onclick="closeImportModal()">Cancel</button>
            </div>
        </div>
    </div>
    
    <!-- Compare Modal -->
    <div class="modal-overlay" id="compareModal">
        <div class="modal" style="max-width:900px;">
            <div class="modal-header">
                <h3>Compare Requests</h3>
                <button class="close-btn" onclick="closeCompareModal()">&times;</button>
            </div>
            <div class="modal-body">
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;">
                    <div>
                        <h4 style="margin-bottom:0.5rem;">Request 1</h4>
                        <div id="compare1" style="background:var(--bg-tertiary);padding:0.75rem;border-radius:0.25rem;font-family:monospace;font-size:0.8rem;max-height:200px;overflow:auto;"></div>
                    </div>
                    <div>
                        <h4 style="margin-bottom:0.5rem;">Request 2</h4>
                        <div id="compare2" style="background:var(--bg-tertiary);padding:0.75rem;border-radius:0.25rem;font-family:monospace;font-size:0.8rem;max-height:200px;overflow:auto;"></div>
                    </div>
                </div>
                <div style="margin-top:1rem;">
                    <h4>Differences</h4>
                    <div id="compareDiff" style="background:var(--bg-tertiary);padding:0.75rem;border-radius:0.25rem;font-family:monospace;font-size:0.8rem;max-height:200px;overflow:auto;"></div>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn-sm secondary" onclick="closeCompareModal()">Close</button>
            </div>
        </div>
    </div>
    
    <script>
        function openImportModal() {
            document.getElementById('importModal').classList.add('active');
            document.getElementById('importData').value = '';
            document.getElementById('importPreview').innerHTML = '';
        }
        
        function closeImportModal() {
            document.getElementById('importModal').classList.remove('active');
        }
        
        function toggleImportType() {
            document.getElementById('importPreview').innerHTML = '';
        }
        
        async function previewImport() {
            const importType = document.getElementById('importType').value;
            const data = document.getElementById('importData').value;
            const preview = document.getElementById('importPreview');
            
            if (!data.trim()) {
                preview.innerHTML = '<span style="color:var(--error)">Please paste the JSON content</span>';
                return;
            }
            
            try {
                const json = JSON.parse(data);
                const endpoints = importType === 'openapi' ? 
                    await parseOpenAPIEndpoints(json) :
                    parsePostmanEndpoints(json);
                
                preview.innerHTML = endpoints.map(e => 
                    '<div style="padding:0.25rem;border-bottom:1px solid var(--border);">' +
                    '<span style="color:var(--success);font-weight:bold;">' + e.method + '</span> ' +
                    '<span>' + e.path + '</span> - ' +
                    '<span style="color:var(--text-secondary)">' + (e.name || e.summary || '') + '</span>' +
                    '</div>'
                ).join('');
            } catch(e) {
                preview.innerHTML = '<span style="color:var(--error)">Invalid JSON: ' + e.message + '</span>';
            }
        }
        
        async function parseOpenAPIEndpoints(spec) {
            const endpoints = [];
            const paths = spec.paths || {};
            for (const [path, methods] of Object.entries(paths)) {
                for (const [method, details] of Object.entries(methods)) {
                    if (['get','post','put','delete','patch'].includes(method.toLowerCase())) {
                        endpoints.push({
                            method: method.toUpperCase(),
                            path: path,
                            summary: details.summary || '',
                            name: details.summary || path
                        });
                    }
                }
            }
            return endpoints;
        }
        
        function parsePostmanEndpoints(collection) {
            const endpoints = [];
            const processItems = (items, folder = '') => {
                for (const item of items) {
                    if (item.item) {
                        processItems(item.item, item.name);
                    } else if (item.request) {
                        const url = item.request.url || {};
                        endpoints.push({
                            method: item.request.method || 'GET',
                            path: url.raw || url.toString() || '/',
                            name: item.name,
                            folder: folder
                        });
                    }
                }
            };
            processItems(collection.item || []);
            return endpoints;
        }
        
        async function doImport() {
            const importType = document.getElementById('importType').value;
            const data = document.getElementById('importData').value;
            
            try {
                const json = JSON.parse(data);
                const endpoint = importType === 'openapi' ? '/api/import/openapi' : '/api/import/postman';
                
                const res = await fetch(endpoint, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(importType === 'openapi' ? {spec: json} : {collection: json})
                });
                
                const result = await res.json();
                alert(result.message || result.error);
                closeImportModal();
                loadData();
            } catch(e) {
                alert('Import failed: ' + e.message);
            }
        }
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


@app.get("/api/environments")
async def get_environments() -> Dict[str, Any]:
    """Get all environments."""
    environments = Environment.get_all()
    active = Environment.get_active()
    return {
        "environments": [
            {
                "id": e.id,
                "name": e.name,
                "variables": e.variables,
                "is_active": e.is_active,
                "created_at": e.created_at,
                "updated_at": e.updated_at,
            }
            for e in environments
        ],
        "active": {"id": active.id, "name": active.name, "variables": active.variables}
        if active
        else None,
    }


@app.post("/api/environments")
async def create_environment(data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new environment."""
    env = Environment(
        name=data.get("name", "New Environment"), variables=data.get("variables", {})
    )
    env.save()
    return {
        "id": env.id,
        "name": env.name,
        "variables": env.variables,
        "message": "Environment created",
    }


@app.put("/api/environments/{env_id}")
async def update_environment(env_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
    """Update an environment."""
    env = Environment(id=env_id)
    if data.get("name"):
        env.name = data["name"]
    if data.get("variables"):
        env.variables = data["variables"]
    env.save()
    return {
        "id": env.id,
        "name": env.name,
        "variables": env.variables,
        "message": "Environment updated",
    }


@app.delete("/api/environments/{env_id}")
async def delete_environment(env_id: int) -> Dict[str, Any]:
    """Delete an environment."""
    env = Environment(id=env_id)
    env.delete()
    return {"message": "Environment deleted"}


@app.post("/api/environments/{env_id}/activate")
async def activate_environment(env_id: int) -> Dict[str, Any]:
    """Activate an environment."""
    envs = Environment.get_all()
    env = next((e for e in envs if e.id == env_id), None)
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")

    env.activate()
    return {
        "id": env.id,
        "name": env.name,
        "variables": env.variables,
        "message": "Environment activated",
    }


@app.get("/api/history")
async def get_request_history(limit: int = 100) -> Dict[str, Any]:
    """Get request history."""
    from socialseed_e2e.dashboard.models import RequestHistory

    history = RequestHistory.get_all(limit)
    return {
        "history": [
            {
                "id": h.id,
                "timestamp": h.timestamp,
                "method": h.method,
                "url": h.url,
                "headers": h.headers,
                "body": h.body,
                "response_status": h.response_status,
                "response_body": h.response_body,
                "response_headers": h.response_headers,
                "duration_ms": h.duration_ms,
                "environment_id": h.environment_id,
            }
            for h in history
        ]
    }


@app.get("/api/history/{history_id}")
async def get_request_history_item(history_id: int) -> Dict[str, Any]:
    """Get a single history entry."""
    from socialseed_e2e.dashboard.models import RequestHistory

    h = RequestHistory.get_by_id(history_id)
    if not h:
        raise HTTPException(status_code=404, detail="History entry not found")

    return {
        "id": h.id,
        "timestamp": h.timestamp,
        "method": h.method,
        "url": h.url,
        "headers": h.headers,
        "body": h.body,
        "response_status": h.response_status,
        "response_body": h.response_body,
        "response_headers": h.response_headers,
        "duration_ms": h.duration_ms,
        "environment_id": h.environment_id,
    }


@app.delete("/api/history")
async def clear_request_history() -> Dict[str, Any]:
    """Clear all request history."""
    from socialseed_e2e.dashboard.models import RequestHistory

    RequestHistory.delete_all()
    return {"message": "History cleared"}


@app.delete("/api/history/{history_id}")
async def delete_request_history_item(history_id: int) -> Dict[str, Any]:
    """Delete a single history entry."""
    from socialseed_e2e.dashboard.models import RequestHistory

    h = RequestHistory.get_by_id(history_id)
    if not h:
        raise HTTPException(status_code=404, detail="History entry not found")

    h.delete()
    return {"message": "History entry deleted"}


@app.get("/api/collections")
async def get_collections() -> Dict[str, Any]:
    """Get all collections with their requests."""
    collections = Collection.get_all()
    result = []
    for col in collections:
        requests = SavedRequest.get_all(col.id)
        result.append(
            {
                "id": col.id,
                "name": col.name,
                "description": col.description,
                "created_at": col.created_at,
                "updated_at": col.updated_at,
                "requests": [
                    {
                        "id": r.id,
                        "name": r.name,
                        "method": r.method,
                        "url": r.url,
                        "headers": r.headers,
                        "body": r.body,
                        "params": r.params,
                        "order_index": r.order_index,
                    }
                    for r in requests
                ],
            }
        )
    return {"collections": result}


@app.post("/api/collections")
async def create_collection(data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new collection."""
    col = Collection(
        name=data.get("name", "New Collection"), description=data.get("description", "")
    )
    col.save()
    return {
        "id": col.id,
        "name": col.name,
        "description": col.description,
        "message": "Collection created",
    }


@app.put("/api/collections/{collection_id}")
async def update_collection(collection_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
    """Update a collection."""
    col = Collection.get_by_id(collection_id)
    if not col:
        raise HTTPException(status_code=404, detail="Collection not found")

    if data.get("name"):
        col.name = data["name"]
    if "description" in data:
        col.description = data["description"]
    col.save()

    return {
        "id": col.id,
        "name": col.name,
        "description": col.description,
        "message": "Collection updated",
    }


@app.delete("/api/collections/{collection_id}")
async def delete_collection(collection_id: int) -> Dict[str, Any]:
    """Delete a collection."""
    col = Collection.get_by_id(collection_id)
    if not col:
        raise HTTPException(status_code=404, detail="Collection not found")

    col.delete()
    return {"message": "Collection deleted"}


@app.get("/api/requests")
async def get_requests(collection_id: int = None) -> Dict[str, Any]:
    """Get all saved requests, optionally filtered by collection."""
    requests = SavedRequest.get_all(collection_id)
    return {
        "requests": [
            {
                "id": r.id,
                "collection_id": r.collection_id,
                "name": r.name,
                "method": r.method,
                "url": r.url,
                "headers": r.headers,
                "body": r.body,
                "params": r.params,
                "order_index": r.order_index,
            }
            for r in requests
        ]
    }


@app.post("/api/requests")
async def create_request(data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new saved request."""
    req = SavedRequest(
        collection_id=data.get("collection_id"),
        name=data.get("name", "New Request"),
        method=data.get("method", "GET"),
        url=data.get("url", ""),
        headers=data.get("headers", "{}"),
        body=data.get("body", ""),
        params=data.get("params", "{}"),
        order_index=data.get("order_index", 0),
    )
    req.save()
    return {
        "id": req.id,
        "name": req.name,
        "method": req.method,
        "url": req.url,
        "message": "Request saved",
    }


@app.put("/api/requests/{request_id}")
async def update_request(request_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
    """Update a saved request."""
    req = SavedRequest.get_by_id(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    if data.get("name"):
        req.name = data["name"]
    if data.get("method"):
        req.method = data["method"]
    if data.get("url"):
        req.url = data["url"]
    if "headers" in data:
        req.headers = data["headers"]
    if "body" in data:
        req.body = data["body"]
    if "params" in data:
        req.params = data["params"]
    if "collection_id" in data:
        req.collection_id = data["collection_id"]
    req.save()

    return {
        "id": req.id,
        "name": req.name,
        "method": req.method,
        "url": req.url,
        "message": "Request updated",
    }


@app.delete("/api/requests/{request_id}")
async def delete_request(request_id: int) -> Dict[str, Any]:
    """Delete a saved request."""
    req = SavedRequest.get_by_id(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    req.delete()
    return {"message": "Request deleted"}


LANGUAGE_TEMPLATES = {
    "curl": """curl -X {{method}} "{{url}}" \\
  -H "Content-Type: application/json"{{headers}}{{body}}""",
    "python": """import requests

response = requests.{{method_lower}}(
    "{{url}}"{{params}}{{headers}}{{body}}
)

print(response.status_code)
print(response.json())""",
    "javascript": """fetch("{{url}}", {
  method: "{{method}}",
  headers: {{headers}}{{body}}
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error(error));""",
    "java": """OkHttpClient client = new OkHttpClient();

Request request = new Request.Builder()
  .url("{{url}}")
  .{{method_lower}}()
{{headers}}  .build();

Response response = client.newCall(request).execute();
System.out.println(response.body().string());""",
    "go": """req, err := http.NewRequest("{{method}}", "{{url}}", nil)
if err != nil {
    log.Fatal(err)
}

client := &http.Client{}
resp, err := client.Do(req)
if err != nil {
    log.Fatal(err)
}
defer resp.Body.Close()

body, _ := io.ReadAll(resp.Body)
fmt.Println(string(body))""",
}


@app.post("/api/snippets")
async def generate_snippet(data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate code snippet from request."""
    method = data.get("method", "GET")
    url = data.get("url", "")
    headers = data.get("headers", {})
    body = data.get("body", "")
    lang = data.get("language", "curl")

    headers_str = ""
    if headers:
        headers_dict = json.loads(headers) if isinstance(headers, str) else headers
        for k, v in headers_dict.items():
            headers_str += f'\\n  -H "{k}: {v}"'

    body_str = ""
    if body:
        body_str += f"\\n  -d '{body}'"

    body_js = ""
    if body:
        body_js += f",\\n  body: JSON.stringify({body})"

    body_py = ""
    if body and method in ["POST", "PUT", "PATCH"]:
        body_py += f",\\n    json={body}"

    body_go = ""
    if body:
        body_go += f", bytes.NewBuffer([]byte(`{body}`))"
        body_go += '\\n  .SetHeader("Content-Type", "application/json")'

    body_java = ""
    if body:
        body_java += (
            f'.post(RequestBody.create(MediaType.parse("application/json"), "{body}"))'
        )

    template = LANGUAGE_TEMPLATES.get(lang, LANGUAGE_TEMPLATES["curl"])

    result = template.replace("{{method}}", method)
    result = result.replace("{{method_lower}}", method.lower())
    result = result.replace("{{url}}", url)
    result = result.replace("{{headers}}", headers_str)
    result = result.replace("{{body}}", body_str)

    return {"snippet": result, "language": lang}


def substitute_variables(text: str, variables: Dict[str, str]) -> str:
    """Substitute {{variable}} placeholders with values."""
    if not text or not variables:
        return text

    def replace_var(match):
        var_name = match.group(1).strip()
        return variables.get(var_name, match.group(0))

    return re.sub(r"\{\{([^}]+)\}\}", replace_var, text)


@app.get("/api/test-content")
async def get_test_content(path: str) -> Dict[str, Any]:
    """Get test file content."""
    test_path = PROJECT_ROOT / "services" / path

    if test_path.exists():
        content = test_path.read_text()
        return {"content": content, "path": str(test_path)}

    return {"error": "Test not found", "path": path}


@app.websocket("/ws/test")
async def websocket_test(websocket):
    """WebSocket endpoint for testing."""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except Exception:
        pass


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

        response_body = (
            response.json()
            if response.headers.get("content-type", "").startswith("application/json")
            else response.text
        )

        result = {
            "status": response.status_code,
            "headers": dict(response.headers),
            "body": response_body,
            "test_name": test_name,
            "sandbox": is_sandbox,
            "timestamp": datetime.now().isoformat(),
        }

        # Save to test_runs (existing table)
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

        # Save to request_history (new table for detailed history)
        cursor.execute(
            """
            INSERT INTO request_history 
            (timestamp, method, url, headers, body, response_status, response_body, duration_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                result["timestamp"],
                method,
                url,
                json.dumps({}),
                json.dumps(body) if body else None,
                response.status_code,
                json.dumps(response_body),
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


def parse_openapi_spec(spec: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Parse OpenAPI spec and extract endpoints."""
    endpoints = []
    paths = spec.get("paths", {})

    for path, methods in paths.items():
        for method, details in methods.items():
            if method.upper() in [
                "GET",
                "POST",
                "PUT",
                "DELETE",
                "PATCH",
                "OPTIONS",
                "HEAD",
            ]:
                params = []

                # Extract parameters
                for param in details.get("parameters", []):
                    params.append(
                        {
                            "name": param.get("name"),
                            "in": param.get("in"),
                            "required": param.get("required", False),
                            "schema": param.get("schema", {}),
                            "description": param.get("description", ""),
                        }
                    )

                # Extract request body for POST/PUT/PATCH
                request_body = None
                if method.upper() in ["POST", "PUT", "PATCH"]:
                    content = details.get("requestBody", {}).get("content", {})
                    if "application/json" in content:
                        request_body = content["application/json"].get("schema", {})

                endpoints.append(
                    {
                        "path": path,
                        "method": method.upper(),
                        "summary": details.get("summary", ""),
                        "description": details.get("description", ""),
                        "parameters": params,
                        "request_body": request_body,
                        "tags": details.get("tags", []),
                    }
                )

    return endpoints


def parse_postman_collection(collection: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Parse Postman collection and extract requests."""
    endpoints = []

    items = collection.get("item", [])

    def parse_items(items_list, folder_name=""):
        for item in items_list:
            if "item" in item:  # Folder
                parse_items(item["item"], item.get("name", ""))
            else:  # Request
                request = item.get("request", {})
                url = request.get("url", {})
                url_str = url if isinstance(url, str) else url.get("raw", "")

                endpoints.append(
                    {
                        "path": url_str,
                        "method": request.get("method", "GET"),
                        "name": item.get("name", "Unnamed"),
                        "description": item.get("description", ""),
                        "folder": folder_name,
                        "headers": request.get("header", []),
                        "body": request.get("body", {}),
                    }
                )

    parse_items(items)
    return endpoints


@app.post("/api/import/openapi")
async def import_openapi(data: Dict[str, Any]) -> Dict[str, Any]:
    """Import endpoints from OpenAPI spec."""
    spec = data.get("spec", {})

    if not spec:
        return {"error": "No spec provided", "endpoints": []}

    try:
        endpoints = parse_openapi_spec(spec)

        # Save to database
        conn = get_db()
        cursor = conn.cursor()

        for ep in endpoints:
            cursor.execute(
                """
                INSERT INTO saved_requests 
                (name, method, url, headers, body, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    ep.get("summary", ep["path"]),
                    ep["method"],
                    ep["path"],
                    json.dumps(ep.get("parameters", [])),
                    json.dumps(ep.get("request_body", {})),
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                ),
            )

        conn.commit()
        conn.close()

        return {
            "message": f"Imported {len(endpoints)} endpoints",
            "endpoints": endpoints,
        }
    except Exception as e:
        return {"error": str(e), "endpoints": []}


@app.post("/api/import/postman")
async def import_postman(data: Dict[str, Any]) -> Dict[str, Any]:
    """Import requests from Postman collection."""
    collection = data.get("collection", {})

    if not collection:
        return {"error": "No collection provided", "endpoints": []}

    try:
        endpoints = parse_postman_collection(collection)

        conn = get_db()
        cursor = conn.cursor()

        for ep in endpoints:
            cursor.execute(
                """
                INSERT INTO saved_requests 
                (name, method, url, headers, body, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    ep.get("name", "Unnamed"),
                    ep["method"],
                    ep["path"],
                    json.dumps(ep.get("headers", [])),
                    json.dumps(ep.get("body", {})),
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                ),
            )

        conn.commit()
        conn.close()

        return {
            "message": f"Imported {len(endpoints)} requests",
            "endpoints": endpoints,
        }
    except Exception as e:
        return {"error": str(e), "endpoints": []}


@app.get("/api/saved-requests")
async def get_saved_requests() -> Dict[str, Any]:
    """Get all saved requests."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, method, url, headers, body, created_at
        FROM saved_requests
        ORDER BY created_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    return {
        "requests": [
            {
                "id": r["id"],
                "name": r["name"],
                "method": r["method"],
                "url": r["url"],
                "headers": json.loads(r["headers"]) if r["headers"] else {},
                "body": json.loads(r["body"]) if r["body"] else {},
                "created_at": r["created_at"],
            }
            for r in rows
        ]
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
