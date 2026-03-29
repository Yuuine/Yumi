"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

Tests for chat router
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from typing import Annotated

import pytest
from fastapi import FastAPI


class TestChatRouter:
    @pytest.mark.asyncio
    async def test_send_message_success(
        self,
        mock_memory_engine,
        mock_emotion_engine,
        mock_llm_service,
        mock_prompt_builder,
        test_user_id,
        test_message,
    ):
        from httpx import ASGITransport, AsyncClient

        from core.auth import get_current_user_id
        from routers.chat import router

        app = FastAPI()
        app.state.memory_engine = mock_memory_engine
        app.state.emotion_engine = mock_emotion_engine
        app.state.llm_service = mock_llm_service
        app.state.prompt_builder = mock_prompt_builder

        async def override_get_current_user_id():
            return test_user_id

        app.dependency_overrides[get_current_user_id] = override_get_current_user_id

        app.include_router(router, prefix="/api")

        mock_model_config = {
            "model_id": "test-model-id",
            "provider_id": "test-provider",
            "base_url": "https://api.test.com",
            "api_key": "test-api-key",
            "model_name": "test-model",
            "display_name": "Test Model",
        }

        with patch(
            "backend.routers.chat._get_active_model_config",
            new_callable=AsyncMock,
            return_value=mock_model_config,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/chat",
                    json={
                        "userId": test_user_id,
                        "message": test_message,
                        "temperature": 0.85,
                    },
                )

                assert response.status_code == 200
                data = response.json()
                assert "reply" in data
                assert "emotion" in data
                assert data["memoryUsed"] == 0

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_send_message_with_memories(
        self,
        mock_memory_engine,
        mock_emotion_engine,
        mock_llm_service,
        mock_prompt_builder,
        test_user_id,
        test_message,
    ):
        from httpx import ASGITransport, AsyncClient

        from core.auth import get_current_user_id
        from routers.chat import router

        mock_memory_engine.search = AsyncMock(
            return_value=[
                {
                    "id": "mem-1",
                    "content": "用户之前提到喜欢音乐",
                    "similarity": 0.8,
                }
            ]
        )

        mock_model_config = {
            "model_id": "test-model-id",
            "provider_id": "test-provider",
            "base_url": "https://api.test.com",
            "api_key": "test-api-key",
            "model_name": "test-model",
            "display_name": "Test Model",
        }

        app = FastAPI()
        app.state.memory_engine = mock_memory_engine
        app.state.emotion_engine = mock_emotion_engine
        app.state.llm_service = mock_llm_service
        app.state.prompt_builder = mock_prompt_builder

        async def override_get_current_user_id():
            return test_user_id

        app.dependency_overrides[get_current_user_id] = override_get_current_user_id

        app.include_router(router, prefix="/api")

        with patch("backend.routers.chat.settings") as mock_settings:
            mock_settings.app.debug = False
            mock_settings.memory.summary_trigger_turns = 70

            with patch(
                "backend.routers.chat._get_active_model_config",
                new_callable=AsyncMock,
                return_value=mock_model_config,
            ):
                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    response = await client.post(
                        "/api/chat",
                        json={
                            "userId": test_user_id,
                            "message": test_message,
                        },
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert data["memoryUsed"] == 1

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_send_message_llm_error(
        self,
        mock_memory_engine,
        mock_emotion_engine,
        mock_llm_service,
        mock_prompt_builder,
        test_user_id,
        test_message,
    ):
        from httpx import ASGITransport, AsyncClient

        from core.auth import get_current_user_id
        from core.exceptions import LLMException
        from routers.chat import router

        mock_llm_service.chat = AsyncMock(side_effect=LLMException("LLM error"))

        app = FastAPI()
        app.state.memory_engine = mock_memory_engine
        app.state.emotion_engine = mock_emotion_engine
        app.state.llm_service = mock_llm_service
        app.state.prompt_builder = mock_prompt_builder

        async def override_get_current_user_id():
            return test_user_id

        app.dependency_overrides[get_current_user_id] = override_get_current_user_id

        from core.error_handlers import setup_exception_handlers
        setup_exception_handlers(app)

        app.include_router(router, prefix="/api")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/chat",
                json={
                    "userId": test_user_id,
                    "message": test_message,
                },
            )

            assert response.status_code == 400

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_chat_history(
        self,
        test_user_id,
    ):
        from httpx import ASGITransport, AsyncClient

        from core.auth import get_current_user_id
        from routers.chat import router
        from database_sqlmodel import get_session

        app = FastAPI()
        app.include_router(router, prefix="/api")

        async def override_get_current_user_id():
            return test_user_id

        app.dependency_overrides[get_current_user_id] = override_get_current_user_id

        mock_log_result = MagicMock()
        mock_log_result.all.return_value = []
        mock_session = AsyncMock()
        mock_session.exec.return_value = mock_log_result
        mock_session.commit = AsyncMock()

        async def mock_get_session():
            yield mock_session

        with patch("backend.database_sqlmodel.get_session", mock_get_session):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get(
                    "/api/chat/history",
                    params={"userId": test_user_id, "limit": 50, "conversationId": "conv-test-1"},
                )

                assert response.status_code == 200
                data = response.json()
                assert "messages" in data

        app.dependency_overrides.clear()


class TestChatRequest:
    def test_chat_request_validation(self):
        from routers.chat import ChatRequest

        request = ChatRequest(
            userId="test-user",
            message="Hello",
        )
        assert request.userId == "test-user"
        assert request.message == "Hello"
        assert request.temperature == 0.85

    def test_chat_request_with_custom_temperature(self):
        from routers.chat import ChatRequest

        request = ChatRequest(
            userId="test-user",
            message="Hello",
            temperature=0.5,
        )
        assert request.temperature == 0.5


class TestChatResponse:
    def test_chat_response_model(self):
        from routers.chat import ChatResponse
        from services.emotion import EmotionData

        response = ChatResponse(
            reply="Hello!",
            emotion=EmotionData(valence=0.5, arousal=0.3),
            memoryUsed=2,
        )
        assert response.reply == "Hello!"
        assert response.emotion.valence == 0.5
        assert response.memoryUsed == 2
        assert response.newSummary is None

    def test_chat_response_with_summary(self):
        from routers.chat import ChatResponse
        from services.emotion import EmotionData

        response = ChatResponse(
            reply="Hello!",
            emotion=EmotionData(valence=0.5, arousal=0.3),
            memoryUsed=2,
            newSummary="Summary of conversation",
        )
        assert response.newSummary == "Summary of conversation"
