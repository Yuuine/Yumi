"""
Audit Log Model - 审计日志模型
存储用户操作审计日志
"""

from datetime import datetime
from typing import Optional, Any
from sqlmodel import Field, SQLModel, Column, JSON


class AuditLog(SQLModel, table=True):
    """审计日志表模型"""
    __tablename__ = "audit_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(index=True)
    user_id: Optional[str] = Field(default=None, index=True)
    action: str = Field(index=True)
    resource_type: str = Field(index=True)
    resource_id: Optional[str] = Field(default=None, index=True)
    result: str
    client_ip: Optional[str] = None
    details: Optional[dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AuditLogCreate(SQLModel):
    """创建审计日志模型"""
    model_config = {
        'protected_namespaces': ()
    }
    timestamp: datetime
    user_id: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    result: str
    client_ip: Optional[str] = None
    details: Optional[dict[str, Any]] = None
