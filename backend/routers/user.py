"""
User API Router
"""

import json
import time

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from ..core import clear_active_model, get_conversation_cache
from ..services.log_service import AuditAction, log_service

router = APIRouter()
logger = log_service.logger if hasattr(log_service, "logger") else None


class UserPreferences(BaseModel):
    communication_style: str = Field("warm", alias="communicationStyle")
    topics_of_interest: list[str] = Field(["生活", "工作", "情感"], alias="topicsOfInterest")
    emotional_support_level: str = Field("high", alias="emotionalSupportLevel")
    response_length: str = Field("medium", alias="responseLength")

    class Config:
        populate_by_name = True


class UserProfile(BaseModel):
    id: str
    role_name: str = Field(..., alias="roleName")
    preferences: UserPreferences

    class Config:
        populate_by_name = True


class PurgeUserRequest(BaseModel):
    userId: str


class PurgeUserResponse(BaseModel):
    success: bool
    cleared: dict[str, int]


@router.get("/user/profile", response_model=UserProfile)
async def get_user_profile(userId: str, req: Request):
    from ..database import get_db

    async with get_db() as db:
        cursor = await db.execute(
            """SELECT id, role_name, preferences_json
               FROM users WHERE id = ?""",
            (userId,),
        )
        row = await cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="User not found")

        preferences = json.loads(row[2]) if row[2] else {}

        return UserProfile(
            id=row[0],
            role_name=row[1],
            preferences=UserPreferences(**preferences),
        )


@router.put("/user/profile", response_model=UserProfile)
async def update_user_profile(profile: UserProfile, req: Request):
    from ..database import get_db

    start_time = time.time()

    try:
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT preferences_json FROM users WHERE id = ?", (profile.id,)
            )
            old_row = await cursor.fetchone()
            old_preferences = json.loads(old_row[0]) if old_row and old_row[0] else {}

            await db.execute(
                """INSERT OR REPLACE INTO users (id, role_name, preferences_json, updated_at)
                   VALUES (?, ?, ?, CURRENT_TIMESTAMP)""",
                (
                    profile.id,
                    profile.role_name,
                    json.dumps(profile.preferences.dict(by_alias=False)),
                ),
            )
            await db.commit()

        latency_ms = (time.time() - start_time) * 1000

        fields_changed = []
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


class UserListItem(BaseModel):
    id: str
    role_name: str = Field(..., alias="roleName")
    created_at: str = Field(..., alias="createdAt")
    updated_at: str = Field(..., alias="updatedAt")

    class Config:
        populate_by_name = True


class ListUsersResponse(BaseModel):
    users: list[UserListItem]


class FullAccountDataResponse(BaseModel):
    id: str
    role_name: str = Field(..., alias="roleName")
    preferences: UserPreferences
    created_at: str = Field(..., alias="createdAt")
    updated_at: str = Field(..., alias="updatedAt")

    class Config:
        populate_by_name = True


@router.get("/user/list", response_model=ListUsersResponse)
async def list_users(req: Request):
    from ..database import get_db

    async with get_db() as db:
        cursor = await db.execute(
            """SELECT id, role_name, created_at, updated_at
               FROM users ORDER BY updated_at DESC""",
        )
        rows = await cursor.fetchall()

        users = []
        for row in rows:
            users.append(
                UserListItem(
                    id=row[0],
                    role_name=row[1],
                    created_at=row[2],
                    updated_at=row[3],
                )
            )

        return ListUsersResponse(users=users)


@router.get("/user/full/{user_id}")
async def get_full_account_data(user_id: str, req: Request):
    from ..database import get_db
    from ..services.character_card import list_character_cards_for_user
    from ..services.conversation_service import conversation_service

    async with get_db() as db:
        cursor = await db.execute(
            """SELECT id, role_name, preferences_json, created_at, updated_at
               FROM users WHERE id = ?""",
            (user_id,),
        )
        row = await cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="User not found")

        preferences = json.loads(row[2]) if row[2] else {}

        character_cards = await list_character_cards_for_user(db, user_id)
        
        conversations = await conversation_service.get_user_conversations(
            user_id=user_id,
            limit=1000,
            offset=0
        )

        return {
            "id": row[0],
            "roleName": row[1],
            "preferences": preferences,
            "createdAt": row[3],
            "updatedAt": row[4],
            "characterCards": [
                {
                    "id": card.id,
                    "userId": card.user_id,
                    "conversationId": card.conversation_id,
                    "roleOverview": card.role_overview,
                    "formalName": card.formal_name,
                    "nickname": card.nickname,
                    "raceOrForm": card.race_or_form,
                    "gender": card.gender,
                    "visualAge": card.visual_age,
                    "actualAge": card.actual_age,
                    "location": card.location,
                    "appearanceDesc": card.appearance_desc,
                    "corePersonality": card.core_personality,
                    "selfPerception": card.self_perception,
                    "attitudeToUser": card.attitude_to_user,
                    "likes": card.likes,
                    "dislikes": card.dislikes,
                    "toneBase": card.tone_base,
                    "wordHabits": card.word_habits,
                    "emotionRules": card.emotion_rules,
                    "lengthPref": card.length_pref,
                    "specialLogicList": card.special_logic_list,
                    "fewShotExamples": card.few_shot_examples,
                    "isActive": card.is_active,
                }
                for card in character_cards
            ],
            "conversations": conversations,
        }


