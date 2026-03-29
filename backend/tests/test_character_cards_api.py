"""Character cards HTTP API and chat integration."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_upsert_and_get_by_id_for_prompt() -> None:
    from database import get_db, init_db
    from services.character_card import (
        CharacterCard,
        get_character_card_by_id,
        upsert_character_card,
    )

    await init_db()
    uid = "acc_prompt_user"
    cid = "char_custom_1"

    card = CharacterCard(
        id=cid,
        user_id=uid,
        conversation_id=None,
        role_overview="概述",
        formal_name="测试名",
        nickname="小测",
        race_or_form="人类",
        gender="女",
        visual_age="20",
        actual_age="20",
        location="本地",
        appearance_desc="描述",
        core_personality="性格",
        self_perception="自认知",
        attitude_to_user="态度",
        likes="喜",
        dislikes="厌",
        tone_base="语气",
        word_habits="用词",
        emotion_rules="情感",
        length_pref="长度",
        special_logic_list="逻辑",
        few_shot_examples="示例",
        is_active=True,
    )

    async with get_db() as db:
        await upsert_character_card(db, card)
        loaded = await get_character_card_by_id(db, uid, cid)

    assert loaded is not None
    assert loaded.formal_name == "测试名"


@pytest.mark.asyncio
async def test_get_character_card_for_chat_prefers_character_id() -> None:
    from database import get_db, init_db
    from services.character_card import (
        CharacterCard,
        get_character_card_for_chat,
        upsert_character_card,
    )

    await init_db()
    uid = "acc_chat_pick"
    c1 = "char_one"
    c2 = "char_two"

    async with get_db() as db:
        await upsert_character_card(
            db,
            CharacterCard(
                id=c1,
                user_id=uid,
                conversation_id=None,
                formal_name="One",
                nickname="",
                role_overview="",
                race_or_form="",
                gender="",
                visual_age="",
                actual_age="",
                location="",
                appearance_desc="",
                core_personality="",
                self_perception="",
                attitude_to_user="",
                likes="",
                dislikes="",
                tone_base="",
                word_habits="",
                emotion_rules="",
                length_pref="",
                special_logic_list="",
                few_shot_examples="",
                is_active=True,
            ),
        )
        await upsert_character_card(
            db,
            CharacterCard(
                id=c2,
                user_id=uid,
                conversation_id=None,
                formal_name="Two",
                nickname="",
                role_overview="",
                race_or_form="",
                gender="",
                visual_age="",
                actual_age="",
                location="",
                appearance_desc="",
                core_personality="",
                self_perception="",
                attitude_to_user="",
                likes="",
                dislikes="",
                tone_base="",
                word_habits="",
                emotion_rules="",
                length_pref="",
                special_logic_list="",
                few_shot_examples="",
                is_active=True,
            ),
        )

        picked = await get_character_card_for_chat(db, uid, c2, None)

    assert picked.id == c2
    assert picked.formal_name == "Two"
