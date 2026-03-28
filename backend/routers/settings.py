"""
Settings API Router
基于 SQLModel 重构
"""

import time

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict
from sqlmodel import select

from ..core import get_logger
from ..database_sqlmodel import get_session
from ..models import Setting
from ..services.cache_service import get_cache_service
from ..services.log_service import AuditAction, log_service

router = APIRouter()
logger = get_logger(__name__)


class AppSettings(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    api_endpoint: str = "http://127.0.0.1:11434/v1"
    api_key: str = ""
    model_name: str = "llama3.1:8b"
    max_tokens: int = 4096
    temperature: float = 0.85
    memory_enabled: bool = True
    emotion_detection: bool = True
    theme: str = "light"
    language: str = "zh-CN"


@router.get("/settings", response_model=AppSettings)
async def get_settings(req: Request):
    """获取系统设置"""
    cache_service = get_cache_service()
    cache_key = "settings:global"
    
    try:
        cached = cache_service.settings.get(cache_key)
        if cached is not None:
            if isinstance(cached, dict) and 'api_endpoint' in cached and 'model_name' in cached:
                logger.debug("SettingsRouter", "Cache HIT", {"key": cache_key})
                return cached
            else:
                logger.debug("SettingsRouter", "Cache has invalid data type, clearing", {"key": cache_key})
                cache_service.settings.delete(cache_key)
    except Exception as e:
        logger.error("SettingsRouter", "Cache read error", {"error": str(e)})
        cache_service.settings.delete(cache_key)
    
    logger.debug("SettingsRouter", "Cache MISS", {"key": cache_key})
    async with get_session() as session:
        result = await session.exec(select(Setting))
        settings_list = result.all()

        settings_dict = {s.key: s.value for s in settings_list}

        result = AppSettings(
            api_endpoint=settings_dict.get("api_endpoint", "http://127.0.0.1:11434/v1"),
            api_key=settings_dict.get("api_key", ""),
            model_name=settings_dict.get("model_name", "llama3.1:8b"),
            max_tokens=int(settings_dict.get("max_tokens", "4096")),
            temperature=float(settings_dict.get("temperature", "0.85")),
            memory_enabled=settings_dict.get("memory_enabled", "true").lower() == "true",
            emotion_detection=settings_dict.get("emotion_detection", "true").lower() == "true",
            theme=settings_dict.get("theme", "light"),
            language=settings_dict.get("language", "zh-CN"),
        )
    
    try:
        cache_service.settings.set(cache_key, result.model_dump())
    except Exception as e:
        logger.error("SettingsRouter", "Cache write error", {"error": str(e)})
    
    return result


@router.put("/settings", response_model=AppSettings)
async def update_settings(settings: AppSettings, req: Request):
    """更新系统设置"""
    start_time = time.time()

    try:
        async with get_session() as session:
            # 获取旧设置
            result = await session.exec(select(Setting))
            old_settings_list = result.all()
            old_settings = {s.key: s.value for s in old_settings_list}

            settings_dict = settings.dict()
            changed_keys = []

            for key, value in settings_dict.items():
                old_value = old_settings.get(key)
                new_value = str(value)
                if old_value != new_value:
                    changed_keys.append(key)

                # 查找或创建设置项
                result = await session.exec(select(Setting).where(Setting.key == key))
                existing = result.first()

                if existing:
                    existing.value = new_value
                else:
                    new_setting = Setting(key=key, value=new_value)
                    session.add(new_setting)

            await session.commit()

        latency_ms = (time.time() - start_time) * 1000

        await log_service.log_audit(
            action=AuditAction.SETTINGS_UPDATE,
            resource_type="settings",
            resource_id="global",
            result="SUCCESS",
            details={
                "changed_keys": changed_keys,
                "latency_ms": round(latency_ms, 2),
            },
        )

        try:
            cache_service = get_cache_service()
            cache_service.settings.delete("settings:global")
        except Exception as e:
            logger.error("SettingsRouter", "Cache invalidate error", {"error": str(e)})

        return settings

    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        await log_service.log_audit(
            action=AuditAction.SETTINGS_UPDATE,
            resource_type="settings",
            resource_id="global",
            result="FAIL",
            details={
                "error": str(e),
                "latency_ms": round(latency_ms, 2),
            },
        )
        raise
