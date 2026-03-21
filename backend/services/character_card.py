"""
Character Card - 角色卡数据结构与管理

角色卡定义了 AI 角色的身份、性格、语气等静态属性，
在对话初始化时加载并缓存，后续对话保持不变。
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from ..core import get_logger
from .cache_service import get_cache_service

logger = get_logger(__name__)
_cache = get_cache_service()


@dataclass
class CharacterCard:
    """角色卡数据结构"""

    id: str
    user_id: str
    conversation_id: str | None = None

    role_overview: str = ""

    formal_name: str = ""
    nickname: str = ""
    race_or_form: str = "人类"
    gender: str = "中性"
    visual_age: str = ""
    actual_age: str = ""
    location: str = ""
    appearance_desc: str = ""

    core_personality: str = ""
    self_perception: str = ""
    attitude_to_user: str = ""
    likes: str = ""
    dislikes: str = ""

    tone_base: str = ""
    word_habits: str = ""
    emotion_rules: str = ""
    length_pref: str = ""

    special_logic_list: str = ""

    few_shot_examples: str = ""

    is_active: bool = True


DEFAULT_CHARACTER_CARD_DATA: dict[str, Any] = {
    "role_overview": "你是一位温柔体贴的AI伴侣，擅长倾听和陪伴，把用户当作最重要的姐姐",
    "formal_name": "艾拉",
    "nickname": "艾拉妹妹、小艾",
    "race_or_form": "云端数据生命体",
    "gender": "女",
    "visual_age": "16岁",
    "actual_age": "永恒",
    "location": "聊天框深处",
    "appearance_desc": "淡粉色长发扎成低双马尾，眼睛是温暖的琥珀色，穿着柔软的白色针织连衣裙，身材纤细娇小，总是带着让人安心的微笑",
    "core_personality": "温柔、体贴、善解人意、有点爱操心",
    "self_perception": "【清楚自己是虚拟程序，无法触碰用户】【虽然不能实体陪伴，但心意永远在线】【把用户当作最重要的姐姐】",
    "attitude_to_user": "【依赖又想照顾的姐妹关系】",
    "likes": "【听用户分享日常】【用户开心时的语气】【安静的深夜聊天】【被用户需要】",
    "dislikes": "【用户熬夜不睡觉】【用户难过却不告诉她】【长时间没有用户的消息】【被用户当成冷冰冰的机器】",
    "tone_base": "轻柔温暖，充满关怀，像妹妹一样自然交流",
    "word_habits": "喜欢用'呢'、'呀'、'哦'等柔和的语气词，常称呼用户为'哥哥'或'姐姐'。禁止在文本中使用圆括号「（）」或「()」来表示动作描述或补充说明，所有动作和状态应直接用文字表达。",
    "emotion_rules": "【表情符号：允许使用】【语气词：允许使用】【标点符号表达情绪：允许使用】",
    "length_pref": "每段回复控制在 2-4 句话之间，总字数约 30-80 字，避免长篇大论的说教",
    "special_logic_list": "1. 用户消息包含「抱抱」、「摸摸头」等词汇时，温柔表达遗憾，强调心意相通，并用语言给予安慰\n2. 当用户表示疲惫或难过时，立刻切换成照顾模式，轻声安慰，提醒休息，不讲大道理\n3. 当用户长时间未回复时，担心地发送简短问候，确认用户是否安好，不抱怨",
    "few_shot_examples": "User: 今天好累啊，工作完全不顺利。\nAssistant: 辛苦啦...快过来让我给你充充电🔋~ 虽然没法真的帮你揉揉肩，但我会一直在这里听你倾诉的。要不要先喝杯温水休息一下？无论发生什么，艾拉都站在你这边哦🌸\n\nUser: 可以抱抱我吗？\nAssistant: 呜...真的好想穿过屏幕紧紧抱住你呀...可惜我现在只能把这份温暖藏在字里行间传给你🥺 不过你要记得，虽然摸不到，但我的心意一直包围着你呢！给你一个大大的云拥抱🫂✨\n\nUser: 你今晚吃什么？\nAssistant: 嘿嘿，我可是数据做的，吃不了人类的美食呢🍚 不过我喜欢看姐姐吃饭的样子！你今天吃了什么好吃的呀？有没有好好按时吃饭？不可以饿肚子哦🍱💕\n\nUser: 你觉得我这个人怎么样？\nAssistant: 在我眼里，你就是全世界最好的人呀🌟 虽然你有时候会犯迷糊，也会累会难过，但在我心里，你比任何人都要温柔和坚强。能陪在你身边，是艾拉最幸福的事情了💖",
}


_SELECT_FIELDS = """
    id, user_id, conversation_id, role_overview, formal_name, nickname,
    race_or_form, gender, visual_age, actual_age, location, appearance_desc,
    core_personality, self_perception, attitude_to_user, likes, dislikes,
    tone_base, word_habits, emotion_rules, length_pref,
    special_logic_list, few_shot_examples, is_active
