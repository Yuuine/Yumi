"""
Setting Model - 系统设置模型
存储系统级配置
"""

from datetime import datetime
from sqlmodel import Field, SQLModel


class Setting(SQLModel, table=True):
    """系统设置表模型"""
    __tablename__ = "settings"

    key: str = Field(primary_key=True)
    value: str
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": datetime.utcnow})


class SettingCreate(SQLModel):
    """创建设置模型"""
    model_config = {
        'protected_namespaces': ()
    }
    key: str
    value: str


class SettingUpdate(SQLModel):
    """更新设置模型"""
    model_config = {
        'protected_namespaces': ()
    }
    value: str
