"""Protobuf schema handler for gRPC testing.

This module provides utilities for handling Protocol Buffer schemas,
including proto file discovery, dynamic message creation, and import handling.
"""

import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union

from google.protobuf import descriptor_pool
from google.protobuf.descriptor import Descriptor
from google.protobuf.message import Message


class ProtoSchemaHandler:
    """Handler for Protocol Buffer schemas.

    This class provides utilities for:
    - Discovering and loading .proto files
    - Compiling proto files to Python modules
    - Creating dynamic message instances
    - Managing proto imports and dependencies

    Example:
        >>> handler = ProtoSchemaHandler("./protos")
        >>> handler.compile_protos()
        >>> request = handler.create_message("user_pb2", "CreateUserRequest")
        >>> request.name = "John"
        >>> request.email = "john@example.com"

    Attributes:
        proto_dir: Directory containing .proto files
        output_dir: Directory for generated Python files
        compiled: Whether protos have been compiled
    """

    def __init__(
        self, proto_dir: Union[str, Path], output_dir: Optional[Union[str, Path]] = None
    ):
        """Initialize the proto schema handler.

        Args:
            proto_dir: Directory containing .proto files
            output_dir: Directory for generated Python files (default: proto_dir)
        """
        self.proto_dir = Path(proto_dir)
        self.output_dir = Path(output_dir) if output_dir else self.proto_dir
        self.compiled = False
        self._message_classes: Dict[str, Type[Message]] = {}
        self._service_classes: Dict[str, Any] = {}
        self._descriptor_pool: Optional[descriptor_pool.DescriptorPool] = None

    def find_proto_files(self) -> List[Path]:
        """Find all .proto files in the proto directory.

        Returns:
            List of paths to .proto files
        """
        if not self.proto_dir.exists():
            return []
        return list(self.proto_dir.rglob("*.proto"))

    def compile_protos(self, force: bool = False) -> List[Path]:
        """Compile all proto files to Python modules.

        Args:
            force: Force recompilation even if already compiled

        Returns:
            List of paths to generated Python files

        Raises:
            RuntimeError: If compilation fails
        """
        if self.compiled and not force:
            return list(self.output_dir.rglob("*_pb2*.py"))

        proto_files = self.find_proto_files()
        if not proto_files:
            raise RuntimeError(f"No .proto files found in {self.proto_dir}")

        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Build protoc command
        generated_files = []

        for proto_file in proto_files:
            cmd = [
                sys.executable,
                "-m",
                "grpc_tools.protoc",
                f"--proto_path={self.proto_dir}",
                f"--python_out={self.output_dir}",
                f"--grpc_python_out={self.output_dir}",
                str(proto_file),
            ]

            try:
                subprocess.run(cmd, capture_output=True, text=True, check=True)

                # Add generated files
                base_name = proto_file.stem
                pb2_file = self.output_dir / f"{base_name}_pb2.py"
                pb2_grpc_file = self.output_dir / f"{base_name}_pb2_grpc.py"

                if pb2_file.exists():
                    generated_files.append(pb2_file)
                if pb2_grpc_file.exists():
                    generated_files.append(pb2_grpc_file)

            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"Failed to compile {proto_file}: {e.stderr}") from e

        # Add output directory to Python path
        if str(self.output_dir) not in sys.path:
            sys.path.insert(0, str(self.output_dir))

        self.compiled = True
        return generated_files

    def load_message_class(self, module_name: str, message_name: str) -> Type[Message]:
        """Load a protobuf message class from a compiled module.

        Args:
            module_name: Name of the generated Python module (e.g., "user_pb2")
            message_name: Name of the message class (e.g., "CreateUserRequest")

        Returns:
            The message class

        Raises:
            ImportError: If module not found
            AttributeError: If message class not found in module
        """
        cache_key = f"{module_name}.{message_name}"
        if cache_key in self._message_classes:
            return self._message_classes[cache_key]

        if not self.compiled:
            self.compile_protos()

        try:
            module = __import__(module_name, fromlist=[message_name])
            message_class = getattr(module, message_name)
            self._message_classes[cache_key] = message_class
            return message_class
        except ImportError as e:
            raise ImportError(
                f"Failed to import {module_name}. "
                f"Make sure protos are compiled and in Python path."
            ) from e

    def load_service_stub(
        self, module_name: str, service_name: str, stub_type: str = "stub"
    ) -> Type:
        """Load a gRPC service stub class.

        Args:
            module_name: Name of the generated gRPC module (e.g., "user_pb2_grpc")
            service_name: Name of the service (e.g., "UserService")
            stub_type: Type of stub - "stub" (client) or "servicer" (server)

        Returns:
            The stub class

        Raises:
            ImportError: If module not found
            AttributeError: If stub class not found
        """
        cache_key = f"{module_name}.{service_name}.{stub_type}"
        if cache_key in self._service_classes:
            return self._service_classes[cache_key]

        if not self.compiled:
            self.compile_protos()

        try:
            module = __import__(module_name, fromlist=[service_name])

            if stub_type == "stub":
                stub_class = getattr(module, f"{service_name}Stub")
            elif stub_type == "servicer":
                stub_class = getattr(module, f"{service_name}Servicer")
            else:
                stub_class = getattr(module, service_name)

            self._service_classes[cache_key] = stub_class
            return stub_class
        except ImportError as e:
            raise ImportError(
                f"Failed to import {module_name}. "
                f"Make sure protos are compiled and in Python path."
            ) from e

    def create_message(self, module_name: str, message_name: str, **kwargs) -> Message:
        """Create a protobuf message instance.

        Args:
            module_name: Name of the generated Python module
            message_name: Name of the message class
            **kwargs: Field values to set on the message

        Returns:
            The created message instance
        """
        message_class = self.load_message_class(module_name, message_name)
        message = message_class()

        for key, value in kwargs.items():
            if hasattr(message, key):
                setattr(message, key, value)
            else:
                raise AttributeError(f"Message {message_name} has no field '{key}'")

        return message

    def parse_message(
        self, module_name: str, message_name: str, json_data: Union[str, Dict[str, Any]]
    ) -> Message:
        """Parse a message from JSON data.

        Args:
            module_name: Name of the generated Python module
            message_name: Name of the message class
            json_data: JSON string or dictionary

        Returns:
            The parsed message instance
        """
        from google.protobuf.json_format import Parse

        if isinstance(json_data, dict):
            import json

            json_data = json.dumps(json_data)

        message_class = self.load_message_class(module_name, message_name)
        message = message_class()
        Parse(json_data, message)
        return message

    def message_to_dict(self, message: Message) -> Dict[str, Any]:
        """Convert a protobuf message to a dictionary.

        Args:
            message: The protobuf message

        Returns:
            Dictionary representation of the message
        """
        from google.protobuf.json_format import MessageToDict

        return MessageToDict(message, preserving_proto_field_name=True)

    def get_message_descriptor(self, module_name: str, message_name: str) -> Descriptor:
        """Get the descriptor for a message type.

        Args:
            module_name: Name of the generated Python module
            message_name: Name of the message class

        Returns:
            The message descriptor
        """
        message_class = self.load_message_class(module_name, message_name)
        return message_class.DESCRIPTOR

    def list_messages(self, module_name: str) -> List[str]:
        """List all message types in a compiled module.

        Args:
            module_name: Name of the generated Python module

        Returns:
            List of message type names
        """
        if not self.compiled:
            self.compile_protos()

        try:
            module = __import__(module_name, fromlist=["DESCRIPTOR"])
            descriptor = getattr(module, "DESCRIPTOR", None)

            if descriptor:
                return [mt.name for mt in descriptor.message_types_by_name.values()]
            return []
        except ImportError:
            return []

    def list_services(self, module_name: str) -> List[str]:
        """List all service types in a compiled gRPC module.

        Args:
            module_name: Name of the generated gRPC module (e.g., "user_pb2_grpc")

        Returns:
            List of service names
        """
        if not self.compiled:
            self.compile_protos()

        try:
            module = __import__(module_name, fromlist=[])
            services = []

            for name in dir(module):
                if name.endswith("Stub") or name.endswith("Servicer"):
                    services.append(name)

            return services
        except ImportError:
            return []

    def validate_proto_syntax(self, proto_file: Union[str, Path]) -> List[str]:
        """Validate a proto file for syntax errors.

        Args:
            proto_file: Path to the .proto file

        Returns:
            List of error messages (empty if valid)
        """
        proto_path = Path(proto_file)
        if not proto_path.exists():
            return [f"File not found: {proto_path}"]

        cmd = [
            sys.executable,
            "-m",
            "grpc_tools.protoc",
            f"--proto_path={self.proto_dir}",
            "--decode_raw",
            str(proto_path),
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, input="")

            if result.returncode != 0:
                return [result.stderr]
            return []
        except Exception as e:
            return [str(e)]


