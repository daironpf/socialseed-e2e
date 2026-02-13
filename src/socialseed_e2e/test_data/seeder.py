"""
Data Seeder for managing test data lifecycle.
Supports tracking created resources for automated cleanup.
"""
import logging
from typing import List, Any, Callable, Optional, Dict, Type, TypeVar, Union
from contextlib import contextmanager

from .factories import DataFactory

logger = logging.getLogger(__name__)

T = TypeVar('T')

class DataSeeder:
    """
    Manages data seeding operations and cleanup.
    """
    def __init__(self):
        self._cleanup_stack: List[Callable[[], None]] = []
        self._factories: Dict[str, DataFactory] = {}

    def register_factory(self, name: str, factory: DataFactory):
        """Register a factory for use by name."""
        self._factories[name] = factory

    def get_factory(self, name: str) -> DataFactory:
        """Get a registered factory."""
        if name not in self._factories:
            raise ValueError(f"Factory '{name}' not found. Register it first.")
        return self._factories[name]

    def seed(self, 
             factory: Union[str, DataFactory], 
             count: int = 1, 
             persist_fn: Optional[Callable[[Any], Any]] = None,
             cleanup_fn: Optional[Callable[[Any], None]] = None,
             **kwargs) -> List[Any]:
        """
        Seeds data using a factory.
        
        Args:
            factory: Factory instance or name of registered factory.
            count: Number of items to create.
            persist_fn: Function to persist the object.
            cleanup_fn: Function to accept the persisted object and delete it.
            **kwargs: Overrides for the factory.
        """
        if isinstance(factory, str):
            factory_instance = self.get_factory(factory)
        else:
            factory_instance = factory

        created_items = []
        for _ in range(count):
            item = factory_instance.create(persist_fn=persist_fn, **kwargs)
            created_items.append(item)
            
            if cleanup_fn:
                # Add cleanup for this item to the stack
                # We use a closure to capture the item specific to this iteration
                def cleanup_action(obj=item):
                    try:
                        cleanup_fn(obj)
                    except Exception as e:
                        logger.error(f"Error cleaning up seeded item: {e}")
                
                self._cleanup_stack.append(cleanup_action)
        
        return created_items

    def cleanup(self):
        """Executes all registered cleanup actions in LIFO order."""
        while self._cleanup_stack:
            action = self._cleanup_stack.pop()
            try:
                action()
            except Exception as e:
                logger.error(f"Error during cleanup execution: {e}")

    @contextmanager
    def scope(self):
        """
        Context manager that automatically runs cleanup on exit.
        
        Usage:
            with seeder.scope():
                seeder.seed(...)
            # Cleanup runs here
        """
        try:
            yield self
        finally:
            self.cleanup()
