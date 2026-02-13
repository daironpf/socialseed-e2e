"""Tests for traffic_interceptor module."""

from datetime import datetime
from unittest.mock import MagicMock, Mock

import pytest

from socialseed_e2e.shadow_runner.traffic_interceptor import (
    CapturedInteraction,
    CapturedRequest,
    CapturedResponse,
    FastAPIMiddleware,
    FlaskMiddleware,
    TrafficInterceptor,
)


class TestCapturedRequest:
    """Test suite for CapturedRequest dataclass."""

    def test_captured_request_creation(self):
        """Test creating a CapturedRequest instance."""
        request = CapturedRequest(
            method="POST",
            path="/api/users",
            headers={"Content-Type": "application/json"},
            body='{"name": "John"}',
            query_params={"page": "1"},
            timestamp=datetime.now(),
        )

        assert request.method == "POST"
        assert request.path == "/api/users"
        assert request.headers["Content-Type"] == "application/json"
        assert request.body == '{"name": "John"}'
        assert request.query_params["page"] == "1"
        assert request.timestamp is not None

    def test_captured_request_defaults(self):
        """Test CapturedRequest with default values."""
        request = CapturedRequest(
            method="GET",
            path="/api/health",
        )

        assert request.method == "GET"
        assert request.path == "/api/health"
        assert request.headers == {}
        assert request.body is None
        assert request.query_params == {}
        assert request.timestamp is not None

    def test_captured_request_to_dict(self):
        """Test converting CapturedRequest to dictionary."""
        request = CapturedRequest(
            method="POST",
            path="/api/users",
            headers={"Content-Type": "application/json"},
            body='{"name": "John"}',
        )

        data = request.to_dict()

        assert data["method"] == "POST"
        assert data["path"] == "/api/users"
        assert data["headers"]["Content-Type"] == "application/json"
        assert data["body"] == '{"name": "John"}'

    def test_captured_request_from_dict(self):
        """Test creating CapturedRequest from dictionary."""
        data = {
            "method": "GET",
            "path": "/api/users",
            "headers": {"Authorization": "Bearer token"},
            "body": None,
            "query_params": {"page": "1"},
            "timestamp": "2024-01-01T00:00:00",
        }

        request = CapturedRequest.from_dict(data)

        assert request.method == "GET"
        assert request.path == "/api/users"
        assert request.headers["Authorization"] == "Bearer token"


class TestCapturedResponse:
    """Test suite for CapturedResponse dataclass."""

    def test_captured_response_creation(self):
        """Test creating a CapturedResponse instance."""
        response = CapturedResponse(
            status_code=200,
            headers={"Content-Type": "application/json"},
            body='{"id": 1, "name": "John"}',
            response_time_ms=45.5,
        )

        assert response.status_code == 200
        assert response.headers["Content-Type"] == "application/json"
        assert response.body == '{"id": 1, "name": "John"}'
        assert response.response_time_ms == 45.5

    def test_captured_response_defaults(self):
        """Test CapturedResponse with default values."""
        response = CapturedResponse(status_code=404)

        assert response.status_code == 404
        assert response.headers == {}
        assert response.body is None
        assert response.response_time_ms == 0.0

    def test_captured_response_to_dict(self):
        """Test converting CapturedResponse to dictionary."""
        response = CapturedResponse(
            status_code=201,
            headers={"Location": "/api/users/1"},
            body='{"id": 1}',
            response_time_ms=30.0,
        )

        data = response.to_dict()

        assert data["status_code"] == 201
        assert data["headers"]["Location"] == "/api/users/1"
        assert data["body"] == '{"id": 1}'
        assert data["response_time_ms"] == 30.0


class TestCapturedInteraction:
    """Test suite for CapturedInteraction dataclass."""

    def test_captured_interaction_creation(self):
        """Test creating a CapturedInteraction instance."""
        request = CapturedRequest(method="POST", path="/api/users")
        response = CapturedResponse(status_code=201)

        interaction = CapturedInteraction(
            request=request,
            response=response,
            timestamp=datetime.now(),
        )

        assert interaction.request == request
        assert interaction.response == response
        assert interaction.timestamp is not None

    def test_captured_interaction_to_dict(self):
        """Test converting CapturedInteraction to dictionary."""
        request = CapturedRequest(method="GET", path="/api/users")
        response = CapturedResponse(status_code=200)

        interaction = CapturedInteraction(
            request=request,
            response=response,
        )

        data = interaction.to_dict()

        assert data["request"]["method"] == "GET"
        assert data["request"]["path"] == "/api/users"
        assert data["response"]["status_code"] == 200


