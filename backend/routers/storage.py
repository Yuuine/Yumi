"""
Storage API Router - 存储状态监控接口
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ..core import get_logger
from ..services.async_storage import get_async_storage_service

router = APIRouter()
logger = get_logger(__name__)


class StorageStatusResponse(BaseModel):
    """存储状态响应模型"""

    taskId: str = Field(..., description="任务ID")
    status: str = Field(..., description="存储状态: pending/completed/failed")
    dbStored: bool = Field(..., description="是否已存储到数据库")
    vectorStored: bool = Field(..., description="是否已存储到向量数据库")
    attempts: int = Field(..., description="重试次数")
    storedAt: str | None = Field(None, description="存储完成时间")


class StorageStatsResponse(BaseModel):
    """存储统计响应模型"""

    queueLength: int = Field(..., description="当前队列长度")
    avgLatencyMs: float = Field(..., description="平均延迟（毫秒）")
    successCount: int = Field(..., description="成功存储数量")
    failureCount: int = Field(..., description="失败存储数量")
    retryCount: int = Field(..., description="重试次数")


@router.get("/storage/status/{task_id}", response_model=StorageStatusResponse)
async def get_storage_status(task_id: str):
    """
    获取指定任务的存储状态

    Args:
        task_id: 任务ID

    Returns:
        StorageStatusResponse: 存储状态信息
    """
    logger.info("获取存储状态: task_id=%s", task_id)

    async_storage = get_async_storage_service()
    task = await async_storage.get_status(task_id)

    if not task:
        return StorageStatusResponse(
            taskId=task_id,
            status="not_found",
            dbStored=False,
            vectorStored=False,
            attempts=0,
            storedAt=None,
        )

    return StorageStatusResponse(
        taskId=task.task_id,
        status=task.status.value,
        dbStored=task.db_stored,
        vectorStored=task.vector_stored,
        attempts=task.attempts,
        storedAt=task.stored_at.strftime("%Y-%m-%dT%H:%M:%SZ") if task.stored_at else None,
    )


@router.get("/storage/stats", response_model=StorageStatsResponse)
async def get_storage_stats():
    """
    获取存储队列统计信息

    Returns:
        StorageStatsResponse: 存储统计信息
    """
    logger.info("获取存储统计信息")

    async_storage = get_async_storage_service()
    stats = await async_storage.get_stats()

    return StorageStatsResponse(
        queueLength=stats.get("queue_size", 0),
        avgLatencyMs=stats.get("avg_latency_ms", 0.0),
        successCount=stats.get("total_completed", 0),
        failureCount=stats.get("total_failed", 0),
        retryCount=stats.get("total_retries", 0),
    )
