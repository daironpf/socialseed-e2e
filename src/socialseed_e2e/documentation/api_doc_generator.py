"""API documentation generator from test cases.

This module generates comprehensive API documentation by analyzing
test cases and extracting endpoint information.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import re

from .models import APIDocumentation, EndpointDoc, ErrorCodeDoc, TestCaseDoc


class APIDocGenerator:
    """Generate API documentation from test cases."""

    def __init__(self, base_url: str = "http://localhost:8080"):
        """Initialize the API documentation generator.

        Args:
            base_url: Base URL for the API
        """
        self.base_url = base_url
        self.endpoints: List[EndpointDoc] = []
        self.error_codes: List[ErrorCodeDoc] = []
        self.schemas: Dict[str, Dict[str, Any]] = {}

    def generate_from_tests(self, test_cases: List[TestCaseDoc]) -> APIDocumentation:
        """Generate API documentation from test cases.

        Args:
            test_cases: List of test case documents

        Returns:
            APIDocumentation object
        """
        endpoint_map: Dict[str, EndpointDoc] = {}

        for test_case in test_cases:
            for step in test_case.steps:
                endpoint_info = self._extract_endpoint_from_step(step, test_case)
                if endpoint_info:
                    key = f"{endpoint_info['method']}:{endpoint_info['path']}"

                    if key not in endpoint_map:
                        endpoint_map[key] = EndpointDoc(
                            path=endpoint_info["path"],
                            method=endpoint_info["method"],
                            summary=endpoint_info.get(
                                "summary",
                                f"{endpoint_info['method']} {endpoint_info['path']}",
                            ),
                            description=endpoint_info.get(
                                "description", test_case.description
                            ),
                        )

                    endpoint_map[key].test_count += 1

                    if endpoint_info.get("parameters"):
                        endpoint_map[key].parameters.extend(endpoint_info["parameters"])

                    if endpoint_info.get("request_body"):
                        endpoint_map[key].request_body = endpoint_info["request_body"]

                    if endpoint_info.get("responses"):
                        for status, response in endpoint_info["responses"].items():
                            if status not in endpoint_map[key].responses:
                                endpoint_map[key].responses[status] = response

                    if test_case.tags:
                        endpoint_map[key].tags = list(
                            set(endpoint_map[key].tags + test_case.tags)
                        )

        self.endpoints = list(endpoint_map.values())

        self._extract_error_codes(test_cases)

        return APIDocumentation(
            title="API Documentation",
            version="1.0.0",
            base_url=self.base_url,
            endpoints=self.endpoints,
            error_codes=self.error_codes,
            schemas=self.schemas,
        )

    def _extract_endpoint_from_step(
        self, step, test_case: TestCaseDoc
    ) -> Optional[Dict[str, Any]]:
        """Extract endpoint information from a test step."""
        action = step.action.lower()

        http_methods = {
            "get": "GET",
            "post": "POST",
            "put": "PUT",
            "patch": "PATCH",
            "delete": "DELETE",
            "head": "HEAD",
            "options": "OPTIONS",
        }

        method = None
        for http_verb, http_method in http_methods.items():
            if http_verb in action:
                method = http_method
                break

        if not method:
            return None

        path = self._extract_path_from_action(action, test_case)

        return {
            "method": method,
            "path": path,
            "summary": f"{method} {path}",
            "description": step.description,
            "parameters": self._extract_parameters(step),
            "request_body": self._extract_request_body(step),
            "responses": self._extract_responses(step),
        }

    def _extract_path_from_action(self, action: str, test_case: TestCaseDoc) -> str:
        """Extract or infer the API path."""
        if test_case.service and test_case.service != "unknown":
            base_path = f"/api/{test_case.service}"
        else:
            base_path = "/api"

        action_clean = (
            action.replace("self.", "")
            .replace(".get(", "/")
            .replace(".post(", "/")
            .replace(".put(", "/")
            .replace(".delete(", "/")
            .replace(".patch(", "/")
        )
        action_clean = re.sub(r"[^a-zA-Z0-9/{}]", "", action_clean)

        if action_clean.startswith("/"):
            return action_clean

        return f"{base_path}/{action_clean}" if action_clean else base_path

    def _extract_parameters(self, step) -> List[Dict[str, Any]]:
        """Extract parameters from a test step."""
        params = []

        if step.request:
            for key, value in step.request.items():
                param_type = self._infer_type(value)
                params.append(
                    {
                        "name": key,
                        "in": "query"
                        if isinstance(value, (str, int, bool))
                        else "body",
                        "type": param_type,
                        "required": True,
                        "example": value,
                    }
                )

        return params

    def _extract_request_body(self, step) -> Optional[Dict[str, Any]]:
        """Extract request body from a test step."""
        if step.request and isinstance(step.request, dict):
            return {
                "type": "object",
                "properties": {
                    key: {"type": self._infer_type(value), "example": value}
                    for key, value in step.request.items()
                },
            }
        return None

    def _extract_responses(self, step) -> Dict[str, Dict[str, Any]]:
        """Extract response information from a test step."""
        responses = {}

        if step.response:
            responses["200"] = {
                "description": "Successful response",
                "example": step.response,
            }

        expected = step.expected_result.lower()
        if "error" in expected or "fail" in expected:
            responses["400"] = {"description": "Bad request"}
            responses["500"] = {"description": "Internal server error"}

        return responses

    def _infer_type(self, value: Any) -> str:
        """Infer JSON type from Python value."""
        if isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "integer"
        elif isinstance(value, float):
            return "number"
        elif isinstance(value, str):
            return "string"
        elif isinstance(value, list):
            return "array"
        elif isinstance(value, dict):
            return "object"
        else:
            return "string"

    def _extract_error_codes(self, test_cases: List[TestCaseDoc]):
        """Extract error codes from test cases."""
        error_patterns = [
            (
                r"40[0-9]",
                "Client Error",
                "The request contains invalid syntax or cannot be fulfilled.",
            ),
            (
                r"50[0-9]",
                "Server Error",
                "The server failed to fulfill a valid request.",
            ),
            (
                r"401",
                "Unauthorized",
                "Authentication is required and has failed or has not been provided.",
            ),
            (
                r"403",
                "Forbidden",
                "The server understood the request but refuses to authorize it.",
            ),
            (r"404", "Not Found", "The requested resource could not be found."),
            (
                r"422",
                "Unprocessable Entity",
                "The request was well-formed but could not be followed.",
            ),
            (
                r"429",
                "Too Many Requests",
                "Too many requests in a given amount of time.",
            ),
        ]

        found_codes = set()

        for test_case in test_cases:
            for step in test_case.steps:
                for pattern, code, desc in error_patterns:
                    if re.search(pattern, step.expected_result) or re.search(
                        pattern, step.description
                    ):
                        if code not in found_codes:
                            self.error_codes.append(
                                ErrorCodeDoc(
                                    code=code,
                                    message=self._get_error_message(code),
                                    description=desc,
                                    possible_causes=[
                                        "Invalid input data",
                                        "Missing required fields",
                                        "Service unavailable",
                                    ],
                                )
                            )
                            found_codes.add(code)

    def _get_error_message(self, code: str) -> str:
        """Get a human-readable error message for a code."""
        messages = {
            "400": "Bad Request",
            "401": "Unauthorized",
            "403": "Forbidden",
            "404": "Not Found",
            "422": "Unprocessable Entity",
            "429": "Too Many Requests",
            "500": "Internal Server Error",
            "502": "Bad Gateway",
            "503": "Service Unavailable",
        }
        return messages.get(code, "Unknown Error")

    def add_endpoint(self, endpoint: EndpointDoc):
        """Manually add an endpoint to the documentation."""
        self.endpoints.append(endpoint)

    def add_error_code(self, error_code: ErrorCodeDoc):
        """Manually add an error code to the documentation."""
        self.error_codes.append(error_code)

    def add_schema(self, name: str, schema: Dict[str, Any]):
        """Add a schema to the documentation."""
        self.schemas[name] = schema

    def get_endpoint(self, path: str, method: str) -> Optional[EndpointDoc]:
        """Get a specific endpoint."""
        for endpoint in self.endpoints:
            if endpoint.path == path and endpoint.method.upper() == method.upper():
                return endpoint
        return None

    def get_endpoints_by_tag(self, tag: str) -> List[EndpointDoc]:
        """Get all endpoints with a specific tag."""
        return [ep for ep in self.endpoints if tag in ep.tags]

    def get_endpoints_by_method(self, method: str) -> List[EndpointDoc]:
        """Get all endpoints for a specific HTTP method."""
        return [ep for ep in self.endpoints if ep.method.upper() == method.upper()]
