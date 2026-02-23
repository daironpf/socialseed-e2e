import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Optional

from pydantic import BaseModel


class RequestSnapshot(BaseModel):
    method: str
    path: str
    headers: dict[str, str]
    body: Optional[str]
    timestamp: datetime


class DependencyMock(BaseModel):
    name: str
    response_status: int
    response_body: str
    response_headers: dict[str, str]
    delay_ms: int = 0


class IncidentReplay(BaseModel):
    incident_id: str
    requests: list[RequestSnapshot]
    dependencies: list[DependencyMock]
    created_at: datetime


class TimeTravelConfig(BaseModel):
    output_dir: Path = Path(".e2e/time_travel")
    mock_server_port: int = 8899
    docker_compose_template: str = "docker-compose.yml.j2"


class IncidentRecorder:
    def __init__(self, config: TimeTravelConfig):
        self.config = config
        self._snapshots: list[RequestSnapshot] = []
        self._dependencies: list[DependencyMock] = []
        self._recording = False

    def start_recording(self, dependencies: Optional[list[str]] = None) -> None:
        self._recording = True
        self._snapshots.clear()
        self._dependencies.clear()

        if dependencies:
            for dep in dependencies:
                self._dependencies.append(
                    DependencyMock(
                        name=dep,
                        response_status=200,
                        response_body="{}",
                        response_headers={},
                    )
                )

    def stop_recording(self) -> list[RequestSnapshot]:
        self._recording = False
        return self._snapshots.copy()

    def record_request(
        self,
        method: str,
        path: str,
        headers: dict[str, str],
        body: Optional[str] = None,
    ) -> None:
        if not self._recording:
            return

        snapshot = RequestSnapshot(
            method=method,
            path=path,
            headers=headers,
            body=body,
            timestamp=datetime.now(),
        )
        self._snapshots.append(snapshot)

    def add_dependency_mock(
        self,
        name: str,
        response_status: int,
        response_body: str,
        delay_ms: int = 0,
    ) -> None:
        mock = DependencyMock(
            name=name,
            response_status=response_status,
            response_body=response_body,
            response_headers={"Content-Type": "application/json"},
            delay_ms=delay_ms,
        )

        for i, dep in enumerate(self._dependencies):
            if dep.name == name:
                self._dependencies[i] = mock
                return

        self._dependencies.append(mock)

    def save_incident(self, incident_id: str) -> IncidentReplay:
        incident = IncidentReplay(
            incident_id=incident_id,
            requests=self._snapshots.copy(),
            dependencies=self._dependencies.copy(),
            created_at=datetime.now(),
        )

        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        output_file = self.config.output_dir / f"{incident_id}.json"

        with open(output_file, "w") as f:
            f.write(incident.model_dump_json(indent=2))

        return incident

    def load_incident(self, incident_id: str) -> Optional[IncidentReplay]:
        input_file = self.config.output_dir / f"{incident_id}.json"
        if not input_file.exists():
            return None

        with open(input_file) as f:
            data = json.load(f)
            data["created_at"] = datetime.fromisoformat(data["created_at"])
            return IncidentReplay(**data)


class MockServerGenerator:
    def __init__(self, config: TimeTravelConfig):
        self.config = config

    def generate_docker_compose(self, incident: IncidentReplay) -> Path:
        compose = {
            "version": "3.8",
            "services": {
                "replay-server": {
                    "image": "nginx:latest",
                    "ports": [f"{self.config.mock_server_port}:80"],
                    "volumes": ["./replay-config:/etc/nginx/conf.d"],
                },
                "mock-services": {
                    "image": "python:3.11-slim",
                    "command": "python -m http.server 8080",
                    "ports": ["8900:8080"],
                },
            },
        }

        output_file = (
            self.config.output_dir / incident.incident_id / "docker-compose.yml"
        )
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            import yaml

            yaml.dump(compose, f)

        return output_file

    def generate_mock_server_script(self, incident: IncidentReplay) -> Path:
        mock_routes = {}
        for req in incident.requests:
            key = f"{req.method}:{req.path}"
            mock_routes[key] = {
                "status": 200,
                "body": req.body or "{}",
            }

        script = f'''#!/usr/bin/env python3
"""Mock server script for incident replay: {incident.incident_id}"""

import json
import asyncio
from aiohttp import web

MOCK_ROUTES = {json.dumps(mock_routes, indent=4)}

async def handle_request(request):
    key = f"{{request.method}}:{{request.path}}"

    if key in MOCK_ROUTES:
        mock = MOCK_ROUTES[key]
        return web.json_response(
            json.loads(mock["body"]),
            status=mock["status"]
        )

    return web.json_response({{"error": "Not mocked"}}, status=404)

app = web.Application()
app.router.add_route("*", "{{path}}", handle_request)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=8900)
'''

        output_file = self.config.output_dir / incident.incident_id / "mock_server.py"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            f.write(script)

        return output_file

    def generate_test_script(self, incident: IncidentReplay) -> Path:
        test_code = f'''"""Test script to reproduce incident: {incident.incident_id}"""

import pytest
import requests
from datetime import datetime

INCIDENT_ID = "{incident.incident_id}"
MOCK_SERVER_URL = "http://localhost:{self.config.mock_server_port}"
INCIDENT_DATE = "{incident.created_at.isoformat()}"

class TestIncidentReplay:
    """Test class that reproduces the incident conditions"""

    def setup_method(self):
        """Setup test environment"""
        self.requests_session = requests.Session()

    def test_reproduce_incident(self):
        """Replay the exact sequence that caused the incident"""
'''

        for i, req in enumerate(incident.requests):
            test_code += f'''
    def test_request_{i + 1}_{req.method.lower()}_{req.path.replace("/", "_").replace("{{", "").replace("}}", "")}(self):
        """{req.method} {req.path}"""
        response = self.requests_session.{req.method.lower()}(
            f"{{MOCK_SERVER_URL}}{req.path}",
            headers={json.dumps(req.headers)},
            json={json.dumps(json.loads(req.body)) if req.body else None},
        )
        assert response.status_code == {200 if "error" not in req.path else 500}
'''

        output_file = self.config.output_dir / incident.incident_id / "test_incident.py"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            f.write(test_code)

        return output_file


class IncidentReproducer:
    def __init__(self, config: TimeTravelConfig):
        self.config = config
        self.recorder = IncidentRecorder(config)
        self.generator = MockServerGenerator(config)

    def prepare_reproduction(self, incident_id: str) -> Path:
        incident = self.recorder.load_incident(incident_id)
        if not incident:
            raise ValueError(f"Incident not found: {incident_id}")

        self.generator.generate_docker_compose(incident)
        self.generator.generate_mock_server_script(incident)
        self.generator.generate_test_script(incident)

        return incident.incident_id

    def generate_replay_package(self, incident_id: str) -> Path:
        incident = self.recorder.load_incident(incident_id)
        if not incident:
            raise ValueError(f"Incident not found: {incident_id}")

        self.generator.generate_docker_compose(incident)
        self.generator.generate_mock_server_script(incident)
        self.generator.generate_test_script(incident)

        return self.config.output_dir / incident_id
