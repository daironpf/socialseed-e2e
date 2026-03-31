"""
Service Port Detector - ISSUE-004
Automatically detects running services and their ports.
"""

import json
import socket
import subprocess
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

import httpx


@dataclass
class DetectedService:
    """A detected service."""
    name: str
    port: int
    protocol: str
    status: str
    process_name: Optional[str] = None
    container_id: Optional[str] = None
    health_endpoint: Optional[str] = None
    response_time_ms: float = 0.0


class PortScanner:
    """Scans for open ports and detects services."""
    
    COMMON_PORTS = {
        3000: "nodejs",
        3001: "nodejs-alt",
        5000: "flask",
        5432: "postgresql",
        5433: "postgresql-alt",
        6379: "redis",
        8000: "fastapi",
        8080: "spring-boot",
        8085: "spring-boot-alt",
        8090: "spring-alt",
        27017: "mongodb",
    }
    
    def __init__(self):
        self._services: List[DetectedService] = []
        self._lock = threading.Lock()
    
    def scan_ports(
        self,
        start_port: int = 3000,
        end_port: int = 9000,
        hosts: List[str] = None,
    ) -> List[DetectedService]:
        """Scan a range of ports for open services."""
        hosts = hosts or ["localhost", "127.0.0.1"]
        services = []
        
        def check_port(host: str, port: int) -> Optional[DetectedService]:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((host, port))
                sock.close()
                
                if result == 0:
                    service_name = self.COMMON_PORTS.get(port, f"unknown-{port}")
                    return DetectedService(
                        name=service_name,
                        port=port,
                        protocol="http",
                        status="running",
                    )
            except:
                pass
            return None
        
        with threading.ThreadPoolExecutor(max_workers=50) as executor:
            futures = []
            for host in hosts:
                for port in range(start_port, end_port + 1):
                    futures.append(executor.submit(check_port, host, port))
            
            for future in futures:
                result = future.result()
                if result:
                    services.append(result)
        
        with self._lock:
            self._services = services
        
        return services
    
    def check_health(
        self,
        service: DetectedService,
    ) -> Dict[str, Any]:
        """Check if a service has a health endpoint."""
        health_paths = ["/health", "/actuator/health", "/api/health", "/status"]
        
        for path in health_paths:
            try:
                start = datetime.now()
                response = httpx.get(
                    f"http://localhost:{service.port}{path}",
                    timeout=3.0,
                )
                duration = (datetime.now() - start).total_seconds() * 1000
                
                if response.status_code < 400:
                    service.health_endpoint = path
                    service.response_time_ms = duration
                    return {
                        "healthy": True,
                        "endpoint": path,
                        "response_time_ms": duration,
                    }
            except:
                pass
        
        return {"healthy": False}
    
    def detect_docker_services(self) -> List[DetectedService]:
        """Detect running Docker containers."""
        services = []
        
        try:
            result = subprocess.run(
                ["docker", "ps", "--format", "{{.ID}}|{{.Names}}|{{.Ports}}"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    if not line:
                        continue
                    
                    parts = line.split("|")
                    if len(parts) >= 2:
                        container_id = parts[0]
                        container_name = parts[1]
                        
                        port = 0
                        if len(parts) >= 3 and ":" in parts[2]:
                            port_str = parts[2].split(":")[-1].split("-")[0]
                            try:
                                port = int(port_str)
                            except:
                                pass
                        
                        if port > 0:
                            services.append(DetectedService(
                                name=container_name,
                                port=port,
                                protocol="http",
                                status="running",
                                container_id=container_id,
                            ))
        except Exception as e:
            print(f"Docker detection failed: {e}")
        
        return services
    
    def detect_all(self) -> List[DetectedService]:
        """Detect all services (ports + Docker)."""
        port_services = self.scan_ports()
        docker_services = self.detect_docker_services()
        
        all_services = {s.port: s for s in port_services}
        
        for s in docker_services:
            if s.port not in all_services:
                all_services[s.port] = s
            else:
                all_services[s.port].container_id = s.container_id
        
        for service in all_services.values():
            self.check_health(service)
        
        return list(all_services.values())


class ServiceConfigGenerator:
    """Generates e2e.conf from detected services."""
    
    def __init__(self):
        self.detector = PortScanner()
    
    def generate_config(
        self,
        services: List[DetectedService],
    ) -> Dict[str, Dict[str, Any]]:
        """Generate configuration for detected services."""
        config = {}
        
        for service in services:
            service_name = self._infer_service_name(service)
            
            config[service_name] = {
                "base_url": f"http://localhost:{service.port}",
                "port": service.port,
                "health_endpoint": service.health_endpoint or "/health",
            }
        
        return config
    
    def _infer_service_name(self, service: DetectedService) -> str:
        """Infer service name from port or container name."""
        name = service.name.lower()
        
        if "postgresql" in name or "5432" in str(service.port):
            return "database"
        if "redis" in name or "6379" in str(service.port):
            return "cache"
        if "mongo" in name or "27017" in str(service.port):
            return "mongodb"
        
        if "8085" in str(service.port):
            return "auth"
        if "8080" in str(service.port):
            return "api"
        
        return f"service_{service.port}"
    
    def save_config(
        self,
        config: Dict[str, Dict[str, Any]],
        output_path: str = "e2e.conf",
    ) -> None:
        """Save configuration to file."""
        config_json = {
            "version": "1.0",
            "generated_at": datetime.now().isoformat(),
            "services": config,
        }
        
        with open(output_path, "w") as f:
            json.dump(config_json, f, indent=2)
        
        print(f"Configuration saved to {output_path}")


def detect_and_configure() -> Dict[str, Any]:
    """Main function to detect services and generate config."""
    detector = PortScanner()
    generator = ServiceConfigGenerator()
    
    print("🔍 Scanning for services...")
    services = detector.detect_all()
    
    print(f"✅ Found {len(services)} services")
    
    for s in services:
        health_status = "✓" if s.health_endpoint else "✗"
        print(f"  - {s.name} (port {s.port}) {health_status}")
    
    config = generator.generate_config(services)
    generator.save_config(config)
    
    return config


_global_detector: Optional[PortScanner] = None


def get_port_detector() -> PortScanner:
    """Get global port detector."""
    global _global_detector
    if _global_detector is None:
        _global_detector = PortScanner()
    return _global_detector
