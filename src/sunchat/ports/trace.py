"""可观测性：每轮情绪与提示注入轨迹。"""

from __future__ import annotations

from typing import Optional, Protocol


class MoodTracePort(Protocol):
    """将单轮元数据以 JSONL 等方式落盘，便于排障与复核（可配置关闭）。"""

    def append_round(
        self,
        *,
        session_id: str,
        round_index: int,
        mood_pct: int,
        valence: float,
        confidence: float,
        emotional_context: str,
        user_text: str,
        assistant_reply: str,
        mood_label: Optional[str] = None,
        judge_used_llm: Optional[bool] = None,
        mbti_type: Optional[str] = None,
        mbti_source: Optional[str] = None,
        mission_primary: Optional[str] = None,
    ) -> None:
        """追加一条回合记录；若未启用应快速返回。"""
        ...
