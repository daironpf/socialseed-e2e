"""Tests for gRPC Testing Module.

This module tests the advanced gRPC testing features.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from socialseed_e2e.grpc import (
    ErrorHandler,
    GrpcResponse,
    GrpcStatusCode,
    GrpcTestingSuite,
    LoadTester,
    StreamCollector,
    StreamingConfig,
    StreamingTester,
    StreamType,
)


class TestStreamCollector:
    """Tests for StreamCollector."""

    def test_initialization(self):
        """Test collector initialization."""
        collector = StreamCollector()
        assert collector.count == 0
        assert collector.is_complete is False

    def test_add_message(self):
        """Test adding messages."""
        collector = StreamCollector()
        collector.add({"id": "1"})
        collector.add({"id": "2"})

        assert collector.count == 2
        assert len(collector.get_all()) == 2

    def test_max_messages(self):
        """Test max messages limit."""
        collector = StreamCollector(max_messages=2)
        collector.add({"id": "1"})
        collector.add({"id": "2"})
        collector.add({"id": "3"})

        assert collector.count == 2

    def test_errors(self):
        """Test error collection."""
        collector = StreamCollector()
        collector.add_error("Error 1")
        collector.add_error("Error 2")

        assert len(collector.get_errors()) == 2

    def test_complete(self):
        """Test stream completion."""
        collector = StreamCollector()
        collector.complete()

        assert collector.is_complete is True

    def test_clear(self):
        """Test clearing collector."""
        collector = StreamCollector()
        collector.add({"id": "1"})
        collector.add_error("Error")
        collector.complete()

        collector.clear()

        assert collector.count == 0
        assert collector.is_complete is False


class TestStreamingTester:
    """Tests for StreamingTester."""

    def test_initialization(self):
        """Test streaming tester initialization."""
        mock_channel = MagicMock()
        tester = StreamingTester(mock_channel)

        assert tester.channel == mock_channel


class TestLoadTester:
    """Tests for LoadTester."""

    def test_initialization(self):
        """Test load tester initialization."""
        mock_channel = MagicMock()
        tester = LoadTester(mock_channel)

        assert tester.channel == mock_channel

    def test_empty_statistics(self):
        """Test statistics with no results."""
        mock_channel = MagicMock()
        tester = LoadTester(mock_channel)

        stats = tester.get_statistics()

        assert stats == {}


class TestErrorHandler:
    """Tests for ErrorHandler."""

    def test_initialization(self):
        """Test error handler initialization."""
        handler = ErrorHandler()
        assert handler.error_log == []

    def test_validate_status_code(self):
        """Test status code validation."""
        handler = ErrorHandler()
        response = GrpcResponse(
            data=None,
            status_code=GrpcStatusCode.NOT_FOUND,
            status_message="Not found",
            duration_ms=0,
        )

        assert handler.validate_status_code(response, GrpcStatusCode.NOT_FOUND) is True
        assert handler.validate_status_code(response, GrpcStatusCode.OK) is False

    def test_is_retriable(self):
        """Test retriable error detection."""
        handler = ErrorHandler()

        # Retriable
        response = GrpcResponse(
            data=None,
            status_code=GrpcStatusCode.UNAVAILABLE,
            status_message="Unavailable",
            duration_ms=0,
        )
        assert handler.is_retriable(response) is True

        # Not retriable
        response = GrpcResponse(
            data=None,
            status_code=GrpcStatusCode.NOT_FOUND,
            status_message="Not found",
            duration_ms=0,
        )
        assert handler.is_retriable(response) is False

    def test_log_error(self):
        """Test error logging."""
        handler = ErrorHandler()
        response = GrpcResponse(
            data=None,
            status_code=GrpcStatusCode.INTERNAL,
            status_message="Internal error",
            duration_ms=0,
        )

        handler.log_error(response)

        assert len(handler.error_log) == 1

    def test_error_summary(self):
        """Test error summary."""
        handler = ErrorHandler()

        # Add multiple errors
        for code in [
            GrpcStatusCode.INTERNAL,
            GrpcStatusCode.INTERNAL,
            GrpcStatusCode.NOT_FOUND,
        ]:
            handler.log_error(
                GrpcResponse(
                    data=None,
                    status_code=code,
                    status_message="",
                    duration_ms=0,
                )
            )

        summary = handler.get_error_summary()

        assert summary["total_errors"] == 3
        assert summary["errors_by_code"][GrpcStatusCode.INTERNAL.value] == 2
        assert summary["errors_by_code"][GrpcStatusCode.NOT_FOUND.value] == 1


class TestGrpcTestingSuite:
    """Tests for GrpcTestingSuite."""

    def test_initialization(self):
        """Test suite initialization."""
        with patch("socialseed_e2e.grpc.insecure_channel"):
            suite = GrpcTestingSuite("localhost:50051")

            assert suite.target == "localhost:50051"

    def test_close(self):
        """Test channel close."""
        with patch("socialseed_e2e.grpc.insecure_channel"):
            mock_channel = MagicMock()
            suite = GrpcTestingSuite("localhost:50051")
            suite.channel = mock_channel

            suite.close()

            mock_channel.close.assert_called_once()


class TestGrpcStatusCode:
    """Tests for GrpcStatusCode."""

    def test_status_codes(self):
        """Test status code values."""
        assert GrpcStatusCode.OK == 0
        assert GrpcStatusCode.CANCELLED == 1
        assert GrpcStatusCode.UNKNOWN == 2
        assert GrpcStatusCode.NOT_FOUND == 5
        assert GrpcStatusCode.INTERNAL == 13
        assert GrpcStatusCode.UNAVAILABLE == 14


class TestStreamingConfig:
    """Tests for StreamingConfig."""

    def test_default_config(self):
        """Test default configuration."""
        config = StreamingConfig(StreamType.UNARY)

        assert config.stream_type == StreamType.UNARY
        assert config.chunk_size is None
        assert config.max_messages is None
        assert config.timeout == 30.0

    def test_custom_config(self):
        """Test custom configuration."""
        config = StreamingConfig(
            StreamType.SERVER_STREAMING,
            chunk_size=1024,
            max_messages=100,
            timeout=60.0,
        )

        assert config.stream_type == StreamType.SERVER_STREAMING
        assert config.chunk_size == 1024
        assert config.max_messages == 100
        assert config.timeout == 60.0
