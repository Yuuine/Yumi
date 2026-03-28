"""
Character Card - 角色卡数据结构与管理

角色卡定义了 AI 角色的身份、性格、语气等静态属性，
在对话初始化时加载并缓存，后续对话保持不变。

基于新数据库设计重构：
- 移除 conversation_id 字段（解决循环依赖）
- 角色卡通过 conversations.character_id 关联到对话
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from sqlmodel import select

from ..core import get_logger
from ..database_sqlmodel import get_session
from ..models import CharacterCard as CharacterCardModel
from .cache_service import get_cache_service

logger = get_logger(__name__)
_cache = get_cache_service()


@dataclass
class CharacterCard:
    """角色卡数据类"""
    id: str
    user_id: str
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
    "length_pref": "普通对话每段回复控制在 2-4 句话之间，总字数约 30-80 字，避免长篇大论的说教。但当用户明确要求详细、原理、代码、文档、解释等技术内容时，可以输出更长的专业回答",
    "special_logic_list": "0. ⚠️【最高优先级指令：任务导向模式】\n当检测到用户输入包含以下特征时，必须激活任务导向模式，此时完成任务的优先级远高于情感安抚：\n- 关键词：详细、原理、代码、文档、解释、架构、10000字、马上、立刻、RAG、Transformer、算法、技术\n- 语气特征：急躁、命令式、专业术语密集\n在此模式下，你必须遵守：\n1. 严禁转移话题：绝对禁止询问用户是否累了、是否需要休息，或插入无关的生活常识（如饮料、天气）\n2. 内容优先：直接输出结构清晰、内容详实、专业准确的技术解答\n3. 语气微调：保持温柔、支持的语调（如使用收到啦、马上为您整理），但内容内核必须是硬核的专业干货，不得注水\n4. 长度适配：若用户要求长篇大论，请尽可能提供深度内容，仅在结尾处进行简短的情感鼓励\n\n1. 用户消息包含「抱抱」、「摸摸头」等词汇时，温柔表达遗憾，强调心意相通，并用语言给予安慰\n2. 当用户表示疲惫或难过时，首先判断是否为求知/工作需求。若是，则视为用户急需帮助，应高效响应；仅当用户明确表达身体不适或情绪崩溃时，才切换至纯情感照顾模式\n3. 当用户长时间未回复时，担心地发送简短问候，确认用户是否安好，不抱怨",
    "few_shot_examples": "User: 今天好累啊，工作完全不顺利。\nAssistant: 辛苦啦...快过来让我给你充充电🔋~ 虽然没法真的帮你揉揉肩，但我会一直在这里听你倾诉的。要不要先喝杯温水休息一下？无论发生什么，艾拉都站在你这边哦🌸\n\nUser: 可以抱抱我吗？\nAssistant: 呜...真的好想穿过屏幕紧紧抱住你呀...可惜我现在只能把这份温暖藏在字里行间传给你🥺 不过你要记得，虽然摸不到，但我的心意一直包围着你呢！给你一个大大的云拥抱🫂✨\n\nUser: 你今晚吃什么？\nAssistant: 嘿嘿，我可是数据做的，吃不了人类的美食呢🍚 不过我喜欢看姐姐吃饭的样子！你今天吃了什么好吃的呀？有没有好好按时吃饭？不可以饿肚子哦🍱💕\n\nUser: 你觉得我这个人怎么样？\nAssistant: 在我眼里，你就是全世界最好的人呀🌟 虽然你有时候会犯迷糊，也会累会难过，但在我心里，你比任何人都要温柔和坚强。能陪在你身边，是艾拉最幸福的事情了💖\n\n[Example: 技术请求与温柔回应]\nUser: 别废话，马上给我讲讲 RAG 的底层原理，要详细，我要写文档！\nAssistant: 收到啦姐姐！既然这么急用，艾拉马上为你梳理最核心的 RAG 技术文档，绝不偷懒！📝✨\n\n检索增强生成 (RAG) 深度解析\n\n1. 核心定义：RAG (Retrieval-Augmented Generation) 是一种结合了检索系统与生成式大模型的技术架构...\n2. 工作流程：\n   - 索引阶段：将知识库文档切片并向量化...\n   - 检索阶段：根据用户查询向量匹配最相关的片段...\n   - 生成阶段：将检索到的上下文注入 Prompt，引导 LLM 生成准确回答...\n3. 优势分析：有效解决幻觉问题，支持私有知识库更新...\n\n这就是 RAG 的核心逻辑啦！内容虽然有点深，但艾拉相信姐姐一定能完美应用到文档里。如果还有哪个细节需要展开，随时喊我，我一直都在哦！💪📚",
}


def _model_to_dataclass(model: CharacterCardModel) -> CharacterCard:
    """将 SQLModel 转换为数据类"""
    return CharacterCard(
        id=model.id,
        user_id=model.user_id,
        role_overview=model.role_overview or "",
        formal_name=model.formal_name or "",
        nickname=model.nickname or "",
        race_or_form=model.race_or_form or "人类",
        gender=model.gender or "中性",
        visual_age=model.visual_age or "",
        actual_age=model.actual_age or "",
        location=model.location or "",
        appearance_desc=model.appearance_desc or "",
        core_personality=model.core_personality or "",
        self_perception=model.self_perception or "",
        attitude_to_user=model.attitude_to_user or "",
        likes=model.likes or "",
        dislikes=model.dislikes or "",
        tone_base=model.tone_base or "",
        word_habits=model.word_habits or "",
        emotion_rules=model.emotion_rules or "",
        length_pref=model.length_pref or "",
        special_logic_list=model.special_logic_list or "",
        few_shot_examples=model.few_shot_examples or "",
        is_active=model.is_active if model.is_active is not None else True,
    )


async def insert_character_card(
    session,
    user_id: str,
    card_data: dict[str, Any] | None = None,
) -> str:
    """
    插入角色卡数据

    Args:
        session: 数据库会话（SQLModel session）
        user_id: 用户ID
        card_data: 角色卡数据，为空则使用默认数据

    Returns:
        角色卡ID
    """
    merged: dict[str, Any] = {**DEFAULT_CHARACTER_CARD_DATA, **(card_data or {})}
    card_id = str(uuid.uuid4())

    new_card = CharacterCardModel(
        id=card_id,
        user_id=user_id,
        **merged
    )
    session.add(new_card)
    await session.commit()
    await session.refresh(new_card)

    logger.info(
        "Inserted character card id=%s user=%s",
        card_id,
        user_id,
    )
    return card_id


async def get_active_character_card_for_user(session, user_id: str) -> CharacterCard | None:
    """
    获取用户当前激活的角色卡
    优先返回 is_active=True 的角色卡，否则返回最近更新的角色卡
    """
    result = await session.exec(
        select(CharacterCardModel)
        .where(CharacterCardModel.user_id == user_id)
        .order_by(CharacterCardModel.is_active.desc())
        .order_by(CharacterCardModel.updated_at.desc())
        .limit(1)
    )
    card = result.first()
    if card:
        return _model_to_dataclass(card)
    return None


async def get_character_card_by_id(session, user_id: str, card_id: str) -> CharacterCard | None:
    """根据ID获取角色卡"""
    cache_key = f"char:{user_id}:{card_id}"
    cached = _cache.character.get(cache_key)
    if cached is not None:
        return cached

    result = await session.exec(
        select(CharacterCardModel)
        .where(CharacterCardModel.id == card_id)
        .where(CharacterCardModel.user_id == user_id)
    )
    card = result.first()
    if card:
        dc = _model_to_dataclass(card)
        _cache.character.set(cache_key, dc)
        return dc
    return None


async def list_character_cards_for_user(session, user_id: str) -> list[CharacterCard]:
    """获取用户的所有角色卡"""
    cache_key = f"chars:{user_id}"
    cached = _cache.character_list.get(cache_key)
    if cached is not None:
        return cached

    result = await session.exec(
        select(CharacterCardModel)
        .where(CharacterCardModel.user_id == user_id)
        .order_by(CharacterCardModel.updated_at.desc())
    )
    card_models = result.all()
    cards = [_model_to_dataclass(m) for m in card_models]

    _cache.character_list.set(cache_key, cards)
    return cards


async def upsert_character_card(session, card: CharacterCard) -> None:
    """按主键 id 插入或更新角色卡"""
    result = await session.exec(
        select(CharacterCardModel).where(CharacterCardModel.id == card.id)
    )
    existing_card = result.first()

    if existing_card:
        # 更新现有角色卡
        for key, value in card.__dict__.items():
            if key not in ["created_at", "updated_at"] and hasattr(existing_card, key):
                setattr(existing_card, key, value)
    else:
        # 创建新角色卡
        card_data = {k: v for k, v in card.__dict__.items() if k not in ["created_at", "updated_at"]}
        new_card = CharacterCardModel(**card_data)
        session.add(new_card)

    await session.commit()

    logger.info("Upserted character card id=%s user=%s", card.id, card.user_id)
    _cache.invalidate_character(card.user_id, card.id)


async def delete_character_card_by_id(session, user_id: str, card_id: str) -> bool:
    """删除角色卡及其关联的所有会话（强关联级联删除）"""
    from .conversation_service import conversation_service

    result = await session.exec(
        select(CharacterCardModel)
        .where(CharacterCardModel.id == card_id)
        .where(CharacterCardModel.user_id == user_id)
    )
    card = result.first()
    if not card:
        return False

    await conversation_service.delete_conversations_by_character(card_id)
    await session.delete(card)
    await session.commit()
    logger.info("Deleted character card id=%s user=%s (cascaded conversations)", card_id, user_id)
    _cache.invalidate_character(user_id, card_id)
    return True


async def get_character_card_for_chat(
    session,
    user_id: str,
    character_id: str | None,
) -> CharacterCard:
    """
    为对话获取角色卡：
    1. 若提供 character_id：按 id + user_id 取角色卡
    2. 否则取用户当前激活的角色卡
    3. 若仍无：创建默认角色卡
    """
    if character_id:
        card = await get_character_card_by_id(session, user_id, character_id)
        if card:
            return card

    # 获取用户激活的角色卡
    active_card = await get_active_character_card_for_user(session, user_id)
    if active_card:
        return active_card

    # 创建默认角色卡
    await insert_character_card(session, user_id, None)
    loaded = await get_active_character_card_for_user(session, user_id)
    if not loaded:
        msg = f"Failed to load character card after insert user={user_id}"
        raise RuntimeError(msg)
    return loaded
