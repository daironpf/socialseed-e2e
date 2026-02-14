"""gRPC Client for Semantic Analyzer Agent.

Provides a client to interact with the Semantic Analyzer gRPC service.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

import grpc

from socialseed_e2e.agents.semantic_analyzer.proto import (
    semantic_analyzer_pb2,
    semantic_analyzer_pb2_grpc,
)


class SemanticAnalyzerClient:
    """Client for Semantic Analyzer gRPC service."""

    def __init__(self, host: str = "localhost", port: int = 50051):
        self.host = host
        self.port = port
        self.channel: Optional[grpc.Channel] = None
        self.stub: Optional[semantic_analyzer_pb2_grpc.SemanticAnalyzerStub] = None

    def connect(self):
        """Connect to the gRPC server."""
        self.channel = grpc.insecure_channel(f"{self.host}:{self.port}")
        self.stub = semantic_analyzer_pb2_grpc.SemanticAnalyzerStub(self.channel)

    def disconnect(self):
        """Disconnect from the gRPC server."""
        if self.channel:
            self.channel.close()
            self.channel = None
            self.stub = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    def analyze(
        self,
        project_root: Path,
        project_name: Optional[str] = None,
        baseline_commit: Optional[str] = None,
        target_commit: Optional[str] = None,
        base_url: Optional[str] = None,
        api_endpoints: Optional[List[Dict[str, Any]]] = None,
        database_configs: Optional[List[Dict[str, Any]]] = None,
        capture_states: bool = True,
        output_path: Optional[Path] = None,
    ) -> semantic_analyzer_pb2.AnalyzeResponse:
        """Run complete semantic drift analysis."""
        if not self.stub:
            raise RuntimeError("Client not connected. Use connect() or context manager.")

        # Build API endpoints
        pb_endpoints = []
        if api_endpoints:
            for endpoint in api_endpoints:
                pb_endpoint = semantic_analyzer_pb2.ApiEndpoint(
                    endpoint=endpoint.get("endpoint", "/"),
                    method=endpoint.get("method", "GET"),
                )
                if "params" in endpoint:
                    pb_endpoint.params.update(endpoint["params"])
                if "body" in endpoint:
                    pb_endpoint.body = str(endpoint["body"])
                if "headers" in endpoint:
                    pb_endpoint.headers.update(endpoint["headers"])
                pb_endpoints.append(pb_endpoint)

        # Build database configs
        pb_databases = []
        if database_configs:
            for db_config in database_configs:
                pb_db = semantic_analyzer_pb2.DatabaseConfig(
                    database_type=db_config.get("type", ""),
                    connection_string=db_config.get("connection", ""),
                    uri=db_config.get("uri", ""),
                    user=db_config.get("user", ""),
                    password=db_config.get("password", ""),
                    database=db_config.get("database", ""),
                )
                pb_databases.append(pb_db)

        request = semantic_analyzer_pb2.AnalyzeRequest(
            project_root=str(project_root),
            project_name=project_name or "",
            baseline_commit=baseline_commit or "",
            target_commit=target_commit or "",
            base_url=base_url or "",
            api_endpoints=pb_endpoints,
            database_configs=pb_databases,
            capture_states=capture_states,
            output_path=str(output_path) if output_path else "",
        )

        return self.stub.Analyze(request)

    def extract_intents(
        self,
        project_root: Path,
        categories: Optional[List[str]] = None,
    ) -> semantic_analyzer_pb2.ExtractIntentsResponse:
        """Extract intent baselines."""
        if not self.stub:
            raise RuntimeError("Client not connected. Use connect() or context manager.")

        request = semantic_analyzer_pb2.ExtractIntentsRequest(
            project_root=str(project_root),
            categories=categories or [],
        )

        return self.stub.ExtractIntents(request)

    def capture_state(
        self,
        project_root: Path,
        snapshot_id: Optional[str] = None,
        commit_hash: Optional[str] = None,
        branch: Optional[str] = None,
        api_endpoints: Optional[List[Dict[str, Any]]] = None,
        database_configs: Optional[List[Dict[str, Any]]] = None,
    ) -> semantic_analyzer_pb2.CaptureStateResponse:
        """Capture state snapshot."""
        if not self.stub:
            raise RuntimeError("Client not connected. Use connect() or context manager.")

        # Build API endpoints
        pb_endpoints = []
        if api_endpoints:
            for endpoint in api_endpoints:
                pb_endpoint = semantic_analyzer_pb2.ApiEndpoint(
                    endpoint=endpoint.get("endpoint", "/"),
                    method=endpoint.get("method", "GET"),
                )
                if "params" in endpoint:
                    pb_endpoint.params.update(endpoint["params"])
                if "body" in endpoint:
                    pb_endpoint.body = str(endpoint["body"])
                if "headers" in endpoint:
                    pb_endpoint.headers.update(endpoint["headers"])
                pb_endpoints.append(pb_endpoint)

        # Build database configs
        pb_databases = []
        if database_configs:
            for db_config in database_configs:
                pb_db = semantic_analyzer_pb2.DatabaseConfig(
                    database_type=db_config.get("type", ""),
                    connection_string=db_config.get("connection", ""),
                    uri=db_config.get("uri", ""),
                    user=db_config.get("user", ""),
                    password=db_config.get("password", ""),
                    database=db_config.get("database", ""),
                )
                pb_databases.append(pb_db)

        request = semantic_analyzer_pb2.CaptureStateRequest(
            project_root=str(project_root),
            snapshot_id=snapshot_id or "",
            commit_hash=commit_hash or "",
            branch=branch or "",
            api_endpoints=pb_endpoints,
            database_configs=pb_databases,
        )

        return self.stub.CaptureState(request)

    def get_analysis_status(self, analysis_id: str) -> semantic_analyzer_pb2.StatusResponse:
        """Get analysis status."""
        if not self.stub:
            raise RuntimeError("Client not connected. Use connect() or context manager.")

        request = semantic_analyzer_pb2.StatusRequest(analysis_id=analysis_id)
        return self.stub.GetAnalysisStatus(request)

    def stream_analysis_progress(self, analysis_id: str):
        """Stream analysis progress."""
        if not self.stub:
            raise RuntimeError("Client not connected. Use connect() or context manager.")

        request = semantic_analyzer_pb2.StreamRequest(analysis_id=analysis_id)
        return self.stub.StreamAnalysisProgress(request)


def query_semantic_analyzer(
    project_root: Path, host: str = "localhost", port: int = 50051, **kwargs
) -> semantic_analyzer_pb2.AnalyzeResponse:
    """Convenience function to query the semantic analyzer.

    Args:
        project_root: Path to the project root
        host: gRPC server host
        port: gRPC server port
        **kwargs: Additional arguments passed to analyze()

    Returns:
        AnalyzeResponse from the server
    """
    with SemanticAnalyzerClient(host, port) as client:
        return client.analyze(project_root=project_root, **kwargs)
