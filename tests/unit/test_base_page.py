"""Tests for enhanced BasePage.

This module contains unit tests for the enhanced BasePage class with
logging, retries, rate limiting, and helper methods.
"""

import json
import time
from unittest.mock import MagicMock, patch

import pytest

from socialseed_e2e.core.base_page import (
    BasePage,
    BasePageError,
    RequestLog,
    RetryConfig,
    RateLimitConfig,
)


class MockResponse:
    """Mock Playwright APIResponse for testing."""
    
    def __init__(self, status=200, body=None, headers=None, url="http://test.com"):
        self.status = status
        self._body = json.dumps(body).encode('utf-8') if body else b'{}'
        self.headers = headers or {"content-type": "application/json"}
        self.url = url
    
    def body(self):
        return self._body
    
    def text(self):
        return self._body.decode('utf-8')
    
    def json(self):
        return json.loads(self._body)


class TestBasePageInitialization:
    """Test cases for BasePage initialization."""
    
    @pytest.fixture
    def mock_playwright(self):
        """Fixture to mock playwright for initialization tests."""
        with patch('playwright.sync_api.sync_playwright') as mock_playwright:
            yield mock_playwright
    
    def test_init_with_base_url(self, mock_playwright):
        """Test initialization with basic parameters."""
        page = BasePage("https://api.example.com")
        
        assert page.base_url == "https://api.example.com"
        assert page.enable_request_logging is True
        assert isinstance(page.retry_config, object)
        assert isinstance(page.rate_limit_config, object)
    
    def test_init_with_custom_headers(self, mock_playwright):
        """Test initialization with custom headers."""
        headers = {"Authorization": "Bearer token123"}
        page = BasePage("https://api.example.com", default_headers=headers)
        
        assert "Authorization" in page.default_headers
        assert page.default_headers["Authorization"] == "Bearer token123"
    
    def test_init_with_retry_config(self, mock_playwright):
        """Test initialization with retry configuration."""
        retry_config = RetryConfig(max_retries=5, backoff_factor=2.0)
        page = BasePage(
            "https://api.example.com",
            retry_config=retry_config
        )
        
        assert page.retry_config.max_retries == 5
        assert page.retry_config.backoff_factor == 2.0
    
    def test_init_with_rate_limit_config(self, mock_playwright):
        """Test initialization with rate limit configuration."""
        rate_config = RateLimitConfig(enabled=True, requests_per_second=5)
        page = BasePage(
            "https://api.example.com",
            rate_limit_config=rate_config
        )
        
        assert page.rate_limit_config.enabled is True
        assert page.rate_limit_config.requests_per_second == 5


class TestRetryConfig:
    """Test cases for RetryConfig dataclass."""
    
    def test_default_values(self):
        """Test default retry configuration."""
        config = RetryConfig()
        
        assert config.max_retries == 3
        assert config.backoff_factor == 1.0
        assert config.max_backoff == 60.0
        assert 502 in config.retry_on
        assert 503 in config.retry_on
        assert 429 in config.retry_on
    
    def test_custom_values(self):
        """Test custom retry configuration."""
        config = RetryConfig(
            max_retries=5,
            backoff_factor=2.0,
            retry_on=[500, 502, 503]
        )
        
        assert config.max_retries == 5
        assert config.backoff_factor == 2.0
        assert config.retry_on == [500, 502, 503]


class TestRateLimitConfig:
    """Test cases for RateLimitConfig dataclass."""
    
    def test_default_values(self):
        """Test default rate limit configuration."""
        config = RateLimitConfig()
        
        assert config.enabled is False
        assert config.requests_per_second == 10.0
        assert config.requests_per_minute == 600.0
        assert config.burst_size == 5
    
    def test_custom_values(self):
        """Test custom rate limit configuration."""
        config = RateLimitConfig(
            enabled=True,
            requests_per_second=2.0,
            burst_size=3
        )
        
        assert config.enabled is True
        assert config.requests_per_second == 2.0
        assert config.burst_size == 3


