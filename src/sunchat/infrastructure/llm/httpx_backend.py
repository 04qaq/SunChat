"""基于共享 ``httpx.AsyncClient`` 的 OpenAI 兼容 Chat Completions 适配器。"""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from typing import List

import httpx

from sunchat.models.message import Message
from sunchat.ports.llm import LlmCompletionsPort

_logger = logging.getLogger(__name__)


def _url(base: str) -> str:
    return f"{base.rstrip('/')}/chat/completions"


class HttpxLlmCompletions(LlmCompletionsPort):
    """
    使用外部注入的 **长期存活** ``AsyncClient``，避免每轮新建连接。

    注意:
        ``stream_chat`` 使用长读；客户端 ``read`` 超时需为可配置/无界（见
        ``sunchat.main`` 中 lifespan 内对 ``httpx`` 的构造方式）。
    """

    __slots__ = ("_client", "_api_key", "_base_url", "_model")

    def __init__(
        self,
        client: httpx.AsyncClient,
        *,
        base_url: str,
        api_key: str,
        model: str,
    ) -> None:
        self._client = client
        self._api_key = api_key
        self._base_url = base_url
        self._model = model

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    async def complete_chat(
        self,
        messages: List[Message],
        *,
        temperature: float = 0.2,
        timeout_s: float = 60.0,
    ) -> str:
        if not self._api_key:
            _logger.error("LLM 调用时 API Key 为空")
            raise ValueError("LLM API key is empty")
        payload = {
            "model": self._model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
            "temperature": temperature,
        }
        r = await self._client.post(
            _url(self._base_url),
            json=payload,
            headers=self._headers(),
            timeout=httpx.Timeout(timeout_s),
        )
        r.raise_for_status()
        data = r.json()
        return (data["choices"][0]["message"].get("content") or "").strip()

    async def stream_chat(self, messages: List[Message]) -> AsyncIterator[str]:
        if not self._api_key:
            _logger.error("LLM 流式调用时 API Key 为空")
            raise ValueError("LLM API key is empty")
        payload = {
            "model": self._model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": True,
        }
        try:
            async with self._client.stream(
                "POST",
                _url(self._base_url),
                json=payload,
                headers=self._headers(),
            ) as r:
                r.raise_for_status()
                async for line in r.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    if line.strip() == "data: [DONE]":
                        break
                    try:
                        raw = line[5:].strip()
                        data = json.loads(raw)
                        delta = data["choices"][0]["delta"].get("content") or ""
                        if delta:
                            yield delta
                    except (json.JSONDecodeError, KeyError, IndexError) as e:
                        _logger.debug("跳过无法解析的 SSE 行: %s", e)
                        continue
        except httpx.HTTPError as e:
            _logger.error("流式补全 HTTP 错误: %s", e, exc_info=True)
            raise


# 与历史模块名/类型别名一致，供少量导入使用
LlmClient = HttpxLlmCompletions
