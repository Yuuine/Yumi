"""
Audit Log Model - 审计日志模型
"""

from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class AuditLogBase(SQLModel):
    """审计日志基础模型"""
    user_id: Optional[str] = Field(default=None, index=True)
    action: str = Field(index=True)
    resource_type: str
    resource_id: Optional[str] = None
    result: str
    client_ip: Optional[str] = None
    details: Optional[str] = None


class AuditLog(AuditLogBase, table=True):
    """审计日志表模型"""
    __tablename__ = "audit_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: str = Field(index=True)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
