"""
Conversation Service - 会话管理服务
管理用户会话的创建、查询、更新和删除
支持角色卡的多会话机制（分身）
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlmodel import select, text

from ..core.logging import get_logger
from ..database_sqlmodel import get_session
from ..models import Conversation, ConversationLog, CharacterCard

logger = get_logger(__name__)


class ConversationService:
    """会话管理服务"""

    @staticmethod
    async def create_conversation(
        user_id: str,
        character_id: str | None = None,
        title: str | None = None,
        conversation_id: str | None = None,
    ) -> dict[str, Any]:
        """
        创建新会话

        Args:
            user_id: 用户ID
            character_id: 绑定的角色卡ID
            title: 会话标题（可选）
            conversation_id: 指定会话ID（可选，默认自动生成）

        Returns:
            新创建的会话对象
        """
        if not conversation_id:
            conversation_id = str(uuid.uuid4())

        async with get_session() as session:
            new_conversation = Conversation(
                id=conversation_id,
                user_id=user_id,
                character_id=character_id,
                title=title or "新对话",
                is_active=True
            )
            session.add(new_conversation)
            await session.commit()

        logger.info(
            "Created conversation: id=%s, user=%s, character=%s",
            conversation_id,
            user_id,
            character_id,
        )

        return {
            "id": conversation_id,
            "user_id": user_id,
            "character_id": character_id,
            "title": title or "新对话",
            "is_active": True,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

    @staticmethod
    async def get_or_create_conversation(
        user_id: str,
        conversation_id: str | None,
        character_id: str | None = None,
    ) -> str:
        """
        获取现有会话或创建新会话

        Args:
            user_id: 用户ID
            conversation_id: 现有会话ID（可选）
            character_id: 角色卡ID（创建新会话时使用）

        Returns:
            会话ID
        """
        if conversation_id:
            async with get_session() as session:
                result = await session.exec(
                    select(Conversation)
                    .where(Conversation.id == conversation_id)
                    .where(Conversation.user_id == user_id)
                    .where(Conversation.is_active == True)
                )
                conversation = result.first()
                if conversation:
                    return conversation_id

        result = await ConversationService.create_conversation(user_id, character_id)
        return result["id"]

    @staticmethod
    async def get_conversation(conversation_id: str) -> dict[str, Any] | None:
        """获取单个会话详情（仅返回活跃会话）"""
        async with get_session() as session:
            result = await session.exec(
                select(Conversation)
                .where(Conversation.id == conversation_id)
                .where(Conversation.is_active == True)
            )
            conversation = result.first()
            if conversation:
                return {
                    "id": conversation.id,
                    "user_id": conversation.user_id,
                    "character_id": conversation.character_id,
                    "title": conversation.title,
                    "created_at": conversation.created_at.isoformat() if conversation.created_at else None,
                    "updated_at": conversation.updated_at.isoformat() if conversation.updated_at else None,
                    "is_active": conversation.is_active
                }
            return None

    @staticmethod
    async def get_user_conversations(
        user_id: str,
        limit: int = 20,
        offset: int = 0,
        character_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        获取用户的会话列表

        Args:
            user_id: 用户ID
            limit: 返回数量限制
            offset: 偏移量
            character_id: 可选，筛选特定角色卡的会话
        """
        async with get_session() as session:
            query = (
                select(Conversation, CharacterCard.nickname, CharacterCard.formal_name)
                .outerjoin(CharacterCard, Conversation.character_id == CharacterCard.id)
                .where(Conversation.user_id == user_id)
                .where(Conversation.is_active == True)
            )

            if character_id:
                query = query.where(Conversation.character_id == character_id)

            query = query.order_by(Conversation.updated_at.desc()).limit(limit).offset(offset)

            result = await session.exec(query)
            rows = result.all()

            conversations = []
            for conv, nickname, formal_name in rows:
                conversations.append({
                    "id": conv.id,
                    "user_id": conv.user_id,
                    "character_id": conv.character_id,
                    "title": conv.title,
                    "created_at": conv.created_at.isoformat() if conv.created_at else None,
                    "updated_at": conv.updated_at.isoformat() if conv.updated_at else None,
                    "character_name": nickname,
                    "formal_name": formal_name
                })

            return conversations

    @staticmethod
    async def get_conversations_by_character(
        user_id: str,
        character_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """
        获取特定角色卡的所有会话（分身列表）

        Args:
            user_id: 用户ID
            character_id: 角色卡ID
            limit: 返回数量限制
            offset: 偏移量
        """
        return await ConversationService.get_user_conversations(
            user_id=user_id,
            limit=limit,
            offset=offset,
            character_id=character_id,
        )

    @staticmethod
    async def update_conversation_timestamp(conversation_id: str) -> None:
        """更新会话的最后活动时间"""
        async with get_session() as session:
            result = await session.exec(select(Conversation).where(Conversation.id == conversation_id))
            conversation = result.first()
            if conversation:
                conversation.updated_at = datetime.now(UTC)
                await session.commit()

    @staticmethod
    async def update_conversation_title(conversation_id: str, title: str) -> dict[str, Any] | None:
        """更新会话标题"""
        async with get_session() as session:
            result = await session.exec(select(Conversation).where(Conversation.id == conversation_id))
            conversation = result.first()
            if conversation:
                conversation.title = title
                conversation.updated_at = datetime.now(UTC)
                await session.commit()
                return {
                    "id": conversation.id,
                    "user_id": conversation.user_id,
                    "character_id": conversation.character_id,
                    "title": conversation.title,
                    "created_at": conversation.created_at.isoformat() if conversation.created_at else None,
                    "updated_at": conversation.updated_at.isoformat() if conversation.updated_at else None,
                    "is_active": conversation.is_active
                }
            return None

    @staticmethod
    async def deactivate_conversation(conversation_id: str) -> None:
        """软删除会话（标记为非活跃）"""
        async with get_session() as session:
            result = await session.exec(select(Conversation).where(Conversation.id == conversation_id))
            conversation = result.first()
            if conversation:
                conversation.is_active = False
                conversation.updated_at = datetime.now(UTC)
                await session.commit()

    @staticmethod
    async def delete_conversations_by_character(character_id: str) -> int:
        """
        删除特定角色卡关联的所有会话及其消息日志（级联删除）

        Args:
            character_id: 角色卡ID

        Returns:
            被删除的会话数量
        """
        async with get_session() as session:
            result = await session.exec(
                select(Conversation).where(Conversation.character_id == character_id)
            )
            conversations = result.all()

            deleted_count = 0
            for conv in conversations:
                await session.execute(
                    text("DELETE FROM conversation_logs WHERE conversation_id = :conv_id"),
                    {"conv_id": conv.id}
                )
                await session.execute(
                    text("DELETE FROM dialogue_interaction_logs WHERE conversation_id = :conv_id"),
                    {"conv_id": conv.id}
                )
                await session.delete(conv)
                deleted_count += 1

            await session.commit()
            logger.info(
                "Deleted %d conversations cascade by character_id=%s",
                deleted_count,
                character_id,
            )
            return deleted_count

    @staticmethod
    async def delete_conversation(conversation_id: str) -> None:
        """彻底删除会话及其关联的对话日志"""
        async with get_session() as session:
            await session.execute(
                text("DELETE FROM dialogue_interaction_logs WHERE conversation_id = :conv_id"),
                {"conv_id": conversation_id}
            )

            result = await session.exec(select(Conversation).where(Conversation.id == conversation_id))
            conversation = result.first()
            if conversation:
                await session.delete(conversation)

            await session.commit()

    @staticmethod
    async def get_conversation_history(
        conversation_id: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """
        获取会话的历史对话记录

        Args:
            conversation_id: 会话ID
            limit: 返回数量限制（默认20条）

        Returns:
            对话记录列表，每条包含 role 和 content，按时间正序排列
        """
        async with get_session() as session:
            result = await session.exec(
                select(ConversationLog)
                .where(ConversationLog.conversation_id == conversation_id)
                .order_by(ConversationLog.timestamp.desc())
                .limit(limit)
            )
            logs = result.all()

            messages = []
            for log in reversed(logs):
                messages.append({
                    "role": log.role,
                    "content": log.content,
                    "timestamp": log.timestamp.isoformat() if log.timestamp else None
                })

            return messages


conversation_service = ConversationService()
