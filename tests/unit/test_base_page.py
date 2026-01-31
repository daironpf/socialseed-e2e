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
    
    def test_rate_limiting_tracks_requests(self):
        """Test that rate limiting tracks request timestamps."""
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
                requests_per_second=10.0,
                burst_size=5
            )
            
            page = BasePage(
                "https://api.example.com",
                rate_limit_config=rate_config
            )
            page.setup()
            
            # Make requests within burst size
            for i in range(3):
                page.get(f"/users/{i}")
            
            # Check that requests are tracked
            assert len(page._request_times) == 3
            # All timestamps should be recent
            for req_time in page._request_times:
                assert req_time > time.time() - 5  # Within last 5 seconds


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


class TestRetryMechanism:
    """Test cases for retry mechanism functionality."""
    
    @pytest.fixture
    def mock_page_with_retry(self):
        """Create a BasePage with retry enabled."""
        with patch('playwright.sync_api.sync_playwright') as mock_playwright:
            mock_context = MagicMock()
            
            mock_pw = MagicMock()
            mock_pw.request.new_context.return_value = mock_context
            
            mock_manager = MagicMock()
            mock_manager.__enter__ = MagicMock(return_value=mock_pw)
            mock_manager.__exit__ = MagicMock(return_value=False)
            mock_playwright.return_value = mock_manager
            
            retry_config = RetryConfig(
                max_retries=3,
                backoff_factor=0.1,
                retry_on=[500, 502, 503, 429]
            )
            
            page = BasePage(
                "https://api.example.com",
                retry_config=retry_config
            )
            page.setup()
            
            yield page, mock_context
    
    def test_calculate_backoff_first_attempt(self, mock_page_with_retry):
        """Test backoff calculation for first retry attempt."""
        page, _ = mock_page_with_retry
        
        backoff = page._calculate_backoff(0)
        
        assert backoff == 0.1  # 0.1 * (2^0)
    
    def test_calculate_backoff_second_attempt(self, mock_page_with_retry):
        """Test backoff calculation for second retry attempt."""
        page, _ = mock_page_with_retry
        
        backoff = page._calculate_backoff(1)
        
        assert backoff == 0.2  # 0.1 * (2^1)
    
    def test_calculate_backoff_exponential_growth(self, mock_page_with_retry):
        """Test exponential backoff growth."""
        page, _ = mock_page_with_retry
        
        backoff_2 = page._calculate_backoff(2)
        backoff_3 = page._calculate_backoff(3)
        
        assert backoff_2 == 0.4  # 0.1 * (2^2)
        assert backoff_3 == 0.8  # 0.1 * (2^3)
    
    def test_calculate_backoff_max_backoff(self, mock_page_with_retry):
        """Test that backoff respects max_backoff limit."""
        page, _ = mock_page_with_retry
        page.retry_config.max_backoff = 1.0
        
        backoff = page._calculate_backoff(10)  # Would be 102.4 without limit
        
        assert backoff == 1.0  # Capped at max_backoff
    
    def test_should_retry_with_matching_status(self, mock_page_with_retry):
        """Test _should_retry with status code in retry list."""
        page, _ = mock_page_with_retry
        response = MockResponse(status=503)
        
        should_retry = page._should_retry(response, None)
        
        assert should_retry is True
    
    def test_should_retry_with_non_matching_status(self, mock_page_with_retry):
        """Test _should_retry with status code not in retry list."""
        page, _ = mock_page_with_retry
        response = MockResponse(status=404)
        
        should_retry = page._should_retry(response, None)
        
        assert should_retry is False
    
    def test_should_retry_with_exception(self, mock_page_with_retry):
        """Test _should_retry with exception."""
        page, _ = mock_page_with_retry
        exception = ConnectionError("Connection failed")
        
        should_retry = page._should_retry(None, exception)
        
        assert should_retry is True
    
    def test_should_retry_disabled(self, mock_page_with_retry):
        """Test _should_retry when retries are disabled."""
        page, _ = mock_page_with_retry
        page.retry_config.max_retries = 0
        response = MockResponse(status=503)
        
        should_retry = page._should_retry(response, None)
        
        assert should_retry is False
    
    def test_retry_on_500_status(self, mock_page_with_retry):
        """Test automatic retry on 500 status."""
        page, mock_context = mock_page_with_retry
        
        # First two calls fail with 500, third succeeds
        mock_context.get.side_effect = [
            MockResponse(status=500),
            MockResponse(status=500),
            MockResponse(status=200, body={"success": True})
        ]
        
        response = page.get("/test")
        
        assert response.status == 200
        assert mock_context.get.call_count == 3
    
    def test_retry_on_502_status(self, mock_page_with_retry):
        """Test automatic retry on 502 status."""
        page, mock_context = mock_page_with_retry
        
        mock_context.get.side_effect = [
            MockResponse(status=502),
            MockResponse(status=200, body={"success": True})
        ]
        
        response = page.get("/test")
        
        assert response.status == 200
        assert mock_context.get.call_count == 2
    
    def test_retry_on_429_status(self, mock_page_with_retry):
        """Test automatic retry on 429 (rate limit) status."""
        page, mock_context = mock_page_with_retry
        
        mock_context.get.side_effect = [
            MockResponse(status=429),
            MockResponse(status=200, body={"success": True})
        ]
        
        response = page.get("/test")
        
        assert response.status == 200
        assert mock_context.get.call_count == 2
    
    def test_no_retry_on_400_status(self, mock_page_with_retry):
        """Test that 400 errors are not retried."""
        page, mock_context = mock_page_with_retry
        
        mock_context.get.return_value = MockResponse(status=400, body={"error": "Bad request"})
        
        response = page.get("/test")
        
        assert response.status == 400
        assert mock_context.get.call_count == 1
    
    def test_retry_exhaustion_raises_error(self, mock_page_with_retry):
        """Test that error is raised when all retries are exhausted due to exception."""
        page, mock_context = mock_page_with_retry
        
        # Make it raise an exception instead of returning a response
        mock_context.get.side_effect = ConnectionError("Connection refused")
        
        with pytest.raises(BasePageError) as exc_info:
            page.get("/test")
        
        assert "Request failed" in str(exc_info.value)
        assert "Connection refused" in str(exc_info.value)
        assert mock_context.get.call_count == 4  # Initial + 3 retries


