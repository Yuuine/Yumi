"""
Chat API Router - 支持流式响应
基于新数据库设计重构
"""

from __future__ import annotations

import json
import time
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import Any, Annotated

from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlmodel import select

from ..core import (
    LLMException,
    MemoryException,
    NoActiveModelException,
    get_active_model,
    get_logger,
    log_with_context,
    set_active_model,
    settings,
    require_current_user,
    validate_user_access,
)
import logging
from ..database_sqlmodel import get_session
from ..models import ConversationLog, ModelConfig, ConversationResponse
from ..services.async_storage import StorageTask, get_async_storage_service
from ..services.cache_service import get_cache_service
from ..services.conversation_service import conversation_service
from ..services.dialogue_log_service import DialogueInteraction, EndReason, dialogue_log_service
from ..services.emotion import EmotionData
from ..services.log_service import log_service

router = APIRouter()
logger = get_logger(__name__)


class ChatRequest(BaseModel):
    userId: str = Field(..., min_length=1, max_length=100, description="用户ID")
    conversationId: str | None = Field(None, description="会话ID")
    characterId: str | None = Field(None, description="当前使用的角色卡 id（与本地账号角色库一致）")
    message: str = Field(..., min_length=1, max_length=10000, description="消息内容")
    temperature: float | None = Field(0.85, ge=0.0, le=2.0, description="温度参数")
    stream: bool = False
    deepThinking: bool = Field(False, description="是否使用深度思考模式")


class ChatResponse(BaseModel):
    reply: str
    emotion: EmotionData
    memoryUsed: int
    newSummary: str | None = None
    conversationId: str | None = None


class ChatMessage(BaseModel):
    id: str
    role: str
    content: str
    timestamp: str
    emotion: EmotionData | None = None


class ChatHistory(BaseModel):
    messages: list[ChatMessage]


class DialogueLogListResponse(BaseModel):
    logs: list[dict]
    total: int


def _format_llm_response(llm_response: Any) -> str:
    """格式化LLM响应内容，处理推理过程和回答的组合"""
    if isinstance(llm_response, str):
        return llm_response

    reasoning = getattr(llm_response, "reasoning_content", None)
    content = getattr(llm_response, "content", None)

    if reasoning and content:
        return f"**推理过程:**\n{reasoning}\n\n**回答:**\n{content}"
    if reasoning:
        return f"**推理过程:**\n{reasoning}"
    return content or ""


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
        async with get_session() as session:
            result = await session.exec(
                select(ModelConfig)
                .where(ModelConfig.account_id == account_id)
                .where(ModelConfig.is_enabled == True)
                .order_by(ModelConfig.updated_at.desc())
                .limit(1)
            )
            config = result.first()

            if config:
                from ..routers.models import decrypt_api_key
                model_config = {
                    "model_id": config.id,
                    "provider_id": config.provider_id,
                    "base_url": config.base_url,
                    "api_key": decrypt_api_key(config.api_key) if config.api_key else "",
                    "model_name": config.model_name,
                    "display_name": config.name,
                }
                set_active_model(account_id, model_config)
                if settings.app.debug:
                    logger.info(
                        "Active model loaded from DB: %s (provider=%s, model=%s)",
                        model_config["display_name"],
                        model_config["provider_id"],
                        model_config["model_name"],
                    )
                return model_config
            return None
    except Exception as e:
        logger.error("Failed to get active model config: %s", e)
        return None


async def _build_context_and_emotion(
    request: ChatRequest,
    conversation_id: str,
    req: Request,
) -> tuple[list[dict], EmotionData, list[Any]]:
    """构建对话上下文并分析用户情绪"""
    memory_engine = req.app.state.memory_engine
    emotion_engine = req.app.state.emotion_engine
    prompt_builder = req.app.state.prompt_builder

    if settings.app.debug:
        user_emotion = EmotionData(valence=0.5, arousal=0.5, label="neutral")
        relevant_memories: list[Any] = []
    else:
        user_emotion = await emotion_engine.analyze(request.message)
        relevant_memories = await memory_engine.search(
            query=request.message,
            user_id=request.userId,
        )

    messages = await prompt_builder.build_context(
        user_id=request.userId,
        conversation_id=conversation_id,
        current_message=request.message,
        memories=relevant_memories,
        user_emotion=user_emotion,
        character_id=request.characterId,
    )

    return messages, user_emotion, relevant_memories


