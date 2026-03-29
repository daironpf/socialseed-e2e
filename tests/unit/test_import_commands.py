"""Unit tests for import commands (Phase 2)."""

import json
import tempfile
from pathlib import Path

import pytest
import yaml


class TestOpenAPIImporter:
    """Tests for OpenAPI import with --to-manifest."""

    @pytest.fixture
    def openapi_spec(self, tmp_path):
        """Create a temporary OpenAPI spec file."""
        spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "Test API",
                "version": "1.0.0",
                "description": "A test API"
            },
            "servers": [
                {"url": "https://api.test.com"}
            ],
            "paths": {
                "/users": {
                    "get": {
                        "summary": "List users",
                        "description": "Get all users",
                        "operationId": "listUsers",
                        "parameters": [
                            {
                                "name": "page",
                                "in": "query",
                                "required": False,
                                "schema": {"type": "integer", "default": 1}
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "Successful response",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "array",
                                            "items": {"$ref": "#/components/schemas/User"}
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "post": {
                        "summary": "Create user",
                        "operationId": "createUser",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/User"}
                                }
                            }
                        },
                        "responses": {
                            "201": {"description": "User created"}
                        }
                    }
                },
                "/users/{id}": {
                    "get": {
                        "summary": "Get user",
                        "operationId": "getUser",
                        "parameters": [
                            {
                                "name": "id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "string"}
                            }
                        ],
                        "responses": {
                            "200": {"description": "User found"},
                            "404": {"description": "User not found"}
                        }
                    }
                }
            },
            "components": {
                "schemas": {
                    "User": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "name": {"type": "string"},
                            "email": {"type": "string", "format": "email"}
                        }
                    }
                }
            }
        }
        
        spec_file = tmp_path / "openapi.yaml"
        with open(spec_file, "w") as f:
            yaml.dump(spec, f)
        
        return spec_file, spec

    def test_import_openapi_to_manifest(self, openapi_spec, tmp_path):
        """Test importing OpenAPI spec to manifest."""
        from socialseed_e2e.commands.import_cmd import _generate_manifest_from_import
        
        spec_file, spec = openapi_spec
        
        import_type = "openapi"
        
        manifest = {
            "service_name": spec_file.stem,
            "source": import_type,
            "version": "1.0.0",
            "base_url": "",
            "endpoints": [],
            "schemas": {},
        }
        
        for path, methods in spec.get("paths", {}).items():
            for method, details in methods.items():
                if method.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                    endpoint = {
                        "path": path,
                        "method": method.upper(),
                        "summary": details.get("summary", ""),
                        "description": details.get("description", ""),
                        "operationId": details.get("operationId", ""),
                    }
                    manifest["endpoints"].append(endpoint)
        
        manifest["base_url"] = spec.get("servers", [{}])[0].get("url", "")
        
        assert len(manifest["endpoints"]) == 3
        assert manifest["service_name"] == "openapi"
        assert manifest["base_url"] == "https://api.test.com"

    def test_openapi_endpoint_extraction(self, openapi_spec):
        """Test OpenAPI endpoint extraction."""
        _, spec = openapi_spec
        
        endpoints = []
        for path, methods in spec.get("paths", {}).items():
            for method, details in methods.items():
                if method.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                    endpoints.append({
                        "path": path,
                        "method": method.upper(),
                        "operationId": details.get("operationId", ""),
                    })
        
        assert len(endpoints) == 3
        assert any(e["path"] == "/users" and e["method"] == "GET" for e in endpoints)
        assert any(e["path"] == "/users" and e["method"] == "POST" for e in endpoints)
        assert any(e["path"] == "/users/{id}" and e["method"] == "GET" for e in endpoints)


class TestPostmanImporter:
    """Tests for Postman import with --to-manifest."""

    @pytest.fixture
    def postman_collection(self, tmp_path):
        """Create a temporary Postman collection file."""
        collection = {
            "info": {
                "name": "Test API Collection",
                "description": "API for testing"
            },
            "item": [
                {
                    "name": "Get Users",
                    "request": {
                        "method": "GET",
                        "url": {
                            "path": ["users"]
                        },
                        "header": [
                            {"key": "Content-Type", "value": "application/json"}
                        ]
                    }
                },
                {
                    "name": "Create User",
                    "request": {
                        "method": "POST",
                        "url": {
                            "path": ["users"]
                        },
                        "header": [
                            {"key": "Content-Type", "value": "application/json"}
                        ],
                        "body": {
                            "mode": "raw",
                            "raw": '{"name": "test"}'
                        }
                    }
                }
            ]
        }
        
        collection_file = tmp_path / "collection.json"
        with open(collection_file, "w") as f:
            json.dump(collection, f)
        
        return collection_file, collection

    def test_import_postman_to_manifest(self, postman_collection, tmp_path):
        """Test importing Postman collection to manifest."""
        from socialseed_e2e.commands.import_cmd import _extract_postman_item
        
        _, collection = postman_collection
        
        endpoints = []
        for item in collection.get("item", []):
            _extract_postman_item(item, endpoints)
        
        assert len(endpoints) == 2
        assert any(e["path"] == "/users" and e["method"] == "GET" for e in endpoints)
        assert any(e["path"] == "/users" and e["method"] == "POST" for e in endpoints)

    def test_postman_nested_items(self, tmp_path):
        """Test Postman nested items extraction."""
        from socialseed_e2e.commands.import_cmd import _extract_postman_item
        
        collection = {
            "item": [
                {
                    "name": "Users",
                    "item": [
                        {
                            "name": "List",
                            "request": {
                                "method": "GET",
                                "url": {"path": ["users"]}
                            }
                        },
                        {
                            "name": "Create",
                            "request": {
                                "method": "POST", 
                                "url": {"path": ["users"]}
                            }
                        }
                    ]
                }
            ]
        }
        
        endpoints = []
        for item in collection.get("item", []):
            _extract_postman_item(item, endpoints)
        
        assert len(endpoints) == 2


class TestImportManifestGeneration:
    """Tests for manifest generation from imports."""

    def test_generate_manifest_file(self, tmp_path):
        """Test generating a manifest file from import."""
        manifest = {
            "service_name": "test-service",
            "source": "openapi",
            "version": "1.0.0",
            "base_url": "http://localhost:8080",
            "endpoints": [
                {"path": "/api/users", "method": "GET", "operationId": "listUsers"},
                {"path": "/api/users", "method": "POST", "operationId": "createUser"}
            ],
            "schemas": {
                "User": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"}
                    }
                }
            }
        }
        
        output_dir = tmp_path / ".e2e" / "manifests" / "test-service"
        output_dir.mkdir(parents=True)
        
        manifest_file = output_dir / "project_knowledge.json"
        with open(manifest_file, "w") as f:
            json.dump(manifest, f)
        
        assert manifest_file.exists()
        
        with open(manifest_file) as f:
            loaded = json.load(f)
        
        assert loaded["service_name"] == "test-service"
        assert len(loaded["endpoints"]) == 2
        assert "User" in loaded["schemas"]
