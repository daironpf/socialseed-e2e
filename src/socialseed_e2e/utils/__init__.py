"""Utility functions for socialseed-e2e."""

from .pydantic_helpers import (
    JavaCompatibleModel,
    camel_field,
    created_at_field,
    current_password_field,
    new_password_field,
    refresh_token_field,
    to_camel_dict,
    updated_at_field,
    user_id_field,
    user_name_field,
    validate_camelcase_model,
)
from .state_management import AuthStateMixin, DynamicStateMixin
from .template_engine import TemplateEngine, to_camel_case, to_class_name, to_snake_case
from .validators import (
    ValidationError,
    validate_base_url,
    validate_dict,
    validate_email,
    validate_integer,
    validate_json_response,
    validate_list,
    validate_pagination_response,
    validate_port,
    validate_service_name,
    validate_status_code,
    validate_string,
    validate_timeout,
    validate_url,
    validate_uuid,
)

__all__ = [
    # State management
    "DynamicStateMixin",
    "AuthStateMixin",
    # Pydantic helpers for Java compatibility
    "JavaCompatibleModel",
    "camel_field",
    "to_camel_dict",
    "validate_camelcase_model",
    "refresh_token_field",
    "user_name_field",
    "user_id_field",
    "created_at_field",
    "updated_at_field",
    "new_password_field",
    "current_password_field",
    # Template engine
    "TemplateEngine",
    "to_class_name",
    "to_snake_case",
    "to_camel_case",
    # Validators
    "ValidationError",
    "validate_url",
    "validate_base_url",
    "validate_port",
    "validate_timeout",
    "validate_service_name",
    "validate_string",
    "validate_integer",
    "validate_email",
    "validate_uuid",
    "validate_status_code",
    "validate_json_response",
    "validate_pagination_response",
    "validate_list",
    "validate_dict",
]
