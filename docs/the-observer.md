# The Observer - Auto-Detect Running Services (Issue #186)

## Overview

**The Observer** is an intelligent service detection system that automatically scans for running APIs, identifies open ports, detects HTTP/gRPC services, and cross-references with your project code to confirm where services are hosted.

## Features

### 🔍 Active Port Scanning
- Scans common API ports (8000, 8080, 3000, 5000, etc.)
- Detects HTTP and HTTPS services
- Detects gRPC services
- Measures response times
- Tests multiple health endpoints

### 🐳 Docker Integration
- Discovers running Docker containers
- Maps container ports to host ports
- Suggests Docker build commands
- Auto-setup with `--auto-setup` flag

### 🔗 Cross-Reference
- Matches detected services with project code
- Validates port configurations from manifest
- Confirms service identity with high confidence

### 🚀 Auto-Setup
- Detects Dockerfile and docker-compose.yml
- Suggests build commands
- Can auto-execute Docker builds
- Estimates build time

## Installation

The Observer is included with socialseed-e2e. No additional installation required.

```bash
pip install socialseed-e2e
```

Optional dependencies for better gRPC detection:
```bash
pip install grpcio  # For gRPC service detection
```

## Quick Start

### Basic Usage

```bash
# Navigate to your project
cd /path/to/your/project

# Run observer
e2e observe
```

### Scan Specific Hosts

```bash
# Scan localhost (default)
e2e observe

# Scan specific hosts
e2e observe --host 192.168.1.100 --host 10.0.0.5

# Scan Docker network
e2e observe --host host.docker.internal
```

### Custom Port Range

```bash
# Scan specific port range
e2e observe --ports 8000-9000

# Scan multiple specific ports
e2e observe --ports 8080,3000,5000,9000
```

### Auto-Setup with Docker

```bash
# Preview what would be built
e2e observe --auto-setup --dry-run

# Actually build and run
e2e observe --auto-setup
```

## How It Works

### 1. Port Scanning

```python
from socialseed_e2e.project_manifest import PortScanner
import asyncio

async def scan():
    scanner = PortScanner(timeout=2.0)

    # Scan localhost
    results = await scanner.scan_host("localhost")

    for result in results:
        print(f"Port {result.port}: {result.service_type}")
        print(f"  Response time: {result.response_time_ms}ms")
        print(f"  Health endpoint: {result.health_endpoint}")

asyncio.run(scan())
```

### 2. Service Observation

```python
from socialseed_e2e.project_manifest import ServiceObserver
import asyncio

async def observe():
    observer = ServiceObserver("/path/to/project")

    results = await observer.observe(
        hosts=["localhost", "127.0.0.1"],
        scan_docker=True,
        cross_reference=True,
    )

    # Access detected services
    for service in observer.detected_services:
        print(f"Service: {service.name}")
        print(f"  URL: {service.base_url}")
        print(f"  Type: {service.service_type}")
        print(f"  From: {service.detected_from}")

asyncio.run(observe())
```

### 3. Docker Auto-Setup

```python
from socialseed_e2e.project_manifest import ServiceObserver
import asyncio

async def setup():
    observer = ServiceObserver("/path/to/project")

    # Check if Docker setup is available
    suggestion = observer._find_docker_setup()

    if suggestion:
        print(f"Dockerfile: {suggestion.dockerfile_path}")
        print(f"Command: {suggestion.suggested_command}")
        print(f"Can auto-build: {suggestion.can_auto_build}")

    # Auto-setup (dry run)
    result = await observer.auto_setup(dry_run=True)
    print(result)

    # Actually build
    result = await observer.auto_setup(dry_run=False)
    print(result)

asyncio.run(setup())
```

## CLI Reference

### `e2e observe`

**Syntax:**
```bash
e2e observe [DIRECTORY] [OPTIONS]
```

**Arguments:**
- `DIRECTORY`: Project directory to observe (default: current directory)

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--host` | `-h` | Hosts to scan (multiple allowed) | localhost, 127.0.0.1 |
| `--ports` | `-p` | Port range (e.g., 8000-9000 or 8080,3000) | Common API ports |
| `--docker` | | Scan Docker containers | Enabled |
| `--no-docker` | | Skip Docker scanning | |
| `--cross-ref` | | Cross-reference with code | Enabled |
| `--no-cross-ref` | | Skip cross-reference | |
| `--auto-setup` | | Auto-build Docker containers | Disabled |
| `--dry-run` | | Preview without executing | Disabled |
| `--timeout` | `-t` | Scan timeout in seconds | 2.0 |

**Examples:**

```bash
# Basic scan
e2e observe

