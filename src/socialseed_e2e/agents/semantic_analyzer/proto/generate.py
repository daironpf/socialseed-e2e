"""Script to generate Python code from protobuf definitions."""

import subprocess
import sys
from pathlib import Path


def generate_proto():
    """Generate Python code from semantic_analyzer.proto."""
    proto_dir = Path(__file__).parent
    proto_file = proto_dir / "semantic_analyzer.proto"

    if not proto_file.exists():
        print(f"Error: Proto file not found at {proto_file}")
        sys.exit(1)

    print(f"Generating Python code from {proto_file}...")

    # Generate Python code using grpcio-tools
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "grpc_tools.protoc",
            f"--proto_path={proto_dir}",
            f"--python_out={proto_dir}",
            f"--grpc_python_out={proto_dir}",
            str(proto_file),
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"Error generating proto code: {result.stderr}")
        sys.exit(1)

    print("✓ Generated semantic_analyzer_pb2.py")
    print("✓ Generated semantic_analyzer_pb2_grpc.py")

    # Fix imports in generated files
    _fix_imports(proto_dir)

    print("✓ Fixed imports in generated files")


def _fix_imports(proto_dir: Path):
    """Fix imports in generated protobuf files."""
    # The generated files have relative imports that need to be fixed
    pb2_file = proto_dir / "semantic_analyzer_pb2.py"
    pb2_grpc_file = proto_dir / "semantic_analyzer_pb2_grpc.py"

    # Fix pb2_grpc imports
    if pb2_grpc_file.exists():
        content = pb2_grpc_file.read_text()
        # Replace relative import with absolute
        content = content.replace(
            "import semantic_analyzer_pb2 as",
            "from socialseed_e2e.agents.semantic_analyzer.proto import semantic_analyzer_pb2 as",
        )
        pb2_grpc_file.write_text(content)


if __name__ == "__main__":
    generate_proto()
