"""
Redis缓存层 - 用于热门选题和LLM响应缓存
如果Redis不可用，自动降级为内存缓存
"""
import json
import time
from typing import Optional, Any
from datetime import timedelta

class MemoryCache:
    """内存缓存（Redis不可用时的降级方案）"""
    def __init__(self):
        self._cache: dict = {}

    def get(self, key: str) -> Optional[Any]:
        item = self._cache.get(key)
        if item and item["expire"] > time.time():
            return json.loads(item["value"])
        return None

    def set(self, key: str, value: Any, expire_seconds: int = 3600):
        self._cache[key] = {
            "value": json.dumps(value, ensure_ascii=False),
            "expire": time.time() + expire_seconds
        }

    def delete(self, key: str):
        self._cache.pop(key, None)

    def exists(self, key: str) -> bool:
        item = self._cache.get(key)
        return item is not None and item["expire"] > time.time()


class CacheManager:
    """缓存管理器 - 自动选择Redis或内存缓存"""

    def __init__(self):
        self._redis = None
        self._memory = MemoryCache()
        self._use_redis = False
        self._try_connect_redis()

    def _try_connect_redis(self):
        """尝试连接Redis"""
        try:
            import redis
            import os
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            self._redis = redis.from_url(redis_url, decode_responses=True)
            self._redis.ping()
            self._use_redis = True
        except Exception:
            self._use_redis = False

    @property
    def is_redis_available(self) -> bool:
        return self._use_redis

    def get(self, key: str) -> Optional[Any]:
        if self._use_redis and self._redis:
            try:
                value = self._redis.get(key)
                return json.loads(value) if value else None
            except Exception:
                pass
        return self._memory.get(key)

    def set(self, key: str, value: Any, expire_seconds: int = 3600):
        if self._use_redis and self._redis:
            try:
                self._redis.setex(key, expire_seconds, json.dumps(value, ensure_ascii=False))
                return
            except Exception:
                pass
        self._memory.set(key, value, expire_seconds)

    def delete(self, key: str):
        if self._use_redis and self._redis:
            try:
                self._redis.delete(key)
            except Exception:
                pass
        self._memory.delete(key)

    def get_stats(self) -> Dict:
        return {
            "backend": "redis" if self._use_redis else "memory",
            "redis_available": self._use_redis
        }


# 缓存Key前缀
CACHE_PREFIX = "grad_assistant:"

# 缓存过期时间
TOPIC_CACHE_TTL = 3600       # 选题缓存1小时
ANALYSIS_CACHE_TTL = 1800    # 分析缓存30分钟
LLM_CACHE_TTL = 600          # LLM响应缓存10分钟

# 全局实例
_cache_manager: Optional[CacheManager] = None

def get_cache() -> CacheManager:
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager
