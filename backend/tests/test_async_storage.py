"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

Tests for Async Storage Service
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestStorageTaskStatus:
    def test_status_values(self):
        from services.async_storage import StorageTaskStatus

        assert StorageTaskStatus.PENDING.value == "pending"
        assert StorageTaskStatus.DB_STORED.value == "db_stored"
        assert StorageTaskStatus.VECTOR_STORED.value == "vector_stored"
        assert StorageTaskStatus.COMPLETED.value == "completed"
        assert StorageTaskStatus.FAILED.value == "failed"


class TestStorageTask:
    def test_create_task(self):
        from services.async_storage import StorageTask

        task = StorageTask.create(
            message_id="msg-123",
            conversation_id="conv-456",
            user_id="user-789",
            role="user",
            content="Hello",
            emotion={"valence": 0.5, "arousal": 0.3},
        )

        assert task.message_id == "msg-123"
        assert task.conversation_id == "conv-456"
        assert task.user_id == "user-789"
        assert task.role == "user"
        assert task.content == "Hello"
        assert task.emotion == {"valence": 0.5, "arousal": 0.3}
        assert task.attempts == 0
        assert task.db_stored is False
        assert task.vector_stored is False
        assert task.stored_at is None
        assert task.task_id is not None

    def test_create_task_without_emotion(self):
        from services.async_storage import StorageTask

        task = StorageTask.create(
            message_id="msg-123",
            conversation_id="conv-456",
            user_id="user-789",
            role="assistant",
            content="Hi there!",
        )

        assert task.emotion is None


