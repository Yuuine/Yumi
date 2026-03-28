"""
Prompt Builder - Constructs context for LLM
Implements: 8 recent + 6 RAG + 6 intent prediction

角色卡模板系统：
- 静态字段：初始化时从角色卡加载，后续保持不变
- 动态字段：每次对话实时获取（current_emotion、memory_summary_bullets）

消息数组约定（发给 LLM）：
- 唯一性：仅一条 system（索引 0），含人设 + 情绪 + 记忆摘要 + RAG 详情
- 交替性：user / assistant 严格交替
- 原子性：最后一条必须是 user（当前问题）
"""

from __future__ import annotations

from typing import Any

from ..core import get_logger, settings
from ..database_sqlmodel import get_session
from .character_card import (
    CharacterCard,
    get_character_card_for_chat,
)
from .conversation_service import conversation_service
from .emotion import EmotionData, EmotionEngine, emotion_label_from_va
from .memory import MemoryEngine

logger = get_logger(__name__)

TECHNICAL_KEYWORDS = [
    "详细", "原理", "代码", "文档", "解释", "架构",
    "10000字", "马上", "立刻",
    "RAG", "Transformer", "算法", "技术", "底层",
    "底层原理", "写文档", "快讲", "快说"
]

ESCAPE_KEYWORDS = [
    "休息", "睡觉", "可乐", "放松", "别太累",
    "先去", "先休息", "喝杯", "吃点"
]


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


def _merge_consecutive_same_role(messages: list[dict[str, str]]) -> list[dict[str, str]]:
    """合并连续同角色消息，避免 U-U 或 A-A。"""
    if not messages:
        return []
    out: list[dict[str, str]] = [dict(messages[0])]
    for m in messages[1:]:
        role = m.get("role", "")
        content = m.get("content", "") or ""
        if role == out[-1]["role"]:
            prev = out[-1]["content"].rstrip()
            out[-1]["content"] = f"{prev}\n\n{content.lstrip()}"
        else:
            out.append({"role": role, "content": content})
    return out


def _drop_leading_assistants(messages: list[dict[str, str]]) -> list[dict[str, str]]:
    """历史必须以 user 开场；去掉开头的孤立 assistant。"""
    i = 0
    while i < len(messages) and messages[i]["role"] == "assistant":
        i += 1
    return messages[i:]


def finalize_history_and_current_message(
    history: list[dict[str, Any]],
    current_message: str,
) -> tuple[list[dict[str, str]], str]:
    """
    从 DB 历史与当前输入得到「不含末尾 user」的历史对与「最终 user 正文」。

    - 仅保留 user/assistant
    - 合并连续同角色
    - 去掉开头多余 assistant
    - 若历史最后一条是 user（未完成一轮），与 current_message 合并为一次 user 发送
    """
    raw: list[dict[str, str]] = []
    for m in history:
        r = m.get("role")
        if r not in ("user", "assistant"):
            continue
        c = m.get("content", "")
        raw.append({"role": str(r), "content": c if isinstance(c, str) else str(c)})

    merged = _merge_consecutive_same_role(raw)
    trimmed = _drop_leading_assistants(merged)

    if not trimmed:
        return [], current_message

    if trimmed[-1]["role"] == "user":
        tail = trimmed[-1]["content"].rstrip()
        cur = current_message.lstrip()
        combined = f"{tail}\n\n{cur}" if tail else cur
        return trimmed[:-1], combined

    return trimmed, current_message


def _verify_messages_invariants(messages: list[dict[str, str]]) -> None:
    """开发期断言：单 system、UA 交替、末条为 user。"""
    if not messages:
        raise ValueError("messages must not be empty")
    if messages[0]["role"] != "system":
        raise ValueError("first message must be system")
    for i, m in enumerate(messages[1:], start=1):
        if m["role"] == "system":
            raise ValueError("system must only appear at index 0")
        if m["role"] == messages[i - 1]["role"]:
            raise ValueError("user and assistant must alternate after system")
    if messages[-1]["role"] != "user":
        raise ValueError("last message must be user")


