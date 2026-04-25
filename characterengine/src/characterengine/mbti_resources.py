"""MBTI 行为资源：foundations.md + personas.yaml（随包分发）。"""
from __future__ import annotations

from importlib.resources import files
from typing import Any

import yaml

from characterengine.config import CharacterEngineConfig

_PERSONAS_MAP: dict[str, Any] | None = None


def _resource_root():
    return files("characterengine.resources")


def load_foundations_excerpt(max_chars: int) -> str:
    path = _resource_root().joinpath("mbti_engine").joinpath("foundations.md")
    text = path.read_text(encoding="utf-8")
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "\n…（已截断，完整见 mbti_engine/foundations.md）"


def _personas_map() -> dict[str, Any]:
    global _PERSONAS_MAP
    if _PERSONAS_MAP is None:
        path = _resource_root().joinpath("mbti_engine").joinpath("personas.yaml")
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        _PERSONAS_MAP = {
            k.upper(): v for k, v in data.items() if isinstance(v, dict)
        }
    return _PERSONAS_MAP


def get_persona(mbti: str) -> dict[str, Any]:
    return _personas_map().get(mbti.strip().upper(), {})


def format_persona_for_main(
    mbti: str, *, config: CharacterEngineConfig | None = None
) -> str:
    cfg = config or CharacterEngineConfig()
    p = get_persona(mbti)
    lim = cfg.mbti_persona_max_chars
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


def format_persona_for_judge(
    mbti: str, *, config: CharacterEngineConfig | None = None
) -> str:
    cfg = config or CharacterEngineConfig()
    p = get_persona(mbti)
    lim = cfg.mbti_judge_persona_excerpt_chars
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
    if max_chars <= 0:
        return ""
    return (
        "### 【MBTI 通用基础（节选）】\n\n"
        + load_foundations_excerpt(max_chars).strip()
    )