class TestAsyncStorageService:
    @pytest.mark.asyncio
    async def test_service_start_and_stop(self):
        from services.async_storage import AsyncStorageService

        service = AsyncStorageService()

        assert service._running is False
        assert service._worker_task is None

        await service.start()
        assert service._running is True
        assert service._worker_task is not None

        await service.stop()
        assert service._running is False
        assert service._worker_task is None

    @pytest.mark.asyncio
    async def test_enqueue_task(self):
        from services.async_storage import AsyncStorageService, StorageTask

        service = AsyncStorageService()

        task = StorageTask.create(
            message_id="msg-1",
            conversation_id="conv-1",
            user_id="user-1",
            role="user",
            content="Test message",
        )

        task_id = await service.enqueue(task)

        assert task_id == task.task_id
        assert service._stats["total_enqueued"] == 1
        assert await service.get_status(task_id) == task

    @pytest.mark.asyncio
    async def test_get_stats(self):
        from services.async_storage import AsyncStorageService

        service = AsyncStorageService()

        stats = await service.get_stats()

        assert "queue_size" in stats
        assert "total_enqueued" in stats
        assert "total_completed" in stats
        assert "total_failed" in stats
        assert "avg_latency_ms" in stats

    @pytest.mark.asyncio
    async def test_set_memory_engine(self):
        from services.async_storage import AsyncStorageService

        service = AsyncStorageService()

        mock_engine = MagicMock()
        service.set_memory_engine(mock_engine)

        assert service._memory_engine == mock_engine

    @pytest.mark.asyncio
    async def test_process_task_success(self):
        from services.async_storage import (
            AsyncStorageService,
            StorageTask,
            StorageTaskStatus,
        )

        service = AsyncStorageService()

        task = StorageTask.create(
            message_id="msg-1",
            conversation_id="conv-1",
            user_id="user-1",
            role="user",
            content="Test message",
        )

        with (
            patch.object(service, "_store_to_db", new_callable=AsyncMock) as mock_db,
            patch.object(service, "_store_to_vector", new_callable=AsyncMock) as mock_vector,
            patch.object(service, "_update_db_status", new_callable=AsyncMock),
        ):
            mock_db.return_value = True
            mock_vector.return_value = "memory-id-123"

            await service._process_task(task)

            assert task.db_stored is True
            assert task.vector_stored is True
            assert task.status == StorageTaskStatus.COMPLETED
            assert task.stored_at is not None
            assert service._stats["total_completed"] == 1

    @pytest.mark.asyncio
    async def test_process_task_db_failure(self):
        from services.async_storage import AsyncStorageService, StorageTask

        service = AsyncStorageService()

        task = StorageTask.create(
            message_id="msg-1",
            conversation_id="conv-1",
            user_id="user-1",
            role="user",
            content="Test message",
        )

        with (
            patch.object(service, "_store_to_db", new_callable=AsyncMock) as mock_db,
            patch.object(service, "_store_to_vector", new_callable=AsyncMock) as mock_vector,
            patch.object(service, "_update_db_status", new_callable=AsyncMock),
            patch.object(service, "_retry_task", new_callable=AsyncMock),
        ):
            mock_db.side_effect = Exception("DB error")
            mock_vector.return_value = "memory-id-123"

            await service._process_task(task)

            assert task.db_stored is False
            assert task.attempts == 1

    @pytest.mark.asyncio
    async def test_retry_mechanism(self):
        from services.async_storage import AsyncStorageService, StorageTask

        service = AsyncStorageService()

        task = StorageTask.create(
            message_id="msg-1",
            conversation_id="conv-1",
            user_id="user-1",
            role="user",
            content="Test message",
        )

        task.attempts = 2

        await service._retry_task(task)

        assert service._stats["total_retries"] == 1

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self):
        from services.async_storage import (
            AsyncStorageService,
            StorageTask,
            StorageTaskStatus,
        )

        service = AsyncStorageService()

        task = StorageTask.create(
            message_id="msg-1",
            conversation_id="conv-1",
            user_id="user-1",
            role="user",
            content="Test message",
        )

        task.attempts = 3

        with (
            patch.object(service, "_store_to_db", new_callable=AsyncMock) as mock_db,
            patch.object(service, "_store_to_vector", new_callable=AsyncMock) as mock_vector,
            patch.object(service, "_update_db_status", new_callable=AsyncMock),
        ):
            mock_db.side_effect = Exception("DB error")
            mock_vector.return_value = None

            await service._process_task(task)

            assert task.status == StorageTaskStatus.FAILED
            assert service._stats["total_failed"] == 1

    @pytest.mark.asyncio
    async def test_store_to_db_success(self):
        from services.async_storage import AsyncStorageService, StorageTask

        service = AsyncStorageService()

        task = StorageTask.create(
            message_id="msg-1",
            conversation_id="conv-1",
            user_id="user-1",
            role="user",
            content="Test message",
            emotion={"valence": 0.5, "arousal": 0.3},
        )

        with patch("backend.services.async_storage.get_db") as mock_get_db:
            mock_db = AsyncMock()
            mock_db.execute = AsyncMock()
            mock_db.commit = AsyncMock()
            mock_db.__aenter__ = AsyncMock(return_value=mock_db)
            mock_db.__aexit__ = AsyncMock(return_value=None)
            mock_get_db.return_value = mock_db

            result = await service._store_to_db(task)

            assert result is True

    @pytest.mark.asyncio
    async def test_store_to_vector_with_engine(self):
        from services.async_storage import AsyncStorageService, StorageTask

        mock_memory_engine = MagicMock()
        mock_memory_engine.store = AsyncMock(return_value="memory-id-123")

        service = AsyncStorageService(memory_engine=mock_memory_engine)

        task = StorageTask.create(
            message_id="msg-1",
            conversation_id="conv-1",
            user_id="user-1",
            role="user",
            content="Test message",
            emotion={"valence": 0.5, "arousal": 0.3},
        )

        result = await service._store_to_vector(task)

        assert result == "memory-id-123"
        mock_memory_engine.store.assert_called_once()

    @pytest.mark.asyncio
    async def test_store_to_vector_without_engine(self):
        from services.async_storage import AsyncStorageService, StorageTask

        service = AsyncStorageService()

        task = StorageTask.create(
            message_id="msg-1",
            conversation_id="conv-1",
            user_id="user-1",
            role="user",
            content="Test message",
        )

        result = await service._store_to_vector(task)

        assert result is None


class TestGetAsyncStorageService:
    def test_singleton_pattern(self):
        from services.async_storage import get_async_storage_service

        service1 = get_async_storage_service()
        service2 = get_async_storage_service()

        assert service1 is service2
