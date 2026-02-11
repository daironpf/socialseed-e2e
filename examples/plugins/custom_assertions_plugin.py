"""Example: Custom Assertion Plugin.

This example demonstrates how to create a custom assertion plugin
that registers new assertion functions with the framework.

Usage:
    1. Save this file as a plugin
    2. The plugin will register custom assertions when loaded
    3. Use the assertions in your tests
"""

import re
from typing import Any, Dict, List, Optional

from socialseed_e2e.plugins import (
    AssertionRegistry,
    IAssertionPlugin,
)


class CustomAssertionsPlugin(IAssertionPlugin):
    """Example plugin that provides custom assertions.

    This plugin registers custom assertion functions that can be
    used throughout the framework for specialized validation.

    Custom Assertions Provided:
        - assert_valid_email: Validates email format
        - assert_valid_url: Validates URL format
        - assert_contains_all: Checks if all items are in a collection
        - assert_json_schema: Validates JSON against a schema
        - assert_status_range: Validates HTTP status code range
    """

    name = "custom-assertions"
    version = "1.0.0"
    description = "Provides custom assertion functions"

    def __init__(self):
        self.registry: Optional[AssertionRegistry] = None

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the plugin.

        Args:
            config: Optional configuration
        """
        print(f"✓ Custom Assertions plugin initialized")

    def shutdown(self) -> None:
        """Clean up resources."""
        print(f"✓ Custom Assertions plugin shutdown")

    def register_assertions(self, registry: AssertionRegistry) -> None:
        """Register custom assertions with the framework.

        Args:
            registry: Assertion registry to register with
        """
        self.registry = registry

        # Register all custom assertions
        registry.register("assert_valid_email", self.assert_valid_email)
        registry.register("assert_valid_url", self.assert_valid_url)
        registry.register("assert_contains_all", self.assert_contains_all)
        registry.register("assert_json_schema", self.assert_json_schema)
        registry.register("assert_status_range", self.assert_status_range)

        print(f"  Registered 5 custom assertions")

    def assert_valid_email(self, email: str) -> None:
        """Assert that a string is a valid email address.

        Args:
            email: Email address to validate

        Raises:
            AssertionError: If email is invalid
        """
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, email):
            raise AssertionError(f"Invalid email format: {email}")

    def assert_valid_url(self, url: str) -> None:
        """Assert that a string is a valid URL.

        Args:
            url: URL to validate

        Raises:
            AssertionError: If URL is invalid
        """
        pattern = r"^https?://[^\s/$.?#].[^\s]*$"
        if not re.match(pattern, url, re.IGNORECASE):
            raise AssertionError(f"Invalid URL format: {url}")

    def assert_contains_all(
        self,
        collection: List[Any],
        items: List[Any],
    ) -> None:
        """Assert that a collection contains all specified items.

        Args:
            collection: Collection to check
            items: Items that should be in the collection

        Raises:
            AssertionError: If any item is missing
        """
        missing = [item for item in items if item not in collection]
        if missing:
            raise AssertionError(f"Collection missing items: {missing}")

    def assert_json_schema(
        self,
        data: Dict[str, Any],
        schema: Dict[str, Any],
    ) -> None:
        """Assert that data matches a JSON schema.

        Basic schema validation - checks required fields and types.

        Args:
            data: Data to validate
            schema: Schema definition with 'required' and 'properties'

        Raises:
            AssertionError: If data doesn't match schema
        """
        # Check required fields
        required = schema.get("required", [])
        for field in required:
            if field not in data:
                raise AssertionError(f"Missing required field: {field}")

        # Check field types
        properties = schema.get("properties", {})
        for field, field_schema in properties.items():
            if field in data:
                expected_type = field_schema.get("type")
                if expected_type:
                    value = data[field]
                    type_map = {
                        "string": str,
                        "integer": int,
                        "number": (int, float),
                        "boolean": bool,
                        "array": list,
                        "object": dict,
                    }
                    if expected_type in type_map:
                        if not isinstance(value, type_map[expected_type]):
                            raise AssertionError(
                                f"Field '{field}' should be {expected_type}, "
                                f"got {type(value).__name__}"
                            )

    def assert_status_range(
        self,
        status_code: int,
        min_code: int = 200,
        max_code: int = 299,
    ) -> None:
        """Assert that HTTP status code is within range.

        Args:
            status_code: HTTP status code
            min_code: Minimum acceptable code (default: 200)
            max_code: Maximum acceptable code (default: 299)

        Raises:
            AssertionError: If status code is out of range
        """
        if not (min_code <= status_code <= max_code):
            raise AssertionError(
                f"Status code {status_code} not in range [{min_code}, {max_code}]"
            )


# Plugin metadata for discovery
__plugin_metadata__ = {
    "name": CustomAssertionsPlugin.name,
    "version": CustomAssertionsPlugin.version,
    "description": CustomAssertionsPlugin.description,
    "author": "socialseed-e2e",
    "entry_point": "custom_assertions_plugin:CustomAssertionsPlugin",
    "tags": ["assertions", "validation", "example"],
}


# Example usage
if __name__ == "__main__":
    print("=" * 60)
    print("Example: Custom Assertions Plugin")
    print("=" * 60)

    # Create plugin
    plugin = CustomAssertionsPlugin()
    plugin.initialize()

    # Create registry and register assertions
    from socialseed_e2e.plugins import AssertionRegistry

    registry = AssertionRegistry()
    plugin.register_assertions(registry)

    print("\n📋 Testing assertions:")

    # Test assert_valid_email
    print("\n1. Testing assert_valid_email:")
    try:
        registry.get("assert_valid_email")("test@example.com")
        print("   ✓ test@example.com is valid")
    except AssertionError as e:
        print(f"   ✗ {e}")

    try:
        registry.get("assert_valid_email")("invalid-email")
        print("   ✗ invalid-email should have failed")
    except AssertionError as e:
        print(f"   ✓ Correctly rejected: {e}")

    # Test assert_valid_url
    print("\n2. Testing assert_valid_url:")
    try:
        registry.get("assert_valid_url")("https://api.example.com")
        print("   ✓ https://api.example.com is valid")
    except AssertionError as e:
        print(f"   ✗ {e}")

    # Test assert_contains_all
    print("\n3. Testing assert_contains_all:")
    try:
        registry.get("assert_contains_all")(
            ["apple", "banana", "cherry"], ["apple", "cherry"]
        )
        print("   ✓ Collection contains all items")
    except AssertionError as e:
        print(f"   ✗ {e}")

    # Test assert_json_schema
    print("\n4. Testing assert_json_schema:")
    user_data = {"id": 1, "name": "John", "email": "john@example.com"}
    user_schema = {
        "required": ["id", "name"],
        "properties": {
            "id": {"type": "integer"},
            "name": {"type": "string"},
            "email": {"type": "string"},
        },
    }
    try:
        registry.get("assert_json_schema")(user_data, user_schema)
        print("   ✓ Data matches schema")
    except AssertionError as e:
        print(f"   ✗ {e}")

    # Test assert_status_range
    print("\n5. Testing assert_status_range:")
    try:
        registry.get("assert_status_range")(200)
        print("   ✓ Status 200 is in valid range")
        registry.get("assert_status_range")(404, 400, 499)
        print("   ✓ Status 404 is in 4xx range")
    except AssertionError as e:
        print(f"   ✗ {e}")

    # List registered assertions
    print("\n📋 Registered assertions:")
    for name in registry.list_assertions():
        print(f"   - {name}")

    plugin.shutdown()

    print("\n" + "=" * 60)
    print("Example completed!")
    print("=" * 60)