async def _call_llm_service(
    messages: list[dict],
    request: ChatRequest,
    active_model: dict,
    req: Request,
) -> tuple[Any, float]:
    """调用LLM服务并返回响应和延迟"""
    llm_service = req.app.state.llm_service
    llm_start_time = time.time()

    logger.info(
        "LLM Request: model=%s, provider=%s, deepThinking=%s, temperature=%.2f, messages_count=%d",
        active_model["model_name"],
        active_model["provider_id"],
        request.deepThinking,
        request.temperature or 0.85,
        len(messages),
    )

    llm_response = await llm_service.chat(
        messages=messages,
        temperature=request.temperature,
        provider_id=active_model["provider_id"],
        base_url=active_model["base_url"],
        api_key=active_model["api_key"],
        model_name=active_model["model_name"],
        use_thinking=request.deepThinking,
    )
    llm_latency_ms = (time.time() - llm_start_time) * 1000

    return llm_response, llm_latency_ms


def _log_llm_request_response(llm_response: Any) -> None:
    """记录LLM请求和响应的详细信息"""
    request_payload = getattr(llm_response, "request_payload", {})
    if request_payload:
        if "messages" not in request_payload:
            logger.warning("request_payload missing messages: %s", request_payload.keys())
        else:
            messages_count = len(request_payload["messages"])
            logger.info("request_payload contains %d messages", messages_count)
            if messages_count > 0:
                first_msg = request_payload["messages"][0]
                logger.info(
                    "First message role: %s, content length: %d",
                    first_msg.get("role"),
                    len(first_msg.get("content", "")),
                )


async def _analyze_assistant_emotion(reply: str, req: Request) -> EmotionData:
    """分析助手回复的情绪"""
    emotion_engine = req.app.state.emotion_engine
    if settings.app.debug:
        return EmotionData(valence=0.5, arousal=0.5, label="neutral")
    return await emotion_engine.analyze(reply)


def _update_dialogue_interaction_success(
    dialogue_interaction: DialogueInteraction,
    user_emotion: EmotionData,
    assistant_emotion: EmotionData,
    llm_response: Any,
    start_time: float,
) -> None:
    """更新对话交互记录（成功情况）"""
    dialogue_interaction.user_emotion = {
        "valence": user_emotion.valence,
        "arousal": user_emotion.arousal,
        "label": user_emotion.label,
    }

    request_payload = getattr(llm_response, "request_payload", {})
    raw_response = getattr(llm_response, "raw_response", {})

    dialogue_interaction.request_detail = json.dumps(request_payload or {}, ensure_ascii=False)
    dialogue_interaction.response_detail = json.dumps(raw_response or {}, ensure_ascii=False)
    dialogue_interaction.assistant_emotion = {
        "valence": assistant_emotion.valence,
        "arousal": assistant_emotion.arousal,
        "label": assistant_emotion.label,
    }

    end_datetime = datetime.now(timezone.utc).isoformat()
    dialogue_interaction.end_time = end_datetime
    dialogue_interaction.duration_ms = int((time.time() - start_time) * 1000)
    dialogue_interaction.is_normal_end = True
    dialogue_interaction.end_reason = EndReason.NORMAL.value


def _update_dialogue_interaction_error(
    dialogue_interaction: DialogueInteraction,
    start_time: float,
    end_reason: EndReason,
) -> None:
    """更新对话交互记录（错误情况）"""
    dialogue_interaction.is_normal_end = False
    dialogue_interaction.end_reason = end_reason.value
    dialogue_interaction.end_time = datetime.now(timezone.utc).isoformat()
    dialogue_interaction.duration_ms = int((time.time() - start_time) * 1000)


