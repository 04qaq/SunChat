"""自研 MBTI 行为资源加载：foundations + personas.yaml，服务心情引擎。"""
from __future__ import annotations

from importlib.resources import files
from typing import Any

import yaml

from sunchat.config import settings

_PERSONAS_MAP: dict[str, Any] | None = None


def load_foundations_excerpt(max_chars: int) -> str:
    """用于推断与（可选）主对话的认知基础节选。"""
    path = files("sunchat.prompts").joinpath("mbti_engine", "foundations.md")
    text = path.read_text(encoding="utf-8")
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "\n…（已截断，完整见 mbti_engine/foundations.md）"


def _personas_map() -> dict[str, Any]:
    global _PERSONAS_MAP
    if _PERSONAS_MAP is None:
        path = files("sunchat.prompts").joinpath("mbti_engine", "personas.yaml")
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        _PERSONAS_MAP = {
            k.upper(): v for k, v in data.items() if isinstance(v, dict)
        }
    return _PERSONAS_MAP


def get_persona(mbti: str) -> dict[str, Any]:
    return _personas_map().get(mbti.strip().upper(), {})


def format_persona_for_main(mbti: str) -> str:
    """主对话第二条 system 内嵌的完整型格块（受 MBTI_PERSONA_MAX_CHARS 限制）。"""
    p = get_persona(mbti)
    lim = settings.MBTI_PERSONA_MAX_CHARS
    if not p:
        return (
            f"## MBTI 行为规格 · {mbti.upper()}\n"
            "（本地 personas.yaml 未收录该型，仅用四字母与 foundations 约束。）"
        )
    lines = [
        f"## MBTI 行为规格 · {mbti.upper()}",
        f"**功能栈**：{p.get('stack', '')}",
        f"**认知习惯**：{p.get('cognitive', '')}",
        f"**决策习惯**：{p.get('decision', '')}",
        f"**压力与心情联动**：{p.get('pressure_mood', '')}",
        f"**外显声线**：{p.get('voice', '')}",
    ]
    text = "\n\n".join(lines)
    if lim > 0 and len(text) > lim:
        return text[: lim - 1].rstrip() + "…"
    return text


def format_persona_for_judge(mbti: str) -> str:
    """心情评判 JSON 内嵌的短摘要，避免重复全文。"""
    p = get_persona(mbti)
    lim = settings.MBTI_JUDGE_PERSONA_EXCERPT_CHARS
    if not p:
        return ""
    parts = [
        str(p.get("stack", "")),
        str(p.get("pressure_mood", "")),
    ]
    s = " ".join(x for x in parts if x)
    if lim > 0 and len(s) > lim:
        return s[: lim - 1].rstrip() + "…"
    return s


def optional_foundations_block_for_main(max_chars: int) -> str:
    """主对话中可选追加的通用 foundations 节选（0 关闭）。"""
    if max_chars <= 0:
        return ""
    return (
        "### 【MBTI 通用基础（节选）】\n\n"
        + load_foundations_excerpt(max_chars).strip()
    )
