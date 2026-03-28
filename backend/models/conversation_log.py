"""
Conversation Log Model - 对话消息模型
存储对话中的消息记录
"""

from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class ConversationLogBase(SQLModel):
    """对话消息基础模型"""
    model_config = {
        'protected_namespaces': ()
    }
    conversation_id: str = Field(index=True, foreign_key="conversations.id")
    user_id: str = Field(index=True, foreign_key="users.id")
    role: str = Field(default="assistant")  # user / assistant
    content: str
    emotion_valence: Optional[float] = None  # 情感效价 -1 ~ 1
    emotion_arousal: Optional[float] = None  # 情感唤醒度 0 ~ 1
    embedding_id: Optional[str] = None  # 向量嵌入ID
    storage_status: str = Field(default="pending")  # pending / stored / failed
    storage_attempts: int = Field(default=0)
    storage_error: Optional[str] = None


class ConversationLog(ConversationLogBase, table=True):
    """对话消息表模型"""
    __tablename__ = "conversation_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
    stored_at: Optional[datetime] = None


class ConversationLogCreate(SQLModel):
    """创建对话消息模型"""
    model_config = {
        'protected_namespaces': ()
    }
    conversation_id: str
    user_id: str
    role: str
    content: str
    emotion_valence: Optional[float] = None
    emotion_arousal: Optional[float] = None
    embedding_id: Optional[str] = None


class ConversationLogResponse(ConversationLogBase):
    """对话消息响应模型"""
    id: int
    timestamp: datetime
    stored_at: Optional[datetime] = None
