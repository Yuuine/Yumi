"""
LLM Service - OpenAI compatible API client
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

from ..core import LLMException, settings

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self) -> None:
        self.api_endpoint = settings.llm.api_endpoint.rstrip("/")
        self.api_key = settings.llm.api_key
        self.model_name = settings.llm.model_name
        self.max_tokens = settings.llm.max_tokens
        self.default_temperature = settings.llm.default_temperature
        self.client = httpx.AsyncClient(timeout=settings.llm.timeout)

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        url = f"{self.api_endpoint}/chat/completions"

        headers: dict[str, str] = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload: dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature or self.default_temperature,
            "max_tokens": max_tokens or self.max_tokens,
        }

        try:
            response = await self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()

            data = response.json()
            return data["choices"][0]["message"]["content"]

        except httpx.HTTPStatusError as e:
            logger.error("LLM API HTTP error: %s", e)
            raise LLMException(
                message="LLM 服务调用失败",
                code="LLM_HTTP_ERROR",
                details={"status_code": e.response.status_code},
            )
        except httpx.TimeoutException:
            logger.error("LLM API timeout")
            raise LLMException(
                message="LLM 服务响应超时",
                code="LLM_TIMEOUT",
            )
        except Exception as e:
            logger.error("LLM service error: %s", e)
            raise LLMException(
                message="LLM 服务内部错误",
                code="LLM_INTERNAL_ERROR",
                details={"error": str(e)},
            )

    async def stream_chat(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
    ):
        import json

        url = f"{self.api_endpoint}/chat/completions"

        headers: dict[str, str] = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload: dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature or self.default_temperature,
            "stream": True,
        }

        try:
            async with self.client.stream(
                "POST", url, json=payload, headers=headers
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            content = chunk["choices"][0]["delta"].get("content")
                            if content:
                                yield content
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue
        except Exception as e:
            logger.error("LLM stream error: %s", e)
            raise LLMException(
                message="LLM 流式响应失败",
                code="LLM_STREAM_ERROR",
                details={"error": str(e)},
            )

    async def count_tokens(self, text: str) -> int:
        return len(text) // 4

    async def close(self) -> None:
        await self.client.aclose()
