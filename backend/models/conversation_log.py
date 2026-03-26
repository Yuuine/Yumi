"""
Conversation Log Model - 会话日志模型
"""

from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class ConversationLogBase(SQLModel):
    """会话日志基础模型"""
    conversation_id: Optional[str] = Field(default=None, index=True)
    user_id: str = Field(index=True)
    role: str
    content: str
    emotion_valence: Optional[float] = None
    emotion_arousal: Optional[float] = None
    embedding_id: Optional[str] = None
    storage_status: str = Field(default="pending")
    storage_attempts: int = Field(default=0)
    storage_error: Optional[str] = None
    stored_at: Optional[datetime] = None


class ConversationLog(ConversationLogBase, table=True):
    """会话日志表模型"""
    __tablename__ = "conversation_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)


class ConversationLogCreate(ConversationLogBase):
    """创建会话日志模型"""
    pass
