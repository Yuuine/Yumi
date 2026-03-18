"""
Model Adapters - 配置驱动的模型适配器

基于 OpenAI API 格式，通过差异配置实现多提供商适配。
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, AsyncIterator

import httpx

from ..core import LLMException, get_logger

logger = get_logger(__name__)


@dataclass
class RequestDiff:
    """请求差异配置"""
    remove_fields: list[str] = field(default_factory=list)
    add_fields: dict[str, Any] = field(default_factory=dict)
    field_mapping: dict[str, str] = field(default_factory=dict)
    default_values: dict[str, Any] = field(default_factory=dict)
    rename_fields: dict[str, str] = field(default_factory=dict)


@dataclass
class ResponseDiff:
    """响应差异配置"""
    extra_content_fields: list[str] = field(default_factory=list)
    reasoning_field: str | None = None
    field_mapping: dict[str, str] = field(default_factory=dict)


@dataclass
class ProviderDiffConfig:
    """提供商差异配置"""
    request_diff: RequestDiff = field(default_factory=RequestDiff)
    response_diff: ResponseDiff = field(default_factory=ResponseDiff)


@dataclass
class ModelConfig:
    """模型配置"""
    provider_id: str
    base_url: str
    api_key: str
    model_name: str
    max_tokens: int = 4096
    temperature: float = 0.85
    timeout: float = 60.0


@dataclass
class ChatResponse:
    """聊天响应"""
    content: str
    reasoning_content: str | None = None
    raw_response: dict[str, Any] = field(default_factory=dict)


@dataclass
class StreamChunk:
    """流式响应块"""
    content: str | None = None
    reasoning_content: str | None = None
    is_done: bool = False


PROVIDER_CONFIGS: dict[str, ProviderDiffConfig] = {
    "deepseek": ProviderDiffConfig(
        request_diff=RequestDiff(),
        response_diff=ResponseDiff(),
    ),
    "deepseek-reasoner": ProviderDiffConfig(
        request_diff=RequestDiff(
            remove_fields=["temperature", "top_p", "presence_penalty", "frequency_penalty", "logprobs"],
        ),
        response_diff=ResponseDiff(
            reasoning_field="reasoning_content",
        ),
    ),
    "kimi": ProviderDiffConfig(
        request_diff=RequestDiff(),
        response_diff=ResponseDiff(),
    ),
    "kimi-k2.5": ProviderDiffConfig(
        request_diff=RequestDiff(
            remove_fields=["temperature", "top_p", "n", "presence_penalty", "frequency_penalty"],
            rename_fields={"max_tokens": "max_completion_tokens"},
        ),
        response_diff=ResponseDiff(),
    ),
    "kimi-k2-turbo-preview": ProviderDiffConfig(
        request_diff=RequestDiff(),
        response_diff=ResponseDiff(),
    ),
}


def get_diff_config(model_name: str, provider_id: str) -> ProviderDiffConfig:
    """获取模型的差异配置"""
    model_lower = model_name.lower()
    if model_lower in PROVIDER_CONFIGS:
        return PROVIDER_CONFIGS[model_lower]
    provider_lower = provider_id.lower()
    if provider_lower in PROVIDER_CONFIGS:
        return PROVIDER_CONFIGS[provider_lower]
    return ProviderDiffConfig()


class OpenAICompatibleAdapter:
    """OpenAI 兼容适配器 - 基于差异配置动态调整"""

    def __init__(self, config: ModelConfig, diff_config: ProviderDiffConfig | None = None):
        self.config = config
        self.diff_config = diff_config or get_diff_config(config.model_name, config.provider_id)
        self.client = httpx.AsyncClient(timeout=config.timeout)

    def get_endpoint(self) -> str:
        base = self.config.base_url.rstrip("/")
        if base.endswith("/v1"):
            return f"{base}/chat/completions"
        if base.endswith("/chat/completions"):
            return base
        return f"{base}/chat/completions"

    def get_headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers

    def build_request_payload(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        stream: bool = False,
        **kwargs,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.config.model_name,
            "messages": messages,
        }

        if temperature is not None:
            payload["temperature"] = temperature
        elif self.config.temperature:
            payload["temperature"] = self.config.temperature

        if max_tokens:
            payload["max_tokens"] = max_tokens
        elif self.config.max_tokens:
            payload["max_tokens"] = self.config.max_tokens

        if stream:
            payload["stream"] = True

        for key, value in self.diff_config.request_diff.default_values.items():
            if key not in payload:
                payload[key] = value

        for field_name in self.diff_config.request_diff.remove_fields:
            payload.pop(field_name, None)

        for old_key, new_key in self.diff_config.request_diff.field_mapping.items():
            if old_key in payload:
                payload[new_key] = payload.pop(old_key)

        for old_key, new_key in self.diff_config.request_diff.rename_fields.items():
            if old_key in payload:
                payload[new_key] = payload.pop(old_key)

        for key, value in self.diff_config.request_diff.add_fields.items():
            payload[key] = value

        return payload

    def parse_response(self, data: dict[str, Any]) -> ChatResponse:
        choices = data.get("choices", [])
        if not choices:
            logger.error("API response missing choices. Full response: %s", json.dumps(data, ensure_ascii=False))
            raise LLMException(
                message="API 返回数据格式错误: 缺少 choices",
                code="LLM_INVALID_RESPONSE",
            )

        message = choices[0].get("message", {})
        content = message.get("content", "")

        reasoning_content = None
        if self.diff_config.response_diff.reasoning_field:
            reasoning_content = message.get(self.diff_config.response_diff.reasoning_field)

        if not content and not reasoning_content:
            logger.warning(
                "Empty response from API. Message keys: %s, Full response: %s",
                list(message.keys()),
                json.dumps(data, ensure_ascii=False)
            )
        else:
            logger.debug(
                "API response parsed. Content length: %d, Reasoning length: %d",
                len(content) if content else 0,
                len(reasoning_content) if reasoning_content else 0
            )

        return ChatResponse(
            content=content,
            reasoning_content=reasoning_content,
            raw_response=data,
        )

    def parse_stream_chunk(self, data: dict[str, Any]) -> StreamChunk:
        choices = data.get("choices", [])
        if not choices:
            return StreamChunk()

        delta = choices[0].get("delta", {})
        content = delta.get("content")

        reasoning_content = None
        if self.diff_config.response_diff.reasoning_field:
            reasoning_content = delta.get(self.diff_config.response_diff.reasoning_field)

        return StreamChunk(
            content=content,
            reasoning_content=reasoning_content,
        )

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> ChatResponse:
        url = self.get_endpoint()
        headers = self.get_headers()
        payload = self.build_request_payload(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
        )

        logger.debug(
            "LLM API request: url=%s, model=%s, payload_keys=%s",
            url, payload.get("model"), list(payload.keys())
        )

        try:
            response = await self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return self.parse_response(data)
        except httpx.HTTPStatusError as e:
            error_body = e.response.text[:500] if e.response else "No response"
            logger.error("LLM API HTTP error: status=%d, body=%s", e.response.status_code, error_body)
            raise LLMException(
                message="LLM 服务调用失败",
                code="LLM_HTTP_ERROR",
                details={"status_code": e.response.status_code, "error_body": error_body},
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
    ) -> AsyncIterator[StreamChunk]:
        url = self.get_endpoint()
        headers = self.get_headers()
        payload = self.build_request_payload(
            messages=messages,
            temperature=temperature,
            stream=True,
        )

        try:
            async with self.client.stream(
                "POST", url, json=payload, headers=headers
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            yield StreamChunk(is_done=True)
                            break
                        try:
                            chunk_data = json.loads(data)
                            stream_chunk = self.parse_stream_chunk(chunk_data)
                            if stream_chunk.content or stream_chunk.reasoning_content:
                                yield stream_chunk
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue
        except Exception as e:
            logger.error("LLM stream error: %s", e)
            raise LLMException(
                message="LLM 流式响应失败",
                code="LLM_STREAM_ERROR",
                details={"error": str(e)},
            )

    async def close(self) -> None:
        await self.client.aclose()


def create_adapter(config: ModelConfig) -> OpenAICompatibleAdapter:
    """创建适配器实例"""
    diff_config = get_diff_config(config.model_name, config.provider_id)
    return OpenAICompatibleAdapter(config, diff_config)
