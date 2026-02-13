"""
Data Factory implementation for generating test data based on Pydantic models.
Inspired by factory_boy but designed for Pydantic and API E2E testing.
"""
import logging
from typing import Any, Callable, Dict, Generic, List, Optional, Type, TypeVar, Union

from pydantic import BaseModel

try:
    from faker import Faker
except ImportError:
    Faker = None  # type: ignore

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class DataFactory(Generic[T]):
    """
    Base class for data factories.

    Usage:
        class UserFactory(DataFactory[User]):
            model = User

            def definition(self):
                return {
                    "username": self.faker.user_name(),
                    "email": self.faker.email()
                }
    """

    model: Type[T]
    _faker: Optional["Faker"] = None

    def __init__(self, locale: str = "en_US"):
        self.locale = locale

    @property
    def faker(self) -> "Faker":
        if self._faker is None:
            if Faker is None:
                raise ImportError("Faker is not installed. Install with 'pip install Faker'")
            self._faker = Faker(self.locale)
        return self._faker

    def definition(self) -> Dict[str, Any]:
        """
        Define default attributes for the model.
        Override this method in subclasses.
        """
        return {}

    def _generate_data(self, **overrides) -> Dict[str, Any]:
        """Generates data by merging definition with overrides."""
        data = self.definition()
        data.update(overrides)
        return data

    def build(self, **kwargs) -> T:
        """
        Builds an instance of the model without persisting it.
        """
        data = self._generate_data(**kwargs)
        return self.model(**data)

    def build_batch(self, size: int, **kwargs) -> List[T]:
        """Builds a batch of model instances."""
        return [self.build(**kwargs) for _ in range(size)]

    def create(self, persist_fn: Optional[Callable[[T], T]] = None, **kwargs) -> T:
        """
        Builds and optionally persists the model instance.

        Args:
            persist_fn: Function to persist the object (e.g., API call).
                        If None, behaves like build().
            **kwargs: Attribute overrides.
        """
        instance = self.build(**kwargs)
        if persist_fn:
            try:
                return persist_fn(instance)
            except Exception as e:
                logger.error(f"Failed to persist instance of {self.model.__name__}: {e}")
                raise e
        return instance

    def create_batch(
        self, size: int, persist_fn: Optional[Callable[[T], T]] = None, **kwargs
    ) -> List[T]:
        """Creates and persists a batch of instances."""
        instances = []
        for _ in range(size):
            instances.append(self.create(persist_fn, **kwargs))
        return instances
