"""Cache management for classification results with optimized serialization."""

import hashlib
import json
import pickle
import time
from pathlib import Path
from typing import Any, Dict, Optional

# Try to import msgpack for faster serialization (3-5x faster than JSON)
try:
    import msgpack
    HAS_MSGPACK = True
except ImportError:
    HAS_MSGPACK = False

from .exceptions import CacheError
from .logger import get_logger

logger = get_logger()


class CacheManager:
    """Manages caching of classification results with optimized serialization."""

    def __init__(
        self,
        cache_dir: str = ".cache",
        ttl_hours: int = 24,
        enabled: bool = True,
        use_binary: bool = True
    ):
        """
        Initialize the cache manager.

        Args:
            cache_dir: Directory to store cache files
            ttl_hours: Time-to-live for cache entries in hours
            enabled: Whether caching is enabled
            use_binary: Use binary serialization (msgpack/pickle) instead of JSON (3-5x faster)
        """
        self.cache_dir = Path(cache_dir)
        self.ttl_seconds = ttl_hours * 3600
        self.enabled = enabled
        self.use_binary = use_binary and (HAS_MSGPACK or True)  # Always available (pickle fallback)
        self.memory_cache: Dict[str, Dict[str, Any]] = {}

        # Determine serialization format
        if self.use_binary:
            if HAS_MSGPACK:
                self.format = 'msgpack'
                self.file_ext = '.msgpack'
                logger.debug("Using msgpack serialization for cache (3-5x faster than JSON)")
            else:
                self.format = 'pickle'
                self.file_ext = '.pkl'
                logger.debug("Using pickle serialization for cache (msgpack not available)")
        else:
            self.format = 'json'
            self.file_ext = '.json'
            logger.debug("Using JSON serialization for cache")

        if self.enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Cache initialized at {self.cache_dir}")

    def get_cache_key(self, file_path: str, file_size: int, modified_time: float) -> str:
        """
        Generate a cache key from file characteristics using MD5 (faster than SHA256).

        Args:
            file_path: Path to the file
            file_size: File size in bytes
            modified_time: File modification timestamp

        Returns:
            Cache key (MD5 hash - 2x faster than SHA256)
        """
        data = f"{file_path}:{file_size}:{modified_time}"
        # Use MD5 for cache keys (speed matters more than collision resistance for cache)
        return hashlib.md5(data.encode()).hexdigest()

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

        # Check disk cache (try all formats for backward compatibility)
        cache_file = self.cache_dir / f"{key}{self.file_ext}"

        # Try current format first
        if cache_file.exists():
            entry = self._read_cache_file(cache_file)
            if entry and self._is_valid(entry):
                # Store in memory cache for faster access
                self.memory_cache[key] = entry
                logger.debug(f"Cache hit (disk): {key[:8]}...")
                return entry['data']
            elif entry:
                # Remove expired cache file
                cache_file.unlink()
                logger.debug(f"Cache expired: {key[:8]}...")

        # Try fallback formats for backward compatibility
        if not cache_file.exists():
            for fallback_ext in ['.json', '.msgpack', '.pkl']:
                if fallback_ext == self.file_ext:
                    continue
                fallback_file = self.cache_dir / f"{key}{fallback_ext}"
                if fallback_file.exists():
                    entry = self._read_cache_file(fallback_file)
                    if entry and self._is_valid(entry):
                        self.memory_cache[key] = entry
                        logger.debug(f"Cache hit (disk, {fallback_ext}): {key[:8]}...")
                        return entry['data']

        return None

    def _read_cache_file(self, cache_file: Path) -> Optional[Dict[str, Any]]:
        """
        Read cache file with appropriate deserializer.

        Args:
            cache_file: Path to cache file

        Returns:
            Cache entry or None if failed
        """
        try:
            ext = cache_file.suffix

            if ext == '.json':
                with open(cache_file, 'r') as f:
                    return json.load(f)

            elif ext == '.msgpack':
                with open(cache_file, 'rb') as f:
                    return msgpack.unpack(f, raw=False)

            elif ext == '.pkl':
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)

            else:
                logger.warning(f"Unknown cache file format: {ext}")
                return None

        except Exception as e:
            logger.warning(f"Failed to read cache file {cache_file}: {e}")
            # Remove corrupted cache file
            try:
                cache_file.unlink()
            except:
                pass
            return None

    def set(self, key: str, data: Dict[str, Any]) -> None:
        """
        Store classification result in cache using optimized serialization.

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

        # Store on disk with appropriate serializer
        cache_file = self.cache_dir / f"{key}{self.file_ext}"
        try:
            if self.format == 'json':
                with open(cache_file, 'w') as f:
                    json.dump(entry, f, indent=2)

            elif self.format == 'msgpack':
                with open(cache_file, 'wb') as f:
                    msgpack.pack(entry, f)

            elif self.format == 'pickle':
                with open(cache_file, 'wb') as f:
                    pickle.dump(entry, f, protocol=pickle.HIGHEST_PROTOCOL)

            logger.debug(f"Cached ({self.format}): {key[:8]}...")

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
        """Clear all cache entries (all formats)."""
        if not self.enabled:
            return

        # Clear memory cache
        self.memory_cache.clear()

        # Clear disk cache (all formats)
        try:
            for ext in ['*.json', '*.msgpack', '*.pkl']:
                for cache_file in self.cache_dir.glob(ext):
                    cache_file.unlink()
            logger.info("Cache cleared")
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics for all formats.

        Returns:
            Dictionary with cache statistics
        """
        if not self.enabled:
            return {
                'enabled': False,
                'format': self.format,
                'memory_entries': 0,
                'disk_entries': 0,
                'total_size_mb': 0
            }

        # Count entries for all formats
        disk_entries = 0
        total_size = 0
        format_breakdown = {}

        for ext in ['*.json', '*.msgpack', '*.pkl']:
            files = list(self.cache_dir.glob(ext))
            count = len(files)
            size = sum(f.stat().st_size for f in files)

            disk_entries += count
            total_size += size

            if count > 0:
                format_name = ext[2:]  # Remove '*.'
                format_breakdown[format_name] = {
                    'count': count,
                    'size_mb': size / (1024 * 1024)
                }

        return {
            'enabled': True,
            'format': self.format,
            'memory_entries': len(self.memory_cache),
            'disk_entries': disk_entries,
            'total_size_mb': total_size / (1024 * 1024),
            'ttl_hours': self.ttl_seconds / 3600,
            'format_breakdown': format_breakdown
        }
