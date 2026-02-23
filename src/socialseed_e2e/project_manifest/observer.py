"""The Observer - Auto-detect running services and ports.

This module provides active port scanning, service detection, and cross-referencing
with project code to automatically identify where APIs are hosted.

Issue #186: Implement "The Observer" to auto-detect running services and ports
"""

import asyncio
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests


@dataclass
class PortScanResult:
    """Result of scanning a specific port."""

    port: int
    is_open: bool
    protocol: str = "unknown"
    service_type: Optional[str] = None  # 'http', 'grpc', 'unknown'
    response_time_ms: Optional[float] = None
    health_endpoint: Optional[str] = None
    api_version: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DetectedService:
    """A detected running service with its details."""

    name: str
    host: str
    port: int
    base_url: str
    service_type: str  # 'http', 'grpc', 'https'
    health_endpoint: Optional[str] = None
    detected_from: str = "scan"  # 'scan', 'docker', 'config', 'code'
    confidence: float = 0.0  # 0.0 to 1.0
    process_info: Optional[Dict[str, Any]] = None
    matched_code_service: Optional[str] = None  # Cross-reference with code


@dataclass
class DockerContainer:
    """Information about a Docker container."""

    container_id: str
    name: str
    image: str
    ports: List[Dict[str, Any]]  # [{'private': 8080, 'public': 8080, 'type': 'tcp'}]
    status: str
    health: Optional[str] = None


@dataclass
class DockerSetupSuggestion:
    """Suggestion for Docker setup."""

    dockerfile_path: Path
    compose_path: Optional[Path]
    suggested_command: str
    can_auto_build: bool
    build_time_estimate: str
    services_in_compose: List[str]


