"""State management mixins for Page Objects.

This module provides mixins for managing dynamic state in Page Objects,
solving the common problem of LSP errors when assigning dynamic attributes
to share state between tests.

Problem:
    When tests need to share state (tokens, IDs), they often assign dynamic
    attributes to the Page object. This causes LSP errors:

    ERROR: Cannot assign to attribute "current_user_email" for class "AuthServicePage"
        Attribute "current_user_email" is unknown

Solution:
    Use DynamicStateMixin which provides a type-safe way to store and retrieve
    shared state between test modules.

Usage:
    class AuthServicePage(BasePage, DynamicStateMixin):
        def __init__(self, base_url: str, **kwargs):
            super().__init__(base_url=base_url, **kwargs)
            self.init_dynamic_state()  # Initialize the state container

    # In test module 01:
    page.set_state("user_id", "123")
    page.set_state("auth_token", "abc")

    # In test module 02:
    user_id = page.get_state("user_id")  # Returns "123"
    auth_token = page.get_state("auth_token")  # Returns "abc"
"""

from typing import Any, Dict, Generic, Optional, TypeVar

T = TypeVar("T")


class DynamicStateMixin:
    """Mixin to add dynamic state management to Page Objects.

    This mixin provides a type-safe, dictionary-based approach to storing
    and retrieving shared state between test modules.

    Attributes:
        _dynamic_state: Internal dictionary storing all dynamic state

    Example:
        class MyPage(BasePage, DynamicStateMixin):
            def __init__(self, base_url: str, **kwargs):
                super().__init__(base_url=base_url, **kwargs)
                self.init_dynamic_state()

        # Store values
        page.set_state("created_user_id", "uuid-123")
        page.set_state("auth_token", "token-abc")

        # Retrieve values
        user_id = page.get_state("created_user_id")  # "uuid-123"
        token = page.get_state("auth_token", default="")  # "token-abc"

        # Type-safe retrieval with casting
        user_id = page.get_state_as(str, "created_user_id")
        count = page.get_state_as(int, "item_count", default=0)
    """

    _dynamic_state: Dict[str, Any]

    def init_dynamic_state(self) -> None:
        """Initialize the dynamic state container.

        Must be called in the __init__ method of your Page class.

        Example:
            class MyPage(BasePage, DynamicStateMixin):
                def __init__(self, base_url: str, **kwargs):
                    super().__init__(base_url=base_url, **kwargs)
                    self.init_dynamic_state()  # Initialize here
        """
        self._dynamic_state = {}

    def set_state(self, key: str, value: Any) -> None:
        """Store a value in the dynamic state.

        Args:
            key: Identifier for the value (e.g., "user_id", "auth_token")
            value: Any value to store

        Example:
            page.set_state("user_id", "123")
            page.set_state("user_data", {"name": "John", "email": "john@example.com"})
        """
        self._dynamic_state[key] = value

    def get_state(self, key: str, default: Any = None) -> Any:
        """Retrieve a value from the dynamic state.

        Args:
            key: Identifier for the value
            default: Value to return if key doesn't exist (default: None)

        Returns:
            The stored value or the default

        Example:
            user_id = page.get_state("user_id")  # Returns value or None
            user_id = page.get_state("user_id", default="")  # Returns value or ""
        """
        return self._dynamic_state.get(key, default)

    def get_state_as(self, type_: type[T], key: str, default: T = None) -> T:
        """Type-safe retrieval of state values.

        Args:
            type_: Expected type of the value (str, int, etc.)
            key: Identifier for the value
            default: Default value if key doesn't exist

        Returns:
            The stored value cast to the specified type

        Raises:
            TypeError: If the stored value is not of the expected type

        Example:
            user_id = page.get_state_as(str, "user_id")
            count = page.get_state_as(int, "item_count", default=0)
        """
        value = self._dynamic_state.get(key, default)
        if value is not None and not isinstance(value, type_):
            raise TypeError(
                f"State value for '{key}' is {type(value).__name__}, " f"expected {type_.__name__}"
            )
        return value

    def has_state(self, key: str) -> bool:
        """Check if a key exists in the dynamic state.

        Args:
            key: Identifier to check

        Returns:
            True if the key exists, False otherwise

        Example:
            if page.has_state("user_id"):
                user_id = page.get_state("user_id")
        """
        return key in self._dynamic_state

    def remove_state(self, key: str) -> Optional[Any]:
        """Remove a value from the dynamic state.

        Args:
            key: Identifier to remove

        Returns:
            The removed value, or None if key didn't exist

        Example:
            old_value = page.remove_state("temporary_token")
        """
        return self._dynamic_state.pop(key, None)

    def clear_state(self) -> None:
        """Clear all dynamic state.

        Useful for cleanup between test suites or when switching users.

        Example:
            page.clear_state()  # Removes all stored values
        """
        self._dynamic_state.clear()

    def get_all_state(self) -> Dict[str, Any]:
        """Get a copy of all dynamic state.

        Returns:
            Dictionary containing all stored state

        Example:
            all_state = page.get_all_state()
            print(f"Stored keys: {list(all_state.keys())}")
        """
        return self._dynamic_state.copy()

    def require_state(self, key: str, error_msg: Optional[str] = None) -> Any:
        """Get a required state value, raising an error if not found.

        This is useful for dependencies between test modules where a value
        MUST exist from a previous step.

        Args:
            key: Identifier for the value
            error_msg: Custom error message (optional)

        Returns:
            The stored value

        Raises:
            RuntimeError: If the key doesn't exist

        Example:
            # Will raise RuntimeError if "user_id" wasn't set by previous test
            user_id = page.require_state("user_id")

            # With custom error message
            user_id = page.require_state(
                "user_id",
                error_msg="User must be created in registration test first"
            )
        """
        if key not in self._dynamic_state:
            msg = (
                error_msg
                or f"Required state '{key}' not found. "
                f"Ensure previous test modules ran successfully."
            )
            raise RuntimeError(msg)
        return self._dynamic_state[key]


