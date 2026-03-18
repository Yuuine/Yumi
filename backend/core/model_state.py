"""
Model State - 全局模型状态管理
用于存储当前活跃模型的标识和配置
"""
from __future__ import annotations

from typing import Any

from .logging import get_logger

logger = get_logger(__name__)

_active_model: dict[str, Any] | None = None


def get_active_model() -> dict[str, Any] | None:
    """获取当前活跃模型配置"""
    return _active_model


def set_active_model(model_config: dict[str, Any]) -> None:
    """设置当前活跃模型配置"""
    global _active_model
    _active_model = model_config
    logger.info(
        "Active model updated: %s (provider=%s, model=%s)",
        model_config.get("display_name", "Unknown"),
        model_config.get("provider_id", "Unknown"),
        model_config.get("model_name", "Unknown"),
    )


def clear_active_model() -> None:
    """清除当前活跃模型配置"""
    global _active_model
    _active_model = None
    logger.info("Active model cleared")


def has_active_model() -> bool:
    """检查是否存在活跃模型"""
    return _active_model is not None
