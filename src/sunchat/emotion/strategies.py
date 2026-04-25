"""情绪策略：以组合替代 ``ws`` 内 if/else 硬分支。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from sunchat.emotion.judge import MoodJudgeResult, compute_mood_signal
from sunchat.models.message import Message
from sunchat.ports.llm import LlmCompletionsPort
from sunchat.ports.mood import MoodStrategy


@dataclass
class LlmMoodStrategy:
    """通过独立评判模型与 ``compute_mood_signal`` 计算心情。"""

    llm: LlmCompletionsPort
    max_dialogue_messages: int
    judge_temperature: float
    judge_timeout_s: float

    async def compute(
        self,
        history: List[Message],
        user_text: str,
        *,
        character_context_json: str | None,
    ) -> MoodJudgeResult:
        return await compute_mood_signal(
            self.llm,
            history,
            user_text,
            character_context_json=character_context_json,
            max_dialogue_messages=self.max_dialogue_messages,
            temperature=self.judge_temperature,
            timeout_s=self.judge_timeout_s,
        )


class StaticMoodStrategy:
    """不调用 LLM，固定中性心情（调试用或节省配额）。"""

    async def compute(
        self,
        history: List[Message],
        user_text: str,
        *,
        character_context_json: str | None,
    ) -> MoodJudgeResult:
        return MoodJudgeResult(
            mood_pct=50,
            label="",
            used_llm=False,
            valence=0.0,
            confidence=0.0,
        )