@router.post("/user/purge", response_model=PurgeUserResponse)
async def purge_user_data(payload: PurgeUserRequest, req: Request):
    from ..database import get_db

    user_id = payload.userId.strip()
    if not user_id:
        raise HTTPException(status_code=400, detail="userId is required")

    memory_engine = req.app.state.memory_engine
    cleared_memory_count = 0
    try:
        cleared_memory_count = await memory_engine.clear_user_memories(user_id)
    except Exception as e:  # noqa: BLE001
        if logger:
            logger.error("Failed to clear vector memories for user %s: %s", user_id, e)
        raise HTTPException(status_code=500, detail="清理向量记忆失败") from e

    try:
        async with get_db() as db:
            cursor = await db.execute("DELETE FROM conversation_logs WHERE user_id = ?", (user_id,))
            cleared_logs = cursor.rowcount or 0

            cursor = await db.execute("DELETE FROM conversations WHERE user_id = ?", (user_id,))
            cleared_conversations = cursor.rowcount or 0

            cursor = await db.execute("DELETE FROM memory_summaries WHERE user_id = ?", (user_id,))
            cleared_summaries = cursor.rowcount or 0

            cursor = await db.execute("DELETE FROM character_cards WHERE user_id = ?", (user_id,))
            cleared_character_cards = cursor.rowcount or 0

            cursor = await db.execute("DELETE FROM audit_logs WHERE user_id = ?", (user_id,))
            cleared_audit_logs = cursor.rowcount or 0

            cursor = await db.execute("DELETE FROM system_logs WHERE user_id = ?", (user_id,))
            cleared_system_logs = cursor.rowcount or 0

            cursor = await db.execute("DELETE FROM users WHERE id = ?", (user_id,))
            cleared_user_profile = cursor.rowcount or 0

            cursor = await db.execute("DELETE FROM model_configs WHERE account_id = ?", (user_id,))
            cleared_model_configs = cursor.rowcount or 0

            await db.commit()

        clear_active_model(user_id)
        conversation_cache = get_conversation_cache()
        conversation_cache.clear_user(user_id)

        prompt_builder = getattr(req.app.state, "prompt_builder", None)
        if prompt_builder and hasattr(prompt_builder, "clear_character_card_cache_for_user"):
            prompt_builder.clear_character_card_cache_for_user(user_id)

        await log_service.log_audit(
            action=AuditAction.USER_PROFILE_UPDATE,
            resource_type="user",
            resource_id=user_id,
            result="SUCCESS",
            user_id=user_id,
            details={
                "event": "PURGE_USER_DATA",
                "cleared": {
                    "memories": cleared_memory_count,
                    "conversation_logs": cleared_logs,
                    "conversations": cleared_conversations,
                    "memory_summaries": cleared_summaries,
                    "character_cards": cleared_character_cards,
                    "audit_logs": cleared_audit_logs,
                    "system_logs": cleared_system_logs,
                    "user_profile": cleared_user_profile,
                    "model_configs": cleared_model_configs,
                },
            },
        )

        return PurgeUserResponse(
            success=True,
            cleared={
                "memories": cleared_memory_count,
                "conversation_logs": cleared_logs,
                "conversations": cleared_conversations,
                "memory_summaries": cleared_summaries,
                "character_cards": cleared_character_cards,
                "audit_logs": cleared_audit_logs,
                "system_logs": cleared_system_logs,
                "user_profile": cleared_user_profile,
                "model_configs": cleared_model_configs,
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        if logger:
            logger.error("Failed to purge user data for %s: %s", user_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail="清理用户数据失败") from e
