"""
Emotion Engine - Emotion detection and analysis
Supports keyword-based analysis and optional transformer model
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel

from ..core import get_logger, settings

logger = get_logger(__name__)

_POSITIVE_EVENT_WORDS = ("开心", "高兴", "成功", "好消息", "太棒了")
_NEGATIVE_EVENT_WORDS = ("难过", "失败", "坏消息", "糟糕", "失望")


def emotion_label_from_va(valence: float, arousal: float) -> str:
    """与关键词分析器一致的情绪标签映射（效价–唤醒度）。"""
    if valence > 0.5 and arousal > 0.6:
        return "兴奋"
    if valence > 0.5 and arousal <= 0.6:
        return "开心"
    if valence > 0.2 and arousal <= 0.4:
        return "平静"
    if valence < -0.5 and arousal > 0.6:
        return "愤怒"
    if valence < -0.5 and arousal <= 0.6:
        return "悲伤"
    if valence < -0.2 and arousal > 0.5:
        return "焦虑"
    if valence < -0.2 and arousal <= 0.5:
        return "低落"
    if arousal > 0.7:
        return "激动"
    return "中性"


def _count_event_words(text: str) -> tuple[int, int]:
    n_pos = sum(1 for w in _POSITIVE_EVENT_WORDS if w in text)
    n_neg = sum(1 for w in _NEGATIVE_EVENT_WORDS if w in text)
    return n_pos, n_neg


@dataclass
class AIEmotionStateRecord:
    current_valence: float
    current_arousal: float
    base_valence: float
    base_arousal: float
    sensitivity: float
    last_updated: datetime


class EmotionData(BaseModel):
    valence: float
    arousal: float
    label: str | None = None
    confidence: float = 1.0


class EmotionAnalyzer(ABC):
    @abstractmethod
    async def analyze(self, text: str) -> EmotionData:
        pass

    @abstractmethod
    async def initialize(self) -> None:
        pass


class KeywordEmotionAnalyzer(EmotionAnalyzer):
    def __init__(self) -> None:
        self.positive_words = [
            "开心",
            "高兴",
            "快乐",
            "幸福",
            "喜欢",
            "爱",
            "美好",
            "温暖",
            "感谢",
            "谢谢",
            "棒",
            "好",
            "太好了",
            "哈哈",
            "嘻嘻",
            "满意",
            "兴奋",
            "期待",
            "希望",
            "信心",
            "成功",
            "胜利",
            "赞",
            "优秀",
        ]

        self.negative_words = [
            "难过",
            "伤心",
            "痛苦",
            "悲伤",
            "讨厌",
            "恨",
            "烦",
            "担心",
            "害怕",
            "焦虑",
            "紧张",
            "压力",
            "累",
            "疲惫",
            "沮丧",
            "失望",
            "绝望",
            "孤独",
            "寂寞",
            "无聊",
            "愤怒",
            "生气",
            "郁闷",
        ]

        self.high_arousal_words = [
            "激动",
            "兴奋",
            "愤怒",
            "生气",
            "害怕",
            "紧张",
            "焦虑",
            "惊喜",
            "震惊",
            "急",
            "疯狂",
            "狂喜",
        ]

        self.low_arousal_words = [
            "平静",
            "放松",
            "无聊",
            "疲惫",
            "困",
            "累",
            "懒",
            "安静",
            "沉默",
            "麻木",
        ]

        self.emotion_patterns: dict[str, tuple[float, float]] = {
            "开心": (0.8, 0.6),
            "高兴": (0.7, 0.5),
            "快乐": (0.8, 0.5),
            "幸福": (0.9, 0.4),
            "喜欢": (0.6, 0.4),
            "爱": (0.9, 0.5),
            "难过": (-0.7, 0.3),
            "伤心": (-0.8, 0.4),
            "痛苦": (-0.9, 0.6),
            "讨厌": (-0.6, 0.5),
            "愤怒": (-0.8, 0.9),
            "生气": (-0.7, 0.8),
            "害怕": (-0.5, 0.8),
            "焦虑": (-0.4, 0.7),
            "担心": (-0.3, 0.5),
            "平静": (0.1, 0.1),
            "无聊": (-0.2, 0.1),
        }

    async def initialize(self) -> None:
        logger.info("Keyword emotion analyzer initialized")

    async def analyze(self, text: str) -> EmotionData:
        valence = 0.0
        arousal = 0.3

        positive_count = sum(1 for word in self.positive_words if word in text)
        negative_count = sum(1 for word in self.negative_words if word in text)
        high_arousal_count = sum(1 for word in self.high_arousal_words if word in text)
        low_arousal_count = sum(1 for word in self.low_arousal_words if word in text)

        valence = (positive_count - negative_count) * 0.15
        valence = max(-1.0, min(1.0, valence))

        arousal += (high_arousal_count - low_arousal_count) * 0.1
        arousal = max(0.0, min(1.0, arousal))

        matched_label = None
        for pattern, (p_valence, p_arousal) in self.emotion_patterns.items():
            if pattern in text:
                valence = valence * 0.5 + p_valence * 0.5
                arousal = arousal * 0.5 + p_arousal * 0.5
                matched_label = pattern
                break

        label = matched_label or self._get_emotion_label(valence, arousal)

        return EmotionData(
            valence=round(valence, 3),
            arousal=round(arousal, 3),
            label=label,
            confidence=0.7 if matched_label else 0.5,
        )

    def _get_emotion_label(self, valence: float, arousal: float) -> str:
        return emotion_label_from_va(valence, arousal)


class TransformerEmotionAnalyzer(EmotionAnalyzer):
    def __init__(self, model_name: str = "uer/roberta-base-finetuned-chinanews-chinese") -> None:
        self.model_name = model_name
        self.pipeline: Any = None
        self.label_mapping = {
            "positive": (0.7, 0.5),
            "negative": (-0.7, 0.5),
            "neutral": (0.0, 0.3),
        }

    async def initialize(self) -> None:
        try:
            from transformers import pipeline

            self.pipeline = pipeline(
                "sentiment-analysis",
                model=self.model_name,
                return_all_scores=True,
            )
            logger.info("Transformer emotion analyzer initialized with model: %s", self.model_name)
        except ImportError:
            logger.warning("Transformers not installed, falling back to keyword analyzer")
            raise
        except Exception as e:
            logger.error("Failed to load transformer model: %s", e)
            raise

    async def analyze(self, text: str) -> EmotionData:
        if not self.pipeline:
            raise RuntimeError("Analyzer not initialized")

        results = self.pipeline(text[:512])

        if isinstance(results, list) and len(results) > 0:
            scores = {item["label"]: item["score"] for item in results[0]}

            valence = 0.0
            arousal = 0.3
            max_label = max(scores.keys(), key=lambda k: scores[k])
            confidence = scores[max_label]

            if "positive" in scores:
                valence += scores["positive"] * 0.7
            if "negative" in scores:
                valence -= scores["negative"] * 0.7

            label = self._map_label(max_label)

            return EmotionData(
                valence=round(valence, 3),
                arousal=round(arousal, 3),
                label=label,
                confidence=round(confidence, 3),
            )

        return EmotionData(valence=0.0, arousal=0.3, label="中性", confidence=0.5)

    def _map_label(self, label: str) -> str:
        label_lower = label.lower()
        if "positive" in label_lower:
            return "积极"
        if "negative" in label_lower:
            return "消极"
        return "中性"


class EmotionEngine:
    def __init__(self) -> None:
        self.analyzer: EmotionAnalyzer | None = None
        self._initialized = False
        self._ai_emotion_states: dict[str, AIEmotionStateRecord] = {}

    def _ai_state_key(self, user_id: str, character_id: str | None) -> str:
        return f"{user_id}\t{character_id or ''}"

    def _default_ai_state(self) -> AIEmotionStateRecord:
        now = datetime.now(timezone.utc)
        bv = settings.emotion.default_base_valence
        ba = settings.emotion.default_base_arousal
        sens = settings.emotion.default_sensitivity
        return AIEmotionStateRecord(bv, ba, bv, ba, sens, now)

    async def step_ai_emotion(
        self,
        user_id: str,
        character_id: str | None,
        user_text: str,
        user_emotion: EmotionData,
    ) -> EmotionData:
        """
        按文档 4.3：时间衰减 → 事件影响 + 共情 → 限幅，并持久化 AI 情绪状态（进程内）。
        """
        key = self._ai_state_key(user_id, character_id)
        state = self._ai_emotion_states.get(key)
        if state is None:
            state = self._default_ai_state()

        now = datetime.now(timezone.utc)
        t = (now - state.last_updated).total_seconds()
        T = max(float(settings.emotion.emotion_half_life), 1.0)
        decay_factor = math.exp(-t / T)

        v_decay = state.base_valence + (state.current_valence - state.base_valence) * decay_factor
        a_decay = state.base_arousal + (state.current_arousal - state.base_arousal) * decay_factor

        n_pos, n_neg = _count_event_words(user_text)
        delta_v = 0.2 * n_pos - 0.2 * n_neg
        delta_a = 0.15 * n_pos + 0.1 * n_neg

        empathy = settings.emotion.empathy_factor
        delta_v_empathy = (user_emotion.valence - v_decay) * empathy * user_emotion.confidence

        sens = state.sensitivity
        new_v = v_decay + (delta_v + delta_v_empathy) * sens
        new_a = a_decay + delta_a * sens

        new_v = max(-1.0, min(1.0, new_v))
        new_a = max(0.0, min(1.0, new_a))

        label = emotion_label_from_va(new_v, new_a)

        self._ai_emotion_states[key] = AIEmotionStateRecord(
            current_valence=new_v,
            current_arousal=new_a,
            base_valence=state.base_valence,
            base_arousal=state.base_arousal,
            sensitivity=state.sensitivity,
            last_updated=now,
        )

        return EmotionData(
            valence=round(new_v, 3),
            arousal=round(new_a, 3),
            label=label,
            confidence=1.0,
        )

    async def initialize(self) -> None:
        if self._initialized:
            return

        model_type = settings.emotion.model

        if model_type == "transformer" and settings.emotion.detection_enabled:
            try:
                self.analyzer = TransformerEmotionAnalyzer()
                await self.analyzer.initialize()
                logger.info("Using transformer-based emotion analyzer")
            except Exception as e:
                logger.warning("Failed to init transformer analyzer, falling back: %s", e)
                self.analyzer = KeywordEmotionAnalyzer()
                await self.analyzer.initialize()
        else:
            self.analyzer = KeywordEmotionAnalyzer()
            await self.analyzer.initialize()
            logger.info("Using keyword-based emotion analyzer")

        self._initialized = True

    async def analyze(self, text: str) -> EmotionData:
        if not settings.emotion.detection_enabled:
            return EmotionData(valence=0.0, arousal=0.3, label="中性")

        if not self.analyzer:
            await self.initialize()

        assert self.analyzer is not None
        return await self.analyzer.analyze(text)

    async def get_emotion_label(self, emotion: EmotionData) -> str:
        return emotion.label or "中性"

    async def get_empathy_response(self, emotion: EmotionData) -> str:
        label = emotion.label or await self.get_emotion_label(emotion)

        empathy_map: dict[str, str] = {
            "兴奋": "听起来你很兴奋！",
            "开心": "很高兴看到你心情不错！",
            "高兴": "很高兴看到你心情不错！",
            "快乐": "很高兴看到你心情不错！",
            "平静": "感觉你现在很平静。",
            "愤怒": "我理解你现在很生气，想说说发生了什么吗？",
            "生气": "我理解你现在很生气，想说说发生了什么吗？",
            "悲伤": "我能感受到你的难过，我在这里陪着你。",
            "难过": "我能感受到你的难过，我在这里陪着你。",
            "伤心": "我能感受到你的难过，我在这里陪着你。",
            "焦虑": "你似乎有些担心，有什么我可以帮你的吗？",
            "担心": "你似乎有些担心，有什么我可以帮你的吗？",
            "低落": "感觉你有些低落，想聊聊吗？",
            "激动": "你看起来情绪很激动，发生什么事了？",
            "积极": "听起来状态不错！",
            "消极": "感觉你有些低落，想聊聊吗？",
            "中性": "",
        }

        return empathy_map.get(label, "")

    async def close(self) -> None:
        if self.analyzer and hasattr(self.analyzer, "close"):
            await self.analyzer.close()
        self._initialized = False
        logger.info("Emotion engine closed")
