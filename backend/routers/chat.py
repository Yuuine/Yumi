"""
Chat API Router - 支持流式响应
"""
from __future__ import annotations

import json
import time
import uuid

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..core import (
    LLMException,
    MemoryException,
    NoActiveModelException,
    get_active_model,
    get_logger,
    set_active_model,
    settings,
)
from ..database import get_db
from ..routers.models import decrypt_api_key
from ..services.async_storage import StorageTask, get_async_storage_service
from ..services.emotion import EmotionData
from ..services.log_service import log_service

router = APIRouter()
logger = get_logger(__name__)


class ChatRequest(BaseModel):
    userId: str = Field(..., min_length=1, max_length=100, description="用户ID")
    conversationId: str | None = Field(None, description="会话ID")
    message: str = Field(..., min_length=1, max_length=10000, description="消息内容")
    temperature: float | None = Field(0.85, ge=0.0, le=2.0, description="温度参数")
    stream: bool = False
    deepThinking: bool = Field(False, description="是否使用深度思考模式")


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


async def _get_active_model_config(account_id: str) -> dict | None:
    """获取活动模型配置（优先从全局状态获取，若为空则从数据库加载）"""
    active_model = get_active_model(account_id)
    if active_model:
        if settings.app.debug:
            logger.info(
                "Active model from cache: %s (provider=%s, model=%s)",
                active_model["display_name"],
                active_model["provider_id"],
                active_model["model_name"],
            )
        return active_model

    try:
        async with get_db() as db:
            cursor = await db.execute(
                """SELECT id, provider_id, base_url, api_key, model_name, name
                   FROM model_configs
                   WHERE account_id = ? AND is_enabled = 1
                   ORDER BY updated_at DESC
                   LIMIT 1"""
                ,
                (account_id,),
            )
            row = await cursor.fetchone()

            if row:
                config = {
                    "model_id": row[0],
                    "provider_id": row[1],
                    "base_url": row[2],
                    "api_key": decrypt_api_key(row[3]) if row[3] else "",
                    "model_name": row[4],
                    "display_name": row[5],
                }
                set_active_model(account_id, config)
                if settings.app.debug:
                    logger.info(
                        "Active model loaded from DB: %s (provider=%s, model=%s)",
                        config["display_name"],
                        config["provider_id"],
                        config["model_name"],
                    )
                return config
            return None
    except Exception as e:
        logger.error("Failed to get active model config: %s", e)
        return None