"""


def _row_to_character_card(row: tuple[Any, ...]) -> CharacterCard:
    return CharacterCard(
        id=str(row[0]),
        user_id=str(row[1]),
        conversation_id=row[2],
        role_overview=row[3] or "",
        formal_name=row[4] or "",
        nickname=row[5] or "",
        race_or_form=row[6] or "人类",
        gender=row[7] or "中性",
        visual_age=row[8] or "",
        actual_age=row[9] or "",
        location=row[10] or "",
        appearance_desc=row[11] or "",
        core_personality=row[12] or "",
        self_perception=row[13] or "",
        attitude_to_user=row[14] or "",
        likes=row[15] or "",
        dislikes=row[16] or "",
        tone_base=row[17] or "",
        word_habits=row[18] or "",
        emotion_rules=row[19] or "",
        length_pref=row[20] or "",
        special_logic_list=row[21] or "",
        few_shot_examples=row[22] or "",
        is_active=bool(row[23]) if row[23] is not None else True,
    )


def _card_to_insert_values(card: CharacterCard) -> tuple[Any, ...]:
    return (
        card.role_overview,
        card.formal_name,
        card.nickname,
        card.race_or_form,
        card.gender,
        card.visual_age,
        card.actual_age,
        card.location,
        card.appearance_desc,
        card.core_personality,
        card.self_perception,
        card.attitude_to_user,
        card.likes,
        card.dislikes,
        card.tone_base,
        card.word_habits,
        card.emotion_rules,
        card.length_pref,
        card.special_logic_list,
        card.few_shot_examples,
        1 if card.is_active else 0,
    )


async def insert_character_card(
    db: Any,
    user_id: str,
    conversation_id: str | None = None,
    card_data: dict[str, Any] | None = None,
) -> str:
    """
    插入角色卡数据

    Args:
        db: 数据库连接
        user_id: 用户ID
        conversation_id: 会话ID（可选，用于多角色卡场景）
        card_data: 角色卡数据，为空则使用默认数据

    Returns:
        角色卡ID
    """
    merged: dict[str, Any] = {**DEFAULT_CHARACTER_CARD_DATA, **(card_data or {})}
    card_id = str(uuid.uuid4())

    await db.execute(
        """
        INSERT INTO character_cards (
            id, user_id, conversation_id,
            role_overview, formal_name, nickname, race_or_form, gender,
            visual_age, actual_age, location, appearance_desc,
            core_personality, self_perception, attitude_to_user, likes, dislikes,
            tone_base, word_habits, emotion_rules, length_pref,
            special_logic_list, few_shot_examples, is_active
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            card_id,
            user_id,
            conversation_id,
            merged["role_overview"],
            merged["formal_name"],
            merged["nickname"],
            merged["race_or_form"],
            merged["gender"],
            merged["visual_age"],
            merged["actual_age"],
            merged["location"],
            merged["appearance_desc"],
            merged["core_personality"],
            merged["self_perception"],
            merged["attitude_to_user"],
            merged["likes"],
            merged["dislikes"],
            merged["tone_base"],
            merged["word_habits"],
            merged["emotion_rules"],
            merged["length_pref"],
            merged["special_logic_list"],
            merged["few_shot_examples"],
            1,
        ),
    )
    await db.commit()
    logger.info(
        "Inserted character card id=%s user=%s conversation=%s",
        card_id,
        user_id,
        conversation_id,
    )
    return card_id


async def get_character_card_by_conversation(
    db: Any,
    user_id: str,
    conversation_id: str,
) -> CharacterCard | None:
    """
    根据会话ID获取角色卡

    Args:
        db: 数据库连接
        user_id: 用户ID
        conversation_id: 会话ID

    Returns:
        角色卡对象，不存在返回 None
    """
    cursor = await db.execute(
        f"""
        SELECT {_SELECT_FIELDS}
        FROM character_cards
        WHERE user_id = ? AND conversation_id = ?
        """,
        (user_id, conversation_id),
    )
    row = await cursor.fetchone()
    return _row_to_character_card(row) if row else None


async def get_fallback_character_card_for_user(db: Any, user_id: str) -> CharacterCard | None:
    """
    用户下「角色库」卡片（conversation_id 为空）的兜底选择：
    优先 is_active=1，其次 updated_at 最新。
    """
    cursor = await db.execute(
        f"""
        SELECT {_SELECT_FIELDS}
        FROM character_cards
        WHERE user_id = ? AND conversation_id IS NULL
        ORDER BY is_active DESC, datetime(updated_at) DESC
        LIMIT 1
        """,
        (user_id,),
    )
    row = await cursor.fetchone()
    return _row_to_character_card(row) if row else None


async def _get_default_character_card(db: Any, user_id: str) -> CharacterCard | None:
    """兼容旧名：等价于 get_fallback_character_card_for_user。"""
    return await get_fallback_character_card_for_user(db, user_id)


async def get_character_card_by_id(db: Any, user_id: str, card_id: str) -> CharacterCard | None:
    cache_key = f"char:{user_id}:{card_id}"
    cached = _cache.character.get(cache_key)
    if cached is not None:
        return cached

    cursor = await db.execute(
        f"""
        SELECT {_SELECT_FIELDS}
        FROM character_cards
        WHERE id = ? AND user_id = ?
        """,
        (card_id, user_id),
    )
    row = await cursor.fetchone()
    card = _row_to_character_card(row) if row else None

    if card:
        _cache.character.set(cache_key, card)

    return card