async def _generate_summary_if_needed(
    user_id: str,
    req: Request,
    active_model: dict | None,
) -> str | None:
    """达阈值时用当前对话模型生成 LLM 摘要并写入 `[摘要]` 向量；每轮对话只计一次 turn。"""
    if settings.app.debug or not active_model:
        return None

    memory_engine = req.app.state.memory_engine
    turn_count = await memory_engine.get_turn_count(user_id)
    if turn_count <= 0 or turn_count % settings.memory.summary_trigger_turns != 0:
        return None

    llm_service = req.app.state.llm_service
    return await memory_engine.summarize_with_llm(
        user_id,
        llm_service,
        provider_id=active_model["provider_id"],
        base_url=active_model["base_url"],
        api_key=active_model["api_key"],
        model_name=active_model["model_name"],
    )


@router.post("/chat", response_model=ChatResponse)
async def send_message(
    request: ChatRequest, 
    req: Request,
    current_user_id: Annotated[str, Depends(require_current_user)]
) -> ChatResponse:
    """发送聊天消息"""
    start_time = time.time()
    start_datetime = datetime.now(timezone.utc).isoformat()

    validate_user_access(request.userId, current_user_id)

    active_model = await _get_active_model_config(request.userId)
    if not active_model:
        raise NoActiveModelException()

    conversation_id = await conversation_service.get_or_create_conversation(
        user_id=request.userId,
        conversation_id=request.conversationId,
        character_id=request.characterId,
    )

    user_message_id = str(uuid.uuid4())
    assistant_message_id = str(uuid.uuid4())

    dialogue_interaction = DialogueInteraction(
        conversation_id=conversation_id,
        user_id=request.userId,
        character_id=request.characterId,
        start_time=start_datetime,
    )

    try:
        await log_service.log_user_action(
            action="SEND_MESSAGE",
            resource_type="conversation",
            resource_id=conversation_id,
            user_id=request.userId,
            extra={"message_length": len(request.message)},
        )

        messages, user_emotion, relevant_memories = await _build_context_and_emotion(
            request, conversation_id, req
        )

        llm_response, llm_latency_ms = await _call_llm_service(messages, request, active_model, req)

        reply = _format_llm_response(llm_response)

        if settings.app.debug:
            logger.info(
                "LLM Response: latency=%.2fms, reply_length=%d",
                llm_latency_ms,
                len(reply),
            )

        _log_llm_request_response(llm_response)

        assistant_emotion = await _analyze_assistant_emotion(reply, req)

        _update_dialogue_interaction_success(
            dialogue_interaction, user_emotion, assistant_emotion, llm_response, start_time
        )

        await dialogue_log_service.log_interaction(dialogue_interaction)
        await conversation_service.update_conversation_timestamp(conversation_id)

        async_storage = get_async_storage_service()

        user_task = StorageTask.create(
            message_id=user_message_id,
            conversation_id=conversation_id,
            user_id=request.userId,
            role="user",
            content=request.message,
            emotion={"valence": user_emotion.valence, "arousal": user_emotion.arousal},
        )
        await async_storage.enqueue(user_task)

        assistant_task = StorageTask.create(
            message_id=assistant_message_id,
            conversation_id=conversation_id,
            user_id=request.userId,
            role="assistant",
            content=reply,
            emotion={"valence": assistant_emotion.valence, "arousal": assistant_emotion.arousal},
        )
        await async_storage.enqueue(assistant_task)

        await req.app.state.memory_engine.record_conversation_turn(request.userId)
        new_summary = await _generate_summary_if_needed(
            request.userId, req, active_model
        )

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
            conversationId=conversation_id,
        )

    except LLMException:
        _update_dialogue_interaction_error(
            dialogue_interaction, start_time, EndReason.PROVIDER_ERROR
        )
        await dialogue_log_service.log_interaction(dialogue_interaction)

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
        _update_dialogue_interaction_error(
            dialogue_interaction, start_time, EndReason.INTERNAL_ERROR
        )
        await dialogue_log_service.log_interaction(dialogue_interaction)

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
        _update_dialogue_interaction_error(dialogue_interaction, start_time, EndReason.UNKNOWN)
        await dialogue_log_service.log_interaction(dialogue_interaction)

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
async def get_chat_history(
    userId: str,
    limit: int = 50,
    offset: int = 0,
    conversationId: str | None = None,
    current_user_id: Annotated[str, Depends(require_current_user)] = "",
) -> ChatHistory:
    """获取指定会话的聊天历史（按时间正序返回当前窗口内的消息）。"""
    
    validate_user_access(userId, current_user_id)
    
    if not conversationId:
        return ChatHistory(messages=[])

    async with get_session() as session:
        result = await session.exec(
            select(ConversationLog)
            .where(ConversationLog.user_id == userId)
            .where(ConversationLog.conversation_id == conversationId)
            .order_by(ConversationLog.timestamp.desc())
            .limit(limit)
            .offset(offset)
        )
        logs = result.all()

        messages = [
            ChatMessage(
                id=str(log.id),
                role=log.role,
                content=log.content,
                timestamp=log.timestamp.isoformat() if log.timestamp else "",
                emotion=(
                    EmotionData(valence=log.emotion_valence, arousal=log.emotion_arousal)
                    if log.emotion_valence is not None and log.emotion_arousal is not None
                    else None
                ),
            )
            for log in reversed(logs)
        ]

        return ChatHistory(messages=messages)


