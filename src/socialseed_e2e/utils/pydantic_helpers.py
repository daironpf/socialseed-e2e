"""Pydantic helpers for Java backend compatibility.

This module provides utilities for handling serialization between Python (snake_case)
and Java (camelCase) naming conventions, which is a common pain point when creating
tests for Spring Boot backends.

Usage:
    from socialseed_e2e.utils.pydantic_helpers import JavaCompatibleModel, to_camel_dict

    class MyRequest(JavaCompatibleModel):
        refresh_token: str = camel_field("refreshToken")
        user_name: str = camel_field("userName")

    # Automatically serializes to camelCase
    request = MyRequest(refresh_token="abc", user_name="john")
    data = request.model_dump(by_alias=True)  # {'refreshToken': 'abc', 'userName': 'john'}
"""

from typing import Any, Dict, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T", bound=BaseModel)


def camel_field(alias: str, **kwargs) -> Any:
    """Create a Pydantic Field with camelCase alias for Java backend compatibility.

    This helper simplifies creating fields that need camelCase serialization
    for Java/Spring Boot backends while keeping snake_case in Python.

    Args:
        alias: The camelCase field name (e.g., "refreshToken", "userName")
        **kwargs: Additional Field arguments (default, description, etc.)

    Returns:
        A Pydantic Field configured for camelCase serialization

    Example:
        class LoginRequest(JavaCompatibleModel):
            refresh_token: str = camel_field("refreshToken")
            user_name: str = camel_field("userName", default="guest")

    Note:
        Always use `by_alias=True` when calling model_dump():
        data = request.model_dump(by_alias=True)
    """
    return Field(..., alias=alias, serialization_alias=alias, **kwargs)


class JavaCompatibleModel(BaseModel):
    """Base model pre-configured for Java/Spring Boot backend compatibility.

    This model automatically:
    - Enables populate_by_name for flexible field access
    - Provides helper methods for camelCase serialization
    - Validates required fields with Java-friendly error messages

    Usage:
        class RefreshTokenRequest(JavaCompatibleModel):
            refresh_token: str = camel_field("refreshToken")

        # Create and serialize
        request = RefreshTokenRequest(refresh_token="abc123")
        json_data = request.to_json()  # Automatically uses camelCase

    Attributes:
        model_config: Configured with populate_by_name=True
    """

    model_config = {"populate_by_name": True}

    def to_dict(self, **kwargs) -> Dict[str, Any]:
        """Serialize to dictionary with camelCase field names.

        This method automatically sets by_alias=True for Java compatibility.

        Args:
            **kwargs: Additional arguments passed to model_dump()

        Returns:
            Dictionary with camelCase keys

        Example:
            request = RefreshTokenRequest(refresh_token="abc")
            data = request.to_dict()  # {'refreshToken': 'abc'}
            data = request.to_dict(exclude={'id'})  # With exclusions
        """
        return self.model_dump(by_alias=True, **kwargs)

    def to_json(self, **kwargs) -> str:
        """Serialize to JSON string with camelCase field names.

        Args:
            **kwargs: Additional arguments passed to model_dump_json()

        Returns:
            JSON string with camelCase keys

        Example:
            request = RefreshTokenRequest(refresh_token="abc")
            json_str = request.to_json()  # '{"refreshToken":"abc"}'
        """
        return self.model_dump_json(by_alias=True, **kwargs)

    @classmethod
    def from_dict(cls: type[T], data: Dict[str, Any]) -> T:
        """Create instance from dictionary, handling both snake_case and camelCase.

        Thanks to populate_by_name=True, this accepts both:
        - Java style: {"refreshToken": "abc"}
        - Python style: {"refresh_token": "abc"}

        Args:
            data: Dictionary with field values

        Returns:
            Instance of the model class

        Example:
            # Works with camelCase (from Java response)
            data = {"refreshToken": "abc"}
            request = RefreshTokenRequest.from_dict(data)

            # Also works with snake_case (from Python)
            data = {"refresh_token": "abc"}
            request = RefreshTokenRequest.from_dict(data)
        """
        return cls.model_validate(data)


def to_camel_dict(model: BaseModel, **kwargs) -> Dict[str, Any]:
    """Convert any Pydantic model to camelCase dictionary.

    This is a standalone function for models that don't inherit from
    JavaCompatibleModel but still need camelCase serialization.

    Args:
        model: Any Pydantic model instance
        **kwargs: Additional arguments for model_dump()

    Returns:
        Dictionary with camelCase keys

    Example:
        class MyModel(BaseModel):
            model_config = {"populate_by_name": True}
            refresh_token: str = Field(alias="refreshToken")

        m = MyModel(refresh_token="abc")
        data = to_camel_dict(m)  # {'refreshToken': 'abc'}

    Note:
        The model must have proper Field(alias="camelCase") definitions
        and model_config with populate_by_name=True for this to work.
    """
    return model.model_dump(by_alias=True, **kwargs)


def validate_camelcase_model(model_class: type[T], data: Dict[str, Any]) -> T:
    """Validate data and create model instance with camelCase support.

    This helper validates input data against a model class and provides
    helpful error messages if validation fails.

    Args:
        model_class: The Pydantic model class to validate against
        data: Dictionary with field values

    Returns:
        Validated model instance

    Raises:
        ValueError: If validation fails, with detailed error message

    Example:
        try:
            request = validate_camelcase_model(RefreshTokenRequest, data)
        except ValueError as e:
            print(f"Validation error: {e}")
    """
    try:
        return model_class.model_validate(data)
    except Exception as e:
        raise ValueError(
            f"Failed to validate {model_class.__name__}: {e}\nInput data: {data}"
        ) from e


# Convenience aliases for common naming patterns
refresh_token_field = lambda **kwargs: camel_field("refreshToken", **kwargs)
access_token_field = lambda **kwargs: camel_field("accessToken", **kwargs)
user_name_field = lambda **kwargs: camel_field("userName", **kwargs)
user_id_field = lambda **kwargs: camel_field("userId", **kwargs)
created_at_field = lambda **kwargs: camel_field("createdAt", **kwargs)
updated_at_field = lambda **kwargs: camel_field("updatedAt", **kwargs)
new_password_field = lambda **kwargs: camel_field("newPassword", **kwargs)
current_password_field = lambda **kwargs: camel_field("currentPassword", **kwargs)