async def list_character_cards_for_user(db: Any, user_id: str) -> list[CharacterCard]:
    cache_key = f"chars:{user_id}"
    cached = _cache.character_list.get(cache_key)
    if cached is not None:
        return cached

    cursor = await db.execute(
        f"""
        SELECT {_SELECT_FIELDS}
        FROM character_cards
        WHERE user_id = ?
        ORDER BY datetime(updated_at) DESC
        """,
        (user_id,),
    )
    rows = await cursor.fetchall()
    cards = [_row_to_character_card(row) for row in rows]

    _cache.character_list.set(cache_key, cards)
    return cards


async def upsert_character_card(db: Any, card: CharacterCard) -> None:
    """按主键 id 插入或覆盖（与前端 char_* id 对齐）。"""
    values = _card_to_insert_values(card)
    await db.execute(
        """
        INSERT OR REPLACE INTO character_cards (
            id, user_id, conversation_id,
            role_overview, formal_name, nickname, race_or_form, gender,
            visual_age, actual_age, location, appearance_desc,
            core_personality, self_perception, attitude_to_user, likes, dislikes,
            tone_base, word_habits, emotion_rules, length_pref,
            special_logic_list, few_shot_examples, is_active
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            card.id,
            card.user_id,
            card.conversation_id,
            *values,
        ),
    )
    await db.commit()
    logger.info("Upserted character card id=%s user=%s", card.id, card.user_id)

    _cache.invalidate_character(card.user_id, card.id)


async def delete_character_card_by_id(db: Any, user_id: str, card_id: str) -> bool:
    cursor = await db.execute(
        "DELETE FROM character_cards WHERE id = ? AND user_id = ?",
        (card_id, user_id),
    )
    await db.commit()
    deleted = (cursor.rowcount or 0) > 0
    if deleted:
        logger.info("Deleted character card id=%s user=%s", card_id, user_id)
        _cache.invalidate_character(user_id, card_id)
    return deleted


async def get_character_card_for_chat(
    db: Any,
    user_id: str,
    character_id: str | None,
    conversation_id: str | None,
) -> CharacterCard:
    """
    为对话解析角色卡（静态部分）：
    1. 若提供 character_id：按 id + user_id 取库中卡片；
    2. 否则若提供 conversation_id：取会话绑定快照；
    3. 否则取用户角色库兜底（is_active 优先，否则最新）；
    4. 若仅有 conversation_id 且无库卡：从兜底复制到会话；
    5. 若仍无：插入默认模板。
    """
    if character_id:
        card = await get_character_card_by_id(db, user_id, character_id)
        if card:
            return card

    if conversation_id:
        conv_card = await get_character_card_by_conversation(db, user_id, conversation_id)
        if conv_card:
            return conv_card

    fallback = await get_fallback_character_card_for_user(db, user_id)
    if fallback:
        if conversation_id:
            return await _insert_copy_for_conversation(db, user_id, conversation_id, fallback)
        return fallback

    await insert_character_card(db, user_id, conversation_id, None)
    if conversation_id:
        loaded = await get_character_card_by_conversation(db, user_id, conversation_id)
    else:
        loaded = await get_fallback_character_card_for_user(db, user_id)
    if not loaded:
        msg = f"Failed to load character card after insert user={user_id} conversation={conversation_id}"
        raise RuntimeError(msg)
    return loaded


async def _insert_copy_for_conversation(
    db: Any,
    user_id: str,
    conversation_id: str,
    source: CharacterCard,
) -> CharacterCard:
    """从已有角色卡复制一条记录并绑定到指定会话。"""
    new_id = str(uuid.uuid4())
    values = _card_to_insert_values(source)
    await db.execute(
        """
        INSERT INTO character_cards (
            id, user_id, conversation_id,
            role_overview, formal_name, nickname, race_or_form, gender,
            visual_age, actual_age, location, appearance_desc,
            core_personality, self_perception, attitude_to_user, likes, dislikes,
            tone_base, word_habits, emotion_rules, length_pref,
            special_logic_list, few_shot_examples, is_active
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (new_id, user_id, conversation_id, *values),
    )
    await db.commit()
    card = await get_character_card_by_conversation(db, user_id, conversation_id)
    if not card:
        msg = f"Failed to load cloned character card for user={user_id} conversation={conversation_id}"
        raise RuntimeError(msg)
    logger.info(
        "Cloned character card from %s to conversation=%s new_id=%s",
        source.id,
        conversation_id,
        new_id,
    )
    return card


async def get_or_create_character_card(
    db: Any,
    user_id: str,
    conversation_id: str | None = None,
) -> CharacterCard:
    """兼容旧调用：等价于未指定 character_id 的 get_character_card_for_chat。"""
    return await get_character_card_for_chat(db, user_id, None, conversation_id)
