"""
异常处理模块
定义统一的异常类型和错误响应格式
"""
from __future__ import annotations

from typing import Any


class YumiException(Exception):
    """Yumi 基础异常类"""

    def __init__(
        self,
        message: str,
        code: str = "UNKNOWN_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "code": self.code,
            "message": self.message,
        }
        if self.details:
            result["details"] = self.details
        return result


class LLMException(YumiException):
    """LLM 服务异常"""

    def __init__(
        self,
        message: str = "LLM 服务调用失败",
        code: str = "LLM_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code, details)


class MemoryException(YumiException):
    """记忆引擎异常"""

    def __init__(
        self,
        message: str = "记忆引擎操作失败",
        code: str = "MEMORY_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code, details)


class DatabaseException(YumiException):
    """数据库异常"""

    def __init__(
        self,
        message: str = "数据库操作失败",
        code: str = "DATABASE_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code, details)


class ValidationException(YumiException):
    """数据验证异常"""

    def __init__(
        self,
        message: str = "数据验证失败",
        code: str = "VALIDATION_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code, details)


class NotFoundException(YumiException):
    """资源不存在异常"""

    def __init__(
        self,
        message: str = "请求的资源不存在",
        code: str = "NOT_FOUND",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code, details)


class AuthenticationException(YumiException):
    """认证异常"""

    def __init__(
        self,
        message: str = "认证失败",
        code: str = "AUTHENTICATION_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code, details)


class RateLimitException(YumiException):
    """请求频率限制异常"""

    def __init__(
        self,
        message: str = "请求过于频繁，请稍后再试",
        code: str = "RATE_LIMIT_EXCEEDED",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code, details)


class NoActiveModelException(YumiException):
    """没有可用模型异常"""

    def __init__(
        self,
        message: str = "没有可用的模型，请先在模型管理中添加并启用一个模型",
        code: str = "NO_ACTIVE_MODEL",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code, details)