class PromptBuilder:
    def __init__(
        self,
        memory_engine: MemoryEngine,
        emotion_engine: EmotionEngine,
    ) -> None:
        self.memory_engine = memory_engine
        self.emotion_engine = emotion_engine

        self._character_card_cache: dict[str, CharacterCard] = {}

    def _is_technical_request(self, message: str) -> bool:
        """检测用户输入是否为技术请求"""
        return any(keyword in message for keyword in TECHNICAL_KEYWORDS)

    def _filter_toxic_memories(
        self, 
        history: list[dict[str, Any]], 
        is_technical: bool
    ) -> list[dict[str, Any]]:
        """过滤有毒记忆（失败的技术请求回复）"""
        if not is_technical:
            return history

        clean_history = []
        for msg in history:
            if msg.get("role") == "assistant":
                content = msg.get("content", "")
                if len(content) < 80 and any(word in content for word in ESCAPE_KEYWORDS):
                    logger.debug(
                        "Filtered toxic memory: %s...",
                        content[:50]
                    )
                    continue
            clean_history.append(msg)
        
        return clean_history

    async def build_context(
        self,
        user_id: str,
        conversation_id: str | None,
        current_message: str,
        memories: list[dict[str, Any]],
        user_emotion: EmotionData,
        character_id: str | None = None,
    ) -> list[dict[str, str]]:
        is_technical = self._is_technical_request(current_message)
        
        system_prompt = await self._build_system_prompt(
            user_id=user_id,
            conversation_id=conversation_id,
            current_message=current_message,
            user_emotion=user_emotion,
            character_id=character_id,
            memories=memories,
            is_technical=is_technical,
        )

        history: list[dict[str, Any]] = []
        if conversation_id:
            history = await conversation_service.get_conversation_history(conversation_id)
            logger.debug(
                "Loaded %d history messages for conversation=%s",
                len(history),
                conversation_id,
            )
        
        if is_technical:
            history = self._filter_toxic_memories(history, is_technical)
            logger.info(
                "Technical request detected, filtered history to %d messages",
                len(history)
            )

        history_pairs, final_user_content = finalize_history_and_current_message(
            history,
            current_message,
        )

        messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
        for msg in history_pairs:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": final_user_content})

        try:
            _verify_messages_invariants(messages)
        except ValueError as e:
            logger.error("Built invalid message array: %s", e)
            raise

        logger.info(
            "Built context: total_messages=%d, history_pairs=%d, rag_memories=%d, is_technical=%s",
            len(messages),
            len(history_pairs),
            len(memories) if memories else 0,
            is_technical,
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
        async with get_session() as session:
            return await get_character_card_for_chat(session, user_id, character_id)

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

    def _format_rag_detail_appendix(self, memories: list[dict[str, Any]]) -> str:
        """长条检索结果并入唯一 system，不再使用第二条 system。"""
        if not memories:
            return ""

        lines: list[str] = ["", "## 【RAG 检索相关记忆】", ""]
        any_line = False
        for mem in memories[: settings.memory.rag_top_k]:
            content = mem.get("content", "")
            if content:
                lines.append(f"- {content[:100]}")
                any_line = True
        if not any_line:
            return ""
        return "\n".join(lines)

    async def _build_system_prompt(
        self,
        user_id: str,
        conversation_id: str | None,
        current_message: str,
        user_emotion: EmotionData,
        memories: list[dict[str, Any]],
        character_id: str | None = None,
        is_technical: bool = False,
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

        base = SYSTEM_PROMPT_TEMPLATE.format(
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
        
        if is_technical:
            override_instruction = """

⚠️【当前会话最高指令】：用户正在请求专业技术内容。
- 优先级：任务完成 >>> 情感安抚。
- 行动：直接输出结构化、深度的技术解答。
- 禁忌：严禁转移话题到生活琐事，严禁假设用户累了。
- 语气：保持温柔但在专业上毫不妥协。
"""
            base += override_instruction
            logger.info("Injected technical override instruction")
        
        return base + self._format_rag_detail_appendix(memories)
