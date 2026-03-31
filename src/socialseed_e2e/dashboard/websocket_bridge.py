"""
WebSocket Bridge for Real-Time Dashboard Communication.

T01: Desarrollar el puente de conexión WebSockets desde el FastAPI Backend al Dashboard Vue.js.

This module provides WebSocket functionality to connect:
- FastAPI Backend <-> Vue.js Dashboard (real-time)
- Traffic Bot <-> Dashboard (live traffic updates)
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set
from dataclasses import dataclass, field

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel


class MessageType(str):
    """WebSocket message types."""
    TRAFFIC = "traffic"
    TEST_RESULT = "test_result"
    TEST_PROGRESS = "test_progress"
    ERROR = "error"
    INFO = "info"
    HEARTBEAT = "heartbeat"


@dataclass
class DashboardMessage:
    """A WebSocket message for the dashboard."""
    type: str
    data: Any
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = "system"


class ConnectionManager:
    """Manages WebSocket connections for the dashboard."""
    
    def __init__(self):
        self._active_connections: Set[WebSocket] = set()
        self._traffic_listeners: List[Callable] = []
        self._test_listeners: List[Callable] = []
    
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self._active_connections.add(websocket)
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        self._active_connections.discard(websocket)
    
    async def send_message(self, message: DashboardMessage):
        """Send a message to all connected clients."""
        if not self._active_connections:
            return
        
        message_data = {
            "type": message.type,
            "data": message.data,
            "timestamp": message.timestamp.isoformat(),
            "source": message.source,
        }
        
        # Send to all connections
        disconnected = set()
        for connection in self._active_connections:
            try:
                await connection.send_json(message_data)
            except Exception:
                disconnected.add(connection)
        
        # Clean up disconnected
        for conn in disconnected:
            self._active_connections.discard(conn)
    
    async def send_traffic_update(self, traffic_data: Dict[str, Any]):
        """Send traffic update to all clients."""
        message = DashboardMessage(
            type=MessageType.TRAFFIC,
            data=traffic_data,
            source="traffic_sniffer"
        )
        await self.send_message(message)
    
    async def send_test_result(self, result: Dict[str, Any]):
        """Send test result to all clients."""
        message = DashboardMessage(
            type=MessageType.TEST_RESULT,
            data=result,
            source="test_runner"
        )
        await self.send_message(message)
    
    async def send_test_progress(self, progress: Dict[str, Any]):
        """Send test progress to all clients."""
        message = DashboardMessage(
            type=MessageType.TEST_PROGRESS,
            data=progress,
            source="test_runner"
        )
        await self.send_message(message)
    
    async def broadcast_info(self, info: str):
        """Broadcast info message to all clients."""
        message = DashboardMessage(
            type=MessageType.INFO,
            data={"message": info},
        )
        await self.send_message(message)
    
    async def broadcast_error(self, error: str):
        """Broadcast error to all clients."""
        message = DashboardMessage(
            type=MessageType.ERROR,
            data={"error": error},
        )
        await self.send_message(message)
    
    def get_connection_count(self) -> int:
        """Get number of active connections."""
        return len(self._active_connections)


# Global connection manager
_manager: Optional[ConnectionManager] = None


def get_manager() -> ConnectionManager:
    """Get the global connection manager."""
    global _manager
    if _manager is None:
        _manager = ConnectionManager()
    return _manager


# FastAPI router for WebSocket endpoints
websocket_router = APIRouter()


@websocket_router.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    """WebSocket endpoint for dashboard real-time updates."""
    manager = get_manager()
    await manager.connect(websocket)
    
    try:
        # Send welcome message
        await websocket.send_json({
            "type": MessageType.INFO,
            "data": {"message": "Connected to dashboard"},
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                msg_type = message.get("type")
                
                if msg_type == MessageType.HEARTBEAT:
                    # Respond to heartbeat
                    await websocket.send_json({
                        "type": MessageType.HEARTBEAT,
                        "timestamp": datetime.now().isoformat()
                    })
                elif msg_type == "ping":
                    await websocket.send_json({"type": "pong"})
                    
            except json.JSONDecodeError:
                pass
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@websocket_router.websocket("/ws/traffic")
async def websocket_traffic(websocket: WebSocket):
    """WebSocket endpoint specifically for traffic updates."""
    manager = get_manager()
    await manager.connect(websocket)
    
    try:
        # Send initial traffic data if available
        # (This would connect to the TrafficSniffer)
        await websocket.send_json({
            "type": "traffic_init",
            "data": {"status": "listening"},
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep connection open
        while True:
            data = await websocket.receive_text()
            # Handle any incoming traffic control messages
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@websocket_router.websocket("/ws/tests")
async def websocket_tests(websocket: WebSocket):
    """WebSocket endpoint for test execution updates."""
    manager = get_manager()
    await manager.connect(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            # Handle test control messages
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)


class DashboardWebSocketClient:
    """Client-side WebSocket helper for the Vue.js dashboard."""
    
    def __init__(self, ws_url: str = "ws://localhost:8000/ws/dashboard"):
        self.ws_url = ws_url
        self._ws = None
        self._connected = False
        self._listeners: Dict[str, List[Callable]] = {
            MessageType.TRAFFIC: [],
            MessageType.TEST_RESULT: [],
            MessageType.TEST_PROGRESS: [],
            MessageType.ERROR: [],
            MessageType.INFO: [],
        }
    
    async def connect(self):
        """Connect to the WebSocket server."""
        import websockets
        
        try:
            self._ws = await websockets.connect(self.ws_url)
            self._connected = True
            # Start listening in background
            asyncio.create_task(self._listen())
        except Exception as e:
            print(f"WebSocket connection failed: {e}")
            self._connected = False
    
    async def _listen(self):
        """Listen for incoming messages."""
        if not self._ws:
            return
            
        try:
            async for message in self._ws:
                data = json.loads(message)
                msg_type = data.get("type")
                
                # Call registered listeners
                if msg_type in self._listeners:
                    for callback in self._listeners[msg_type]:
                        callback(data.get("data"))
                        
        except Exception as e:
            print(f"WebSocket listen error: {e}")
            self._connected = False
    
    def on(self, message_type: str, callback: Callable):
        """Register a callback for a message type."""
        if message_type in self._listeners:
            self._listeners[message_type].append(callback)
    
    async def send(self, message: Dict[str, Any]):
        """Send a message to the server."""
        if self._ws and self._connected:
            await self._ws.send(json.dumps(message))
    
    async def close(self):
        """Close the WebSocket connection."""
        if self._ws:
            await self._ws.close()
            self._connected = False


# Integration helper for existing modules
class TrafficToDashboardBridge:
    """Bridge traffic sniffer events to dashboard."""
    
    def __init__(self):
        self.manager = get_manager()
    
    async def notify_traffic(self, traffic_data: Dict[str, Any]):
        """Send traffic update to dashboard."""
        await self.manager.send_traffic_update(traffic_data)


class TestRunnerToDashboardBridge:
    """Bridge test runner events to dashboard."""
    
    def __init__(self):
        self.manager = get_manager()
    
    async def notify_result(self, result: Dict[str, Any]):
        """Send test result to dashboard."""
        await self.manager.send_test_result(result)
    
    async def notify_progress(self, progress: Dict[str, Any]):
        """Send test progress to dashboard."""
        await self.manager.send_test_progress(progress)


if __name__ == "__main__":
    # Example: Start WebSocket server
    print("WebSocket Bridge for Dashboard")
    print("=" * 40)
    print("This module provides:")
    print("  - WebSocket endpoints at /ws/dashboard")
    print("  - Real-time traffic updates")
    print("  - Test execution streaming")
    print("  - Vue.js client helper")