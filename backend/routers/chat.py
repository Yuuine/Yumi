"""
Chat API Router - 支持流式响应
"""
from __future__ import annotations

import json
from datetime import datetime

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..core import LLMException, MemoryException, NoActiveModelException, get_logger, settings
from ..database import get_db
from ..services.emotion import EmotionData
from ..routers.models import decrypt_api_key

router = APIRouter()
logger = get_logger(__name__)


class ChatRequest(BaseModel):
    userId: str = Field(..., min_length=1, max_length=100, description="用户ID")
    message: str = Field(..., min_length=1, max_length=10000, description="消息内容")
    temperature: float | None = Field(0.85, ge=0.0, le=2.0, description="温度参数")
    stream: bool = False


class ChatResponse(BaseModel):
    reply: str
    emotion: EmotionData
    memoryUsed: int
    newSummary: str | None = None


class ChatMessage(BaseModel):
    id: str
    role: str
    content: str
    timestamp: str
    emotion: EmotionData | None = None


class ChatHistory(BaseModel):
    messages: list[ChatMessage]


async def _get_active_model_config() -> dict | None:
    """从数据库获取活动模型配置"""
    try:
        async with await get_db() as db:
            cursor = await db.execute(
                """SELECT provider_id, base_url, api_key, model_name
                   FROM model_configs
                   WHERE is_enabled = 1
                   LIMIT 1"""
            )
            row = await cursor.fetchone()

            if row:
                return {
                    "provider_id": row[0],
                    "base_url": row[1],
                    "api_key": decrypt_api_key(row[2]) if row[2] else "",
                    "model_name": row[3],
                }
            return None
    except Exception as e:
        logger.error("Failed to get active model config: %s", e)
        return None


@router.post("/chat", response_model=ChatResponse)
async def send_message(request: ChatRequest, req: Request):
    memory_engine = req.app.state.memory_engine
    emotion_engine = req.app.state.emotion_engine
    llm_service = req.app.state.llm_service
    prompt_builder = req.app.state.prompt_builder

    active_model = await _get_active_model_config()
    if not active_model:
        raise NoActiveModelException()

    try:
        user_emotion = await emotion_engine.analyze(request.message)

        relevant_memories = await memory_engine.search(
            query=request.message,
            user_id=request.userId,
        )

        messages = await prompt_builder.build_context(
            user_id=request.userId,
            current_message=request.message,
            memories=relevant_memories,
            user_emotion=user_emotion,
        )

        reply = await llm_service.chat(
            messages=messages,
            temperature=request.temperature,
            provider_id=active_model["provider_id"],
            base_url=active_model["base_url"],
            api_key=active_model["api_key"],
            model_name=active_model["model_name"],
        )

        assistant_emotion = await emotion_engine.analyze(reply)

        async with await get_db() as db:
            await db.execute(
                """INSERT INTO conversation_logs
                   (user_id, role, content, emotion_valence, emotion_arousal)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    request.userId,
                    "user",
                    request.message,
                    user_emotion.valence,
                    user_emotion.arousal,
                ),
            )
            await db.execute(
                """INSERT INTO conversation_logs
                   (user_id, role, content, emotion_valence, emotion_arousal)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    request.userId,
                    "assistant",
                    reply,
                    assistant_emotion.valence,
                    assistant_emotion.arousal,
                ),
            )
            await db.commit()

        await memory_engine.store(
            user_id=request.userId,
            content=f"用户: {request.message}\n助手: {reply}",
            metadata={
                "emotion_valence": user_emotion.valence,
                "emotion_arousal": user_emotion.arousal,
                "emotion_label": user_emotion.label,
                "timestamp": datetime.now().isoformat(),
            },
        )

        new_summary = None
        turn_count = await memory_engine.get_turn_count(request.userId)
        if (
            turn_count > 0
            and turn_count % settings.memory.summary_trigger_turns == 0
        ):
            new_summary = await memory_engine.summarize(request.userId)

        return ChatResponse(
            reply=reply,
            emotion=assistant_emotion,
            memoryUsed=len(relevant_memories),
            newSummary=new_summary,
        )

    except LLMException:
        raise
    except MemoryException:
        raise
    except Exception as e:
        logger.exception("Unexpected error in chat endpoint: %s", e)
        raise


@router.get("/chat/history", response_model=ChatHistory)
async def get_chat_history(userId: str, limit: int = 50, req: Request = None):
    async with await get_db() as db:
        cursor = await db.execute(
            """SELECT id, role, content, timestamp, emotion_valence, emotion_arousal
               FROM conversation_logs
               WHERE user_id = ?
               ORDER BY timestamp DESC
               LIMIT ?""",
            (userId, limit),
        )
        rows = await cursor.fetchall()

        messages = []
        for row in reversed(rows):
            emotion = None
            if row[4] is not None and row[5] is not None:
                emotion = EmotionData(valence=row[4], arousal=row[5])

            messages.append(
                ChatMessage(
                    id=str(row[0]),
                    role=row[1],
                    content=row[2],
                    timestamp=row[3],
                    emotion=emotion,
                )
            )

        return ChatHistory(messages=messages)


@router.get("/chat/stream")
async def stream_chat(
    userId: str,
    message: str,
    req: Request,
    temperature: float = 0.85,
):
    memory_engine = req.app.state.memory_engine
    emotion_engine = req.app.state.emotion_engine
    llm_service = req.app.state.llm_service
    prompt_builder = req.app.state.prompt_builder

    active_model = await _get_active_model_config()

    async def generate():
        if not active_model:
            yield f"data: {json.dumps({'error': '没有可用的模型，请先在模型管理中添加并启用一个模型'})}\n\n"
            return

        try:
            user_emotion = await emotion_engine.analyze(message)

            relevant_memories = await memory_engine.search(
                query=message,
                user_id=userId,
            )

            messages = await prompt_builder.build_context(
                user_id=userId,
                current_message=message,
                memories=relevant_memories,
                user_emotion=user_emotion,
            )

            full_reply = ""
            async for chunk in llm_service.stream_chat(
                messages=messages,
                temperature=temperature,
                provider_id=active_model["provider_id"],
                base_url=active_model["base_url"],
                api_key=active_model["api_key"],
                model_name=active_model["model_name"],
            ):
                full_reply += chunk
                yield f"data: {json.dumps({'content': chunk})}\n\n"

            assistant_emotion = await emotion_engine.analyze(full_reply)

            async with await get_db() as db:
                await db.execute(
                    """INSERT INTO conversation_logs
                       (user_id, role, content, emotion_valence, emotion_arousal)
                       VALUES (?, ?, ?, ?, ?)""",
                    (
                        userId,
                        "user",
                        message,
                        user_emotion.valence,
                        user_emotion.arousal,
                    ),
                )
                await db.execute(
                    """INSERT INTO conversation_logs
                       (user_id, role, content, emotion_valence, emotion_arousal)
                       VALUES (?, ?, ?, ?, ?)""",
                    (
                        userId,
                        "assistant",
                        full_reply,
                        assistant_emotion.valence,
                        assistant_emotion.arousal,
                    ),
                )
                await db.commit()

            await memory_engine.store(
                user_id=userId,
                content=f"用户: {message}\n助手: {full_reply}",
                metadata={
                    "emotion_valence": user_emotion.valence,
                    "emotion_arousal": user_emotion.arousal,
                    "emotion_label": user_emotion.label,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            yield f"data: {json.dumps({'done': True, 'emotion': {'valence': assistant_emotion.valence, 'arousal': assistant_emotion.arousal}})}\n\n"

        except Exception as e:
            logger.error("Stream error: %s", e)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
