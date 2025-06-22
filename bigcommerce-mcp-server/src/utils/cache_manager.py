"""Cache manager for BigCommerce MCP Server"""

import asyncio
import json
import time
from typing import Any, Dict, Optional, Callable
from functools import wraps
import hashlib
import logging

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages caching for API responses and search results"""
    
    def __init__(self, default_ttl: int = 3600):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        self._lock = asyncio.Lock()
    
    def _generate_key(self, prefix: str, params: Dict[str, Any]) -> str:
        """Generate a cache key from prefix and parameters"""
        # Sort params for consistent key generation
        sorted_params = json.dumps(params, sort_keys=True)
        hash_value = hashlib.md5(sorted_params.encode()).hexdigest()
        return f"{prefix}:{hash_value}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        async with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if time.time() < entry['expires_at']:
                    logger.debug(f"Cache hit for key: {key}")
                    return entry['value']
                else:
                    # Remove expired entry
                    del self._cache[key]
                    logger.debug(f"Cache expired for key: {key}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with TTL"""
        if ttl is None:
            ttl = self.default_ttl
        
        async with self._lock:
            self._cache[key] = {
                'value': value,
                'expires_at': time.time() + ttl,
                'created_at': time.time()
            }
            logger.debug(f"Cache set for key: {key} with TTL: {ttl}s")
    
    async def invalidate(self, pattern: Optional[str] = None) -> None:
        """Invalidate cache entries matching pattern or all entries"""
        async with self._lock:
            if pattern is None:
                self._cache.clear()
                logger.info("Cache cleared")
            else:
                keys_to_remove = [
                    key for key in self._cache.keys()
                    if pattern in key
                ]
                for key in keys_to_remove:
                    del self._cache[key]
                logger.info(f"Invalidated {len(keys_to_remove)} cache entries matching '{pattern}'")
    
    def cache_key(self, prefix: str):
        """Decorator for caching async function results"""
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate cache key from function arguments
                cache_params = {
                    'args': args[1:] if args else [],  # Skip self
                    'kwargs': kwargs
                }
                key = self._generate_key(prefix, cache_params)
                
                # Check cache first
                cached_value = await self.get(key)
                if cached_value is not None:
                    return cached_value
                
                # Call function and cache result
                result = await func(*args, **kwargs)
                await self.set(key, result)
                return result
            
            return wrapper
        return decorator
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_entries = len(self._cache)
        expired_entries = sum(
            1 for entry in self._cache.values()
            if time.time() >= entry['expires_at']
        )
        
        return {
            'total_entries': total_entries,
            'active_entries': total_entries - expired_entries,
            'expired_entries': expired_entries,
            'cache_keys': list(self._cache.keys())[:10]  # First 10 keys
        }