@router.post("/chat", response_model=ChatResponse)
async def send_message(request: ChatRequest, req: Request):
    start_time = time.time()
    conversation_id = str(uuid.uuid4())
    user_message_id = str(uuid.uuid4())
    assistant_message_id = str(uuid.uuid4())

    memory_engine = req.app.state.memory_engine
    emotion_engine = req.app.state.emotion_engine
    llm_service = req.app.state.llm_service
    prompt_builder = req.app.state.prompt_builder

    active_model = await _get_active_model_config(request.userId)
    if not active_model:
        raise NoActiveModelException()

    try:
        await log_service.log_user_action(
            action="SEND_MESSAGE",
            resource_type="conversation",
            resource_id=conversation_id,
            user_id=request.userId,
            extra={"message_length": len(request.message)},
        )

        if settings.app.debug:
            messages = [{"role": "user", "content": request.message}]
            user_emotion = EmotionData(valence=0.5, arousal=0.5, label="neutral")
            relevant_memories = []
        else:
            # TODO: 后续需要优化情感分析的准确性和性能
            user_emotion = await emotion_engine.analyze(request.message)

            # TODO: 后续需要支持记忆搜索结果的排序和过滤优化
            relevant_memories = await memory_engine.search(
                query=request.message,
                user_id=request.userId,
            )

            # TODO: 后续需要支持自定义提示词模板和上下文长度配置
            messages = await prompt_builder.build_context(
                user_id=request.userId,
                conversation_id=request.conversationId,
                current_message=request.message,
                memories=relevant_memories,
                user_emotion=user_emotion,
            )

        llm_start_time = time.time()

        logger.info(
            "LLM Request: model=%s, provider=%s, deepThinking=%s, temperature=%.2f, messages_count=%d",
            active_model["model_name"],
            active_model["provider_id"],
            request.deepThinking,
            request.temperature,
            len(messages),
        )

        reply = await llm_service.chat(
            messages=messages,
            temperature=request.temperature,
            provider_id=active_model["provider_id"],
            base_url=active_model["base_url"],
            api_key=active_model["api_key"],
            model_name=active_model["model_name"],
            use_thinking=request.deepThinking,
        )
        llm_latency_ms = (time.time() - llm_start_time) * 1000

        if settings.app.debug:
            logger.info(
                "LLM Response: latency=%.2fms, reply_length=%d",
                llm_latency_ms,
                len(reply),
            )

        if settings.app.debug:
            assistant_emotion = EmotionData(valence=0.5, arousal=0.5, label="neutral")
            user_emotion = EmotionData(valence=0.5, arousal=0.5, label="neutral")
        else:
            assistant_emotion = await emotion_engine.analyze(reply)

        await log_service.log_ai_interaction(
            conversation_id=conversation_id,
            message_id=user_message_id,
            role="user",
            content=request.message,
            emotion={"valence": user_emotion.valence, "arousal": user_emotion.arousal, "label": user_emotion.label},
            user_id=request.userId,
        )

        await log_service.log_ai_interaction(
            conversation_id=conversation_id,
            message_id=assistant_message_id,
            role="assistant",
            content=reply,
            emotion={"valence": assistant_emotion.valence, "arousal": assistant_emotion.arousal, "label": assistant_emotion.label},
            model_info={
                "provider": active_model["provider_id"],
                "model": active_model["model_name"],
            },
            latency_ms=llm_latency_ms,
            user_id=request.userId,
        )

        # 使用异步存储服务存储消息
        async_storage = get_async_storage_service()

        # 用户消息存储任务
        user_task = StorageTask.create(
            message_id=user_message_id,
            conversation_id=conversation_id,
            user_id=request.userId,
            role="user",
            content=request.message,
            emotion={"valence": user_emotion.valence, "arousal": user_emotion.arousal} if user_emotion else None,
        )
        await async_storage.enqueue(user_task)

        # 助手消息存储任务
        assistant_task = StorageTask.create(
            message_id=assistant_message_id,
            conversation_id=conversation_id,
            user_id=request.userId,
            role="assistant",
            content=reply,
            emotion={"valence": assistant_emotion.valence, "arousal": assistant_emotion.arousal} if assistant_emotion else None,
        )
        await async_storage.enqueue(assistant_task)

        new_summary = None
        if not settings.app.debug:
            turn_count = await memory_engine.get_turn_count(request.userId)
            if (
                turn_count > 0
                and turn_count % settings.memory.summary_trigger_turns == 0
            ):
                new_summary = await memory_engine.summarize(request.userId)

        total_latency_ms = (time.time() - start_time) * 1000
        await log_service.log_user_action(
            action="RECEIVE_RESPONSE",
            resource_type="conversation",
            resource_id=conversation_id,
            result="SUCCESS",
            user_id=request.userId,
            duration_ms=total_latency_ms,
            extra={
                "reply_length": len(reply),
                "llm_latency_ms": llm_latency_ms,
            },
        )

        return ChatResponse(
            reply=reply,
            emotion=assistant_emotion,
            memoryUsed=len(relevant_memories),
            newSummary=new_summary,
        )

    except LLMException:
        await log_service.log_user_action(
            action="RECEIVE_RESPONSE",
            resource_type="conversation",
            resource_id=conversation_id,
            result="FAIL",
            user_id=request.userId,
            extra={"error": "LLM error"},
        )
        raise
    except MemoryException:
        await log_service.log_user_action(
            action="RECEIVE_RESPONSE",
            resource_type="conversation",
            resource_id=conversation_id,
            result="FAIL",
            user_id=request.userId,
            extra={"error": "Memory error"},
        )
        raise
    except Exception as e:
        logger.exception("Unexpected error in chat endpoint: %s", e)
        await log_service.log_user_action(
            action="RECEIVE_RESPONSE",
            resource_type="conversation",
            resource_id=conversation_id,
            result="FAIL",
            user_id=request.userId,
            extra={"error": str(e)},
        )
        raise