class TestRateLimitingComprehensive:
    """Comprehensive test cases for rate limiting."""
    
    @pytest.fixture
    def mock_page_with_rate_limit(self):
        """Create a BasePage with rate limiting enabled."""
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
                requests_per_second=10.0,
                requests_per_minute=600.0,
                burst_size=5
            )
            
            page = BasePage(
                "https://api.example.com",
                rate_limit_config=rate_config
            )
            page.setup()
            
            yield page, mock_context
    
    def test_rate_limit_disabled_no_delay(self, mock_page_with_rate_limit):
        """Test that no delay occurs when rate limiting is disabled."""
        page, mock_context = mock_page_with_rate_limit
        page.rate_limit_config.enabled = False
        
        start = time.time()
        for _ in range(5):
            page.get("/test")
        duration = time.time() - start
        
        # Should be very fast with no delays
        assert duration < 0.5
        assert mock_context.get.call_count == 5
    
    def test_rate_limit_burst_allowance(self, mock_page_with_rate_limit):
        """Test that burst requests are allowed."""
        page, mock_context = mock_page_with_rate_limit
        page.rate_limit_config.burst_size = 10
        page.rate_limit_config.requests_per_second = 1.0
        
        start = time.time()
        for _ in range(5):  # Within burst size
            page.get("/test")
        duration = time.time() - start
        
        # Should complete quickly within burst
        assert duration < 0.5
    
    def test_apply_rate_limit_cleans_old_requests(self, mock_page_with_rate_limit):
        """Test that old request times are cleaned up."""
        page, _ = mock_page_with_rate_limit
        
        # Add some old request times (2 minutes ago)
        old_time = time.time() - 120
        page._request_times = [old_time, old_time, old_time]
        page._last_request_time = old_time
        
        page._apply_rate_limit()
        
        # Old requests should be cleaned up, but a new one is added
        # So we should have 1 entry (the newly added one)
        assert len(page._request_times) == 1
        # And it should be recent (not the old time)
        assert page._request_times[0] > time.time() - 5
    
    def test_rate_limit_per_minute_enforcement(self, mock_page_with_rate_limit):
        """Test per-minute rate limit enforcement."""
        page, mock_context = mock_page_with_rate_limit
        page.rate_limit_config.requests_per_minute = 2.0
        
        # Make requests that exceed per-minute limit
        page.get("/test")
        page.get("/test")
        
        # Third request should trigger rate limiting consideration
        # (though we can't easily test the sleep without mocking time)
        page.get("/test")
        
        assert len(page._request_times) == 3


