"""
Logging System - 结构化日志系统

- 结构化 JSON 日志格式
- 请求追踪 (request_id)
- 敏感信息过滤
- 日志文件轮转
- 自动归档清理
"""
from __future__ import annotations

import json
import logging
import os
import re
import sys
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone, timedelta
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import Any

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)

BEIJING_TZ = timezone(timedelta(hours=8))


SENSITIVE_PATTERNS = [
    (re.compile(r"(api[_-]?key|apikey|token|secret|password|pwd)['\"]?\s*[:=]\s*['\"]?([^'\"\\s,}]+)", re.IGNORECASE), r"\1=***REDACTED***"),
    (re.compile(r"(Bearer\s+)[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE), r"\1***REDACTED***"),
    (re.compile(r"(sk-[a-zA-Z0-9]{20,})"), r"sk-***REDACTED***"),
]


def filter_sensitive_info(message: str) -> str:
    """过滤敏感信息"""
    result = message
    for pattern, replacement in SENSITIVE_PATTERNS:
        result = pattern.sub(replacement, result)
    return result


class StructuredFormatter(logging.Formatter):
    """结构化 JSON 日志格式化器"""

    def __init__(self, app_name: str = "yumi", app_version: str = "1.0.0", environment: str = "production"):
        super().__init__()
        self.app_name = app_name
        self.app_version = app_version
        self.environment = environment

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(BEIJING_TZ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": filter_sensitive_info(record.getMessage()),
            "request_id": request_id_var.get(),
        }

        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id

        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data

        log_data["source"] = {
            "app": self.app_name,
            "version": self.app_version,
            "environment": self.environment,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False, default=str)


class HumanReadableFormatter(logging.Formatter):
    """人类可读格式（开发环境）"""

    def format(self, record: logging.LogRecord) -> str:
        request_id = request_id_var.get()
        request_part = f"[{request_id[:8]}] " if request_id else ""
        message = filter_sensitive_info(record.getMessage())
        timestamp = datetime.now(BEIJING_TZ).strftime("%Y-%m-%d %H:%M:%S")
        return f"{timestamp} | {record.levelname:8} | {record.name:30} | {request_part}{message}"


class SensitiveFilter(logging.Filter):
    """敏感信息过滤器"""

    def filter(self, record: logging.LogRecord) -> bool:
        if record.msg:
            record.msg = filter_sensitive_info(str(record.msg))
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: filter_sensitive_info(str(v)) if isinstance(v, str) else v for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(filter_sensitive_info(str(arg)) if isinstance(arg, str) else arg for arg in record.args)
        return True


class YumiLogger:
    """Yumi 日志管理器"""

    _initialized = False
    _log_dir: Path | None = None

    @classmethod
    def setup(
        cls,
        level: str = "INFO",
        log_dir: str | Path | None = None,
        app_name: str = "yumi",
        app_version: str = "1.0.0",
        environment: str = "production",
        max_file_size: int = 10 * 1024 * 1024,
        backup_count: int = 5,
        enable_file_log: bool = True,
        enable_json_format: bool = False,
    ) -> None:
        """
        初始化日志系统

        Args:
            level: 日志级别
            log_dir: 日志目录
            app_name: 应用名称
            app_version: 应用版本
            environment: 运行环境
            max_file_size: 单个日志文件最大大小 (字节)
            backup_count: 保留的日志文件数量
            enable_file_log: 是否启用文件日志
            enable_json_format: 是否使用 JSON 格式
        """
        if cls._initialized:
            return

        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        root_logger.addFilter(SensitiveFilter())

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        if enable_json_format:
            console_handler.setFormatter(StructuredFormatter(app_name, app_version, environment))
        else:
            console_handler.setFormatter(HumanReadableFormatter())
        root_logger.addHandler(console_handler)

        if enable_file_log and log_dir:
            cls._log_dir = Path(log_dir)
            cls._log_dir.mkdir(parents=True, exist_ok=True)

            file_handler = RotatingFileHandler(
                filename=cls._log_dir / "app.log",
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding="utf-8",
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(StructuredFormatter(app_name, app_version, environment))
            root_logger.addHandler(file_handler)

            error_handler = RotatingFileHandler(
                filename=cls._log_dir / "error.log",
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding="utf-8",
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(StructuredFormatter(app_name, app_version, environment))
            root_logger.addHandler(error_handler)

        cls._initialized = True

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """获取指定名称的日志记录器"""
        return logging.getLogger(name)

    @classmethod
    def set_request_id(cls, request_id: str | None = None) -> str:
        """设置当前请求 ID"""
        rid = request_id or str(uuid.uuid4())
        request_id_var.set(rid)
        return rid

    @classmethod
    def clear_request_id(cls) -> None:
        """清除当前请求 ID"""
        request_id_var.set(None)

    @classmethod
    def get_log_dir(cls) -> Path | None:
        """获取日志目录"""
        return cls._log_dir


def get_logger(name: str) -> logging.Logger:
    """获取日志记录器的便捷函数"""
    return YumiLogger.get_logger(name)


def log_with_context(
    logger: logging.Logger,
    level: int,
    message: str,
    user_id: str | None = None,
    **extra: Any,
) -> None:
    """带上下文信息的日志记录"""
    record = logger.makeRecord(
        logger.name,
        level,
        "",
        0,
        message,
        (),
        None,
    )
    if user_id:
        record.user_id = user_id
    if extra:
        record.extra_data = extra
    logger.handle(record)
