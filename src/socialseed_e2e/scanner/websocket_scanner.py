"""WebSocket events scanner for detecting WebSocket events and channels.

This module detects WebSocket server events, message formats, rooms/channels,
and generates example connection code.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class WebSocketEvent:
    """Represents a WebSocket event."""

    name: str
    direction: str  # "server" or "client"
    description: str = ""
    payload_schema: Dict[str, Any] = field(default_factory=dict)
    file_path: Optional[str] = None
    line_number: int = 0


@dataclass
class WebSocketInfo:
    """Represents detected WebSocket information."""

    events: List[WebSocketEvent] = field(default_factory=list)
    rooms: List[Dict[str, Any]] = field(default_factory=list)
    connection_code: str = ""
    namespace: str = "/"
    authentication: Dict[str, str] = field(default_factory=dict)


class WebSocketScanner:
    """Scans source code to extract WebSocket events."""

    EVENT_PATTERNS = {
        "python": {
            "socketio": [
                r"@sio\.on\(['\"](\w+)['\"]\)",
                r"\.on\(['\"](\w+)['\"]\)",
                r"emit\(['\"](\w+)['\"]",
            ],
            "websocket": [
                r"ws\.on\(['\"](\w+)['\"]\)",
                r"on\(['\"]message['\"]\)",
                r"on\(['\"]open['\"]\)",
                r"on\(['\"]close['\"]\)",
            ],
            "fastapi": [
                r"websocket\.(on|on_message|on_connect|on_disconnect)",
                r"@app\.websocket\(['\"](\/[\w\/]+)['\"]\)",
            ],
        },
        "java": {
            "spring": [
                r"@OnMessage",
                r"@OnOpen",
                r"@OnClose",
                r"@OnError",
                r"session\.sendRemoteString\(['\"](\w+)['\"]",
                r"broadcast\(['\"](\w+)['\"]",
            ],
            "javax": [
                r"@ServerEndpoint",
                r"@OnOpen",
                r"@OnMessage",
                r"@OnClose",
            ],
        },
        "javascript": {
            "socketio": [
                r"socket\.on\(['\"](\w+)['\"]",
                r"io\.on\(['\"]connection['\"]",
                r"emit\(['\"](\w+)['\"]",
            ],
            "ws": [
                r"ws\.on\(['\"](\w+)['\"]",
                r"\.on\(['\"]message['\"]",
            ],
            "native": [
                r"new WebSocket\(['\"]([\w:\/\.]+)['\"]\)",
                r"websocket\.send\(",
                r"websocket\.on",
            ],
        },
        "nodejs": {
            "socketio": [
                r"io\.(on|emit)\(['\"](\w+)['\"]",
                r"socket\.(on|emit)\(['\"](\w+)['\"]",
            ],
            "ws": [
                r"wss\.on\(['\"](\w+)['\"]",
                r"ws\.on\(['\"](\w+)['\"]",
            ],
        },
    }

    ROOM_PATTERNS = [
        r"join\(['\"](\w+)['\"]",
        r"to\(['\"](\w+)['\"]",
        r"in\(['\"](\w+)['\"]",
        r"room\(['\"]([\w\-]+)['\"]",
        r"socket\.join\(",
        r"\.joinRoom\(",
    ]

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def scan(self) -> WebSocketInfo:
        """Scan project and return WebSocket information."""
        info = WebSocketInfo()

        self._detect_events(info)
        self._detect_rooms(info)
        self._generate_connection_code(info)

        return info

    def _detect_events(self, info: WebSocketInfo) -> None:
        """Detect WebSocket events."""
        files_to_scan = self._get_websocket_files()

        for file_path in files_to_scan:
            content = file_path.read_text(errors="ignore")
            lines = content.split("\n")

            for line_num, line in enumerate(lines, 1):
                for lang, frameworks in self.EVENT_PATTERNS.items():
                    for framework, patterns in frameworks.items():
                        for pattern in patterns:
                            matches = re.finditer(pattern, line, re.IGNORECASE)
                            for match in matches:
                                if len(match.groups()) > 0:
                                    event_name = match.group(1) if match.lastindex else match.group(0)
                                    if event_name and len(event_name) < 50:
                                        direction = self._infer_direction(line, event_name)
                                        info.events.append(WebSocketEvent(
                                            name=event_name,
                                            direction=direction,
                                            file_path=str(file_path),
                                            line_number=line_num,
                                        ))

        info.events = self._deduplicate_events(info.events)

    def _infer_direction(self, line: str, event_name: str) -> str:
        """Infer event direction from code context."""
        line_lower = line.lower()
        
        if "emit(" in line_lower or "send" in line_lower:
            return "client"
        elif ".on(" in line_lower or "onmessage" in line_lower:
            return "server"
        elif "broadcast" in line_lower:
            return "server"
        
        if event_name in ["connect", "connection", "disconnect", "disconnected", 
                         "open", "close", "error"]:
            return "server"
        
        return "server"

    def _detect_rooms(self, info: WebSocketInfo) -> None:
        """Detect rooms/channels."""
        files_to_scan = self._get_websocket_files()

        for file_path in files_to_scan:
            content = file_path.read_text(errors="ignore")

            for pattern in self.ROOM_PATTERNS:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    if match.groups():
                        room_name = match.group(1)
                        info.rooms.append({
                            "name": room_name,
                            "file": str(file_path),
                        })

    def _deduplicate_events(self, events: List[WebSocketEvent]) -> List[WebSocketEvent]:
        """Remove duplicate events."""
        seen = set()
        unique = []
        for event in events:
            key = (event.name, event.direction)
            if key not in seen:
                seen.add(key)
                unique.append(event)
        return unique

    def _generate_connection_code(self, info: WebSocketInfo) -> None:
        """Generate example connection code."""
        code = '''# WebSocket Connection Example

import socketio

sio = socketio.Client()

@sio.on('connect')
def on_connect():
    print('Connected to server')

@sio.on('disconnect')
def on_disconnect():
    print('Disconnected from server')

'''
        for event in info.events:
            if event.direction == "server":
                code += f'''@sio.on('{event.name}')
def on_{event.name.replace(':', '_')}(data):
    print(f'Received {event.name}: {{data}}')

'''

        code += '''
# Connect to server
# sio.connect('http://localhost:3000')
# sio.wait()
'''
        info.connection_code = code

    def _get_websocket_files(self) -> List[Path]:
        """Get list of files related to WebSocket."""
        patterns = ["*socket*.py", "*socket*.js", "*socket*.ts", "*websocket*.py", "*ws*.js"]
        files = []

        for pattern in patterns:
            files.extend(self.project_root.rglob(pattern))

        socket_import = r"import.*socket|require.*socket|from.*socket"
        for ext in [".py", ".js", ".ts", ".java"]:
            for f in self.project_root.rglob(f"*{ext}"):
                if "socket" not in f.stem.lower():
                    try:
                        content = f.read_text(errors="ignore")
                        if re.search(socket_import, content, re.IGNORECASE):
                            files.append(f)
                    except Exception:
                        pass

        return files


def generate_websocket_doc(project_root: Path, output_path: Optional[Path] = None) -> str:
    """Generate WEBSOCKET_EVENTS.md document."""
    scanner = WebSocketScanner(project_root)
    info = scanner.scan()

    doc = """# Eventos WebSocket

