"""
Tests for Storage API Router
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestStorageStatusEndpoint:
    @pytest.mark.asyncio
    async def test_get_storage_status_success(self):
        from fastapi import FastAPI
        from httpx import ASGITransport, AsyncClient

        from backend.routers.storage import router
        from backend.services.async_storage import StorageTask

        mock_task = StorageTask.create(
            message_id="msg-1",
            conversation_id="conv-1",
            user_id="user-1",
            role="user",
            content="Test message",
        )
        mock_task.db_stored = True
        mock_task.vector_stored = True
        mock_task.stored_at = None

        app = FastAPI()
        app.include_router(router, prefix="/api")

        with patch("backend.routers.storage.get_async_storage_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_status = AsyncMock(return_value=mock_task)
            mock_get_service.return_value = mock_service

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get(f"/api/storage/status/{mock_task.task_id}")

                assert response.status_code == 200
                data = response.json()
                assert data["taskId"] == mock_task.task_id
                assert data["status"] == "pending"
                assert data["dbStored"] is True
                assert data["vectorStored"] is True

    @pytest.mark.asyncio
    async def test_get_storage_status_not_found(self):
        from fastapi import FastAPI
        from httpx import ASGITransport, AsyncClient

        from backend.routers.storage import router

        app = FastAPI()
        app.include_router(router, prefix="/api")

        with patch("backend.routers.storage.get_async_storage_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_status = AsyncMock(return_value=None)
            mock_get_service.return_value = mock_service

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/api/storage/status/nonexistent-id")

                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "not_found"
                assert data["dbStored"] is False
                assert data["vectorStored"] is False


class TestStorageStatsEndpoint:
    @pytest.mark.asyncio
    async def test_get_storage_stats(self):
        from fastapi import FastAPI
        from httpx import ASGITransport, AsyncClient

        from backend.routers.storage import router

        mock_stats = {
            "queue_size": 5,
            "total_enqueued": 100,
            "total_completed": 95,
            "total_failed": 2,
            "total_retries": 3,
            "avg_latency_ms": 120.5,
        }

        app = FastAPI()
        app.include_router(router, prefix="/api")

        with patch("backend.routers.storage.get_async_storage_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_stats = AsyncMock(return_value=mock_stats)
            mock_get_service.return_value = mock_service

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/api/storage/stats")

                assert response.status_code == 200
                data = response.json()
                assert data["queueLength"] == 5
                assert data["avgLatencyMs"] == 120.5
                assert data["successCount"] == 95
                assert data["failureCount"] == 2
                assert data["retryCount"] == 3

    @pytest.mark.asyncio
    async def test_get_storage_stats_empty(self):
        from fastapi import FastAPI
        from httpx import ASGITransport, AsyncClient

        from backend.routers.storage import router

        mock_stats = {
            "queue_size": 0,
            "total_enqueued": 0,
            "total_completed": 0,
            "total_failed": 0,
            "total_retries": 0,
            "avg_latency_ms": 0.0,
        }

        app = FastAPI()
        app.include_router(router, prefix="/api")

        with patch("backend.routers.storage.get_async_storage_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_stats = AsyncMock(return_value=mock_stats)
            mock_get_service.return_value = mock_service

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/api/storage/stats")

                assert response.status_code == 200
                data = response.json()
                assert data["queueLength"] == 0
                assert data["avgLatencyMs"] == 0.0
                assert data["successCount"] == 0
                assert data["failureCount"] == 0
                assert data["retryCount"] == 0


class TestStorageResponseModels:
    def test_storage_status_response_model(self):
        from backend.routers.storage import StorageStatusResponse

        response = StorageStatusResponse(
            taskId="task-123",
            status="completed",
            dbStored=True,
            vectorStored=True,
            attempts=1,
            storedAt="2024-01-01T00:00:00Z",
        )

        assert response.taskId == "task-123"
        assert response.status == "completed"
        assert response.dbStored is True
        assert response.vectorStored is True
        assert response.attempts == 1
        assert response.storedAt == "2024-01-01T00:00:00Z"

    def test_storage_stats_response_model(self):
        from backend.routers.storage import StorageStatsResponse

        response = StorageStatsResponse(
            queueLength=10,
            avgLatencyMs=150.5,
            successCount=100,
            failureCount=5,
            retryCount=8,
        )

        assert response.queueLength == 10
        assert response.avgLatencyMs == 150.5
        assert response.successCount == 100
        assert response.failureCount == 5
        assert response.retryCount == 8
