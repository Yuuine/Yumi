"""
Dialogue Interaction Log Model - 对话交互日志模型
存储详细的对话交互信息，用于分析和优化
"""

from datetime import datetime
from typing import Optional, Any
from sqlmodel import Field, SQLModel, Column, JSON


class DialogueInteractionLog(SQLModel, table=True):
    """对话交互日志表模型"""
    __tablename__ = "dialogue_interaction_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: Optional[str] = Field(default=None, index=True)
    user_id: str = Field(index=True)
    character_id: Optional[str] = Field(default=None, index=True)
    request_detail: dict[str, Any] = Field(sa_column=Column(JSON))
    response_detail: Optional[dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    start_time: datetime = Field(index=True)
    end_time: Optional[datetime] = None
    duration_ms: Optional[int] = None
    is_normal_end: bool = Field(default=True)
    end_reason: str = Field(default="")
    user_emotion: Optional[dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    assistant_emotion: Optional[dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    trace_id: Optional[str] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DialogueInteractionLogCreate(SQLModel):
    """创建对话交互日志模型"""
    model_config = {
        'protected_namespaces': ()
    }
    conversation_id: Optional[str] = None
    user_id: str
    character_id: Optional[str] = None
    request_detail: dict[str, Any]
    response_detail: Optional[dict[str, Any]] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[int] = None
    is_normal_end: bool = True
    end_reason: str = ""
    user_emotion: Optional[dict[str, Any]] = None
    assistant_emotion: Optional[dict[str, Any]] = None
    trace_id: Optional[str] = None
