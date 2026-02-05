"""Universal Pydantic helpers for multi-language backend compatibility.

This module provides utilities for handling serialization between Python and
different backend naming conventions (Java/camelCase, C#/PascalCase, Python/snake_case, etc.).

The framework automatically detects and handles the naming convention of the backend API,
making it easy to create tests for APIs written in any language.

Usage:
    from socialseed_e2e.utils.pydantic_helpers import (
        APIModel, api_field, NamingConvention, get_naming_convention
    )

    # For Java/Spring Boot backend (camelCase)
    class LoginRequest(APIModel):
        model_config = {"naming_convention": NamingConvention.CAMEL_CASE}
        refresh_token: str = api_field("refreshToken")
        user_name: str = api_field("userName")

    # For C#/ASP.NET backend (PascalCase)
    class UserRequest(APIModel):
        model_config = {"naming_convention": NamingConvention.PASCAL_CASE}
        user_id: str = api_field("UserId")
        email_address: str = api_field("EmailAddress")

    # For Python/Flask backend (snake_case)
    class DataRequest(APIModel):
        model_config = {"naming_convention": NamingConvention.SNAKE_CASE}
        user_id: str = api_field("user_id")
        created_at: str = api_field("created_at")

    # Automatic serialization with correct convention
    request = LoginRequest(refresh_token="abc", user_name="john")
    data = request.to_dict()  # {'refreshToken': 'abc', 'userName': 'john'}
"""

import re
from enum import Enum
from typing import Any, Dict, Optional, TypeVar, Union, get_args, get_origin

from pydantic import BaseModel, EmailStr, Field

T = TypeVar("T", bound=BaseModel)


class NamingConvention(Enum):
    """Supported naming conventions for different backend languages."""

    CAMEL_CASE = "camelCase"  # Java, JavaScript, TypeScript, Go
    PASCAL_CASE = "PascalCase"  # C#, Pascal
    SNAKE_CASE = "snake_case"  # Python, Rust, Ruby
    KEBAB_CASE = "kebab-case"  # Some APIs, URLs
    UPPER_SNAKE = "UPPER_SNAKE"  # Environment variables, constants


def to_camel_case(snake_str: str) -> str:
    """Convert snake_case to camelCase.

    Examples:
        >>> to_camel_case("refresh_token")
        'refreshToken'
        >>> to_camel_case("user_id")
        'userId'
    """
    components = snake_str.split("_")
    return components[0] + "".join(x.capitalize() for x in components[1:])


def to_pascal_case(snake_str: str) -> str:
    """Convert snake_case to PascalCase.

    Examples:
        >>> to_pascal_case("user_id")
        'UserId'
        >>> to_pascal_case("refresh_token")
        'RefreshToken'
    """
    components = snake_str.split("_")
    return "".join(x.capitalize() for x in components)


def to_snake_case(camel_str: str) -> str:
    """Convert camelCase/PascalCase to snake_case.

    Examples:
        >>> to_snake_case("refreshToken")
        'refresh_token'
        >>> to_snake_case("UserId")
        'user_id'
    """
    # Handle PascalCase
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", camel_str)
    # Handle camelCase
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def to_kebab_case(snake_str: str) -> str:
    """Convert snake_case to kebab-case."""
    return snake_str.replace("_", "-")


def api_field(json_name: str, convention: Optional[NamingConvention] = None, **kwargs) -> Any:
    """Create a Pydantic Field with proper alias configuration.

    This helper creates fields that serialize correctly for any backend
    naming convention. The framework automatically handles the conversion.

    Args:
        json_name: The field name as it appears in JSON/API
        convention: Naming convention hint (optional, defaults to camelCase)
        **kwargs: Additional Field arguments (default, description, etc.)

    Returns:
        A Pydantic Field configured for the specified naming convention

    Examples:
        # For Java backend (camelCase)
        refresh_token: str = api_field("refreshToken")

        # For C# backend (PascalCase)
        user_id: str = api_field("UserId", NamingConvention.PASCAL_CASE)

        # With default value
        page_size: int = api_field("pageSize", default=20)

        # With description
        email: str = api_field("email", description="User email address")
    """
    return Field(..., alias=json_name, serialization_alias=json_name, **kwargs)