class AuthStateMixin(DynamicStateMixin):
    """Specialized mixin for authentication-related state.

    Provides convenient properties for common auth values like tokens,
    user IDs, and credentials.

    Example:
        class AuthPage(BasePage, AuthStateMixin):
            def __init__(self, base_url: str, **kwargs):
                super().__init__(base_url=base_url, **kwargs)
                self.init_auth_state()  # Initializes both auth and dynamic state

        # Store auth values
        page.access_token = "token-abc"
        page.user_id = "user-123"

        # Retrieve auth values
        token = page.access_token
        user_id = page.user_id
    """

    def init_auth_state(self) -> None:
        """Initialize both dynamic state and auth-specific properties."""
        self.init_dynamic_state()
        # Initialize standard auth properties
        self.set_state("access_token", None)
        self.set_state("refresh_token", None)
        self.set_state("user_id", None)
        self.set_state("user_email", None)
        self.set_state("user_name", None)

    @property
    def access_token(self) -> Optional[str]:
        """Get the current access token."""
        return self.get_state("access_token")

    @access_token.setter
    def access_token(self, value: Optional[str]) -> None:
        """Set the access token."""
        self.set_state("access_token", value)

    @property
    def refresh_token(self) -> Optional[str]:
        """Get the current refresh token."""
        return self.get_state("refresh_token")

    @refresh_token.setter
    def refresh_token(self, value: Optional[str]) -> None:
        """Set the refresh token."""
        self.set_state("refresh_token", value)

    @property
    def user_id(self) -> Optional[str]:
        """Get the current user ID."""
        return self.get_state("user_id")

    @user_id.setter
    def user_id(self, value: Optional[str]) -> None:
        """Set the user ID."""
        self.set_state("user_id", value)

    @property
    def user_email(self) -> Optional[str]:
        """Get the current user email."""
        return self.get_state("user_email")

    @user_email.setter
    def user_email(self, value: Optional[str]) -> None:
        """Set the user email."""
        self.set_state("user_email", value)

    @property
    def user_name(self) -> Optional[str]:
        """Get the current user name."""
        return self.get_state("user_name")

    @user_name.setter
    def user_name(self, value: Optional[str]) -> None:
        """Set the user name."""
        self.set_state("user_name", value)

    @property
    def is_authenticated(self) -> bool:
        """Check if currently authenticated (has access token)."""
        return self.access_token is not None

    def clear_auth(self) -> None:
        """Clear all authentication state."""
        self.set_state("access_token", None)
        self.set_state("refresh_token", None)
        self.set_state("user_id", None)
