"""
Integration Tests for Async Storage
"""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest


class TestMessageStorageIntegration:
    @pytest.mark.asyncio
    async def test_full_message_storage_flow(self):
        from backend.services.async_storage import (
            AsyncStorageService,
            StorageTask,
            StorageTaskStatus,
        )

        service = AsyncStorageService()

        task = StorageTask.create(
            message_id="msg-integration-1",
            conversation_id="conv-integration-1",
            user_id="user-integration-1",
            role="user",
            content="Integration test message",
            emotion={"valence": 0.5, "arousal": 0.3},
        )

        with (
            patch.object(service, "_store_to_db", new_callable=AsyncMock) as mock_db,
            patch.object(service, "_store_to_vector", new_callable=AsyncMock) as mock_vector,
            patch.object(service, "_update_db_status", new_callable=AsyncMock),
        ):
            mock_db.return_value = True
            mock_vector.return_value = "memory-integration-1"

            task_id = await service.enqueue(task)
            assert task_id is not None

            await service._process_task(task)

            assert task.status == StorageTaskStatus.COMPLETED
            assert task.db_stored is True
            assert task.vector_stored is True
            assert task.stored_at is not None

    @pytest.mark.asyncio
    async def test_storage_failure_recovery(self):
        from backend.services.async_storage import (
            AsyncStorageService,
            StorageTask,
            StorageTaskStatus,
        )

        service = AsyncStorageService()

        task = StorageTask.create(
            message_id="msg-failure-1",
            conversation_id="conv-failure-1",
            user_id="user-failure-1",
            role="user",
            content="Failure test message",
        )

        call_count = 0

        async def failing_db_store(t):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Simulated DB failure")
            return True

        with (
            patch.object(service, "_store_to_db", side_effect=failing_db_store),
            patch.object(service, "_store_to_vector", new_callable=AsyncMock) as mock_vector,
            patch.object(service, "_update_db_status", new_callable=AsyncMock),
        ):
            mock_vector.return_value = "memory-recovery-1"

            await service._process_task(task)
            assert task.attempts == 1

            await service._process_task(task)
            assert task.attempts == 2

            await service._process_task(task)
            assert task.status == StorageTaskStatus.COMPLETED
            assert task.db_stored is True

    @pytest.mark.asyncio
    async def test_concurrent_storage_tasks(self):
        from backend.services.async_storage import (
            AsyncStorageService,
            StorageTask,
            StorageTaskStatus,
        )

        service = AsyncStorageService()

        tasks = []
        for i in range(10):
            task = StorageTask.create(
                message_id=f"msg-concurrent-{i}",
                conversation_id=f"conv-concurrent-{i}",
                user_id="user-concurrent",
                role="user" if i % 2 == 0 else "assistant",
                content=f"Concurrent message {i}",
            )
            tasks.append(task)

        with (
            patch.object(service, "_store_to_db", new_callable=AsyncMock) as mock_db,
            patch.object(service, "_store_to_vector", new_callable=AsyncMock) as mock_vector,
            patch.object(service, "_update_db_status", new_callable=AsyncMock),
        ):
            mock_db.return_value = True
            mock_vector.return_value = "memory-concurrent"

            for task in tasks:
                await service.enqueue(task)

            assert service._stats["total_enqueued"] == 10

            for task in tasks:
                await service._process_task(task)

            assert service._stats["total_completed"] == 10

            for task in tasks:
                assert task.status == StorageTaskStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_worker_queue_processing(self):
        from backend.services.async_storage import (
            AsyncStorageService,
            StorageTask,
        )

        service = AsyncStorageService()

        task = StorageTask.create(
            message_id="msg-worker-1",
            conversation_id="conv-worker-1",
            user_id="user-worker-1",
            role="user",
            content="Worker test message",
        )

        with (
            patch.object(service, "_store_to_db", new_callable=AsyncMock) as mock_db,
            patch.object(service, "_store_to_vector", new_callable=AsyncMock) as mock_vector,
            patch.object(service, "_update_db_status", new_callable=AsyncMock),
        ):
            mock_db.return_value = True
            mock_vector.return_value = "memory-worker-1"

            await service.start()

            await service.enqueue(task)

            await asyncio.sleep(0.5)

            await service.stop()

            stats = await service.get_stats()
            assert stats["total_enqueued"] >= 1


class TestStorageStatsIntegration:
    @pytest.mark.asyncio
    async def test_stats_tracking(self):
        from backend.services.async_storage import AsyncStorageService, StorageTask

        service = AsyncStorageService()

        initial_stats = await service.get_stats()
        assert initial_stats["total_enqueued"] == 0
        assert initial_stats["total_completed"] == 0
        assert initial_stats["total_failed"] == 0

        task = StorageTask.create(
            message_id="msg-stats-1",
            conversation_id="conv-stats-1",
            user_id="user-stats-1",
            role="user",
            content="Stats test message",
        )

        with (
            patch.object(service, "_store_to_db", new_callable=AsyncMock) as mock_db,
            patch.object(service, "_store_to_vector", new_callable=AsyncMock) as mock_vector,
            patch.object(service, "_update_db_status", new_callable=AsyncMock),
        ):
            mock_db.return_value = True
            mock_vector.return_value = "memory-stats-1"

            await service.enqueue(task)
            await service._process_task(task)

            stats = await service.get_stats()
            assert stats["total_enqueued"] == 1
            assert stats["total_completed"] == 1

    @pytest.mark.asyncio
    async def test_latency_tracking(self):
        from backend.services.async_storage import AsyncStorageService, StorageTask

        service = AsyncStorageService()

        task = StorageTask.create(
            message_id="msg-latency-1",
            conversation_id="conv-latency-1",
            user_id="user-latency-1",
            role="user",
            content="Latency test message",
        )

        with (
            patch.object(service, "_store_to_db", new_callable=AsyncMock) as mock_db,
            patch.object(service, "_store_to_vector", new_callable=AsyncMock) as mock_vector,
            patch.object(service, "_update_db_status", new_callable=AsyncMock),
        ):
            mock_db.return_value = True
            mock_vector.return_value = "memory-latency-1"

            await service.enqueue(task)
            await service._process_task(task)

            stats = await service.get_stats()
            assert stats["avg_latency_ms"] >= 0