async def _build_stream_context(
    userId: str,
    message: str,
    conversation_id: str,
    characterId: str | None,
    req: Request,
) -> tuple[list[dict], EmotionData, list[Any]]:
    """为流式响应构建上下文"""
    memory_engine = req.app.state.memory_engine
    emotion_engine = req.app.state.emotion_engine
    prompt_builder = req.app.state.prompt_builder

    if settings.app.debug:
        user_emotion = EmotionData(valence=0.5, arousal=0.5, label="neutral")
        relevant_memories: list[Any] = []
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
        character_id=characterId,
    )

    return messages, user_emotion, relevant_memories


async def _stream_chat_generator(
    userId: str,
    message: str,
    conversationId: str | None,
    characterId: str | None,
    temperature: float,
    deepThinking: bool,
    active_model: dict,
    start_time: float,
    start_datetime: str,
    req: Request,
) -> AsyncGenerator[str, None]:
    """流式聊天响应生成器"""
    if not active_model:
        yield f"data: {json.dumps({'error': '没有可用的模型，请先在模型管理中添加并启用一个模型'})}\n\n"
        return

    conversation_id = await conversation_service.get_or_create_conversation(
        user_id=userId,
        conversation_id=conversationId,
        character_id=characterId,
    )

    user_message_id = str(uuid.uuid4())
    assistant_message_id = str(uuid.uuid4())

    dialogue_interaction = DialogueInteraction(
        conversation_id=conversation_id,
        user_id=userId,
        character_id=characterId,
        start_time=start_datetime,
    )

    try:
        if settings.app.debug:
            logger.info(
                "Stream LLM Request: model=%s, provider=%s, deepThinking=%s, temperature=%.2f",
                active_model["model_name"],
                active_model["provider_id"],
                deepThinking,
                temperature,
            )

        messages, user_emotion, _ = await _build_stream_context(
            userId, message, conversation_id, characterId, req
        )

        dialogue_interaction.user_emotion = {
            "valence": user_emotion.valence,
            "arousal": user_emotion.arousal,
            "label": user_emotion.label,
        }

        full_reply = ""
        stream_start_time = time.time()
        request_payload = None
        response_chunks = []

        llm_service = req.app.state.llm_service
        async for chunk in llm_service.stream_chat(
            messages=messages,
            temperature=temperature,
            provider_id=active_model["provider_id"],
            base_url=active_model["base_url"],
            api_key=active_model["api_key"],
            model_name=active_model["model_name"],
            use_thinking=deepThinking,
        ):
            if isinstance(chunk, str):
                full_reply += chunk
                yield f"data: {json.dumps({'content': chunk})}\n\n"
            elif hasattr(chunk, "request_payload"):
                request_payload = chunk.request_payload
                response_chunks = chunk.raw_response_chunks

        stream_latency_ms = (time.time() - stream_start_time) * 1000
        if settings.app.debug:
            logger.info(
                "Stream LLM Response: latency=%.2fms, reply_length=%d",
                stream_latency_ms,
                len(full_reply),
            )

        if request_payload:
            dialogue_interaction.request_detail = json.dumps(request_payload, ensure_ascii=False)

        if response_chunks:
            dialogue_interaction.response_detail = json.dumps(response_chunks, ensure_ascii=False)

        assistant_emotion = await _analyze_assistant_emotion(full_reply, req)

        dialogue_interaction.assistant_emotion = {
            "valence": assistant_emotion.valence,
            "arousal": assistant_emotion.arousal,
            "label": assistant_emotion.label,
        }

        dialogue_interaction.end_time = datetime.now(timezone.utc).isoformat()
        dialogue_interaction.duration_ms = int((time.time() - start_time) * 1000)
        dialogue_interaction.is_normal_end = True
        dialogue_interaction.end_reason = EndReason.NORMAL.value

        await dialogue_log_service.log_interaction(dialogue_interaction)
        await conversation_service.update_conversation_timestamp(conversation_id)

        async_storage = get_async_storage_service()

        user_task = StorageTask.create(
            message_id=user_message_id,
            conversation_id=conversation_id,
            user_id=userId,
            role="user",
            content=message,
            emotion={"valence": user_emotion.valence, "arousal": user_emotion.arousal},
        )
        await async_storage.enqueue(user_task)

        assistant_task = StorageTask.create(
            message_id=assistant_message_id,
            conversation_id=conversation_id,
            user_id=userId,
            role="assistant",
            content=full_reply,
            emotion={"valence": assistant_emotion.valence, "arousal": assistant_emotion.arousal},
        )
        await async_storage.enqueue(assistant_task)

        await req.app.state.memory_engine.record_conversation_turn(userId)
        new_summary = await _generate_summary_if_needed(userId, req, active_model)

        done_payload: dict[str, Any] = {
            "done": True,
            "conversationId": conversation_id,
            "emotion": {
                "valence": assistant_emotion.valence,
                "arousal": assistant_emotion.arousal,
            },
        }
        if new_summary:
            done_payload["newSummary"] = new_summary
        yield f"data: {json.dumps(done_payload)}\n\n"

    except Exception as e:
        logger.error("Stream error: %s", e)

        dialogue_interaction.is_normal_end = False
        dialogue_interaction.end_reason = EndReason.UNKNOWN.value
        dialogue_interaction.end_time = datetime.now(timezone.utc).isoformat()
        dialogue_interaction.duration_ms = int((time.time() - start_time) * 1000)
        await dialogue_log_service.log_interaction(dialogue_interaction)

        yield f"data: {json.dumps({'error': str(e)})}\n\n"


