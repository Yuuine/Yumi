"""Tests for character card persistence."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_get_or_create_default_card_for_user() -> None:
    from database import get_db, init_db
    from services.character_card import get_or_create_character_card

    await init_db()
    uid = "test-char-user-1"

    async with get_db() as db:
        card = await get_or_create_character_card(db, uid, None)

    assert card.user_id == uid
    assert card.conversation_id is None
    assert "艾拉" in card.formal_name
    assert card.role_overview

    async with get_db() as db:
        again = await get_or_create_character_card(db, uid, None)

    assert again.id == card.id


@pytest.mark.asyncio
async def test_get_or_create_clones_default_for_conversation() -> None:
    from database import get_db, init_db
    from services.character_card import (
        get_character_card_by_conversation,
        get_or_create_character_card,
    )

    await init_db()
    uid = "test-char-user-2"
    conv = "conv-123"

    async with get_db() as db:
        default = await get_or_create_character_card(db, uid, None)

    async with get_db() as db:
        bound = await get_or_create_character_card(db, uid, conv)

    assert bound.conversation_id == conv
    assert bound.formal_name == default.formal_name
    assert bound.id != default.id

    async with get_db() as db:
        loaded = await get_character_card_by_conversation(db, uid, conv)

    assert loaded is not None
    assert loaded.id == bound.id
