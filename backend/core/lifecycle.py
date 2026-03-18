"""
Log Lifecycle Manager
Handles log archiving and cleanup based on retention policies
"""
from __future__ import annotations

import asyncio
import gzip
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from .config import settings
from .logging import get_logger

logger = get_logger(__name__)


class LogLifecycleManager:
    """日志生命周期管理器"""

    HOT_STORAGE_DAYS = 7
    WARM_STORAGE_DAYS = 30
    COLD_STORAGE_DAYS = 365

    def __init__(self, db_path: Optional[Path] = None, archive_dir: Optional[Path] = None):
        self.db_path = db_path or settings.database.full_path
        self.archive_dir = archive_dir or (settings.database.full_path.parent / "log_archives")
        self._running = False
        self._task: Optional[asyncio.Task] = None

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
        import aiosqlite

        cutoff = datetime.now() - timedelta(days=self.HOT_STORAGE_DAYS)

        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT * FROM system_logs WHERE timestamp < ?",
                    (cutoff.isoformat(),)
                )
                rows = await cursor.fetchall()

                if rows:
                    columns = [desc[0] for desc in cursor.description]
                    logs = [dict(zip(columns, row)) for row in rows]

                    archive_file = self.archive_dir / f"system_logs_{cutoff.strftime('%Y%m%d')}.json.gz"
                    with gzip.open(archive_file, 'wt', encoding='utf-8') as f:
                        json.dump(logs, f, ensure_ascii=False)

                    await db.execute(
                        "DELETE FROM system_logs WHERE timestamp < ?",
                        (cutoff.isoformat(),)
                    )
                    await db.commit()

                    logger.info("Archived %d system logs to %s", len(logs), archive_file)

                cursor = await db.execute(
                    "SELECT * FROM audit_logs WHERE timestamp < ?",
                    (cutoff.isoformat(),)
                )
                audit_rows = await cursor.fetchall()

                if audit_rows:
                    columns = [desc[0] for desc in cursor.description]
                    logs = [dict(zip(columns, row)) for row in audit_rows]

                    archive_file = self.archive_dir / f"audit_logs_{cutoff.strftime('%Y%m%d')}.json.gz"
                    with gzip.open(archive_file, 'wt', encoding='utf-8') as f:
                        json.dump(logs, f, ensure_ascii=False)

                    await db.execute(
                        "DELETE FROM audit_logs WHERE timestamp < ?",
                        (cutoff.isoformat(),)
                    )
                    await db.commit()

                    logger.info("Archived %d audit logs to %s", len(logs), archive_file)

        except Exception as e:
            logger.error("Failed to archive old logs: %s", e)

    async def _delete_expired_archives(self) -> None:
        """删除超过保留期的归档文件"""
        cutoff = datetime.now() - timedelta(days=self.COLD_STORAGE_DAYS)

        for file in self.archive_dir.glob("*.json.gz"):
            try:
                file_date_str = file.stem.split('_')[-1]
                file_date = datetime.strptime(file_date_str, '%Y%m%d')

                if file_date < cutoff:
                    file.unlink()
                    logger.info("Deleted expired archive: %s", file)
            except (ValueError, IndexError):
                continue

    async def run_cleanup_once(self) -> dict:
        """执行一次清理（用于手动触发）"""
        result = {
            "system_logs_archived": 0,
            "audit_logs_archived": 0,
            "archives_deleted": 0,
        }

        import aiosqlite

        cutoff = datetime.now() - timedelta(days=self.HOT_STORAGE_DAYS)

        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT COUNT(*) FROM system_logs WHERE timestamp < ?",
                    (cutoff.isoformat(),)
                )
                row = await cursor.fetchone()
                result["system_logs_archived"] = row[0] if row else 0

                cursor = await db.execute(
                    "SELECT COUNT(*) FROM audit_logs WHERE timestamp < ?",
                    (cutoff.isoformat(),)
                )
                row = await cursor.fetchone()
                result["audit_logs_archived"] = row[0] if row else 0

            await self._archive_old_logs()

            cutoff_cold = datetime.now() - timedelta(days=self.COLD_STORAGE_DAYS)
            for file in self.archive_dir.glob("*.json.gz"):
                try:
                    file_date_str = file.stem.split('_')[-1]
                    file_date = datetime.strptime(file_date_str, '%Y%m%d')
                    if file_date < cutoff_cold:
                        result["archives_deleted"] += 1
                except (ValueError, IndexError):
                    continue

            await self._delete_expired_archives()

        except Exception as e:
            logger.error("Cleanup failed: %s", e)
            result["error"] = str(e)

        return result


_lifecycle_manager: Optional[LogLifecycleManager] = None


def get_lifecycle_manager() -> LogLifecycleManager:
    """获取日志生命周期管理器单例"""
    global _lifecycle_manager
    if _lifecycle_manager is None:
        _lifecycle_manager = LogLifecycleManager()
    return _lifecycle_manager
