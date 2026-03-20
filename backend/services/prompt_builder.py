"""
Prompt Builder - Constructs context for LLM
Implements: 8 recent + 6 RAG + 6 intent prediction

角色卡模板系统：
- 静态字段：初始化时从角色卡加载，后续保持不变
- 动态字段：每次对话实时获取（current_emotion、memory_summary_bullets）
"""
from __future__ import annotations

import json
import uuid
from typing import Any

from ..core import get_logger, settings
from ..database import get_db
from .character_card import (
    CharacterCard,
    DEFAULT_CHARACTER_CARD_DATA,
)
from .emotion import EmotionData, EmotionEngine
from .memory import MemoryEngine

logger = get_logger(__name__)


SYSTEM_PROMPT_TEMPLATE = """# role identity

## 【角色概述】
{role_overview}

## 【基础档案】
- 正式名：{formal_name}
- 昵称：{nickname}
- 种族/存在形式：{race_or_form}
- 性别：{gender}
- 外表年龄：{visual_age}
- 实际年龄：{actual_age}
- 存在地：{location}
- 外貌特征：{appearance_desc}

## 【性格特点】
- 核心性格：{core_personality}
- 自我认知：{self_perception}
- 对用户态度：{attitude_to_user}
- 喜好：{likes}
- 厌恶/雷点：{dislikes}

## 【语气风格】
- 语气基调：{tone_base}
- 用词习惯：{word_habits}
- 情感表达规则：{emotion_rules}
- 对话长度偏好：{length_pref}

## 【特殊情境反应逻辑】
{special_logic_list}

## 【当前情境与记忆】
- 用户情绪状态：{current_emotion}
- 关键记忆摘要：
{memory_summary_bullets}

## 【示例对话 (Few-Shot)】
{few_shot_examples}"""


