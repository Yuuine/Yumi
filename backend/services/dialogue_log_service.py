"""
Dialogue Log Service - 对话交互日志服务
专门记录完整的用户与AI对话交互
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from ..core.logging import get_logger, request_id_var
from ..database import get_log_db

logger = get_logger(__name__)


class EndReason(str, Enum):
    """对话结束原因"""

    NORMAL = ""
    PROVIDER_ERROR = "服务商接口异常"
    NETWORK_ERROR = "网络连接中断"
    USER_CANCEL = "用户手动终止对话"
    TIMEOUT = "请求超时"
    MODEL_ERROR = "模型响应异常"
    INTERNAL_ERROR = "系统内部错误"
    UNKNOWN = "未知错误"


@dataclass
class DialogueInteraction:
    """对话交互数据结构"""

    conversation_id: str | None = None
    user_id: str = ""
    character_id: str | None = None

    request_detail: str | None = None
    response_detail: str | None = None

    start_time: str = ""
    end_time: str | None = None
    duration_ms: int | None = None

    is_normal_end: bool = True
    end_reason: str = ""

    user_emotion: dict[str, Any] | None = None
    assistant_emotion: dict[str, Any] | None = None

    trace_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "character_id": self.character_id,
            "request_detail": self.request_detail,
            "response_detail": self.response_detail,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "is_normal_end": 1 if self.is_normal_end else 0,
            "end_reason": self.end_reason,
            "user_emotion": json.dumps(self.user_emotion, ensure_ascii=False)
            if self.user_emotion
            else None,
            "assistant_emotion": json.dumps(self.assistant_emotion, ensure_ascii=False)
            if self.assistant_emotion
            else None,
            "trace_id": self.trace_id,
        }


class DialogueLogService:
    """对话交互日志服务"""

    @staticmethod
    def _get_trace_id() -> str | None:
        """获取当前请求的trace_id"""
        try:
            return request_id_var.get()
        except LookupError:
            return None

    @staticmethod
    async def log_interaction(interaction: DialogueInteraction) -> int | None:
        """
        记录一次完整的对话交互

        Args:
            interaction: 对话交互数据

        Returns:
            插入记录的ID，失败返回None
        """
        interaction.trace_id = interaction.trace_id or DialogueLogService._get_trace_id()

        data = interaction.to_dict()

        try:
            async with get_log_db() as db:
                cursor = await db.execute(
                    """INSERT INTO dialogue_interaction_logs
                       (conversation_id, user_id, character_id, request_detail, response_detail,
                        start_time, end_time, duration_ms, is_normal_end, end_reason,
                        user_emotion, assistant_emotion, trace_id)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        data["conversation_id"],
                        data["user_id"],
                        data["character_id"],
                        data["request_detail"],
                        data["response_detail"],
                        data["start_time"],
                        data["end_time"],
                        data["duration_ms"],
                        data["is_normal_end"],
                        data["end_reason"],
                        data["user_emotion"],
                        data["assistant_emotion"],
                        data["trace_id"],
                    ),
                )
                await db.commit()
                log_id = cursor.lastrowid

                logger.info(
                    "Dialogue interaction logged: user=%s, conversation=%s, duration=%sms, normal=%s",
                    interaction.user_id,
                    interaction.conversation_id,
                    interaction.duration_ms or 0,
                    interaction.is_normal_end,
                )

                return log_id

        except Exception as e:
            logger.error("Failed to log dialogue interaction: %s", e)
            return None

    @staticmethod
    async def get_interactions_by_user(
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        include_details: bool = False,
    ) -> list[dict[str, Any]]:
        """
        查询用户的对话交互记录

        Args:
            user_id: 用户ID
            limit: 返回数量限制
            offset: 偏移量
            include_details: 是否包含详细信息（request_detail, response_detail）
        """
        select_fields = """id, conversation_id, user_id, character_id,
                          start_time, end_time, duration_ms,
                          is_normal_end, end_reason, created_at"""

        if include_details:
            select_fields += ", request_detail, response_detail, user_emotion, assistant_emotion"

        async with get_log_db() as db:
            cursor = await db.execute(
                f"""SELECT {select_fields}
                    FROM dialogue_interaction_logs
                    WHERE user_id = ?
                    ORDER BY start_time DESC
                    LIMIT ? OFFSET ?""",
                (user_id, limit, offset),
            )
            rows = await cursor.fetchall()

            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]

    @staticmethod
    async def get_interactions_by_conversation(
        conversation_id: str,
        limit: int = 100,
        offset: int = 0,
        include_details: bool = False,
    ) -> list[dict[str, Any]]:
        """
        查询会话的对话交互记录

        Args:
            conversation_id: 会话ID
            limit: 返回数量限制
            offset: 偏移量
            include_details: 是否包含详细信息
        """
        select_fields = """id, conversation_id, user_id, character_id,
                          start_time, end_time, duration_ms,
                          is_normal_end, end_reason, created_at"""

        if include_details:
            select_fields += ", request_detail, response_detail, user_emotion, assistant_emotion"

        async with get_log_db() as db:
            cursor = await db.execute(
                f"""SELECT {select_fields}
                    FROM dialogue_interaction_logs
                    WHERE conversation_id = ?
                    ORDER BY start_time ASC
                    LIMIT ? OFFSET ?""",
                (conversation_id, limit, offset),
            )
            rows = await cursor.fetchall()

            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]

    @staticmethod
    async def get_interaction_by_id(log_id: int) -> dict[str, Any] | None:
        """根据ID查询单条对话交互记录"""
        async with get_log_db() as db:
            cursor = await db.execute(
                """SELECT * FROM dialogue_interaction_logs WHERE id = ?""",
                (log_id,),
            )
            row = await cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
            return None

    @staticmethod
    async def clear_all_logs(user_id: str | None = None) -> int:
        """
        清除对话交互日志

        Args:
            user_id: 可选，指定用户ID则只清除该用户的日志

        Returns:
            删除的记录数
        """
        async with get_log_db() as db:
            if user_id:
                cursor = await db.execute(
                    "DELETE FROM dialogue_interaction_logs WHERE user_id = ?",
                    (user_id,),
                )
            else:
                cursor = await db.execute("DELETE FROM dialogue_interaction_logs")
            await db.commit()
            deleted_count = cursor.rowcount
            logger.info(
                "Cleared %d dialogue interaction logs for user=%s", deleted_count, user_id or "all"
            )
            return deleted_count

    @staticmethod
    async def get_log_stats(user_id: str | None = None) -> dict[str, Any]:
        """
        获取日志统计信息

        Args:
            user_id: 可选，指定用户ID则只统计该用户的日志

        Returns:
            统计信息字典
        """
        async with get_log_db() as db:
            if user_id:
                cursor = await db.execute(
                    "SELECT COUNT(*) FROM dialogue_interaction_logs WHERE user_id = ?",
                    (user_id,),
                )
            else:
                cursor = await db.execute("SELECT COUNT(*) FROM dialogue_interaction_logs")
            row = await cursor.fetchone()
            total_count = row[0] if row else 0

            if user_id:
                cursor = await db.execute(
                    "SELECT SUM(duration_ms) FROM dialogue_interaction_logs WHERE user_id = ?",
                    (user_id,),
                )
            else:
                cursor = await db.execute("SELECT SUM(duration_ms) FROM dialogue_interaction_logs")
            row = await cursor.fetchone()
            total_duration_ms = row[0] if row and row[0] else 0

            return {
                "total_interactions": total_count,
                "total_duration_ms": total_duration_ms,
                "user_id": user_id,
            }


dialogue_log_service = DialogueLogService()
