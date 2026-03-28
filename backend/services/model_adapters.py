"""
Model Adapters - 配置驱动的模型适配器

基于 OpenAI API 格式，通过 YAML 配置文件实现多提供商适配。
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

import httpx

from ..core import LLMException, get_logger
from .providers import load_model_config
from .providers.base import ProviderModelConfig

logger = get_logger(__name__)


@dataclass
class ModelConfig:
    """模型运行时配置"""

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
    request_payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class StreamChunk:
    """流式响应块"""

    content: str | None = None
    reasoning_content: str | None = None
    is_done: bool = False
    raw_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class StreamChatResult:
    """流式聊天结果"""

    request_payload: dict[str, Any] = field(default_factory=dict)
    raw_response_chunks: list[dict[str, Any]] = field(default_factory=list)


class OpenAICompatibleAdapter:
    """OpenAI 兼容适配器 - 基于 YAML 配置动态调整"""

    def __init__(
        self,
        config: ModelConfig,
        provider_config: ProviderModelConfig | None = None,
    ):
        self.config = config
        self.provider_config = provider_config or load_model_config(config.model_name)
        self.client = httpx.AsyncClient(
            timeout=config.timeout,
            trust_env=False,
        )

    def get_endpoint(self) -> str:
        base = self.config.base_url.rstrip("/")
        if self.provider_config:
            suffix = self.provider_config.api.endpoint_suffix
            if base.endswith("/v1") and suffix.startswith("/v1"):
                return f"{base}{suffix[3:]}"
            if base.endswith(suffix):
                return base
            return f"{base}{suffix}"
        if base.endswith("/v1"):
            return f"{base}/chat/completions"
        if base.endswith("/chat/completions"):
            return base
        return f"{base}/chat/completions"

    def get_headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        auth_type = "bearer"
        if self.provider_config:
            auth_type = self.provider_config.api.auth_type
        if self.config.api_key and auth_type == "bearer":
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers

    def build_request_payload(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        stream: bool = False,
        use_thinking: bool = False,
        frequency_penalty: float | None = None,
        presence_penalty: float | None = None,
        response_format: dict | None = None,
        stop: str | list[str] | None = None,
        stream_options: dict | None = None,
        top_p: float | None = None,
        tools: list | None = None,
        tool_choice: str | dict | None = None,
        logprobs: bool = False,
        top_logprobs: int | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """
        构建请求体

        TODO: 多模态支持
        - 支持 content 字段为 List[Dict] 类型
        - 支持 image_url 和 video_url 类型
        - 参考 Kimi API 文档的 content 字段说明
        """
        payload: dict[str, Any] = {
            "model": self.config.model_name,
            "messages": messages,
        }

        if self.provider_config:
            defaults = self.provider_config.request.defaults
            unsupported = self.provider_config.request.unsupported_fields
            special = self.provider_config.request.special

            def add_field(name: str, value: Any, default: Any = None):
                if name in unsupported:
                    return
                if value is not None:
                    payload[name] = value
                elif default is not None:
                    payload[name] = default
                elif name in defaults:
                    payload[name] = defaults[name]

            add_field("temperature", temperature, self.config.temperature)
            add_field("max_tokens", max_tokens, self.config.max_tokens)
            add_field("top_p", top_p)
            add_field("frequency_penalty", frequency_penalty)
            add_field("presence_penalty", presence_penalty)
            add_field("response_format", response_format)
            add_field("stop", stop)
            add_field("stream_options", stream_options)
            add_field("tools", tools)
            add_field("tool_choice", tool_choice)
            add_field("logprobs", logprobs)
            add_field("top_logprobs", top_logprobs)

            if stream:
                payload["stream"] = True

            thinking_config = special.get("thinking", {})
            if thinking_config.get("supported"):
                if use_thinking:
                    payload["thinking"] = {"type": "enabled"}
                    logger.info("Deep thinking enabled for %s", self.config.model_name)
                elif thinking_config.get("default_on"):
                    payload["thinking"] = {"type": "disabled"}

            field_rename = special.get("field_rename", {})
            for old_key, new_key in field_rename.items():
                if old_key in payload:
                    payload[new_key] = payload.pop(old_key)
        else:
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

        return payload

    def parse_response(self, data: dict[str, Any]) -> ChatResponse:
        choices = data.get("choices", [])
        if not choices:
            logger.error(
                "API response missing choices. Full response: %s",
                json.dumps(data, ensure_ascii=False),
            )
            raise LLMException(
                message="API 返回数据格式错误: 缺少 choices",
                code="LLM_INVALID_RESPONSE",
            )

        message = choices[0].get("message", {})
        content = message.get("content", "")

        reasoning_content = None
        if self.provider_config and self.provider_config.response.reasoning_field:
            reasoning_content = message.get(self.provider_config.response.reasoning_field)

        if not content and not reasoning_content:
            logger.warning(
                "Empty response from API. Message keys: %s, Full response: %s",
                list(message.keys()),
                json.dumps(data, ensure_ascii=False),
            )
        else:
            logger.debug(
                "API response parsed. Content length: %d, Reasoning length: %d",
                len(content) if content else 0,
                len(reasoning_content) if reasoning_content else 0,
            )

        return ChatResponse(
            content=content,
            reasoning_content=reasoning_content,
            raw_response=data,
        )

    def parse_stream_chunk(self, data: dict[str, Any]) -> StreamChunk:
        choices = data.get("choices", [])
        if not choices:
            return StreamChunk(raw_data=data)

        delta = choices[0].get("delta", {})
        content = delta.get("content")

        reasoning_content = None
        if self.provider_config and self.provider_config.response.reasoning_field:
            reasoning_content = delta.get(self.provider_config.response.reasoning_field)

        return StreamChunk(
            content=content,
            reasoning_content=reasoning_content,
            raw_data=data,
        )

    def _get_proxy_urls(self) -> list[str]:
        """获取代理URL列表"""
        if (
            hasattr(self.config, 'proxy_config')
            and self.config.proxy_config
            and self.config.proxy_config.enabled
            and self.config.proxy_config.mode == "smart"
        ):
            return self.config.proxy_config.get_proxy_urls_for_fallback()
        return []

    async def _try_request_with_proxy(
        self,
        url: str,
        headers: dict[str, str],
        payload: dict[str, Any],
        proxy_url: str,
        stream: bool = False,
    ):
        """使用指定代理尝试请求"""
        async with httpx.AsyncClient(
            timeout=self.config.timeout,
            proxy=proxy_url,
        ) as proxy_client:
            if stream:
                return await self._stream_request(url, headers, payload, client=proxy_client)
            response = await proxy_client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response

    async def _do_request(
        self,
        url: str,
        headers: dict[str, str],
        payload: dict[str, Any],
        stream: bool = False,
    ):
        last_error: Exception | None = None
        proxy_urls = self._get_proxy_urls()

        try:
            if stream:
                return await self._stream_request(url, headers, payload)
            response = await self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            last_error = e
            if not proxy_urls:
                raise
        except Exception:
            raise

        for proxy_url in proxy_urls[:5]:
            try:
                response = await self._try_request_with_proxy(
                    url, headers, payload, proxy_url, stream
                )
                logger.info("Smart proxy retry success: %s", proxy_url)
                return response
            except (httpx.ConnectError, httpx.TimeoutException) as e:
                last_error = e
                logger.debug("Proxy %s failed: %s", proxy_url, e)
                continue

        if last_error:
            raise last_error

    async def _stream_request(
        self,
        url: str,
        headers: dict[str, str],
        payload: dict[str, Any],
        client: httpx.AsyncClient | None = None,
    ):
        c = client or self.client
        return c.stream("POST", url, json=payload, headers=headers)

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        use_thinking: bool = False,
    ) -> ChatResponse:
        url = self.get_endpoint()
        headers = self.get_headers()
        payload = self.build_request_payload(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
            use_thinking=use_thinking,
        )

        logger.debug(
            "LLM API request: url=%s, model=%s, payload_keys=%s",
            url,
            payload.get("model"),
            list(payload.keys()),
        )

        try:
            response = await self._do_request(url, headers, payload, stream=False)
            if not isinstance(response, httpx.Response):
                raise LLMException(message="Invalid response", code="LLM_INTERNAL_ERROR")
            data = response.json()
            parsed = self.parse_response(data)
            return ChatResponse(
                content=parsed.content,
                reasoning_content=parsed.reasoning_content,
                raw_response=data,
                request_payload=payload,
            )
        except httpx.HTTPStatusError as e:
            error_body = e.response.text[:500] if e.response else "No response"
            logger.error(
                "LLM API HTTP error: status=%d, body=%s", e.response.status_code, error_body
            )
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
        except LLMException:
            raise
        except json.JSONDecodeError as e:
            error_body = response.text[:500] if response else "No response"
            logger.error("LLM API JSON decode error: %s, body=%s", e, error_body)
            raise LLMException(
                message="LLM 返回数据解析失败",
                code="LLM_INVALID_RESPONSE",
                details={"error": str(e), "body_preview": error_body},
            )
        except Exception as e:
            logger.error(
                "LLM service error: %s (type=%s)",
                str(e) or repr(e),
                type(e).__name__,
                exc_info=True,
            )
            raise LLMException(
                message="LLM 服务内部错误",
                code="LLM_INTERNAL_ERROR",
                details={"error": str(e) or repr(e), "type": type(e).__name__},
            )

    async def stream_chat(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        use_thinking: bool = False,
    ) -> AsyncIterator[StreamChunk | StreamChatResult]:
        url = self.get_endpoint()
        headers = self.get_headers()
        payload = self.build_request_payload(
            messages=messages,
            temperature=temperature,
            stream=True,
            use_thinking=use_thinking,
        )

        clients: list[tuple[httpx.AsyncClient, bool]] = [(self.client, False)]
        if (
            hasattr(self.config, 'proxy_config')
            and self.config.proxy_config
            and self.config.proxy_config.enabled
            and self.config.proxy_config.mode == "smart"
        ):
            for proxy_url in self.config.proxy_config.get_proxy_urls_for_fallback():
                clients.append(
                    (
                        httpx.AsyncClient(
                            timeout=self.config.timeout,
                            proxy=proxy_url,
                        ),
                        True,
                    )
                )

        last_error: Exception | None = None
        for client, should_close in clients:
            try:
                chunks_data: list[dict[str, Any]] = []
                async with client.stream("POST", url, json=payload, headers=headers) as response:
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]":
                                yield StreamChunk(is_done=True)
                                yield StreamChatResult(
                                    request_payload=payload,
                                    raw_response_chunks=chunks_data,
                                )
                                return
                            try:
                                chunk_data = json.loads(data)
                                chunks_data.append(chunk_data)
                                stream_chunk = self.parse_stream_chunk(chunk_data)
                                if stream_chunk.content or stream_chunk.reasoning_content:
                                    yield stream_chunk
                            except (json.JSONDecodeError, KeyError, IndexError):
                                continue
                return
            except (httpx.ConnectError, httpx.TimeoutException) as e:
                last_error = e
                logger.debug("Stream connection failed, trying next: %s", e)
                if should_close:
                    await client.aclose()
                continue
            except Exception as e:
                if should_close:
                    await client.aclose()
                logger.error("LLM stream error: %s", e)
                raise LLMException(
                    message="LLM 流式响应失败",
                    code="LLM_STREAM_ERROR",
                    details={"error": str(e)},
                )

        if last_error:
            raise last_error

    async def close(self) -> None:
        await self.client.aclose()


def create_adapter(config: ModelConfig) -> OpenAICompatibleAdapter:
    """创建适配器实例"""
    provider_config = load_model_config(config.model_name)
    return OpenAICompatibleAdapter(config, provider_config)
