"""
Settings API Router
"""

import time

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict

from ..services.log_service import AuditAction, log_service

router = APIRouter()


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
    from ..database import get_db

    async with get_db() as db:
        cursor = await db.execute("SELECT key, value FROM settings")
        rows = await cursor.fetchall()

        settings_dict = {row[0]: row[1] for row in rows}

        return AppSettings(
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


@router.put("/settings", response_model=AppSettings)
async def update_settings(settings: AppSettings, req: Request):
    from ..database import get_db

    start_time = time.time()

    try:
        async with get_db() as db:
            cursor = await db.execute("SELECT key, value FROM settings")
            old_rows = await cursor.fetchall()
            old_settings = {row[0]: row[1] for row in old_rows}

            settings_dict = settings.dict()
            changed_keys = []

            for key, value in settings_dict.items():
                old_value = old_settings.get(key)
                new_value = str(value)
                if old_value != new_value:
                    changed_keys.append(key)

                await db.execute(
                    """INSERT OR REPLACE INTO settings (key, value, updated_at)
                       VALUES (?, ?, CURRENT_TIMESTAMP)""",
                    (key, new_value),
                )
            await db.commit()

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