@router.get("/chat/history", response_model=ChatHistory)
async def get_chat_history(userId: str, limit: int = 50, offset: int = 0, request: Request = None):  # type: ignore[assignment]
    async with get_db() as db:
        cursor = await db.execute(
            """SELECT id, role, content, timestamp, emotion_valence, emotion_arousal
               FROM conversation_logs
               WHERE user_id = ?
               ORDER BY timestamp DESC
               LIMIT ? OFFSET ?""",
            (userId, limit, offset),
        )
        rows = await cursor.fetchall()

        messages = []
        for row in list(reversed(list(rows))):
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
    conversationId: str | None = None,
    temperature: float = 0.85,
    deepThinking: bool = False,
):
    memory_engine = req.app.state.memory_engine
    emotion_engine = req.app.state.emotion_engine
    llm_service = req.app.state.llm_service
    prompt_builder = req.app.state.prompt_builder
    active_model = await _get_active_model_config(userId)

    conversation_id = conversationId or str(uuid.uuid4())

    user_message_id = str(uuid.uuid4())
    assistant_message_id = str(uuid.uuid4())

    async def generate():
        if not active_model:
            yield f"data: {json.dumps({'error': '没有可用的模型，请先在模型管理中添加并启用一个模型'})}\n\n"
            return

        try:
            if settings.app.debug:
                logger.info(
                    "Stream LLM Request: model=%s, provider=%s, deepThinking=%s, temperature=%.2f",
                    active_model["model_name"],
                    active_model["provider_id"],
                    deepThinking,
                    temperature,
                )

            if settings.app.debug:
                messages = [{"role": "user", "content": message}]
                user_emotion = EmotionData(valence=0.5, arousal=0.5, label="neutral")
            else:
                user_emotion = await emotion_engine.analyze(message)

                relevant_memories = await memory_engine.search(
                    query=message,
                    user_id=userId,
                )

                messages = await prompt_builder.build_context(
                    user_id=userId,
                    conversation_id=conversation_id,
                    current_message=message,
                    memories=relevant_memories,
                    user_emotion=user_emotion,
                )

            full_reply = ""
            stream_start_time = time.time()
            async for chunk in llm_service.stream_chat(
                messages=messages,
                temperature=temperature,
                provider_id=active_model["provider_id"],
                base_url=active_model["base_url"],
                api_key=active_model["api_key"],
                model_name=active_model["model_name"],
                use_thinking=deepThinking,
            ):
                full_reply += chunk
                yield f"data: {json.dumps({'content': chunk})}\n\n"

            if settings.app.debug:
                stream_latency_ms = (time.time() - stream_start_time) * 1000
                logger.info(
                    "Stream LLM Response: latency=%.2fms, reply_length=%d",
                    stream_latency_ms,
                    len(full_reply),
                )

            if settings.app.debug:
                assistant_emotion = EmotionData(valence=0.5, arousal=0.5, label="neutral")
                user_emotion = EmotionData(valence=0.5, arousal=0.5, label="neutral")
            else:
                assistant_emotion = await emotion_engine.analyze(full_reply)

            # 使用异步存储服务存储消息
            async_storage = get_async_storage_service()

            # 用户消息存储任务
            user_task = StorageTask.create(
                message_id=user_message_id,
                conversation_id=conversation_id,
                user_id=userId,
                role="user",
                content=message,
                emotion={"valence": user_emotion.valence, "arousal": user_emotion.arousal} if user_emotion else None,
            )
            await async_storage.enqueue(user_task)

            # 助手消息存储任务
            assistant_task = StorageTask.create(
                message_id=assistant_message_id,
                conversation_id=conversation_id,
                user_id=userId,
                role="assistant",
                content=full_reply,
                emotion={"valence": assistant_emotion.valence, "arousal": assistant_emotion.arousal} if assistant_emotion else None,
            )
            await async_storage.enqueue(assistant_task)

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