# Scan specific directory
e2e observe /path/to/project

# Scan remote host
e2e observe --host 192.168.1.100

# Scan multiple hosts
e2e observe --host host1 --host host2 --host host3

# Custom port range
e2e observe --ports 8000-9000

# Specific ports
e2e observe --ports 8080,3000,5000

# No Docker scanning
e2e observe --no-docker

# Auto-setup environment
e2e observe --auto-setup

# Preview auto-setup
e2e observe --auto-setup --dry-run

# Faster scanning (lower timeout)
e2e observe --timeout 1.0

# Slower but more reliable
e2e observe --timeout 5.0
```

## Use Cases

### 1. Discover Running Services

When you inherit a project and don't know what services are running:

```bash
e2e observe

# Output:
# 🔭 The Observer - Service Detection
#    Project: /home/user/legacy-project
#    Hosts: localhost, 127.0.0.1
#
# 📡 Scanning for services...
#
# ✅ Services Detected:
#
# ┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━┳━━━━━━━┳━━━━━━━━┓
# ┃ Service         ┃ URL                 ┃ Type ┃ Source┃ Health ┃
# ┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━╇━━━━━━━╇━━━━━━━━┩
# ┃ users-api       ┃ http://localhost:8080┃ HTTP ┃ docker┃ /health│
# ┃ payment-service ┃ http://localhost:3000┃ HTTP ┃ scan  ┃ /ping  │
# ┃ notification-svc┃ http://localhost:5000┃ HTTP ┃ scan  ┃ N/A    │
# └─────────────────┴─────────────────────┴──────┴───────┴────────┘
```

### 2. Verify Docker Setup

Check if Docker containers are running correctly:

```bash
e2e observe --docker

# Output:
# 🐳 Docker Containers:
#
# ┏━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┓
# ┃ Name        ┃ Image              ┃ Ports     ┃ Status          ┃
# ┡━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━┩
# ┃ users-api   ┃ myapp/users:latest ┃ 8080->8080┃ Up 2 hours      │
# ┃ postgres-db ┃ postgres:14        ┃ 5432->5432┃ Up 2 hours      │
# ┃ redis-cache ┃ redis:alpine       ┃ 6379->6379┃ Up 2 hours      │
# └─────────────┴────────────────────┴───────────┴─────────────────┘
```

### 3. Auto-Setup Development Environment

One-command setup for new developers:

```bash
# Check what would be built
e2e observe --auto-setup --dry-run

# Output:
# 🐳 Docker Setup:
#    Dockerfile: /home/user/project/Dockerfile
#    docker-compose: /home/user/project/docker-compose.yml
#
#    Dockerfile found at /home/user/project/Dockerfile
#    Command: docker-compose -f docker-compose.yml up -d
#
# 🚀 Auto-setting up environment...
#    Command: docker-compose -f docker-compose.yml up -d
#
#    ✅ Setup successful!
```

### 4. Cross-Reference with Code

Match running services with code:

```bash
e2e observe --cross-ref

# Output:
# 🔗 Cross-References:
#    ✓ service-8080 matches users-api (port 8080)
#    ✓ service-3000 matches payment-service (port 3000)
```

## API Reference

### PortScanner

```python
class PortScanner:
    def __init__(self, timeout: float = 2.0, max_workers: int = 50)

    async def scan_host(
        self,
        host: str,
        ports: Optional[List[int]] = None,
        detect_protocols: bool = True
    ) -> List[PortScanResult]
```

### ServiceObserver

```python
class ServiceObserver:
    def __init__(self, project_root: Path)

    async def observe(
        self,
        hosts: Optional[List[str]] = None,
        scan_docker: bool = True,
        cross_reference: bool = True
    ) -> Dict[str, Any]

    async def auto_setup(self, dry_run: bool = True) -> Dict[str, Any]
```

### Data Classes

```python
@dataclass
class PortScanResult:
    port: int
    is_open: bool
    protocol: str
    service_type: Optional[str]  # 'http', 'grpc', 'unknown'
    response_time_ms: Optional[float]
    health_endpoint: Optional[str]

@dataclass
class DetectedService:
    name: str
    host: str
    port: int
    base_url: str
    service_type: str
    health_endpoint: Optional[str]
    detected_from: str  # 'scan', 'docker', 'config', 'code'
    confidence: float

