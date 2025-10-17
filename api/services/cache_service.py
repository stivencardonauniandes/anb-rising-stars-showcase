"""
Redis cache service for caching rankings and other data
"""
import redis
import json
import os
from typing import Optional, Any, Dict, List
import logging

logger = logging.getLogger(__name__)

class CacheService:
    def __init__(self):
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            self.redis_client.ping()
            logger.info("✅ Redis connection established")
        except Exception as e:
            logger.warning(f"❌ Redis connection failed: {e}")
            self.redis_client = None
    
    def _is_available(self) -> bool:
        """Check if Redis is available"""
        return self.redis_client is not None
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self._is_available():
            return None
            
        try:
            value = self.redis_client.get(key)
            if value is None:
                return None
            return json.loads(value)
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, expire: int = 300) -> bool:
        """Set value in cache with expiration (default 5 minutes)"""
        if not self._is_available():
            return False
            
        try:
            serialized_value = json.dumps(value, default=str)
            return self.redis_client.setex(key, expire, serialized_value)
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self._is_available():
            return False
            
        try:
            return self.redis_client.delete(key) > 0
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        if not self._is_available():
            return 0
            
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache delete pattern error for pattern {pattern}: {e}")
            return 0
    
    def generate_rankings_key(self, page: int, limit: int, sort_by: str = "votes") -> str:
        """Generate cache key for rankings"""
        return f"rankings:{sort_by}:page:{page}:limit:{limit}"
    
    def invalidate_rankings_cache(self):
        """Invalidate all rankings cache"""
        pattern = "rankings:*"
        deleted = self.delete_pattern(pattern)
        logger.info(f"Invalidated {deleted} rankings cache entries")
        return deleted

# Global cache instance
cache_service = CacheService()
