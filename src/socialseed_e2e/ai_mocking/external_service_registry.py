"""External Service Registry with predefined schemas for common APIs.

This module provides pre-configured schemas, endpoints, and mock behaviors
for popular third-party services like Stripe, Google Maps, AWS, etc.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class MockEndpoint:
    """Definition of a mock endpoint."""

    path: str
    method: str
    response_schema: Dict[str, Any]
    status_code: int = 200
    response_example: Optional[Dict[str, Any]] = None
    request_schema: Optional[Dict[str, Any]] = None
    headers: Dict[str, str] = field(default_factory=dict)
    delay_ms: int = 0
    conditional_response: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None


@dataclass
class ExternalServiceDefinition:
    """Complete definition of an external service for mocking."""

    name: str
    base_url: str
    description: str
    endpoints: List[MockEndpoint] = field(default_factory=list)
    auth_type: str = "bearer"  # bearer, api_key, oauth2, none
    headers: Dict[str, str] = field(default_factory=dict)
    error_responses: Dict[int, Dict[str, Any]] = field(default_factory=dict)
    webhook_support: bool = False


class ExternalServiceRegistry:
    """Registry of predefined external service definitions."""

    def __init__(self):
        """Initialize registry with default service definitions."""
        self._services: Dict[str, ExternalServiceDefinition] = {}
        self._register_default_services()

    def _register_default_services(self) -> None:
        """Register all predefined services."""
        self._register_stripe()
        self._register_google_maps()
        self._register_aws_s3()
        self._register_sendgrid()
        self._register_twilio()
        self._register_github()
        self._register_slack()
        self._register_openai()
        self._register_paypal()

    def _register_stripe(self) -> None:
        """Register Stripe API definition."""
        endpoints = [
            MockEndpoint(
                path="/v1/customers",
                method="POST",
                request_schema={
                    "type": "object",
                    "properties": {
                        "email": {"type": "string", "format": "email"},
                        "name": {"type": "string"},
                        "description": {"type": "string"},
                    },
                    "required": ["email"],
                },
                response_schema={
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "object": {"type": "string", "enum": ["customer"]},
                        "email": {"type": "string"},
                        "name": {"type": "string"},
                        "created": {"type": "integer"},
                    },
                },
                response_example={
                    "id": "cus_1234567890",
                    "object": "customer",
                    "email": "test@example.com",
                    "name": "Test Customer",
                    "created": 1640995200,
                },
            ),
            MockEndpoint(
                path="/v1/customers/{id}",
                method="GET",
                response_schema={
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "object": {"type": "string"},
                        "email": {"type": "string"},
                    },
                },
                response_example={
                    "id": "cus_1234567890",
                    "object": "customer",
                    "email": "test@example.com",
                },
            ),
            MockEndpoint(
                path="/v1/charges",
                method="POST",
                request_schema={
                    "type": "object",
                    "properties": {
                        "amount": {"type": "integer"},
                        "currency": {"type": "string"},
                        "customer": {"type": "string"},
                        "source": {"type": "string"},
                    },
                    "required": ["amount", "currency"],
                },
                response_schema={
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "object": {"type": "string"},
                        "amount": {"type": "integer"},
                        "currency": {"type": "string"},
                        "status": {"type": "string"},
                    },
                },
                response_example={
                    "id": "ch_1234567890",
                    "object": "charge",
                    "amount": 2000,
                    "currency": "usd",
                    "status": "succeeded",
                },
            ),
            MockEndpoint(
                path="/v1/payment_intents",
                method="POST",
                request_schema={
                    "type": "object",
                    "properties": {
                        "amount": {"type": "integer"},
                        "currency": {"type": "string"},
                        "automatic_payment_methods": {"type": "object"},
                    },
                    "required": ["amount", "currency"],
                },
                response_schema={
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "object": {"type": "string"},
                        "amount": {"type": "integer"},
                        "client_secret": {"type": "string"},
                        "status": {"type": "string"},
                    },
                },
                response_example={
                    "id": "pi_1234567890",
                    "object": "payment_intent",
                    "amount": 2000,
                    "client_secret": "pi_1234567890_secret_xyz",
                    "status": "requires_confirmation",
                },
            ),
        ]

        self._services["stripe"] = ExternalServiceDefinition(
            name="stripe",
            base_url="https://api.stripe.com",
            description="Stripe payment processing API",
            endpoints=endpoints,
            auth_type="bearer",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
            error_responses={
                400: {
                    "error": {
                        "type": "invalid_request_error",
                        "message": "Invalid request",
                    }
                },
                401: {
                    "error": {
                        "type": "authentication_error",
                        "message": "Invalid API key",
                    }
                },
                404: {
                    "error": {
                        "type": "invalid_request_error",
                        "message": "Resource not found",
                    }
                },
            },
            webhook_support=True,
        )

    def _register_google_maps(self) -> None:
        """Register Google Maps API definition."""
        endpoints = [
            MockEndpoint(
                path="/maps/api/geocode/json",
                method="GET",
                response_schema={
                    "type": "object",
                    "properties": {
                        "results": {"type": "array"},
                        "status": {"type": "string"},
                    },
                },
                response_example={
                    "results": [
                        {
                            "formatted_address": "1600 Amphitheatre Parkway, Mountain View, CA",
                            "geometry": {
                                "location": {
                                    "lat": 37.4224764,
                                    "lng": -122.0842499,
                                },
                            },
                            "place_id": "ChIJ2eUgeAK6j4ARbn5u_wAGqWA",
                        },
                    ],
                    "status": "OK",
                },
            ),
            MockEndpoint(
                path="/maps/api/directions/json",
                method="GET",
                response_schema={
                    "type": "object",
                    "properties": {
                        "routes": {"type": "array"},
                        "status": {"type": "string"},
                    },
                },
                response_example={
                    "routes": [
                        {
                            "summary": "US-101 N",
                            "legs": [
                                {
                                    "distance": {"text": "14.5 km", "value": 14500},
                                    "duration": {"text": "20 mins", "value": 1200},
                                },
                            ],
                        },
                    ],
                    "status": "OK",
                },
            ),
            MockEndpoint(
                path="/maps/api/place/nearbysearch/json",
                method="GET",
                response_schema={
                    "type": "object",
                    "properties": {
                        "results": {"type": "array"},
                        "status": {"type": "string"},
                    },
                },
                response_example={
                    "results": [
                        {
                            "name": "Example Place",
                            "vicinity": "123 Main St",
                            "rating": 4.5,
                            "place_id": "ChIJ1234567890",
                        },
                    ],
                    "status": "OK",
                },
            ),
        ]

        self._services["google_maps"] = ExternalServiceDefinition(
            name="google_maps",
            base_url="https://maps.googleapis.com",
            description="Google Maps Platform APIs",
            endpoints=endpoints,
            auth_type="api_key",
            error_responses={
                400: {"error_message": "Invalid request", "status": "INVALID_REQUEST"},
                403: {"error_message": "API key expired", "status": "REQUEST_DENIED"},
                404: {"error_message": "Not found", "status": "NOT_FOUND"},
            },
        )

    def _register_aws_s3(self) -> None:
        """Register AWS S3 API definition."""
        endpoints = [
            MockEndpoint(
                path="/{bucket}",
                method="PUT",
                status_code=200,
                response_schema={"type": "object"},
                response_example={},
                headers={"Location": "/{bucket}"},
            ),
            MockEndpoint(
                path="/{bucket}/{key}",
                method="PUT",
                status_code=200,
                response_schema={
                    "type": "object",
                    "properties": {
                        "ETag": {"type": "string"},
                    },
                },
                response_example={"ETag": '"abc123"'},
            ),
            MockEndpoint(
                path="/{bucket}/{key}",
                method="GET",
                response_schema={"type": "object"},
                response_example={
                    "Body": "file content",
                    "ContentType": "application/octet-stream",
                },
            ),
            MockEndpoint(
                path="/{bucket}",
                method="GET",
                response_schema={
                    "type": "object",
                    "properties": {
                        "Contents": {"type": "array"},
                    },
                },
                response_example={
                    "Contents": [
                        {
                            "Key": "file1.txt",
                            "Size": 1024,
                            "LastModified": "2024-01-01T00:00:00Z",
                        },
                    ],
                },
            ),
        ]

        self._services["aws_s3"] = ExternalServiceDefinition(
            name="aws_s3",
            base_url="https://{bucket}.s3.{region}.amazonaws.com",
            description="AWS S3 object storage API",
            endpoints=endpoints,
            auth_type="aws_signature",
            headers={
                "Content-Type": "application/xml",
            },
            error_responses={
                403: {"Error": {"Code": "AccessDenied", "Message": "Access Denied"}},
                404: {
                    "Error": {
                        "Code": "NoSuchKey",
                        "Message": "The specified key does not exist",
                    }
                },
            },
        )

    def _register_sendgrid(self) -> None:
        """Register SendGrid API definition."""
        endpoints = [
            MockEndpoint(
                path="/v3/mail/send",
                method="POST",
                request_schema={
                    "type": "object",
                    "properties": {
                        "personalizations": {"type": "array"},
                        "from": {"type": "object"},
                        "subject": {"type": "string"},
                        "content": {"type": "array"},
                    },
                    "required": ["personalizations", "from", "subject"],
                },
                response_schema={"type": "object"},
                status_code=202,
                response_example={},
            ),
            MockEndpoint(
                path="/v3/mail/batch",
                method="POST",
                response_schema={"type": "object"},
                response_example={"batch_id": "abc123"},
            ),
        ]

        self._services["sendgrid"] = ExternalServiceDefinition(
            name="sendgrid",
            base_url="https://api.sendgrid.com",
            description="SendGrid email delivery API",
            endpoints=endpoints,
            auth_type="bearer",
            error_responses={
                400: {"errors": [{"message": "Bad request", "field": "subject"}]},
                401: {"errors": [{"message": "Invalid API key"}]},
            },
        )

    def _register_twilio(self) -> None:
        """Register Twilio API definition."""
        endpoints = [
            MockEndpoint(
                path="/2010-04-01/Accounts/{account_sid}/Messages.json",
                method="POST",
                request_schema={
                    "type": "object",
                    "properties": {
                        "To": {"type": "string"},
                        "From": {"type": "string"},
                        "Body": {"type": "string"},
                    },
                    "required": ["To", "From"],
                },
                response_schema={
                    "type": "object",
                    "properties": {
                        "sid": {"type": "string"},
                        "status": {"type": "string"},
                    },
                },
                response_example={
                    "sid": "SM1234567890",
                    "status": "queued",
                    "to": "+1234567890",
                    "from": "+0987654321",
                },
            ),
        ]

        self._services["twilio"] = ExternalServiceDefinition(
            name="twilio",
            base_url="https://api.twilio.com",
            description="Twilio SMS and communication API",
            endpoints=endpoints,
            auth_type="basic",
            error_responses={
                400: {
                    "code": 21211,
                    "message": "Invalid 'To' phone number",
                    "status": 400,
                },
                401: {"code": 20003, "message": "Authentication failed", "status": 401},
            },
        )

    def _register_github(self) -> None:
        """Register GitHub API definition."""
        endpoints = [
            MockEndpoint(
                path="/repos/{owner}/{repo}",
                method="GET",
                response_schema={
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "string"},
                        "full_name": {"type": "string"},
                    },
                },
                response_example={
                    "id": 12345,
                    "name": "example-repo",
                    "full_name": "owner/example-repo",
                    "private": False,
                },
            ),
            MockEndpoint(
                path="/repos/{owner}/{repo}/issues",
                method="POST",
                request_schema={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "body": {"type": "string"},
                    },
                    "required": ["title"],
                },
                response_schema={
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "number": {"type": "integer"},
                        "title": {"type": "string"},
                    },
                },
                response_example={
                    "id": 123456,
                    "number": 42,
                    "title": "Test issue",
                    "state": "open",
                },
            ),
        ]

        self._services["github"] = ExternalServiceDefinition(
            name="github",
            base_url="https://api.github.com",
            description="GitHub REST API",
            endpoints=endpoints,
            auth_type="bearer",
            headers={
                "Accept": "application/vnd.github.v3+json",
            },
            error_responses={
                401: {
                    "message": "Bad credentials",
                    "documentation_url": "https://docs.github.com",
                },
                404: {
                    "message": "Not Found",
                    "documentation_url": "https://docs.github.com",
                },
                403: {"message": "API rate limit exceeded"},
            },
            webhook_support=True,
        )

    def _register_slack(self) -> None:
        """Register Slack API definition."""
        endpoints = [
            MockEndpoint(
                path="/api/chat.postMessage",
                method="POST",
                request_schema={
                    "type": "object",
                    "properties": {
                        "channel": {"type": "string"},
                        "text": {"type": "string"},
                    },
                    "required": ["channel"],
                },
                response_schema={
                    "type": "object",
                    "properties": {
                        "ok": {"type": "boolean"},
                        "channel": {"type": "string"},
                        "ts": {"type": "string"},
                    },
                },
                response_example={
                    "ok": True,
                    "channel": "C1234567890",
                    "ts": "1234567890.123456",
                    "message": {"text": "Hello", "user": "U123456"},
                },
            ),
            MockEndpoint(
                path="/api/users.info",
                method="GET",
                response_schema={
                    "type": "object",
                    "properties": {
                        "ok": {"type": "boolean"},
                        "user": {"type": "object"},
                    },
                },
                response_example={
                    "ok": True,
                    "user": {
                        "id": "U123456",
                        "name": "john_doe",
                        "real_name": "John Doe",
                    },
                },
            ),
        ]

        self._services["slack"] = ExternalServiceDefinition(
            name="slack",
            base_url="https://slack.com/api",
            description="Slack Web API",
            endpoints=endpoints,
            auth_type="bearer",
            headers={
                "Content-Type": "application/json",
            },
            error_responses={
                200: {"ok": False, "error": "channel_not_found"},
                401: {"ok": False, "error": "invalid_auth"},
            },
            webhook_support=True,
        )

    def _register_openai(self) -> None:
        """Register OpenAI API definition."""
        endpoints = [
            MockEndpoint(
                path="/v1/chat/completions",
                method="POST",
                request_schema={
                    "type": "object",
                    "properties": {
                        "model": {"type": "string"},
                        "messages": {"type": "array"},
                        "temperature": {"type": "number"},
                    },
                    "required": ["model", "messages"],
                },
                response_schema={
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "object": {"type": "string"},
                        "choices": {"type": "array"},
                    },
                },
                response_example={
                    "id": "chatcmpl-123",
                    "object": "chat.completion",
                    "created": 1677652288,
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": "Hello! How can I help you today?",
                            },
                            "finish_reason": "stop",
                        },
                    ],
                },
                delay_ms=500,  # Simulate API delay
            ),
            MockEndpoint(
                path="/v1/completions",
                method="POST",
                response_schema={
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "choices": {"type": "array"},
                    },
                },
                response_example={
                    "id": "cmpl-123",
                    "choices": [{"text": "This is a completion", "index": 0}],
                },
            ),
            MockEndpoint(
                path="/v1/embeddings",
                method="POST",
                request_schema={
                    "type": "object",
                    "properties": {
                        "model": {"type": "string"},
                        "input": {"type": "string"},
                    },
                    "required": ["model", "input"],
                },
                response_schema={
                    "type": "object",
                    "properties": {
                        "object": {"type": "string"},
                        "data": {"type": "array"},
                    },
                },
                response_example={
                    "object": "list",
                    "data": [
                        {
                            "object": "embedding",
                            "embedding": [0.1, 0.2, 0.3],
                            "index": 0,
                        },
                    ],
                },
            ),
        ]

        self._services["openai"] = ExternalServiceDefinition(
            name="openai",
            base_url="https://api.openai.com",
            description="OpenAI API for GPT models",
            endpoints=endpoints,
            auth_type="bearer",
            headers={
                "Content-Type": "application/json",
            },
            error_responses={
                400: {
                    "error": {
                        "message": "Invalid request",
                        "type": "invalid_request_error",
                    }
                },
                401: {
                    "error": {
                        "message": "Invalid API key",
                        "type": "authentication_error",
                    }
                },
                429: {
                    "error": {
                        "message": "Rate limit exceeded",
                        "type": "rate_limit_error",
                    }
                },
            },
        )

    def _register_paypal(self) -> None:
        """Register PayPal API definition."""
        endpoints = [
            MockEndpoint(
                path="/v2/checkout/orders",
                method="POST",
                request_schema={
                    "type": "object",
                    "properties": {
                        "intent": {"type": "string"},
                        "purchase_units": {"type": "array"},
                    },
                    "required": ["intent", "purchase_units"],
                },
                response_schema={
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "status": {"type": "string"},
                    },
                },
                response_example={
                    "id": "5O190127TN364715T",
                    "status": "CREATED",
                    "links": [{"href": "https://api.paypal.com/...", "rel": "approve"}],
                },
            ),
            MockEndpoint(
                path="/v2/checkout/orders/{order_id}/capture",
                method="POST",
                response_schema={
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "status": {"type": "string"},
                    },
                },
                response_example={
                    "id": "5O190127TN364715T",
                    "status": "COMPLETED",
                },
            ),
            MockEndpoint(
                path="/v1/oauth2/token",
                method="POST",
                response_schema={
                    "type": "object",
                    "properties": {
                        "access_token": {"type": "string"},
                        "token_type": {"type": "string"},
                    },
                },
                response_example={
                    "scope": "https://uri.paypal.com/...",
                    "access_token": "A21AA...",
                    "token_type": "Bearer",
                    "expires_in": 3600,
                },
            ),
        ]

        self._services["paypal"] = ExternalServiceDefinition(
            name="paypal",
            base_url="https://api.paypal.com",
            description="PayPal REST API",
            endpoints=endpoints,
            auth_type="oauth2",
            headers={
                "Content-Type": "application/json",
            },
            error_responses={
                400: {
                    "name": "INVALID_REQUEST",
                    "message": "Request is not well-formed",
                },
                401: {
                    "error": "invalid_client",
                    "error_description": "Client authentication failed",
                },
            },
        )

    def get_service(self, name: str) -> Optional[ExternalServiceDefinition]:
        """Get a service definition by name.

        Args:
            name: Service name (e.g., 'stripe', 'google_maps')

        Returns:
            Service definition or None if not found
        """
        return self._services.get(name.lower())

    def list_services(self) -> List[str]:
        """List all registered service names.

        Returns:
            List of service names
        """
        return list(self._services.keys())

    def has_service(self, name: str) -> bool:
        """Check if a service is registered.

        Args:
            name: Service name to check

        Returns:
            True if service is registered
        """
        return name.lower() in self._services

    def register_service(self, definition: ExternalServiceDefinition) -> None:
        """Register a custom service definition.

        Args:
            definition: Service definition to register
        """
        self._services[definition.name.lower()] = definition

    def get_mock_endpoint(
        self, service_name: str, path: str, method: str = "GET"
    ) -> Optional[MockEndpoint]:
        """Get a specific mock endpoint for a service.

        Args:
            service_name: Name of the service
            path: Endpoint path
            method: HTTP method

        Returns:
            MockEndpoint if found, None otherwise
        """
        service = self.get_service(service_name)
        if not service:
            return None

        for endpoint in service.endpoints:
            # Simple path matching (could be improved with pattern matching)
            if endpoint.path == path and endpoint.method.upper() == method.upper():
                return endpoint

        return None
