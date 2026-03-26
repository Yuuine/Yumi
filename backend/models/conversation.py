"""
Conversation Model - 会话模型
"""

from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class ConversationBase(SQLModel):
    """会话基础模型"""
    user_id: str = Field(index=True)
    character_id: Optional[str] = Field(default=None, index=True)
    title: Optional[str] = None
    is_active: bool = Field(default=True, index=True)


class Conversation(ConversationBase, table=True):
    """会话表模型"""
    __tablename__ = "conversations"

    id: str = Field(primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": datetime.utcnow})


class ConversationCreate(ConversationBase):
    """创建会话模型"""
    id: str


class ConversationUpdate(SQLModel):
    """更新会话模型"""
    character_id: Optional[str] = None
    title: Optional[str] = None
    is_active: Optional[bool] = None