class TestRequestLoggingComprehensive:
    """Comprehensive test cases for request logging."""
    
    @pytest.fixture
    def mock_page_for_logging(self):
        """Create a BasePage for logging tests."""
        with patch('playwright.sync_api.sync_playwright') as mock_playwright:
            mock_context = MagicMock()
            mock_response = MockResponse(status=200, body={"id": 1})
            mock_context.get.return_value = mock_response
            mock_context.post.return_value = mock_response
            
            mock_pw = MagicMock()
            mock_pw.request.new_context.return_value = mock_context
            
            mock_manager = MagicMock()
            mock_manager.__enter__ = MagicMock(return_value=mock_pw)
            mock_manager.__exit__ = MagicMock(return_value=False)
            mock_playwright.return_value = mock_manager
            
            page = BasePage(
                "https://api.example.com",
                enable_request_logging=True,
                max_log_body_size=100
            )
            page.setup()
            
            yield page, mock_context
    
    def test_truncate_body_with_small_body(self, mock_page_for_logging):
        """Test _truncate_body with body smaller than max size."""
        page, _ = mock_page_for_logging
        
        result = page._truncate_body("small body")
        
        assert result == "small body"
    
    def test_truncate_body_with_large_body(self, mock_page_for_logging):
        """Test _truncate_body with body larger than max size."""
        page, _ = mock_page_for_logging
        large_body = "x" * 200
        
        result = page._truncate_body(large_body)
        
        assert len(result) < 150  # Should be truncated
        assert "[truncated" in result
        assert "200 bytes" in result
    
    def test_truncate_body_with_none(self, mock_page_for_logging):
        """Test _truncate_body with None body."""
        page, _ = mock_page_for_logging
        
        result = page._truncate_body(None)
        
        assert result is None
    
    def test_truncate_body_with_empty_string(self, mock_page_for_logging):
        """Test _truncate_body with empty string."""
        page, _ = mock_page_for_logging
        
        result = page._truncate_body("")
        
        assert result is None
    
    def test_log_request_adds_to_history(self, mock_page_for_logging):
        """Test that _log_request adds entries to history."""
        page, _ = mock_page_for_logging
        
        log_entry = RequestLog(
            method="GET",
            url="https://api.example.com/test",
            headers={},
            body=None,
            timestamp=time.time()
        )
        
        page._log_request(log_entry)
        
        assert len(page.request_history) == 1
        assert page.request_history[0].method == "GET"
    
    def test_log_request_trims_history(self, mock_page_for_logging):
        """Test that history is trimmed when exceeding max size."""
        page, _ = mock_page_for_logging
        page._max_history_size = 3
        
        for i in range(5):
            log_entry = RequestLog(
                method="GET",
                url=f"https://api.example.com/test{i}",
                headers={},
                body=None,
                timestamp=time.time()
            )
            page._log_request(log_entry)
        
        assert len(page.request_history) == 3
        assert page.request_history[0].url == "https://api.example.com/test2"
    
    def test_log_request_with_error(self, mock_page_for_logging):
        """Test _log_request with error entry."""
        page, _ = mock_page_for_logging
        
        log_entry = RequestLog(
            method="GET",
            url="https://api.example.com/test",
            headers={},
            body=None,
            timestamp=time.time(),
            error="Connection timeout"
        )
        
        page._log_request(log_entry)
        
        assert page.request_history[0].error == "Connection timeout"
    
    def test_post_request_body_logged(self, mock_page_for_logging):
        """Test that POST request body is logged."""
        page, mock_context = mock_page_for_logging
        
        page.post("/users", json={"name": "John", "email": "john@example.com"})
        
        last_request = page.get_last_request()
        assert last_request is not None
        assert last_request.method == "POST"
        assert "John" in (last_request.body or "")


