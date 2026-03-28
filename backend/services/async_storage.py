"""
Async Storage Service - 异步存储服务
实现消息的异步存储，包括数据库存储和向量存储
支持重试机制和状态追踪
基于 SQLModel 重构
"""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from sqlmodel import select

from ..core import get_logger
from ..database_sqlmodel import get_session
from ..models import ConversationLog
from .log_service import log_service

logger = get_logger(__name__)


class StorageTaskStatus(str, Enum):
    """存储任务状态枚举"""

    PENDING = "pending"
    DB_STORED = "db_stored"
    VECTOR_STORED = "vector_stored"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class StorageTask:
    """存储任务数据类"""

    task_id: str
    message_id: str
    conversation_id: str
    user_id: str
    role: str
    content: str
    emotion: dict[str, Any] | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: StorageTaskStatus = StorageTaskStatus.PENDING
    attempts: int = 0
    error: str | None = None
    db_stored: bool = False
    vector_stored: bool = False
    stored_at: datetime | None = None

    @classmethod
    def create(
        cls,
        message_id: str,
        conversation_id: str,
        user_id: str,
        role: str,
        content: str,
        emotion: dict[str, Any] | None = None,
    ) -> StorageTask:
        """创建新的存储任务"""
        return cls(
            task_id=str(uuid.uuid4()),
            message_id=message_id,
            conversation_id=conversation_id,
            user_id=user_id,
            role=role,
            content=content,
            emotion=emotion,
        )