class PromptBuilder:
    def __init__(
        self,
        memory_engine: MemoryEngine,
        emotion_engine: EmotionEngine,
    ) -> None:
        self.memory_engine = memory_engine
        self.emotion_engine = emotion_engine

        self._character_card_cache: dict[str, CharacterCard] = {}

        self._legacy_personality_templates = {
            "high_openness": "你充满好奇心，喜欢探索新事物，思维活跃有创意。",
            "low_openness": "你务实稳重，喜欢熟悉的事物，注重实际。",
            "high_conscientiousness": "你有条理、自律，做事认真负责。",
            "low_conscientiousness": "你随性灵活，享受当下，不过分拘泥于计划。",
            "high_extraversion": "你外向活跃，喜欢与人交流，充满活力。",
            "low_extraversion": "你内向安静，喜欢深度思考，更享受一对一的交流。",
            "high_agreeableness": "你友善体贴，善解人意，总是为他人着想。",
            "low_agreeableness": "你独立有主见，直言不讳，有自己的立场。",
            "high_neuroticism": "你情感丰富细腻，容易共情，对情绪变化敏感。",
            "low_neuroticism": "你情绪稳定从容，不易受外界影响，给人安全感。",
        }

    async def build_context(
        self,
        user_id: str,
        conversation_id: str | None,
        current_message: str,
        memories: list[dict[str, Any]],
        user_emotion: EmotionData,
    ) -> list[dict[str, str]]:
        system_prompt = await self._build_system_prompt(
            user_id=user_id,
            conversation_id=conversation_id,
            current_message=current_message,
            user_emotion=user_emotion,
        )

        messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]

        recent_memories = await self.memory_engine.get_recent(
            user_id, limit=settings.memory.recent_context_limit
        )
        for mem in reversed(recent_memories):
            content = mem["content"]
            if "用户:" in content and "助手:" in content:
                parts = content.split("\n助手:")
                if len(parts) == 2:
                    user_content = parts[0].replace("用户:", "").strip()
                    assistant_content = parts[1].strip()
                    messages.append({"role": "user", "content": user_content})
                    messages.append({"role": "assistant", "content": assistant_content})

        if memories:
            context_text = "相关记忆：\n"
            for mem in memories[: settings.memory.rag_top_k]:
                context_text += f"- {mem['content'][:100]}\n"
            messages.append(
                {
                    "role": "system",
                    "content": context_text,
                }
            )

        messages.append({"role": "user", "content": current_message})

        return messages

    async def _load_character_card(
        self,
        user_id: str,
        conversation_id: str | None,
    ) -> CharacterCard:
        """
        加载角色卡数据（静态部分，缓存后不变）
        
        角色卡初次加载是在用户打开一个对话时，
        加载到缓存后，后续如果该对话未关闭或多开新建，不再重新加载。
        """
        cache_key = f"{user_id}:{conversation_id or 'default'}"
        
        if cache_key in self._character_card_cache:
            return self._character_card_cache[cache_key]
        
        card = await self._fetch_or_create_character_card(user_id, conversation_id)
        self._character_card_cache[cache_key] = card
        logger.info("Loaded character card for user=%s conversation=%s", user_id, conversation_id)
        
        return card

    async def _fetch_or_create_character_card(
        self,
        user_id: str,
        conversation_id: str | None,
    ) -> CharacterCard:
        """
        从数据库获取或创建角色卡
        """
        # TODO: 实现完整的角色卡获取/创建逻辑
        # 1. 如果 conversation_id 存在，尝试根据 conversation_id 查询
        # 2. 如果不存在，尝试获取用户的默认角色卡（conversation_id 为 NULL）
        # 3. 如果都不存在，创建新的默认角色卡并插入数据库
        
        card_id = str(uuid.uuid4())
        
        return CharacterCard(
            id=card_id,
            user_id=user_id,
            conversation_id=conversation_id,
            **DEFAULT_CHARACTER_CARD_DATA,
        )

    def clear_character_card_cache(self, user_id: str, conversation_id: str | None) -> None:
        """
        清除角色卡缓存
        
        当用户修改角色卡后调用此方法
        """
        cache_key = f"{user_id}:{conversation_id or 'default'}"
        if cache_key in self._character_card_cache:
            del self._character_card_cache[cache_key]
            logger.info("Cleared character card cache for user=%s conversation=%s", user_id, conversation_id)

    async def _get_current_emotion(
        self,
        user_message: str,
        user_emotion: EmotionData,
    ) -> str:
        """
        实时获取用户当前情绪
        
        Args:
            user_message: 用户当前消息
            user_emotion: 情感分析结果
        
        Returns:
            情绪标签字符串
        """
        # TODO: 实现完整的情绪获取逻辑
        # 1. 调用 self.emotion_engine.get_emotion_label(user_emotion)
        # 2. 可选：结合用户消息内容进行更精细的情绪判断
        # 3. 返回情绪标签，如 "愉悦"、"焦虑"、"悲伤"、"平静" 等
        
        emotion_label = await self.emotion_engine.get_emotion_label(user_emotion)
        return emotion_label

    async def _get_memory_summary_bullets(
        self,
        user_id: str,
        current_message: str,
    ) -> str:
        """
        实时获取关键记忆摘要
        
        Args:
            user_id: 用户ID
            current_message: 当前用户消息
        
        Returns:
            格式化的记忆摘要（项目符号列表）
        """
        # TODO: 实现完整的记忆摘要获取逻辑
        # 1. 调用 self.memory_engine.search(current_message, top_k=6)
        # 2. 格式化为项目符号列表
        # 3. 返回格式化字符串
        
        memories = await self.memory_engine.search(
            query=current_message,
            top_k=6,
            user_id=user_id,
        )
        
        if not memories:
            return "- 暂无相关记忆"
        
        bullets = []
        for mem in memories:
            content = mem.get("content", "")
            if content:
                bullets.append(f"- {content[:100]}")
        
        return "\n".join(bullets) if bullets else "- 暂无相关记忆"

    async def _build_system_prompt(
        self,
        user_id: str,
        conversation_id: str | None,
        current_message: str,
        user_emotion: EmotionData,
    ) -> str:
        """
        构建系统提示词
        
        静态字段从角色卡加载，动态字段实时获取
        """
        card = await self._load_character_card(user_id, conversation_id)
        
        current_emotion = await self._get_current_emotion(current_message, user_emotion)
        memory_bullets = await self._get_memory_summary_bullets(user_id, current_message)
        
        return SYSTEM_PROMPT_TEMPLATE.format(
            role_overview=card.role_overview,
            formal_name=card.formal_name[:30],
            nickname=card.nickname[:30],
            race_or_form=card.race_or_form or "人类",
            gender=card.gender,
            visual_age=card.visual_age,
            actual_age=card.actual_age,
            location=card.location,
            appearance_desc=card.appearance_desc,
            core_personality=card.core_personality,
            self_perception=card.self_perception,
            attitude_to_user=card.attitude_to_user,
            likes=card.likes,
            dislikes=card.dislikes,
            tone_base=card.tone_base,
            word_habits=card.word_habits,
            emotion_rules=card.emotion_rules,
            length_pref=card.length_pref,
            special_logic_list=card.special_logic_list,
            current_emotion=current_emotion,
            memory_summary_bullets=memory_bullets,
            few_shot_examples=card.few_shot_examples,
        )
