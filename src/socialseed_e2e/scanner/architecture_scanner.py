"""Architecture scanner for detecting system architecture and technologies.

This module detects application architecture (monolith, microservices, serverless)
and identifies technologies used (frontend, backend, database, message queues).
"""

import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ArchitectureInfo:
    """Represents detected architecture information."""

    app_type: str = "unknown"
    detected_patterns: List[str] = field(default_factory=list)
    technologies: Dict[str, List[Dict[str, str]]] = field(default_factory=dict)
    services: List[Dict[str, Any]] = field(default_factory=list)
    dependencies: List[Dict[str, str]] = field(default_factory=list)
    diagram_mermaid: str = ""


class ArchitectureScanner:
    """Scans project to detect architecture and technologies."""

    FRAMEWORK_PATTERNS = {
        "backend": {
            "Spring Boot": [r"spring-boot-starter", r"@SpringBootApplication", r"@RestController"],
            "Express": [r"\"express\"", r"require\(['\"]express['\"]\)", r"const express = "],
            "FastAPI": [r"\"fastapi\"", r"from fastapi import", r"@app\.(get|post|put|delete)"],
            "Django": [r"\"django\"", r"from django import", r"urlpatterns"],
            "Flask": [r"\"flask\"", r"from flask import", r"@app\.route"],
            "NestJS": [r"@Controller\(\)", r"@Injectable\(\)", r"@Module\("],
            "Gin": [r"github.com/gin-gonic/gin", r"gin\.Engine", r"func.*gin\."],
            "ASP.NET": [r"\[ApiController\]", r"\[Route\(", r"ControllerBase"],
            "Rails": [r"gem 'rails'", r"class.*Controller < ApplicationController"],
            "Laravel": [r"use Illuminate", r"Route::", r"app/Http/Controllers"],
        },
        "frontend": {
            "React": [r"\"react\"", r"from 'react'", r"useState", r"jsx", r"tsx"],
            "Vue": [r"\"vue\"", r"from 'vue'", r"createApp", r"ref\(", r"\<template\>"],
            "Angular": [r"@Component\(", r"@NgModule", r"@Injectable\(", r"import.*@angular"],
            "Svelte": [r"\"svelte\"", r"from 'svelte'", r"export let", r"onMount"],
            "Next.js": [r"next", r"getServerSideProps", r"getStaticProps", r"app router"],
            "Nuxt": [r"\"nuxt\"", r"nuxt.config", r"asyncData"],
            "SvelteKit": [r"@sveltejs/kit", r"load\(", r"PageData"],
        },
        "database": {
            "PostgreSQL": [r"postgresql", r"pg", r"postgres", r"pg_hba.conf"],
            "MySQL": [r"mysql", r"mysqld", r"mysql2"],
            "MongoDB": [r"mongodb", r"mongoose", r"mongod"],
            "Redis": [r"redis", r"ioredis", r"redigo"],
            "SQLite": [r"sqlite", r"sqlite3"],
            "Neo4j": [r"neo4j", r"cypher", r"graph DB"],
            "Elasticsearch": [r"elasticsearch", r"@elastic"],
            "Cassandra": [r"cassandra", r"datastax"],
        },
        "message_queue": {
            "Kafka": [r"kafka", r"spring-kafka", r"kafka-python"],
            "RabbitMQ": [r"rabbitmq", r"amqp", r"pika"],
            "ActiveMQ": [r"activemq", r"jms"],
            "SQS": [r"aws-sdk.*sqs", r"SQS", r"AmazonSQS"],
            "Pub/Sub": [r"@google-cloud/pubsub", r"google-cloud-pubsub"],
        },
        "cache": {
            "Redis": [r"redis", r"ioredis"],
            "Memcached": [r"memcached", r"pymemcache"],
            "Ehcache": [r"ehcache"],
        },
    }

    ARCHITECTURE_INDICATORS = {
        "monolith": [
            r"single.*application",
            r"monolith",
            r"all-in-one",
            r"one.*project",
            r"modules\/",
            r"src\/main",
        ],
        "microservices": [
            r"services\/",
            r"microservice",
            r"docker-compose",
            r"kubernetes",
            r"k8s",
            r"@FeignClient",
            r"@PathVariable.*service",
            r"eureka",
            r"consul",
        ],
        "serverless": [
            r"serverless\.yml",
            r"serverless\.yaml",
            r"lambda",
            r"@Lambda",
            r"aws-lambda",
            r"cloud-function",
            r"azure-function",
            r"google-cloud-function",
        ],
    }

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def scan(self) -> ArchitectureInfo:
        """Scan project and return architecture information."""
        info = ArchitectureInfo()

        self._detect_technologies(info)
        self._detect_architecture_type(info)
        self._detect_services(info)
        self._detect_dependencies(info)
        self._generate_diagram(info)

        return info

    def _detect_technologies(self, info: ArchitectureInfo) -> None:
        """Detect technologies used in the project."""
        files_to_scan = self._get_source_files()

        for category, frameworks in self.FRAMEWORK_PATTERNS.items():
            detected = []
            for framework, patterns in frameworks.items():
                for file_path in files_to_scan:
                    content = file_path.read_text(errors="ignore")
                    for pattern in patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            detected.append({
                                "name": framework,
                                "file": str(file_path.relative_to(self.project_root)),
                            })
                            break
            if detected:
                info.technologies[category] = detected

    def _detect_architecture_type(self, info: ArchitectureInfo) -> None:
        """Detect architecture type (monolith, microservices, serverless)."""
        scores = {"monolith": 0, "microservices": 0, "serverless": 0}

        files_to_scan = self._get_source_files()
        config_files = list(self.project_root.glob("*"))
        config_files.extend(self.project_root.glob(".*"))

        for file_path in files_to_scan:
            content = file_path.read_text(errors="ignore")
            for arch_type, patterns in self.ARCHITECTURE_INDICATORS.items():
                for pattern in patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        scores[arch_type] += 1

        for cf in config_files:
            if cf.is_file():
                name = cf.name.lower()
                if "serverless" in name:
                    scores["serverless"] += 3
                if "docker-compose" in name or "docker-compose.yml" in name:
                    scores["microservices"] += 2
                if "dockerfile" in name:
                    scores["microservices"] += 1

        if scores:
            info.app_type = max(scores, key=scores.get)
            info.detected_patterns = [k for k, v in scores.items() if v > 0]

    def _detect_services(self, info: ArchitectureInfo) -> None:
        """Detect services in the project."""
        services_dir = self.project_root / "services"
        if services_dir.exists():
            for item in services_dir.iterdir():
                if item.is_dir() and not item.name.startswith("."):
                    port = self._detect_service_port(item)
                    info.services.append({
                        "name": item.name,
                        "path": str(item.relative_to(self.project_root)),
                        "port": port,
                    })

        src_services = self.project_root / "src"
        if src_services.exists():
            for item in src_services.iterdir():
                if item.is_dir() and not item.name.startswith("."):
                    if self._is_service_module(item):
                        port = self._detect_service_port(item)
                        info.services.append({
                            "name": item.name,
                            "path": str(item.relative_to(self.project_root)),
                            "port": port,
                        })

    def _detect_service_port(self, service_path: Path) -> Optional[int]:
        """Detect port used by a service."""
        patterns = [
            r"port[:\s=]+(\d+)",
            r"PORT[:\s=]+(\d+)",
            r"server.*port[:\s=]+(\d+)",
            r"@Value.*(\$\{.*port.*\})",
        ]

        for pattern in patterns:
            if (service_path / "src").exists():
                for f in (service_path / "src").rglob("*.py"):
                    content = f.read_text(errors="ignore")
                    match = re.search(pattern, content, re.IGNORECASE)
                    if match:
                        try:
                            return int(match.group(1))
                        except (ValueError, IndexError):
                            pass

        common_ports = [3000, 3001, 4000, 5000, 5173, 8080, 8081, 8085, 8090, 8000]
        for port in common_ports:
            if self._check_port(port):
                return port
        return None

    def _check_port(self, port: int) -> bool:
        """Check if a port is in use."""
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(("localhost", port))
        sock.close()
        return result == 0

    def _is_service_module(self, path: Path) -> bool:
        """Check if a directory is a service module."""
        if (path / "main.py").exists():
            return True
        if (path / "app.py").exists():
            return True
        if (path / "server.py").exists():
            return True
        return False

    def _detect_dependencies(self, info: ArchitectureInfo) -> None:
        """Detect external dependencies."""
        files = [
            self.project_root / "requirements.txt",
            self.project_root / "package.json",
            self.project_root / "pom.xml",
            self.project_root / "build.gradle",
            self.project_root / "go.mod",
            self.project_root / "Cargo.toml",
        ]

        for file_path in files:
            if file_path.exists():
                deps = self._parse_dependencies(file_path)
                info.dependencies.extend(deps)

    def _parse_dependencies(self, file_path: Path) -> List[Dict[str, str]]:
        """Parse dependencies from package manager files."""
        deps = []
        content = file_path.read_text(errors="ignore")

        if file_path.name == "requirements.txt":
            for line in content.split("\n"):
                line = line.strip()
                if line and not line.startswith("#"):
                    if "==" in line:
                        name, version = line.split("==", 1)
                        deps.append({"name": name.strip(), "version": version.strip(), "type": "pip"})
                    elif ">=" in line:
                        name, version = line.split(">=", 1)
                        deps.append({"name": name.strip(), "version": f">={version.strip()}", "type": "pip"})

        elif file_path.name == "package.json":
            try:
                data = json.loads(content)
                for dep_type in ["dependencies", "devDependencies"]:
                    if dep_type in data:
                        for name, version in data[dep_type].items():
                            deps.append({"name": name, "version": version, "type": "npm"})
            except json.JSONDecodeError:
                pass

        return deps

    def _get_source_files(self) -> List[Path]:
        """Get list of source files to scan."""
        extensions = [".py", ".js", ".ts", ".java", ".go", ".rs", ".cs"]
        files = []

        for ext in extensions:
            files.extend(self.project_root.rglob(f"*{ext}"))

        ignore_dirs = {"node_modules", ".git", "venv", "env", "__pycache__", "dist", "build", ".venv"}
        return [f for f in files if not any(ignored in f.parts for ignored in ignore_dirs)]

    def _generate_diagram(self, info: ArchitectureInfo) -> None:
        """Generate Mermaid diagram."""
        lines = ["graph TD"]

        for tech_category, techs in info.technologies.items():
            if techs:
                tech_names = ", ".join([t["name"] for t in techs])
                lines.append(f"    {tech_category.upper()}[{tech_category.upper()}: {tech_names}]")

        if info.services:
            lines.append("    CLIENT[Client]")
            for service in info.services:
                lines.append(f"    CLIENT --> {service['name'].upper().replace('-', '_')}")
                lines.append(f"    {service['name'].upper().replace('-', '_')}[{service['name']}]")
                if service.get("port"):
                    lines[-1] += f" :{service['port']}"

        info.diagram_mermaid = "\n".join(lines)


