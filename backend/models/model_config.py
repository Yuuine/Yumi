"""
Model Config Model - 模型配置模型
基于新数据库设计，account_id 必须关联到用户
"""

from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class ModelConfigBase(SQLModel):
    """模型配置基础模型"""
    model_config = {
        'protected_namespaces': ()
    }
    account_id: str = Field(index=True, foreign_key="users.id")
    provider_id: str = Field(index=True, foreign_key="model_providers.id")
    name: str
    base_url: str
    api_key: Optional[str] = None  # 加密存储
    model_name: str
    custom_model_name: Optional[str] = None
    model_type: str = Field(default="text")
    max_tokens: int = Field(default=4096)
    temperature: float = Field(default=0.85)
    is_enabled: bool = Field(default=False, index=True)
    is_tested: bool = Field(default=False)
    test_status: str = Field(default="untested")  # untested / success / failed
    last_test_at: Optional[datetime] = None
    last_test_message: Optional[str] = None
    edit_count: int = Field(default=0)


class ModelConfig(ModelConfigBase, table=True):
    """模型配置表模型"""
    __tablename__ = "model_configs"

    id: str = Field(primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": datetime.utcnow})


class ModelConfigCreate(SQLModel):
    """创建模型配置模型"""
    model_config = {
        'protected_namespaces': ()
    }
    id: str
    account_id: str
    provider_id: str
    name: str
    base_url: str
    api_key: Optional[str] = None
    model_name: str
    custom_model_name: Optional[str] = None
    model_type: str = "text"
    max_tokens: int = 4096
    temperature: float = 0.85


class ModelConfigUpdate(SQLModel):
    """更新模型配置模型"""
    model_config = {
        'protected_namespaces': ()
    }
    name: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model_name: Optional[str] = None
    custom_model_name: Optional[str] = None
    model_type: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    is_enabled: Optional[bool] = None
    is_tested: Optional[bool] = None
    test_status: Optional[str] = None
    last_test_at: Optional[datetime] = None
    last_test_message: Optional[str] = None
    edit_count: Optional[int] = None
