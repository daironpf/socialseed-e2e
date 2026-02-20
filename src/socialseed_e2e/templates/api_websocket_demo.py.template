#!/usr/bin/env python3
"""WebSocket Demo API for socialseed-e2e Testing

This is a simple WebSocket API for real-time messaging.
Use this API to test WebSocket functionality in socialseed-e2e.

Usage:
    # Install aiohttp first
    pip install aiohttp
    
    # Start the WebSocket server
    python api-websocket-demo.py
    
    # The WebSocket server will be available at http://localhost:50052
    # WebSocket endpoint: ws://localhost:50052/ws

WebSocket Messages:
    {"type": "ping"}                    - Ping the server
    {"type": "echo", "data": "msg"}    - Echo back a message
    {"type": "broadcast", "message": "msg", "sender": "name"} - Broadcast to all clients
    {"type": "subscribe", "channel": "name"} - Subscribe to a channel
"""

import asyncio
import json
from datetime import datetime
from aiohttp import web
import aiohttp


class WebSocketHandler:
    """WebSocket handler for real-time messaging"""
    
    def __init__(self):
        self.connections = set()
        self.channels = {}
        self.messages = []
    
    async def handle_websocket(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self.connections.add(ws)
        
        try:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        await self.process_message(ws, data)
                    except json.JSONDecodeError:
                        await ws.send_json({
                            "type": "error",
                            "message": "Invalid JSON"
                        })
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    print(f"WebSocket error: {ws.exception()}")
        finally:
            self.connections.remove(ws)
        return ws
    
    async def process_message(self, ws, data):
        msg_type = data.get("type")
        response = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "original_type": msg_type
        }
        
        if msg_type == "ping":
            response["type"] = "pong"
            response["message"] = "Pong from server"
            
        elif msg_type == "echo":
            response["type"] = "echo"
            response["data"] = data.get("data")
            response["message"] = "Echoed successfully"
            
        elif msg_type == "broadcast":
            response["type"] = "broadcast"
            response["message"] = data.get("message")
            response["sender"] = data.get("sender", "anonymous")
            # Broadcast to all other connections
            for conn in self.connections:
                if conn != ws:
                    await conn.send_json(response)
                    
        elif msg_type == "subscribe":
            channel = data.get("channel")
            if channel:
                if channel not in self.channels:
                    self.channels[channel] = set()
                self.channels[channel].add(ws)
                response["type"] = "subscribed"
                response["channel"] = channel
                response["message"] = f"Subscribed to channel: {channel}"
                
        elif msg_type == "publish":
            channel = data.get("channel")
            message = data.get("message")
            if channel and channel in self.channels:
                response["type"] = "publish"
                response["channel"] = channel
                response["message"] = message
                for conn in self.channels[channel]:
                    if conn != ws:
                        await conn.send_json(response)
                        
        elif msg_type == "get_channels":
            response["type"] = "channels"
            response["channels"] = list(self.channels.keys())
            
        else:
            response["type"] = "error"
            response["message"] = f"Unknown message type: {msg_type}"
        
        self.messages.append(response)
        await ws.send_json(response)


async def health(request):
    """Health check endpoint"""
    return web.json_response({
        "status": "healthy",
        "service": "websocket-demo",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })


async def websocket_handler(request):
    """WebSocket endpoint handler"""
    handler = request.app["ws_handler"]
    return await handler.handle_websocket(request)


def create_app():
    """Create and configure the aiohttp application"""
    app = web.Application()
    handler = WebSocketHandler()
    app["ws_handler"] = handler
    app.router.add_get("/health", health)
    app.router.add_get("/ws", websocket_handler)
    return app


if __name__ == "__main__":
    app = create_app()
    
    print("=" * 60)
    print("🚀 WebSocket Demo API for socialseed-e2e Testing")
    print("=" * 60)
    print("\n📍 HTTP URL: http://localhost:50052")
    print("📍 WebSocket URL: ws://localhost:50052/ws")
    print("\nWebSocket message types:")
    print('  {"type": "ping"}')
    print('  {"type": "echo", "data": "message"}')
    print('  {"type": "broadcast", "message": "msg", "sender": "name"}')
    print('  {"type": "subscribe", "channel": "name"}')
    print('  {"type": "publish", "channel": "name", "message": "msg"}')
    print('  {"type": "get_channels"}')
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60 + "\n")
    
    web.run_app(app, host="0.0.0.0", port=50052)
