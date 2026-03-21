"""
Pytest configuration and fixtures
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_settings():
    from backend.core.config import Settings

    settings = Settings()
    settings.database.path = ":memory:"
    settings.vector_db.persist_dir = "data/test_chroma"
    settings.llm.api_endpoint = "http://localhost:11434/v1"
    settings.llm.model_name = "test-model"
    settings.emotion.detection_enabled = True
    settings.emotion.model = "keyword"
    return settings


@pytest.fixture
def mock_llm_response():
    return "这是一个测试回复"


@pytest.fixture
def mock_emotion_data():
    return {"valence": 0.5, "arousal": 0.3}


@pytest_asyncio.fixture
async def mock_memory_engine():
    engine = MagicMock()
    engine.search = AsyncMock(return_value=[])
    engine.store = AsyncMock(return_value="test-memory-id")
    engine.get_recent = AsyncMock(return_value=[])
    engine.get_turn_count = AsyncMock(return_value=0)
    engine.close = AsyncMock()
    return engine


@pytest_asyncio.fixture
async def mock_emotion_engine():
    from backend.services.emotion import EmotionData

    engine = MagicMock()
    engine.analyze = AsyncMock(return_value=EmotionData(valence=0.5, arousal=0.3, label="中性"))
    engine.get_emotion_label = AsyncMock(return_value="中性")
    engine.get_empathy_response = AsyncMock(return_value="")
    return engine


@pytest_asyncio.fixture
async def mock_llm_service():
    service = MagicMock()
    service.chat = AsyncMock(return_value="这是一个测试回复")
    service.stream_chat = AsyncMock()
    service.close = AsyncMock()
    return service


@pytest_asyncio.fixture
async def mock_prompt_builder():
    builder = MagicMock()
    builder.build_context = AsyncMock(
        return_value=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello"},
        ]
    )
    return builder


@pytest.fixture
def test_user_id():
    return "test-user-123"


@pytest.fixture
def test_message():
    return "你好，这是一个测试消息"


@pytest.fixture(autouse=True)
def setup_test_env(tmp_path: Path, monkeypatch):
    test_data_dir = tmp_path / "data"
    test_data_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("YUMI_DB_PATH", str(test_data_dir / "test.db"))
    monkeypatch.setenv("YUMI_VECTOR_PERSIST_DIR", str(test_data_dir / "chroma"))
