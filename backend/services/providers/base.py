"""
模型提供商配置基础模型

定义模型配置的数据结构，用于解析和存储 YAML 配置文件。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ModelInfo:
    """模型基本信息"""
    name: str
    provider: str
    description: str = ""


@dataclass
class RequestConfig:
    """请求参数配置"""
    defaults: dict[str, Any] = field(default_factory=dict)
    supported_fields: list[str] = field(default_factory=list)
    unsupported_fields: list[str] = field(default_factory=list)
    special: dict[str, Any] = field(default_factory=dict)


@dataclass
class ResponseConfig:
    """响应解析配置"""
    content_field: str = "choices[0].message.content"
    reasoning_field: str | None = None


@dataclass
class StreamConfig:
    """流式响应配置"""
    format: str = "sse"
    done_signal: str = "[DONE]"
    content_field: str = "choices[0].delta.content"


@dataclass
class ApiConfig:
    """API 配置"""
    endpoint_suffix: str = "/chat/completions"
    auth_type: str = "bearer"


@dataclass
class ProviderModelConfig:
    """提供商模型完整配置"""
    model: ModelInfo
    api: ApiConfig = field(default_factory=ApiConfig)
    request: RequestConfig = field(default_factory=RequestConfig)
    response: ResponseConfig = field(default_factory=ResponseConfig)
    stream: StreamConfig = field(default_factory=StreamConfig)

    def get_default(self, field_name: str, default_value: Any = None) -> Any:
        """获取字段的默认值"""
        return self.request.defaults.get(field_name, default_value)

    def is_field_supported(self, field_name: str) -> bool:
        """检查字段是否被支持"""
        if field_name in self.request.unsupported_fields:
            return False
        if self.request.supported_fields:
            return field_name in self.request.supported_fields
        return True

    def should_remove_field(self, field_name: str) -> bool:
        """检查字段是否应该被移除"""
        return field_name in self.request.unsupported_fields