class AsyncStorageService:
    """异步存储服务

    负责将消息异步存储到数据库和向量数据库
    支持并行存储、重试机制和状态追踪
    """

    MAX_RETRIES = 3

    def __init__(self, memory_engine: Any = None) -> None:
        """初始化异步存储服务

        Args:
            memory_engine: 记忆引擎实例，用于向量存储
        """
        self._queue: asyncio.Queue[StorageTask] = asyncio.Queue()
        self._tasks: dict[str, StorageTask] = {}
        self._worker_task: asyncio.Task | None = None
        self._running = False
        self._memory_engine = memory_engine

        self._stats: dict[str, Any] = {
            "total_enqueued": 0,
            "total_completed": 0,
            "total_failed": 0,
            "total_retries": 0,
        }

    async def start(self) -> None:
        """启动异步存储服务"""
        if self._running:
            return

        self._running = True
        self._worker_task = asyncio.create_task(self._worker())
        logger.info("Async storage service started")

        # 处理之前未完成的记录
        pending_count = await self.process_pending_records()
        if pending_count > 0:
            logger.info("Processed %d pending records", pending_count)

    async def stop(self) -> None:
        """停止异步存储服务"""
        if not self._running:
            return

        self._running = False

        # 等待队列中的任务完成
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

        logger.info("Async storage service stopped")

    async def enqueue(self, task: StorageTask) -> None:
        """将任务加入队列

        Args:
            task: 存储任务
        """
        self._tasks[task.task_id] = task
        await self._queue.put(task)
        self._stats["total_enqueued"] += 1
        logger.debug("Enqueued storage task: %s", task.task_id)

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            **self._stats,
            "queue_size": self._queue.qsize(),
            "pending_tasks": len(self._tasks),
        }

    async def _worker(self) -> None:
        """工作线程，处理队列中的任务"""
        while self._running:
            try:
                task = await self._queue.get()
                await self._process_task(task)
                self._queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Worker error: %s", e)

    async def _process_task(self, task: StorageTask) -> None:
        """处理单个任务

        Args:
            task: 存储任务
        """
        task.attempts += 1
        start_time = time.time()

        try:
            # 1. 存储到数据库
            if not task.db_stored:
                success = await self._store_to_db(task)
                if success:
                    task.db_stored = True
                    task.status = StorageTaskStatus.DB_STORED

            # 2. 存储到向量数据库
            if task.db_stored and not task.vector_stored:
                memory_id = await self._store_to_vector(task)
                if memory_id:
                    task.vector_stored = True
                    task.status = StorageTaskStatus.VECTOR_STORED

            # 3. 更新状态
            if task.db_stored and (task.vector_stored or not self._memory_engine):
                task.status = StorageTaskStatus.COMPLETED
                task.stored_at = datetime.now(timezone.utc)
                self._stats["total_completed"] += 1

                latency_ms = (time.time() - start_time) * 1000
                logger.debug(
                    "Task completed: %s (latency=%.2fms)",
                    task.task_id,
                    latency_ms,
                )

            # 4. 更新数据库状态
            await self._update_db_status(task)

            # 5. 清理完成的任务
            if task.status == StorageTaskStatus.COMPLETED:
                del self._tasks[task.task_id]

        except Exception as e:
            task.error = str(e)
            logger.error(
                "Task failed: %s, attempt %d/%d, error: %s",
                task.task_id,
                task.attempts,
                self.MAX_RETRIES,
                e,
            )

            if task.attempts < self.MAX_RETRIES:
                await self._retry_task(task)
            else:
                task.status = StorageTaskStatus.FAILED
                self._stats["total_failed"] += 1

            await self._update_db_status(task)

    async def _retry_task(self, task: StorageTask) -> None:
        """重试任务

        Args:
            task: 需要重试的任务
        """
        self._stats["total_retries"] += 1
        logger.info(
            "Retrying task %s (attempt %d/%d)",
            task.task_id,
            task.attempts,
            self.MAX_RETRIES,
        )
        await self._queue.put(task)

    async def _store_to_db(self, task: StorageTask) -> bool:
        """存储到数据库

        Args:
            task: 存储任务

        Returns:
            是否成功
        """
        start_time = time.time()
        try:
            async with get_session() as session:
                log_entry = ConversationLog(
                    conversation_id=task.conversation_id,
                    user_id=task.user_id,
                    role=task.role,
                    content=task.content,
                    timestamp=task.timestamp,
                    emotion_valence=task.emotion.get("valence") if task.emotion else None,
                    emotion_arousal=task.emotion.get("arousal") if task.emotion else None,
                    storage_status=StorageTaskStatus.PENDING.value,
                    storage_attempts=task.attempts,
                )
                session.add(log_entry)
                await session.commit()

            latency_ms = (time.time() - start_time) * 1000

            await log_service.log_db_operation(
                operation="INSERT",
                table="conversation_logs",
                resource_id=task.conversation_id,
                result="SUCCESS",
                latency_ms=latency_ms,
                affected_rows=1,
                user_id=task.user_id,
                extra={
                    "message_id": task.message_id,
                    "role": task.role,
                },
            )

            logger.debug(
                "Stored message to DB: conversation=%s, role=%s",
                task.conversation_id,
                task.role,
            )
            return True

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            await log_service.log_db_operation(
                operation="INSERT",
                table="conversation_logs",
                resource_id=task.conversation_id,
                result="FAIL",
                error=str(e),
                latency_ms=latency_ms,
                user_id=task.user_id,
            )
            logger.error("Failed to store to DB: %s", e)
            raise

    async def _store_to_vector(self, task: StorageTask) -> str | None:
        """存储到向量数据库

        Args:
            task: 存储任务

        Returns:
            向量ID，失败返回 None
        """
        if not self._memory_engine:
            logger.debug("Memory engine not available, skipping vector storage")
            return None

        try:
            metadata = {
                "conversation_id": task.conversation_id,
                "message_id": task.message_id,
                "role": task.role,
                "timestamp": task.timestamp.isoformat(),
            }

            if task.emotion:
                metadata["emotion_valence"] = task.emotion.get("valence", 0.5)
                metadata["emotion_arousal"] = task.emotion.get("arousal", 0.5)

            memory_id = await self._memory_engine.store(
                user_id=task.user_id,
                content=f"[{task.role}] {task.content}",
                metadata=metadata,
            )

            if memory_id:
                logger.debug(
                    "Stored to vector DB: memory_id=%s, user=%s",
                    memory_id,
                    task.user_id,
                )
                return memory_id

            return None

        except Exception as e:
            logger.error("Failed to store to vector DB: %s", e)
            raise

    async def _update_db_status(self, task: StorageTask) -> None:
        """更新数据库中的存储状态

        Args:
            task: 存储任务
        """
        start_time = time.time()
        try:
            async with get_session() as session:
                result = await session.exec(
                    select(ConversationLog)
                    .where(ConversationLog.conversation_id == task.conversation_id)
                    .where(ConversationLog.timestamp == task.timestamp)
                    .order_by(ConversationLog.id.desc())
                )
                log_entry = result.first()

                if log_entry:
                    log_entry.storage_status = task.status.value
                    log_entry.storage_attempts = task.attempts
                    log_entry.storage_error = task.error
                    log_entry.stored_at = task.stored_at
                    await session.commit()

            latency_ms = (time.time() - start_time) * 1000
            await log_service.log_db_operation(
                operation="UPDATE",
                table="conversation_logs",
                resource_id=task.conversation_id,
                result="SUCCESS",
                latency_ms=latency_ms,
                user_id=task.user_id,
                extra={
                    "status": task.status.value,
                    "attempts": task.attempts,
                },
            )

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            await log_service.log_db_operation(
                operation="UPDATE",
                table="conversation_logs",
                resource_id=task.conversation_id,
                result="FAIL",
                error=str(e),
                latency_ms=latency_ms,
                user_id=task.user_id,
            )
            logger.error("Failed to update DB status: %s", e)

    async def process_pending_records(self, limit: int = 100) -> int:
        """处理数据库中待处理的记录

        用于启动时处理之前未完成的存储任务

        Args:
            limit: 最大处理数量

        Returns:
            处理的记录数量
        """
        try:
            async with get_session() as session:
                result = await session.exec(
                    select(ConversationLog)
                    .where(ConversationLog.storage_status == StorageTaskStatus.PENDING.value)
                    .where(ConversationLog.storage_attempts < self.MAX_RETRIES)
                    .order_by(ConversationLog.timestamp.asc())
                    .limit(limit)
                )
                logs = result.all()

                for log_entry in logs:
                    emotion = None
                    if log_entry.emotion_valence is not None or log_entry.emotion_arousal is not None:
                        emotion = {
                            "valence": log_entry.emotion_valence or 0.5,
                            "arousal": log_entry.emotion_arousal or 0.5,
                        }

                    task = StorageTask(
                        task_id=str(uuid.uuid4()),
                        message_id=str(uuid.uuid4()),
                        conversation_id=log_entry.conversation_id,
                        user_id=log_entry.user_id,
                        role=log_entry.role,
                        content=log_entry.content,
                        emotion=emotion,
                        timestamp=log_entry.timestamp,
                        attempts=log_entry.storage_attempts or 0,
                    )

                    await self.enqueue(task)

                if logs:
                    logger.info("Enqueued %d pending records for processing", len(logs))

                return len(logs)

        except Exception as e:
            logger.error("Failed to process pending records: %s", e)
            return 0


_async_storage_service: AsyncStorageService | None = None


def get_async_storage_service(memory_engine: Any = None) -> AsyncStorageService:
    """获取异步存储服务实例（单例）"""
    global _async_storage_service
    if _async_storage_service is None:
        _async_storage_service = AsyncStorageService(memory_engine)
    return _async_storage_service
