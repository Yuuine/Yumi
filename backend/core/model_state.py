"""
Model State - 全局模型状态管理
用于存储当前活跃模型的标识和配置
"""

from __future__ import annotations

from typing import Any

from .logging import get_logger

logger = get_logger(__name__)

_active_models: dict[str, dict[str, Any]] = {}


def get_active_model(account_id: str) -> dict[str, Any] | None:
    """获取指定账号的活跃模型配置"""
    return _active_models.get(account_id)


def set_active_model(account_id: str, model_config: dict[str, Any]) -> None:
    """设置指定账号的活跃模型配置"""
    _active_models[account_id] = model_config
    logger.info(
        "Active model updated for account %s: %s (provider=%s, model=%s)",
        account_id,
        model_config.get("display_name", "Unknown"),
        model_config.get("provider_id", "Unknown"),
        model_config.get("model_name", "Unknown"),
    )


def clear_active_model(account_id: str | None = None) -> None:
    """清除活跃模型配置（可指定账号，或清除全部）"""
    if account_id is None:
        _active_models.clear()
        logger.info("All active models cleared")
        return
    _active_models.pop(account_id, None)
    logger.info("Active model cleared for account %s", account_id)


def has_active_model(account_id: str) -> bool:
    """检查指定账号是否存在活跃模型"""
    return account_id in _active_models
