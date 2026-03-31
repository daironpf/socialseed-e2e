"""gRPC services scanner for extracting protobuf definitions.

This module parses .proto files, detects gRPC services and methods,
identifies streaming types, and generates client code examples.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class GrpcMethod:
    """Represents a gRPC method."""

    name: str
    input_type: str
    output_type: str
    streaming: str  # "none", "client", "server", "bidirectional"
    description: str = ""
    file_path: Optional[str] = None
    line_number: int = 0


@dataclass
class GrpcMessage:
    """Represents a protobuf message."""

    name: str
    fields: List[Dict[str, Any]] = field(default_factory=list)
    file_path: Optional[str] = None


@dataclass
class GrpcService:
    """Represents a gRPC service."""

    name: str
    methods: List[GrpcMethod] = field(default_factory=list)
    package: str = ""
    file_path: Optional[str] = None
    proto_file: Optional[str] = None


@dataclass
class GrpcInfo:
    """Represents detected gRPC information."""

    services: List[GrpcService] = field(default_factory=list)
    messages: List[GrpcMessage] = field(default_factory=list)
    authentication: Dict[str, str] = field(default_factory=dict)


class GrpcScanner:
    """Scans source code to extract gRPC services."""

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def scan(self) -> GrpcInfo:
        """Scan project and return gRPC information."""
        info = GrpcInfo()

        self._parse_proto_files(info)
        self._detect_grpc_services(info)
        self._detect_authentication(info)

        return info

    def _parse_proto_files(self, info: GrpcInfo) -> None:
        """Parse .proto files."""
        proto_files = list(self.project_root.rglob("*.proto"))

        for proto_file in proto_files:
            content = proto_file.read_text(errors="ignore")
            lines = content.split("\n")

            package = ""
            in_service = False
            current_service = None
            in_message = False
            current_message = None

            for line_num, line in enumerate(lines, 1):
                line = line.strip()

                package_match = re.match(r"package\s+([^;]+);", line)
                if package_match:
                    package = package_match.group(1).strip()

                syntax_match = re.match(r'syntax\s*=\s*["\'](\d+\.\d+)["\'];', line)
                if syntax_match:
                    continue

                service_match = re.match(r"service\s+(\w+)\s*\{", line)
                if service_match:
                    in_service = True
                    current_service = GrpcService(
                        name=service_match.group(1),
                        package=package,
                        file_path=str(proto_file),
                        proto_file=str(proto_file.name),
                    )
                    continue

                if in_service and line == "}":
                    in_service = False
                    if current_service:
                        info.services.append(current_service)
                        current_service = None
                    continue

                if in_service:
                    method_match = re.match(
                        r"rpc\s+(\w+)\s*\((.*?)\)\s*returns\s*\((.*?)\);",
                        line
                    )
                    if method_match:
                        method_name = method_match.group(1)
                        input_type = method_match.group(2)
                        output_type = method_match.group(3)

                        streaming = "none"
                        if "stream" in input_type:
                            streaming = "client"
                        if "stream" in output_type:
                            if streaming == "client":
                                streaming = "bidirectional"
                            else:
                                streaming = "server"

                        current_service.methods.append(GrpcMethod(
                            name=method_name,
                            input_type=input_type.replace("stream ", "").strip(),
                            output_type=output_type.replace("stream ", "").strip(),
                            streaming=streaming,
                            file_path=str(proto_file),
                            line_number=line_num,
                        ))

                message_match = re.match(r"message\s+(\w+)\s*\{", line)
                if message_match:
                    in_message = True
                    current_message = GrpcMessage(
                        name=message_match.group(1),
                        file_path=str(proto_file),
                    )
                    continue

                if in_message and line == "}":
                    in_message = False
                    if current_message:
                        info.messages.append(current_message)
                        current_message = None
                    continue

                if in_message:
                    field_match = re.match(
                        r"(repeated\s+)?(\w+)\s+(\w+)\s*=\s*(\d+)(.*);",
                        line
                    )
                    if field_match:
                        field_info = {
                            "type": field_match.group(2),
                            "name": field_match.group(3),
                            "number": field_match.group(4),
                            "repeated": bool(field_match.group(1)),
                        }
                        current_message.fields.append(field_info)

    def _detect_grpc_services(self, info: GrpcInfo) -> None:
        """Detect gRPC service implementations."""
        patterns = [
            r"grpc\.server",
            r"add_\w+Servicer_to_server",
            r"class.*Servicer",
            r"@grpc\.unary",
            r"@grpc.stream",
            r"def.*handler.*grpc",
        ]

        for ext in [".py", ".js", ".ts", ".go", ".java"]:
            for file_path in self.project_root.rglob(f"*{ext}"):
                try:
                    content = file_path.read_text(errors="ignore")
                    for pattern in patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            info.services.append(GrpcService(
                                name=file_path.stem.replace("_servicer", "").replace("Servicer", ""),
                                file_path=str(file_path),
                            ))
                            break
                except Exception:
                    pass

    def _detect_authentication(self, info: GrpcInfo) -> None:
        """Detect gRPC authentication methods."""
        for ext in [".py", ".js", ".ts"]:
            for file_path in self.project_root.rglob(f"*{ext}"):
                try:
                    content = file_path.read_text(errors="ignore")

                    if "ssl" in content.lower() or "tls" in content.lower():
                        info.authentication["TLS"] = "SSL/TLS encryption detected"

                    if "jwt" in content.lower() or "bearer" in content.lower():
                        info.authentication["JWT"] = "JWT token in metadata detected"

                    if "oauth" in content.lower():
                        info.authentication["OAuth2"] = "OAuth2 authentication detected"
                except Exception:
                    pass


def generate_grpc_doc(project_root: Path, output_path: Optional[Path] = None) -> str:
    """Generate GRPC_SERVICES.md document."""
    scanner = GrpcScanner(project_root)
    info = scanner.scan()

    doc = "# Servicios gRPC\n\n"

    for service in info.services:
        doc += f"## {service.name}\n\n"
        doc += f"- Package: `{service.package}`\n"
        if service.proto_file:
            doc += f"- Proto: `{service.proto_file}`\n"
        doc += f"- File: `{service.file_path or 'N/A'}`\n\n"

        if service.methods:
            doc += "### Métodos\n\n"
            for method in service.methods:
                doc += f"#### {method.name}\n"
                doc += f"- Input: `{method.input_type}`\n"
                doc += f"- Output: `{method.output_type}`\n"
                doc += f"- Streaming: `{method.streaming}`\n"
                doc += f"- Line: `{method.line_number}`\n\n"

                streaming_desc = {
                    "none": "Unary call",
                    "client": "Client streaming",
                    "server": "Server streaming",
                    "bidirectional": "Bidirectional streaming",
                }.get(method.streaming, "")

                if streaming_desc:
                    doc += f"**{streaming_desc}**\n\n"

    if info.messages:
        doc += "## Mensajes/Types\n\n"
        for msg in info.messages:
            doc += f"### {msg.name}\n\n"
            if msg.fields:
                doc += "| Campo | Tipo | Número |\n"
                doc += "|-------|------|--------|\n"
                for field in msg.fields:
                    type_str = field["type"]
                    if field["repeated"]:
                        type_str = f"repeated {type_str}"
                    doc += f"| {field['name']} | {type_str} | {field['number']} |\n"
            doc += "\n"

    if info.authentication:
        doc += "## Autenticación\n\n"
        for auth_type, description in info.authentication.items():
            doc += f"- **{auth_type}**: {description}\n"
        doc += "\n"

    doc += "## Ejemplo de Cliente Python\n\n"
    doc += "```python\n"
    doc += "import grpc\n"
    doc += "import {service}_pb2\n"
    doc += "import {service}_pb2_grpc\n\n"
    doc += "channel = grpc.insecure_channel('localhost:50051')\n"
    doc += "stub = {service}_pb2_grpc.{service}Stub(channel)\n\n"
    doc += "# Ejemplo de llamada\n"
    doc += "# response = stub.{method}({service}_pb2.{method}Request(...))\n"
    doc += "```\n"

    if output_path:
        output_path.write_text(doc)

    return doc


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        project_root = Path(sys.argv[1])
        print(generate_grpc_doc(project_root))
    else:
        print("Usage: python grpc_scanner.py <project_root>")
