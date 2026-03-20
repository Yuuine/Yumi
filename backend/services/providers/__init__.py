"""
模型提供商配置加载器

从 YAML 文件加载模型配置，支持按模型名称查找配置。
"""
from __future__ import annotations

import logging
from pathlib import Path

import yaml

from .base import (
    ApiConfig,
    ModelInfo,
    ProviderModelConfig,
    RequestConfig,
    ResponseConfig,
    StreamConfig,
)

logger = logging.getLogger(__name__)

PROVIDERS_DIR = Path(__file__).parent

_config_cache: dict[str, ProviderModelConfig] = {}


def load_model_config(model_name: str) -> ProviderModelConfig | None:
    """
    加载指定模型的配置
    
    Args:
        model_name: 模型名称，如 "deepseek-chat", "gpt-4"
        
    Returns:
        模型配置对象，如果未找到则返回 None
    """
    model_lower = model_name.lower()
    
    if model_lower in _config_cache:
        return _config_cache[model_lower]
    
    for provider_dir in PROVIDERS_DIR.iterdir():
        if not provider_dir.is_dir():
            continue
        if provider_dir.name.startswith("_"):
            continue
            
        config_file = provider_dir / f"{model_lower}.yaml"
        if config_file.exists():
            config = _parse_config(config_file)
            if config:
                _config_cache[model_lower] = config
                logger.debug("Loaded config for model: %s from %s", model_name, config_file)
                return config
    
    logger.debug("No config found for model: %s", model_name)
    return None


def _parse_config(file_path: Path) -> ProviderModelConfig | None:
    """
    解析 YAML 配置文件
    
    Args:
        file_path: 配置文件路径
        
    Returns:
        解析后的配置对象，解析失败返回 None
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        
        if not data:
            logger.warning("Empty config file: %s", file_path)
            return None
        
        model_info = ModelInfo(
            name=data.get("model", {}).get("name", file_path.stem),
            provider=data.get("model", {}).get("provider", "unknown"),
            description=data.get("model", {}).get("description", ""),
        )
        
        api_data = data.get("api", {})
        api_config = ApiConfig(
            endpoint_suffix=api_data.get("endpoint_suffix", "/chat/completions"),
            auth_type=api_data.get("auth_type", "bearer"),
        )
        
        request_data = data.get("request", {})
        request_config = RequestConfig(
            defaults=request_data.get("defaults", {}),
            supported_fields=request_data.get("supported_fields", []),
            unsupported_fields=request_data.get("unsupported_fields", []),
            special=request_data.get("special", {}),
        )
        
        response_data = data.get("response", {})
        response_config = ResponseConfig(
            content_field=response_data.get("content_field", "choices[0].message.content"),
            reasoning_field=response_data.get("reasoning_field"),
        )
        
        stream_data = data.get("stream", {})
        stream_config = StreamConfig(
            format=stream_data.get("format", "sse"),
            done_signal=stream_data.get("done_signal", "[DONE]"),
            content_field=stream_data.get("content_field", "choices[0].delta.content"),
        )
        
        return ProviderModelConfig(
            model=model_info,
            api=api_config,
            request=request_config,
            response=response_config,
            stream=stream_config,
        )
        
    except yaml.YAMLError as e:
        logger.error("Failed to parse YAML config %s: %s", file_path, e)
        return None
    except Exception as e:
        logger.error("Failed to load config %s: %s", file_path, e)
        return None


def get_all_models() -> list[str]:
    """
    获取所有已配置的模型名称
    
    Returns:
        模型名称列表
    """
    models = []
    for provider_dir in PROVIDERS_DIR.iterdir():
        if not provider_dir.is_dir():
            continue
        if provider_dir.name.startswith("_"):
            continue
        for config_file in provider_dir.glob("*.yaml"):
            models.append(config_file.stem)
    return sorted(models)


def get_models_by_provider(provider: str) -> list[str]:
    """
    获取指定提供商的所有模型名称
    
    Args:
        provider: 提供商名称，如 "deepseek", "openai"
        
    Returns:
        该提供商下的模型名称列表
    """
    models = []
    provider_dir = PROVIDERS_DIR / provider.lower()
    if provider_dir.is_dir():
        for config_file in provider_dir.glob("*.yaml"):
            models.append(config_file.stem)
    return sorted(models)


def clear_cache() -> None:
    """清除配置缓存"""
    _config_cache.clear()


def reload_config(model_name: str) -> ProviderModelConfig | None:
    """
    重新加载指定模型的配置
    
    Args:
        model_name: 模型名称
        
    Returns:
        重新加载的配置对象
    """
    model_lower = model_name.lower()
    if model_lower in _config_cache:
        del _config_cache[model_lower]
    return load_model_config(model_name)