class APIModel(BaseModel):
    """Universal base model for any backend API compatibility.

    This model automatically handles serialization for different backend
    naming conventions (camelCase, PascalCase, snake_case, etc.).

    Usage:
        # Java/Spring Boot (camelCase - default)
        class LoginRequest(APIModel):
            refresh_token: str = api_field("refreshToken")

        # C#/ASP.NET (PascalCase)
        class UserRequest(APIModel):
            model_config = {"naming_convention": NamingConvention.PASCAL_CASE}
            user_id: str = api_field("UserId")

        # Python/Flask (snake_case)
        class DataRequest(APIModel):
            model_config = {"naming_convention": NamingConvention.SNAKE_CASE}
            created_at: str = api_field("created_at")

    Configuration:
        Set naming_convention in model_config to match your backend:
        - NamingConvention.CAMEL_CASE (default) - Java, JS, TS, Go
        - NamingConvention.PASCAL_CASE - C#, Pascal
        - NamingConvention.SNAKE_CASE - Python, Rust
        - NamingConvention.KEBAB_CASE - Some APIs
    """

    model_config = {
        "populate_by_name": True,
        "naming_convention": NamingConvention.CAMEL_CASE,
        "validate_assignment": True,
        "extra": "ignore",  # Ignore extra fields from API responses
    }

    def to_dict(self, **kwargs) -> Dict[str, Any]:
        """Serialize to dictionary with proper naming convention.

        Automatically uses by_alias=True to convert field names
        to the backend's expected format.

        Args:
            **kwargs: Additional arguments passed to model_dump()

        Returns:
            Dictionary with correctly named keys

        Examples:
            # Java backend (camelCase)
            request = LoginRequest(refresh_token="abc")
            data = request.to_dict()  # {'refreshToken': 'abc'}

            # With exclusions
            data = request.to_dict(exclude={'password'})
        """
        return self.model_dump(by_alias=True, **kwargs)

    def to_json(self, **kwargs) -> str:
        """Serialize to JSON string with proper naming convention.

        Args:
            **kwargs: Additional arguments for model_dump_json()

        Returns:
            JSON string with correctly named keys
        """
        return self.model_dump_json(by_alias=True, **kwargs)

    @classmethod
    def from_dict(cls: type[T], data: Dict[str, Any]) -> T:
        """Create instance from dictionary with flexible field matching.

        Thanks to populate_by_name=True, this accepts both:
        - API format: {"refreshToken": "abc", "userName": "john"}
        - Python format: {"refresh_token": "abc", "user_name": "john"}

        Args:
            data: Dictionary with field values

        Returns:
            Instance of the model class

        Examples:
            # From API response (camelCase)
            data = {"refreshToken": "abc"}
            request = RefreshTokenRequest.from_dict(data)

            # From Python code (snake_case)
            data = {"refresh_token": "abc"}
            request = RefreshTokenRequest.from_dict(data)
        """
        return cls.model_validate(data)

    @classmethod
    def get_naming_convention(cls) -> NamingConvention:
        """Get the naming convention for this model.

        Returns:
            The NamingConvention enum value
        """
        config = cls.model_config
        convention = config.get("naming_convention", NamingConvention.CAMEL_CASE)
        if isinstance(convention, str):
            return NamingConvention(convention)
        return convention


def to_api_dict(model: BaseModel, **kwargs) -> Dict[str, Any]:
    """Convert any Pydantic model to API-compatible dictionary.

    This is a standalone function that works with any model,
    including those that don't inherit from APIModel.

    Args:
        model: Any Pydantic model instance
        **kwargs: Additional arguments for model_dump()

    Returns:
        Dictionary with aliased keys

    Example:
        class MyModel(BaseModel):
            model_config = {"populate_by_name": True}
            refresh_token: str = Field(alias="refreshToken")

        m = MyModel(refresh_token="abc")
        data = to_api_dict(m)  # {'refreshToken': 'abc'}
    """
    defaults = {"by_alias": True}
    defaults.update(kwargs)
    return model.model_dump(**defaults)


