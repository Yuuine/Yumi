"""
System Log Model - 系统日志模型
"""

from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class SystemLogBase(SQLModel):
    """系统日志基础模型"""
    level: str
    event_type: str
    trace_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    content: str


class SystemLog(SystemLogBase, table=True):
    """系统日志表模型"""
    __tablename__ = "system_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: str = Field(index=True)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
