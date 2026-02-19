from pathlib import Path
from typing import Any, Callable, Optional
import asyncio
import json
from datetime import datetime

from pydantic import BaseModel
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import uvicorn


class EndpointNode(BaseModel):
    path: str
    method: str
    children: dict[str, "EndpointNode"] = {}


class TrafficEvent(BaseModel):
    method: str
    path: str
    status_code: int
    timestamp: datetime
    duration_ms: float


class DashboardConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8501
    title: str = "SocialSeed E2E Dashboard"
    static_dir: Optional[Path] = None


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass


class TrafficStreamer:
    def __init__(self, manager: ConnectionManager):
        self.manager = manager

    async def stream_traffic(self, traffic: TrafficEvent):
        message = {
            "type": "traffic",
            "data": traffic.model_dump(),
        }
        await self.manager.broadcast(message)


def build_endpoint_tree(endpoints: list[dict]) -> EndpointNode:
    root = EndpointNode(path="/", method="")

    for endpoint in endpoints:
        path = endpoint.get("path", "/")
        method = endpoint.get("method", "GET")

        parts = [p for p in path.split("/") if p]
        current = root

        for i, part in enumerate(parts):
            is_param = part.startswith("{")
            key = part if not is_param else ":param"

            if key not in current.children:
                current.children[key] = EndpointNode(
                    path="/".join(parts[: i + 1]) if i < len(parts) else path,
                    method=method if i == len(parts) - 1 else "",
                )
            current = current.children[key]

    return root