class TestRequestLog:
    """Test cases for RequestLog dataclass."""
    
    def test_request_log_creation(self):
        """Test creating a request log entry."""
        log = RequestLog(
            method="GET",
            url="https://api.example.com/users",
            headers={"Accept": "application/json"},
            body=None,
            timestamp=time.time()
        )
        
        assert log.method == "GET"
        assert log.url == "https://api.example.com/users"
        assert log.duration_ms == 0.0
        assert log.status is None


class TestBasePageError:
    """Test cases for BasePageError exception."""
    
    def test_error_with_context(self):
        """Test error with full context."""
        error = BasePageError(
            message="Request failed",
            url="https://api.example.com/users",
            method="GET",
            status=404,
            response_text='{"error": "Not found"}'
        )
        
        assert "Request failed" in str(error)
        assert "GET" in str(error)
        assert "404" in str(error)
        assert "Not found" in str(error)
    
    def test_error_without_context(self):
        """Test error without context."""
        error = BasePageError(message="Simple error")
        
        assert "Simple error" in str(error)


class TestHttpMethods:
    """Test cases for HTTP methods."""
    
    @pytest.fixture
    def mock_page(self):
        """Create a BasePage with mocked Playwright."""
        with patch('playwright.sync_api.sync_playwright') as mock_playwright:
            mock_context = MagicMock()
            mock_response = MockResponse(status=200, body={"id": 1})
            mock_context.get.return_value = mock_response
            mock_context.post.return_value = mock_response
            mock_context.put.return_value = mock_response
            mock_context.delete.return_value = mock_response
            mock_context.patch.return_value = mock_response
            
            mock_pw = MagicMock()
            mock_pw.request.new_context.return_value = mock_context
            
            mock_manager = MagicMock()
            mock_manager.__enter__ = MagicMock(return_value=mock_pw)
            mock_manager.__exit__ = MagicMock(return_value=False)
            mock_playwright.return_value = mock_manager
            
            page = BasePage("https://api.example.com")
            page.setup()
            
            yield page, mock_context
    
    def test_get_request(self, mock_page):
        """Test GET request."""
        page, mock_context = mock_page
        
        response = page.get("/users/123")
        
        mock_context.get.assert_called_once()
        assert response.status == 200
    
    def test_post_request(self, mock_page):
        """Test POST request."""
        page, mock_context = mock_page
        
        response = page.post("/users", json={"name": "John"})
        
        mock_context.post.assert_called_once()
        assert response.status == 200
    
    def test_put_request(self, mock_page):
        """Test PUT request."""
        page, mock_context = mock_page
        
        response = page.put("/users/123", json={"name": "Jane"})
        
        mock_context.put.assert_called_once()
        assert response.status == 200
    
    def test_delete_request(self, mock_page):
        """Test DELETE request."""
        page, mock_context = mock_page
        
        response = page.delete("/users/123")
        
        mock_context.delete.assert_called_once()
        assert response.status == 200
    
    def test_patch_request(self, mock_page):
        """Test PATCH request."""
        page, mock_context = mock_page
        
        response = page.patch("/users/123", json={"name": "Updated"})
        
        mock_context.patch.assert_called_once()
        assert response.status == 200


