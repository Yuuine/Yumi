"""
Memory Engine - Long-term memory with ChromaDB
Implements Ebbinghaus decay, semantic deduplication, and LLM summarization
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import chromadb
import numpy as np

from ..core import MemoryException, settings

logger = logging.getLogger(__name__)


class MemoryEngine:
    def __init__(self) -> None:
        persist_dir = Path(settings.vector_db.persist_dir)
        persist_dir.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(path=str(persist_dir))
        self.collection = None
        self.turn_counts: dict[str, int] = {}
        self._embedding_cache: dict[str, list[float]] = {}

    async def initialize(self) -> None:
        self.collection = self.client.get_or_create_collection(
            name=settings.vector_db.collection_name,
            metadata={"description": "Yumi long-term memory storage"},
        )
        logger.info(
            "Memory engine initialized with %d memories", self.collection.count()
        )

    async def store(
        self,
        user_id: str,
        content: str,
        metadata: dict[str, Any] | None = None,
        skip_dedup: bool = False,
    ) -> str | None:
        if not skip_dedup:
            is_duplicate = await self._check_semantic_duplicate(user_id, content)
            if is_duplicate:
                logger.debug("Skipped storing duplicate memory for user %s", user_id)
                return None

        memory_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        if metadata is None:
            metadata = {}

        metadata.update(
            {
                "user_id": user_id,
                "timestamp": timestamp,
                "importance_score": self._calculate_importance(content),
            }
        )

        try:
            self.collection.add(
                documents=[content],
                metadatas=[metadata],
                ids=[memory_id],
            )
        except Exception as e:
            logger.error("Failed to store memory: %s", e)
            raise MemoryException(
                message="存储记忆失败",
                code="MEMORY_STORE_ERROR",
                details={"error": str(e)},
            )

        self.turn_counts[user_id] = self.turn_counts.get(user_id, 0) + 1

        logger.debug("Stored memory %s for user %s", memory_id, user_id)
        return memory_id

    async def _check_semantic_duplicate(
        self,
        user_id: str,
        content: str,
        threshold: float = 0.95,
    ) -> bool:
        try:
            results = self.collection.query(
                query_texts=[content],
                n_results=3,
                where={"user_id": user_id},
                include=["distances"],
            )

            if results["distances"] and results["distances"][0]:
                min_distance = min(results["distances"][0])
                similarity = 1 - min_distance
                return similarity >= threshold
        except Exception as e:
            logger.warning("Duplicate check failed: %s", e)

        return False

    async def search(
        self,
        query: str,
        top_k: int | None = None,
        user_id: str | None = None,
        apply_decay: bool = True,
    ) -> list[dict[str, Any]]:
        top_k = top_k or settings.memory.rag_top_k

        where_filter = None
        if user_id:
            where_filter = {"user_id": user_id}

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                where=where_filter,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as e:
            logger.error("Failed to search memory: %s", e)
            raise MemoryException(
                message="检索记忆失败",
                code="MEMORY_SEARCH_ERROR",
                details={"error": str(e)},
            )

        memories = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                metadata = results["metadatas"][0][i]
                distance = results["distances"][0][i]
                similarity = 1 - distance

                decay_factor = 1.0
                if apply_decay and "timestamp" in metadata:
                    decay_factor = self._calculate_decay(metadata["timestamp"])

                effective_similarity = similarity * decay_factor

                memories.append(
                    {
                        "id": results["ids"][0][i],
                        "content": doc,
                        "timestamp": metadata.get("timestamp", ""),
                        "similarity": effective_similarity,
                        "decay_factor": decay_factor,
                        "metadata": metadata,
                    }
                )

        memories.sort(key=lambda x: x["similarity"], reverse=True)
        return memories[:top_k]

    async def get_recent(
        self, user_id: str, limit: int | None = None
    ) -> list[dict[str, Any]]:
        limit = limit or settings.memory.recent_context_limit

        try:
            results = self.collection.query(
                query_texts=[""],
                n_results=limit,
                where={"user_id": user_id},
                include=["documents", "metadatas"],
            )
        except Exception as e:
            logger.error("Failed to get recent memories: %s", e)
            raise MemoryException(
                message="获取近期记忆失败",
                code="MEMORY_RECENT_ERROR",
                details={"error": str(e)},
            )

        memories = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                memories.append(
                    {
                        "id": results["ids"][0][i],
                        "content": doc,
                        "timestamp": results["metadatas"][0][i].get("timestamp", ""),
                    }
                )

        return sorted(memories, key=lambda x: x["timestamp"], reverse=True)[:limit]

    async def get_turn_count(self, user_id: str) -> int:
        return self.turn_counts.get(user_id, 0)

    async def summarize_with_llm(
        self,
        user_id: str,
        llm_service: Any,
    ) -> str:
        recent_memories = await self.get_recent(user_id, limit=35)

        if not recent_memories:
            return ""

        conversation_text = ""
        for mem in recent_memories:
            conversation_text += mem["content"] + "\n"

        summary_prompt = f"""请对以下对话内容进行简洁的摘要，提取关键信息和情感要点：

