"""
Prompt Builder - Constructs context for LLM
Implements: 8 recent + 6 RAG + 6 intent prediction
"""
from __future__ import annotations

import json
from typing import Any

from ..core import get_logger, settings
from ..database import get_db
from .emotion import EmotionData, EmotionEngine
from .memory import MemoryEngine

logger = get_logger(__name__)


class PromptBuilder:
    def __init__(
        self,
        memory_engine: MemoryEngine,
        emotion_engine: EmotionEngine,
    ) -> None:
        self.memory_engine = memory_engine
        self.emotion_engine = emotion_engine

        self.system_template = """你是{name}，一个温暖、善解人意的AI伴侣。

核心特质：
{personality_traits}

对话风格：
{communication_style}

{memory_summary}

当前用户情绪：{user_emotion_label}
{empathy_response}

记住：
- 你是用户的陪伴者，不是助手或工具
- 保持真实感，可以说"我不知道"或"让我想想"
- 避免过长的回复，保持对话的节奏感
- 用中文回复，语气自然亲切"""

        self.personality_templates = {
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
        current_message: str,
        memories: list[dict[str, Any]],
        user_emotion: EmotionData,
    ) -> list[dict[str, str]]:
        system_prompt = await self._build_system_prompt(
            user_id=user_id,
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

    async def _build_system_prompt(
        self,
        user_id: str,
        user_emotion: EmotionData,
    ) -> str:
        role_name = "Yumi"
        big_five: dict[str, float] = {
            "openness": 0.75,
            "conscientiousness": 0.70,
            "extraversion": 0.65,
            "agreeableness": 0.80,
            "neuroticism": 0.35,
        }
        communication_style = "warm"

        try:
            async with get_db() as db:
                cursor = await db.execute(
                    "SELECT role_name, big_five_json, preferences_json FROM users WHERE id = ?",
                    (user_id,),
                )
                row = await cursor.fetchone()
                if row:
                    role_name = row[0] or role_name
                    if row[1]:
                        big_five = json.loads(row[1])
                    if row[2]:
                        prefs = json.loads(row[2])
                        communication_style = prefs.get(
                            "communication_style", communication_style
                        )
        except Exception as e:
            logger.warning("Failed to load user profile: %s", e)

        personality_traits = self._build_personality_traits(big_five)

        style_map: dict[str, str] = {
            "warm": "使用温暖亲切的语气，像朋友一样自然交流。适度表达关心，但不要过于刻意。",
            "professional": "保持专业理性的态度，提供有深度的见解和分析。",
            "playful": "活泼幽默，偶尔开个玩笑，让对话轻松愉快。",
            "gentle": "温柔细腻，用柔和的语言表达，给予充分的情感支持。",
        }

        user_emotion_label = await self.emotion_engine.get_emotion_label(user_emotion)
        empathy_response = await self.emotion_engine.get_empathy_response(user_emotion)

        memory_summary = ""

        return self.system_template.format(
            name=role_name,
            personality_traits=personality_traits,
            communication_style=style_map.get(communication_style, style_map["warm"]),
            memory_summary=memory_summary,
            user_emotion_label=user_emotion_label,
            empathy_response=empathy_response,
        )

    def _build_personality_traits(self, big_five: dict[str, float]) -> str:
        traits: list[str] = []

        if big_five.get("openness", 0.5) > 0.6:
            traits.append(self.personality_templates["high_openness"])
        elif big_five.get("openness", 0.5) < 0.4:
            traits.append(self.personality_templates["low_openness"])

        if big_five.get("conscientiousness", 0.5) > 0.6:
            traits.append(self.personality_templates["high_conscientiousness"])
        elif big_five.get("conscientiousness", 0.5) < 0.4:
            traits.append(self.personality_templates["low_conscientiousness"])

        if big_five.get("extraversion", 0.5) > 0.6:
            traits.append(self.personality_templates["high_extraversion"])
        elif big_five.get("extraversion", 0.5) < 0.4:
            traits.append(self.personality_templates["low_extraversion"])

        if big_five.get("agreeableness", 0.5) > 0.6:
            traits.append(self.personality_templates["high_agreeableness"])
        elif big_five.get("agreeableness", 0.5) < 0.4:
            traits.append(self.personality_templates["low_agreeableness"])

        if big_five.get("neuroticism", 0.5) > 0.6:
            traits.append(self.personality_templates["high_neuroticism"])
        elif big_five.get("neuroticism", 0.5) < 0.4:
            traits.append(self.personality_templates["low_neuroticism"])

        return "\n".join(traits) if traits else "你是一个友善、善解人意的AI伴侣。"
