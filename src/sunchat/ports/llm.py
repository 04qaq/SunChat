"""大模型补全端口的抽象：便于单测中注入 Fake 实现。"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import List, Protocol

from sunchat.models.message import Message


class LlmCompletionsPort(Protocol):
    """
    与 OpenAI 兼容的 Chat Completions 能力（流式/非流式）。

    由 ``HttpxLlmCompletions`` 以 httpx 实现；调用方只依赖本协议，不依赖 httpx。
    """

    async def complete_chat(
        self,
        messages: List[Message],
        *,
        temperature: float = 0.2,
        timeout_s: float = 60.0,
    ) -> str:
        """非流式补全；用于短输出（如情绪评判 JSON）。"""
        ...

    def stream_chat(self, messages: List[Message]) -> AsyncIterator[str]:
        """
        流式增量 token（异步迭代器）。

        各实现应确保在连接关闭时可被上层取消，避免长连接空转（具体由调用栈协作）。
        """
        ...