## Conexión

```python
import socketio

sio = socketio.Client()

@sio.on('connect')
def on_connect():
    print('Connected to server')

@sio.on('disconnect')
def on_disconnect():
    print('Disconnected from server')
```

"""

    if info.events:
        doc += "## Eventos del Servidor\n\n"
        for event in info.events:
            if event.direction == "server":
                doc += f"### {event.name}\n"
                doc += f"Recibido del servidor: {event.description or 'N/A'}\n"
                doc += f"- Archivo: `{event.file_path}:{event.line_number}`\n\n"

    if info.events:
        doc += "## Eventos del Cliente\n\n"
        for event in info.events:
            if event.direction == "client":
                doc += f"### {event.name}\n"
                doc += f"Enviado al servidor: {event.description or 'N/A'}\n\n"

    if info.rooms:
        doc += "## Rooms/Canales\n\n"
        doc += "| Room | Archivo |\n"
        doc += "|------|--------|\n"
        for room in info.rooms:
            doc += f"| {room['name']} | `{room.get('file', 'N/A')}` |\n"
        doc += "\n"

    doc += "## Código de Ejemplo\n\n"
    doc += "```python\n" + info.connection_code + "```\n"

    if output_path:
        output_path.write_text(doc)

    return doc


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        project_root = Path(sys.argv[1])
        print(generate_websocket_doc(project_root))
    else:
        print("Usage: python websocket_scanner.py <project_root>")
