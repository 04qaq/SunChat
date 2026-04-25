# sunchat/emotion/judge.py
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from importlib.resources import files
from typing import List

from sunchat.ports.llm import LlmCompletionsPort
from sunchat.models.message import Message
from sunchat.prompt_resources import read_prompt_text

_logger = logging.getLogger(__name__)


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


def _dialogue_block(
    history: List[Message], user_text: str, max_messages: int
) -> str:
    lines: List[str] = []
    tail = history[-max_messages:]
    for m in tail:
        who = "用户" if m.role == "user" else "助手"
        lines.append(f"{who}: {m.content}")
    lines.append(f"用户: {user_text}")
    return "\n".join(lines)


def load_character_traits_json() -> str:
    """无心理引擎上下文时的回退（兼容旧 JSON）。"""
    path = files("sunchat.prompts").joinpath("character_traits.json")
    if path.is_file():
        return path.read_text(encoding="utf-8")
    return "{}"


def load_judge_system_prompt() -> str:
    return read_prompt_text("judge_system.txt")


async def compute_mood_signal(
    llm: LlmCompletionsPort,
    history: List[Message],
    user_text: str,
    *,
    character_context_json: str | None = None,
    max_dialogue_messages: int,
    temperature: float,
    timeout_s: float,
) -> MoodJudgeResult:
    """
    调用评判模型得到 valence / confidence / label，映射为 mood_pct（0～100）。

    不使用历史 EMA；失败时 mood_pct=50。
    character_context_json：心理引擎组装的 CHARACTER_JSON；为空则回退 character_traits.json。

    Args:
        llm: 补全端口实现。
        history: 当前对话历史（不含本轮用户句则仍传入 user_text）。
        user_text: 本轮用户纯文本。
        character_context_json: 心理侧 CHARACTER JSON，可空。
        max_dialogue_messages: 参与拼接的历史条数上限。
        temperature: 评判用采样温度。
        timeout_s: 非流式请求超时（秒）。

    Returns:
        :class:`MoodJudgeResult`：主链路使用 ``mood_pct``、``label`` 等字段。
    """
    traits = character_context_json or load_character_traits_json()
    dialogue = _dialogue_block(history, user_text, max_dialogue_messages)
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
            temperature=temperature,
            timeout_s=timeout_s,
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
    except Exception as exc:
        _logger.warning("心情评判失败，已回退为中性: %s", exc, exc_info=True)
        return MoodJudgeResult(
            mood_pct=50,
            label="（评判失败，已中性处理）",
            used_llm=False,
            valence=0.0,
            confidence=0.0,
        )
