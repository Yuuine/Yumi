"""
Async Storage Service - 异步存储服务
实现消息的异步存储，包括数据库存储和向量存储
支持重试机制和状态追踪
"""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from ..core import get_logger
from ..database import get_db
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
            "total_db_stored": 0,
            "total_vector_stored": 0,
            "total_latency_ms": 0.0,
        }

    async def start(self) -> None:
        """启动后台工作协程"""
        if self._running:
            return

        self._running = True
        self._worker_task = asyncio.create_task(self._worker())
        logger.info("Async storage service started")

    async def stop(self) -> None:
        """优雅关闭工作协程"""
        self._running = False

        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
            self._worker_task = None

        logger.info(
            "Async storage service stopped - completed: %d, failed: %d",
            self._stats["total_completed"],
            self._stats["total_failed"],
        )

    async def enqueue(self, task: StorageTask) -> str:
        """将任务加入队列

        Args:
            task: 存储任务

        Returns:
            任务ID
        """
        await self._queue.put(task)
        self._tasks[task.task_id] = task
        self._stats["total_enqueued"] += 1

        logger.debug(
            "Enqueued storage task %s for message %s",
            task.task_id,
            task.message_id,
        )

        return task.task_id

    async def get_status(self, task_id: str) -> StorageTask | None:
        """获取任务状态

        Args:
            task_id: 任务ID

        Returns:
            任务对象，不存在则返回 None
        """
        return self._tasks.get(task_id)

    async def get_stats(self) -> dict[str, Any]:
        """获取统计信息

        Returns:
            统计信息字典
        """
        stats = self._stats.copy()
        stats["queue_size"] = self._queue.qsize()
        stats["pending_tasks"] = len(
            [t for t in self._tasks.values() if t.status == StorageTaskStatus.PENDING]
        )

        if self._stats["total_completed"] > 0:
            stats["avg_latency_ms"] = (
                self._stats["total_latency_ms"] / self._stats["total_completed"]
            )
        else:
            stats["avg_latency_ms"] = 0.0

        return stats

    def set_memory_engine(self, memory_engine: Any) -> None:
        """设置记忆引擎实例

        Args:
            memory_engine: 记忆引擎实例
        """
        self._memory_engine = memory_engine

    async def _worker(self) -> None:
        """后台工作协程，持续处理队列中的任务"""
        while self._running:
            try:
                task = await asyncio.wait_for(
                    self._queue.get(),
                    timeout=1.0,
                )
                await self._process_task(task)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Worker error: %s", e)

    async def _process_task(self, task: StorageTask) -> None:
        """处理单个存储任务

        并行执行数据库存储和向量存储

        Args:
            task: 存储任务
        """
        start_time = datetime.now(timezone.utc)
        task.attempts += 1

        logger.debug(
            "Processing task %s (attempt %d/%d)",
            task.task_id,
            task.attempts,
            self.MAX_RETRIES,
        )

        try:
            db_result, vector_result = await asyncio.gather(
                self._store_to_db(task),
                self._store_to_vector(task),
                return_exceptions=True,
            )

            if isinstance(db_result, Exception):
                logger.error("DB storage failed: %s", db_result)
                task.db_stored = False
            else:
                task.db_stored = bool(db_result)

            if isinstance(vector_result, Exception):
                logger.error("Vector storage failed: %s", vector_result)
                task.vector_stored = False
                task.error = str(vector_result)
            elif vector_result:
                task.vector_stored = True

            if task.db_stored and task.vector_stored:
                task.status = StorageTaskStatus.COMPLETED
                task.stored_at = datetime.now(timezone.utc)
                self._stats["total_completed"] += 1
                self._stats["total_db_stored"] += 1
                self._stats["total_vector_stored"] += 1

                latency = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
                self._stats["total_latency_ms"] += latency

                logger.debug(
                    "Task %s completed in %.2fms",
                    task.task_id,
                    latency,
                )
            elif task.db_stored:
                task.status = StorageTaskStatus.DB_STORED
                self._stats["total_db_stored"] += 1

                if task.attempts < self.MAX_RETRIES:
                    await self._retry_task(task)
                else:
                    task.status = StorageTaskStatus.FAILED
                    self._stats["total_failed"] += 1
                    logger.warning(
                        "Task %s failed after %d attempts: %s",
                        task.task_id,
                        task.attempts,
                        task.error,
                    )
            else:
                if task.attempts < self.MAX_RETRIES:
                    await self._retry_task(task)
                else:
                    task.status = StorageTaskStatus.FAILED
                    self._stats["total_failed"] += 1
                    logger.warning(
                        "Task %s failed after %d attempts: %s",
                        task.task_id,
                        task.attempts,
                        task.error,
                    )

            await self._update_db_status(task)

        except Exception as e:
            logger.error("Task %s processing error: %s", task.task_id, e)
            task.error = str(e)

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
            async with get_db() as db:
                await db.execute(
                    """INSERT INTO conversation_logs
                       (conversation_id, user_id, role, content, timestamp,
                        emotion_valence, emotion_arousal, storage_status, storage_attempts)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        task.conversation_id,
                        task.user_id,
                        task.role,
                        task.content,
                        task.timestamp.isoformat(),
                        task.emotion.get("valence") if task.emotion else None,
                        task.emotion.get("arousal") if task.emotion else None,
                        StorageTaskStatus.PENDING.value,
                        task.attempts,
                    ),
                )
                await db.commit()

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
            async with get_db() as db:
                await db.execute(
                    """UPDATE conversation_logs
                       SET storage_status = ?,
                           storage_attempts = ?,
                           storage_error = ?,
                           stored_at = ?
                       WHERE conversation_id = ?
                         AND timestamp = ?""",
                    (
                        task.status.value,
                        task.attempts,
                        task.error,
                        task.stored_at.isoformat() if task.stored_at else None,
                        task.conversation_id,
                        task.timestamp.isoformat(),
                    ),
                )
                await db.commit()

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
            async with get_db() as db:
                cursor = await db.execute(
                    """SELECT conversation_id, user_id, role, content, timestamp,
                              emotion_valence, emotion_arousal, storage_attempts
                       FROM conversation_logs
                       WHERE storage_status = 'pending'
                         AND storage_attempts < ?
                       ORDER BY timestamp ASC
                       LIMIT ?""",
                    (self.MAX_RETRIES, limit),
                )
                rows = list(await cursor.fetchall())

                for row in rows:
                    emotion = None
                    if row[5] is not None or row[6] is not None:
                        emotion = {
                            "valence": row[5] or 0.5,
                            "arousal": row[6] or 0.5,
                        }

                    task = StorageTask(
                        task_id=str(uuid.uuid4()),
                        message_id=str(uuid.uuid4()),
                        conversation_id=row[0],
                        user_id=row[1],
                        role=row[2],
                        content=row[3],
                        emotion=emotion,
                        timestamp=datetime.fromisoformat(row[4])
                        if isinstance(row[4], str)
                        else row[4],
                        attempts=row[7] or 0,
                    )

                    await self.enqueue(task)

                if rows:
                    logger.info("Enqueued %d pending records for processing", len(rows))

                return len(rows)

        except Exception as e:
            logger.error("Failed to process pending records: %s", e)
            return 0


_async_storage_service: AsyncStorageService | None = None


def get_async_storage_service() -> AsyncStorageService:
    """获取异步存储服务单例

    Returns:
        异步存储服务实例
    """
    global _async_storage_service
    if _async_storage_service is None:
        _async_storage_service = AsyncStorageService()
    return _async_storage_service
