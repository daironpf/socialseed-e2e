"""Shadow Runner - Main entry point for Behavior-Driven Test Generation.

Captures real application traffic and generates tests based on user behavior.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from socialseed_e2e.shadow_runner.capture_filter import CaptureFilter, SmartFilter
from socialseed_e2e.shadow_runner.privacy_sanitizer import PrivacySanitizer
from socialseed_e2e.shadow_runner.session_recorder import SessionRecorder, UserSession
from socialseed_e2e.shadow_runner.test_generator import (
    GeneratedTest,
    TestExporter,
    TestGenerator,
)
from socialseed_e2e.shadow_runner.traffic_interceptor import (
    CapturedInteraction,
    TrafficInterceptor,
)


# Configuration classes for CLI
@dataclass
class CaptureConfig:
    """Configuration for traffic capture."""

    target_url: str
    output_path: str
    filter_health_checks: bool = True
    filter_static_assets: bool = True
    sanitize_pii: bool = True
    max_requests: Optional[int] = None
    duration: Optional[int] = None


@dataclass
class TestGenerationConfig:
    """Configuration for test generation."""

    service_name: str
    output_dir: str = "services"
    template: str = "standard"
    group_by: str = "endpoint"
    include_auth_patterns: bool = False


@dataclass
class ReplayConfig:
    """Configuration for session replay."""

    capture_file: str
    target_url: Optional[str] = None
    speed: str = "fast"
    stop_on_error: bool = False


class ShadowRunner:
    """Main Shadow Runner class for capturing traffic and generating tests."""

    def __init__(
        self,
        output_dir: str = "./captured_tests",
        enable_filtering: bool = True,
        enable_sanitization: bool = True,
        enable_session_tracking: bool = True,
    ):
        """Initialize the Shadow Runner.

        Args:
            output_dir: Directory to save captured data and generated tests
            enable_filtering: Enable traffic filtering
            enable_sanitization: Enable privacy sanitization
            enable_session_tracking: Enable session recording
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.interceptor = TrafficInterceptor()
        self.filter = SmartFilter() if enable_filtering else CaptureFilter()
        self.sanitizer = PrivacySanitizer() if enable_sanitization else None
        self.session_recorder = (
            SessionRecorder(self.output_dir / "sessions")
            if enable_session_tracking
            else None
        )
        self.test_generator = TestGenerator()
        self.test_exporter = TestExporter()

        # State
        self.capturing = False
        self.current_session_id: Optional[str] = None

    def start_capturing(
        self,
        user_id: Optional[str] = None,
        session_metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Start capturing traffic.

        Args:
            user_id: Optional user identifier
            session_metadata: Optional session metadata
        """
        self.capturing = True

        # Start interceptor
        self.interceptor.start_capturing()

        # Start session
        if self.session_recorder:
            self.current_session_id = self.session_recorder.start_session(
                user_id=user_id,
                metadata=session_metadata,
            )

        # Register callback to process interactions
        self.interceptor.register_callback(self._process_interaction)

        print(f"🎬 Shadow Runner: Started capturing traffic")
        print(f"   Output directory: {self.output_dir.absolute()}")
        if self.current_session_id:
            print(f"   Session ID: {self.current_session_id}")

    def stop_capturing(self) -> Dict[str, Any]:
        """Stop capturing traffic.

        Returns:
            Capture summary
        """
        if not self.capturing:
            return {}

        self.capturing = False
        self.interceptor.stop_capturing()

        # End session
        if self.session_recorder and self.current_session_id:
            self.session_recorder.end_session(self.current_session_id)
            self.current_session_id = None

        # Get statistics
        stats = self.get_statistics()

        print(f"\n⏹️  Shadow Runner: Stopped capturing")
        print(f"   Total requests: {stats['total_requests']}")
        print(f"   Filtered requests: {stats['filtered_requests']}")
        print(f"   Final captured: {stats['final_captured']}")

        return stats

    def _process_interaction(self, interaction: CapturedInteraction) -> None:
        """Process a captured interaction.

        Args:
            interaction: Captured interaction
        """
        # Apply filtering
        if not self.filter.should_capture(interaction):
            return

        # Apply sanitization
        if self.sanitizer:
            interaction = self.sanitizer.sanitize_interaction(interaction)

        # Add to session
        if self.session_recorder and self.current_session_id:
            self.session_recorder.add_interaction_to_session(
                self.current_session_id, interaction
            )

    def generate_tests(
        self,
        group_by: str = "endpoint",
        output_format: str = "service",
        service_name: str = "captured",
    ) -> List[Path]:
        """Generate tests from captured traffic.

        Args:
            group_by: How to group tests ("endpoint", "session", "none")
            output_format: Output format ("service", "single_file")
            service_name: Service name for generated tests

        Returns:
            List of generated file paths
        """
        # Get captured interactions
        interactions = self.interceptor.get_captured_interactions()

        if not interactions:
            print("⚠️  No interactions captured")
            return []

        # Generate tests
        tests = self.test_generator.generate_tests_from_traffic(interactions, group_by)

        if not tests:
            print("⚠️  No tests generated")
            return []

        # Export tests
        generated_files = []

        if output_format == "service":
            file_path = self.test_exporter.export_to_service_directory(
                tests, service_name, self.output_dir
            )
            generated_files.append(file_path)
        else:
            file_path = self.output_dir / f"test_{service_name}_captured.py"
            self.test_exporter.export_to_python_file(tests, file_path, service_name)
            generated_files.append(file_path)

        print(f"\n✅ Generated {len(tests)} tests")
        print(f"   Output: {generated_files[0]}")

        return generated_files

    def save_capture(self, filename: str = "capture.json") -> Path:
        """Save captured interactions to file.

        Args:
            filename: Output filename

        Returns:
            Path to saved file
        """
        file_path = self.output_dir / filename
        self.interceptor.save_to_file(file_path)
        return file_path

    def load_capture(self, filename: str = "capture.json") -> None:
        """Load captured interactions from file.

        Args:
            filename: Input filename
        """
        file_path = self.output_dir / filename
        if file_path.exists():
            self.interceptor.load_from_file(file_path)

    def get_statistics(self) -> Dict[str, Any]:
        """Get capture statistics.

        Returns:
            Statistics dictionary
        """
        all_interactions = self.interceptor.get_captured_interactions()
        filtered_interactions = self.filter.filter_interactions(all_interactions)

        stats = {
            "total_requests": len(all_interactions),
            "filtered_requests": len(all_interactions) - len(filtered_interactions),
            "final_captured": len(filtered_interactions),
            "capture_rate": len(filtered_interactions) / len(all_interactions)
            if all_interactions
            else 0,
        }

        # Add filter statistics
        filter_stats = self.filter.get_statistics(all_interactions)
        stats["filter_stats"] = filter_stats

        # Add interceptor statistics
        interceptor_stats = self.interceptor.get_statistics()
        stats["interceptor_stats"] = interceptor_stats

        # Add session statistics
        if self.session_recorder:
            session_stats = self.session_recorder.get_session_statistics()
            stats["session_stats"] = session_stats

        return stats

    def get_privacy_report(self) -> Dict[str, Any]:
        """Get privacy sanitization report.

        Returns:
            Privacy report
        """
        if not self.sanitizer:
            return {"enabled": False}

        interactions = self.interceptor.get_captured_interactions()
        return self.sanitizer.get_sanitization_report(interactions)

    def clear_capture(self) -> None:
        """Clear all captured interactions."""
        self.interceptor.clear_captured()

    def replay_session(
        self,
        session_id: str,
        callback: Optional[Callable] = None,
    ) -> List[Dict[str, Any]]:
        """Replay a captured session.

        Args:
            session_id: Session ID to replay
            callback: Optional callback for each interaction

        Returns:
            Replay results
        """
        if not self.session_recorder:
            return []

        return self.session_recorder.replay_session(session_id, callback)

    def generate_middleware_flask(self) -> str:
        """Generate Flask middleware code.

        Returns:
            Middleware code
        """
        code = """
# Flask middleware for Shadow Runner
from socialseed_e2e.shadow_runner.traffic_interceptor import FlaskMiddleware

# Initialize shadow runner
from socialseed_e2e.shadow_runner import ShadowRunner
shadow = ShadowRunner(output_dir="./captured_tests")
shadow.start_capturing()

# Create middleware
middleware = FlaskMiddleware(shadow.interceptor)

# Register with Flask app
app.before_request(middleware.before_request)
app.after_request(middleware.after_request)
"""
        return code

    def generate_middleware_fastapi(self) -> str:
        """Generate FastAPI middleware code.

        Returns:
            Middleware code
        """
        code = """
# FastAPI middleware for Shadow Runner
from socialseed_e2e.shadow_runner.traffic_interceptor import FastAPIMiddleware

# Initialize shadow runner
from socialseed_e2e.shadow_runner import ShadowRunner
shadow = ShadowRunner(output_dir="./captured_tests")
shadow.start_capturing()

# Create middleware
middleware = FastAPIMiddleware(shadow.interceptor)

# Register with FastAPI app
app.add_middleware(BaseHTTPMiddleware, dispatch=middleware.dispatch)
"""
        return code


# Convenience functions


def capture_with_context(
    func: Callable, output_dir: str = "./captured_tests", **shadow_kwargs
) -> Any:
    """Capture traffic while executing a function.

    Args:
        func: Function to execute
        output_dir: Output directory
        **shadow_kwargs: Additional ShadowRunner arguments

    Returns:
        Function result
    """
    runner = ShadowRunner(output_dir=output_dir, **shadow_kwargs)

    try:
        runner.start_capturing()
        result = func()
        return result
    finally:
        runner.stop_capturing()
        runner.generate_tests()


# Export main components
__all__ = [
    "ShadowRunner",
    "TrafficInterceptor",
    "CaptureFilter",
    "SmartFilter",
    "PrivacySanitizer",
    "SessionRecorder",
    "TestGenerator",
    "TestExporter",
    "GeneratedTest",
    "CapturedInteraction",
    "capture_with_context",
]
