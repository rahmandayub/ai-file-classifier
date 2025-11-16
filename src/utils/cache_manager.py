"""Cache management for classification results."""

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

from .exceptions import CacheError
from .logger import get_logger

logger = get_logger()


class CacheManager:
    """Manages caching of classification results."""

    def __init__(
        self,
        cache_dir: str = ".cache",
        ttl_hours: int = 24,
        enabled: bool = True
    ):
        """
        Initialize the cache manager.

        Args:
            cache_dir: Directory to store cache files
            ttl_hours: Time-to-live for cache entries in hours
            enabled: Whether caching is enabled
        """
        self.cache_dir = Path(cache_dir)
        self.ttl_seconds = ttl_hours * 3600
        self.enabled = enabled
        self.memory_cache: Dict[str, Dict[str, Any]] = {}

        if self.enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Cache initialized at {self.cache_dir}")

    def get_cache_key(self, file_path: str, file_size: int, modified_time: float) -> str:
        """
        Generate a cache key from file characteristics.

        Args:
            file_path: Path to the file
            file_size: File size in bytes
            modified_time: File modification timestamp

        Returns:
            Cache key (SHA256 hash)
        """
        data = f"{file_path}:{file_size}:{modified_time}"
        return hashlib.sha256(data.encode()).hexdigest()

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached classification result.

        Args:
            key: Cache key

        Returns:
            Cached data or None if not found or expired
        """
        if not self.enabled:
            return None

        # Check memory cache first
        if key in self.memory_cache:
            entry = self.memory_cache[key]
            if self._is_valid(entry):
                logger.debug(f"Cache hit (memory): {key[:8]}...")
                return entry['data']
            else:
                # Remove expired entry
                del self.memory_cache[key]

        # Check disk cache
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    entry = json.load(f)

                if self._is_valid(entry):
                    # Store in memory cache for faster access
                    self.memory_cache[key] = entry
                    logger.debug(f"Cache hit (disk): {key[:8]}...")
                    return entry['data']
                else:
                    # Remove expired cache file
                    cache_file.unlink()
                    logger.debug(f"Cache expired: {key[:8]}...")

            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to read cache file: {e}")
                # Remove corrupted cache file
                try:
                    cache_file.unlink()
                except:
                    pass

        return None

    def set(self, key: str, data: Dict[str, Any]) -> None:
        """
        Store classification result in cache.

        Args:
            key: Cache key
            data: Data to cache
        """
        if not self.enabled:
            return

        entry = {
            'timestamp': time.time(),
            'data': data
        }

        # Store in memory cache
        self.memory_cache[key] = entry

        # Store on disk
        cache_file = self.cache_dir / f"{key}.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump(entry, f, indent=2)
            logger.debug(f"Cached: {key[:8]}...")
        except IOError as e:
            logger.warning(f"Failed to write cache file: {e}")

    def _is_valid(self, entry: Dict[str, Any]) -> bool:
        """
        Check if cache entry is still valid.

        Args:
            entry: Cache entry with timestamp and data

        Returns:
            True if valid, False if expired
        """
        if 'timestamp' not in entry:
            return False

        age = time.time() - entry['timestamp']
        return age < self.ttl_seconds

    def clear(self) -> None:
        """Clear all cache entries."""
        if not self.enabled:
            return

        # Clear memory cache
        self.memory_cache.clear()

        # Clear disk cache
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
            logger.info("Cache cleared")
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        if not self.enabled:
            return {
                'enabled': False,
                'memory_entries': 0,
                'disk_entries': 0,
                'total_size_mb': 0
            }

        disk_entries = len(list(self.cache_dir.glob("*.json")))
        total_size = sum(f.stat().st_size for f in self.cache_dir.glob("*.json"))

        return {
            'enabled': True,
            'memory_entries': len(self.memory_cache),
            'disk_entries': disk_entries,
            'total_size_mb': total_size / (1024 * 1024),
            'ttl_hours': self.ttl_seconds / 3600
        }
