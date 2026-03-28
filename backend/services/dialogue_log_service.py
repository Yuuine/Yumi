"""
Dialogue Log Service - 对话交互日志服务
专门记录完整的用户与AI对话交互
基于 SQLModel 重构
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from sqlmodel import select, func

from ..core.logging import get_logger, request_id_var
from ..database_sqlmodel import get_log_session
from ..models import DialogueInteractionLog

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

    def to_model(self) -> DialogueInteractionLog:
        """转换为 SQLModel"""
        return DialogueInteractionLog(
            conversation_id=self.conversation_id,
            user_id=self.user_id,
            character_id=self.character_id,
            request_detail=json.loads(self.request_detail) if self.request_detail else {},
            response_detail=json.loads(self.response_detail) if self.response_detail else None,
            start_time=datetime.fromisoformat(self.start_time) if self.start_time else datetime.now(timezone.utc),
            end_time=datetime.fromisoformat(self.end_time) if self.end_time else None,
            duration_ms=self.duration_ms,
            is_normal_end=self.is_normal_end,
            end_reason=self.end_reason,
            user_emotion=self.user_emotion,
            assistant_emotion=self.assistant_emotion,
            trace_id=self.trace_id,
        )


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

        try:
            async with get_log_session() as session:
                log_entry = interaction.to_model()
                session.add(log_entry)
                await session.commit()
                await session.refresh(log_entry)

                logger.info(
                    "Dialogue interaction logged: user=%s, conversation=%s, duration=%sms, normal=%s",
                    interaction.user_id,
                    interaction.conversation_id,
                    interaction.duration_ms or 0,
                    interaction.is_normal_end,
                )

                return log_entry.id

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
        async with get_log_session() as session:
            query = select(DialogueInteractionLog).where(
                DialogueInteractionLog.user_id == user_id
            ).order_by(DialogueInteractionLog.start_time.desc()).limit(limit).offset(offset)

            result = await session.exec(query)
            logs = result.all()

            items = []
            for log in logs:
                item = {
                    "id": log.id,
                    "conversation_id": log.conversation_id,
                    "user_id": log.user_id,
                    "character_id": log.character_id,
                    "start_time": log.start_time.isoformat() if log.start_time else None,
                    "end_time": log.end_time.isoformat() if log.end_time else None,
                    "duration_ms": log.duration_ms,
                    "is_normal_end": log.is_normal_end,
                    "end_reason": log.end_reason,
                    "created_at": log.created_at.isoformat() if log.created_at else None,
                }
                if include_details:
                    item["request_detail"] = log.request_detail
                    item["response_detail"] = log.response_detail
                    item["user_emotion"] = log.user_emotion
                    item["assistant_emotion"] = log.assistant_emotion
                items.append(item)

            return items

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
        async with get_log_session() as session:
            query = select(DialogueInteractionLog).where(
                DialogueInteractionLog.conversation_id == conversation_id
            ).order_by(DialogueInteractionLog.start_time.asc()).limit(limit).offset(offset)

            result = await session.exec(query)
            logs = result.all()

            items = []
            for log in logs:
                item = {
                    "id": log.id,
                    "conversation_id": log.conversation_id,
                    "user_id": log.user_id,
                    "character_id": log.character_id,
                    "start_time": log.start_time.isoformat() if log.start_time else None,
                    "end_time": log.end_time.isoformat() if log.end_time else None,
                    "duration_ms": log.duration_ms,
                    "is_normal_end": log.is_normal_end,
                    "end_reason": log.end_reason,
                    "created_at": log.created_at.isoformat() if log.created_at else None,
                }
                if include_details:
                    item["request_detail"] = log.request_detail
                    item["response_detail"] = log.response_detail
                    item["user_emotion"] = log.user_emotion
                    item["assistant_emotion"] = log.assistant_emotion
                items.append(item)

            return items

    @staticmethod
    async def get_interaction_by_id(log_id: int) -> dict[str, Any] | None:
        """根据ID查询单条对话交互记录"""
        async with get_log_session() as session:
            result = await session.exec(
                select(DialogueInteractionLog).where(DialogueInteractionLog.id == log_id)
            )
            log = result.first()

            if log:
                return {
                    "id": log.id,
                    "conversation_id": log.conversation_id,
                    "user_id": log.user_id,
                    "character_id": log.character_id,
                    "request_detail": log.request_detail,
                    "response_detail": log.response_detail,
                    "start_time": log.start_time.isoformat() if log.start_time else None,
                    "end_time": log.end_time.isoformat() if log.end_time else None,
                    "duration_ms": log.duration_ms,
                    "is_normal_end": log.is_normal_end,
                    "end_reason": log.end_reason,
                    "user_emotion": log.user_emotion,
                    "assistant_emotion": log.assistant_emotion,
                    "trace_id": log.trace_id,
                    "created_at": log.created_at.isoformat() if log.created_at else None,
                }
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
        async with get_log_session() as session:
            if user_id:
                result = await session.exec(
                    select(DialogueInteractionLog).where(DialogueInteractionLog.user_id == user_id)
                )
                logs = result.all()
                for log in logs:
                    await session.delete(log)
            else:
                result = await session.exec(select(DialogueInteractionLog))
                logs = result.all()
                for log in logs:
                    await session.delete(log)

            await session.commit()
            deleted_count = len(logs)
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
        async with get_log_session() as session:
            if user_id:
                count_result = await session.exec(
                    select(func.count(DialogueInteractionLog.id)).where(
                        DialogueInteractionLog.user_id == user_id
                    )
                )
                total_count = count_result.one()

                duration_result = await session.exec(
                    select(func.sum(DialogueInteractionLog.duration_ms)).where(
                        DialogueInteractionLog.user_id == user_id
                    )
                )
                total_duration_ms = duration_result.one() or 0
            else:
                count_result = await session.exec(select(func.count(DialogueInteractionLog.id)))
                total_count = count_result.one()

                duration_result = await session.exec(select(func.sum(DialogueInteractionLog.duration_ms)))
                total_duration_ms = duration_result.one() or 0

            return {
                "total_interactions": total_count,
                "total_duration_ms": total_duration_ms,
                "user_id": user_id,
            }


dialogue_log_service = DialogueLogService()
