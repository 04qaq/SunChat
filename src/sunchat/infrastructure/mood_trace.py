"""将每轮心情与注入上下文以 JSONL 落盘，实现 :class:`sunchat.ports.trace.MoodTracePort`。"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Optional


def _session_file_name(session_id: str) -> str:
    return "".join(
        c if c.isalnum() or c in "-_" else "_" for c in session_id
    )


def _trace_path(mood_trace_dir: str, session_id: str) -> str:
    base = mood_trace_dir.strip() or "data/mood_trace"
    os.makedirs(base, exist_ok=True)
    safe = _session_file_name(session_id)
    return os.path.join(base, f"{safe}.jsonl")


class JsonlMoodTraceWriter:
    """
    按配置启用时，在目录下为每个会话写独立 ``.jsonl`` 文件；否则 ``append_round`` 为空操作。
    """

    __slots__ = ("_base_dir", "_enabled")

    def __init__(self, *, enabled: bool, base_dir: str) -> None:
        self._enabled = enabled
        self._base_dir = base_dir

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
        if not self._enabled:
            return
        if round_index < 0:
            raise ValueError("round_index 必须非负")
        if not (0 <= mood_pct <= 100):
            raise ValueError("mood_pct 应在 0～100 之间")

        path = _trace_path(self._base_dir, session_id)
        record: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "round": round_index,
            "session_id": session_id,
            "mood": {
                "mood_pct": mood_pct,
                "valence": round(valence, 6),
                "confidence": round(confidence, 6),
                "note": "mood_pct 由评判 valence×confidence 映射至 0～100（50 中性），无 EMA",
            },
            "mood_judge": {
                "label": mood_label,
                "used_llm": judge_used_llm,
            },
            "psychology": {
                "mbti_type": mbti_type,
                "mbti_source": mbti_source,
                "mission_primary": mission_primary,
            },
            "prompt_injection": {
                "emotional_context": emotional_context,
            },
            "dialogue": {
                "user": user_text,
                "assistant": assistant_reply,
                "assistant_char_count": len(assistant_reply),
            },
        }
        line = json.dumps(record, ensure_ascii=False) + "\n"
        with open(path, "a", encoding="utf-8") as f:
            f.write(line)
