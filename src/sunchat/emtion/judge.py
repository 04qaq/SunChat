# app/emtion/judge.py
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from importlib.resources import files
from typing import List

from sunchat.config import settings
from sunchat.llm.client import LLMClient
from sunchat.models.message import Message
from sunchat.prompt_resources import read_prompt_text


@dataclass
class MoodJudgeResult:
    """评判模型对本轮心情的结构化结果；主对话仅使用 mood_pct + label 注入，无 EMA。"""

    mood_pct: int
    label: str
    used_llm: bool
    valence: float = 0.0
    confidence: float = 0.0


def _valence_to_mood_pct(valence: float, confidence: float) -> int:
    """将 [-1,1] 的 valence 按置信度缩放后映射为 0～100，50 为中性。"""
    v_eff = max(-1.0, min(1.0, valence)) * max(0.0, min(1.0, confidence))
    x = (v_eff + 1.0) * 50.0
    return int(round(max(0.0, min(100.0, x))))


def _extract_json_object(text: str) -> str:
    s = text.strip()
    if s.startswith("```"):
        s = re.sub(r"^```(?:json)?\s*", "", s, flags=re.IGNORECASE)
        s = re.sub(r"\s*```\s*$", "", s)
    start = s.find("{")
    if start == -1:
        raise ValueError("no JSON object in model output")
    depth = 0
    for i in range(start, len(s)):
        if s[i] == "{":
            depth += 1
        elif s[i] == "}":
            depth -= 1
            if depth == 0:
                return s[start : i + 1]
    raise ValueError("unbalanced braces in model output")


def _parse_judge_payload(raw: str) -> tuple[float, float, str]:
    blob = _extract_json_object(raw)
    data = json.loads(blob)
    valence = float(data["valence"])
    confidence = float(data.get("confidence", 1.0))
    label = str(data.get("label", "") or "").strip() or "—"
    valence = max(-1.0, min(1.0, valence))
    confidence = max(0.0, min(1.0, confidence))
    return valence, confidence, label


def _dialogue_block(history: List[Message], user_text: str) -> str:
    lines: List[str] = []
    tail = history[-settings.MOOD_JUDGE_MAX_MESSAGES :]
    for m in tail:
        who = "用户" if m.role == "user" else "助手"
        lines.append(f"{who}: {m.content}")
    lines.append(f"用户: {user_text}")
    return "\n".join(lines)


def load_character_traits_json() -> str:
    """无心理引擎上下文时的回退（兼容旧 JSON）。"""
    path = files("sunchat").joinpath("prompts", "character_traits.json")
    if path.is_file():
        return path.read_text(encoding="utf-8")
    return "{}"


def load_judge_system_prompt() -> str:
    return read_prompt_text("judge_system.txt")


async def compute_mood_signal(
    llm: LLMClient,
    history: List[Message],
    user_text: str,
    *,
    character_context_json: str | None = None,
) -> MoodJudgeResult:
    """
    调用评判模型得到 valence / confidence / label，映射为 mood_pct（0～100）。
    不使用历史 EMA；失败时 mood_pct=50。
    character_context_json：心理引擎组装的 CHARACTER_JSON；为空则回退 character_traits.json。
    """
    traits = character_context_json or load_character_traits_json()
    dialogue = _dialogue_block(history, user_text)
    user_payload = (
        "## CHARACTER_JSON\n"
        f"{traits}\n\n"
        "## DIALOGUE\n"
        f"{dialogue}\n"
    )

    system = load_judge_system_prompt()
    messages = [
        Message("system", system),
        Message("user", user_payload),
    ]

    try:
        raw = await llm.complete_chat(
            messages,
            temperature=0.15,
            timeout_s=settings.MOOD_JUDGE_TIMEOUT_S,
        )
        valence, confidence, label = _parse_judge_payload(raw)
        mood_pct = _valence_to_mood_pct(valence, confidence)
        return MoodJudgeResult(
            mood_pct=mood_pct,
            label=label,
            used_llm=True,
            valence=valence,
            confidence=confidence,
        )
    except Exception:
        return MoodJudgeResult(
            mood_pct=50,
            label="（评判失败，已中性处理）",
            used_llm=False,
            valence=0.0,
            confidence=0.0,
        )