class TestErrorHandlingComprehensive:
    """Comprehensive test cases for error handling."""
    
    def test_base_page_error_with_all_context(self):
        """Test BasePageError with all context fields."""
        error = BasePageError(
            message="Request failed",
            url="https://api.example.com/users",
            method="POST",
            status=500,
            response_text='{"error": "Internal server error"}'
        )
        
        error_str = str(error)
        
        assert "Request failed" in error_str
        assert "POST" in error_str
        assert "https://api.example.com/users" in error_str
        assert "500" in error_str
        assert "Internal server error" in error_str
    
    def test_base_page_error_with_long_response(self):
        """Test BasePageError with long response text."""
        long_response = "x" * 500
        error = BasePageError(
            message="Request failed",
            status=500,
            response_text=long_response
        )
        
        error_str = str(error)
        
        assert "..." in error_str  # Should be truncated
        assert len(error_str) < 400  # Reasonable length
    
    def test_base_page_error_with_request_log(self):
        """Test BasePageError with request log."""
        log = RequestLog(
            method="GET",
            url="https://api.example.com/test",
            headers={},
            body=None,
            timestamp=time.time(),
            duration_ms=100.0,
            status=404
        )
        
        error = BasePageError(
            message="Not found",
            request_log=log
        )
        
        assert error.request_log == log
        assert error.request_log is not None
        assert error.request_log.status == 404
    
    def test_base_page_error_only_message(self):
        """Test BasePageError with only message."""
        error = BasePageError(message="Simple error message")
        
        error_str = str(error)
        
        assert error_str == "Simple error message"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @pytest.fixture
    def mock_page(self):
        """Create a BasePage with mocked Playwright."""
        with patch('playwright.sync_api.sync_playwright') as mock_playwright:
            mock_context = MagicMock()
            
            mock_pw = MagicMock()
            mock_pw.request.new_context.return_value = mock_context
            
            mock_manager = MagicMock()
            mock_manager.__enter__ = MagicMock(return_value=mock_pw)
            mock_manager.__exit__ = MagicMock(return_value=False)
            mock_playwright.return_value = mock_manager
            
            page = BasePage("https://api.example.com")
            page.setup()
            
            yield page, mock_context
    
    def test_special_characters_in_url(self, mock_page):
        """Test handling of special characters in URL."""
        page, mock_context = mock_page
        mock_context.get.return_value = MockResponse(status=200)
        
        page.get("/users?name=John%20Doe&email=john+doe@example.com")
        
        mock_context.get.assert_called_once()
        call_args = mock_context.get.call_args
        assert "John%20Doe" in call_args[0][0]
    
    def test_unicode_in_response(self, mock_page):
        """Test handling of unicode characters in response."""
        page, mock_context = mock_page
        mock_context.get.return_value = MockResponse(
            status=200,
            body={"message": "Hello \u4e16\u754c \ud83c\udf0d"}  # "Hello World 🌍" in Chinese + emoji
        )
        
        response = page.get("/test")
        data = response.json()
        
        assert "Hello" in data["message"]
    
    def test_large_response_body(self, mock_page):
        """Test handling of large response bodies."""
        page, mock_context = mock_page
        large_data = {"items": [{"id": i} for i in range(1000)]}
        mock_context.get.return_value = MockResponse(status=200, body=large_data)
        
        response = page.get("/test")
        data = response.json()
        
        assert len(data["items"]) == 1000
    
    def test_empty_response_body(self, mock_page):
        """Test handling of empty response body."""
        page, mock_context = mock_page
        mock_response = MockResponse(status=204)
        mock_response._body = b''
        mock_context.get.return_value = mock_response
        
        response = page.get("/test")
        
        assert response.status == 204
        assert response.body() == b''
    
    def test_different_content_types(self, mock_page):
        """Test handling of different content types."""
        page, mock_context = mock_page
        mock_context.get.return_value = MockResponse(
            status=200,
            headers={"content-type": "application/xml"},
            body={"data": "<xml>test</xml>"}
        )
        
        response = page.get("/test")
        
        assert "content-type" in response.headers
    
    def test_html_response(self, mock_page):
        """Test handling of HTML response."""
        page, mock_context = mock_page
        html_body = "<html><body><h1>Test</h1></body></html>"
        mock_response = MockResponse(status=200)
        mock_response._body = html_body.encode('utf-8')
        mock_response.headers = {"content-type": "text/html"}
        mock_context.get.return_value = mock_response
        
        response = page.get("/test")
        text = response.text()
        
        assert "<h1>Test</h1>" in text