class TestAssertionMethods:
    """Test cases for assertion helper methods."""
    
    @pytest.fixture
    def mock_page(self):
        """Create a BasePage with mocked Playwright."""
        with patch('playwright.sync_api.sync_playwright'):
            page = BasePage("https://api.example.com")
            yield page
    
    def test_assert_status_success(self, mock_page):
        """Test assert_status with matching status."""
        response = MockResponse(status=200)
        page = mock_page
        
        result = page.assert_status(response, 200)
        
        assert result is response
    
    def test_assert_status_failure(self, mock_page):
        """Test assert_status with non-matching status."""
        response = MockResponse(status=404, body={"error": "Not found"})
        page = mock_page
        
        with pytest.raises(BasePageError) as exc_info:
            page.assert_status(response, 200)
        
        assert "404" in str(exc_info.value)
        assert "Expected status [200]" in str(exc_info.value)
    
    def test_assert_status_multiple_codes(self, mock_page):
        """Test assert_status with list of acceptable codes."""
        response = MockResponse(status=201)
        page = mock_page
        
        result = page.assert_status(response, [200, 201, 202])
        
        assert result is response
    
    def test_assert_ok_success(self, mock_page):
        """Test assert_ok with 2xx status."""
        response = MockResponse(status=201)
        page = mock_page
        
        result = page.assert_ok(response)
        
        assert result is response
    
    def test_assert_ok_failure(self, mock_page):
        """Test assert_ok with non-2xx status."""
        response = MockResponse(status=500, body={"error": "Server error"})
        page = mock_page
        
        with pytest.raises(BasePageError) as exc_info:
            page.assert_ok(response)
        
        assert "500" in str(exc_info.value)
        assert "Expected 2xx" in str(exc_info.value)
    
    def test_assert_json_success(self, mock_page):
        """Test assert_json with valid JSON."""
        response = MockResponse(status=200, body={"id": 1, "name": "John"})
        page = mock_page
        
        data = page.assert_json(response)
        
        assert data["id"] == 1
        assert data["name"] == "John"
    
    def test_assert_json_with_key(self, mock_page):
        """Test assert_json with key extraction."""
        response = MockResponse(status=200, body={"data": {"user": {"name": "John"}}})
        page = mock_page
        
        name = page.assert_json(response, key="data.user.name")
        
        assert name == "John"
    
    def test_assert_json_key_not_found(self, mock_page):
        """Test assert_json with non-existent key."""
        response = MockResponse(status=200, body={"id": 1})
        page = mock_page
        
        with pytest.raises(BasePageError) as exc_info:
            page.assert_json(response, key="nonexistent")
        
        assert "nonexistent" in str(exc_info.value)
    
    def test_assert_header_success(self, mock_page):
        """Test assert_header with matching header."""
        response = MockResponse(status=200, headers={"content-type": "application/json"})
        page = mock_page
        
        value = page.assert_header(response, "content-type")
        
        assert value == "application/json"
    
    def test_assert_header_with_value(self, mock_page):
        """Test assert_header with expected value."""
        response = MockResponse(status=200, headers={"content-type": "application/json"})
        page = mock_page
        
        value = page.assert_header(response, "content-type", "application/json")
        
        assert value == "application/json"
    
    def test_assert_header_not_found(self, mock_page):
        """Test assert_header with non-existent header."""
        response = MockResponse(status=200, headers={})
        page = mock_page
        
        with pytest.raises(BasePageError) as exc_info:
            page.assert_header(response, "x-custom-header")
        
        assert "x-custom-header" in str(exc_info.value)
    
    def test_assert_header_wrong_value(self, mock_page):
        """Test assert_header with wrong value."""
        response = MockResponse(status=200, headers={"content-type": "text/html"})
        page = mock_page
        
        with pytest.raises(BasePageError) as exc_info:
            page.assert_header(response, "content-type", "application/json")
        
        assert "text/html" in str(exc_info.value)
        assert "application/json" in str(exc_info.value)


