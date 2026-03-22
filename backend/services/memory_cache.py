"""
Cached Memory Engine - 优化的记忆引擎
使用内存缓存减少 ChromaDB 查询频率
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from ..core import get_logger, get_lru_cache
from .memory import MemoryEngine

logger = get_logger(__name__)


class CachedMemoryEngine:
    """带缓存的记忆引擎，减少 ChromaDB 查询"""

    def __init__(self, memory_engine: MemoryEngine):
        self._engine = memory_engine
        self._cache = get_lru_cache()
        self._cache_ttl = 300.0

    async def initialize(self) -> None:
        await self._engine.initialize()

    async def store(
        self,
        user_id: str,
        content: str,
        metadata: dict[str, Any] | None = None,
        skip_dedup: bool = False,
    ) -> str | None:
        cache_key = f"search:{user_id}:{hash(content[:100])}"
        self._cache.delete(cache_key)

        recent_cache_key = f"recent:{user_id}"
        self._cache.delete(recent_cache_key)

        return await self._engine.store(user_id, content, metadata, skip_dedup)

    async def search(
        self,
        query: str,
        top_k: int | None = None,
        user_id: str | None = None,
        apply_decay: bool = True,
    ) -> list[dict[str, Any]]:
        if not user_id:
            return await self._engine.search(query, top_k, user_id, apply_decay)

        cache_key = f"search:{user_id}:{hash(query[:100])}:{top_k}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            logger.debug("Cache hit for search: %s", cache_key)
            return cached

        results = await self._engine.search(query, top_k, user_id, apply_decay)
        self._cache.set(cache_key, results, ttl=self._cache_ttl)
        return results

    async def get_recent(self, user_id: str, limit: int | None = None) -> list[dict[str, Any]]:
        cache_key = f"recent:{user_id}:{limit}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            logger.debug("Cache hit for recent: %s", cache_key)
            return cached

        results = await self._engine.get_recent(user_id, limit)
        self._cache.set(cache_key, results, ttl=self._cache_ttl)
        return results

    async def get_turn_count(self, user_id: str) -> int:
        cache_key = f"turn_count:{user_id}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        count = await self._engine.get_turn_count(user_id)
        self._cache.set(cache_key, count, ttl=60.0)
        return count

    async def record_conversation_turn(self, user_id: str) -> int:
        self._cache.delete(f"turn_count:{user_id}")
        return await self._engine.record_conversation_turn(user_id)

    async def summarize_with_llm(
        self,
        user_id: str,
        llm_service: Any,
        **kwargs: Any,
    ) -> str:
        self._cache.clear()
        return await self._engine.summarize_with_llm(user_id, llm_service, **kwargs)

    async def summarize(self, user_id: str) -> str:
        return await self._engine.summarize(user_id)

    async def get_stats(self, user_id: str) -> dict[str, Any]:
        return await self._engine.get_stats(user_id)

    async def delete_memory(self, memory_id: str) -> bool:
        self._cache.clear()
        return await self._engine.delete_memory(memory_id)

    async def clear_user_memories(self, user_id: str) -> int:
        self._cache.clear()
        return await self._engine.clear_user_memories(user_id)

    async def close(self) -> None:
        await self._engine.close()


class MemoryOptimizer:
    """记忆优化器 - 管理记忆清理和归档"""

    def __init__(self, memory_engine: MemoryEngine):
        self._engine = memory_engine
        self._last_cleanup = datetime.now()
        self._cleanup_interval = 3600.0

    async def cleanup_old_memories(self, max_age_days: int = 90) -> int:
        """清理旧记忆"""
        now = datetime.now()
        if (now - self._last_cleanup).total_seconds() < self._cleanup_interval:
            return 0

        try:
            collection = self._engine._ensure_collection()
            results = collection.get(include=["metadatas", "ids"])

            if not results["ids"]:
                return 0

            cutoff = datetime.now().timestamp() - (max_age_days * 86400)
            ids_to_delete = []

            for i, meta in enumerate(results["metadatas"]):
                if "timestamp" in meta:
                    try:
                        ts = datetime.fromisoformat(meta["timestamp"]).timestamp()
                        if ts < cutoff:
                            ids_to_delete.append(results["ids"][i])
                    except (ValueError, TypeError):
                        pass

            if ids_to_delete:
                collection.delete(ids=ids_to_delete)
                logger.info("Cleaned up %d old memories", len(ids_to_delete))

            self._last_cleanup = now
            return len(ids_to_delete)

        except Exception as e:
            logger.error("Failed to cleanup old memories: %s", e)
            return 0

    async def compress_memories(self, user_id: str, threshold: int = 100) -> bool:
        """压缩用户记忆 - 将多次对话合并"""
        try:
            stats = await self._engine.get_stats(user_id)

            if stats["total_memories"] < threshold:
                return False

            memories = await self._engine.get_recent(user_id, limit=threshold)

            for mem in memories:
                await self._engine.delete_memory(mem["id"])

            logger.info("Compressed %d memories for user %s", len(memories), user_id)
            return True

        except Exception as e:
            logger.error("Failed to compress memories: %s", e)
            return False


def create_cached_memory_engine() -> CachedMemoryEngine:
    """创建带缓存的记忆引擎"""
    base_engine = MemoryEngine()
    return CachedMemoryEngine(base_engine)