def generate_architecture_doc(project_root: Path, output_path: Optional[Path] = None) -> str:
    """Generate ARCHITECTURE.md document."""
    scanner = ArchitectureScanner(project_root)
    info = scanner.scan()

    doc = """# Arquitectura del Proyecto

## Tipo de Aplicación
"""
    doc += f"- [{'x' if info.app_type == 'monolith' else ' '}] Monolito\n"
    doc += f"- [{'x' if info.app_type == 'microservices' else ' '}] Microservicios\n"
    doc += f"- [{'x' if info.app_type == 'serverless' else ' '}] Serverless\n"

    doc += "\n## Tecnologías Detectadas\n"
    doc += "| Componente | Tecnología | Archivo |\n"
    doc += "|------------|------------|--------|\n"
    for category, techs in info.technologies.items():
        for tech in techs:
            doc += f"| {category} | {tech['name']} | `{tech.get('file', 'N/A')}` |\n"

    doc += "\n## Diagrama de Arquitectura\n"
    doc += "```mermaid\n" + info.diagram_mermaid + "\n```\n"

    if info.services:
        doc += "\n## Servicios\n"
        doc += "| Servicio | Puerto | Path |\n"
        doc += "|----------|--------|------|\n"
        for service in info.services:
            port = service.get("port", "N/A")
            doc += f"| {service['name']} | {port} | `{service['path']}` |\n"

    if output_path:
        output_path.write_text(doc)

    return doc


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        project_root = Path(sys.argv[1])
        print(generate_architecture_doc(project_root))
    else:
        print("Usage: python architecture_scanner.py <project_root>")
