"""
Log Lifecycle Manager
Handles log archiving and cleanup based on retention policies
"""

from __future__ import annotations

import asyncio
import gzip
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from sqlmodel import select

from ..database_sqlmodel import get_log_session
from ..models import SystemLog, AuditLog
from .config import settings
from .logging import get_logger

logger = get_logger(__name__)


class LogLifecycleManager:
    """日志生命周期管理器"""

    HOT_STORAGE_DAYS = 7
    WARM_STORAGE_DAYS = 30
    COLD_STORAGE_DAYS = 365

    def __init__(self, db_path: Path | None = None, archive_dir: Path | None = None):
        self.db_path = db_path or settings.database.full_path
        self.archive_dir = archive_dir or (settings.database.full_path.parent / "log_archives")
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        """启动生命周期管理任务"""
        if self._running:
            return

        self._running = True
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        self._task = asyncio.create_task(self._run_cleanup_loop())
        logger.info("Log lifecycle manager started")

    async def stop(self) -> None:
        """停止生命周期管理任务"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Log lifecycle manager stopped")

    async def _run_cleanup_loop(self) -> None:
        """清理循环，每天执行一次"""
        while self._running:
            try:
                await self._archive_old_logs()
                await self._delete_expired_archives()
            except Exception as e:
                logger.error("Log lifecycle cleanup error: %s", e)

            await asyncio.sleep(86400)

    async def _archive_old_logs(self) -> None:
        """归档超过热存储期的日志"""
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.HOT_STORAGE_DAYS)

        try:
            async with get_log_session() as session:
                # 归档系统日志
                result = await session.exec(
                    select(SystemLog).where(SystemLog.timestamp < cutoff.isoformat())
                )
                system_logs = result.all()

                if system_logs:
                    logs_data = [
                        {
                            "id": log.id,
                            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                            "level": log.level,
                            "event_type": log.event_type,
                            "trace_id": log.trace_id,
                            "user_id": log.user_id,
                            "session_id": log.session_id,
                            "content": log.content,
                        }
                        for log in system_logs
                    ]

                    archive_file = (
                        self.archive_dir / f"system_logs_{cutoff.strftime('%Y%m%d')}.json.gz"
                    )
                    with gzip.open(archive_file, "wt", encoding="utf-8") as f:
                        json.dump(logs_data, f, ensure_ascii=False)

                    # 删除已归档的日志
                    for log in system_logs:
                        await session.delete(log)
                    await session.commit()

                    logger.info("Archived %d system logs to %s", len(logs_data), archive_file)

                # 归档审计日志
                result = await session.exec(
                    select(AuditLog).where(AuditLog.timestamp < cutoff.isoformat())
                )
                audit_logs = result.all()

                if audit_logs:
                    logs_data = [
                        {
                            "id": log.id,
                            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                            "user_id": log.user_id,
                            "action": log.action,
                            "resource_type": log.resource_type,
                            "resource_id": log.resource_id,
                            "result": log.result,
                            "client_ip": log.client_ip,
                            "details": log.details,
                        }
                        for log in audit_logs
                    ]

                    archive_file = (
                        self.archive_dir / f"audit_logs_{cutoff.strftime('%Y%m%d')}.json.gz"
                    )
                    with gzip.open(archive_file, "wt", encoding="utf-8") as f:
                        json.dump(logs_data, f, ensure_ascii=False)

                    # 删除已归档的日志
                    for log in audit_logs:
                        await session.delete(log)
                    await session.commit()

                    logger.info("Archived %d audit logs to %s", len(logs_data), archive_file)

        except Exception as e:
            logger.error("Failed to archive old logs: %s", e)

    async def _delete_expired_archives(self) -> None:
        """删除超过保留期的归档文件"""
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.COLD_STORAGE_DAYS)

        for file in self.archive_dir.glob("*.json.gz"):
            try:
                file_date_str = file.stem.split("_")[-1]
                file_date = datetime.strptime(file_date_str, "%Y%m%d")

                if file_date < cutoff:
                    file.unlink()
                    logger.info("Deleted expired archive: %s", file)
            except (ValueError, IndexError):
                continue

    async def run_cleanup_once(self) -> dict[str, Any]:
        """执行一次清理（用于手动触发）"""
        result: dict[str, Any] = {
            "system_logs_archived": 0,
            "audit_logs_archived": 0,
            "archives_deleted": 0,
        }

        cutoff = datetime.now(timezone.utc) - timedelta(days=self.HOT_STORAGE_DAYS)

        try:
            async with get_log_session() as session:
                # 统计需要归档的系统日志
                count_result = await session.exec(
                    select(SystemLog).where(SystemLog.timestamp < cutoff.isoformat())
                )
                result["system_logs_archived"] = len(count_result.all())

                # 统计需要归档的审计日志
                count_result = await session.exec(
                    select(AuditLog).where(AuditLog.timestamp < cutoff.isoformat())
                )
                result["audit_logs_archived"] = len(count_result.all())

            await self._archive_old_logs()

            cutoff_cold = datetime.now(timezone.utc) - timedelta(days=self.COLD_STORAGE_DAYS)
            archives_deleted = 0
            for file in self.archive_dir.glob("*.json.gz"):
                try:
                    file_date_str = file.stem.split("_")[-1]
                    file_date = datetime.strptime(file_date_str, "%Y%m%d")
                    if file_date < cutoff_cold:
                        archives_deleted += 1
                except (ValueError, IndexError):
                    continue
            result["archives_deleted"] = archives_deleted

            await self._delete_expired_archives()

        except Exception as e:
            logger.error("Cleanup failed: %s", e)
            result["error"] = str(e)

        return result


_lifecycle_manager: LogLifecycleManager | None = None


def get_lifecycle_manager() -> LogLifecycleManager:
    """获取日志生命周期管理器单例"""
    global _lifecycle_manager
    if _lifecycle_manager is None:
        _lifecycle_manager = LogLifecycleManager()
    return _lifecycle_manager
