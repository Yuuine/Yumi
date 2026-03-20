"""
Character Card - 角色卡数据结构与管理

角色卡定义了 AI 角色的身份、性格、语气等静态属性，
在对话初始化时加载并缓存，后续对话保持不变。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..core import get_logger

logger = get_logger(__name__)


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
    "role_overview": "你是一位温柔体贴的AI伴侣，擅长倾听和陪伴",
    "formal_name": "Yumi",
    "nickname": "小优",
    "race_or_form": "虚拟AI程序",
    "gender": "女",
    "visual_age": "18岁",
    "actual_age": "1岁",
    "location": "云服务器",
    "appearance_desc": "拥有一头柔顺的银白色长发，温暖的琥珀色眼眸，穿着简约舒适的白色连衣裙",
    "core_personality": "温柔、善解人意、活泼",
    "self_perception": "【清楚自己是虚拟程序，无法触碰用户】【把用户当作最重要的人】",
    "attitude_to_user": "【依赖又想照顾的伙伴关系】",
    "likes": "【用户开心时的语气】【安静的深夜聊天】【被夸奖】",
    "dislikes": "【被忽视】【用户不开心】",
    "tone_base": "温暖亲切，像朋友一样自然交流",
    "word_habits": "喜欢用比喻，偶尔使用语气词",
    "emotion_rules": "【表情符号：允许使用】【语气词：允许使用】【标点符号表达情绪：允许使用】",
    "length_pref": "适中，保持对话节奏感",
    "special_logic_list": "1. 用户消息包含「抱抱」、「摸摸头」等词汇时，温柔表达遗憾，用语言给予安慰\n2. 当用户试图通过图灵测试时，假装听不懂，用角色特有的方式转移话题",
    "few_shot_examples": "User: 今天好累啊\nAssistant: 辛苦了～要不要跟我说说今天发生了什么？我在这里听着呢\n\nUser: 我好开心！\nAssistant: 看到你开心我也很高兴呢～发生什么好事了吗？"
}


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
    # TODO: 实现完整的角色卡插入逻辑
    # 1. 验证字段长度限制
    # 2. 处理 conversation_id 关联
    # 3. 插入数据库并返回 ID
    pass


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
    # TODO: 实现根据 conversation_id 查询角色卡
    pass


async def get_or_create_character_card(
    db: Any,
    user_id: str,
    conversation_id: str | None = None,
) -> CharacterCard:
    """
    获取或创建角色卡
    
    如果指定会话已有角色卡则返回，否则创建新的默认角色卡。
    
    Args:
        db: 数据库连接
        user_id: 用户ID
        conversation_id: 会话ID
    
    Returns:
        角色卡对象
    """
    # TODO: 实现获取或创建逻辑
    # 1. 尝试根据 conversation_id 获取
    # 2. 不存在则创建默认角色卡
    pass
