"""gRPC Server for Semantic Analyzer Agent.

Implements the gRPC service defined in semantic_analyzer.proto,
allowing other agents to query the semantic analyzer via gRPC.
"""

import time
from concurrent import futures
from pathlib import Path
from typing import Any, Dict, Optional

import grpc

# Import generated protobuf modules
from socialseed_e2e.agents.semantic_analyzer.proto import (
    semantic_analyzer_pb2,
    semantic_analyzer_pb2_grpc,
)
from socialseed_e2e.agents.semantic_analyzer.semantic_analyzer_agent import SemanticAnalyzerAgent


class SemanticAnalyzerServicer(semantic_analyzer_pb2_grpc.SemanticAnalyzerServicer):
    """gRPC servicer implementation for semantic analyzer."""

    def __init__(self):
        self.active_analyses: Dict[str, Dict[str, Any]] = {}
        self.agents: Dict[str, SemanticAnalyzerAgent] = {}

    def Analyze(self, request, context):
        """Run complete semantic drift analysis."""
        analysis_id = f"analysis_{int(time.time())}_{hash(request.project_root) % 10000}"

        try:
            # Create agent
            agent = SemanticAnalyzerAgent(
                project_root=Path(request.project_root),
                project_name=request.project_name or None,
                base_url=request.base_url or None,
            )

            self.agents[analysis_id] = agent
            self.active_analyses[analysis_id] = {
                "status": "EXTRACTING_INTENTS",
                "progress": 0.0,
                "message": "Starting analysis...",
            }

            # Convert API endpoints
            api_endpoints = []
            for endpoint in request.api_endpoints:
                api_endpoints.append(
                    {
                        "endpoint": endpoint.endpoint,
                        "method": endpoint.method,
                        "params": dict(endpoint.params),
                        "body": endpoint.body,
                        "headers": dict(endpoint.headers),
                    }
                )

            # Convert database configs
            database_configs = []
            for db_config in request.database_configs:
                database_configs.append(
                    {
                        "type": db_config.database_type,
                        "connection": db_config.connection_string,
                        "uri": db_config.uri,
                        "user": db_config.user,
                        "password": db_config.password,
                        "database": db_config.database,
                    }
                )

            # Run analysis
            report = agent.analyze(
                baseline_commit=request.baseline_commit or None,
                target_commit=request.target_commit or None,
                api_endpoints=api_endpoints or None,
                database_configs=database_configs or None,
                capture_states=request.capture_states,
                output_path=Path(request.output_path) if request.output_path else None,
            )

            # Generate summary
            summary = semantic_analyzer_pb2.AnalysisSummary(
                total_drifts=len(report.detected_drifts),
                total_intents=len(report.intent_baselines),
                has_critical_issues=report.has_critical_drifts(),
            )

            # Add severity distribution
            for drift in report.detected_drifts:
                severity = drift.severity.value
                summary.severity_distribution[severity] = (
                    summary.severity_distribution.get(severity, 0) + 1
                )

            # Add type distribution
            for drift in report.detected_drifts:
                drift_type = drift.drift_type.name
                summary.type_distribution[drift_type] = (
                    summary.type_distribution.get(drift_type, 0) + 1
                )

            self.active_analyses[analysis_id] = {
                "status": "COMPLETED",
                "progress": 100.0,
                "message": "Analysis completed successfully",
            }

            return semantic_analyzer_pb2.AnalyzeResponse(
                report_id=report.report_id,
                report_path=str(agent.report_generator.get_latest_report() or ""),
                json_path=str(
                    agent.report_generator.reports_dir / f"semantic_drift_{report.report_id}.json"
                ),
                summary=summary,
                success=True,
            )

        except Exception as e:
            self.active_analyses[analysis_id] = {
                "status": "FAILED",
                "progress": 0.0,
                "message": str(e),
            }

            return semantic_analyzer_pb2.AnalyzeResponse(
                success=False,
                error_message=str(e),
            )

    def ExtractIntents(self, request, context):
        """Extract intent baselines only."""
        try:
            agent = SemanticAnalyzerAgent(
                project_root=Path(request.project_root),
            )

            intent_baselines = agent.intent_extractor.extract_all()

            # Filter by categories if specified
            if request.categories:
                intent_baselines = [i for i in intent_baselines if i.category in request.categories]

            # Convert to protobuf
            pb_intents = []
            for intent in intent_baselines:
                pb_intent = semantic_analyzer_pb2.IntentBaseline(
                    intent_id=intent.intent_id,
                    description=intent.description,
                    category=intent.category,
                    expected_behavior=intent.expected_behavior,
                    success_criteria=intent.success_criteria,
                    related_entities=intent.related_entities,
                    preconditions=intent.preconditions,
                    postconditions=intent.postconditions,
                    confidence=intent.confidence,
                )

                # Add sources
                for source in intent.sources:
                    pb_source = semantic_analyzer_pb2.IntentSource(
                        source_type=source.source_type,
                        source_path=source.source_path,
                        line_number=source.line_number or 0,
                        url=source.url or "",
                        title=source.title or "",
                        content=source.content,
                        extracted_at=int(source.extracted_at.timestamp()),
                    )
                    pb_intent.sources.append(pb_source)

                pb_intents.append(pb_intent)

            return semantic_analyzer_pb2.ExtractIntentsResponse(
                intents=pb_intents,
                total_count=len(pb_intents),
                success=True,
            )

        except Exception as e:
            return semantic_analyzer_pb2.ExtractIntentsResponse(
                success=False,
                error_message=str(e),
            )

    def CaptureState(self, request, context):
        """Capture state snapshot."""
        try:
            agent = SemanticAnalyzerAgent(
                project_root=Path(request.project_root),
            )

            # Convert API endpoints
            api_endpoints = []
            for endpoint in request.api_endpoints:
                api_endpoints.append(
                    {
                        "endpoint": endpoint.endpoint,
                        "method": endpoint.method,
                        "params": dict(endpoint.params),
                        "body": endpoint.body,
                        "headers": dict(endpoint.headers),
                    }
                )

            # Convert database configs
            database_configs = []
            for db_config in request.database_configs:
                database_configs.append(
                    {
                        "type": db_config.database_type,
                        "connection": db_config.connection_string,
                        "uri": db_config.uri,
                        "user": db_config.user,
                        "password": db_config.password,
                        "database": db_config.database,
                    }
                )

            snapshot = agent.state_analyzer.capture_baseline_state(
                commit_hash=request.commit_hash or None,
                branch=request.branch or None,
                api_endpoints=api_endpoints or None,
                database_configs=database_configs or None,
            )

            return semantic_analyzer_pb2.CaptureStateResponse(
                snapshot_id=snapshot.snapshot_id,
                api_snapshot_count=len(snapshot.api_snapshots),
                database_snapshot_count=len(snapshot.database_snapshots),
                success=True,
            )

        except Exception as e:
            return semantic_analyzer_pb2.CaptureStateResponse(
                success=False,
                error_message=str(e),
            )

    def DetectDrift(self, request, context):
        """Detect drift between states."""
        try:
            # This would typically load snapshots from storage
            # For now, return an error indicating this needs implementation
            return semantic_analyzer_pb2.DetectDriftResponse(
                success=False,
                error_message="Direct drift detection from snapshots not implemented. Use Analyze instead.",
            )

        except Exception as e:
            return semantic_analyzer_pb2.DetectDriftResponse(
                success=False,
                error_message=str(e),
            )

    def GetAnalysisStatus(self, request, context):
        """Get analysis status."""
        analysis_id = request.analysis_id

        if analysis_id not in self.active_analyses:
            return semantic_analyzer_pb2.StatusResponse(
                analysis_id=analysis_id,
                status=semantic_analyzer_pb2.AnalysisStatus.FAILED,
                message="Analysis not found",
            )

        analysis = self.active_analyses[analysis_id]

        status_map = {
            "PENDING": semantic_analyzer_pb2.AnalysisStatus.PENDING,
            "EXTRACTING_INTENTS": semantic_analyzer_pb2.AnalysisStatus.EXTRACTING_INTENTS,
            "CAPTURING_BASELINE": semantic_analyzer_pb2.AnalysisStatus.CAPTURING_BASELINE,
            "CAPTURING_CURRENT": semantic_analyzer_pb2.AnalysisStatus.CAPTURING_CURRENT,
            "DETECTING_DRIFT": semantic_analyzer_pb2.AnalysisStatus.DETECTING_DRIFT,
            "GENERATING_REPORT": semantic_analyzer_pb2.AnalysisStatus.GENERATING_REPORT,
            "COMPLETED": semantic_analyzer_pb2.AnalysisStatus.COMPLETED,
            "FAILED": semantic_analyzer_pb2.AnalysisStatus.FAILED,
            "CANCELLED": semantic_analyzer_pb2.AnalysisStatus.CANCELLED,
        }

        return semantic_analyzer_pb2.StatusResponse(
            analysis_id=analysis_id,
            status=status_map.get(analysis["status"], semantic_analyzer_pb2.AnalysisStatus.FAILED),
            current_step=analysis["status"],
            progress_percent=analysis["progress"],
            message=analysis["message"],
        )

    def StreamAnalysisProgress(self, request, context):
        """Stream analysis progress."""
        analysis_id = request.analysis_id

        while True:
            if analysis_id not in self.active_analyses:
                yield semantic_analyzer_pb2.ProgressUpdate(
                    analysis_id=analysis_id,
                    status=semantic_analyzer_pb2.AnalysisStatus.FAILED,
                    message="Analysis not found",
                    timestamp=int(time.time()),
                )
                break

            analysis = self.active_analyses[analysis_id]

            status_map = {
                "PENDING": semantic_analyzer_pb2.AnalysisStatus.PENDING,
                "EXTRACTING_INTENTS": semantic_analyzer_pb2.AnalysisStatus.EXTRACTING_INTENTS,
                "CAPTURING_BASELINE": semantic_analyzer_pb2.AnalysisStatus.CAPTURING_BASELINE,
                "CAPTURING_CURRENT": semantic_analyzer_pb2.AnalysisStatus.CAPTURING_CURRENT,
                "DETECTING_DRIFT": semantic_analyzer_pb2.AnalysisStatus.DETECTING_DRIFT,
                "GENERATING_REPORT": semantic_analyzer_pb2.AnalysisStatus.GENERATING_REPORT,
                "COMPLETED": semantic_analyzer_pb2.AnalysisStatus.COMPLETED,
                "FAILED": semantic_analyzer_pb2.AnalysisStatus.FAILED,
                "CANCELLED": semantic_analyzer_pb2.AnalysisStatus.CANCELLED,
            }

            yield semantic_analyzer_pb2.ProgressUpdate(
                analysis_id=analysis_id,
                status=status_map.get(
                    analysis["status"], semantic_analyzer_pb2.AnalysisStatus.FAILED
                ),
                step=analysis["status"],
                progress_percent=analysis["progress"],
                message=analysis["message"],
                timestamp=int(time.time()),
            )

            # Stop streaming if analysis is complete or failed
            if analysis["status"] in ["COMPLETED", "FAILED", "CANCELLED"]:
                break

            time.sleep(1)  # Wait before next update


class SemanticAnalyzerServer:
    """gRPC server for semantic analyzer."""

    def __init__(self, port: int = 50051):
        self.port = port
        self.server: Optional[grpc.Server] = None

    def start(self):
        """Start the gRPC server."""
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

        semantic_analyzer_pb2_grpc.add_SemanticAnalyzerServicer_to_server(
            SemanticAnalyzerServicer(),
            self.server,
        )

        self.server.add_insecure_port(f"[::]:{self.port}")
        self.server.start()

        print(f"🚀 Semantic Analyzer gRPC Server started on port {self.port}")

    def stop(self, grace_period: Optional[int] = None):
        """Stop the gRPC server."""
        if self.server:
            self.server.stop(grace_period)
            print("🛑 Semantic Analyzer gRPC Server stopped")

    def wait_for_termination(self):
        """Wait for the server to terminate."""
        if self.server:
            self.server.wait_for_termination()


def serve(port: int = 50051):
    """Start the semantic analyzer gRPC server."""
    server = SemanticAnalyzerServer(port)
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
