"""
User API Router
"""
import json
import time

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ..services.log_service import AuditAction, log_service

router = APIRouter()
logger = log_service.logger if hasattr(log_service, 'logger') else None


class BigFiveTraits(BaseModel):
    openness: float = 0.75
    conscientiousness: float = 0.70
    extraversion: float = 0.65
    agreeableness: float = 0.80
    neuroticism: float = 0.35


class UserPreferences(BaseModel):
    communication_style: str = "warm"
    topics_of_interest: list[str] = ["生活", "工作", "情感"]
    emotional_support_level: str = "high"
    response_length: str = "medium"


class UserProfile(BaseModel):
    id: str
    role_name: str
    big_five: BigFiveTraits
    preferences: UserPreferences


@router.get("/user/profile", response_model=UserProfile)
async def get_user_profile(userId: str, req: Request):
    from ..database import get_db

    async with get_db() as db:
        cursor = await db.execute(
            """SELECT id, role_name, big_five_json, preferences_json
               FROM users WHERE id = ?""",
            (userId,)
        )
        row = await cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="User not found")

        big_five = json.loads(row[2]) if row[2] else {}
        preferences = json.loads(row[3]) if row[3] else {}

        return UserProfile(
            id=row[0],
            role_name=row[1],
            big_five=BigFiveTraits(**big_five),
            preferences=UserPreferences(**preferences)
        )


@router.put("/user/profile", response_model=UserProfile)
async def update_user_profile(profile: UserProfile, req: Request):
    from ..database import get_db

    start_time = time.time()
    
    try:
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT big_five_json, preferences_json FROM users WHERE id = ?",
                (profile.id,)
            )
            old_row = await cursor.fetchone()
            old_big_five = json.loads(old_row[0]) if old_row and old_row[0] else {}
            old_preferences = json.loads(old_row[1]) if old_row and old_row[1] else {}

            await db.execute(
                """INSERT OR REPLACE INTO users (id, role_name, big_five_json, preferences_json, updated_at)
                   VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)""",
                (
                    profile.id,
                    profile.role_name,
                    json.dumps(profile.big_five.dict()),
                    json.dumps(profile.preferences.dict())
                )
            )
            await db.commit()

        latency_ms = (time.time() - start_time) * 1000

        fields_changed = []
        if old_big_five != profile.big_five.dict():
            fields_changed.append("big_five")
        if old_preferences != profile.preferences.dict():
            fields_changed.append("preferences")

        await log_service.log_audit(
            action=AuditAction.USER_PROFILE_UPDATE,
            resource_type="user",
            resource_id=profile.id,
            result="SUCCESS",
            user_id=profile.id,
            details={
                "fields_changed": fields_changed,
                "latency_ms": round(latency_ms, 2),
            },
        )

        return profile

    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        await log_service.log_audit(
            action=AuditAction.USER_PROFILE_UPDATE,
            resource_type="user",
            resource_id=profile.id,
            result="FAIL",
            user_id=profile.id,
            details={
                "error": str(e),
                "latency_ms": round(latency_ms, 2),
            },
        )
        raise
