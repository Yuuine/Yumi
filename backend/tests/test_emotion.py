"""
Tests for Emotion Engine
"""

from __future__ import annotations

from unittest.mock import patch

import pytest


class TestKeywordEmotionAnalyzer:
    @pytest.mark.asyncio
    async def test_analyze_positive_text(self):
        from backend.services.emotion import KeywordEmotionAnalyzer

        analyzer = KeywordEmotionAnalyzer()
        await analyzer.initialize()

        result = await analyzer.analyze("今天我很开心，感觉非常幸福！")

        assert result.valence > 0
        assert result.label in ["开心", "幸福", "兴奋"]

    @pytest.mark.asyncio
    async def test_analyze_negative_text(self):
        from backend.services.emotion import KeywordEmotionAnalyzer

        analyzer = KeywordEmotionAnalyzer()
        await analyzer.initialize()

        result = await analyzer.analyze("我很伤心，感觉很难过")

        assert result.valence < 0
        assert result.label in ["伤心", "难过", "悲伤"]

    @pytest.mark.asyncio
    async def test_analyze_neutral_text(self):
        from backend.services.emotion import KeywordEmotionAnalyzer

        analyzer = KeywordEmotionAnalyzer()
        await analyzer.initialize()

        result = await analyzer.analyze("今天天气不错")

        assert -0.2 <= result.valence <= 0.2

    @pytest.mark.asyncio
    async def test_analyze_high_arousal(self):
        from backend.services.emotion import KeywordEmotionAnalyzer

        analyzer = KeywordEmotionAnalyzer()
        await analyzer.initialize()

        result = await analyzer.analyze("我非常激动！太兴奋了！")

        assert result.arousal >= 0.5

    @pytest.mark.asyncio
    async def test_analyze_low_arousal(self):
        from backend.services.emotion import KeywordEmotionAnalyzer

        analyzer = KeywordEmotionAnalyzer()
        await analyzer.initialize()

        result = await analyzer.analyze("我很平静，感觉很放松")

        assert result.arousal < 0.5

    def test_get_emotion_label(self):
        from backend.services.emotion import KeywordEmotionAnalyzer

        analyzer = KeywordEmotionAnalyzer()

        assert analyzer._get_emotion_label(0.8, 0.7) == "兴奋"
        assert analyzer._get_emotion_label(0.6, 0.4) == "开心"
        assert analyzer._get_emotion_label(-0.7, 0.8) == "愤怒"
        assert analyzer._get_emotion_label(-0.6, 0.4) == "悲伤"
        assert analyzer._get_emotion_label(-0.3, 0.6) == "焦虑"
        assert analyzer._get_emotion_label(0.0, 0.3) == "中性"


class TestEmotionEngine:
    @pytest.mark.asyncio
    async def test_initialize_keyword_analyzer(self):
        from backend.services.emotion import EmotionEngine

        with patch("backend.services.emotion.settings") as mock_settings:
            mock_settings.emotion.model = "keyword"
            mock_settings.emotion.detection_enabled = True

            engine = EmotionEngine()
            await engine.initialize()

            assert engine._initialized is True

    @pytest.mark.asyncio
    async def test_analyze_disabled(self):
        from backend.services.emotion import EmotionEngine

        with patch("backend.services.emotion.settings") as mock_settings:
            mock_settings.emotion.detection_enabled = False

            engine = EmotionEngine()
            await engine.initialize()

            result = await engine.analyze("任何文本")

            assert result.valence == 0.0
            assert result.arousal == 0.3
            assert result.label == "中性"

    @pytest.mark.asyncio
    async def test_get_empathy_response(self):
        from backend.services.emotion import EmotionData, EmotionEngine

        with patch("backend.services.emotion.settings") as mock_settings:
            mock_settings.emotion.model = "keyword"
            mock_settings.emotion.detection_enabled = True

            engine = EmotionEngine()
            await engine.initialize()

        emotion = EmotionData(valence=0.8, arousal=0.6, label="开心")
        response = await engine.get_empathy_response(emotion)

        assert "高兴" in response or "心情不错" in response

        emotion = EmotionData(valence=-0.7, arousal=0.5, label="悲伤")
        response = await engine.get_empathy_response(emotion)

        assert "难过" in response or "陪着你" in response


class TestEmotionData:
    def test_emotion_data_model(self):
        from backend.services.emotion import EmotionData

        emotion = EmotionData(
            valence=0.5,
            arousal=0.3,
            label="中性",
            confidence=0.8,
        )

        assert emotion.valence == 0.5
        assert emotion.arousal == 0.3
        assert emotion.label == "中性"
        assert emotion.confidence == 0.8

    def test_emotion_data_defaults(self):
        from backend.services.emotion import EmotionData

        emotion = EmotionData(valence=0.0, arousal=0.0)

        assert emotion.label is None
        assert emotion.confidence == 1.0
