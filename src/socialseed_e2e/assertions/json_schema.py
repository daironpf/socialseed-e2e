"""JSON Schema assertions for socialseed-e2e."""

import json
from typing import Any, Dict, List, Optional, Union

from socialseed_e2e.assertions.base import E2EAssertionError

try:
    import jsonschema

    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False


def assert_valid_schema(
    data: Union[Dict[str, Any], List[Any], str],
    schema: Union[Dict[str, Any], str],
    message: Optional[str] = None,
) -> None:
    """Assert that data matches the provided JSON schema.

    Args:
        data: The data to validate (dict, list or JSON string)
        schema: The JSON schema (dict or JSON string)
        message: Optional custom error message

    Raises:
        ImportError: If jsonschema is not installed
        E2EAssertionError: If validation fails
    """
    if not HAS_JSONSCHEMA:
        raise ImportError(
            "jsonschema package is required for schema validation. "
            "Install it with: pip install jsonschema"
        )

    # Parse JSON if strings are provided
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError as e:
            raise E2EAssertionError(f"Data is not valid JSON: {str(e)}", actual=data)

    if isinstance(schema, str):
        try:
            schema = json.loads(schema)
        except json.JSONDecodeError as e:
            raise E2EAssertionError(f"Schema is not valid JSON: {str(e)}", actual=schema)

    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.exceptions.ValidationError as e:
        default_msg = f"JSON Schema validation failed: {e.message}"
        if e.path:
            path = " -> ".join(str(p) for p in e.path)
            default_msg += f" (Path: {path})"

        raise E2EAssertionError(
            message=message or default_msg,
            actual=e.instance,
            expected=e.validator_value,
            context={"schema_path": list(e.schema_path)},
        )
    except jsonschema.exceptions.SchemaError as e:
        raise E2EAssertionError(f"Invalid JSON Schema: {e.message}")
