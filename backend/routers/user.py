"""
User API Router
"""

import json
import time

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from sqlmodel import select

from ..core import clear_active_model, get_conversation_cache, get_logger
from ..database_sqlmodel import get_session
from ..services.cache_service import get_cache_service
from ..models import (
    User,
    Conversation,
    ConversationLog,
    CharacterCard,
    ModelConfig,
)
from ..services.log_service import AuditAction, log_service

router = APIRouter()
logger = get_logger(__name__)


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
    cache_service = get_cache_service()
    cache_key = f"user:{userId}"
    
    try:
        cached = cache_service.user.get(cache_key)
        if cached is not None:
            if isinstance(cached, dict) and 'id' in cached and 'roleName' in cached and 'preferences' in cached:
                logger.debug("UserRouter", "Cache HIT", {"key": cache_key})
                return cached
            else:
                logger.debug("UserRouter", "Cache has invalid data type, clearing", {"key": cache_key})
                cache_service.user.delete(cache_key)
    except Exception as e:
        logger.error("UserRouter", "Cache read error", {"error": str(e)})
        cache_service.user.delete(cache_key)
    
    logger.debug("UserRouter", "Cache MISS", {"key": cache_key})
    async with get_session() as session:
        result = await session.exec(select(User).where(User.id == userId))
        user = result.first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        preferences = json.loads(user.preferences_json) if user.preferences_json else {}

        result = UserProfile(
            id=user.id,
            role_name=user.role_name,
            preferences=UserPreferences(**preferences),
        )
    
    try:
        cache_service.user.set(cache_key, result.model_dump(by_alias=True))
    except Exception as e:
        logger.error("UserRouter", "Cache write error", {"error": str(e)})
    
    return result


@router.put("/user/profile", response_model=UserProfile)
async def update_user_profile(profile: UserProfile, req: Request):
    start_time = time.time()

    try:
        async with get_session() as session:
            result = await session.exec(select(User).where(User.id == profile.id))
            user = result.first()

            old_preferences = {}
            if user:
                old_preferences = json.loads(user.preferences_json) if user.preferences_json else {}
                user.role_name = profile.role_name
                user.preferences_json = json.dumps(profile.preferences.dict(by_alias=False))
            else:
                user = User(
                    id=profile.id,
                    role_name=profile.role_name,
                    preferences_json=json.dumps(profile.preferences.dict(by_alias=False))
                )
                session.add(user)

            await session.commit()
            await session.refresh(user)

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

        try:
            cache_service = get_cache_service()
            cache_service.invalidate_user(profile.id)
        except Exception as e:
            logger.error("UserRouter", "Cache invalidate error", {"error": str(e)})

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
    async with get_session() as session:
        result = await session.exec(select(User).order_by(User.updated_at.desc()))
        users = result.all()

        user_list = []
        for user in users:
            user_list.append(
                UserListItem(
                    id=user.id,
                    role_name=user.role_name,
                    created_at=user.created_at.isoformat() if user.created_at else "",
                    updated_at=user.updated_at.isoformat() if user.updated_at else "",
                )
            )

        return ListUsersResponse(users=user_list)


@router.get("/user/full/{user_id}")
async def get_full_account_data(user_id: str, req: Request):
    from ..services.character_card import list_character_cards_for_user
    from ..services.conversation_service import conversation_service

    async with get_session() as session:
        result = await session.exec(select(User).where(User.id == user_id))
        user = result.first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        preferences = json.loads(user.preferences_json) if user.preferences_json else {}

        character_cards = await list_character_cards_for_user(session, user_id)

        conversations = await conversation_service.get_user_conversations(
            user_id=user_id,
            limit=1000,
            offset=0
        )

        return {
            "id": user.id,
            "roleName": user.nickname,
            "preferences": preferences,
            "createdAt": user.created_at.isoformat() if user.created_at else "",
            "updatedAt": user.updated_at.isoformat() if user.updated_at else "",
            "characterCards": [
                {
                    "id": card.id,
                    "userId": card.user_id,
                    "conversationId": getattr(card, 'conversation_id', None),
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
        async with get_session() as session:
            cleared_logs = 0
            result = await session.exec(select(ConversationLog).where(ConversationLog.user_id == user_id))
            logs_to_delete = result.all()
            for log in logs_to_delete:
                await session.delete(log)
                cleared_logs += 1

            cleared_conversations = 0
            result = await session.exec(select(Conversation).where(Conversation.user_id == user_id))
            convs_to_delete = result.all()
            for conv in convs_to_delete:
                await session.delete(conv)
                cleared_conversations += 1

            # TODO: MemorySummary 模型已移除，需要重新实现记忆清理逻辑
            cleared_summaries = 0

            cleared_character_cards = 0
            result = await session.exec(select(CharacterCard).where(CharacterCard.user_id == user_id))
            cards_to_delete = result.all()
            for card in cards_to_delete:
                await session.delete(card)
                cleared_character_cards += 1

            # TODO: AuditLog 和 SystemLog 在日志数据库中，需要从日志数据库清理
            cleared_audit_logs = 0
            cleared_system_logs = 0

            cleared_user_profile = 0
            result = await session.exec(select(User).where(User.id == user_id))
            user_to_delete = result.first()
            if user_to_delete:
                await session.delete(user_to_delete)
                cleared_user_profile = 1

            cleared_model_configs = 0
            result = await session.exec(select(ModelConfig).where(ModelConfig.account_id == user_id))
            configs_to_delete = result.all()
            for config in configs_to_delete:
                await session.delete(config)
                cleared_model_configs += 1

            await session.commit()

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
