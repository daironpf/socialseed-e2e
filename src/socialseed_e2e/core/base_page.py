"""Enhanced BasePage with logging, retries, and rate limiting.

This module provides an enhanced BasePage class for API testing with
production-ready features including structured logging, automatic retries,
rate limiting, and comprehensive request/response logging.
"""

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Type, Union

from playwright.sync_api import APIRequestContext, APIResponse, Playwright

from socialseed_e2e.core.headers import DEFAULT_BROWSER_HEADERS, DEFAULT_JSON_HEADERS
from socialseed_e2e.core.models import ServiceConfig

# Configure logger
logger = logging.getLogger(__name__)


@dataclass
class RetryConfig:
    """Configuration for automatic retry mechanism.

    Attributes:
        max_retries: Maximum number of retry attempts (default: 3)
        backoff_factor: Exponential backoff multiplier (default: 1.0)
        max_backoff: Maximum backoff time in seconds (default: 60)
        retry_on: List of HTTP status codes to retry on (default: [502, 503, 504, 429])
        retry_exceptions: List of exception types to retry on
    """

    max_retries: int = 3
    backoff_factor: float = 1.0
    max_backoff: float = 60.0
    retry_on: Optional[List[int]] = None
    retry_exceptions: Optional[List[Type[Exception]]] = None

    def __post_init__(self):
        """Initialize default retry configuration values."""
        if self.retry_on is None:
            self.retry_on = [502, 503, 504, 429]  # Include 429 (rate limit)
        if self.retry_exceptions is None:
            self.retry_exceptions = [Exception]


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting.

    Attributes:
        enabled: Whether rate limiting is enabled (default: False)
        requests_per_second: Maximum requests per second (default: 10)
        requests_per_minute: Maximum requests per minute (default: 600)
        burst_size: Allow burst of requests (default: 5)
    """

    enabled: bool = False
    requests_per_second: float = 10.0
    requests_per_minute: float = 600.0
    burst_size: int = 5


@dataclass
class RequestLog:
    """Log entry for a single request.

    Attributes:
        method: HTTP method
        url: Full request URL
        headers: Request headers (may be filtered)
        body: Request body (JSON string)
        timestamp: When the request was made
        duration_ms: Request duration in milliseconds
        status: Response status code
        response_headers: Response headers
        response_body: Response body (truncated if too large)
        error: Error message if request failed
    """

    method: str
    url: str
    headers: Dict[str, str]
    body: Optional[str]
    timestamp: float
    duration_ms: float = 0.0
    status: Optional[int] = None
    response_headers: Optional[Dict[str, str]] = None
    response_body: Optional[str] = None
    error: Optional[str] = None


@dataclass
class ServiceHealth:
    """Service health status.

    Attributes:
        healthy: Whether the service is healthy
        status_code: HTTP status code from health check
        response_time_ms: Response time in milliseconds
        message: Health check message
        timestamp: When the check was performed
    """

    healthy: bool
    status_code: Optional[int] = None
    response_time_ms: float = 0.0
    message: str = ""
    timestamp: float = field(default_factory=time.time)


class BasePageError(Exception):
    """Enhanced exception with request context."""

    def __init__(
        self,
        message: str,
        url: Optional[str] = None,
        method: Optional[str] = None,
        status: Optional[int] = None,
        response_text: Optional[str] = None,
        request_log: Optional[RequestLog] = None,
    ):
        """Initialize exception with request context."""
        super().__init__(message)
        self.url = url
        self.method = method
        self.status = status
        self.response_text = response_text
        self.request_log = request_log

    def __str__(self) -> str:
        """Return formatted error message with context."""
        parts = [super().__str__()]
        if self.method and self.url:
            parts.append(f"Request: {self.method} {self.url}")
        if self.status:
            parts.append(f"Status: {self.status}")
        if self.response_text:
            preview = self.response_text[:200]
            if len(self.response_text) > 200:
                preview += "..."
            parts.append(f"Response: {preview}")
        return "\n  ".join(parts)


class BasePage:
    """Enhanced base class for API testing with logging, retries, and rate limiting.

    This class extends the basic API testing capabilities with production-ready
    features including:

    - Structured logging of all requests and responses
    - Automatic retry mechanism with exponential backoff
    - Rate limiting to avoid overwhelming APIs
    - Request timing and performance metrics
    - Enhanced error messages with full context
    - Helper methods for common assertions
    - Service health checking

    Example:
        >>> page = BasePage("https://api.example.com")
        >>> page.setup()
        >>>
        >>> # Enable retries for transient failures
        >>> page.retry_config = RetryConfig(max_retries=3)
        >>>
        >>> # Enable rate limiting
        >>> page.rate_limit_config = RateLimitConfig(
        ...     enabled=True,
        ...     requests_per_second=5
        ... )
        >>>
        >>> # Make request with automatic retry and logging
        >>> response = page.get("/users/123")
        >>>
        >>> # Use helper methods for assertions
        >>> page.assert_status(response, 200)
        >>> user = page.assert_json(response)
        >>>
        >>> page.teardown()

    Attributes:
        base_url: The base URL for the API
        default_headers: Headers applied to all requests
        retry_config: Configuration for automatic retries
        rate_limit_config: Configuration for rate limiting
        enable_request_logging: Whether to log all requests
        max_log_body_size: Maximum size for logged request/response bodies
        request_history: List of RequestLog entries for recent requests
    """

    def __init__(
        self,
        base_url: str,
        playwright: Optional[Playwright] = None,
        default_headers: Optional[Dict[str, str]] = None,
        retry_config: Optional[RetryConfig] = None,
        rate_limit_config: Optional[RateLimitConfig] = None,
        enable_request_logging: bool = True,
        max_log_body_size: int = 10000,
        health_endpoint: str = "/actuator/health",
    ) -> None:
        """Initialize the BasePage.

        Args:
            base_url: The base URL for the API (e.g., "https://api.example.com")
            playwright: Optional Playwright instance (created if not provided)
            default_headers: Headers to include in all requests
            retry_config: Configuration for automatic retries (default: no retries)
            rate_limit_config: Configuration for rate limiting (default: disabled)
            enable_request_logging: Whether to log requests and responses
            max_log_body_size: Maximum size for logged bodies (truncated if larger)
            health_endpoint: Endpoint for health checks (default: /actuator/health)
        """
        self.base_url: str = base_url.rstrip("/")
        self.playwright_manager: Optional[Any] = None
        self.playwright: Optional[Playwright] = None
        self.default_headers = (
            default_headers
            if default_headers is not None
            else {**DEFAULT_JSON_HEADERS, **DEFAULT_BROWSER_HEADERS}
        )
        self.headers = self.default_headers  # Alias for easier access in tests
        self.health_endpoint = health_endpoint

        # Initialize Playwright
        if playwright:
            self.playwright = playwright
        else:
            self.playwright_manager = __import__("playwright").sync_api.sync_playwright()
            self.playwright = self.playwright_manager.__enter__()

        self.api_context: Optional[APIRequestContext] = None

        # Configuration
        self.retry_config = retry_config or RetryConfig(max_retries=0)
        self.rate_limit_config = rate_limit_config or RateLimitConfig(enabled=False)
        self.enable_request_logging = enable_request_logging
        self.max_log_body_size = max_log_body_size

        # Rate limiting state
        self._request_times: List[float] = []
        self._last_request_time: float = 0.0

        # Request history (last 100 requests)
        self.request_history: List[RequestLog] = []
        self._max_history_size = 100

        # Response interceptors
        self._response_interceptors: List[Callable[[APIResponse], None]] = []

        logger.info(f"BasePage initialized for {self.base_url}")

    @classmethod
    def from_config(
        cls, config: ServiceConfig, playwright: Optional[Playwright] = None, **kwargs
    ) -> "BasePage":
        """Create a BasePage from a ServiceConfig object.

        Args:
            config: Service configuration object
            playwright: Optional Playwright instance
            **kwargs: Additional arguments passed to BasePage constructor
        Returns:
            Configured BasePage instance
        """
        return cls(
            base_url=config.base_url,
            playwright=playwright,
            default_headers=config.default_headers,
            health_endpoint=getattr(config, "health_endpoint", "/actuator/health"),
            **kwargs,
        )

    def setup(self) -> None:
        """Initialize the API context.

        This method creates the Playwright APIRequestContext. It is called
        automatically before making requests if not already set up.
        """
        if not self.api_context:
            assert self.playwright is not None
            self.api_context = self.playwright.request.new_context()
            logger.debug("API context initialized")

    def teardown(self) -> None:
        """Clean up the API context and resources.

        Always call this method when done to release resources properly.
        """
        if self.api_context:
            self.api_context.dispose()
            self.api_context = None
            logger.debug("API context disposed")

        if self.playwright_manager:
            self.playwright_manager.__exit__(None, None, None)
            self.playwright_manager = None
            self.playwright = None
            logger.debug("Playwright manager cleaned up")

        logger.info("BasePage teardown complete")

    def _ensure_setup(self) -> None:
        """Ensure API context is set up before making requests."""
        if not self.api_context:
            self.setup()

    def _prepare_headers(self, headers: Optional[Dict[str, str]]) -> Dict[str, str]:
        """Combine active headers with request-specific headers.

        Args:
            headers: Request-specific headers to merge with defaults

        Returns:
            Merged headers dictionary
        """
        request_headers = self.headers.copy()
        if headers:
            request_headers.update(headers)
        return request_headers

    def _apply_rate_limit(self) -> None:
        """Apply rate limiting before making a request.

        This method enforces the configured rate limits by sleeping
        if necessary to maintain the desired request rate.
        """
        if not self.rate_limit_config.enabled:
            return

        now = time.time()

        # Clean up old request times (older than 1 minute)
        cutoff = now - 60.0
        self._request_times = [t for t in self._request_times if t > cutoff]

        # Check per-minute limit
        if len(self._request_times) >= self.rate_limit_config.requests_per_minute:
            sleep_time = 60.0 - (now - self._request_times[0])
            if sleep_time > 0:
                logger.warning(f"Rate limit (per minute) reached, sleeping for {sleep_time:.2f}s")
                time.sleep(sleep_time)

        # Check per-second limit with burst allowance
        recent_requests = len([t for t in self._request_times if t > now - 1.0])
        if (
            recent_requests
            >= self.rate_limit_config.requests_per_second + self.rate_limit_config.burst_size
        ):
            sleep_time = 1.0 / self.rate_limit_config.requests_per_second
            logger.warning(f"Rate limit (per second) reached, sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)

        # Update request tracking
        self._request_times.append(now)
        self._last_request_time = now

    def _calculate_backoff(self, attempt: int) -> float:
        """Calculate exponential backoff time.

        Args:
            attempt: Current retry attempt number (0-indexed)

        Returns:
            Sleep time in seconds
        """
        backoff = self.retry_config.backoff_factor * (2**attempt)
        return float(min(backoff, self.retry_config.max_backoff))

    def _should_retry(
        self, response: Optional[APIResponse], exception: Optional[Exception]
    ) -> bool:
        """Determine if a request should be retried.

        Args:
            response: The API response (None if exception occurred)
            exception: The exception that occurred (None if successful)

        Returns:
            True if the request should be retried
        """
        if self.retry_config.max_retries <= 0:
            return False

        # Check if exception type is in retry list
        if exception:
            return any(
                isinstance(exception, exc_type)
                for exc_type in (self.retry_config.retry_exceptions or [])
            )

        # Check if status code is in retry list
        if response and response.status in (self.retry_config.retry_on or []):
            return True

        return False

    def _log_request(self, log_entry: RequestLog) -> None:
        """Add a request to the history and log it.

        Args:
            log_entry: The request log entry to add
        """
        self.request_history.append(log_entry)

        # Trim history if too large
        if len(self.request_history) > self._max_history_size:
            self.request_history.pop(0)

        if self.enable_request_logging:
            if log_entry.error:
                logger.error(
                    f"{log_entry.method} {log_entry.url} - ERROR: {log_entry.error} "
                    f"({log_entry.duration_ms:.0f}ms)"
                )
            else:
                logger.info(
                    f"{log_entry.method} {log_entry.url} - {log_entry.status} "
                    f"({log_entry.duration_ms:.0f}ms)"
                )

    def _truncate_body(self, body: Optional[str]) -> Optional[str]:
        """Truncate body for logging if too large.

        Args:
            body: The body string to truncate

        Returns:
            Truncated body or None
        """
        if not body:
            return None
        if len(body) > self.max_log_body_size:
            return (
                body[: self.max_log_body_size] + f"\n... [truncated, total size: {len(body)} bytes]"
            )
        return body

    def _serialize_body(self, data: Any) -> Optional[str]:
        """Serialize request body for logging.

        Args:
            data: The data to serialize (dict, list, or string)

        Returns:
            JSON string representation or None
        """
        if data is None:
            return None
        if isinstance(data, str):
            return data
        try:
            return json.dumps(data, indent=2)
        except (TypeError, ValueError):
            return str(data)

    def _make_request(self, method: str, endpoint: str, **kwargs) -> APIResponse:
        """Make an HTTP request with retry logic and logging.

        This is the core method that handles all requests with:
        - Rate limiting
        - Automatic retries
        - Request/response logging
        - Timing information

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, PATCH)
            endpoint: API endpoint (e.g., "/users/123")
            **kwargs: Additional arguments for the Playwright request
                - data: Form data or dict to send
                - json: JSON payload (alternative to data)
                - headers: Request-specific headers
                - params: Query parameters (GET only)

        Returns:
            APIResponse object

        Raises:
            BasePageError: If the request fails after all retries
        """
        self._ensure_setup()
        assert self.api_context is not None
        self._apply_rate_limit()

        full_url = f"{self.base_url}{endpoint}"
        last_response: Optional[APIResponse] = None

        # Prepare body - handle both 'data' and 'json' parameters
        request_body = kwargs.get("json") or kwargs.get("data")

        # Prepare request log
        request_log = RequestLog(
            method=method,
            url=full_url,
            headers=self._prepare_headers(kwargs.get("headers")),
            body=self._truncate_body(self._serialize_body(request_body)),
            timestamp=time.time(),
        )

        for attempt in range(self.retry_config.max_retries + 1):
            start_time = time.time()

            try:
                # Make the request
                if method == "GET":
                    last_response = self.api_context.get(
                        full_url,
                        headers=request_log.headers,
                        params=kwargs.get("params"),
                    )
                elif method == "POST":
                    last_response = self.api_context.post(
                        full_url, data=request_body, headers=request_log.headers
                    )
                elif method == "PUT":
                    last_response = self.api_context.put(
                        full_url, data=request_body, headers=request_log.headers
                    )
                elif method == "DELETE":
                    # DELETE with body support
                    if request_body:
                        # Use fetch with DELETE method for body support
                        last_response = self.api_context.fetch(
                            full_url,
                            method="DELETE",
                            data=request_body
                            if isinstance(request_body, str)
                            else json.dumps(request_body),
                            headers=request_log.headers,
                        )
                    else:
                        last_response = self.api_context.delete(
                            full_url, headers=request_log.headers
                        )
                elif method == "PATCH":
                    last_response = self.api_context.patch(
                        full_url, data=request_body, headers=request_log.headers
                    )
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                # Apply response interceptors
                for interceptor in self._response_interceptors:
                    try:
                        interceptor(last_response)
                    except Exception as e:
                        logger.warning(f"Response interceptor failed: {e}")

                # Update log with response info
                request_log.duration_ms = (time.time() - start_time) * 1000
                request_log.status = last_response.status
                request_log.response_headers = dict(last_response.headers)

                # Try to get response body for logging
                try:
                    body = last_response.body()
                    request_log.response_body = self._truncate_body(
                        body.decode("utf-8") if body else None
                    )
                except Exception:
                    pass

                # Check if we should retry
                if attempt < self.retry_config.max_retries and self._should_retry(
                    last_response, None
                ):
                    backoff = self._calculate_backoff(attempt)
                    logger.warning(
                        f"Retry {attempt + 1}/{self.retry_config.max_retries} "
                        f"for {method} {endpoint} "
                        f"(status: {last_response.status}, backoff: {backoff:.2f}s)"
                    )
                    time.sleep(backoff)
                    continue

                # Success or non-retryable response
                self._log_request(request_log)
                return last_response

            except Exception as e:
                request_log.duration_ms = (time.time() - start_time) * 1000

                # Check if we should retry on exception
                if attempt < self.retry_config.max_retries and self._should_retry(None, e):
                    backoff = self._calculate_backoff(attempt)
                    logger.warning(
                        f"Retry {attempt + 1}/{self.retry_config.max_retries} "
                        f"for {method} {endpoint} "
                        f"(error: {e}, backoff: {backoff:.2f}s)"
                    )
                    time.sleep(backoff)
                    continue

                # Log failure
                request_log.error = str(e)
                self._log_request(request_log)

                # Raise enhanced error
                raise BasePageError(
                    message=f"Request failed after {attempt + 1} attempt(s): {e}",
                    url=full_url,
                    method=method,
                    request_log=request_log,
                ) from e

        # Should not reach here, but just in case
        self._log_request(request_log)
        return last_response

    # Public HTTP methods

    def get(
        self,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> APIResponse:
        """Perform a GET request.

        Args:
            endpoint: API endpoint (e.g., "/users/123")
            headers: Optional request-specific headers
            params: Optional query parameters

        Returns:
            APIResponse object
        """
        return self._make_request("GET", endpoint, headers=headers, params=params)

    def post(
        self,
        endpoint: str,
        data: Optional[Union[Dict[str, Any], str]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> APIResponse:
        """Perform a POST request.

        Args:
            endpoint: API endpoint (e.g., "/users")
            data: Form data or dict (use either data or json, not both)
            json: JSON payload (use either data or json, not both)
            headers: Optional request-specific headers

        Returns:
            APIResponse object
        """
        body = json if json is not None else data
        return self._make_request("POST", endpoint, data=body, headers=headers)

    def put(
        self,
        endpoint: str,
        data: Optional[Union[Dict[str, Any], str]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> APIResponse:
        """Perform a PUT request.

        Args:
            endpoint: API endpoint (e.g., "/users/123")
            data: Form data or dict (use either data or json, not both)
            json: JSON payload (use either data or json, not both)
            headers: Optional request-specific headers

        Returns:
            APIResponse object
        """
        body = json if json is not None else data
        return self._make_request("PUT", endpoint, data=body, headers=headers)

    def delete(
        self,
        endpoint: str,
        data: Optional[Union[Dict[str, Any], str]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> APIResponse:
        """Perform a DELETE request.

        Args:
            endpoint: API endpoint (e.g., "/users/123")
            data: Request body as dict or string (for non-standard REST APIs)
            json: JSON payload (alternative to data)
            headers: Optional request-specific headers

        Returns:
            APIResponse object
        """
        body = json if json is not None else data
        return self._make_request("DELETE", endpoint, data=body, headers=headers)

    def patch(
        self,
        endpoint: str,
        data: Optional[Union[Dict[str, Any], str]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> APIResponse:
        """Perform a PATCH request.

        Args:
            endpoint: API endpoint (e.g., "/users/123")
            data: Form data or dict (use either data or json, not both)
            json: JSON payload (use either data or json, not both)
            headers: Optional request-specific headers

        Returns:
            APIResponse object
        """
        body = json if json is not None else data
        return self._make_request("PATCH", endpoint, data=body, headers=headers)

    # Assertion helpers

    def assert_status(
        self,
        response: APIResponse,
        expected_status: Union[int, List[int]],
        message: Optional[str] = None,
    ) -> APIResponse:
        """Assert that response status matches expected.

        Args:
            response: The API response to check
            expected_status: Expected status code or list of acceptable codes
            message: Optional custom error message

        Returns:
            The response (for chaining)

        Raises:
            BasePageError: If status doesn't match
        """
        if isinstance(expected_status, int):
            expected_status = [expected_status]

        if response.status not in expected_status:
            try:
                body_preview = response.text()[:500]
            except Exception:
                body_preview = "<unable to read body>"

            error_msg = message or f"Expected status {expected_status}, got {response.status}"
            raise BasePageError(
                message=error_msg,
                url=response.url,
                status=response.status,
                response_text=body_preview,
            )

        return response

    def assert_ok(self, response: APIResponse) -> APIResponse:
        """Assert that response status is 2xx (success).

        Args:
            response: The API response to check

        Returns:
            The response (for chaining)

        Raises:
            BasePageError: If status is not 2xx
        """
        if not (200 <= response.status < 300):
            try:
                body_preview = response.text()[:500]
            except Exception:
                body_preview = "<unable to read body>"

            raise BasePageError(
                message=f"Expected 2xx status, got {response.status}",
                url=response.url,
                status=response.status,
                response_text=body_preview,
            )

        return response

    def assert_json(self, response: APIResponse, key: Optional[str] = None) -> Any:
        """Parse response as JSON with optional key extraction.

        Args:
            response: The API response to parse
            key: Optional key to extract from JSON (e.g., "data.user.name")

        Returns:
            Parsed JSON data, or value at key if specified

        Raises:
            BasePageError: If JSON parsing fails or key not found
        """
        try:
            data = response.json()
        except Exception as e:
            raise BasePageError(
                message=f"Failed to parse JSON response: {e}",
                url=response.url,
                status=response.status,
            ) from e

        if key:
            keys = key.split(".")
            value = data
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    keys_display = list(value.keys()) if isinstance(value, dict) else "N/A"
                    raise BasePageError(
                        message=(
                            f"Key '{key}' not found in response. " f"Available keys: {keys_display}"
                        ),
                        url=response.url,
                        status=response.status,
                    )
            return value

        return data

    def assert_header(
        self,
        response: APIResponse,
        header_name: str,
        expected_value: Optional[str] = None,
    ) -> str:
        """Assert that response contains a specific header.

        Args:
            response: The API response to check
            header_name: Name of the header to check (case-insensitive)
            expected_value: Optional expected value (if None, just checks existence)

        Returns:
            The header value

        Raises:
            BasePageError: If header not found or value doesn't match
        """
        headers = {k.lower(): v for k, v in response.headers.items()}
        header_lower = header_name.lower()

        if header_lower not in headers:
            available = list(response.headers.keys())
            raise BasePageError(
                message=f"Header '{header_name}' not found. Available: {available}",
                url=response.url,
                status=response.status,
            )

        value = headers[header_lower]

        if expected_value and value != expected_value:
            raise BasePageError(
                message=(
                    f"Header '{header_name}' has value '{value}', " f"expected '{expected_value}'"
                ),
                url=response.url,
                status=response.status,
            )

        return str(value)

    def assert_schema(
        self,
        response: APIResponse,
        schema: Union[Dict[str, Any], type],
        message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Assert that response matches a JSON schema or Pydantic model.

        Args:
            response: The API response to validate
            schema: JSON schema dict or Pydantic model class
            message: Optional custom error message

        Returns:
            The parsed JSON data

        Raises:
            BasePageError: If validation fails
        """
        try:
            data = response.json()
        except Exception as e:
            raise BasePageError(
                message=f"Failed to parse JSON response: {e}",
                url=response.url,
                status=response.status,
            ) from e

        # Check if schema is a Pydantic model
        if isinstance(schema, type) and hasattr(schema, "model_validate"):
            try:
                schema.model_validate(data)
            except Exception as e:
                raise BasePageError(
                    message=message or f"Response does not match schema: {e}",
                    url=response.url,
                    status=response.status,
                    response_text=str(data)[:200],
                )
        else:
            # JSON schema validation (basic implementation)
            if isinstance(schema, dict) and "properties" in schema:
                required = schema.get("required", [])
                properties = schema.get("properties", {})

                for key in required:
                    if key not in data:
                        raise BasePageError(
                            message=message or f"Required field '{key}' missing from response",
                            url=response.url,
                            status=response.status,
                        )

                for key, prop_schema in properties.items():
                    if key in data:
                        expected_type = prop_schema.get("type")
                        if expected_type and not self._check_type(data[key], expected_type):
                            raise BasePageError(
                                message=message
                                or f"Field '{key}' has wrong type. Expected {expected_type}",
                                url=response.url,
                                status=response.status,
                            )

        return data

    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Check if a value matches an expected JSON schema type.

        Args:
            value: The value to check
            expected_type: Expected type (string, integer, number, boolean, array, object)

        Returns:
            True if types match
        """
        type_map = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict,
        }

        if expected_type in type_map:
            return isinstance(value, type_map[expected_type])
        return True

    # Utility methods

    def get_response_text(self, response: APIResponse) -> str:
        """Get response text from Playwright APIResponse.

        Args:
            response: The API response

        Returns:
            Response body as string
        """
        return response.text()

    def get_last_request(self) -> Optional[RequestLog]:
        """Get the most recent request log entry.

        Returns:
            The last RequestLog or None if no requests made
        """
        if self.request_history:
            return self.request_history[-1]
        return None

    def get_request_stats(self) -> Dict[str, Any]:
        """Get statistics about requests made.

        Returns:
            Dictionary with request statistics:
            - total_requests: Total number of requests
            - successful_requests: Number of 2xx responses
            - failed_requests: Number of non-2xx responses
            - total_duration_ms: Total time spent in requests
            - average_duration_ms: Average request duration
            - status_distribution: Count of each status code
        """
        if not self.request_history:
            return {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "total_duration_ms": 0.0,
                "average_duration_ms": 0.0,
                "status_distribution": {},
            }

        total_duration = sum(r.duration_ms for r in self.request_history)
        status_counts: Dict[int, int] = {}
        successful = 0
        failed = 0

        for req in self.request_history:
            if req.status:
                status_counts[req.status] = status_counts.get(req.status, 0) + 1
                if 200 <= req.status < 300:
                    successful += 1
                else:
                    failed += 1

        return {
            "total_requests": len(self.request_history),
            "successful_requests": successful,
            "failed_requests": failed,
            "total_duration_ms": total_duration,
            "average_duration_ms": total_duration / len(self.request_history),
            "status_distribution": status_counts,
        }

    def add_response_interceptor(self, interceptor: Callable[[APIResponse], None]) -> None:
        """Add a response interceptor.

        Interceptors are called after each successful response.
        They receive the APIResponse object and can be used for:
        - Logging
        - Token extraction
        - Response transformation
        - Metrics collection

        Args:
            interceptor: Callable that receives APIResponse
        """
        self._response_interceptors.append(interceptor)

    def clear_response_interceptors(self) -> None:
        """Remove all response interceptors."""
        self._response_interceptors.clear()

    def check_health(self, timeout: Optional[int] = None) -> ServiceHealth:
        """Check if the service is healthy.

        Makes a request to the health endpoint and returns status.

        Args:
            timeout: Request timeout in milliseconds (uses default if not specified)

        Returns:
            ServiceHealth object with health status
        """
        start_time = time.time()
        try:
            old_timeout = None
            if timeout and self.api_context:
                # Note: Playwright doesn't support per-request timeout easily
                # This is a simplified implementation
                pass

            response = self.get(self.health_endpoint)
            response_time = (time.time() - start_time) * 1000

            is_healthy = 200 <= response.status < 300

            try:
                body = response.json()
                message = body.get("status", "OK") if isinstance(body, dict) else "OK"
            except:
                message = "OK" if is_healthy else "Unhealthy"

            return ServiceHealth(
                healthy=is_healthy,
                status_code=response.status,
                response_time_ms=response_time,
                message=message,
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ServiceHealth(
                healthy=False,
                status_code=None,
                response_time_ms=response_time,
                message=str(e),
            )

    def wait_for_healthy(
        self, timeout: int = 30, interval: float = 1.0, raise_on_timeout: bool = True
    ) -> bool:
        """Wait for the service to become healthy.

        Polls the health endpoint until it returns healthy or timeout is reached.

        Args:
            timeout: Maximum time to wait in seconds
            interval: Polling interval in seconds
            raise_on_timeout: Whether to raise exception on timeout

        Returns:
            True if service became healthy, False if timed out

        Raises:
            BasePageError: If raise_on_timeout is True and service doesn't become healthy
        """
        start_time = time.time()
        attempts = 0

        while time.time() - start_time < timeout:
            attempts += 1
            health = self.check_health()

            if health.healthy:
                logger.info(f"Service became healthy after {attempts} attempt(s)")
                return True

            logger.debug(f"Health check failed (attempt {attempts}): {health.message}")
            time.sleep(interval)

        if raise_on_timeout:
            raise BasePageError(
                message=f"Service did not become healthy within {timeout}s",
                url=f"{self.base_url}{self.health_endpoint}",
            )

        return False

    @classmethod
    def wait_for_service(
        cls,
        url: str,
        health_endpoint: str = "/actuator/health",
        timeout: int = 30,
        interval: float = 1.0,
    ) -> bool:
        """Wait for a service to become healthy without creating a persistent instance.

        This is a class method that creates a temporary instance just for health checking.

        Args:
            url: Service base URL
            health_endpoint: Health check endpoint
            timeout: Maximum wait time in seconds
            interval: Polling interval

        Returns:
            True if service became healthy

        Example:
            >>> BasePage.wait_for_service("http://localhost:8081", timeout=60)
        """
        page = cls(base_url=url, health_endpoint=health_endpoint)
        try:
            page.setup()
            return page.wait_for_healthy(timeout=timeout, interval=interval)
        finally:
            page.teardown()
