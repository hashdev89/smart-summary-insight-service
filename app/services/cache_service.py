"""Caching service for request deduplication and performance."""
from typing import Optional, Any
from cachetools import TTLCache
import hashlib
import json
from app.config import settings


class CacheService:
    """Simple in-memory cache with TTL for request deduplication."""
    
    def __init__(self):
        """Initialize cache with TTL from settings."""
        self.cache: TTLCache[str, Any] = TTLCache(
            maxsize=1000,
            ttl=settings.cache_ttl_seconds
        )
        self.enabled = settings.enable_cache
    
    def _generate_key(self, structured_data: Optional[dict], notes: list) -> str:
        """
        Generate a cache key from request data.
        Uses deterministic hashing for deduplication.
        """
        # Normalize data for consistent hashing
        cache_data = {
            "structured_data": structured_data or {},
            "notes": sorted(notes) if isinstance(notes, list) else [notes]
        }
        
        # Create deterministic JSON string
        cache_str = json.dumps(cache_data, sort_keys=True, ensure_ascii=False)
        
        # Hash for shorter key
        return hashlib.sha256(cache_str.encode()).hexdigest()
    
    def get(self, structured_data: Optional[dict], notes: list) -> Optional[Any]:
        """Retrieve cached response if available."""
        if not self.enabled:
            return None
        
        key = self._generate_key(structured_data, notes)
        return self.cache.get(key)
    
    def set(self, structured_data: Optional[dict], notes: list, value: Any) -> None:
        """Store response in cache."""
        if not self.enabled:
            return
        
        key = self._generate_key(structured_data, notes)
        self.cache[key] = value
    
    def clear(self) -> None:
        """Clear all cached entries."""
        self.cache.clear()


# Global cache instance
cache_service = CacheService()

