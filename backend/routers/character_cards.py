"""
Character cards API — 与前端本地角色库同步（user_id 为账号 id）
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field

from ..core import get_logger
from ..database import get_db
from ..services.character_card import (
    CharacterCard,
    delete_character_card_by_id,
    list_character_cards_for_user,
    upsert_character_card,
)

router = APIRouter()
logger = get_logger(__name__)


def _card_to_response(card: CharacterCard) -> dict[str, Any]:
    return {
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


class CharacterCardUpsertBody(BaseModel):
    """与前端 CharacterCardFlat 对齐（camelCase）。"""

    model_config = ConfigDict(populate_by_name=True)

    role_overview: str = Field("", alias="roleOverview")
    formal_name: str = Field("", alias="formalName")
    nickname: str = ""
    race_or_form: str = Field("人类", alias="raceOrForm")
    gender: str = "中性"
    visual_age: str = Field("", alias="visualAge")
    actual_age: str = Field("", alias="actualAge")
    location: str = ""
    appearance_desc: str = Field("", alias="appearanceDesc")
    core_personality: str = Field("", alias="corePersonality")
    self_perception: str = Field("", alias="selfPerception")
    attitude_to_user: str = Field("", alias="attitudeToUser")
    likes: str = ""
    dislikes: str = ""
    tone_base: str = Field("", alias="toneBase")
    word_habits: str = Field("", alias="wordHabits")
    emotion_rules: str = Field("", alias="emotionRules")
    length_pref: str = Field("", alias="lengthPref")
    special_logic_list: str = Field("", alias="specialLogicList")
    few_shot_examples: str = Field("", alias="fewShotExamples")
    is_active: bool = Field(True, alias="isActive")


class BatchCardItem(CharacterCardUpsertBody):
    id: str


class BatchUpsertBody(BaseModel):
    cards: list[BatchCardItem]


def _body_to_character(card_id: str, user_id: str, body: CharacterCardUpsertBody) -> CharacterCard:
    return CharacterCard(
        id=card_id,
        user_id=user_id,
        conversation_id=None,
        role_overview=body.role_overview,
        formal_name=body.formal_name,
        nickname=body.nickname,
        race_or_form=body.race_or_form or "人类",
        gender=body.gender,
        visual_age=body.visual_age,
        actual_age=body.actual_age,
        location=body.location,
        appearance_desc=body.appearance_desc,
        core_personality=body.core_personality,
        self_perception=body.self_perception,
        attitude_to_user=body.attitude_to_user,
        likes=body.likes,
        dislikes=body.dislikes,
        tone_base=body.tone_base,
        word_habits=body.word_habits,
        emotion_rules=body.emotion_rules,
        length_pref=body.length_pref,
        special_logic_list=body.special_logic_list,
        few_shot_examples=body.few_shot_examples,
        is_active=body.is_active,
    )


def _clear_prompt_cache(req: Request, user_id: str) -> None:
    prompt_builder = getattr(req.app.state, "prompt_builder", None)
    if prompt_builder and hasattr(prompt_builder, "clear_character_card_cache_for_user"):
        prompt_builder.clear_character_card_cache_for_user(user_id)


@router.get("/character-cards")
async def list_character_cards(
    userId: str = Query(..., min_length=1),
) -> list[dict[str, Any]]:
    async with get_db() as db:
        cards = await list_character_cards_for_user(db, userId)
    return [_card_to_response(c) for c in cards]


@router.put("/character-cards/{card_id}")
async def upsert_one_character_card(
    card_id: str,
    req: Request,
    body: CharacterCardUpsertBody,
    userId: str = Query(..., min_length=1),
) -> dict[str, Any]:
    if len(card_id) < 1:
        raise HTTPException(status_code=400, detail="Invalid card id")

    card = _body_to_character(card_id, userId, body)
    async with get_db() as db:
        await upsert_character_card(db, card)

    _clear_prompt_cache(req, userId)

    return {"success": True, "id": card_id}


@router.put("/character-cards/batch")
async def upsert_character_cards_batch(
    req: Request,
    payload: BatchUpsertBody,
    userId: str = Query(..., min_length=1),
) -> dict[str, Any]:
    if not payload.cards:
        return {"success": True, "count": 0}

    async with get_db() as db:
        for item in payload.cards:
            flat = item.model_dump(exclude={"id"})
            body = CharacterCardUpsertBody(**flat)
            card = _body_to_character(item.id, userId, body)
            await upsert_character_card(db, card)

    _clear_prompt_cache(req, userId)
    return {"success": True, "count": len(payload.cards)}


@router.delete("/character-cards/{card_id}")
async def delete_character_card_endpoint(
    card_id: str,
    req: Request,
    userId: str = Query(..., min_length=1),
) -> dict[str, Any]:
    async with get_db() as db:
        ok = await delete_character_card_by_id(db, userId, card_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Character card not found")
    _clear_prompt_cache(req, userId)
    return {"success": True, "id": card_id}
