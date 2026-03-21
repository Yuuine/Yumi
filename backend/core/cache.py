"""
Memory Cache - 轻量级内存缓存层
使用 Python 内置机制实现，无外部依赖
"""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CacheEntry:
    value: Any
    expire_at: float | None = None

    def is_expired(self) -> bool:
        if self.expire_at is None:
            return False
        return time.time() > self.expire_at


class LRUCache:
    """线程安全的 LRU 缓存"""

    def __init__(self, max_size: int = 1000):
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._max_size = max_size
        self._lock = threading.RLock()

    def get(self, key: str) -> Any | None:
        with self._lock:
            if key not in self._cache:
                return None

            entry = self._cache[key]
            if entry.is_expired():
                del self._cache[key]
                return None

            self._cache.move_to_end(key)
            return entry.value

    def set(self, key: str, value: Any, ttl: float | None = None) -> None:
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            else:
                if len(self._cache) >= self._max_size:
                    self._cache.popitem(last=False)

            self._cache[key] = CacheEntry(value=value, expire_at=time.time() + ttl if ttl else None)

    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()

    def size(self) -> int:
        with self._lock:
            return len(self._cache)

    def cleanup_expired(self) -> int:
        """清理过期条目，返回清理数量"""
        with self._lock:
            expired_keys = [key for key, entry in self._cache.items() if entry.is_expired()]
            for key in expired_keys:
                del self._cache[key]
            return len(expired_keys)


class TTLCache:
    """基于时间的缓存，用于会话状态"""

    def __init__(self, default_ttl: float = 300.0):
        self._cache: dict[str, CacheEntry] = {}
        self._default_ttl = default_ttl
        self._lock = threading.RLock()

    def get(self, key: str) -> Any | None:
        with self._lock:
            if key not in self._cache:
                return None

            entry = self._cache[key]
            if entry.is_expired():
                del self._cache[key]
                return None

            return entry.value

    def set(self, key: str, value: Any, ttl: float | None = None) -> None:
        with self._lock:
            self._cache[key] = CacheEntry(
                value=value, expire_at=time.time() + (ttl or self._default_ttl)
            )

    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def touch(self, key: str, ttl: float | None = None) -> bool:
        """刷新 TTL"""
        with self._lock:
            if key not in self._cache:
                return False

            entry = self._cache[key]
            if entry.is_expired():
                del self._cache[key]
                return False

            entry.expire_at = time.time() + (ttl or self._default_ttl)
            return True

    def cleanup_expired(self) -> int:
        with self._lock:
            expired_keys = [key for key, entry in self._cache.items() if entry.is_expired()]
            for key in expired_keys:
                del self._cache[key]
            return len(expired_keys)


@dataclass
class ConversationContext:
    """对话上下文缓存"""

    user_id: str
    messages: list[dict[str, str]] = field(default_factory=list)
    last_update: float = field(default_factory=time.time)
    message_count: int = 0


class ConversationCache:
    """对话上下文缓存 - 管理热点用户的近期对话"""

    def __init__(self, max_users: int = 100, max_messages_per_user: int = 20):
        self._user_contexts: dict[str, ConversationContext] = {}
        self._max_users = max_users
        self._max_messages_per_user = max_messages_per_user
        self._lock = threading.RLock()
        self._access_order: list[str] = []

    def get_context(self, user_id: str) -> ConversationContext | None:
        with self._lock:
            if user_id not in self._user_contexts:
                return None

            ctx = self._user_contexts[user_id]
            if time.time() - ctx.last_update > 300:
                del self._user_contexts[user_id]
                if user_id in self._access_order:
                    self._access_order.remove(user_id)
                return None

            if user_id in self._access_order:
                self._access_order.remove(user_id)
            self._access_order.append(user_id)

            return ctx

    def add_message(self, user_id: str, role: str, content: str) -> None:
        with self._lock:
            if user_id not in self._user_contexts:
                if len(self._user_contexts) >= self._max_users:
                    oldest = self._access_order.pop(0)
                    del self._user_contexts[oldest]

                self._user_contexts[user_id] = ConversationContext(user_id=user_id)
                self._access_order.append(user_id)

            ctx = self._user_contexts[user_id]
            ctx.messages.append({"role": role, "content": content})
            ctx.message_count += 1
            ctx.last_update = time.time()

            if len(ctx.messages) > self._max_messages_per_user:
                ctx.messages = ctx.messages[-self._max_messages_per_user :]

    def clear_user(self, user_id: str) -> bool:
        with self._lock:
            if user_id in self._user_contexts:
                del self._user_contexts[user_id]
                if user_id in self._access_order:
                    self._access_order.remove(user_id)
                return True
            return False

    def get_recent_messages(self, user_id: str, limit: int = 8) -> list[dict[str, str]]:
        ctx = self.get_context(user_id)
        if not ctx:
            return []
        return ctx.messages[-limit:]


_conversation_cache: ConversationCache | None = None
_lru_cache: LRUCache | None = None
_ttl_cache: TTLCache | None = None


def get_conversation_cache() -> ConversationCache:
    global _conversation_cache
    if _conversation_cache is None:
        _conversation_cache = ConversationCache(max_users=100, max_messages_per_user=20)
    return _conversation_cache


def get_lru_cache() -> LRUCache:
    global _lru_cache
    if _lru_cache is None:
        _lru_cache = LRUCache(max_size=1000)
    return _lru_cache


def get_ttl_cache() -> TTLCache:
    global _ttl_cache
    if _ttl_cache is None:
        _ttl_cache = TTLCache(default_ttl=300.0)
    return _ttl_cache
