"""
Memory Summary Model - 记忆摘要模型
"""

from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class MemorySummaryBase(SQLModel):
    """记忆摘要基础模型"""
    model_config = {
        'protected_namespaces': ()
    }
    user_id: str = Field(index=True)
    conversation_id: Optional[str] = Field(default=None, index=True)
    summary: str
    turn_count: int = Field(default=0)


class MemorySummary(MemorySummaryBase, table=True):
    """记忆摘要表模型"""
    __tablename__ = "memory_summaries"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