class PortScanner:
    """Active port scanner for detecting HTTP and gRPC services."""

    # Common ports to scan for web services
    COMMON_HTTP_PORTS = [80, 443, 8000, 8080, 8443, 3000, 5000, 9000, 10000]
    COMMON_GRPC_PORTS = [50051, 50052, 50053, 50054, 50055]
    COMMON_API_PORTS = [
        8000,
        8080,
        8443,  # Standard HTTP/HTTPS
        3000,
        3001,  # Node.js/React
        5000,
        5001,  # Flask/Python
        8001,
        8081,
        8082,  # Alternative HTTP
        9000,
        9001,  # Alternative APIs
        10000,  # Alternative
    ]

    # Health check endpoints to try
    HEALTH_ENDPOINTS = [
        "/health",
        "/healthz",
        "/actuator/health",
        "/api/health",
        "/status",
        "/ping",
        "/ready",
        "/alive",
    ]

    def __init__(self, timeout: float = 2.0, max_workers: int = 50):
        """Initialize port scanner.

        Args:
            timeout: Timeout for each port scan in seconds
            max_workers: Maximum concurrent workers for scanning
        """
        self.timeout = timeout
        self.max_workers = max_workers

    async def scan_host(
        self,
        host: str,
        ports: Optional[List[int]] = None,
        detect_protocols: bool = True,
    ) -> List[PortScanResult]:
        """Scan a host for open ports.

        Args:
            host: Host to scan (e.g., 'localhost', '127.0.0.1')
            ports: List of ports to scan (defaults to COMMON_API_PORTS)
            detect_protocols: Whether to detect HTTP/gRPC protocols

        Returns:
            List of PortScanResult for open ports
        """
        if ports is None:
            ports = self.COMMON_API_PORTS

        # Use asyncio for concurrent scanning
        semaphore = asyncio.Semaphore(self.max_workers)

        async def scan_with_limit(port: int) -> Optional[PortScanResult]:
            async with semaphore:
                return await self._scan_port(host, port, detect_protocols)

        # Scan all ports concurrently
        tasks = [scan_with_limit(port) for port in ports]
        results = await asyncio.gather(*tasks)

        # Filter out None results (closed ports)
        return [r for r in results if r is not None and r.is_open]

    async def _scan_port(
        self, host: str, port: int, detect_protocols: bool
    ) -> Optional[PortScanResult]:
        """Scan a single port.

        Args:
            host: Host to scan
            port: Port number
            detect_protocols: Whether to detect protocol

        Returns:
            PortScanResult if port is open, None otherwise
        """
        start_time = time.time()

        try:
            # Try TCP connection
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port), timeout=self.timeout
            )

            response_time = (time.time() - start_time) * 1000

            result = PortScanResult(port=port, is_open=True, response_time_ms=response_time)

            if detect_protocols:
                # Detect protocol
                await self._detect_protocol(reader, writer, host, port, result)

            writer.close()
            await writer.wait_closed()

            return result

        except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
            return None

    async def _detect_protocol(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        host: str,
        port: int,
        result: PortScanResult,
    ) -> None:
        """Detect if the service is HTTP or gRPC.

        Args:
            reader: Stream reader
            writer: Stream writer
            host: Host
            port: Port
            result: PortScanResult to update
        """
        # First, try HTTP/HTTPS detection
        http_detected = await self._try_http_detection(host, port, result)

        if not http_detected:
            # Try gRPC detection
            await self._try_grpc_detection(host, port, result)

    async def _try_http_detection(self, host: str, port: int, result: PortScanResult) -> bool:
        """Try to detect HTTP/HTTPS service.

        Args:
            host: Host
            port: Port
            result: PortScanResult to update

        Returns:
            True if HTTP detected, False otherwise
        """
        protocols = ["http", "https"]

        for protocol in protocols:
            try:
                url = f"{protocol}://{host}:{port}"

                # Try to connect with a simple GET
                response = requests.get(
                    url,
                    timeout=self.timeout,
                    verify=False,  # Don't verify SSL for local dev
                    allow_redirects=True,
                )

                result.service_type = protocol
                result.protocol = protocol

                # Try to find health endpoint
                for endpoint in self.HEALTH_ENDPOINTS:
                    try:
                        health_url = urljoin(url, endpoint)
                        health_response = requests.get(
                            health_url, timeout=self.timeout, verify=False
                        )
                        if health_response.status_code in [200, 204]:
                            result.health_endpoint = endpoint
                            break
                    except:
                        continue

                return True

            except requests.exceptions.RequestException:
                continue

        return False

    async def _try_grpc_detection(self, host: str, port: int, result: PortScanResult) -> bool:
        """Try to detect gRPC service.

        Args:
            host: Host
            port: Port
            result: PortScanResult to update

        Returns:
            True if gRPC detected, False otherwise
        """
        # gRPC uses HTTP/2, so we check for HTTP/2 upgrade headers
        # This is a simplified check

        try:
            import grpc

            # Try to create a channel
            target = f"{host}:{port}"
            channel = grpc.insecure_channel(target)

            # Try to get channel state
            state = channel.get_state(try_to_connect=True)

            # Wait a bit for connection
            await asyncio.sleep(0.5)

            state = channel.get_state()

            if state == grpc.ChannelConnectivity.READY:
                result.service_type = "grpc"
                result.protocol = "grpc"
                result.metadata["grpc_version"] = "unknown"
                channel.close()
                return True

            channel.close()

        except ImportError:
            # grpc not installed, skip gRPC detection
            pass
        except Exception:
            pass

        return False

    def get_process_on_port(self, port: int) -> Optional[Dict[str, Any]]:
        """Get process information for a port.

        Args:
            port: Port number

        Returns:
            Dictionary with process info or None
        """
        try:
            # Use lsof on Unix-like systems
            result = subprocess.run(
                ["lsof", "-i", f":{port}", "-P", "-n"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0 and result.stdout:
                lines = result.stdout.strip().split("\n")
                if len(lines) > 1:  # First line is header
                    # Parse the first data line
                    parts = lines[1].split()
                    if len(parts) >= 9:
                        return {
                            "command": parts[0],
                            "pid": parts[1],
                            "user": parts[2],
                            "fd": parts[3],
                            "type": parts[4],
                            "device": parts[5],
                            "size": parts[6],
                            "node": parts[7],
                            "name": parts[8],
                        }
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        # Try netstat as fallback
        try:
            result = subprocess.run(["netstat", "-tlnp"], capture_output=True, text=True, timeout=5)

            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if f":{port}" in line:
                        parts = line.split()
                        if len(parts) >= 7:
                            return {
                                "protocol": parts[0],
                                "local_address": parts[3],
                                "foreign_address": parts[4],
                                "state": parts[5],
                                "program": parts[6] if len(parts) > 6 else "unknown",
                            }
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return None


class ServiceObserver:
    """Observer that monitors and detects running services."""

    def __init__(self, project_root: Path):
        """Initialize observer.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root
        self.port_scanner = PortScanner()
        self.detected_services: List[DetectedService] = []
        self.docker_containers: List[DockerContainer] = []

    async def observe(
        self,
        hosts: Optional[List[str]] = None,
        scan_docker: bool = True,
        cross_reference: bool = True,
    ) -> Dict[str, Any]:
        """Run observation and detect all services.

        Args:
            hosts: List of hosts to scan (defaults to localhost)
            scan_docker: Whether to scan Docker containers
            cross_reference: Whether to cross-reference with project code

        Returns:
            Dictionary with all detection results
        """
        if hosts is None:
            hosts = ["localhost", "127.0.0.1"]

        print(f"🔍 Observing project: {self.project_root}")
        print(f"   Hosts: {', '.join(hosts)}\n")

        results = {
            "hosts_scanned": [],
            "services_detected": [],
            "docker_containers": [],
            "dockerfile_found": None,
            "cross_references": [],
            "suggestions": [],
        }

        # 1. Scan ports on each host
        print("📡 Scanning for open ports...")
        for host in hosts:
            open_ports = await self.port_scanner.scan_host(host)
            results["hosts_scanned"].append(
                {
                    "host": host,
                    "open_ports": [r.port for r in open_ports],
                    "services": len(open_ports),
                }
            )

            # Convert to detected services
            for port_result in open_ports:
                service = self._port_result_to_service(host, port_result)
                self.detected_services.append(service)

        print(f"   ✓ Found {len(self.detected_services)} running services\n")

        # 2. Scan Docker if available
        if scan_docker:
            print("🐳 Scanning Docker containers...")
            self.docker_containers = self._scan_docker_containers()
            results["docker_containers"] = [
                {
                    "name": c.name,
                    "image": c.image,
                    "ports": c.ports,
                    "status": c.status,
                }
                for c in self.docker_containers
            ]

            # Update services from Docker
            self._update_services_from_docker()

            print(f"   ✓ Found {len(self.docker_containers)} containers\n")

        # 3. Find Dockerfile and suggest setup
        docker_suggestion = self._find_docker_setup()
        if docker_suggestion:
            results["dockerfile_found"] = str(docker_suggestion.dockerfile_path)
            results["suggestions"].append(
                {
                    "type": "docker",
                    "message": f"Dockerfile found at {docker_suggestion.dockerfile_path}",
                    "can_auto_build": docker_suggestion.can_auto_build,
                    "command": docker_suggestion.suggested_command,
                }
            )

            print(f"🐳 Dockerfile found: {docker_suggestion.dockerfile_path}")
            if docker_suggestion.compose_path:
                print(f"   docker-compose: {docker_suggestion.compose_path}")
            print(f"   Suggested: {docker_suggestion.suggested_command}\n")

        # 4. Cross-reference with project code
        if cross_reference:
            print("🔗 Cross-referencing with project code...")
            cross_refs = self._cross_reference_with_code()
            results["cross_references"] = cross_refs

            for ref in cross_refs:
                print(f"   ✓ Matched: {ref['detected_service']} → {ref['code_service']}")

        results["services_detected"] = [
            {
                "name": s.name,
                "url": s.base_url,
                "type": s.service_type,
                "health": s.health_endpoint,
                "confidence": s.confidence,
            }
            for s in self.detected_services
        ]

        return results

    def _port_result_to_service(self, host: str, result: PortScanResult) -> DetectedService:
        """Convert PortScanResult to DetectedService.

        Args:
            host: Host
            result: Port scan result

        Returns:
            DetectedService
        """
        protocol = result.service_type or "http"
        base_url = f"{protocol}://{host}:{result.port}"

        # Try to get process info
        process_info = self.port_scanner.get_process_on_port(result.port)

        # Generate service name from process or port
        if process_info:
            name = process_info.get("command", f"service-{result.port}")
        else:
            name = f"service-{protocol}-{result.port}"

        return DetectedService(
            name=name,
            host=host,
            port=result.port,
            base_url=base_url,
            service_type=protocol,
            health_endpoint=result.health_endpoint,
            detected_from="scan",
            confidence=0.8 if result.service_type else 0.5,
            process_info=process_info,
        )

    def _scan_docker_containers(self) -> List[DockerContainer]:
        """Scan for running Docker containers.

        Returns:
            List of Docker containers
        """
        containers = []

        try:
            # Get running containers
            result = subprocess.run(
                [
                    "docker",
                    "ps",
                    "--format",
                    "{{.ID}}|{{.Names}}|{{.Image}}|{{.Ports}}|{{.Status}}",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    if not line or "|" not in line:
                        continue

                    parts = line.split("|")
                    if len(parts) >= 5:
                        container_id = parts[0]
                        name = parts[1]
                        image = parts[2]
                        ports_str = parts[3]
                        status = parts[4]

                        # Parse ports
                        ports = self._parse_docker_ports(ports_str)

                        containers.append(
                            DockerContainer(
                                container_id=container_id,
                                name=name,
                                image=image,
                                ports=ports,
                                status=status,
                            )
                        )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return containers

    def _parse_docker_ports(self, ports_str: str) -> List[Dict[str, Any]]:
        """Parse Docker ports string.

        Args:
            ports_str: Docker ports string (e.g., "0.0.0.0:8080->8080/tcp")

        Returns:
            List of port dictionaries
        """
        ports = []

        if not ports_str or ports_str.strip() == "":
            return ports

        # Parse format like "0.0.0.0:8080->8080/tcp, 0.0.0.0:8443->8443/tcp"
        for port_mapping in ports_str.split(","):
            port_mapping = port_mapping.strip()

            if "->" in port_mapping:
                # Format: host_ip:host_port->container_port/protocol
                parts = port_mapping.split("->")
                if len(parts) == 2:
                    host_part = parts[0]
                    container_part = parts[1]

                    # Extract host port
                    if ":" in host_part:
                        host_port = host_part.split(":")[-1]
                    else:
                        host_port = host_part

                    # Extract container port and protocol
                    if "/" in container_part:
                        container_port, protocol = container_part.split("/")
                    else:
                        container_port = container_part
                        protocol = "tcp"

                    try:
                        ports.append(
                            {
                                "public": int(host_port),
                                "private": int(container_port),
                                "type": protocol,
                            }
                        )
                    except ValueError:
                        continue

        return ports

    def _update_services_from_docker(self) -> None:
        """Update detected services with Docker container information."""
        for container in self.docker_containers:
            for port_mapping in container.ports:
                public_port = port_mapping.get("public")

                # Check if we already detected this port
                existing = next((s for s in self.detected_services if s.port == public_port), None)

                if existing:
                    # Update with Docker info
                    existing.name = container.name
                    existing.detected_from = "docker"
                    existing.confidence = 0.95
                else:
                    # Create new service from Docker
                    service = DetectedService(
                        name=container.name,
                        host="localhost",
                        port=public_port,
                        base_url=f"http://localhost:{public_port}",
                        service_type="http",
                        detected_from="docker",
                        confidence=0.9,
                    )
                    self.detected_services.append(service)

    def _find_docker_setup(self) -> Optional[DockerSetupSuggestion]:
        """Find Dockerfile and docker-compose in project.

        Returns:
            DockerSetupSuggestion if found, None otherwise
        """
        dockerfile_path = None
        compose_path = None

        # Look for Dockerfile
        for dockerfile_name in ["Dockerfile", "dockerfile", "Dockerfile.dev"]:
            path = self.project_root / dockerfile_name
            if path.exists():
                dockerfile_path = path
                break

        # Look for docker-compose
        for compose_name in [
            "docker-compose.yml",
            "docker-compose.yaml",
            "compose.yml",
            "compose.yaml",
        ]:
            path = self.project_root / compose_name
            if path.exists():
                compose_path = path
                break

        if not dockerfile_path and not compose_path:
            return None

        # Determine command
        if compose_path:
            suggested_command = f"docker-compose -f {compose_path.name} up -d"
            can_auto_build = True

            # Parse services from compose
            services = self._parse_compose_services(compose_path)
        elif dockerfile_path:
            suggested_command = f"docker build -t {self.project_root.name} -f {dockerfile_path.name} . && docker run -d {self.project_root.name}"
            can_auto_build = True
            services = []
        else:
            suggested_command = ""
            can_auto_build = False
            services = []

        return DockerSetupSuggestion(
            dockerfile_path=dockerfile_path or Path(""),
            compose_path=compose_path,
            suggested_command=suggested_command,
            can_auto_build=can_auto_build,
            build_time_estimate="1-3 minutes",
            services_in_compose=services,
        )

    def _parse_compose_services(self, compose_path: Path) -> List[str]:
        """Parse services from docker-compose file.

        Args:
            compose_path: Path to docker-compose file

        Returns:
            List of service names
        """
        try:
            import yaml

            with open(compose_path, "r") as f:
                compose = yaml.safe_load(f)

            services = compose.get("services", {})
            return list(services.keys())
        except Exception:
            return []

    def _cross_reference_with_code(self) -> List[Dict[str, Any]]:
        """Cross-reference detected services with project code.

        Returns:
            List of cross-reference results
        """
        cross_refs = []

        # Load project manifest if available
        manifest_path = self.project_root / "project_knowledge.json"
        if not manifest_path.exists():
            return cross_refs

        try:
            import json

            with open(manifest_path, "r") as f:
                manifest = json.load(f)

            services_in_code = manifest.get("services", [])

            for detected in self.detected_services:
                # Try to match by port
                for code_service in services_in_code:
                    ports_in_code = [p.get("port") for p in code_service.get("ports", [])]

                    if detected.port in ports_in_code:
                        detected.matched_code_service = code_service.get("name")
                        detected.confidence = 1.0

                        cross_refs.append(
                            {
                                "detected_service": detected.name,
                                "code_service": code_service.get("name"),
                                "port": detected.port,
                                "confidence": 1.0,
                            }
                        )
                        break
        except Exception:
            pass

        return cross_refs

    async def auto_setup(self, dry_run: bool = True) -> Dict[str, Any]:
        """Automatically setup the environment using Docker.

        Args:
            dry_run: If True, only show what would be done

        Returns:
            Dictionary with setup results
        """
        suggestion = self._find_docker_setup()

        if not suggestion:
            return {
                "success": False,
                "message": "No Dockerfile or docker-compose found",
            }

        if not suggestion.can_auto_build:
            return {
                "success": False,
                "message": "Cannot auto-build with current configuration",
            }

        if dry_run:
            return {
                "success": True,
                "dry_run": True,
                "message": "Would execute:",
                "command": suggestion.suggested_command,
                "estimated_time": suggestion.build_time_estimate,
            }

        # Execute the build
        print("🚀 Auto-setting up environment...")
        print(f"   Command: {suggestion.suggested_command}\n")

        try:
            result = subprocess.run(
                suggestion.suggested_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd=str(self.project_root),
            )

            if result.returncode == 0:
                return {
                    "success": True,
                    "message": "Build successful",
                    "output": result.stdout,
                }
            else:
                return {
                    "success": False,
                    "message": "Build failed",
                    "error": result.stderr,
                }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "message": "Build timed out after 5 minutes",
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Build error: {str(e)}",
            }