@dataclass
class DockerSetupSuggestion:
    dockerfile_path: Path
    compose_path: Optional[Path]
    suggested_command: str
    can_auto_build: bool
    build_time_estimate: str
    services_in_compose: List[str]
```

## Configuration

### Environment Variables

```bash
# Default timeout for port scanning
export E2E_OBSERVER_TIMEOUT=2.0

# Default hosts to scan
export E2E_OBSERVER_HOSTS="localhost,127.0.0.1"

# Docker command preference
export E2E_DOCKER_CMD="docker"  # or "podman"
```

### Common Ports Scanned

By default, The Observer scans these ports:

- **HTTP APIs**: 8000, 8080, 8443, 3000, 5000, 9000, 10000
- **gRPC**: 50051, 50052, 50053, 50054, 50055
- **Standard**: 80, 443

You can customize with `--ports` flag.

## Troubleshooting

### "No services detected"

**Problem**: Observer doesn't find any services.

**Solutions:**
1. Check if services are actually running:
   ```bash
   curl http://localhost:8080/health
   ```

2. Try scanning more ports:
   ```bash
   e2e observe --ports 3000-10000
   ```

3. Increase timeout for slow services:
   ```bash
   e2e observe --timeout 5.0
   ```

### "Docker command not found"

**Problem**: Docker is not installed or not in PATH.

**Solution:**
```bash
# Install Docker
# Or use without Docker scanning:
e2e observe --no-docker
```

### "Permission denied scanning ports"

**Problem**: Not enough permissions to scan ports.

**Solutions:**
1. Run with appropriate permissions
2. Scan only higher ports (above 1024):
   ```bash
   e2e observe --ports 8000-9000
   ```

### "gRPC detection not working"

**Problem**: gRPC services not being detected.

**Solution:**
```bash
# Install grpcio
pip install grpcio

# Or manually specify port:
e2e observe --ports 50051,50052
```

## Best Practices

### 1. Use in CI/CD

```yaml
# .github/workflows/detect-services.yml
- name: Detect Services
  run: |
    e2e observe --timeout 5.0
```

### 2. Document Discovered Services

```bash
# Save results to file
e2e observe > services.txt

# Or use in scripts
SERVICES=$(e2e observe --format json)
```

### 3. Integration with Tests

```python
# conftest.py
import pytest
from socialseed_e2e.project_manifest import ServiceObserver

@pytest.fixture(scope="session")
def running_services():
    observer = ServiceObserver(".")
    asyncio.run(observer.observe())
    return observer.detected_services

def test_services_running(running_services):
    assert len(running_services) > 0, "No services detected"
```

## Examples

### Example 1: Microservices Environment

```bash
# Project with multiple services
e2e observe --host localhost

# Output:
# ✅ Services Detected:
#    users-api       : http://localhost:8080  (Docker)
#    payment-service : http://localhost:3000  (Docker)
#    notification-svc: http://localhost:5000  (Process)
#    redis           : localhost:6379         (Docker)
#    postgres        : localhost:5432         (Docker)
```

### Example 2: New Developer Setup

```bash
# Clone project
git clone https://github.com/company/project.git
cd project

# One command to setup
e2e observe --auto-setup

# Output:
# 🔭 The Observer
# 🐳 Building Docker containers...
# ✅ Build successful
# 📡 Services ready:
#    - API: http://localhost:8080
#    - DB: localhost:5432
```

### Example 3: Troubleshooting

```bash
# Check if specific service is running
e2e observe --ports 8080

# Debug with verbose output
e2e observe --timeout 10.0
```

## Future Enhancements

Planned improvements for Issue #186:

- [ ] Kubernetes pod detection
- [ ] Service mesh integration (Istio, Linkerd)
- [ ] Cloud provider discovery (AWS, GCP, Azure)
- [ ] Service dependency graph generation
- [ ] Health check aggregation
- [ ] Network latency measurement
- [ ] SSL/TLS certificate validation

## Contributing

To contribute to The Observer:

1. Fork the repository
2. Create a feature branch
3. Add tests for new detection methods
4. Submit a pull request

See `tests/project_manifest/test_observer.py` for test examples.

## References

- Issue #186: Implement "The Observer" to auto-detect running services and ports
- Related: Issue #184 (Deep Scanner), Issue #185 (Autonomous Test Generation)
