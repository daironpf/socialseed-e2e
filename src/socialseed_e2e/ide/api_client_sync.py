"""API Client integration for importing/exporting test collections.

This module provides integration with popular API clients like
Postman, Insomnia, and HTTP clients.
"""

import json
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


class PostmanImporter:
    """Import Postman collections."""

    def __init__(self):
        """Initialize Postman importer."""
        self.collection: Dict[str, Any] = {}

    def load_collection(self, file_path: str) -> Dict[str, Any]:
        """Load Postman collection from file.

        Args:
            file_path: Path to Postman collection JSON

        Returns:
            Parsed collection
        """
        with open(file_path, "r") as f:
            self.collection = json.load(f)
        return self.collection

    def to_e2e_tests(self) -> List[Dict[str, Any]]:
        """Convert Postman collection to E2E tests.

        Returns:
            List of test definitions
        """
        tests = []

        items = self.collection.get("item", [])

        for item in items:
            if isinstance(item, dict):
                test = self._convert_item(item)
                if test:
                    tests.append(test)

        return tests

    def _convert_item(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Convert a single Postman item to E2E test.

        Args:
            item: Postman item

        Returns:
            E2E test definition
        """
        request = item.get("request", {})
        if not request:
            return None

        method = request.get("method", "GET")
        url = request.get("url", {})

        if isinstance(url, dict):
            path = url.get("raw", "/")
        else:
            path = url

        name = item.get("name", "unnamed_test")

        return {
            "name": f"test_{name.replace(' ', '_').lower()}",
            "description": f"Generated from Postman: {name}",
            "method": method,
            "path": path,
            "headers": self._extract_headers(request.get("header", [])),
            "body": request.get("body"),
            "params": self._extract_params(url),
        }

    def _extract_headers(self, headers: List[Dict[str, str]]) -> Dict[str, str]:
        """Extract headers from Postman format."""
        result = {}
        for header in headers:
            if isinstance(header, dict):
                key = header.get("key", "")
                value = header.get("value", "")
                if key:
                    result[key] = value
        return result

    def _extract_params(self, url: Any) -> Dict[str, str]:
        """Extract query parameters from Postman URL."""
        if isinstance(url, dict):
            params = url.get("query", [])
            result = {}
            for param in params:
                if isinstance(param, dict):
                    key = param.get("key", "")
                    value = param.get("value", "")
                    if key:
                        result[key] = value
            return result
        return {}


class PostmanExporter:
    """Export tests to Postman collection."""

    def __init__(self):
        """Initialize Postman exporter."""
        self.collection: Dict[str, Any] = {
            "info": {
                "name": "SocialSeed E2E Tests",
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            },
            "item": [],
        }

    def add_test(
        self,
        name: str,
        method: str,
        path: str,
        headers: Optional[Dict] = None,
        body: Optional[Dict] = None,
    ):
        """Add a test to the collection.

        Args:
            name: Test name
            method: HTTP method
            path: API path
            headers: Request headers
            body: Request body
        """
        item = {
            "name": name,
            "request": {
                "method": method,
                "url": {
                    "raw": path,
                    "path": path.strip("/").split("/") if path else [],
                },
            },
        }

        if headers:
            item["request"]["header"] = [
                {"key": k, "value": v} for k, v in headers.items()
            ]

        if body:
            item["request"]["body"] = {
                "mode": "raw",
                "raw": json.dumps(body, indent=2),
            }

        self.collection["item"].append(item)

    def export(self, file_path: str):
        """Export collection to file.

        Args:
            file_path: Output file path
        """
        with open(file_path, "w") as f:
            json.dump(self.collection, f, indent=2)


class OpenAPIImporter:
    """Import OpenAPI specifications."""

    def __init__(self):
        """Initialize OpenAPI importer."""
        self.spec: Dict[str, Any] = {}

    def load_spec(self, file_path: str) -> Dict[str, Any]:
        """Load OpenAPI spec from file.

        Args:
            file_path: Path to OpenAPI spec (JSON or YAML)

        Returns:
            Parsed spec
        """
        path = Path(file_path)

        if path.suffix in [".yaml", ".yml"]:
            with open(file_path, "r") as f:
                self.spec = yaml.safe_load(f)
        else:
            with open(file_path, "r") as f:
                self.spec = json.load(f)

        return self.spec

    def to_e2e_tests(self) -> List[Dict[str, Any]]:
        """Convert OpenAPI spec to E2E tests.

        Returns:
            List of test definitions
        """
        tests = []

        paths = self.spec.get("paths", {})

        for path, methods in paths.items():
            for method, details in methods.items():
                if method.upper() in [
                    "GET",
                    "POST",
                    "PUT",
                    "DELETE",
                    "PATCH",
                    "OPTIONS",
                    "HEAD",
                ]:
                    test = self._convert_endpoint(path, method, details)
                    tests.append(test)

        return tests

    def _convert_endpoint(
        self, path: str, method: str, details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert OpenAPI endpoint to E2E test.

        Args:
            path: API path
            method: HTTP method
            details: Endpoint details

        Returns:
            E2E test definition
        """
        operation_id = details.get(
            "operationId", f"{method}_{path.replace('/', '_').strip('_')}"
        )

        return {
            "name": f"test_{operation_id}",
            "description": details.get("summary", details.get("description", "")),
            "method": method.upper(),
            "path": path,
            "parameters": details.get("parameters", []),
            "request_body": details.get("requestBody"),
            "responses": details.get("responses", {}),
            "tags": details.get("tags", []),
            "security": details.get("security", []),
        }

    def get_endpoints_summary(self) -> Dict[str, Any]:
        """Get summary of all endpoints.

        Returns:
            Summary dictionary
        """
        paths = self.spec.get("paths", {})

        summary = {
            "total_endpoints": 0,
            "by_method": {},
            "by_tag": {},
        }

        for path, methods in paths.items():
            for method in methods.keys():
                if method.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                    summary["total_endpoints"] += 1

                    summary["by_method"][method.upper()] = (
                        summary["by_method"].get(method.upper(), 0) + 1
                    )

                    tags = methods.get("tags", ["untagged"])
                    for tag in tags:
                        summary["by_tag"][tag] = summary["by_tag"].get(tag, 0) + 1

        return summary


class APIClientSync:
    """Synchronize tests with API clients."""

    def __init__(self):
        """Initialize API client sync."""
        self.postman = PostmanImporter()
        self.openapi = OpenAPIImporter()

    def import_from_postman(self, file_path: str) -> List[Dict[str, Any]]:
        """Import tests from Postman collection.

        Args:
            file_path: Path to Postman collection

        Returns:
            List of test definitions
        """
        self.postman.load_collection(file_path)
        return self.postman.to_e2e_tests()

    def import_from_openapi(self, file_path: str) -> List[Dict[str, Any]]:
        """Import tests from OpenAPI spec.

        Args:
            file_path: Path to OpenAPI spec

        Returns:
            List of test definitions
        """
        self.openapi.load_spec(file_path)
        return self.openapi.to_e2e_tests()

    def export_to_postman(self, tests: List[Dict[str, Any]], file_path: str):
        """Export tests to Postman collection.

        Args:
            tests: List of test definitions
            file_path: Output file path
        """
        exporter = PostmanExporter()

        for test in tests:
            exporter.add_test(
                name=test.get("name", "unnamed"),
                method=test.get("method", "GET"),
                path=test.get("path", "/"),
                headers=test.get("headers"),
                body=test.get("body"),
            )

        exporter.export(file_path)

    def sync_collection(
        self, source_path: str, target_path: str, source_type: str = "postman"
    ):
        """Sync tests between formats.

        Args:
            source_path: Source file path
            target_path: Target file path
            source_type: Source type (postman, openapi)
        """
        if source_type == "postman":
            tests = self.import_from_postman(source_path)
        else:
            tests = self.import_from_openapi(source_path)

        self.export_to_postman(tests, target_path)
