"""将心理画像组装为评判用 JSON 与主对话 system 补充段。"""
from __future__ import annotations

import json

from sunchat.config import settings
from sunchat.mbti_engine.content import (
    format_persona_for_judge,
    format_persona_for_main,
    optional_foundations_block_for_main,
)
from sunchat.psychology.models import PsychologyProfileModel


def judge_character_context_json(
    profile: PsychologyProfileModel,
    mbti_type: str,
    cognitive_hint: str,
) -> str:
    """供心情评判模型使用的 CHARACTER_JSON 字符串。"""
    persona_j = format_persona_for_judge(mbti_type)
    payload = {
        "name": profile.role.name,
        "name_reading": profile.role.name_reading,
        "role_summary": profile.role.role_summary,
        "ocean": profile.ocean.model_dump(),
        "ocean_notes": profile.ocean_notes,
        "behavior_hints": list(profile.behavior_hints),
        "scenario": profile.scenario,
        "relationship": profile.relationship,
        "behavior_logic": {
            "framework": "MBTI",
            "engine": "sun_mbti_engine",
            "type": mbti_type.upper(),
            "cognitive_hint": cognitive_hint or profile.mbti.notes,
            "persona_excerpt_for_mood": persona_j,
            "playbook_note": "完整型格见主对话 system 中《MBTI 行为规格》；推断心情须结合 pressure_mood 与 OCEAN。",
        },
        "drives": profile.drives.model_dump(mode="json"),
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def build_psychology_system_message(
    profile: PsychologyProfileModel,
    mbti_type: str,
    cognitive_hint: str,
) -> str:
    """第二条 system：心理引擎（MBTI 型格 + 可选 foundations 节选 + drives）。"""
    d = profile.drives
    lines: list[str] = [
        "### 【心理引擎 · 行为逻辑】",
        f"- 信息加工与表达须符合 **MBTI {mbti_type.upper()}** 与本节《行为规格》（与五维气质叠加；禁止仅靠四字母随意发挥）。",
    ]
    hint = (cognitive_hint or profile.mbti.notes or "").strip()
    if hint:
        lines.append(f"- 推断/配置给出的认知提示：**{hint}**")
    lines += ["", format_persona_for_main(mbti_type), ""]
    found_blk = optional_foundations_block_for_main(
        settings.MBTI_MAIN_FOUNDATIONS_MAX_CHARS
    )
    if found_blk.strip():
        lines += [found_blk, ""]
    lines += [
        "### 【心理引擎 · 目标与需要】",
        f"- **主目标（mission.primary）**：{d.mission.primary or '（可在 psychology_profile.yaml 的 drives.mission 配置）'}",
    ]
    if (d.mission.narrative or "").strip():
        lines.append(f"- **叙事补充（mission.narrative）**：{d.mission.narrative.strip()}")
    if d.needs:
        lines.append(
            "- **需要层（needs，可扩展）**："
            + json.dumps(d.needs, ensure_ascii=False)
        )
    if d.extensions:
        lines.append(
            "- **扩展位（drives.extensions，供后续任务/插件读取）**："
            + json.dumps(d.extensions, ensure_ascii=False)
        )
    lines += [
        "",
        "请在本轮回复中让人物的目标与需要自然影响动机与措辞；未配置项勿编造具体事实，可保持留白。",
    ]
    return "\n".join(lines).strip()
