"""
Archive Manager - 对话归档管理
定期归档旧对话，减少活跃数据量
"""
from __future__ import annotations

import json
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from ..core import get_logger, settings

logger = get_logger(__name__)


class ArchiveManager:
    """对话归档管理器"""

    def __init__(
        self,
        archive_dir: str = "data/archives",
        max_age_days: int = 30,
        archive_interval_hours: int = 24,
    ):
        self._archive_dir = Path(archive_dir)
        self._archive_dir.mkdir(parents=True, exist_ok=True)
        self._max_age_days = max_age_days
        self._archive_interval = archive_interval_hours * 3600.0
        self._last_archive = datetime.now()
        self._lock = threading.Lock()
        self._db = None

    def set_db(self, db) -> None:
        """设置数据库连接"""
        self._db = db

    async def archive_old_conversations(self) -> int:
        """归档旧对话，返回归档数量"""
        if not self._db:
            logger.warning("Database not set, skipping archive")
            return 0

        if (datetime.now() - self._last_archive).total_seconds() < self._archive_interval:
            return 0

        with self._lock:
            try:
                cutoff_date = (
                    datetime.now() - timedelta(days=self._max_age_days)
                ).isoformat()

                cursor = await self._db.execute(
                    """SELECT id, user_id, title, created_at, updated_at
                       FROM conversations
                       WHERE updated_at < ? AND is_active = 0""",
                    (cutoff_date,),
                )
                rows = await cursor.fetchall()

                if not rows:
                    return 0

                archive_count = 0
                archive_data = []

                for row in rows:
                    conv_id, user_id, title, created_at, updated_at = row

                    log_cursor = await self._db.execute(
                        """SELECT role, content, timestamp, emotion_valence, emotion_arousal
                           FROM conversation_logs
                           WHERE conversation_id = ?
                           ORDER BY timestamp""",
                        (conv_id,),
                    )
                    logs = await log_cursor.fetchall()

                    archive_entry = {
                        "conversation_id": conv_id,
                        "user_id": user_id,
                        "title": title,
                        "created_at": created_at,
                        "updated_at": updated_at,
                        "messages": [
                            {
                                "role": log[0],
                                "content": log[1],
                                "timestamp": log[2],
                                "emotion_valence": log[3],
                                "emotion_arousal": log[4],
                            }
                            for log in logs
                        ],
                    }
                    archive_data.append(archive_entry)

                    await self._db.execute(
                        "DELETE FROM conversation_logs WHERE conversation_id = ?",
                        (conv_id,),
                    )
                    await self._db.execute(
                        "DELETE FROM conversations WHERE id = ?", (conv_id,)
                    )

                    archive_count += 1

                if archive_data:
                    archive_file = (
                        self._archive_dir
                        / f"archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    )
                    with open(archive_file, "w", encoding="utf-8") as f:
                        json.dump(archive_data, f, ensure_ascii=False, indent=2)

                    logger.info(
                        "Archived %d conversations to %s",
                        archive_count,
                        archive_file,
                    )

                await self._db.commit()
                self._last_archive = datetime.now()

                return archive_count

            except Exception as e:
                logger.error("Failed to archive conversations: %s", e)
                return 0

    def list_archives(self) -> list[dict[str, Any]]:
        """列出所有归档文件"""
        archives = []
        for file in sorted(self._archive_dir.glob("archive_*.json")):
            stat = file.stat()
            archives.append(
                {
                    "filename": file.name,
                    "size": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "message_count": self._count_archive_messages(file),
                }
            )
        return archives

    def _count_archive_messages(self, archive_file: Path) -> int:
        """统计归档文件中的消息数量"""
        try:
            with open(archive_file, encoding="utf-8") as f:
                data = json.load(f)
                return sum(len(conv.get("messages", [])) for conv in data)
        except Exception:
            return 0

    async def restore_archive(self, filename: str) -> int | None:
        """恢复归档文件，返回恢复的消息数量"""
        archive_file = self._archive_dir / filename
        if not archive_file.exists():
            logger.error("Archive file not found: %s", filename)
            return None

        if not self._db:
            logger.warning("Database not set, skipping restore")
            return None

        try:
            with open(archive_file, encoding="utf-8") as f:
                archive_data = json.load(f)

            message_count = 0

            for conv in archive_data:
                await self._db.execute(
                    """INSERT OR IGNORE INTO conversations
                       (id, user_id, title, created_at, updated_at, is_active)
                       VALUES (?, ?, ?, ?, ?, 0)""",
                    (
                        conv["conversation_id"],
                        conv["user_id"],
                        conv["title"],
                        conv["created_at"],
                        conv["updated_at"],
                    ),
                )

                for msg in conv.get("messages", []):
                    await self._db.execute(
                        """INSERT INTO conversation_logs
                           (conversation_id, user_id, role, content, timestamp,
                            emotion_valence, emotion_arousal)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (
                            conv["conversation_id"],
                            conv["user_id"],
                            msg["role"],
                            msg["content"],
                            msg["timestamp"],
                            msg.get("emotion_valence"),
                            msg.get("emotion_arousal"),
                        ),
                    )
                    message_count += 1

            await self._db.commit()
            logger.info("Restored %d messages from %s", message_count, filename)
            return message_count

        except Exception as e:
            logger.error("Failed to restore archive: %s", e)
            return None


_archive_manager: ArchiveManager | None = None


def get_archive_manager() -> ArchiveManager:
    global _archive_manager
    if _archive_manager is None:
        _archive_manager = ArchiveManager(
            archive_dir="data/archives",
            max_age_days=30,
            archive_interval_hours=24,
        )
    return _archive_manager
