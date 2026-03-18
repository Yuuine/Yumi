"""
User API Router
"""
import json

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter()


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

    async with get_db() as db:
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

        return profile