class TestRequestLogging:
    """Test cases for request logging."""
    
    @pytest.fixture
    def mock_page_with_logging(self):
        """Create a BasePage with logging enabled."""
        with patch('playwright.sync_api.sync_playwright') as mock_playwright:
            mock_context = MagicMock()
            mock_response = MockResponse(status=200, body={"id": 1})
            mock_context.get.return_value = mock_response
            
            mock_pw = MagicMock()
            mock_pw.request.new_context.return_value = mock_context
            
            mock_manager = MagicMock()
            mock_manager.__enter__ = MagicMock(return_value=mock_pw)
            mock_manager.__exit__ = MagicMock(return_value=False)
            mock_playwright.return_value = mock_manager
            
            page = BasePage(
                "https://api.example.com",
                enable_request_logging=True
            )
            page.setup()
            
            yield page, mock_context
    
    def test_request_history_populated(self, mock_page_with_logging):
        """Test that request history is populated after requests."""
        page, mock_context = mock_page_with_logging
        
        page.get("/users/123")
        
        assert len(page.request_history) == 1
        assert page.request_history[0].method == "GET"
    
    def test_get_last_request(self, mock_page_with_logging):
        """Test getting the last request log."""
        page, mock_context = mock_page_with_logging
        
        page.get("/users/123")
        page.get("/users/456")
        
        last_request = page.get_last_request()
        
        assert last_request is not None
        assert "456" in last_request.url
    
    def test_get_request_stats_empty(self, mock_page_with_logging):
        """Test request stats with no requests."""
        page, _ = mock_page_with_logging
        page.request_history.clear()  # Clear any previous requests
        
        stats = page.get_request_stats()
        
        assert stats["total_requests"] == 0
        assert stats["successful_requests"] == 0
    
    def test_get_request_stats_with_requests(self, mock_page_with_logging):
        """Test request stats with multiple requests."""
        page, mock_context = mock_page_with_logging
        
        page.get("/users/123")
        page.get("/users/456")
        
        stats = page.get_request_stats()
        
        assert stats["total_requests"] == 2
        assert stats["successful_requests"] == 2
        assert stats["status_distribution"][200] == 2


class TestRateLimiting:
    """Test cases for rate limiting functionality."""
    
    def test_rate_limiting_applies_delay(self):
        """Test that rate limiting applies delays between requests."""
        with patch('playwright.sync_api.sync_playwright') as mock_playwright:
            mock_context = MagicMock()
            mock_context.get.return_value = MockResponse(status=200)
            
            mock_pw = MagicMock()
            mock_pw.request.new_context.return_value = mock_context
            
            mock_manager = MagicMock()
            mock_manager.__enter__ = MagicMock(return_value=mock_pw)
            mock_manager.__exit__ = MagicMock(return_value=False)
            mock_playwright.return_value = mock_manager
            
            rate_config = RateLimitConfig(
                enabled=True,
                requests_per_second=1.0,  # Very restrictive for testing
                burst_size=1
            )
            
            page = BasePage(
                "https://api.example.com",
                rate_limit_config=rate_config
            )
            page.setup()
            
            # First request should work immediately
            start = time.time()
            page.get("/users/1")
            
            # Second request should be delayed
            page.get("/users/2")
            duration = time.time() - start
            
            # Should have taken at least 1 second due to rate limiting
            assert duration >= 0.9  # Allow some tolerance


class TestBackwardsCompatibility:
    """Test backwards compatibility with old BasePage API."""
    
    @pytest.fixture
    def mock_page(self):
        """Create a BasePage with mocked Playwright."""
        with patch('playwright.sync_api.sync_playwright'):
            page = BasePage("https://api.example.com")
            yield page
    
    def test_from_config_factory(self):
        """Test from_config factory method."""
        from socialseed_e2e.core.models import ServiceConfig
        
        config = ServiceConfig(
            name="test-service",
            base_url="https://api.example.com",
            default_headers={"X-Custom": "value"}
        )
        
        with patch('playwright.sync_api.sync_playwright'):
            page = BasePage.from_config(config)
            
            assert page.base_url == "https://api.example.com"
            assert page.default_headers["X-Custom"] == "value"
    
    def test_get_response_text(self, mock_page):
        """Test get_response_text utility method."""
        response = MockResponse(status=200, body={"message": "Hello"})
        page = mock_page
        
        text = page.get_response_text(response)
        
        assert "Hello" in text