class ProtoRegistry:
    """Registry for managing multiple proto schema handlers.

    This class allows managing multiple proto directories and
    provides a unified interface for accessing message types.

    Example:
        >>> registry = ProtoRegistry()
        >>> registry.register("users", "./protos/users")
        >>> registry.register("orders", "./protos/orders")
        >>>
        >>> handler = registry.get("users")
        >>> request = handler.create_message("user_pb2", "GetUserRequest")
    """

    def __init__(self):
        """Initialize the proto registry."""
        self._handlers: Dict[str, ProtoSchemaHandler] = {}

    def register(
        self,
        name: str,
        proto_dir: Union[str, Path],
        output_dir: Optional[Union[str, Path]] = None,
    ) -> ProtoSchemaHandler:
        """Register a new proto schema handler.

        Args:
            name: Name to identify this proto collection
            proto_dir: Directory containing .proto files
            output_dir: Directory for generated Python files

        Returns:
            The registered handler
        """
        handler = ProtoSchemaHandler(proto_dir, output_dir)
        self._handlers[name] = handler
        return handler

    def get(self, name: str) -> ProtoSchemaHandler:
        """Get a registered handler.

        Args:
            name: Name of the registered handler

        Returns:
            The handler instance

        Raises:
            KeyError: If handler not found
        """
        if name not in self._handlers:
            raise KeyError(f"No proto handler registered for '{name}'")
        return self._handlers[name]

    def list_handlers(self) -> List[str]:
        """List all registered handler names.

        Returns:
            List of handler names
        """
        return list(self._handlers.keys())

    def compile_all(self) -> Dict[str, List[Path]]:
        """Compile protos for all registered handlers.

        Returns:
            Dictionary mapping handler names to lists of generated files
        """
        results = {}
        for name, handler in self._handlers.items():
            results[name] = handler.compile_protos()
        return results
