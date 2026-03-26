"""
Setting Model - 设置模型
"""

from datetime import datetime
from sqlmodel import Field, SQLModel


class SettingBase(SQLModel):
    """设置基础模型"""
    key: str = Field(primary_key=True)
    value: str


class Setting(SettingBase, table=True):
    """设置表模型"""
    __tablename__ = "settings"

    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": datetime.utcnow})
