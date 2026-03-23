"""
Prompt Builder - Constructs context for LLM
Implements: 8 recent + 6 RAG + 6 intent prediction

角色卡模板系统：
- 静态字段：初始化时从角色卡加载，后续保持不变
- 动态字段：每次对话实时获取（current_emotion、memory_summary_bullets）
"""

from __future__ import annotations

from typing import Any

from ..core import get_logger, settings
from ..database import get_db
from .character_card import (
    CharacterCard,
    get_character_card_for_chat,
)
from .conversation_service import conversation_service
from .emotion import EmotionData, EmotionEngine, emotion_label_from_va
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

【AI 当前情绪】
- 情绪状态：{ai_emotion_label}
- 愉悦度：{ai_valence:.2f} (-1.0=消极 ~ 1.0=积极)
- 激动度：{ai_arousal:.2f} (0.0=平静 ~ 1.0=激动)

【用户情绪】
- 情绪状态：{user_emotion_label}
- 愉悦度：{user_valence:.2f}
- 激动度：{user_arousal:.2f}

【回复要求】
1. 保持你当前的情绪状态进行回复
2. 对用户的情绪给予适当的共情回应
3. 不要暴露你在分析情绪

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

    async def build_context(
        self,
        user_id: str,
        conversation_id: str | None,
        current_message: str,
        memories: list[dict[str, Any]],
        user_emotion: EmotionData,
        character_id: str | None = None,
    ) -> list[dict[str, str]]:
        system_prompt = await self._build_system_prompt(
            user_id=user_id,
            conversation_id=conversation_id,
            current_message=current_message,
            user_emotion=user_emotion,
            character_id=character_id,
            memories=memories,
        )

        messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]

        if conversation_id:
            history = await conversation_service.get_conversation_history(conversation_id)
            logger.debug(
                "Loaded %d history messages for conversation=%s",
                len(history),
                conversation_id,
            )
            for msg in history:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"],
                })

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

        logger.info(
            "Built context: total_messages=%d, history=%d, rag_memories=%d",
            len(messages),
            len(history) if conversation_id else 0,
            len(memories) if memories else 0,
        )

        return messages

    async def _load_character_card(
        self,
        user_id: str,
        conversation_id: str | None,
        character_id: str | None,
    ) -> CharacterCard:
        """
        加载角色卡数据（静态部分，缓存后不变）

        缓存键包含 character_id，避免多角色切换时串卡。
        """
        cache_key = f"{user_id}:{conversation_id or 'default'}:{character_id or 'none'}"

        if cache_key in self._character_card_cache:
            return self._character_card_cache[cache_key]

        card = await self._fetch_character_card_for_prompt(user_id, character_id, conversation_id)
        self._character_card_cache[cache_key] = card
        logger.info(
            "Loaded character card for user=%s conversation=%s character=%s",
            user_id,
            conversation_id,
            character_id,
        )

        return card

    async def _fetch_character_card_for_prompt(
        self,
        user_id: str,
        character_id: str | None,
        conversation_id: str | None,
    ) -> CharacterCard:
        async with get_db() as db:
            return await get_character_card_for_chat(db, user_id, character_id, conversation_id)

    def clear_character_card_cache(self, user_id: str, conversation_id: str | None) -> None:
        """
        清除某一 user+conversation 下所有 character 变体的缓存键。
        """
        prefix = f"{user_id}:{conversation_id or 'default'}:"
        keys_to_delete = [k for k in self._character_card_cache if k.startswith(prefix)]
        for k in keys_to_delete:
            del self._character_card_cache[k]
        if keys_to_delete:
            logger.info(
                "Cleared character card cache for user=%s conversation=%s (%d keys)",
                user_id,
                conversation_id,
                len(keys_to_delete),
            )

    def clear_character_card_cache_for_user(self, user_id: str) -> None:
        """清除该用户下所有角色卡缓存条目（任意 conversation / character 组合）。"""
        prefix = f"{user_id}:"
        keys_to_delete = [key for key in self._character_card_cache if key.startswith(prefix)]
        for key in keys_to_delete:
            del self._character_card_cache[key]
        if keys_to_delete:
            logger.info(
                "Cleared %d character card cache keys for user=%s", len(keys_to_delete), user_id
            )

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

    def _format_memory_summary_bullets(self, memories: list[dict[str, Any]]) -> str:
        """由已检索的 RAG 结果格式化关键记忆摘要，避免重复 search。"""
        if not memories:
            return "- 暂无相关记忆"

        bullets = []
        for mem in memories[: settings.memory.rag_top_k]:
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
        memories: list[dict[str, Any]],
        character_id: str | None = None,
    ) -> str:
        """
        构建系统提示词

        静态字段从角色卡加载，动态字段实时获取
        """
        card = await self._load_character_card(user_id, conversation_id, character_id)

        if settings.app.debug:
            ai_emotion = EmotionData(valence=0.0, arousal=0.3, label="中性")
        elif not settings.emotion.ai_emotion_enabled:
            bv, ba = (
                settings.emotion.default_base_valence,
                settings.emotion.default_base_arousal,
            )
            ai_emotion = EmotionData(
                valence=bv,
                arousal=ba,
                label=emotion_label_from_va(bv, ba),
            )
        else:
            ai_emotion = await self.emotion_engine.step_ai_emotion(
                user_id, character_id, current_message, user_emotion
            )

        user_emotion_label = await self._get_current_emotion(current_message, user_emotion)
        ai_emotion_label = ai_emotion.label or emotion_label_from_va(
            ai_emotion.valence, ai_emotion.arousal
        )
        memory_bullets = self._format_memory_summary_bullets(memories)

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
            ai_emotion_label=ai_emotion_label,
            ai_valence=ai_emotion.valence,
            ai_arousal=ai_emotion.arousal,
            user_emotion_label=user_emotion_label,
            user_valence=user_emotion.valence,
            user_arousal=user_emotion.arousal,
            memory_summary_bullets=memory_bullets,
            few_shot_examples=card.few_shot_examples,
        )
