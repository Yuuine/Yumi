"""
User Model - 用户模型
"""

from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class UserBase(SQLModel):
    """用户基础模型"""
    nickname: Optional[str] = Field(default=None, unique=True, index=True)
    password_hash: Optional[str] = Field(default=None)
    role_name: str = Field(default="Yumi")
    preferences_json: Optional[str] = Field(default=None)


class User(UserBase, table=True):
    """用户表模型"""
    __tablename__ = "users"

    id: str = Field(primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": datetime.utcnow})


class UserCreate(UserBase):
    """创建用户模型"""
    id: str


class UserUpdate(SQLModel):
    """更新用户模型"""
    nickname: Optional[str] = None
    password_hash: Optional[str] = None
    role_name: Optional[str] = None
    preferences_json: Optional[str] = None
