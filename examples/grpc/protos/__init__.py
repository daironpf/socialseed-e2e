"""Protos package for generated protobuf modules.

This directory will contain the generated protobuf Python modules after
compiling the .proto files.

To compile:
    python -m grpc_tools.protoc \
        --proto_path=. \
        --python_out=./protos \
        --grpc_python_out=./protos \
        user.proto
"""

# Proto modules will be generated here
