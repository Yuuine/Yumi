"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

Tests for Memory Engine
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestMemoryEngine:
    @pytest.mark.asyncio
    async def test_store_memory(self, tmp_path):
        from services.memory import MemoryEngine

        with patch("backend.services.memory.settings") as mock_settings:
            mock_settings.vector_db.persist_dir = str(tmp_path / "chroma")
            mock_settings.vector_db.collection_name = "test_memory"
            mock_settings.memory.decay_rate = 0.003
            mock_settings.memory.min_decay_factor = 0.1

            engine = MemoryEngine()

            with patch.object(engine, "collection", MagicMock()):
                engine.collection.add = MagicMock()

                memory_id = await engine.store(
                    user_id="test-user",
                    content="Test memory content",
                    metadata={"test": True},
                    skip_dedup=True,
                )

                assert memory_id is not None

    @pytest.mark.asyncio
    async def test_store_duplicate_memory(self, tmp_path):
        from services.memory import MemoryEngine

        with patch("backend.services.memory.settings") as mock_settings:
            mock_settings.vector_db.persist_dir = str(tmp_path / "chroma")
            mock_settings.vector_db.collection_name = "test_memory"
            mock_settings.memory.deduplication_threshold = 0.85

            engine = MemoryEngine()

            mock_collection = MagicMock()
            mock_collection.query = MagicMock(
                return_value={
                    "distances": [[0.01]],
                    "ids": [["existing-id"]],
                }
            )
            engine.collection = mock_collection

            memory_id = await engine.store(
                user_id="test-user",
                content="Duplicate content",
                skip_dedup=False,
            )

            assert memory_id is None

    @pytest.mark.asyncio
    async def test_search_memories(self, tmp_path):
        from services.memory import MemoryEngine

        with patch("backend.services.memory.settings") as mock_settings:
            mock_settings.vector_db.persist_dir = str(tmp_path / "chroma")
            mock_settings.vector_db.collection_name = "test_memory"
            mock_settings.memory.rag_top_k = 6

            engine = MemoryEngine()

            mock_collection = MagicMock()
            mock_collection.query = MagicMock(
                return_value={
                    "documents": [["Memory 1", "Memory 2"]],
                    "metadatas": [
                        [
                            {"user_id": "test-user", "timestamp": "2024-01-01T00:00:00"},
                            {"user_id": "test-user", "timestamp": "2024-01-02T00:00:00"},
                        ]
                    ],
                    "distances": [[0.1, 0.2]],
                    "ids": [["mem-1", "mem-2"]],
                }
            )
            engine.collection = mock_collection

            results = await engine.search(
                query="test query",
                user_id="test-user",
            )

            assert len(results) == 2
            assert results[0]["content"] == "Memory 1"

    @pytest.mark.asyncio
    async def test_get_recent_memories(self, tmp_path):
        from services.memory import MemoryEngine

        with patch("backend.services.memory.settings") as mock_settings:
            mock_settings.vector_db.persist_dir = str(tmp_path / "chroma")
            mock_settings.vector_db.collection_name = "test_memory"
            mock_settings.memory.recent_context_limit = 8

            engine = MemoryEngine()

            mock_collection = MagicMock()
            mock_collection.query = MagicMock(
                return_value={
                    "documents": [["Recent 1", "Recent 2"]],
                    "metadatas": [
                        [
                            {"timestamp": "2024-01-01T00:00:00"},
                            {"timestamp": "2024-01-02T00:00:00"},
                        ]
                    ],
                    "ids": [["recent-1", "recent-2"]],
                }
            )
            engine.collection = mock_collection

            results = await engine.get_recent(user_id="test-user")

            assert len(results) == 2

    @pytest.mark.asyncio
    async def test_get_turn_count(self, tmp_path):
        from services.memory import MemoryEngine

        with patch("backend.services.memory.settings") as mock_settings:
            mock_settings.vector_db.persist_dir = str(tmp_path / "chroma")

            engine = MemoryEngine()
            engine.turn_counts["test-user"] = 5

            count = await engine.get_turn_count("test-user")
            assert count == 5

            count = await engine.get_turn_count("unknown-user")
            assert count == 0

    @pytest.mark.asyncio
    async def test_summarize(self, tmp_path):
        from services.memory import MemoryEngine

        with patch("backend.services.memory.settings") as mock_settings:
            mock_settings.vector_db.persist_dir = str(tmp_path / "chroma")

            engine = MemoryEngine()

            with patch.object(
                engine,
                "get_recent",
                AsyncMock(
                    return_value=[
                        {"content": "User: Hello\nAssistant: Hi!", "timestamp": "2024-01-01"},
                        {
                            "content": "User: How are you?\nAssistant: I'm good!",
                            "timestamp": "2024-01-02",
                        },
                    ]
                ),
            ):
                summary = await engine.summarize("test-user")

                assert "对话摘要" in summary

    @pytest.mark.asyncio
    async def test_get_stats(self, tmp_path):
        from services.memory import MemoryEngine

        with patch("backend.services.memory.settings") as mock_settings:
            mock_settings.vector_db.persist_dir = str(tmp_path / "chroma")

            engine = MemoryEngine()

            mock_collection = MagicMock()
            mock_collection.get = MagicMock(
                return_value={
                    "ids": ["mem-1", "mem-2", "mem-3"],
                    "metadatas": [
                        {"timestamp": "2024-01-01", "importance_score": 0.8},
                        {"timestamp": "2024-01-02", "importance_score": 0.6},
                        {"timestamp": "2024-01-03", "importance_score": 0.7},
                    ],
                }
            )
            engine.collection = mock_collection

            stats = await engine.get_stats("test-user")

            assert stats["total_memories"] == 3
            assert stats["oldest_memory"] == "2024-01-01"
            assert stats["newest_memory"] == "2024-01-03"

    @pytest.mark.asyncio
    async def test_delete_memory(self, tmp_path):
        from services.memory import MemoryEngine

        with patch("backend.services.memory.settings") as mock_settings:
            mock_settings.vector_db.persist_dir = str(tmp_path / "chroma")

            engine = MemoryEngine()

            mock_collection = MagicMock()
            mock_collection.delete = MagicMock()
            engine.collection = mock_collection

            result = await engine.delete_memory("mem-123")

            assert result is True

    @pytest.mark.asyncio
    async def test_clear_user_memories(self, tmp_path):
        from services.memory import MemoryEngine

        with patch("backend.services.memory.settings") as mock_settings:
            mock_settings.vector_db.persist_dir = str(tmp_path / "chroma")

            engine = MemoryEngine()

            mock_collection = MagicMock()
            mock_collection.get = MagicMock(
                return_value={
                    "ids": ["mem-1", "mem-2"],
                }
            )
            mock_collection.delete = MagicMock()
            engine.collection = mock_collection

            count = await engine.clear_user_memories("test-user")

            assert count == 2


