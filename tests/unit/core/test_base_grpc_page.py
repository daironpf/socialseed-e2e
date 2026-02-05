"""Unit tests for BaseGrpcPage.

This module tests the gRPC page functionality without requiring
a real gRPC server (using mocks).
"""

import pytest

# Skip all tests if gRPC is not available
try:
    import grpc

    from socialseed_e2e.core.base_grpc_page import BaseGrpcPage, GrpcCallLog, GrpcRetryConfig

    GRPC_AVAILABLE = True
except ImportError:
    GRPC_AVAILABLE = False


pytestmark = [
    pytest.mark.unit,
    pytest.mark.skipif(not GRPC_AVAILABLE, reason="gRPC not available"),
]


class TestGrpcRetryConfig:
    """Test GrpcRetryConfig class."""

    def test_default_values(self):
        """Test default retry configuration."""
        config = GrpcRetryConfig()

        assert config.max_retries == 3
        assert config.backoff_factor == 1.0
        assert config.max_backoff == 60.0
        # Default retry codes: UNAVAILABLE(14), DEADLINE_EXCEEDED(4), RESOURCE_EXHAUSTED(8)
        assert config.retry_codes == [14, 4, 8]

    def test_custom_values(self):
        """Test custom retry configuration."""
        config = GrpcRetryConfig(
            max_retries=5, backoff_factor=2.0, max_backoff=120.0, retry_codes=[14, 4]
        )

        assert config.max_retries == 5
        assert config.backoff_factor == 2.0
        assert config.max_backoff == 120.0
        assert config.retry_codes == [14, 4]


class TestGrpcCallLog:
    """Test GrpcCallLog class."""

    def test_default_values(self):
        """Test default call log values."""
        import time

        log = GrpcCallLog(
            service="TestService",
            method="TestMethod",
            request={"id": "123"},
            timestamp=time.time(),
        )

        assert log.service == "TestService"
        assert log.method == "TestMethod"
        assert log.request == {"id": "123"}
        assert log.duration_ms == 0.0
        assert log.status_code is None
        assert log.response is None
        assert log.error is None


class TestBaseGrpcPage:
    """Test BaseGrpcPage class."""

    def test_init_default_values(self):
        """Test page initialization with defaults."""
        page = BaseGrpcPage("localhost:50051")

        assert page.host == "localhost:50051"
        assert page.use_tls is False
        assert page.credentials is None
        assert page.timeout == 30.0
        assert page._channel is None
        assert len(page._stubs) == 0
        assert len(page.call_logs) == 0

    def test_init_custom_values(self):
        """Test page initialization with custom values."""
        retry_config = GrpcRetryConfig(max_retries=5)
        page = BaseGrpcPage(
            host="example.com:443",
            use_tls=True,
            timeout=60.0,
            retry_config=retry_config,
        )

        assert page.host == "example.com:443"
        assert page.use_tls is True
        assert page.timeout == 60.0
        assert page.retry_config.max_retries == 5

    def test_channel_not_initialized(self):
        """Test accessing channel before setup raises error."""
        page = BaseGrpcPage("localhost:50051")

        with pytest.raises(RuntimeError, match="Channel not initialized"):
            _ = page.channel

    def test_get_stub_not_registered(self):
        """Test getting unregistered stub raises error."""
        page = BaseGrpcPage("localhost:50051")

        with pytest.raises(KeyError, match="Stub 'nonexistent' not registered"):
            page.get_stub("nonexistent")

    def test_call_method_not_found(self):
        """Test calling non-existent method raises error."""
        page = BaseGrpcPage("localhost:50051")

        # Mock a stub
        class MockStub:
            pass

        page._stubs["test"] = MockStub()

        with pytest.raises(AttributeError, match="Method 'nonexistent' not found"):
            page.call("test", "nonexistent", {})

    def test_assert_ok_success(self):
        """Test assert_ok with valid response."""
        page = BaseGrpcPage("localhost:50051")

        # Should not raise
        page.assert_ok({"id": "123"}, "test context")

    def test_assert_ok_failure(self):
        """Test assert_ok with None response."""
        page = BaseGrpcPage("localhost:50051")

        with pytest.raises(AssertionError, match="gRPC response is None"):
            page.assert_ok(None)

    def test_assert_ok_with_context(self):
        """Test assert_ok failure includes context."""
        page = BaseGrpcPage("localhost:50051")

        with pytest.raises(AssertionError, match="test context: gRPC response is None"):
            page.assert_ok(None, "test context")

    def test_clear_logs(self):
        """Test clearing call logs."""
        page = BaseGrpcPage("localhost:50051")

        # Add a mock log
        import time

        page.call_logs.append(
            GrpcCallLog(service="Test", method="Test", request={}, timestamp=time.time())
        )

        assert len(page.call_logs) == 1

        page.clear_logs()

        assert len(page.call_logs) == 0

    def test_context_manager(self):
        """Test using page as context manager."""
        # Note: This would require mocking grpc.insecure_channel
        # For now, just verify the context manager methods exist
        page = BaseGrpcPage("localhost:50051")

        assert hasattr(page, "__enter__")
        assert hasattr(page, "__exit__")
