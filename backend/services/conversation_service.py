"""
Conversation Service - 会话管理服务
管理用户会话的创建、查询、更新和删除
支持角色卡的多会话机制（分身）
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from ..core.logging import get_logger
from ..database import get_db

logger = get_logger(__name__)


class ConversationService:
    """会话管理服务"""

    @staticmethod
    async def create_conversation(
        user_id: str,
        character_id: str | None = None,
        title: str | None = None,
    ) -> str:
        """
        创建新会话

        Args:
            user_id: 用户ID
            character_id: 绑定的角色卡ID
            title: 会话标题（可选）

        Returns:
            新创建的会话ID
        """
        conversation_id = str(uuid.uuid4())
        now = datetime.now(UTC).isoformat()

        async with get_db() as db:
            await db.execute(
                """INSERT INTO conversations (id, user_id, character_id, title, created_at, updated_at, is_active)
                   VALUES (?, ?, ?, ?, ?, ?, 1)""",
                (conversation_id, user_id, character_id, title, now, now),
            )
            await db.commit()

        logger.info(
            "Created conversation: id=%s, user=%s, character=%s",
            conversation_id,
            user_id,
            character_id,
        )

        return conversation_id

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
            async with get_db() as db:
                cursor = await db.execute(
                    """SELECT id FROM conversations WHERE id = ? AND user_id = ? AND is_active = 1""",
                    (conversation_id, user_id),
                )
                row = await cursor.fetchone()
                if row:
                    return conversation_id

        return await ConversationService.create_conversation(user_id, character_id)

    @staticmethod
    async def get_conversation(conversation_id: str) -> dict[str, Any] | None:
        """获取单个会话详情"""
        async with get_db() as db:
            cursor = await db.execute(
                """SELECT id, user_id, character_id, title, created_at, updated_at, is_active
                   FROM conversations WHERE id = ?""",
                (conversation_id,),
            )
            row = await cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
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
        base_query = """SELECT c.id, c.user_id, c.character_id, c.title, c.created_at, c.updated_at,
                               cc.nickname as character_name, cc.formal_name
                        FROM conversations c
                        LEFT JOIN character_cards cc ON c.character_id = cc.id
                        WHERE c.user_id = ? AND c.is_active = 1"""

        params: list[Any] = [user_id]

        if character_id:
            base_query += " AND c.character_id = ?"
            params.append(character_id)

        base_query += " ORDER BY c.updated_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        async with get_db() as db:
            cursor = await db.execute(base_query, params)
            rows = await cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]

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
        now = datetime.now(UTC).isoformat()
        async with get_db() as db:
            await db.execute(
                """UPDATE conversations SET updated_at = ? WHERE id = ?""",
                (now, conversation_id),
            )
            await db.commit()

    @staticmethod
    async def update_conversation_title(conversation_id: str, title: str) -> None:
        """更新会话标题"""
        now = datetime.now(UTC).isoformat()
        async with get_db() as db:
            await db.execute(
                """UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?""",
                (title, now, conversation_id),
            )
            await db.commit()

    @staticmethod
    async def deactivate_conversation(conversation_id: str) -> None:
        """软删除会话（标记为非活跃）"""
        now = datetime.now(UTC).isoformat()
        async with get_db() as db:
            await db.execute(
                """UPDATE conversations SET is_active = 0, updated_at = ? WHERE id = ?""",
                (now, conversation_id),
            )
            await db.commit()

    @staticmethod
    async def delete_conversation(conversation_id: str) -> None:
        """彻底删除会话及其关联的对话日志"""
        async with get_db() as db:
            await db.execute(
                """DELETE FROM dialogue_interaction_logs WHERE conversation_id = ?""",
                (conversation_id,),
            )
            await db.execute(
                """DELETE FROM conversations WHERE id = ?""",
                (conversation_id,),
            )
            await db.commit()

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
        async with get_db() as db:
            cursor = await db.execute(
                """SELECT role, content, timestamp 
                   FROM conversation_logs 
                   WHERE conversation_id = ? 
                   ORDER BY timestamp DESC 
                   LIMIT ?""",
                (conversation_id, limit),
            )
            rows = await cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            messages = [dict(zip(columns, row)) for row in rows]
            messages.reverse()
            return messages


conversation_service = ConversationService()
