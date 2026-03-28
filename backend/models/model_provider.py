"""
Model Provider Model - 模型提供商模型
存储支持的 AI 模型提供商信息
"""

from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class ModelProviderBase(SQLModel):
    """模型提供商基础模型"""
    model_config = {
        'protected_namespaces': ()
    }
    name: str = Field(index=True, unique=True)  # 内部标识，如 deepseek
    display_name: str  # 显示名称，如 DeepSeek
    description: Optional[str] = None


class ModelProvider(ModelProviderBase, table=True):
    """模型提供商表模型"""
    __tablename__ = "model_providers"

    id: str = Field(primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ModelProviderCreate(ModelProviderBase):
    """创建模型提供商模型"""
    id: str


class ModelProviderUpdate(SQLModel):
    """更新模型提供商模型"""
    model_config = {
        'protected_namespaces': ()
    }
    display_name: Optional[str] = None
    description: Optional[str] = None
