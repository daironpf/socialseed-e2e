"""Response caching for API test optimization.

This module provides response caching for GET requests to reduce
redundant API calls during test execution.
"""

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry for API responses."""

    key: str
    response_data: Dict[str, Any]
    timestamp: float
    ttl: float = 3600  # Default 1 hour TTL

    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        return time.time() - self.timestamp > self.ttl


@dataclass
class CacheConfig:
    """Configuration for response caching."""

    enabled: bool = False
    cache_dir: str = ".e2e/cache"
    default_ttl: float = 3600  # 1 hour
    max_entries: int = 1000
    cache_get_only: bool = True  # Only cache GET requests


class ResponseCache:
    """In-memory response cache for API requests."""

    def __init__(self, config: Optional[CacheConfig] = None):
        """Initialize the response cache.

        Args:
            config: Cache configuration. If None, uses defaults.
        """
        self.config = config or CacheConfig()
        self._cache: Dict[str, CacheEntry] = {}
        self._hits: int = 0
        self._misses: int = 0

    def _generate_key(
        self,
        method: str,
        url: str,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
    ) -> str:
        """Generate a cache key from request parameters.

        Args:
            method: HTTP method
            url: Request URL
            params: Query parameters
            headers: Request headers

        Returns:
            Cache key string
        """
        key_data = {
            "method": method.upper(),
            "url": url,
            "params": params or {},
            "headers": headers or {},
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_string.encode()).hexdigest()

    def get(
        self,
        method: str,
        url: str,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get a cached response.

        Args:
            method: HTTP method
            url: Request URL
            params: Query parameters
            headers: Request headers

        Returns:
            Cached response data or None if not found/expired
        """
        if not self.config.enabled:
            return None

        # Only cache GET requests by default
        if self.config.cache_get_only and method.upper() != "GET":
            return None

        key = self._generate_key(method, url, params, headers)

        if key in self._cache:
            entry = self._cache[key]
            if not entry.is_expired():
                self._hits += 1
                logger.debug(f"Cache HIT: {method} {url}")
                return entry.response_data
            else:
                # Remove expired entry
                del self._cache[key]

        self._misses += 1
        logger.debug(f"Cache MISS: {method} {url}")
        return None

    def set(
        self,
        method: str,
        url: str,
        response_data: Dict[str, Any],
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        ttl: Optional[float] = None,
    ) -> None:
        """Store a response in the cache.

        Args:
            method: HTTP method
            url: Request URL
            response_data: Response data to cache
            params: Query parameters
            headers: Request headers
            ttl: Time to live in seconds
        """
        if not self.config.enabled:
            return

        # Only cache GET requests by default
        if self.config.cache_get_only and method.upper() != "GET":
            return

        # Evict oldest entries if cache is full
        if len(self._cache) >= self.config.max_entries:
            self._evict_oldest()

        key = self._generate_key(method, url, params, headers)
        ttl = ttl or self.config.default_ttl

        self._cache[key] = CacheEntry(
            key=key,
            response_data=response_data,
            timestamp=time.time(),
            ttl=ttl,
        )

        logger.debug(f"Cache SET: {method} {url}")

    def _evict_oldest(self) -> None:
        """Evict the oldest cache entry."""
        if not self._cache:
            return

        oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k].timestamp)
        del self._cache[oldest_key]
        logger.debug(f"Evicted oldest cache entry: {oldest_key[:16]}...")

    def invalidate(self, url: Optional[str] = None) -> int:
        """Invalidate cache entries.

        Args:
            url: If provided, only invalidate entries for this URL.
                 If None, clear entire cache.

        Returns:
            Number of entries invalidated
        """
        if url is None:
            count = len(self._cache)
            self._cache.clear()
            return count

        # Find and remove entries for specific URL
        keys_to_remove = [
            k for k, v in self._cache.items() if v.response_data.get("url") == url
        ]
        for key in keys_to_remove:
            del self._cache[key]

        return len(keys_to_remove)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "enabled": self.config.enabled,
            "entries": len(self._cache),
            "max_entries": self.config.max_entries,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{hit_rate:.1f}%",
        }

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0


class FileCache:
    """File-based cache for persisting responses across test runs."""

    def __init__(self, cache_dir: str = ".e2e/cache"):
        """Initialize file-based cache.

        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, key: str) -> Path:
        """Get the file path for a cache key."""
        return self.cache_dir / f"{key}.json"

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get a cached response from file.

        Args:
            key: Cache key

        Returns:
            Cached response data or None
        """
        cache_path = self._get_cache_path(key)
        if not cache_path.exists():
            return None

        try:
            with open(cache_path) as f:
                data = json.load(f)

            # Check if expired
            if time.time() - data.get("timestamp", 0) > data.get("ttl", 3600):
                cache_path.unlink()
                return None

            return data.get("response")
        except (json.JSONDecodeError, IOError):
            return None

    def set(
        self,
        key: str,
        response: Dict[str, Any],
        ttl: float = 3600,
    ) -> None:
        """Store a response in file cache.

        Args:
            key: Cache key
            response: Response data to cache
            ttl: Time to live in seconds
        """
        cache_path = self._get_cache_path(key)
        data = {
            "timestamp": time.time(),
            "ttl": ttl,
            "response": response,
        }

        try:
            with open(cache_path, "w") as f:
                json.dump(data, f)
        except IOError as e:
            logger.warning(f"Failed to write cache file: {e}")

    def clear(self) -> None:
        """Clear all cached files."""
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()


# Global cache instance
_global_cache: Optional[ResponseCache] = None


def get_cache(config: Optional[CacheConfig] = None) -> ResponseCache:
    """Get the global response cache instance.

    Args:
        config: Cache configuration. Uses existing if None.

    Returns:
        Global ResponseCache instance
    """
    global _global_cache

    if _global_cache is None:
        _global_cache = ResponseCache(config)

    return _global_cache


def reset_cache() -> None:
    """Reset the global cache."""
    global _global_cache
    _global_cache = None


__all__ = [
    "CacheConfig",
    "CacheEntry",
    "ResponseCache",
    "FileCache",
    "get_cache",
    "reset_cache",
]
