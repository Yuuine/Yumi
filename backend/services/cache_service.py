"""
缓存服务 - 带命中率统计的缓存层
为用户、角色卡、对话等数据提供缓存和统计功能
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any

from ..core import get_logger, log_with_context
from ..core.cache import LRUCache, TTLCache
import logging

logger = get_logger(__name__)


@dataclass
class CacheStats:
    """缓存统计数据"""

    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    evictions: int = 0
    created_at: float = field(default_factory=time.time)

    @property
    def total_requests(self) -> int:
        return self.hits + self.misses

    @property
    def hit_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.hits / self.total_requests

    def to_dict(self) -> dict[str, Any]:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "sets": self.sets,
            "deletes": self.deletes,
            "evictions": self.evictions,
            "total_requests": self.total_requests,
            "hit_rate": round(self.hit_rate * 100, 2),
            "created_at": self.created_at,
            "uptime_seconds": round(time.time() - self.created_at, 1),
        }


class TrackedLRUCache:
    """带统计的 LRU 缓存"""

    def __init__(self, name: str, max_size: int = 1000, default_ttl: float | None = None):
        self._name = name
        self._cache = LRUCache(max_size=max_size)
        self._default_ttl = default_ttl
        self._stats = CacheStats()
        self._lock = threading.RLock()

    def get(self, key: str) -> Any | None:
        with self._lock:
            value = self._cache.get(key)
            if value is not None:
                self._stats.hits += 1
                log_with_context(logger, logging.DEBUG, f"CacheService HIT: cache={self._name}, key={key}", cache=self._name, key=key)
            else:
                self._stats.misses += 1
                log_with_context(logger, logging.DEBUG, f"CacheService MISS: cache={self._name}, key={key}", cache=self._name, key=key)
            return value

    def set(self, key: str, value: Any, ttl: float | None = None) -> None:
        with self._lock:
            actual_ttl = ttl if ttl is not None else self._default_ttl
            old_size = self._cache.size()
            self._cache.set(key, value, actual_ttl)
            new_size = self._cache.size()
            self._stats.sets += 1
            if old_size == new_size and old_size > 0:
                self._stats.evictions += 1
                log_with_context(logger, logging.DEBUG, f"CacheService EVICT: cache={self._name}, key={key}", cache=self._name, key=key)
            log_with_context(logger, logging.DEBUG, f"CacheService SET: cache={self._name}, key={key}", cache=self._name, key=key)

    def delete(self, key: str) -> bool:
        with self._lock:
            result = self._cache.delete(key)
            if result:
                self._stats.deletes += 1
                log_with_context(logger, logging.DEBUG, f"CacheService DELETE: cache={self._name}, key={key}", cache=self._name, key=key)
            return result

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
            log_with_context(logger, logging.INFO, f"CacheService CLEAR: cache={self._name}", cache=self._name)

    def size(self) -> int:
        return self._cache.size()

    def get_stats(self) -> CacheStats:
        with self._lock:
            return CacheStats(**self._stats.__dict__)

    def reset_stats(self) -> None:
        with self._lock:
            self._stats = CacheStats()
            log_with_context(logger, logging.INFO, f"CacheService RESET_STATS: cache={self._name}", cache=self._name)


class TrackedTTLCache:
    """带统计的 TTL 缓存"""

    def __init__(self, name: str, default_ttl: float = 300.0):
        self._name = name
        self._cache = TTLCache(default_ttl=default_ttl)
        self._stats = CacheStats()
        self._lock = threading.RLock()

    def get(self, key: str) -> Any | None:
        with self._lock:
            value = self._cache.get(key)
            if value is not None:
                self._stats.hits += 1
            else:
                self._stats.misses += 1
            return value

    def set(self, key: str, value: Any, ttl: float | None = None) -> None:
        with self._lock:
            self._cache.set(key, value, ttl)
            self._stats.sets += 1

    def delete(self, key: str) -> bool:
        with self._lock:
            result = self._cache.delete(key)
            if result:
                self._stats.deletes += 1
            return result

    def touch(self, key: str, ttl: float | None = None) -> bool:
        return self._cache.touch(key, ttl)

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()

    def get_stats(self) -> CacheStats:
        with self._lock:
            return CacheStats(**self._stats.__dict__)

    def reset_stats(self) -> None:
        with self._lock:
            self._stats = CacheStats()


class CacheService:
    """统一缓存服务"""

    _instance: CacheService | None = None
    _lock = threading.RLock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True

        # 各个缓存实例
        self._user_cache = TrackedLRUCache("user", max_size=100, default_ttl=300.0)
        self._character_cache = TrackedLRUCache("character", max_size=200, default_ttl=600.0)
        self._character_list_cache = TrackedLRUCache(
            "character_list", max_size=100, default_ttl=120.0
        )
        self._conversation_cache = TrackedLRUCache("conversation", max_size=100, default_ttl=120.0)
        self._conversation_list_cache = TrackedLRUCache(
            "conversation_list", max_size=100, default_ttl=60.0
        )
        self._message_cache = TrackedLRUCache("message", max_size=500, default_ttl=60.0)
        self._settings_cache = TrackedLRUCache("settings", max_size=10, default_ttl=300.0)

        self._caches: dict[str, TrackedLRUCache | TrackedTTLCache] = {
            "user": self._user_cache,
            "character": self._character_cache,
            "character_list": self._character_list_cache,
            "conversation": self._conversation_cache,
            "conversation_list": self._conversation_list_cache,
            "message": self._message_cache,
            "settings": self._settings_cache,
        }

        log_with_context(logger, logging.INFO, "CacheService Initialized")

    @property
    def user(self) -> TrackedLRUCache:
        return self._user_cache

    @property
    def character(self) -> TrackedLRUCache:
        return self._character_cache

    @property
    def character_list(self) -> TrackedLRUCache:
        return self._character_list_cache

    @property
    def conversation(self) -> TrackedLRUCache:
        return self._conversation_cache

    @property
    def conversation_list(self) -> TrackedLRUCache:
        return self._conversation_list_cache

    @property
    def message(self) -> TrackedLRUCache:
        return self._message_cache

    @property
    def settings(self) -> TrackedLRUCache:
        return self._settings_cache

    def get_cache(self, name: str) -> TrackedLRUCache | TrackedTTLCache | None:
        return self._caches.get(name)

    def get_all_stats(self) -> dict[str, dict[str, Any]]:
        return {name: cache.get_stats().to_dict() for name, cache in self._caches.items()}

    def reset_all_stats(self) -> None:
        for cache in self._caches.values():
            cache.reset_stats()
        log_with_context(logger, logging.INFO, "CacheService All stats reset")

    def invalidate_user(self, user_id: str) -> None:
        """失效用户相关的所有缓存"""
        self._user_cache.delete(f"user:{user_id}")
        self._character_list_cache.delete(f"chars:{user_id}")
        self._conversation_list_cache.delete(f"convs:{user_id}")
        log_with_context(logger, logging.DEBUG, f"CacheService Invalidate user: user_id={user_id}", user_id=user_id)

    def invalidate_character(self, user_id: str, char_id: str) -> None:
        """失效角色卡相关缓存"""
        self._character_cache.delete(f"char:{user_id}:{char_id}")
        self._character_list_cache.delete(f"chars:{user_id}")
        log_with_context(
            logger, logging.DEBUG, f"CacheService Invalidate character: user_id={user_id}, char_id={char_id}", 
            user_id=user_id, char_id=char_id
        )

    def invalidate_conversation(self, user_id: str, conv_id: str) -> None:
        """失效对话相关缓存"""
        self._conversation_cache.delete(f"conv:{user_id}:{conv_id}")
        self._conversation_list_cache.delete(f"convs:{user_id}")
        self._message_cache.delete(f"msgs:{user_id}:{conv_id}")
        log_with_context(
            logger, logging.DEBUG, f"CacheService Invalidate conversation: user_id={user_id}, conv_id={conv_id}", 
            user_id=user_id, conv_id=conv_id
        )


_cache_service: CacheService | None = None


def get_cache_service() -> CacheService:
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service