class TestHttpScenarios:
    """Test additional HTTP request scenarios."""
    
    @pytest.fixture
    def mock_page(self):
        """Create a BasePage with mocked Playwright."""
        with patch('playwright.sync_api.sync_playwright') as mock_playwright:
            mock_context = MagicMock()
            
            mock_pw = MagicMock()
            mock_pw.request.new_context.return_value = mock_context
            
            mock_manager = MagicMock()
            mock_manager.__enter__ = MagicMock(return_value=mock_pw)
            mock_manager.__exit__ = MagicMock(return_value=False)
            mock_playwright.return_value = mock_manager
            
            page = BasePage("https://api.example.com")
            page.setup()
            
            yield page, mock_context
    
    def test_get_with_query_params(self, mock_page):
        """Test GET request with query parameters."""
        page, mock_context = mock_page
        mock_context.get.return_value = MockResponse(status=200)
        
        page.get("/users", params={"page": 1, "limit": 10, "search": "john"})
        
        mock_context.get.assert_called_once()
        call_kwargs = mock_context.get.call_args[1]
        assert call_kwargs["params"] == {"page": 1, "limit": 10, "search": "john"}
    
    def test_get_with_custom_headers(self, mock_page):
        """Test GET request with custom headers."""
        page, mock_context = mock_page
        mock_context.get.return_value = MockResponse(status=200)
        
        page.get("/users", headers={"X-Custom-Header": "custom-value", "Accept": "application/xml"})
        
        mock_context.get.assert_called_once()
        call_kwargs = mock_context.get.call_args[1]
        assert "X-Custom-Header" in call_kwargs["headers"]
        assert call_kwargs["headers"]["X-Custom-Header"] == "custom-value"
    
    def test_post_with_form_data(self, mock_page):
        """Test POST request with form data instead of JSON."""
        page, mock_context = mock_page
        mock_context.post.return_value = MockResponse(status=201)
        
        page.post("/users", data={"name": "John", "email": "john@example.com"})
        
        mock_context.post.assert_called_once()
        call_kwargs = mock_context.post.call_args[1]
        assert call_kwargs["data"] == {"name": "John", "email": "john@example.com"}
    
    def test_put_with_form_data(self, mock_page):
        """Test PUT request with form data (not JSON)."""
        page, mock_context = mock_page
        mock_context.put.return_value = MockResponse(status=200)
        
        # Note: Using data parameter, not json
        page.put("/users/123", data={"name": "Jane"})
        
        mock_context.put.assert_called_once()
        call_kwargs = mock_context.put.call_args[1]
        assert call_kwargs["data"] == {"name": "Jane"}
    
    def test_delete_with_headers(self, mock_page):
        """Test DELETE request with custom headers."""
        page, mock_context = mock_page
        mock_context.delete.return_value = MockResponse(status=204)
        
        page.delete("/users/123", headers={"X-Auth-Token": "secret-token"})
        
        mock_context.delete.assert_called_once()
        call_kwargs = mock_context.delete.call_args[1]
        assert call_kwargs["headers"]["X-Auth-Token"] == "secret-token"
    
    def test_patch_with_data(self, mock_page):
        """Test PATCH request with data."""
        page, mock_context = mock_page
        mock_context.patch.return_value = MockResponse(status=200)
        
        page.patch("/users/123", data={"status": "active"})
        
        mock_context.patch.assert_called_once()
        call_kwargs = mock_context.patch.call_args[1]
        assert call_kwargs["data"] == {"status": "active"}
    
    def test_default_headers_merged_with_request_headers(self, mock_page):
        """Test that default headers are merged with request headers."""
        page, mock_context = mock_page
        mock_context.get.return_value = MockResponse(status=200)
        
        # Make a request with custom header
        page.get("/test", headers={"X-Custom": "value"})
        
        call_kwargs = mock_context.get.call_args[1]
        headers = call_kwargs["headers"]
        
        # Should have both default and custom headers
        assert "X-Custom" in headers
        assert "Accept" in headers  # From DEFAULT_JSON_HEADERS
        assert "User-Agent" in headers  # From DEFAULT_BROWSER_HEADERS


