"""
Conversation Model - 会话模型
基于新数据库设计，添加软删除支持
角色卡与会话为强关联（级联删除通过代码逻辑实现）
"""

from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class ConversationBase(SQLModel):
    """会话基础模型"""
    model_config = {
        'protected_namespaces': ()
    }
    user_id: str = Field(index=True, foreign_key="users.id")
    character_id: Optional[str] = Field(default=None, index=True, foreign_key="character_cards.id")
    title: Optional[str] = None
    is_active: bool = Field(default=True, index=True)


class Conversation(ConversationBase, table=True):
    """会话表模型"""
    __tablename__ = "conversations"

    id: str = Field(primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": datetime.utcnow})
    deleted_at: Optional[datetime] = None  # 软删除时间

    def is_deleted(self) -> bool:
        """检查会话是否已删除"""
        return self.deleted_at is not None


class ConversationCreate(SQLModel):
    """创建会话模型"""
    model_config = {
        'protected_namespaces': ()
    }
    id: str
    user_id: str
    character_id: Optional[str] = None
    title: Optional[str] = None
    is_active: bool = True


class ConversationUpdate(SQLModel):
    """更新会话模型"""
    model_config = {
        'protected_namespaces': ()
    }
    character_id: Optional[str] = None
    title: Optional[str] = None
    is_active: Optional[bool] = None


class ConversationResponse(ConversationBase):
    """会话响应模型"""
    id: str
    created_at: datetime
    updated_at: datetime