@router.get("/chat/stream")
async def stream_chat(
    userId: str,
    message: str,
    req: Request,
    conversationId: str | None = None,
    characterId: str | None = None,
    temperature: float = 0.85,
    deepThinking: bool = False,
) -> StreamingResponse:
    """流式聊天响应"""
    active_model = await _get_active_model_config(userId)
    if not active_model:
        raise NoActiveModelException()
    
    start_time = time.time()
    start_datetime = datetime.now(timezone.utc).isoformat()

    return StreamingResponse(
        _stream_chat_generator(
            userId,
            message,
            conversationId,
            characterId,
            temperature,
            deepThinking,
            active_model,
            start_time,
            start_datetime,
            req,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/dialogue-logs", response_model=DialogueLogListResponse)
async def get_dialogue_logs(
    userId: str,
    limit: int = 50,
    offset: int = 0,
    includeDetails: bool = False,
) -> DialogueLogListResponse:
    """获取用户的对话交互日志列表"""
    logs = await dialogue_log_service.get_interactions_by_user(
        user_id=userId,
        limit=limit,
        offset=offset,
        include_details=includeDetails,
    )
    return DialogueLogListResponse(logs=logs, total=len(logs))


@router.get("/dialogue-logs/{log_id}")
async def get_dialogue_log_detail(log_id: int) -> Any:
    """获取单条对话交互日志详情"""
    log = await dialogue_log_service.get_interaction_by_id(log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Dialogue log not found")
    return log


@router.get("/conversations")
async def get_conversations(
    userId: str,
    characterId: str | None = None,
    limit: int = 20,
    offset: int = 0,
    current_user_id: Annotated[str, Depends(require_current_user)] = "",
) -> dict[str, Any]:
    """获取用户的会话列表，可按角色卡筛选"""
    
    validate_user_access(userId, current_user_id)
    
    cache_service = get_cache_service()
    cache_key = f"convs:{userId}:{characterId}:{limit}:{offset}"
    
    cached = cache_service.conversation_list.get(cache_key)
    if cached is not None:
        log_with_context(logger, logging.DEBUG, f"ChatRouter Cache HIT: key={cache_key}", key=cache_key)
        return cached
    
    log_with_context(logger, logging.DEBUG, f"ChatRouter Cache MISS: key={cache_key}", key=cache_key)
    conversations = await conversation_service.get_user_conversations(
        user_id=userId,
        limit=limit,
        offset=offset,
        character_id=characterId,
    )
    result = {"conversations": conversations}
    cache_service.conversation_list.set(cache_key, result)
    return result


@router.get("/conversations/{conversation_id}/dialogue-logs")
async def get_conversation_dialogue_logs(
    conversation_id: str,
    includeDetails: bool = False,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    """获取特定会话的对话交互日志"""
    logs = await dialogue_log_service.get_interactions_by_conversation(
        conversation_id=conversation_id,
        limit=limit,
        offset=offset,
        include_details=includeDetails,
    )
    return {"logs": logs}


@router.delete("/dialogue-logs")
async def clear_dialogue_logs(userId: str | None = None) -> dict[str, Any]:
    """清除对话交互日志，不传userId则清除所有"""
    deleted_count = await dialogue_log_service.clear_all_logs(user_id=userId)
    return {"deleted_count": deleted_count, "user_id": userId}


@router.get("/dialogue-logs/stats")
async def get_dialogue_log_stats(userId: str | None = None) -> Any:
    """获取对话交互日志统计信息"""
    stats = await dialogue_log_service.get_log_stats(user_id=userId)
    return stats


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    request: dict[str, Any],
    current_user_id: Annotated[str, Depends(require_current_user)] = "",
) -> ConversationResponse:
    """创建新会话"""
    user_id = request.get("userId") or request.get("user_id")
    character_id = request.get("characterId") or request.get("character_id")
    conversation_id = request.get("id")
    title = request.get("title", "新对话")

    if not user_id:
        raise HTTPException(status_code=400, detail="userId is required")

    validate_user_access(user_id, current_user_id)

    created = await conversation_service.create_conversation(
        user_id=user_id,
        character_id=character_id,
        conversation_id=conversation_id,
        title=title,
    )
    cache_service = get_cache_service()
    cache_service.invalidate_conversation(user_id, created["id"])
    return created


@router.put("/conversations/{conversation_id}/title")
async def update_conversation_title(
    conversation_id: str,
    request: dict[str, Any],
    current_user_id: Annotated[str, Depends(require_current_user)] = "",
) -> dict[str, Any]:
    """更新会话标题"""
    title = request.get("title", "")
    
    # 获取会话信息以验证权限
    conversation = await conversation_service.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    validate_user_access(conversation["user_id"], current_user_id)
    
    updated = await conversation_service.update_conversation_title(
        conversation_id=conversation_id,
        title=title,
    )
    cache_service = get_cache_service()
    cache_service.invalidate_conversation(conversation["user_id"], conversation_id)
    return {"success": True, "conversation": updated}


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user_id: Annotated[str, Depends(require_current_user)] = "",
) -> dict[str, Any]:
    """删除会话"""
    # 获取会话信息以验证权限
    conversation = await conversation_service.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    validate_user_access(conversation["user_id"], current_user_id)
    
    await conversation_service.delete_conversation(conversation_id)
    cache_service = get_cache_service()
    cache_service.invalidate_conversation(conversation["user_id"], conversation_id)
    return {"success": True, "message": "Conversation deleted"}
