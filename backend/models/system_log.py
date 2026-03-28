"""
System Log Model - 系统日志模型
存储系统运行日志
"""

from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class SystemLog(SQLModel, table=True):
    """系统日志表模型"""
    __tablename__ = "system_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(index=True)
    level: str = Field(index=True)
    event_type: str = Field(index=True)
    trace_id: Optional[str] = Field(default=None, index=True)
    user_id: Optional[str] = Field(default=None, index=True)
    session_id: Optional[str] = None
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SystemLogCreate(SQLModel):
    """创建系统日志模型"""
    model_config = {
        'protected_namespaces': ()
    }
    timestamp: datetime
    level: str
    event_type: str
    trace_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    content: str