{conversation_text}

摘要要求：
1. 保留重要的事实信息（如用户提到的喜好、经历等）
2. 概括情感变化趋势
3. 突出关键话题
4. 控制在200字以内

摘要："""

        try:
            summary = await llm_service.chat(
                messages=[{"role": "user", "content": summary_prompt}],
                temperature=0.3,
                max_tokens=300,
            )

            await self.store(
                user_id=user_id,
                content=f"[摘要] {summary}",
                metadata={"type": "summary", "timestamp": datetime.now().isoformat()},
                skip_dedup=True,
            )

            logger.info("Generated and stored LLM summary for user %s", user_id)
            return summary

        except Exception as e:
            logger.error("Failed to generate LLM summary: %s", e)
            return await self.summarize(user_id)

    async def summarize(self, user_id: str) -> str:
        recent_memories = await self.get_recent(user_id, limit=35)

        if not recent_memories:
            return ""

        summary_text = "对话摘要:\n"
        for mem in recent_memories:
            summary_text += f"- {mem['content'][:100]}...\n"

        return summary_text

    async def get_stats(self, user_id: str) -> dict[str, Any]:
        try:
            results = self.collection.get(
                where={"user_id": user_id},
                include=["metadatas"],
            )
        except Exception as e:
            logger.error("Failed to get memory stats: %s", e)
            raise MemoryException(
                message="获取记忆统计失败",
                code="MEMORY_STATS_ERROR",
                details={"error": str(e)},
            )

        total = len(results["ids"]) if results["ids"] else 0

        timestamps = []
        importance_scores = []

        if results["metadatas"]:
            for meta in results["metadatas"]:
                if "timestamp" in meta:
                    timestamps.append(meta["timestamp"])
                if "importance_score" in meta:
                    importance_scores.append(meta["importance_score"])

        return {
            "total_memories": total,
            "oldest_memory": min(timestamps) if timestamps else None,
            "newest_memory": max(timestamps) if timestamps else None,
            "avg_importance": float(np.mean(importance_scores))
            if importance_scores
            else 0.0,
        }

    async def delete_memory(self, memory_id: str) -> bool:
        try:
            self.collection.delete(ids=[memory_id])
            logger.debug("Deleted memory %s", memory_id)
            return True
        except Exception as e:
            logger.error("Failed to delete memory: %s", e)
            return False

    async def clear_user_memories(self, user_id: str) -> int:
        try:
            results = self.collection.get(
                where={"user_id": user_id},
                include=["ids"],
            )

            if results["ids"]:
                self.collection.delete(ids=results["ids"])
                count = len(results["ids"])
                self.turn_counts[user_id] = 0
                logger.info("Cleared %d memories for user %s", count, user_id)
                return count

            return 0
        except Exception as e:
            logger.error("Failed to clear user memories: %s", e)
            return 0

    def _calculate_importance(self, content: str) -> float:
        importance_keywords = [
            "喜欢",
            "讨厌",
            "爱",
            "恨",
            "重要",
            "记住",
            "忘记",
            "生日",
            "名字",
            "工作",
            "家",
            "梦想",
            "目标",
            "家人",
            "朋友",
            "健康",
            "计划",
        ]

        score = 0.5
        for keyword in importance_keywords:
            if keyword in content:
                score += 0.08

        question_words = ["为什么", "怎么", "如何", "什么"]
        for word in question_words:
            if word in content:
                score += 0.05

        return min(score, 1.0)

    def _calculate_decay(self, timestamp_str: str) -> float:
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
            days_elapsed = (datetime.now() - timestamp).days

            importance_factor = 1.0
            decay = 1 - settings.memory.decay_rate * days_elapsed * importance_factor
            return max(decay, settings.memory.min_decay_factor)
        except (ValueError, TypeError):
            return 1.0

    async def close(self) -> None:
        pass
