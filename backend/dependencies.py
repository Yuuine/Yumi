"""
依赖注入模块
提供 FastAPI 依赖注入的服务实例
"""
from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Request

from .services.emotion import EmotionEngine
from .services.llm import LLMService
from .services.memory import MemoryEngine
from .services.prompt_builder import PromptBuilder


@lru_cache
def get_memory_engine() -> MemoryEngine:
    return MemoryEngine()


@lru_cache
def get_emotion_engine() -> EmotionEngine:
    return EmotionEngine()


@lru_cache
def get_llm_service() -> LLMService:
    return LLMService()


@lru_cache
def get_prompt_builder(
    memory_engine: MemoryEngine = Depends(get_memory_engine),
    emotion_engine: EmotionEngine = Depends(get_emotion_engine),
) -> PromptBuilder:
    return PromptBuilder(memory_engine, emotion_engine)


MemoryDep = Annotated[MemoryEngine, Depends(get_memory_engine)]
EmotionDep = Annotated[EmotionEngine, Depends(get_emotion_engine)]
LLMDep = Annotated[LLMService, Depends(get_llm_service)]
PromptBuilderDep = Annotated[PromptBuilder, Depends(get_prompt_builder)]


def get_memory_from_app(request: Request) -> MemoryEngine:
    return request.app.state.memory_engine


def get_emotion_from_app(request: Request) -> EmotionEngine:
    return request.app.state.emotion_engine


def get_llm_from_app(request: Request) -> LLMService:
    return request.app.state.llm_service


def get_prompt_builder_from_app(request: Request) -> PromptBuilder:
    return request.app.state.prompt_builder


AppMemoryDep = Annotated[MemoryEngine, Depends(get_memory_from_app)]
AppEmotionDep = Annotated[EmotionEngine, Depends(get_emotion_from_app)]
AppLLMDep = Annotated[LLMService, Depends(get_llm_from_app)]
AppPromptBuilderDep = Annotated[PromptBuilder, Depends(get_prompt_builder_from_app)]
