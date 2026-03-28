"""
User Model - 用户模型
基于新数据库设计，添加软删除支持
"""

from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class UserBase(SQLModel):
    """用户基础模型"""
    model_config = {
        'protected_namespaces': ()
    }
    nickname: str = Field(index=True, unique=True)
    role_name: str = Field(default="Yumi")
    preferences_json: Optional[str] = None


class User(UserBase, table=True):
    """用户表模型"""
    __tablename__ = "users"

    id: str = Field(primary_key=True)
    password_hash: str  # 密码哈希，bcrypt加密
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": datetime.utcnow})
    deleted_at: Optional[datetime] = None  # 软删除时间

    def is_deleted(self) -> bool:
        """检查用户是否已删除"""
        return self.deleted_at is not None


class UserCreate(SQLModel):
    """创建用户模型"""
    model_config = {
        'protected_namespaces': ()
    }
    id: str
    nickname: str
    password_hash: str
    role_name: str = "Yumi"
    preferences_json: Optional[str] = None


class UserUpdate(SQLModel):
    """更新用户模型"""
    model_config = {
        'protected_namespaces': ()
    }
    nickname: Optional[str] = None
    role_name: Optional[str] = None
    preferences_json: Optional[str] = None
    password_hash: Optional[str] = None


class UserResponse(UserBase):
    """用户响应模型（不包含敏感信息）"""
    id: str
    created_at: datetime
    updated_at: datetime