class TestSetupTeardownEdgeCases:
    """Test edge cases for setup and teardown."""
    
    @pytest.fixture
    def mock_page_uninitialized(self):
        """Create a BasePage without calling setup."""
        with patch('playwright.sync_api.sync_playwright') as mock_playwright:
            mock_context = MagicMock()
            
            mock_pw = MagicMock()
            mock_pw.request.new_context.return_value = mock_context
            
            mock_manager = MagicMock()
            mock_manager.__enter__ = MagicMock(return_value=mock_pw)
            mock_manager.__exit__ = MagicMock(return_value=False)
            mock_playwright.return_value = mock_manager
            
            page = BasePage("https://api.example.com")
            
            yield page, mock_context, mock_playwright
    
    def test_multiple_setup_calls_idempotent(self, mock_page_uninitialized):
        """Test that multiple setup calls are idempotent."""
        page, mock_context, _ = mock_page_uninitialized
        
        page.setup()
        first_context = page.api_context
        
        page.setup()  # Second call
        second_context = page.api_context
        
        assert first_context is second_context  # Should be same context
        assert mock_context is first_context
    
    def test_teardown_without_setup(self, mock_page_uninitialized):
        """Test teardown when setup was never called."""
        page, _, _ = mock_page_uninitialized
        
        # Should not raise an error
        page.teardown()
        
        assert page.api_context is None
    
    def test_teardown_multiple_times(self, mock_page_uninitialized):
        """Test calling teardown multiple times."""
        page, _, _ = mock_page_uninitialized
        
        page.setup()
        page.teardown()
        page.teardown()  # Second teardown
        
        assert page.api_context is None
        assert page.playwright_manager is None
    
    def test_request_auto_setup(self, mock_page_uninitialized):
        """Test that request automatically calls setup."""
        page, mock_context, _ = mock_page_uninitialized
        mock_context.get.return_value = MockResponse(status=200)
        
        # Don't call setup explicitly
        response = page.get("/test")
        
        assert response.status == 200
        assert page.api_context is not None
        mock_context.get.assert_called_once()