def validate_api_model(model_class: type[T], data: Dict[str, Any]) -> T:
    """Validate data and create model instance with helpful error messages.

    Args:
        model_class: The Pydantic model class to validate against
        data: Dictionary with field values

    Returns:
        Validated model instance

    Raises:
        ValueError: If validation fails, with detailed error message

    Example:
        try:
            request = validate_api_model(LoginRequest, data)
        except ValueError as e:
            print(f"Validation error: {e}")
    """
    try:
        return model_class.model_validate(data)
    except Exception as e:
        # Provide helpful error message
        class_name = model_class.__name__
        fields = list(model_class.model_fields.keys())
        raise ValueError(
            f"Failed to validate {class_name}: {e}\n"
            f"Expected fields: {fields}\n"
            f"Input data: {data}"
        ) from e


def detect_naming_convention(sample_data: Dict[str, Any]) -> NamingConvention:
    """Detect the naming convention used in sample data.

    Analyzes the keys of a dictionary to determine the likely
    naming convention being used.

    Args:
        sample_data: Dictionary with sample field names

    Returns:
        Detected NamingConvention

    Example:
        >>> data = {"refreshToken": "abc", "userName": "john"}
        >>> detect_naming_convention(data)
        NamingConvention.CAMEL_CASE
    """
    if not sample_data:
        return NamingConvention.CAMEL_CASE  # Default

    keys = list(sample_data.keys())
    if not keys:
        return NamingConvention.CAMEL_CASE

    # Check first few keys
    sample_keys = keys[:5]

    camel_count = 0
    pascal_count = 0
    snake_count = 0
    kebab_count = 0

    for key in sample_keys:
        if "-" in key:
            kebab_count += 1
        elif "_" in key:
            snake_count += 1
        elif key[0].isupper():
            pascal_count += 1
        elif any(c.isupper() for c in key[1:]):
            camel_count += 1

    # Determine most likely convention
    counts = [
        (camel_count, NamingConvention.CAMEL_CASE),
        (pascal_count, NamingConvention.PASCAL_CASE),
        (snake_count, NamingConvention.SNAKE_CASE),
        (kebab_count, NamingConvention.KEBAB_CASE),
    ]

    # Return the one with highest count, or default to camelCase
    return (
        max(counts, key=lambda x: x[0])[1]
        if max(c[0] for c in counts) > 0
        else NamingConvention.CAMEL_CASE
    )


# Convenience field creators for common patterns
def camel_field(name: str, **kwargs) -> Any:
    """Create field for camelCase (Java, JS, TS, Go)."""
    if "_" in name:
        # If name is snake_case, convert to camelCase
        name = to_camel_case(name)
    return api_field(name, NamingConvention.CAMEL_CASE, **kwargs)


def pascal_field(name: str, **kwargs) -> Any:
    """Create field for PascalCase (C#)."""
    if "_" in name:
        # If name is snake_case, convert to PascalCase
        name = to_pascal_case(name)
    return api_field(name, NamingConvention.PASCAL_CASE, **kwargs)


def snake_field(name: str, **kwargs) -> Any:
    """Create field for snake_case (Python, Rust)."""
    return api_field(name, NamingConvention.SNAKE_CASE, **kwargs)


# Pre-defined fields for common patterns
refresh_token_field = lambda **kwargs: camel_field("refreshToken", **kwargs)
access_token_field = lambda **kwargs: camel_field("accessToken", **kwargs)
user_name_field = lambda **kwargs: camel_field("userName", **kwargs)
user_id_field = lambda **kwargs: camel_field("userId", **kwargs)
created_at_field = lambda **kwargs: camel_field("createdAt", **kwargs)
updated_at_field = lambda **kwargs: camel_field("updatedAt", **kwargs)
new_password_field = lambda **kwargs: camel_field("newPassword", **kwargs)
current_password_field = lambda **kwargs: camel_field("currentPassword", **kwargs)


# Backwards compatibility aliases
JavaCompatibleModel = APIModel  # For existing code
to_camel_dict = to_api_dict  # For existing code
validate_camelcase_model = validate_api_model  # For existing code
