# app/emtion/trace.py
"""将每轮心情指数、评判元数据、注入主模型的文案与助手输出写入 JSONL。"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Optional

from sunchat.config import settings


def _trace_path(session_id: str) -> str:
    base = settings.MOOD_TRACE_DIR.strip() or "data/mood_trace"
    os.makedirs(base, exist_ok=True)
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in session_id)
    return os.path.join(base, f"{safe}.jsonl")


def append_chat_round_trace(
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
    if not settings.MOOD_TRACE_ENABLED:
        return

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

    path = _trace_path(session_id)
    line = json.dumps(record, ensure_ascii=False) + "\n"
    with open(path, "a", encoding="utf-8") as f:
        f.write(line)
