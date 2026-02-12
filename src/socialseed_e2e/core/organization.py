"""Advanced test organization for socialseed-e2e.

Provides decorators and utilities for tagging, dependencies, and priorities.
"""

from enum import IntEnum
from typing import Callable, List, Optional, Any, Set, Dict


class Priority(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


def tag(*tags: str):
    """Decorator to add tags to a test module's run function."""
    def decorator(func: Callable):
        if not hasattr(func, "_e2e_metadata"):
            func._e2e_metadata = {}
        if "tags" not in func._e2e_metadata:
            func._e2e_metadata["tags"] = set()
        func._e2e_metadata["tags"].update(tags)
        return func
    return decorator


def depends_on(*dependencies: str):
    """Decorator to define test dependencies.
    
    Dependencies should be valid test module names (e.g. 'test_login').
    """
    def decorator(func: Callable):
        if not hasattr(func, "_e2e_metadata"):
            func._e2e_metadata = {}
        if "depends_on" not in func._e2e_metadata:
            func._e2e_metadata["depends_on"] = set()
        func._e2e_metadata["depends_on"].update(dependencies)
        return func
    return decorator


def priority(level: Priority):
    """Decorator to set test priority."""
    def decorator(func: Callable):
        if not hasattr(func, "_e2e_metadata"):
            func._e2e_metadata = {}
        func._e2e_metadata["priority"] = level
        return func
    return decorator


class TestOrganizationManager:
    """Handles filtering and sorting of tests based on metadata."""

    @staticmethod
    def get_metadata(func: Callable) -> Dict[str, Any]:
        """Extract e2e metadata from a function."""
        return getattr(func, "_e2e_metadata", {
            "tags": set(),
            "depends_on": set(),
            "priority": Priority.MEDIUM
        })

    @staticmethod
    def filter_tests(
        modules: List[Any], 
        include_tags: Optional[Set[str]] = None, 
        exclude_tags: Optional[Set[str]] = None
    ) -> List[Any]:
        """Filter list of test modules based on tags.
        
        Args:
            modules: List of objects with a 'run_func' or similar
            include_tags: If provided, only include tests having at least ONE of these tags
            exclude_tags: If provided, exclude tests having at least ONE of these tags
        """
        filtered = []
        for mod in modules:
            # We assume mod has a 'run' attribute which is the function
            func = getattr(mod, "run", None)
            if not func:
                filtered.append(mod)
                continue

            metadata = TestOrganizationManager.get_metadata(func)
            tags = metadata.get("tags", set())

            # Exclude logic
            if exclude_tags and (tags & exclude_tags):
                continue
            
            # Include logic
            if include_tags and not (tags & include_tags):
                continue
                
            filtered.append(mod)
        
        return filtered

    @staticmethod
    def sort_tests(modules: List[Path], load_func: Callable[[Path], Optional[Callable]]) -> List[Path]:
        """Sort test modules by dependencies and priority.
        
        Uses a topological sort for dependencies, with priority as a secondary sort key.
        """
        # 1. Load functions and extract metadata
        metadata_map = {}
        for path in modules:
            func = load_func(path)
            if func:
                metadata_map[path.stem] = (path, TestOrganizationManager.get_metadata(func))
            else:
                metadata_map[path.stem] = (path, {
                    "tags": set(), 
                    "depends_on": set(), 
                    "priority": Priority.MEDIUM
                })

        # 2. Build adjacency list for topological sort
        adj = {name: [] for name in metadata_map}
        in_degree = {name: 0 for name in metadata_map}
        
        for name, (path, meta) in metadata_map.items():
            for dep in meta.get("depends_on", set()):
                if dep in metadata_map:
                    adj[dep].append(name)
                    in_degree[name] += 1
                # If dependency not found in current set, we just ignore it for sorting
                # (it might be a cross-service dependency handled elsewhere or just missing)

        # 3. Kahn's algorithm with priority-aware queue
        import heapq
        
        # We want higher priority (higher number) to go first among nodes with 0 in-degree.
        # heapq is a min-priority queue, so we use -priority.
        queue = []
        for name, degree in in_degree.items():
            if degree == 0:
                p = metadata_map[name][1].get("priority", Priority.MEDIUM)
                # (negative_priority, name)
                heapq.heappush(queue, (-int(p), name))

        sorted_paths = []
        while queue:
            p, name = heapq.heappop(queue)
            sorted_paths.append(metadata_map[name][0])
            
            for neighbor in adj[name]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    neighbor_p = metadata_map[neighbor][1].get("priority", Priority.MEDIUM)
                    heapq.heappush(queue, (-int(neighbor_p), neighbor))

        # If we have cycles or remaining items, just append them to avoid losing tests
        if len(sorted_paths) < len(modules):
            seen = {p.stem for p in sorted_paths}
            for path in modules:
                if path.stem not in seen:
                    sorted_paths.append(path)
                    
        return sorted_paths
