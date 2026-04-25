"""心情/情绪信号来源的策略接口（可替换、可单测）。"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Protocol

from sunchat.models.message import Message

if TYPE_CHECKING:
    from sunchat.emotion.judge import MoodJudgeResult


class MoodStrategy(Protocol):
    """
    根据对话片段与用户本轮输入，产出供主链路与状态 XML 使用的心情信号。

    实现可包括：LLM 评判、固定中性、规则或未来的多模型融合等，业务编排层
    只依赖本协议，不分支硬编码在 WebSocket 处理函数内。
    """

    async def compute(
        self,
        history: List[Message],
        user_text: str,
        *,
        character_context_json: str | None,
    ) -> "MoodJudgeResult":
        """返回本轮情绪标签与数值等（见 ``MoodJudgeResult``）。"""
        ...