class TestMemoryImportance:
    def test_calculate_importance_high(self, tmp_path):
        from services.memory import MemoryEngine

        with patch("backend.services.memory.settings") as mock_settings:
            mock_settings.vector_db.persist_dir = str(tmp_path / "chroma")

            engine = MemoryEngine()

            importance = engine._calculate_importance("我喜欢音乐，这是我的梦想")

            assert importance >= 0.5

    def test_calculate_importance_low(self, tmp_path):
        from services.memory import MemoryEngine

        with patch("backend.services.memory.settings") as mock_settings:
            mock_settings.vector_db.persist_dir = str(tmp_path / "chroma")

            engine = MemoryEngine()

            importance = engine._calculate_importance("今天天气不错")

            assert importance == 0.5


class TestMemoryDecay:
    def test_calculate_decay_recent(self, tmp_path):
        from datetime import datetime

        from services.memory import MemoryEngine

        with patch("backend.services.memory.settings") as mock_settings:
            mock_settings.vector_db.persist_dir = str(tmp_path / "chroma")
            mock_settings.memory.decay_rate = 0.003
            mock_settings.memory.min_decay_factor = 0.1

            engine = MemoryEngine()

            recent_timestamp = datetime.now().isoformat()
            decay = engine._calculate_decay(recent_timestamp)

            assert decay >= 0.9

    def test_calculate_decay_old(self, tmp_path):
        from datetime import datetime, timedelta

        from services.memory import MemoryEngine

        with patch("backend.services.memory.settings") as mock_settings:
            mock_settings.vector_db.persist_dir = str(tmp_path / "chroma")
            mock_settings.memory.decay_rate = 0.003
            mock_settings.memory.min_decay_factor = 0.1

            engine = MemoryEngine()

            old_timestamp = (datetime.now() - timedelta(days=100)).isoformat()
            decay = engine._calculate_decay(old_timestamp)

            assert decay <= 0.7
            assert decay >= 0.1
