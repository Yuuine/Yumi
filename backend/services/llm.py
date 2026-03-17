"""
LLM Service - 使用配置驱动适配器支持多种模型提供商
"""
from __future__ import annotations

import json
from typing import AsyncIterator

from ..core import LLMException, get_logger, settings
from .model_adapters import (
    ChatResponse,
    ModelConfig,
    OpenAICompatibleAdapter,
    StreamChunk,
    create_adapter,
)

logger = get_logger(__name__)


class LLMService:
    def __init__(self) -> None:
        self._adapter: OpenAICompatibleAdapter | None = None
        self._config: ModelConfig | None = None

    def _create_config(
        self,
        provider_id: str = "openai",
        base_url: str | None = None,
        api_key: str | None = None,
        model_name: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> ModelConfig:
        return ModelConfig(
            provider_id=provider_id,
            base_url=(base_url or settings.llm.api_endpoint).rstrip("/"),
            api_key=api_key or settings.llm.api_key,
            model_name=model_name or settings.llm.model_name,
            max_tokens=max_tokens or settings.llm.max_tokens,
            temperature=temperature or settings.llm.default_temperature,
            timeout=settings.llm.timeout,
        )

    def get_adapter(
        self,
        provider_id: str = "openai",
        base_url: str | None = None,
        api_key: str | None = None,
        model_name: str | None = None,
    ) -> OpenAICompatibleAdapter:
        config = self._create_config(
            provider_id=provider_id,
            base_url=base_url,
            api_key=api_key,
            model_name=model_name,
        )
        return create_adapter(config)

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        provider_id: str = "openai",
        base_url: str | None = None,
        api_key: str | None = None,
        model_name: str | None = None,
    ) -> str:
        adapter = self.get_adapter(
            provider_id=provider_id,
            base_url=base_url,
            api_key=api_key,
            model_name=model_name,
        )

        try:
            response = await adapter.chat(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            if response.reasoning_content and response.content:
                return f"**推理过程:**\n{response.reasoning_content}\n\n**回答:**\n{response.content}"
            elif response.reasoning_content:
                return f"**推理过程:**\n{response.reasoning_content}"
            return response.content
        finally:
            await adapter.close()

    async def stream_chat(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        provider_id: str = "openai",
        base_url: str | None = None,
        api_key: str | None = None,
        model_name: str | None = None,
    ) -> AsyncIterator[str]:
        adapter = self.get_adapter(
            provider_id=provider_id,
            base_url=base_url,
            api_key=api_key,
            model_name=model_name,
        )

        try:
            in_reasoning = False
            async for chunk in adapter.stream_chat(
                messages=messages,
                temperature=temperature,
            ):
                if chunk.is_done:
                    break

                if chunk.reasoning_content:
                    if not in_reasoning:
                        yield "**推理过程:**\n"
                        in_reasoning = True
                    yield chunk.reasoning_content

                if chunk.content:
                    if in_reasoning:
                        yield "\n\n**回答:**\n"
                        in_reasoning = False
                    yield chunk.content
        finally:
            await adapter.close()

    async def test_connection(
        self,
        provider_id: str,
        base_url: str,
        api_key: str,
        model_name: str,
        test_message: str = "你好，请简单介绍一下你自己。",
    ) -> tuple[bool, str, str | None, float | None]:
        adapter = self.get_adapter(
            provider_id=provider_id,
            base_url=base_url,
            api_key=api_key,
            model_name=model_name,
        )

        logger.info(
            "Test connection starting: provider=%s, base_url=%s, model=%s",
            provider_id, base_url, model_name
        )

        try:
            response = await adapter.chat(
                messages=[{"role": "user", "content": test_message}],
                max_tokens=512,
            )

            latency = 0.0
            if "latency" in response.raw_response:
                latency = response.raw_response["latency"]

            logger.info(
                "Test connection response: content_len=%d, reasoning_len=%d, raw_response_keys=%s",
                len(response.content) if response.content else 0,
                len(response.reasoning_content) if response.reasoning_content else 0,
                list(response.raw_response.keys())
            )

            if not response.content and not response.reasoning_content:
                logger.warning(
                    "Empty response from model. Raw response: %s",
                    json.dumps(response.raw_response, ensure_ascii=False, default=str)
                )

            if response.reasoning_content and response.content:
                content = f"**推理过程:**\n{response.reasoning_content}\n\n**回答:**\n{response.content}"
            elif response.reasoning_content:
                content = f"**推理过程:**\n{response.reasoning_content}"
            elif response.content:
                content = response.content
            else:
                content = "模型返回成功，但无内容输出。请检查模型名称和 API 配置。"

            return True, "连接成功", content, latency
        except LLMException as e:
            logger.error("Test connection LLM error: %s", e.message)
            return False, e.message, None, None
        except Exception as e:
            logger.error("Test connection error: %s", e, exc_info=True)
            return False, f"测试失败: {str(e)}", None, None
        finally:
            await adapter.close()

    async def count_tokens(self, text: str) -> int:
        return len(text) // 4

    async def close(self) -> None:
        if self._adapter:
            await self._adapter.close()
            self._adapter = None
