"""
Settings API Router
"""

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict

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

    async with await get_db() as db:
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
            language=settings_dict.get("language", "zh-CN")
        )


@router.put("/settings", response_model=AppSettings)
async def update_settings(settings: AppSettings, req: Request):
    from ..database import get_db

    async with await get_db() as db:
        settings_dict = settings.dict()
        for key, value in settings_dict.items():
            await db.execute(
                """INSERT OR REPLACE INTO settings (key, value, updated_at)
                   VALUES (?, ?, CURRENT_TIMESTAMP)""",
                (key, str(value))
            )
        await db.commit()

        return settings
