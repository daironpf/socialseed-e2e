"""Unit tests for Pydantic helpers.

This module contains unit tests for universal Pydantic helpers
and multi-language backend compatibility utilities.
"""

import pytest
from pydantic import Field

from socialseed_e2e.utils.pydantic_helpers import (
    APIModel,
    NamingConvention,
    api_field,
    camel_field,
    detect_naming_convention,
    pascal_field,
    to_api_dict,
    to_camel_case,
    to_pascal_case,
    to_snake_case,
    validate_api_model,
)


class TestNamingConversions:
    """Test string naming conversion utilities."""

    def test_to_camel_case(self):
        assert to_camel_case("user_id") == "userId"
        assert to_camel_case("refresh_token_test") == "refreshTokenTest"

    def test_to_pascal_case(self):
        assert to_pascal_case("user_id") == "UserId"
        assert to_pascal_case("refresh_token_test") == "RefreshTokenTest"

    def test_to_snake_case(self):
        assert to_snake_case("userId") == "user_id"
        assert to_snake_case("UserId") == "user_id"
        assert to_snake_case("refreshTokenTest") == "refresh_token_test"


class TestAPIModel:
    """Test the APIModel base class."""

    def test_api_model_camel_case(self):
        class User(APIModel):
            user_id: str = api_field("userId")
            email: str = api_field("emailAddress")

        user = User(user_id="123", email="test@example.com")

        # Test serialization
        d = user.to_dict()
        assert d == {"userId": "123", "emailAddress": "test@example.com"}

        # Test deserialization
        user2 = User.from_dict({"userId": "456", "emailAddress": "test2@example.com"})
        assert user2.user_id == "456"

    def test_api_model_pascal_case(self):
        class User(APIModel):
            model_config = {"naming_convention": NamingConvention.PASCAL_CASE}
            user_id: str = api_field("UserId")

        user = User(user_id="123")
        assert user.to_dict() == {"UserId": "123"}

    def test_validate_api_model_success(self):
        class SimpleModel(APIModel):
            name: str

        data = {"name": "test"}
        model = validate_api_model(SimpleModel, data)
        assert model.name == "test"

    def test_validate_api_model_failure(self):
        class SimpleModel(APIModel):
            name: str

        with pytest.raises(ValueError, match="Failed to validate SimpleModel"):
            validate_api_model(SimpleModel, {"wrong": "data"})


class TestFieldHelpers:
    """Test convenience field creators."""

    def test_camel_field(self):
        class MyModel(APIModel):
            user_id: str = camel_field("user_id")

        m = MyModel(user_id="abc")
        assert m.to_dict() == {"userId": "abc"}

    def test_pascal_field(self):
        class MyModel(APIModel):
            user_id: str = pascal_field("user_id")

        m = MyModel(user_id="abc")
        assert m.to_dict() == {"UserId": "abc"}


def test_to_api_dict():
    from pydantic import BaseModel

    class LegacyModel(BaseModel):
        user_id: str = Field(alias="userId")

    m = LegacyModel(userId="123")
    assert to_api_dict(m) == {"userId": "123"}


def test_detect_naming_convention():
    assert detect_naming_convention({"userId": "1"}) == NamingConvention.CAMEL_CASE
    assert detect_naming_convention({"UserId": "1"}) == NamingConvention.PASCAL_CASE
    assert detect_naming_convention({"user_id": "1"}) == NamingConvention.SNAKE_CASE
    assert detect_naming_convention({"user-id": "1"}) == NamingConvention.KEBAB_CASE