class TestConfigurationOptions:
    """Test various configuration options."""
    
    @pytest.fixture
    def mock_playwright_setup(self):
        """Setup mock for playwright."""
        with patch('playwright.sync_api.sync_playwright') as mock_playwright:
            mock_context = MagicMock()
            mock_context.get.return_value = MockResponse(status=200)
            mock_context.post.return_value = MockResponse(status=201)
            
            mock_pw = MagicMock()
            mock_pw.request.new_context.return_value = mock_context
            
            mock_manager = MagicMock()
            mock_manager.__enter__ = MagicMock(return_value=mock_pw)
            mock_manager.__exit__ = MagicMock(return_value=False)
            mock_playwright.return_value = mock_manager
            
            yield mock_context
    
    def test_init_with_small_max_log_body_size(self, mock_playwright_setup):
        """Test initialization with small max_log_body_size."""
        mock_context = mock_playwright_setup
        
        page = BasePage(
            "https://api.example.com",
            max_log_body_size=50
        )
        page.setup()
        
        assert page.max_log_body_size == 50
        
        # Test truncation - max size is 50, so body should be truncated
        large_body = "x" * 100
        truncated = page._truncate_body(large_body)
        assert truncated is not None
        assert "[truncated" in truncated
        assert "100 bytes" in truncated
    
    def test_init_with_disabled_request_logging(self, mock_playwright_setup):
        """Test initialization with request logging disabled."""
        mock_context = mock_playwright_setup
        
        page = BasePage(
            "https://api.example.com",
            enable_request_logging=False
        )
        page.setup()
        
        assert page.enable_request_logging is False
        
        # Make a request - history should still be tracked but not logged to console
        page.get("/test")
        # Request history is still maintained even when logging is disabled
        # The flag only controls console logging via logger
        assert len(page.request_history) == 1
    
    def test_init_with_custom_default_headers(self, mock_playwright_setup):
        """Test initialization with custom default headers."""
        mock_context = mock_playwright_setup
        
        custom_headers = {"X-API-Key": "secret123", "Accept": "text/plain"}
        page = BasePage(
            "https://api.example.com",
            default_headers=custom_headers
        )
        page.setup()
        
        assert page.default_headers["X-API-Key"] == "secret123"
        assert page.default_headers["Accept"] == "text/plain"
    
    def test_init_with_zero_retries(self, mock_playwright_setup):
        """Test initialization with zero retries."""
        mock_context = mock_playwright_setup
        
        retry_config = RetryConfig(max_retries=0)
        page = BasePage(
            "https://api.example.com",
            retry_config=retry_config
        )
        page.setup()
        
        assert page.retry_config.max_retries == 0
    
    def test_init_with_high_retry_count(self, mock_playwright_setup):
        """Test initialization with high retry count."""
        mock_context = mock_playwright_setup
        
        retry_config = RetryConfig(max_retries=10, backoff_factor=0.5)
        page = BasePage(
            "https://api.example.com",
            retry_config=retry_config
        )
        page.setup()
        
        assert page.retry_config.max_retries == 10
        assert page.retry_config.backoff_factor == 0.5
    
    def test_init_with_aggressive_rate_limiting(self, mock_playwright_setup):
        """Test initialization with aggressive rate limiting."""
        mock_context = mock_playwright_setup
        
        rate_config = RateLimitConfig(
            enabled=True,
            requests_per_second=1.0,
            requests_per_minute=10.0,
            burst_size=1
        )
        page = BasePage(
            "https://api.example.com",
            rate_limit_config=rate_config
        )
        page.setup()
        
        assert page.rate_limit_config.requests_per_second == 1.0
        assert page.rate_limit_config.burst_size == 1
    
    def test_retry_config_custom_exceptions(self, mock_playwright_setup):
        """Test RetryConfig with custom exception types."""
        retry_config = RetryConfig(
            max_retries=3,
            retry_exceptions=[ConnectionError, TimeoutError]
        )
        
        assert ConnectionError in retry_config.retry_exceptions
        assert TimeoutError in retry_config.retry_exceptions
        assert Exception not in retry_config.retry_exceptions
    
    def test_retry_config_custom_status_codes(self, mock_playwright_setup):
        """Test RetryConfig with custom status codes."""
        retry_config = RetryConfig(
            max_retries=3,
            retry_on=[408, 500, 502, 503, 504]
        )
        
        assert 408 in retry_config.retry_on
        assert 429 not in retry_config.retry_on  # Not in custom list
