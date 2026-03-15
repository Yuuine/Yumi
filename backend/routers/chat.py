"""
Chat API Router - 支持流式响应
"""
from __future__ import annotations

import json
import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..core import LLMException, MemoryException, settings
from ..database import get_db
from ..services.emotion import EmotionData

router = APIRouter()
logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    userId: str
    message: str
    temperature: float | None = 0.85
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


@router.post("/chat", response_model=ChatResponse)
async def send_message(request: ChatRequest, req: Request):
    memory_engine = req.app.state.memory_engine
    emotion_engine = req.app.state.emotion_engine
    llm_service = req.app.state.llm_service
    prompt_builder = req.app.state.prompt_builder

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
                "emotion": user_emotion.model_dump(),
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
        raise HTTPException(status_code=500, detail="服务器内部错误") from e


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

    async def generate():
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
                    "emotion": user_emotion.model_dump(),
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
