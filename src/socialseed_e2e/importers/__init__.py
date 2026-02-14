"""
Migration Assistant for importing external formats into SocialSeed E2E.

This module provides importers for:
- Postman Collections (v2.1)
- OpenAPI/Swagger specifications (3.0+)
- Postman Environments
- Curl commands

Usage:
    from socialseed_e2e.importers import PostmanImporter, OpenAPIImporter

    importer = PostmanImporter()
    tests = importer.import_collection("collection.json")
"""

from socialseed_e2e.importers.curl_importer import CurlImporter
from socialseed_e2e.importers.openapi_importer import OpenAPIImporter
from socialseed_e2e.importers.postman_importer import (
    PostmanEnvironmentImporter,
    PostmanImporter,
)

__all__ = [
    "PostmanImporter",
    "PostmanEnvironmentImporter",
    "OpenAPIImporter",
    "CurlImporter",
]
