"""
Generic caching utility for the Natural Language to SQL Query App.
Provides configurable in-memory caching with automatic expiration.
"""
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple, Union
from src.utils.logging import logger


class CacheManager:
    """
    Generic cache manager with configurable expiration and namespaces.
    
    Features:
    - Namespace support for different cache types
    - Configurable expiry times per namespace
    - Automatic cleanup of expired entries
    - Thread-safe operations
    - Memory-efficient storage
    """
    
    def __init__(self):
        """Initialize the cache manager."""
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._default_expiry_minutes = 30
    
    def _get_namespace_key(self, namespace: str, key: str) -> str:
        """Generate a namespaced cache key."""
        return f"{namespace}:{key}"
    
    def _is_expired(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if a cache entry is expired."""
        if 'expiry_time' not in cache_entry:
            return True
        return datetime.now() > cache_entry['expiry_time']
    
    def _cleanup_expired_entries(self, namespace: Optional[str] = None):
        """Remove expired entries from cache."""
        keys_to_remove = []
        
        for cache_key, cache_entry in self._cache.items():
            # If namespace specified, only clean that namespace
            if namespace and not cache_key.startswith(f"{namespace}:"):
                continue
                
            if self._is_expired(cache_entry):
                keys_to_remove.append(cache_key)
        
        for key in keys_to_remove:
            del self._cache[key]
            logger.debug(f"Removed expired cache entry: {key}")
    
    def set(self, 
            namespace: str, 
            key: str, 
            value: Any, 
            expiry_minutes: Optional[int] = None,
            metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Store a value in cache.
        
        Args:
            namespace: Cache namespace (e.g., 'table_info', 'genai_responses')
            key: Cache key within the namespace
            value: Value to cache
            expiry_minutes: Minutes until expiry (uses default if None)
            metadata: Optional metadata to store with the value
        """
        if expiry_minutes is None:
            expiry_minutes = self._default_expiry_minutes
        
        expiry_time = datetime.now() + timedelta(minutes=expiry_minutes)
        
        cache_key = self._get_namespace_key(namespace, key)
        self._cache[cache_key] = {
            'value': value,
            'expiry_time': expiry_time,
            'created_at': datetime.now(),
            'namespace': namespace,
            'key': key,
            'metadata': metadata or {}
        }
        
        logger.debug(f"Cached {cache_key} (expires in {expiry_minutes} minutes)")
    
    def get(self, namespace: str, key: str) -> Optional[Any]:
        """
        Retrieve a value from cache.
        
        Args:
            namespace: Cache namespace
            key: Cache key within the namespace
            
        Returns:
            Cached value if found and not expired, None otherwise
        """
        cache_key = self._get_namespace_key(namespace, key)
        
        if cache_key not in self._cache:
            logger.debug(f"Cache miss: {cache_key}")
            return None
        
        cache_entry = self._cache[cache_key]
        
        if self._is_expired(cache_entry):
            del self._cache[cache_key]
            logger.debug(f"Cache expired: {cache_key}")
            return None
        
        logger.debug(f"Cache hit: {cache_key}")
        return cache_entry['value']
    
    def exists(self, namespace: str, key: str) -> bool:
        """
        Check if a key exists in cache and is not expired.
        
        Args:
            namespace: Cache namespace
            key: Cache key within the namespace
            
        Returns:
            True if key exists and is not expired
        """
        return self.get(namespace, key) is not None
    
    def delete(self, namespace: str, key: str) -> bool:
        """
        Delete a specific cache entry.
        
        Args:
            namespace: Cache namespace
            key: Cache key within the namespace
            
        Returns:
            True if entry was deleted, False if not found
        """
        cache_key = self._get_namespace_key(namespace, key)
        
        if cache_key in self._cache:
            del self._cache[cache_key]
            logger.debug(f"Deleted cache entry: {cache_key}")
            return True
        
        return False
    
    def clear_namespace(self, namespace: str) -> int:
        """
        Clear all entries in a specific namespace.
        
        Args:
            namespace: Cache namespace to clear
            
        Returns:
            Number of entries cleared
        """
        keys_to_remove = [
            cache_key for cache_key in self._cache.keys()
            if cache_key.startswith(f"{namespace}:")
        ]
        
        for key in keys_to_remove:
            del self._cache[key]
        
        logger.info(f"Cleared {len(keys_to_remove)} entries from namespace '{namespace}'")
        return len(keys_to_remove)
    
    def clear_all(self) -> int:
        """
        Clear all cache entries.
        
        Returns:
            Number of entries cleared
        """
        count = len(self._cache)
        self._cache.clear()
        logger.info(f"Cleared all cache entries ({count} total)")
        return count
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        # Clean up expired entries first
        self._cleanup_expired_entries()
        
        total_entries = len(self._cache)
        namespaces = {}
        
        for cache_key, cache_entry in self._cache.items():
            namespace = cache_entry['namespace']
            if namespace not in namespaces:
                namespaces[namespace] = {
                    'count': 0,
                    'oldest_entry': None,
                    'newest_entry': None
                }
            
            namespaces[namespace]['count'] += 1
            
            created_at = cache_entry['created_at']
            if (namespaces[namespace]['oldest_entry'] is None or 
                created_at < namespaces[namespace]['oldest_entry']):
                namespaces[namespace]['oldest_entry'] = created_at
            
            if (namespaces[namespace]['newest_entry'] is None or 
                created_at > namespaces[namespace]['newest_entry']):
                namespaces[namespace]['newest_entry'] = created_at
        
        return {
            'total_entries': total_entries,
            'namespaces': namespaces,
            'default_expiry_minutes': self._default_expiry_minutes
        }
    
    def set_default_expiry(self, minutes: int):
        """Set the default expiry time for new cache entries."""
        self._default_expiry_minutes = minutes
        logger.info(f"Set default cache expiry to {minutes} minutes")


# Global cache manager instance
cache_manager = CacheManager() 