class DashboardServer:
    def __init__(
        self,
        config: DashboardConfig,
        on_chat_message: Optional[Callable[[str], str]] = None,
    ):
        self.config = config
        self.on_chat_message = on_chat_message
        self.app = FastAPI(title=config.title)
        self.manager = ConnectionManager()
        self.streamer = TrafficStreamer(self.manager)
        self._setup_routes()

    def _setup_routes(self):
        @self.app.get("/", response_class=HTMLResponse)
        async def root():
            return self._get_dashboard_html()

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await self.manager.connect(websocket)
            try:
                while True:
                    data = await websocket.receive_text()
                    if self.on_chat_message:
                        response = self.on_chat_message(data)
                        await websocket.send_json(
                            {
                                "type": "chat_response",
                                "data": response,
                            }
                        )
            except WebSocketDisconnect:
                self.manager.disconnect(websocket)

        @self.app.post("/api/endpoints")
        async def update_endpoints(endpoints: list[dict]):
            tree = build_endpoint_tree(endpoints)
            await self.manager.broadcast(
                {
                    "type": "endpoints_updated",
                    "data": self._serialize_tree(tree),
                }
            )
            return {"status": "ok"}

    def _serialize_tree(self, node: EndpointNode) -> dict:
        result = {
            "path": node.path,
            "method": node.method,
            "children": {},
        }
        for key, child in node.children.items():
            result["children"][key] = self._serialize_tree(child)
        return result

    def _get_dashboard_html(self) -> str:
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SocialSeed E2E Dashboard</title>
    <script src="https://unpkg.com/react@18/umd/react.development.js"></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
        .endpoint-tree { max-height: 400px; overflow-y: auto; }
        .live-stream { max-height: 300px; overflow-y: auto; }
        .method-get { background: #61affe; color: white; }
        .method-post { background: #49cc90; color: white; }
        .method-put { background: #fca130; color: white; }
        .method-delete { background: #f93e3e; color: white; }
        .method-patch { background: #50e3c2; color: white; }
    </style>
</head>
<body class="bg-gray-900 text-white">
    <div id="root"></div>
    
    <script type="text/babel">
        const { useState, useEffect, useRef } = React;
        
        function App() {
            const [activeTab, setActiveTab] = useState('endpoints');
            const [endpoints, setEndpoints] = useState({});
            const [traffic, setTraffic] = useState([]);
            const [chatMessages, setChatMessages] = useState([]);
            const [chatInput, setChatInput] = useState('');
            const wsRef = useRef(null);
            
            useEffect(() => {
                wsRef.current = new WebSocket(`ws://${window.location.host}/ws`);
                
                wsRef.current.onmessage = (event) => {
                    const msg = JSON.parse(event.data);
                    if (msg.type === 'traffic') {
                        setTraffic(prev => [msg.data, ...prev].slice(0, 100));
                    } else if (msg.type === 'endpoints_updated') {
                        setEndpoints(msg.data);
                    } else if (msg.type === 'chat_response') {
                        setChatMessages(prev => [...prev, { role: 'assistant', content: msg.data }]);
                    }
                };
                
                return () => wsRef.current?.close();
            }, []);
            
            const sendChat = () => {
                if (!chatInput.trim()) return;
                setChatMessages(prev => [...prev, { role: 'user', content: chatInput }]);
                wsRef.current?.send(chatInput);
                setChatInput('');
            };
            
            return (
                <div className="flex h-screen">
                    <div className="w-64 bg-gray-800 p-4">
                        <h1 className="text-xl font-bold mb-4">SocialSeed E2E</h1>
                        <nav className="space-y-2">
                            <button onClick={() => setActiveTab('endpoints')} 
                                className={`w-full text-left p-2 rounded ${activeTab === 'endpoints' ? 'bg-blue-600' : 'hover:bg-gray-700'}`}>
                                Endpoints
                            </button>
                            <button onClick={() => setActiveTab('traffic')} 
                                className={`w-full text-left p-2 rounded ${activeTab === 'traffic' ? 'bg-blue-600' : 'hover:bg-gray-700'}`}>
                                Live Traffic
                            </button>
                            <button onClick={() => setActiveTab('chat')} 
                                className={`w-full text-left p-2 rounded ${activeTab === 'chat' ? 'bg-blue-600' : 'hover:bg-gray-700'}`}>
                                AI Chat
                            </button>
                        </nav>
                    </div>
                    
                    <div className="flex-1 p-4 overflow-auto">
                        {activeTab === 'endpoints' && (
                            <div className="bg-gray-800 rounded p-4">
                                <h2 className="text-lg font-bold mb-4">API Endpoints</h2>
                                <EndpointTree data={endpoints} />
                            </div>
                        )}
                        
                        {activeTab === 'traffic' && (
                            <div className="bg-gray-800 rounded p-4">
                                <h2 className="text-lg font-bold mb-4">Live Traffic</h2>
                                <div className="live-stream space-y-2">
                                    {traffic.map((t, i) => (
                                        <div key={i} className="flex items-center gap-2 p-2 bg-gray-700 rounded">
                                            <span className={`px-2 py-1 rounded text-xs font-bold method-${t.method.toLowerCase()}`}>
                                                {t.method}
                                            </span>
                                            <span className="flex-1">{t.path}</span>
                                            <span className={`px-2 py-1 rounded ${t.status_code < 400 ? 'text-green-400' : 'text-red-400'}`}>
                                                {t.status_code}
                                            </span>
                                            <span className="text-gray-400 text-sm">{t.duration_ms}ms</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                        
                        {activeTab === 'chat' && (
                            <div className="bg-gray-800 rounded p-4 h-full flex flex-col">
                                <h2 className="text-lg font-bold mb-4">AI Assistant</h2>
                                <div className="flex-1 overflow-auto mb-4 space-y-4">
                                    {chatMessages.map((msg, i) => (
                                        <div key={i} className={`p-3 rounded ${msg.role === 'user' ? 'bg-blue-900 ml-8' : 'bg-gray-700 mr-8'}`}>
                                            {msg.content}
                                        </div>
                                    ))}
                                </div>
                                <div className="flex gap-2">
                                    <input 
                                        value={chatInput}
                                        onChange={(e) => setChatInput(e.target.value)}
                                        onKeyPress={(e) => e.key === 'Enter' && sendChat()}
                                        placeholder="Ask AI to generate tests..."
                                        className="flex-1 p-2 bg-gray-700 rounded border border-gray-600"
                                    />
                                    <button onClick={sendChat} className="px-4 bg-blue-600 rounded hover:bg-blue-700">
                                        Send
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            );
        }
        
        function EndpointTree({ data, depth = 0 }) {
            if (!data || !data.children) return null;
            
            return (
                <div className="ml-4">
                    {Object.entries(data.children).map(([key, node]) => (
                        <div key={key} className="py-1">
                            {node.method && (
                                <span className={`inline-block px-2 py-0.5 rounded text-xs font-bold mr-2 method-${node.method.toLowerCase()}`}>
                                    {node.method}
                                </span>
                            )}
                            <span className={node.method ? "text-blue-300" : "text-gray-400"}>
                                {node.path}
                            </span>
                            <EndpointTree data={node} depth={depth + 1} />
                        </div>
                    ))}
                </div>
            );
        }
        
        ReactDOM.createRoot(document.getElementById('root')).render(<App />);
    </script>
</body>
</html>"""

    def run(self):
        uvicorn.run(self.app, host=self.config.host, port=self.config.port)