class TestTrafficInterceptor:
    """Test suite for TrafficInterceptor class."""

    def test_traffic_interceptor_creation(self):
        """Test creating a TrafficInterceptor instance."""
        interceptor = TrafficInterceptor()

        assert interceptor.captured_interactions == []
        assert interceptor.is_recording is False

    def test_start_recording(self):
        """Test starting recording."""
        interceptor = TrafficInterceptor()

        interceptor.start_recording()

        assert interceptor.is_recording is True

    def test_stop_recording(self):
        """Test stopping recording."""
        interceptor = TrafficInterceptor()
        interceptor.start_recording()

        captured = interceptor.stop_recording()

        assert interceptor.is_recording is False
        assert captured == []

    def test_capture_request_response(self):
        """Test capturing request and response."""
        interceptor = TrafficInterceptor()
        interceptor.start_recording()

        request = CapturedRequest(method="POST", path="/api/users")
        response = CapturedResponse(status_code=201)

        interceptor.capture_request(request)
        interceptor.capture_response(response)

        captured = interceptor.stop_recording()

        assert len(captured) == 1
        assert captured[0].request == request
        assert captured[0].response == response

    def test_get_captured_interactions(self):
        """Test getting captured interactions."""
        interceptor = TrafficInterceptor()
        interceptor.start_recording()

        request = CapturedRequest(method="GET", path="/api/health")
        response = CapturedResponse(status_code=200)

        interceptor.capture_request(request)
        interceptor.capture_response(response)

        interactions = interceptor.get_captured_interactions()

        assert len(interactions) == 1
        assert interactions[0].request.path == "/api/health"

    def test_clear_captured(self):
        """Test clearing captured interactions."""
        interceptor = TrafficInterceptor()
        interceptor.start_recording()

        request = CapturedRequest(method="GET", path="/api/test")
        response = CapturedResponse(status_code=200)

        interceptor.capture_request(request)
        interceptor.capture_response(response)

        interceptor.clear_captured()

        assert len(interceptor.captured_interactions) == 0

    def test_no_capture_when_not_recording(self):
        """Test that no capture happens when not recording."""
        interceptor = TrafficInterceptor()
        # Don't start recording

        request = CapturedRequest(method="POST", path="/api/users")
        response = CapturedResponse(status_code=201)

        interceptor.capture_request(request)
        interceptor.capture_response(response)

        assert len(interceptor.captured_interactions) == 0


class TestFlaskMiddleware:
    """Test suite for FlaskMiddleware class."""

    def test_flask_middleware_creation(self):
        """Test creating FlaskMiddleware instance."""
        mock_app = Mock()
        middleware = FlaskMiddleware(mock_app)

        assert middleware.app == mock_app
        assert isinstance(middleware.interceptor, TrafficInterceptor)

    def test_flask_middleware_call(self):
        """Test Flask middleware call method."""
        mock_app = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.get_data.return_value = b'{"status": "ok"}'
        mock_app.return_value = mock_response

        middleware = FlaskMiddleware(mock_app)

        # Mock environ
        environ = {
            "REQUEST_METHOD": "GET",
            "PATH_INFO": "/api/health",
            "QUERY_STRING": "",
        }
        start_response = Mock()

        middleware(environ, start_response)

        mock_app.assert_called_once()


class TestFastAPIMiddleware:
    """Test suite for FastAPIMiddleware class."""

    def test_fastapi_middleware_creation(self):
        """Test creating FastAPIMiddleware instance."""
        middleware = FastAPIMiddleware(Mock())

        assert isinstance(middleware.interceptor, TrafficInterceptor)

    @pytest.mark.asyncio
    async def test_fastapi_middleware_dispatch(self):
        """Test FastAPI middleware dispatch method."""
        mock_app = Mock()
        middleware = FastAPIMiddleware(mock_app)

        # Mock request and response
        mock_request = Mock()
        mock_request.method = "GET"
        mock_request.url.path = "/api/health"
        mock_request.headers = {}
        mock_request.query_params = {}

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.body = b'{"status": "ok"}'

        # Call dispatch
        response = await middleware.dispatch(mock_request, lambda req: mock_response)

        assert response == mock_response


class TestTrafficInterceptorIntegration:
    """Integration tests for TrafficInterceptor."""

    def test_full_capture_flow(self):
        """Test complete capture flow with multiple requests."""
        interceptor = TrafficInterceptor()
        interceptor.start_recording()

        # Capture first request/response
        request1 = CapturedRequest(
            method="POST",
            path="/api/users",
            body='{"name": "John"}',
        )
        response1 = CapturedResponse(status_code=201, body='{"id": 1}')

        interceptor.capture_request(request1)
        interceptor.capture_response(response1)

        # Capture second request/response
        request2 = CapturedRequest(
            method="GET",
            path="/api/users/1",
        )
        response2 = CapturedResponse(
            status_code=200,
            body='{"id": 1, "name": "John"}',
        )

        interceptor.capture_request(request2)
        interceptor.capture_response(response2)

        # Stop and verify
        captured = interceptor.stop_recording()

        assert len(captured) == 2
        assert captured[0].request.path == "/api/users"
        assert captured[1].request.path == "/api/users/1"

    def test_paired_request_response(self):
        """Test that requests and responses are correctly paired."""
        interceptor = TrafficInterceptor()
        interceptor.start_recording()

        # Request without response should not be captured
        request = CapturedRequest(method="GET", path="/api/test")
        interceptor.capture_request(request)

        # Response should complete the pair
        response = CapturedResponse(status_code=200)
        interceptor.capture_response(response)

        captured = interceptor.stop_recording()

        assert len(captured) == 1
        assert captured[0].request is request
        assert captured[0].response is response
